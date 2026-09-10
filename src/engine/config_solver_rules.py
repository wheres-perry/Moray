"""Z3 rules generated from the canonical engine feature registry."""

from typing import Any

from z3 import And, Bool, Implies, Int  # type: ignore

from engine.config_registry import (
    EVALUATION_FEATURES,
    SEARCH_FEATURES,
    SEARCH_PARAMETERS,
)


class ConfigSolverRules:
    """Build symbolic constraints from registry records."""

    def __init__(self) -> None:
        """Create variables and dependency/range constraints."""
        self.eval_vars: dict[str, Any] = {
            spec.name: Bool(spec.name) for spec in EVALUATION_FEATURES
        }
        self.search_bool_vars: dict[str, Any] = {
            spec.name: Bool(spec.name) for spec in SEARCH_FEATURES
        }
        self.search_int_vars: dict[str, Any] = {
            spec.name: Int(spec.name) for spec in SEARCH_PARAMETERS
        }

        all_bool_vars = {**self.eval_vars, **self.search_bool_vars}
        self.eval_rules = self._dependency_rules(EVALUATION_FEATURES, all_bool_vars)
        self.search_rules = self._dependency_rules(SEARCH_FEATURES, all_bool_vars)

        for spec in SEARCH_PARAMETERS:
            value = self.search_int_vars[spec.name]
            self.search_rules.append(
                (
                    f"{spec.display_name} must be between "
                    f"{spec.minimum} and {spec.maximum}.",
                    And(value >= spec.minimum, value <= spec.maximum),
                )
            )

        iid_min = self.search_int_vars["iid_min_depth"]
        iid_reduction = self.search_int_vars["iid_depth_reduction"]
        self.search_rules.append(
            (
                "IID minimum depth must exceed its positive depth reduction.",
                Implies(self.search_bool_vars["use_iid"], iid_min > iid_reduction),
            )
        )

    @staticmethod
    def _dependency_rules(
        specs: tuple[Any, ...], variables: dict[str, Any]
    ) -> list[tuple[str, object]]:
        """Create implication rules for all registered dependencies."""
        rules: list[tuple[str, object]] = []
        for spec in specs:
            if not spec.requires_all:
                continue
            requirements = [variables[name] for name in spec.requires_all]
            names = ", ".join(spec.requires_all)
            rules.append(
                (
                    f"{spec.display_name} requires: {names}.",
                    Implies(variables[spec.name], And(*requirements)),
                )
            )
        return rules
