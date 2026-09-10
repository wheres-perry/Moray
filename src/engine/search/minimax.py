"""Thin Python wrapper around the C++ negamax searcher.

The real search loop lives in ``engine._core.moray_core.CppMinimax``.
This module preserves the legacy ``Minimax`` import path and exposes the
attributes the existing test suite and factory layer touch directly
(``stats``, ``tt``, ``move_sorter``, ``zobrist``, ``start_time``,
``time_up``, ``_check_time_limit``…).
"""

from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from engine._core import moray_core as chess
from engine.config import EngineConfig, ResolvedEngineConfig
from engine.config_registry import required_services
from engine.config_solver import ConfigSolver
from engine.search.move_ordering import MoveSorter
from engine.search.see import StaticExchangeEvaluator
from engine.search.stats import SearchStats
from engine.search.transposition_table import TranspositionTable
from engine.search.zobrist import Zobrist

if TYPE_CHECKING:
    from engine.evaluators import Evaluator

# Fields that exist on both the native MinimaxStats struct and the Python
# SearchStats dataclass.  We copy these from C++ into Python after every
# search so tests/UCI code can observe idiomatic Python dataclass fields.
_SHARED_STATS_FIELDS: tuple[str, ...] = (
    "nodes",
    "depth",
    "seldepth",
    "tt_hits",
    "hashfull",
    "beta_cutoffs",
    "first_move_cuts",
    "killer_cuts",
    "history_cuts",
    "qsearch_nodes",
    "null_move_cuts",
    "pvs_researches",
    "lmr_researches",
    "qs_see_pruning",
    "qs_delta_pruning",
    "check_extensions",
    "iid_searches",
    "root_move_changes",
    "history_saturation",
    "score",
)


class Minimax:
    """Config-driven negamax searcher backed by the C++ implementation."""

    NEG_INF = float("-inf")
    POS_INF = float("inf")
    MATE_SCORE = 100_000
    TIME_CHECK_INTERVAL = 2048

    def __init__(
        self,
        board: chess.Board,
        evaluator: Evaluator,
        config: EngineConfig | ResolvedEngineConfig,
    ) -> None:
        """Build the underlying C++ search and all its dependencies."""
        resolved = (
            config
            if isinstance(config, ResolvedEngineConfig)
            else ConfigSolver(config).resolve()
        )
        self.board = board
        self.evaluator = evaluator
        self.config = resolved
        self.search_cfg = resolved.search

        self.stats = SearchStats()
        self.node_count = 0
        self.time_up = False
        self.start_time: float | None = None
        services = required_services(self.search_cfg)

        self.zobrist: Zobrist | None = None
        self.tt: TranspositionTable | None = None
        if "transposition_table" in services:
            self.zobrist = Zobrist()
            self.tt = TranspositionTable(self.search_cfg)
            self.zobrist.hash_board(self.board)

        self.move_sorter: MoveSorter | None = None
        if "move_sorter" in services:
            self.move_sorter = MoveSorter(self.search_cfg)

        self.see: StaticExchangeEvaluator | None = None
        if "see" in services:
            self.see = StaticExchangeEvaluator()

        self.root_best_move: chess.Move | None = None

        self._cpp = chess.CppMinimax(
            board,
            evaluator,
            self.tt,
            self.move_sorter,
            self.see,
            self.zobrist,
            self.search_cfg,
        )

    # ── Public API ────────────────────────────────────────────────
    def reset_state(
        self,
        clear_tt: bool = True,
        clear_history: bool = True,
        clear_killers: bool = True,
    ) -> None:
        """Reset search state; optionally preserve TT, history, and killer tables."""
        self._cpp.reset_state(
            clear_tt=clear_tt,
            clear_history=clear_history,
            clear_killers=clear_killers,
        )
        self.stats.reset()
        self.node_count = 0
        self.root_best_move = None

    def find_best_move(
        self,
        depth: int | None = None,
        max_time: float | None = None,
    ) -> tuple[float | None, chess.Move | None]:
        """Run IDDFS up to *depth*.

        Returns the best (score, move) pair from White's perspective.
        """
        requested_depth = depth if depth is not None else self.config.search_depth
        if type(requested_depth) is not int or not 1 <= requested_depth <= 128:
            raise ValueError("Search depth must be an integer between 1 and 128")
        target_depth = requested_depth
        if self.search_cfg.max_depth is not None:
            target_depth = min(target_depth, self.search_cfg.max_depth)
        if max_time is not None and (not math.isfinite(max_time) or max_time <= 0):
            raise ValueError("Search max_time override must be finite and positive")

        self.start_time = time.time()
        self.time_up = False
        self.root_best_move = None

        if self.zobrist is not None:
            self.zobrist.hash_board(self.board)

        score, move = self._cpp.find_best_move(target_depth, max_time)
        self._sync_stats_from_cpp()

        self.time_up = bool(self._cpp.time_up)
        self.root_best_move = self._cpp.root_best_move
        self.node_count = int(self.stats.nodes)
        return score, move

    @property
    def effective_features(self) -> dict[str, bool]:
        """Return the feature flags installed in the compiled C++ plan."""
        return dict(self._cpp.effective_features)

    @property
    def effective_search_config(self) -> dict[str, object]:
        """Return the exact scalar and feature values installed in C++."""
        return dict(self._cpp.effective_config)

    @property
    def feature_stats(self) -> dict[str, dict[str, int]]:
        """Return considered/eligible/applied telemetry for every feature."""
        return {name: dict(values) for name, values in self._cpp.feature_stats.items()}

    def find_top_move(self, depth: int = 1) -> tuple[float | None, chess.Move | None]:
        """Backward-compatible alias for previous API."""
        return self.find_best_move(depth)

    # ── Test/debug helpers ───────────────────────────────────────
    def _check_time_limit(self) -> bool:
        """Check if the search has exceeded the configured time limit."""
        max_time = self.search_cfg.max_time
        if max_time is None or self.start_time is None:
            return False
        if time.time() - self.start_time >= max_time:
            self.time_up = True
            return True
        return False

    # ── Internal helpers ─────────────────────────────────────────
    def _sync_stats_from_cpp(self) -> None:
        """Copy C++ MinimaxStats fields into the Python SearchStats dataclass."""
        cpp_stats = self._cpp.stats
        for field in _SHARED_STATS_FIELDS:
            setattr(self.stats, field, getattr(cpp_stats, field))
