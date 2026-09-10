"""Runtime behavior for unusual but valid search-plan combinations."""

from __future__ import annotations

import pytest

from engine._core import moray_core as chess
from engine.config_registry import SEARCH_FEATURES, CorrectnessClass
from engine.config_solver import ConfigSolver
from engine.configurations import ablation_pair, minimal_config
from engine.factory import create_engine


def test_lmr_executes_without_pvs() -> None:
    """LMR depth policy remains reachable when full-window search is selected."""
    config = minimal_config()
    config.search.use_alpha_beta = True
    config.search.use_move_ordering = True
    config.search.use_lmr = True
    config.search.lmr_min_depth = 1
    config.search.lmr_min_move_number = 1
    config.search.max_time = None
    engine = create_engine(config)

    score, move = engine.find_best_move(2)

    assert score is not None
    assert move is not None
    assert engine.searcher.feature_stats["use_lmr"]["applied"] > 0
    assert engine.searcher.feature_stats["use_pvs"]["applied"] == 0


def test_lmr_executes_without_alpha_beta_or_move_ordering() -> None:
    """LMR remains a real depth policy in plain full-width minimax."""
    config = minimal_config()
    config.search.use_lmr = True
    config.search.lmr_min_depth = 1
    config.search.lmr_min_move_number = 1
    config.search.max_time = None
    engine = create_engine(config)

    score, move = engine.find_best_move(2)

    assert score is not None
    assert move is not None
    assert engine.searcher.feature_stats["use_lmr"]["applied"] > 0


def test_quiescence_executes_without_alpha_beta() -> None:
    """Quiescence is supported as a full-width tactical extension."""
    config = minimal_config()
    config.search.use_quiescence_search = True
    config.search.qs_max_depth = 2
    engine = create_engine(config)

    engine.find_best_move(1)

    assert engine.searcher.feature_stats["use_quiescence_search"]["applied"] > 0


def test_iid_is_installed_without_alpha_beta() -> None:
    """IID remains part of full-width search when hash ordering is available."""
    config = minimal_config()
    config.search.use_move_ordering = True
    config.search.use_transposition_table = True
    config.search.use_hash_move_ordering = True
    config.search.use_iid = True
    config.search.iid_min_depth = 2
    config.search.iid_depth_reduction = 1
    config.search.tt_size_mb = 1
    engine = create_engine(config)

    engine.find_best_move(2)

    telemetry = engine.searcher.feature_stats["use_iid"]
    assert engine.searcher.effective_features["use_iid"] is True
    assert telemetry["considered"] > 0


def test_enabled_but_ineligible_feature_is_not_a_config_error() -> None:
    """Runtime eligibility is observable and never treated as invalid config."""
    config = minimal_config()
    config.search.use_check_extensions = True
    engine = create_engine(config)

    engine.find_best_move(1)
    telemetry = engine.searcher.feature_stats["use_check_extensions"]

    assert engine.searcher.effective_features["use_check_extensions"] is True
    assert telemetry["considered"] > 0
    assert telemetry["applied"] == 0


@pytest.mark.parametrize(
    "feature_name",
    ["use_futility_pruning", "use_extended_futility_pruning"],
)
def test_futility_policies_execute_without_alpha_beta(feature_name: str) -> None:
    """Best-so-far scoring is sufficient to compose forward futility."""
    config = minimal_config()
    setattr(config.search, feature_name, True)
    engine = create_engine(config)

    engine.find_best_move(2)

    telemetry = engine.searcher.feature_stats[feature_name]
    assert telemetry["considered"] > 0
    assert telemetry["eligible"] > 0


def test_pvs_executes_without_move_ordering() -> None:
    """PVS window policy does not require a move-ordering implementation."""
    config = minimal_config()
    config.search.use_alpha_beta = True
    config.search.use_pvs = True
    config.search.max_time = None
    engine = create_engine(config)

    score, move = engine.find_best_move(2)

    assert score is not None
    assert move is not None
    assert engine.searcher.move_sorter is None
    assert engine.searcher.feature_stats["use_pvs"]["applied"] > 0


def test_qs_see_has_service_without_move_ordering() -> None:
    """QS SEE pruning receives SEE directly rather than through MoveSorter."""
    config = minimal_config()
    config.search.use_alpha_beta = True
    config.search.use_quiescence_search = True
    config.search.use_see_pruning_in_qs = True
    engine = create_engine(config)

    assert engine.searcher.move_sorter is None
    assert engine.searcher.see is not None
    assert engine.searcher.effective_features["use_see_pruning_in_qs"] is True


def test_static_exchange_service_can_report_losing_capture() -> None:
    """The standalone SEE service distinguishes a defended losing capture."""
    board = chess.Board.from_fen("3q3k/8/8/3p4/3Q4/8/8/K7 w - - 0 1")
    move = chess.Move.from_uci("d4d5")
    service = chess.StaticExchangeEvaluator()
    assert service.evaluate(board, move) < 0


@pytest.mark.parametrize(
    ("pvs", "lmr"),
    [(False, False), (False, True), (True, False), (True, True)],
)
def test_pvs_lmr_quadrants_terminate_and_preserve_board(pvs: bool, lmr: bool) -> None:
    """Window and reduction policies compose in every Boolean quadrant."""
    config = minimal_config()
    config.search.use_alpha_beta = True
    config.search.use_pvs = pvs
    config.search.use_move_ordering = lmr
    config.search.use_lmr = lmr
    config.search.lmr_min_depth = 1
    config.search.lmr_min_move_number = 1
    config.search.max_time = None
    ConfigSolver(config).solve()
    engine = create_engine(config)
    before = engine.board.fen()

    score, move = engine.find_best_move(2)

    assert score is not None
    assert move is not None
    assert move in engine.board.generate_legal_moves()
    assert engine.board.fen() == before


def test_max_depth_caps_explicit_search_request() -> None:
    """The configured maximum depth is an operational runtime limit."""
    config = minimal_config()
    config.search.max_depth = 1
    config.search.max_time = None
    engine = create_engine(config)

    engine.find_best_move(4)

    assert engine.stats.depth == 1


def test_disabled_features_never_report_application() -> None:
    """Telemetry proves disabled feature branches did not run."""
    engine = create_engine(minimal_config())
    engine.find_best_move(1)
    assert all(
        values["applied"] == 0 for values in engine.searcher.feature_stats.values()
    )


@pytest.mark.parametrize("max_time", [0.0, -1.0, float("inf"), float("nan")])
def test_per_search_time_override_must_be_finite_and_positive(max_time: float) -> None:
    """One-shot time controls receive the same boundary validation as config."""
    engine = create_engine(minimal_config())
    with pytest.raises(ValueError, match="finite and positive"):
        engine.find_best_move(1, max_time=max_time)


@pytest.mark.parametrize("max_time", [0.0, -1.0, float("inf"), float("nan")])
def test_native_time_boundary_is_defensive(max_time: float) -> None:
    """The native API rejects invalid limits even when Python is bypassed."""
    engine = create_engine(minimal_config())
    with pytest.raises(ValueError, match="finite and positive"):
        engine.searcher._cpp.find_best_move(1, max_time)


@pytest.mark.parametrize("depth", [0, -1, 129, 1.5])
def test_per_search_depth_must_be_representable(depth: object) -> None:
    """Direct search requests cannot bypass the runtime depth boundary."""
    engine = create_engine(minimal_config())
    with pytest.raises(ValueError, match="integer between 1 and 128"):
        engine.find_best_move(depth)  # type: ignore[arg-type]


@pytest.mark.parametrize("depth", [0, 129])
def test_native_search_depth_boundary_is_defensive(depth: int) -> None:
    """The native API independently protects callers that bypass Python."""
    engine = create_engine(minimal_config())
    with pytest.raises(ValueError, match="between 1 and 128"):
        engine.searcher._cpp.find_best_move(depth)


@pytest.mark.parametrize(
    "feature_name",
    [
        spec.name
        for spec in SEARCH_FEATURES
        if spec.correctness is CorrectnessClass.EXACT
    ],
)
def test_exact_feature_ablation_preserves_score(feature_name: str) -> None:
    """Every exact optimization agrees with its dependency-matched control."""
    control, treatment = ablation_pair(feature_name)
    control.search.max_time = None
    treatment.search.max_time = None
    control.search.tt_size_mb = 1
    treatment.search.tt_size_mb = 1
    fen = "4k3/8/8/8/8/8/4Q3/4K3 w - - 0 1"
    control_engine = create_engine(control, fen)
    treatment_engine = create_engine(treatment, fen)

    control_score, control_move = control_engine.find_best_move(2)
    treatment_score, treatment_move = treatment_engine.find_best_move(2)

    assert control_score == treatment_score
    assert control_move is not None
    assert treatment_move is not None
