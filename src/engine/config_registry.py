"""Canonical registry for configurable engine features and parameters.

The registry is the authoritative description of the public configuration
surface. Validation, UCI option discovery, generated configuration tests, and
runtime capability checks consume these records instead of maintaining their
own lists of flags.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Literal

ConfigScope = Literal["search", "evaluation"]
KNOWN_RUNTIME_SERVICES = frozenset(
    {"move_sorter", "see", "transposition_table", "zobrist"}
)


class CorrectnessClass(Enum):
    """How an optimization is expected to compare with reference minimax."""

    EXACT = "exact"
    SELECTIVE = "selective"
    EVALUATION = "evaluation"


@dataclass(frozen=True)
class FeatureSpec:
    """Declarative description of one Boolean engine feature.

    ``requires_all`` is reserved for structural prerequisites: dependencies
    without which the feature cannot be installed in the search. Conditions
    that merely make a feature ineligible at a particular node do not belong
    in configuration validation.
    """

    name: str
    scope: ConfigScope
    display_name: str
    requires_all: tuple[str, ...] = ()
    services: tuple[str, ...] = ()
    capability: str = ""
    correctness: CorrectnessClass = CorrectnessClass.EXACT


@dataclass(frozen=True)
class ParameterSpec:
    """Representable and operational bounds for one integer parameter."""

    name: str
    scope: ConfigScope
    minimum: int
    maximum: int
    display_name: str
    uci_name: str | None = None


_FEATURES = (
    FeatureSpec(
        "use_move_ordering",
        "search",
        "Move ordering",
        services=("move_sorter",),
        capability="move_ordering",
    ),
    FeatureSpec(
        "use_mvv_lva",
        "search",
        "MVV-LVA ordering",
        requires_all=("use_move_ordering",),
        capability="mvv_lva",
    ),
    FeatureSpec(
        "use_history_heuristic",
        "search",
        "History heuristic",
        requires_all=("use_move_ordering", "use_alpha_beta"),
        capability="history_heuristic",
    ),
    FeatureSpec(
        "use_countermove_heuristic",
        "search",
        "Countermove heuristic",
        requires_all=("use_move_ordering", "use_alpha_beta"),
        capability="countermove_heuristic",
    ),
    FeatureSpec(
        "use_see_ordering",
        "search",
        "SEE ordering",
        requires_all=("use_move_ordering",),
        services=("see",),
        capability="see_ordering",
    ),
    FeatureSpec(
        "use_killer_moves",
        "search",
        "Killer moves",
        requires_all=("use_move_ordering", "use_alpha_beta"),
        capability="killer_moves",
    ),
    FeatureSpec(
        "use_hash_move_ordering",
        "search",
        "Hash-move ordering",
        requires_all=("use_move_ordering", "use_transposition_table"),
        services=("transposition_table", "zobrist"),
        capability="hash_move_ordering",
    ),
    FeatureSpec(
        "use_alpha_beta", "search", "Alpha-beta pruning", capability="alpha_beta"
    ),
    FeatureSpec(
        "use_pvs",
        "search",
        "Principal Variation Search",
        requires_all=("use_alpha_beta",),
        capability="pvs",
    ),
    FeatureSpec(
        "use_quiescence_search",
        "search",
        "Quiescence search",
        capability="quiescence_search",
        correctness=CorrectnessClass.SELECTIVE,
    ),
    FeatureSpec(
        "use_iid",
        "search",
        "Internal iterative deepening",
        requires_all=("use_hash_move_ordering",),
        capability="iid",
    ),
    FeatureSpec(
        "use_null_move_pruning",
        "search",
        "Null-move pruning",
        requires_all=("use_alpha_beta",),
        capability="null_move_pruning",
        correctness=CorrectnessClass.SELECTIVE,
    ),
    FeatureSpec(
        "use_lmr",
        "search",
        "Late-move reductions",
        capability="lmr",
        correctness=CorrectnessClass.SELECTIVE,
    ),
    FeatureSpec(
        "use_futility_pruning",
        "search",
        "Futility pruning",
        capability="futility_pruning",
        correctness=CorrectnessClass.SELECTIVE,
    ),
    FeatureSpec(
        "use_extended_futility_pruning",
        "search",
        "Extended futility pruning",
        capability="extended_futility_pruning",
        correctness=CorrectnessClass.SELECTIVE,
    ),
    FeatureSpec(
        "use_reverse_futility_pruning",
        "search",
        "Reverse futility pruning",
        requires_all=("use_alpha_beta",),
        capability="reverse_futility_pruning",
        correctness=CorrectnessClass.SELECTIVE,
    ),
    FeatureSpec(
        "use_delta_pruning",
        "search",
        "Delta pruning",
        requires_all=("use_quiescence_search",),
        capability="delta_pruning",
        correctness=CorrectnessClass.SELECTIVE,
    ),
    FeatureSpec(
        "use_see_pruning_in_qs",
        "search",
        "SEE pruning in quiescence search",
        requires_all=("use_quiescence_search",),
        services=("see",),
        capability="see_pruning_in_qs",
        correctness=CorrectnessClass.SELECTIVE,
    ),
    FeatureSpec(
        "use_aspiration_windows",
        "search",
        "Aspiration windows",
        requires_all=("use_alpha_beta",),
        capability="aspiration_windows",
    ),
    FeatureSpec(
        "use_check_extensions",
        "search",
        "Check extensions",
        capability="check_extensions",
        correctness=CorrectnessClass.SELECTIVE,
    ),
    FeatureSpec(
        "use_transposition_table",
        "search",
        "Transposition table",
        services=("transposition_table", "zobrist"),
        capability="transposition_table",
    ),
    FeatureSpec(
        "use_tt_aging",
        "search",
        "Transposition-table aging",
        requires_all=("use_transposition_table",),
        capability="tt_aging",
    ),
    FeatureSpec(
        "use_pst",
        "evaluation",
        "Piece-square tables",
        capability="pst",
        correctness=CorrectnessClass.EVALUATION,
    ),
    FeatureSpec(
        "use_pawn_structure",
        "evaluation",
        "Pawn-structure evaluation",
        capability="pawn_structure",
        correctness=CorrectnessClass.EVALUATION,
    ),
    FeatureSpec(
        "use_mobility",
        "evaluation",
        "Mobility evaluation",
        capability="mobility",
        correctness=CorrectnessClass.EVALUATION,
    ),
    FeatureSpec(
        "use_king_safety",
        "evaluation",
        "King-safety evaluation",
        capability="king_safety",
        correctness=CorrectnessClass.EVALUATION,
    ),
    FeatureSpec(
        "game_stage_conscious",
        "evaluation",
        "Game-stage-conscious evaluation",
        capability="game_stage_conscious",
        correctness=CorrectnessClass.EVALUATION,
    ),
)

_PARAMETERS = (
    ParameterSpec("history_max_score", "search", 1, 1_000_000, "History maximum score"),
    ParameterSpec(
        "see_capture_threshold",
        "search",
        -1_000_000,
        1_000_000,
        "SEE capture threshold",
    ),
    ParameterSpec("killer_slots_per_ply", "search", 1, 8, "Killer slots per ply"),
    ParameterSpec("qs_max_depth", "search", 1, 128, "Quiescence maximum depth"),
    ParameterSpec("iid_min_depth", "search", 2, 128, "IID minimum depth"),
    ParameterSpec("iid_depth_reduction", "search", 1, 127, "IID depth reduction"),
    ParameterSpec("nmp_reduction_r", "search", 1, 32, "NMP reduction"),
    ParameterSpec("nmp_min_depth", "search", 1, 128, "NMP minimum depth"),
    ParameterSpec("lmr_min_depth", "search", 1, 128, "LMR minimum depth"),
    ParameterSpec("lmr_min_move_number", "search", 1, 256, "LMR minimum move number"),
    ParameterSpec(
        "futility_margin_standard", "search", 1, 1_000_000, "Futility margin"
    ),
    ParameterSpec(
        "futility_margin_extended",
        "search",
        1,
        1_000_000,
        "Extended futility margin",
    ),
    ParameterSpec(
        "rfp_margin_multiplier", "search", 1, 1_000_000, "RFP margin multiplier"
    ),
    ParameterSpec("rfp_max_depth", "search", 1, 128, "RFP maximum depth"),
    ParameterSpec("delta_margin", "search", 1, 1_000_000, "Delta margin"),
    ParameterSpec(
        "aspiration_window_margin",
        "search",
        1,
        1_000_000,
        "Aspiration-window margin",
    ),
    ParameterSpec("max_check_extensions", "search", 1, 128, "Maximum check extensions"),
    ParameterSpec("tt_size_mb", "search", 1, 1024, "Transposition-table size", "Hash"),
)


def _ensure_acyclic(by_name: dict[str, FeatureSpec]) -> None:
    """Reject dependency cycles so recursive closure generation is safe."""
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visiting:
            raise RuntimeError(f"Feature registry dependency cycle includes {name}")
        if name in visited:
            return
        visiting.add(name)
        for requirement in by_name[name].requires_all:
            visit(requirement)
        visiting.remove(name)
        visited.add(name)

    for name in by_name:
        visit(name)


def _validate_registry() -> None:
    """Fail during import when registry metadata is ambiguous or cyclic."""
    feature_names = [spec.name for spec in _FEATURES]
    parameter_names = [spec.name for spec in _PARAMETERS]
    if len(feature_names) != len(set(feature_names)):
        raise RuntimeError("Feature registry contains duplicate names")
    if len(parameter_names) != len(set(parameter_names)):
        raise RuntimeError("Parameter registry contains duplicate names")
    if set(feature_names) & set(parameter_names):
        raise RuntimeError("Feature and parameter registry names must be distinct")
    capabilities = [spec.capability for spec in _FEATURES]
    if any(not capability for capability in capabilities):
        raise RuntimeError("Every feature must declare a runtime capability")
    if len(capabilities) != len(set(capabilities)):
        raise RuntimeError("Feature capabilities must be unique")
    if any(spec.minimum > spec.maximum for spec in _PARAMETERS):
        raise RuntimeError("Parameter registry contains an inverted range")

    by_name = {spec.name: spec for spec in _FEATURES}
    for spec in _FEATURES:
        unknown = set(spec.requires_all) - by_name.keys()
        if unknown:
            raise RuntimeError(
                f"{spec.name} has unknown dependencies: {sorted(unknown)}"
            )
        unknown_services = set(spec.services) - KNOWN_RUNTIME_SERVICES
        if unknown_services:
            raise RuntimeError(
                f"{spec.name} has unknown services: {sorted(unknown_services)}"
            )
    _ensure_acyclic(by_name)


_validate_registry()

FEATURE_REGISTRY = MappingProxyType({spec.name: spec for spec in _FEATURES})
PARAMETER_REGISTRY = MappingProxyType({spec.name: spec for spec in _PARAMETERS})

SEARCH_FEATURES = tuple(spec for spec in _FEATURES if spec.scope == "search")
EVALUATION_FEATURES = tuple(spec for spec in _FEATURES if spec.scope == "evaluation")
SEARCH_PARAMETERS = tuple(spec for spec in _PARAMETERS if spec.scope == "search")


def required_services(config: object) -> frozenset[str]:
    """Return services required by the enabled registered search features."""
    services: set[str] = set()
    for spec in SEARCH_FEATURES:
        if bool(getattr(config, spec.name)):
            services.update(spec.services)
    return frozenset(services)
