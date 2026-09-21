"""Tests for the Stockfish NNUE (SFNNv16) evaluation subsystem.

Verifies:
- Binary loading and weight-tensor shapes for official Stockfish SFNNv16 nets
- SFNNv16 feature extractor correctness (Full_Threats + PP_3Wide + HalfKAv2_hm^)
- Directional plausibility and numerical benchmark evaluations
- Integration with EvaluationConfig, EvalBackend, EvaluatorFactory
- Evaluator contract fulfillment for both python-chess Board and Moray core.Board
"""

from __future__ import annotations

import os

import chess as pychess
import pytest

from engine._core import moray_core as core
from engine.config import EngineConfig, EvalBackend, EvaluationConfig
from engine.config_solver import ConfigSolver
from engine.evaluators import (
    EvaluatorFactory,
    NNUEEvaluator,
    StockfishNNUEEvaluator,
    extract_sfnnv16_features,
)

SF_NET_PATH = "models/stockfish.nnue"
HAS_NET = os.path.isfile(SF_NET_PATH)

CURATED_BENCHMARKS = [
    (
        "Starting Position",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        35.81,
    ),
    (
        "White Up a Queen",
        "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        2922.59,
    ),
    (
        "Black Up a Queen",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1",
        -2488.91,
    ),
    (
        "Scholar's Mate (Mated)",
        "r1bqkb1r/pppp1Qpp/2n5/4p3/2B1n3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4",
        230.84,
    ),
    (
        "Lucena Winning Rook Endgame",
        "1K1k4/1P6/8/8/8/8/r7/2R5 w - - 0 1",
        1815.59,
    ),
    (
        "Tactical Sicilian Pin",
        "r1bqkb1r/pp3ppp/2np4/1B1Np3/4n3/5N2/PPP2PPP/R1BQK2R w KQkq - 0 8",
        -32.06,
    ),
]


@pytest.fixture(scope="module")
def sf_evaluator() -> StockfishNNUEEvaluator:
    """Return a cached StockfishNNUEEvaluator loaded from the test net file."""
    return StockfishNNUEEvaluator(SF_NET_PATH)


# ── Feature extractor tests ──────────────────────────────────────────────────


class TestSFNNv16Extractor:
    """Unit tests for extract_sfnnv16_features."""

    def test_starting_position_feature_count(self) -> None:
        """Verify active features in the starting position."""
        board = pychess.Board()
        w_feats = extract_sfnnv16_features(board, is_white_pov=True)
        b_feats = extract_sfnnv16_features(board, is_white_pov=False)
        assert len(w_feats) > 0
        assert len(b_feats) > 0
        assert len(w_feats) == len(b_feats)

    def test_piece_missing_changes_features(self) -> None:
        """Removing a queen alters the active feature set."""
        board_full = pychess.Board()
        board_no_queen = pychess.Board(
            "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        )
        full = extract_sfnnv16_features(board_full, is_white_pov=True)
        no_q = extract_sfnnv16_features(board_no_queen, is_white_pov=True)
        assert len(no_q) < len(full)

    def test_all_indices_within_bounds(self) -> None:
        """Every returned index must be in the valid [0, 88944) range."""
        board = pychess.Board()
        for is_wp in (True, False):
            feats = extract_sfnnv16_features(board, is_white_pov=is_wp)
            assert all(0 <= idx < 88_944 for idx in feats), (
                f"Out-of-range index in {'white' if is_wp else 'black'} POV"
            )

    def test_empty_board_returns_empty(self) -> None:
        """A completely empty board (no kings) returns empty list."""
        board = pychess.Board(fen=None)
        board.clear()
        feats = extract_sfnnv16_features(board, is_white_pov=True)
        assert feats == []


# ── Loading / shape tests ────────────────────────────────────────────────────


@pytest.mark.skipif(
    not HAS_NET, reason="Stockfish NNUE network not found in models/stockfish.nnue"
)
class TestStockfishNNUELoading:
    """Verify binary loading and weight-tensor shapes."""

    def test_ft_weights_shape(self, sf_evaluator: StockfishNNUEEvaluator) -> None:
        """Feature-transformer weights must have shape (88944, 1032)."""
        assert sf_evaluator.ft_weights.shape == (88_944, 1_032)

    def test_ft_bias_shape(self, sf_evaluator: StockfishNNUEEvaluator) -> None:
        """FT bias must cover L1 (1024) + PSQT (8) = 1032 entries."""
        assert sf_evaluator.ft_bias.shape == (1_032,)

    def test_layer_stack_count(self, sf_evaluator: StockfishNNUEEvaluator) -> None:
        """Exactly 8 layer-stack buckets must be present."""
        assert len(sf_evaluator.l1_weights) == 8
        assert len(sf_evaluator.l2_weights) == 8
        assert len(sf_evaluator.out_weights) == 8

    def test_layer_shapes(self, sf_evaluator: StockfishNNUEEvaluator) -> None:
        """Layer weights and biases must have correct dimensions."""
        for b in range(8):
            assert sf_evaluator.l1_weights[b].shape == (32, 1_024)
            assert sf_evaluator.l1_biases[b].shape == (32,)
            assert sf_evaluator.l2_weights[b].shape == (32, 64)
            assert sf_evaluator.l2_biases[b].shape == (32,)
            assert sf_evaluator.out_weights[b].shape == (1, 128)
            assert sf_evaluator.out_biases[b].shape == (1,)

    def test_description_loaded(self, sf_evaluator: StockfishNNUEEvaluator) -> None:
        """Network description string must be non-empty."""
        assert len(sf_evaluator.description) > 0

    def test_evaluator_is_subclass_of_nnue(
        self, sf_evaluator: StockfishNNUEEvaluator
    ) -> None:
        """StockfishNNUEEvaluator must inherit from NNUEEvaluator."""
        assert isinstance(sf_evaluator, NNUEEvaluator)


# ── Numerical benchmark evaluations ──────────────────────────────────────────


@pytest.mark.skipif(
    not HAS_NET, reason="Stockfish NNUE network not found in models/stockfish.nnue"
)
class TestStockfishNNUEBenchmarks:
    """Verify numerical scores against benchmark positions."""

    @pytest.mark.parametrize(
        ("name", "fen", "expected_cp"),
        CURATED_BENCHMARKS,
    )
    def test_benchmark_evaluation(
        self,
        sf_evaluator: StockfishNNUEEvaluator,
        name: str,
        fen: str,
        expected_cp: float,
    ) -> None:
        """Verify position score matches expected value within 0.1 cp."""
        board = pychess.Board(fen)
        score = sf_evaluator.go(board)
        assert abs(score - expected_cp) < 0.1, (
            f"{name}: expected {expected_cp:.2f} cp, got {score:.2f} cp"
        )

    def test_go_accepts_core_board(self, sf_evaluator: StockfishNNUEEvaluator) -> None:
        """The go() method must accept a Moray core.Board."""
        board = core.Board()
        score = sf_evaluator.go(board)
        assert abs(score - 35.81) < 0.1


# ── Factory / config integration ─────────────────────────────────────────────


@pytest.mark.skipif(
    not HAS_NET, reason="Stockfish NNUE network not found in models/stockfish.nnue"
)
class TestStockfishNNUEFactory:
    """Verify factory wiring and EvaluationConfig dispatch."""

    def test_factory_nnue_stockfish_backend_dispatches(self) -> None:
        """EvaluatorFactory must return StockfishNNUEEvaluator for nnue_stockfish."""
        cfg = EvaluationConfig(
            backend=EvalBackend.NNUE_STOCKFISH,
            nnue_path=SF_NET_PATH,
        )
        evaluator = EvaluatorFactory.create(cfg)
        assert isinstance(evaluator, StockfishNNUEEvaluator)

        engine_cfg = EngineConfig(
            evaluation=cfg,
            search_depth=2,
        )
        solver = ConfigSolver(engine_cfg)
        resolved = solver.resolve()
        assert resolved.evaluation.backend == EvalBackend.NNUE_STOCKFISH
        assert resolved.evaluation.nnue_path == SF_NET_PATH
        evaluator_resolved = EvaluatorFactory.create(resolved.evaluation)
        assert isinstance(evaluator_resolved, StockfishNNUEEvaluator)

    def test_nnue_stockfish_enum_value(self) -> None:
        """EvalBackend.NNUE_STOCKFISH must equal 'nnue_stockfish'."""
        assert EvalBackend.NNUE_STOCKFISH == "nnue_stockfish"
