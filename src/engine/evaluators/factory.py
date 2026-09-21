"""Evaluator factory and composite evaluator.

The factory reads an ``EvaluationConfig`` and assembles a ready-to-use
``Evaluator`` instance by constructing a C++ ``CompositeEvaluator`` and
pushing the selected components into it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from engine._core import moray_core as chess
from engine.evaluators.components import (
    KingSafetyComponent,
    MaterialComponent,
    MobilityComponent,
    PawnStructureComponent,
    PSTComponent,
)
from engine.evaluators.nnue import NNUEEvaluator
from engine.evaluators.nnue_stockfish import StockfishNNUEEvaluator

if TYPE_CHECKING:
    from engine.config import EvaluationConfig, ResolvedEvaluationConfig
    from engine.evaluators.base import Evaluator

_ev = chess.evaluators

CompositeEvaluator = _ev.CompositeEvaluator

# The native IEvaluator pybind11 class cannot be expressed in the current
# moray_core.pyi stub as a regular importable type, so we fall back
# to ``object`` under TYPE_CHECKING and resolve to the real class at
# runtime.  Both MockEvaluator and SimpleEvaluator subclass it so that C++
# code (Minimax, CompositeEvaluator.add_component) can dispatch natively.
_IEvaluatorBase: Any = _ev.IEvaluator


class MockEvaluator(_IEvaluatorBase):  # type: ignore[misc]
    """Always returns 0.0 — useful for testing search in isolation."""

    def __init__(self) -> None:
        """Initialize the no-op evaluator."""
        super().__init__()

    def go(self, board: chess.Board) -> float:  # noqa: ARG002
        """Return zero regardless of board state."""
        return 0.0


class SimpleEvaluator(_IEvaluatorBase):  # type: ignore[misc]
    """Material-only evaluator — useful for tests needing non-zero scores."""

    def __init__(self) -> None:
        """Initialize with a single material component."""
        super().__init__()
        inner = CompositeEvaluator()
        inner.add_component(MaterialComponent())
        self._inner = inner

    def go(self, board: chess.Board) -> float:
        """Return material-only evaluation score."""
        return float(self._inner.go(board))


class EvaluatorFactory:
    """Build an ``Evaluator`` from an ``EvaluationConfig``."""

    @staticmethod
    def create(config: EvaluationConfig | ResolvedEvaluationConfig) -> Evaluator:
        """Assemble the evaluator according to *config* flags.

        Material counting is always included.  Each optional component is
        appended only when its flag is ``True``.  When ``game_stage_conscious``
        is set, every phase-aware component is constructed with ``gsc=True``.
        """
        backend = getattr(config, "backend", "handcrafted")
        if isinstance(backend, str):
            backend_val = backend.lower()
        else:
            backend_val = getattr(backend, "value", str(backend)).lower()

        if backend_val in ("nnue_custom", "custom_nnue"):
            net_path = getattr(config, "nnue_path", None) or "latent_threats.nnue"
            return NNUEEvaluator(net_path=net_path)

        if backend_val == "nnue_stockfish":
            net_path = getattr(config, "nnue_path", None) or "models/stockfish.nnue"
            return StockfishNNUEEvaluator(net_path=net_path)

        gsc = config.game_stage_conscious
        composite = CompositeEvaluator()
        composite.add_component(MaterialComponent())

        if config.use_pst:
            composite.add_component(PSTComponent(gsc=gsc))

        if config.use_pawn_structure:
            composite.add_component(PawnStructureComponent(gsc=gsc))

        if config.use_mobility:
            composite.add_component(MobilityComponent(gsc=gsc))

        if config.use_king_safety:
            composite.add_component(KingSafetyComponent(gsc=gsc))

        return composite

    @staticmethod
    def create_mock() -> Evaluator:
        """Create a zero-valued mock evaluator."""
        return MockEvaluator()
