"""Configuration data structures for the chess engine."""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from engine.constants import DEFAULT_DEPTH, DEFAULT_TIMEOUT


@dataclass
class SearchConfig:
    """Configuration for the chess engine search algorithm and optimizations."""

    # ========================================================================
    # 1. General Search Settings
    # ========================================================================
    max_time: float | None = DEFAULT_TIMEOUT
    max_depth: int | None = None  # Useful for depth-limited searches

    class TTPolicy(Enum):
        """Transposition table aging policy."""

        NONE = 0
        AGING = 1

    def __post_init__(self) -> None:
        """Defer dependency validation to the canonical configuration solver."""

    # ========================================================================
    # Move Ordering
    # ========================================================================
    use_move_ordering: bool = True

    use_mvv_lva: bool = True

    use_history_heuristic: bool = True
    history_max_score: int = 16384

    use_countermove_heuristic: bool = True

    use_see_ordering: bool = True
    see_capture_threshold: int = 0

    use_killer_moves: bool = True
    killer_slots_per_ply: int = 2

    use_hash_move_ordering: bool = True

    # ========================================================================
    # Search Algorithms & Enhancements
    # ========================================================================
    use_alpha_beta: bool = True
    use_pvs: bool = True

    use_quiescence_search: bool = True
    qs_max_depth: int = 16

    use_iid: bool = True
    iid_min_depth: int = 5
    iid_depth_reduction: int = 2

    # ========================================================================
    # Pruning & Reductions
    # ========================================================================
    use_null_move_pruning: bool = True
    nmp_reduction_r: int = 3
    nmp_min_depth: int = 3

    use_lmr: bool = True
    lmr_min_depth: int = 3
    lmr_min_move_number: int = 4

    use_futility_pruning: bool = True
    futility_margin_standard: int = 300

    use_extended_futility_pruning: bool = True
    futility_margin_extended: int = 500

    use_reverse_futility_pruning: bool = True
    rfp_margin_multiplier: int = 120
    rfp_max_depth: int = 8

    use_delta_pruning: bool = True
    delta_margin: int = 200

    use_see_pruning_in_qs: bool = True

    # ========================================================================
    # State Evaluation & Hashing
    # ========================================================================
    use_aspiration_windows: bool = True
    aspiration_window_margin: int = 50

    use_check_extensions: bool = True
    max_check_extensions: int = 16

    use_transposition_table: bool = True
    tt_size_mb: int = 64
    use_tt_aging: bool = True


@dataclass
class EvaluationConfig:
    """Configuration for the static board evaluation.

    Components (each independently toggleable):
      - PST:            Piece-Square Tables
      - Pawn Structure: Doubled / isolated / passed pawn analysis
      - Mobility:       Piece mobility scoring
      - King Safety:    Pawn shield, open-file penalties, attack zone
    """

    use_pst: bool = True
    use_pawn_structure: bool = True
    use_mobility: bool = True
    use_king_safety: bool = True
    game_stage_conscious: bool = True

    def __post_init__(self) -> None:
        """Defer dependency validation to the canonical configuration solver."""


@dataclass
class EngineConfig:
    """Top-level configuration for the chess engine."""

    search: SearchConfig = field(default_factory=SearchConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    search_depth: int = DEFAULT_DEPTH

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to a dictionary."""
        return asdict(self)

    def save_to_json(self, file_path: str | Path) -> None:
        """Save configuration to a JSON file."""
        data = self.to_dict()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EngineConfig":
        """Create configuration from a dictionary.

        This handles nested config objects validation automatically.
        """
        search_data = data.get("search", {})
        eval_data = data.get("evaluation", {})

        search_config = SearchConfig(**search_data)
        eval_config = EvaluationConfig(**eval_data)

        main_data = data.copy()
        main_data.pop("search", None)
        main_data.pop("evaluation", None)

        return cls(search=search_config, evaluation=eval_config, **main_data)

    @classmethod
    def load_from_json(cls, file_path: str | Path) -> "EngineConfig":
        """Load configuration from a JSON file."""
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def __str__(self) -> str:
        """Return a human-readable string representation of the engine configuration.

        Returns:
            A formatted string showing search depth, search flags, and evaluation flags.

        """
        parts: list[str] = [f"Depth: {self.search_depth}"]
        parts.append(self._format_search_flags())
        parts.append(self._format_evaluation_flags())
        return " | ".join(parts)

    def _format_search_flags(self) -> str:  # noqa: C901, PLR0912
        """Format search-related configuration flags into a readable string.

        Returns:
            A string representation of enabled search features and algorithms.
            Returns "Search: [Base Minimax]" if alpha-beta is disabled,
            or "Search: [Empty]" if no flags are enabled.

        """
        s_flags: list[str] = []
        cfg = self.search

        if cfg.use_alpha_beta:
            s_flags.append("a-b")
        else:
            s_flags.append("Base Minimax")

        s_flags.append("IDDFS")

        if cfg.use_pvs:
            s_flags.append("PVS")
            if cfg.use_aspiration_windows:
                s_flags.append("AspWin")

        if cfg.use_transposition_table:
            tt_flags = "TT/Z"
            if cfg.use_tt_aging:
                tt_flags += "+Age"
            s_flags.append(tt_flags)
            if cfg.use_iid:
                s_flags.append("IID")

        if cfg.use_move_ordering:
            s_flags.append("MoveOrder")

        if cfg.use_lmr:
            s_flags.append("LMR")
        if cfg.use_null_move_pruning:
            s_flags.append("NMP")
        if cfg.use_futility_pruning:
            s_flags.append("Futility")
        if cfg.use_quiescence_search:
            s_flags.append("QS")

        if s_flags:
            return f"Search: [{', '.join(s_flags)}]"
        return "Search: [Empty]"

    def _format_evaluation_flags(self) -> str:
        """Format evaluation-related configuration flags into a readable string.

        Returns:
            A string representation of enabled evaluation features.
            Returns "Eval: [Material]" if no evaluation features are enabled.

        """
        e = self.evaluation
        parts: list[str] = []
        if e.use_pst:
            parts.append("PST")
        if e.use_pawn_structure:
            parts.append("Pawns")
        if e.use_mobility:
            parts.append("Mobility")
        if e.use_king_safety:
            parts.append("KingSafety")
        if e.game_stage_conscious:
            parts.append("GSC")

        if parts:
            return f"Eval: [{', '.join(parts)}]"
        return "Eval: [Material]"


@dataclass(frozen=True)
class ResolvedSearchConfig:
    """Immutable search configuration accepted by the solver."""

    max_time: float | None
    max_depth: int | None
    use_move_ordering: bool
    use_mvv_lva: bool
    use_history_heuristic: bool
    history_max_score: int
    use_countermove_heuristic: bool
    use_see_ordering: bool
    see_capture_threshold: int
    use_killer_moves: bool
    killer_slots_per_ply: int
    use_hash_move_ordering: bool
    use_alpha_beta: bool
    use_pvs: bool
    use_quiescence_search: bool
    qs_max_depth: int
    use_iid: bool
    iid_min_depth: int
    iid_depth_reduction: int
    use_null_move_pruning: bool
    nmp_reduction_r: int
    nmp_min_depth: int
    use_lmr: bool
    lmr_min_depth: int
    lmr_min_move_number: int
    use_futility_pruning: bool
    futility_margin_standard: int
    use_extended_futility_pruning: bool
    futility_margin_extended: int
    use_reverse_futility_pruning: bool
    rfp_margin_multiplier: int
    rfp_max_depth: int
    use_delta_pruning: bool
    delta_margin: int
    use_see_pruning_in_qs: bool
    use_aspiration_windows: bool
    aspiration_window_margin: int
    use_check_extensions: bool
    max_check_extensions: int
    use_transposition_table: bool
    tt_size_mb: int
    use_tt_aging: bool

    @classmethod
    def from_config(cls, config: SearchConfig) -> "ResolvedSearchConfig":
        """Snapshot a validated mutable search configuration."""
        values = asdict(config)
        if values["max_time"] is not None:
            values["max_time"] = float(values["max_time"])
        return cls(**values)


@dataclass(frozen=True)
class ResolvedEvaluationConfig:
    """Immutable evaluation configuration accepted by the solver."""

    use_pst: bool
    use_pawn_structure: bool
    use_mobility: bool
    use_king_safety: bool
    game_stage_conscious: bool

    @classmethod
    def from_config(cls, config: EvaluationConfig) -> "ResolvedEvaluationConfig":
        """Snapshot a validated mutable evaluation configuration."""
        return cls(**asdict(config))


@dataclass(frozen=True)
class ResolvedEngineConfig:
    """Immutable, validated configuration consumed by runtime objects."""

    search: ResolvedSearchConfig
    evaluation: ResolvedEvaluationConfig
    search_depth: int

    @classmethod
    def from_config(cls, config: EngineConfig) -> "ResolvedEngineConfig":
        """Snapshot a validated mutable engine configuration."""
        return cls(
            search=ResolvedSearchConfig.from_config(config.search),
            evaluation=ResolvedEvaluationConfig.from_config(config.evaluation),
            search_depth=config.search_depth,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the applied configuration."""
        return asdict(self)

    @property
    def fingerprint(self) -> str:
        """Return a stable identifier suitable for experiment result records."""
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
