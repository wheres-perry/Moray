"""Registry-driven configuration invariants."""

from dataclasses import FrozenInstanceError, asdict, fields

import pytest

import engine
from engine.config import (
    EngineConfig,
    EvaluationConfig,
    ResolvedEvaluationConfig,
    ResolvedSearchConfig,
    SearchConfig,
)
from engine.config_registry import (
    EVALUATION_FEATURES,
    FEATURE_REGISTRY,
    SEARCH_FEATURES,
    SEARCH_PARAMETERS,
    ParameterSpec,
    required_services,
)
from engine.config_solver import ConfigSolver, ConfigSolverError
from engine.configurations import (
    ablation_pair,
    iter_valid_search_configs,
    maximal_config,
    minimal_config,
    pairwise_search_configs,
)
from engine.factory import create_engine, create_engine_runtime


def test_registry_covers_every_public_feature_and_parameter() -> None:
    """Every configurable field must have canonical registry metadata."""
    search_fields = {field.name for field in fields(SearchConfig)}
    evaluation_fields = {field.name for field in fields(EvaluationConfig)}
    registered_search = {spec.name for spec in SEARCH_FEATURES}
    registered_evaluation = {spec.name for spec in EVALUATION_FEATURES}
    registered_parameters = {spec.name for spec in SEARCH_PARAMETERS}

    assert {name for name in search_fields if name.startswith("use_")} == (
        registered_search
    )
    assert registered_evaluation == evaluation_fields - {"backend", "nnue_path"}
    assert registered_parameters == search_fields - registered_search - {
        "max_time",
        "max_depth",
    }
    assert {field.name for field in fields(ResolvedSearchConfig)} == search_fields
    assert {
        field.name for field in fields(ResolvedEvaluationConfig)
    } == evaluation_fields
    assert all(spec.capability for spec in FEATURE_REGISTRY.values())


def test_configuration_registry_and_generators_are_public_api() -> None:
    """Experiment code can discover and generate plans from the package root."""
    assert engine.FEATURE_REGISTRY is FEATURE_REGISTRY
    assert engine.minimal_config().search.use_alpha_beta is False
    assert engine.maximal_config().search.use_alpha_beta is True


def test_resolved_config_is_immutable_and_has_stable_fingerprint() -> None:
    """Runtime configuration is an immutable, reproducibly identified snapshot."""
    config = minimal_config()
    first = ConfigSolver(config).resolve()
    second = ConfigSolver(EngineConfig.from_dict(config.to_dict())).resolve()

    assert first.fingerprint == second.fingerprint
    with pytest.raises(FrozenInstanceError):
        first.search.use_pvs = True  # type: ignore[misc]

    integer_time = minimal_config()
    integer_time.search.max_time = 1
    float_time = minimal_config()
    float_time.search.max_time = 1.0
    assert (
        ConfigSolver(integer_time).resolve().fingerprint
        == ConfigSolver(float_time).resolve().fingerprint
    )


@pytest.mark.parametrize("spec", SEARCH_PARAMETERS, ids=lambda spec: spec.name)
def test_parameter_bounds_are_enforced(spec: ParameterSpec) -> None:
    """Both sides of every registry range are rejected."""
    name = spec.name
    for value in (spec.minimum - 1, spec.maximum + 1):
        config = minimal_config()
        setattr(config.search, name, value)
        with pytest.raises(ConfigSolverError, match=spec.display_name):
            ConfigSolver(config).solve()


@pytest.mark.parametrize("spec", SEARCH_PARAMETERS, ids=lambda spec: spec.name)
def test_parameter_bounds_construct_native_plan(spec: ParameterSpec) -> None:
    """Every declared endpoint is representable by the C++ search plan."""
    for value in (spec.minimum, spec.maximum):
        config = minimal_config()
        setattr(config.search, spec.name, value)
        engine = create_engine(config)
        assert engine.searcher.effective_search_config[spec.name] == value


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    [
        ("use_pvs", 1, "boolean"),
        ("tt_size_mb", True, "integer"),
        ("max_depth", 2.5, "integer or None"),
        ("max_time", "fast", "number or None"),
    ],
)
def test_noncanonical_field_types_are_rejected(
    field_name: str, value: object, message: str
) -> None:
    """Configuration values must not rely on implicit native coercions."""
    config = minimal_config()
    setattr(config.search, field_name, value)
    with pytest.raises(ConfigSolverError, match=message):
        ConfigSolver(config).solve()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_time_limit_is_rejected(value: float) -> None:
    """NaN and both infinities are never valid time limits."""
    config = minimal_config()
    config.search.max_time = value
    with pytest.raises(ConfigSolverError, match="finite"):
        ConfigSolver(config).solve()


def test_zero_iid_reduction_is_rejected() -> None:
    """IID cannot recursively search at the same depth."""
    config = maximal_config()
    config.search.iid_min_depth = 1
    config.search.iid_depth_reduction = 0
    with pytest.raises(ConfigSolverError):
        ConfigSolver(config).solve()


def test_ablation_pair_differs_only_by_target_feature() -> None:
    """A generated ablation holds every nontarget value constant."""
    control, treatment = ablation_pair("use_lmr")
    control_data = control.to_dict()
    treatment_data = treatment.to_dict()

    assert control_data["search"].pop("use_lmr") is False
    assert treatment_data["search"].pop("use_lmr") is True
    assert control_data == treatment_data


def test_evaluation_ablation_pair_differs_only_by_target_feature() -> None:
    """Evaluation flags use the same registry-driven ablation machinery."""
    control, treatment = ablation_pair("use_pawn_structure")
    control_data = control.to_dict()
    treatment_data = treatment.to_dict()

    assert control_data["evaluation"].pop("use_pawn_structure") is False
    assert treatment_data["evaluation"].pop("use_pawn_structure") is True
    assert control_data == treatment_data


@pytest.mark.parametrize(
    ("feature_name", "missing_requirement"),
    [
        (spec.name, requirement)
        for spec in FEATURE_REGISTRY.values()
        for requirement in spec.requires_all
    ],
)
def test_every_declared_structural_dependency_blocks(
    feature_name: str, missing_requirement: str
) -> None:
    """Each registry edge denotes a real rejected structural omission."""
    _, treatment = ablation_pair(feature_name)
    requirement = FEATURE_REGISTRY[missing_requirement]
    setattr(getattr(treatment, requirement.scope), missing_requirement, False)

    with pytest.raises(ConfigSolverError):
        ConfigSolver(treatment).solve()


def test_z3_model_generator_yields_unique_valid_configs() -> None:
    """The exhaustive iterator blocks prior models and yields valid plans."""
    configs = tuple(iter_valid_search_configs(limit=64))
    fingerprints = {ConfigSolver(config).resolve().fingerprint for config in configs}
    assert len(configs) == len(fingerprints) == 64


def test_pairwise_generator_returns_valid_diverse_configs() -> None:
    """Pairwise generation returns a compact, valid configuration set."""
    configs = pairwise_search_configs()
    assert len(configs) > len(SEARCH_FEATURES)
    assert all(ConfigSolver(config).solve() is config.search for config in configs)


def test_every_pairwise_config_runs_through_the_native_plan() -> None:
    """Every pairwise plan crosses C++ and completes a legal smoke search."""
    for config in pairwise_search_configs():
        config.search.tt_size_mb = 1
        config.search.qs_max_depth = 2
        engine = create_engine(config)
        before = engine.board.fen()
        expected = {
            spec.name: getattr(config.search, spec.name) for spec in SEARCH_FEATURES
        }
        score, move = engine.find_best_move(1)

        assert engine.searcher.effective_features == expected
        assert score is not None
        assert move is not None
        assert move in engine.board.generate_legal_moves()
        assert engine.board.fen() == before


def test_all_evaluation_flag_combinations_construct() -> None:
    """Evaluation features remain independently mixable in all 32 combinations."""
    for mask in range(1 << len(EVALUATION_FEATURES)):
        config = minimal_config()
        for index, spec in enumerate(EVALUATION_FEATURES):
            setattr(config.evaluation, spec.name, bool(mask & (1 << index)))
        engine = create_engine(config)
        assert (
            engine.effective_config.evaluation
            == ConfigSolver(config).resolve().evaluation
        )


def test_runtime_exposes_resolved_snapshot_not_mutable_request() -> None:
    """Mutating the request after assembly cannot alter the runtime plan."""
    config = minimal_config()
    runtime = create_engine_runtime(config)
    config.search.use_alpha_beta = True
    assert runtime.config.search.use_alpha_beta is False


def test_cpp_effective_config_round_trips_resolved_values() -> None:
    """Every resolved search setting arrives unchanged in the native plan."""
    config = minimal_config()
    config.search.use_alpha_beta = True
    config.search.use_pvs = True
    config.search.max_depth = 3
    resolved = ConfigSolver(config).resolve()
    engine = create_engine(config)

    assert engine.searcher.effective_search_config == asdict(resolved.search)
    assert set(engine.searcher.effective_features) == {
        spec.name for spec in SEARCH_FEATURES
    }


def test_required_services_are_derived_from_enabled_capabilities() -> None:
    """Enabled capabilities declaratively request their runtime services."""
    config = minimal_config()
    config.search.use_alpha_beta = True
    config.search.use_quiescence_search = True
    config.search.use_see_pruning_in_qs = True
    assert required_services(config.search) == frozenset({"see"})

    config.search.use_move_ordering = True
    config.search.use_transposition_table = True
    assert required_services(config.search) == frozenset(
        {"move_sorter", "see", "transposition_table", "zobrist"}
    )
