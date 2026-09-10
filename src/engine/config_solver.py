"""Configuration solver for chess engine search components.

Validates that an ``EngineConfig`` satisfies all dependency and
hyperparameter rules defined in ``ConfigSolverRules``.
"""

from __future__ import annotations

import logging
import math

from z3 import BoolVal, IntVal, is_true, simplify, substitute  # type: ignore

from engine.config import EngineConfig, ResolvedEngineConfig, SearchConfig
from engine.config_registry import (
    EVALUATION_FEATURES,
    SEARCH_FEATURES,
    SEARCH_PARAMETERS,
)
from engine.config_solver_rules import ConfigSolverRules

logger = logging.getLogger(__name__)


class ConfigSolverError(Exception):
    """Raised when a configuration violates dependency or hyperparameter rules."""


class ConfigSolver:
    """Validate feature dependencies and hyperparameters for search engines.

    Instantiate with an ``EngineConfig`` and call :meth:`solve` to run all
    rules.  On the first violation a ``ConfigSolverError`` is raised with a
    human-readable description; otherwise the ``SearchConfig`` is returned.
    """

    def __init__(self, config: EngineConfig) -> None:
        """Initialize the ConfigSolver with an engine configuration.

        Args:
            config: The engine configuration to validate.

        """
        self.config = config
        self.search_config = config.search
        self._rules = ConfigSolverRules()

    def solve(self) -> SearchConfig:
        """Validate all rules and return the search config."""
        self._validate_field_types()
        self._validate_global_bounds()
        self._check_rules(
            self._rules.eval_rules,
            self._build_eval_substitutions(),
        )
        self._check_rules(
            self._rules.search_rules,
            self._build_search_substitutions(),
        )

        logger.debug(
            "All feature dependencies and hyperparameters validated successfully"
        )
        return self.search_config

    def resolve(self) -> ResolvedEngineConfig:
        """Validate and return an immutable runtime snapshot."""
        self.solve()
        return ResolvedEngineConfig.from_config(self.config)

    # ------------------------------------------------------------------
    # Global bounds (not expressible as z3 Implies over config fields)
    # ------------------------------------------------------------------

    def _validate_field_types(self) -> None:
        """Reject values that Python could otherwise coerce at native boundaries."""
        for feature_spec in (*SEARCH_FEATURES, *EVALUATION_FEATURES):
            value = getattr(getattr(self.config, feature_spec.scope), feature_spec.name)
            if type(value) is not bool:
                raise ConfigSolverError(
                    f"{feature_spec.display_name} must be a boolean"
                )

        for parameter_spec in SEARCH_PARAMETERS:
            value = getattr(self.search_config, parameter_spec.name)
            if type(value) is not int:
                raise ConfigSolverError(
                    f"{parameter_spec.display_name} must be an integer"
                )

        if type(self.config.search_depth) is not int:
            raise ConfigSolverError("Search depth must be an integer")
        if (
            self.search_config.max_depth is not None
            and type(self.search_config.max_depth) is not int
        ):
            raise ConfigSolverError("Search max_depth must be an integer or None")
        if self.search_config.max_time is not None and (
            isinstance(self.search_config.max_time, bool)
            or not isinstance(self.search_config.max_time, (int, float))
        ):
            raise ConfigSolverError("Minimax timeout must be a number or None")

    def _validate_global_bounds(self) -> None:
        """Validate global configuration bounds that are not expressible as z3 rules.

        Checks that search depth is within valid range (1-128) and that
        max_time is positive if specified.

        Raises:
            ConfigSolverError: If any global bound constraint is violated.

        """
        if self.config.search_depth < 1:
            raise ConfigSolverError(
                f"Search depth must be at least 1, got {self.config.search_depth}"
            )
        if self.config.search_depth > 128:
            raise ConfigSolverError(
                f"Search depth too high (max 128), got {self.config.search_depth}"
            )
        if self.search_config.max_time is not None and not math.isfinite(
            self.search_config.max_time
        ):
            raise ConfigSolverError("Minimax timeout must be finite")
        if self.search_config.max_time is not None and self.search_config.max_time <= 0:
            raise ConfigSolverError(
                f"Minimax timeout must be positive, got {self.search_config.max_time}"
            )
        if self.search_config.max_depth is not None and not (
            1 <= self.search_config.max_depth <= 128
        ):
            raise ConfigSolverError(
                "Search max_depth must be between 1 and 128 when specified"
            )

    # ------------------------------------------------------------------
    # Substitution builders
    # ------------------------------------------------------------------

    def _build_eval_substitutions(self) -> list[tuple[object, object]]:
        """Build z3 variable substitutions for evaluation configuration.

        Returns:
            A list of (z3_variable, z3_value) tuples for evaluation settings.

        """
        evl = self.config.evaluation
        return [
            (var, BoolVal(getattr(evl, name)))
            for name, var in self._rules.eval_vars.items()
        ]

    def _build_search_substitutions(self) -> list[tuple[object, object]]:
        """Build z3 variable substitutions for search configuration.

        Returns:
            A list of (z3_variable, z3_value) tuples for both boolean and
            integer search settings.

        """
        cfg = self.search_config
        subs: list[tuple[object, object]] = [
            (var, BoolVal(getattr(cfg, name)))
            for name, var in self._rules.search_bool_vars.items()
        ]
        subs += [
            (var, IntVal(getattr(cfg, name)))
            for name, var in self._rules.search_int_vars.items()
        ]
        return subs

    # ------------------------------------------------------------------
    # Rule checker
    # ------------------------------------------------------------------

    @staticmethod
    def _check_rules(
        rules: list[tuple[str, object]],
        substitutions: list[tuple[object, object]],
    ) -> None:
        """Check all rules against the given substitutions.

        Args:
            rules: A list of (description, constraint) tuples where description
                is a human-readable error message and constraint is a z3 expression.
            substitutions: A list of (z3_variable, z3_value) tuples to substitute
                into the constraints.

        Raises:
            ConfigSolverError: If any rule evaluates to false after substitution.

        """
        for description, constraint in rules:
            result = simplify(substitute(constraint, substitutions))
            if not is_true(result):
                raise ConfigSolverError(description)
