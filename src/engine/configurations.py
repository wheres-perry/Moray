"""Generated configurations for optimization experiments."""

from __future__ import annotations

from itertools import combinations, product
from typing import TYPE_CHECKING

from z3 import BoolVal, Or, Solver, is_true, sat  # type: ignore

from engine.config import EngineConfig
from engine.config_registry import (
    EVALUATION_FEATURES,
    FEATURE_REGISTRY,
    SEARCH_FEATURES,
)
from engine.config_solver import ConfigSolver
from engine.config_solver_rules import ConfigSolverRules

if TYPE_CHECKING:
    from collections.abc import Iterator


def minimal_config() -> EngineConfig:
    """Return material-only minimax with every optional feature disabled."""
    config = EngineConfig()
    for spec in (*SEARCH_FEATURES, *EVALUATION_FEATURES):
        setattr(getattr(config, spec.scope), spec.name, False)
    return config


def maximal_config() -> EngineConfig:
    """Return the validated configuration with every registered feature enabled."""
    config = EngineConfig()
    for spec in FEATURE_REGISTRY.values():
        setattr(getattr(config, spec.scope), spec.name, True)
    ConfigSolver(config).solve()
    return config


def ablation_pair(feature_name: str) -> tuple[EngineConfig, EngineConfig]:
    """Return control/treatment configs differing only in the target feature.

    The control contains the feature's complete dependency closure. The
    treatment is identical except that the requested feature is enabled.
    """
    if feature_name not in FEATURE_REGISTRY:
        raise KeyError(f"Unknown feature: {feature_name}")

    treatment = minimal_config()

    def enable(name: str) -> None:
        spec = FEATURE_REGISTRY[name]
        for requirement in spec.requires_all:
            enable(requirement)
        setattr(getattr(treatment, spec.scope), name, True)

    enable(feature_name)
    control = EngineConfig.from_dict(treatment.to_dict())
    target = FEATURE_REGISTRY[feature_name]
    setattr(getattr(control, target.scope), feature_name, False)
    ConfigSolver(control).solve()
    ConfigSolver(treatment).solve()
    return control, treatment


def iter_valid_search_configs(limit: int | None = None) -> Iterator[EngineConfig]:
    """Yield valid Boolean search configurations directly from the Z3 model."""
    rules = ConfigSolverRules()
    solver = Solver()
    solver.add(*(constraint for _, constraint in rules.search_rules))

    defaults = EngineConfig().search
    for name, variable in rules.search_int_vars.items():
        solver.add(variable == getattr(defaults, name))

    produced = 0
    variables = tuple(rules.search_bool_vars.values())
    while solver.check() == sat and (limit is None or produced < limit):
        model = solver.model()
        config = minimal_config()
        values: list[bool] = []
        for spec in SEARCH_FEATURES:
            variable = rules.search_bool_vars[spec.name]
            enabled = is_true(model.eval(variable, model_completion=True))
            setattr(config.search, spec.name, enabled)
            values.append(enabled)
        ConfigSolver(config).solve()
        yield config
        produced += 1
        solver.add(
            Or(
                *(
                    variable != BoolVal(value)
                    for variable, value in zip(variables, values, strict=True)
                )
            )
        )


def pairwise_search_configs() -> tuple[EngineConfig, ...]:
    """Generate a compact set covering every feasible pair of flag values."""
    rules = ConfigSolverRules()
    defaults = EngineConfig().search
    by_assignment: dict[tuple[bool, ...], EngineConfig] = {}
    solver = Solver()
    solver.add(*(constraint for _, constraint in rules.search_rules))
    for name, variable in rules.search_int_vars.items():
        solver.add(variable == getattr(defaults, name))

    for left, right in combinations(SEARCH_FEATURES, 2):
        for left_value, right_value in product((False, True), repeat=2):
            solver.push()
            solver.add(rules.search_bool_vars[left.name] == left_value)
            solver.add(rules.search_bool_vars[right.name] == right_value)
            if solver.check() != sat:
                solver.pop()
                continue

            model = solver.model()
            config = minimal_config()
            assignment: list[bool] = []
            for spec in SEARCH_FEATURES:
                variable = rules.search_bool_vars[spec.name]
                enabled = is_true(model.eval(variable, model_completion=True))
                setattr(
                    config.search,
                    spec.name,
                    enabled,
                )
                assignment.append(enabled)
            by_assignment[tuple(assignment)] = config
            solver.pop()

    return tuple(by_assignment.values())
