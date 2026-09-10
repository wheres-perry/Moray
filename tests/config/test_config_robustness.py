"""Robustness tests for the engine configuration system.

This module rigorously tests the configuration validation and factory logic to ensure
dependencies are enforced and incompatibilities are caught.
"""

import pytest

from engine.config import EngineConfig, EvaluationConfig, SearchConfig
from engine.config_solver import ConfigSolverError
from engine.configurations import minimal_config
from engine.factory import create_engine_runtime


class TestConfigRobustness:
    """Test suite for configuration validation and dependency enforcement."""

    def test_valid_alpha_beta_only(self):
        """Verifies Custom Core + Python Search (Alpha-Beta Only) is valid."""
        cfg = EngineConfig(
            search=SearchConfig(
                use_alpha_beta=True,
                use_move_ordering=False,
                use_transposition_table=False,
                use_tt_aging=False,
                use_hash_move_ordering=False,
                use_iid=False,
                use_check_extensions=False,
                use_pvs=False,
                use_quiescence_search=False,
                use_null_move_pruning=False,
                use_killer_moves=False,
                use_history_heuristic=False,
                use_countermove_heuristic=False,
                use_mvv_lva=False,
                use_see_ordering=False,
                use_lmr=False,
                use_delta_pruning=False,
                use_see_pruning_in_qs=False,
                use_futility_pruning=False,
                use_extended_futility_pruning=False,
                use_reverse_futility_pruning=False,
                use_aspiration_windows=False,
            ),
        )
        assert cfg.search.use_alpha_beta is True
        assert cfg.search.use_move_ordering is False

        runtime = create_engine_runtime(cfg)
        assert runtime is not None

    def test_invalid_killer_without_ordering(self):
        """Verifies runtime resolution rejects killers without ordering."""
        config = minimal_config()
        config.search.use_alpha_beta = True
        config.search.use_killer_moves = True
        with pytest.raises(ConfigSolverError, match="Killer moves requires"):
            create_engine_runtime(config)

    def test_invalid_pvs_without_ab(self):
        """Verifies PVS requires Alpha-Beta."""
        config = minimal_config()
        config.search.use_pvs = True
        with pytest.raises(ConfigSolverError, match="Principal Variation Search"):
            create_engine_runtime(config)

    def test_invalid_tt_aging_without_tt(self):
        """Verifies TT Aging requires TT."""
        config = minimal_config()
        config.search.use_tt_aging = True
        with pytest.raises(ConfigSolverError, match="Transposition-table aging"):
            create_engine_runtime(config)

    def test_full_optimization_stack(self):
        """Verifies a fully loaded configuration passes validation."""
        cfg = EngineConfig(
            search=SearchConfig(
                use_alpha_beta=True,
                use_move_ordering=True,
                use_transposition_table=True,
                use_tt_aging=True,
                use_pvs=True,
                use_quiescence_search=True,
                use_killer_moves=True,
                use_history_heuristic=True,
                use_countermove_heuristic=True,
                use_lmr=True,
                use_null_move_pruning=True,
            )
        )
        runtime = create_engine_runtime(cfg)
        score, move = runtime.searcher.search(1)
        assert score is not None
        assert move is not None

    def test_pawn_structure_is_independent_of_pst(self):
        """Verifies pawn structure can be isolated for ablation experiments."""
        config = minimal_config()
        config.evaluation = EvaluationConfig(
            use_pst=False,
            use_pawn_structure=True,
            use_mobility=False,
            use_king_safety=False,
            game_stage_conscious=False,
        )
        runtime = create_engine_runtime(config)
        assert runtime.evaluator is not None
        assert len(runtime.evaluator.components()) == 2
