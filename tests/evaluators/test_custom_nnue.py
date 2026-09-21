"""Tests for custom NNUE evaluation subsystem.

Verifies:
- LEB128 decoding and binary weight loading from latent_threats.nnue
- Composed feature extraction (Full_Threats, PP_3Wide, HalfKAv2_hm^, LatentThreats)
- Bit-accurate numerical parity against ground truth for curated benchmark positions
- Evaluator contract fulfillment for both python-chess Board and Moray core.Board
- Integration with EvaluationConfig, EvalBackend, EvaluatorFactory, and engine search
"""

from __future__ import annotations

import os
from pathlib import Path

import chess as pychess
import pytest

from engine._core import moray_core as core
from engine.config import EngineConfig, EvalBackend, EvaluationConfig
from engine.config_solver import ConfigSolver
from engine.evaluators import CustomNNUEEvaluator, EvaluatorFactory, NNUEEvaluator
from engine.evaluators.nnue import decode_leb128, extract_features
from engine.factory import create_engine

NET_PATH = "latent_threats.nnue"
HAS_NET = os.path.isfile(NET_PATH)

CURATED_BENCHMARKS = [
    (
        "Starting Position",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        54.44,
    ),
    (
        "White Up a Queen",
        "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        3827.06,
    ),
    (
        "Black Up a Queen",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1",
        -4182.00,
    ),
    (
        "Scholar's Mate (Mated)",
        "r1bqkb1r/pppp1Qpp/2n5/4p3/2B1n3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4",
        103.19,
    ),
    (
        "Lucena Winning Rook Endgame",
        "1K1k4/1P6/8/8/8/8/r7/2R5 w - - 0 1",
        1416.69,
    ),
    (
        "Tactical Sicilian Pin",
        "r1bqkb1r/pp3ppp/2np4/1B1Np3/4n3/5N2/PPP2PPP/R1BQK2R w KQkq - 0 8",
        -3.72,
    ),
]


class TestDecodeLEB128:
    """Unit tests for LEB128 variable-length integer decoding."""

    def test_decode_leb128_values(self) -> None:
        """Verify decoding of positive, negative, and multi-byte LEB128 integers."""
        data = bytes([0x00, 0x01, 0x7F, 0xE5, 0x8E, 0x26])
        arr = decode_leb128(data, 4)
        assert arr.tolist() == [0, 1, -1, 624485]


class TestCustomFeatureExtractor:
    """Unit tests for custom NNUE feature extraction including Latent Threats."""

    def test_starting_position_feature_count(self) -> None:
        """Verify feature extraction returns symmetric active features."""
        board = pychess.Board()
        w_feats = extract_features(board, is_white_pov=True)
        b_feats = extract_features(board, is_white_pov=False)
        assert len(w_feats) > 0
        assert len(w_feats) == len(b_feats)

    def test_latent_threats_detected_in_pin(self) -> None:
        """Verify pin produces features in LatentThreats range [88944, 101232)."""
        # Bb5 pins Nc6 against king Ke8
        board = pychess.Board(
            "r1bqkb1r/pp3ppp/2np4/1B1Np3/4n3/5N2/PPP2PPP/R1BQK2R w KQkq - 0 8"
        )
        feats = extract_features(board, is_white_pov=True)
        lt_feats = [idx for idx in feats if idx >= 88_944]
        assert len(lt_feats) > 0
        assert all(idx < 101_232 for idx in lt_feats)

    def test_all_indices_within_bounds(self) -> None:
        """Every returned feature index must be within [0, 101232)."""
        board = pychess.Board()
        for is_wp in (True, False):
            feats = extract_features(board, is_white_pov=is_wp)
            assert all(0 <= idx < 101_232 for idx in feats)

    def test_empty_board_returns_empty(self) -> None:
        """An empty board without kings returns no features."""
        board = pychess.Board(fen=None)
        board.clear()
        feats = extract_features(board, is_white_pov=True)
        assert feats == []


class TestNNUEAliasAndErrors:
    """Verify alias and missing network file handling without loading weights."""

    def test_alias_equivalence(self) -> None:
        """Verify CustomNNUEEvaluator is aliased to NNUEEvaluator."""
        assert CustomNNUEEvaluator is NNUEEvaluator

    def test_file_not_found(self) -> None:
        """Verify FileNotFoundError is raised when network binary is missing."""
        with pytest.raises(FileNotFoundError):
            NNUEEvaluator("non_existent_file.nnue")


@pytest.fixture(scope="module")
def nnue_evaluator() -> NNUEEvaluator:
    """Load NNUEEvaluator once for the module."""
    return NNUEEvaluator(NET_PATH)


@pytest.mark.skipif(not HAS_NET, reason="latent_threats.nnue not present in workspace")
class TestNNUELoading:
    """Verify loading and weight tensor shapes."""

    def test_load_network_success(self, nnue_evaluator: NNUEEvaluator) -> None:
        """Verify layer tensor dimensions match network specification."""
        assert nnue_evaluator.ft_weights.shape == (101232, 1032)
        assert nnue_evaluator.ft_bias.shape == (1032,)
        assert len(nnue_evaluator.l1_weights) == 8
        assert len(nnue_evaluator.l2_weights) == 8
        assert len(nnue_evaluator.out_weights) == 8


@pytest.mark.skipif(not HAS_NET, reason="latent_threats.nnue not present in workspace")
class TestNNUENumericalParity:
    """Verify exact numerical parity against ground truth benchmark positions."""

    @pytest.mark.parametrize(("name", "fen", "expected"), CURATED_BENCHMARKS)
    def test_curated_benchmarks_pychess(
        self, nnue_evaluator: NNUEEvaluator, name: str, fen: str, expected: float
    ) -> None:
        """Verify parity against ground truth for python-chess Board."""
        board = pychess.Board(fen)
        score = nnue_evaluator.go(board)
        diff = abs(score - expected)
        assert diff < 0.05, (
            f"{name}: got {score:.2f}, expected {expected:.2f} (diff {diff:.2f})"
        )

    @pytest.mark.parametrize(("name", "fen", "expected"), CURATED_BENCHMARKS)
    def test_curated_benchmarks_moray_board(
        self, nnue_evaluator: NNUEEvaluator, name: str, fen: str, expected: float
    ) -> None:
        """Verify parity against ground truth for Moray C++ core Board."""
        board = core.Board()
        board.set_fen(fen)
        score = nnue_evaluator.go(board)
        diff = abs(score - expected)
        assert diff < 0.05, (
            f"{name}: got {score:.2f}, expected {expected:.2f} (diff {diff:.2f})"
        )


@pytest.mark.skipif(not HAS_NET, reason="latent_threats.nnue not present in workspace")
class TestNNUEFactoryAndConfig:
    """Verify integration with configuration solver and EvaluatorFactory."""

    def test_factory_creates_nnue_evaluator(self) -> None:
        """Verify EvaluatorFactory instantiates NNUEEvaluator with EvalBackend enum."""
        eval_cfg = EvaluationConfig(backend=EvalBackend.NNUE_CUSTOM, nnue_path=NET_PATH)
        evaluator = EvaluatorFactory.create(eval_cfg)
        assert isinstance(evaluator, NNUEEvaluator)

    def test_factory_string_backend(self) -> None:
        """Verify EvaluatorFactory accepts string backend name."""
        eval_cfg = EvaluationConfig(backend="nnue_custom", nnue_path=NET_PATH)
        evaluator = EvaluatorFactory.create(eval_cfg)
        assert isinstance(evaluator, NNUEEvaluator)

    def test_config_solver_resolves_nnue(self) -> None:
        """Verify ConfigSolver correctly resolves custom NNUE configuration."""
        engine_cfg = EngineConfig(
            evaluation=EvaluationConfig(
                backend=EvalBackend.NNUE_CUSTOM, nnue_path=NET_PATH
            ),
            search_depth=2,
        )
        solver = ConfigSolver(engine_cfg)
        resolved = solver.resolve()
        assert resolved.evaluation.backend == EvalBackend.NNUE_CUSTOM
        assert resolved.evaluation.nnue_path == NET_PATH

    def test_engine_search_with_nnue(self) -> None:
        """Verify engine end-to-end Minimax search executes with NNUE evaluator."""
        engine_cfg = EngineConfig(
            evaluation=EvaluationConfig(
                backend=EvalBackend.NNUE_CUSTOM, nnue_path=NET_PATH
            ),
            search_depth=1,
        )
        engine = create_engine(engine_cfg)
        score, best_move = engine.search()
        assert best_move is not None
        assert isinstance(score, (int, float))
