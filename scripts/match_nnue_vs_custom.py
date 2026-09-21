"""Elo match runner: Stockfish NNUE vs Custom NNUE (Latent Threats).

Plays paired opening games with alternating colors, computes match score,
relative Elo difference, and 95% confidence intervals.
"""

from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass
from typing import Any

from engine._core import moray_core as chess
from engine.config import EvalBackend, EvaluationConfig
from engine.configurations import maximal_config
from engine.factory import create_engine

OPENINGS = [
    (
        "Standard Starting Pos",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    ),
    (
        "Open Game (1. e4 e5)",
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    ),
    (
        "Queen's Pawn (1. d4 d5)",
        "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2",
    ),
    (
        "Sicilian Defense (1. e4 c5)",
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    ),
    (
        "French Defense (1. e4 e6)",
        "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    ),
    (
        "Caro-Kann Defense (1. e4 c6)",
        "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    ),
    (
        "Ruy Lopez (1. e4 e5 2. Nf3 Nc6 3. Bb5)",
        "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    ),
    (
        "Italian Game (1. e4 e5 2. Nf3 Nc6 3. Bc4)",
        "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    ),
    (
        "Queen's Gambit (1. d4 d5 2. c4)",
        "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2",
    ),
    (
        "King's Indian Setup (1. d4 Nf6 2. c4 g6)",
        "rnbqkb1r/pppppp1p/5np1/8/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3",
    ),
]


@dataclass
class GameResult:
    """Outcome record of a single game."""

    opening_name: str
    opening_fen: str
    custom_is_white: bool
    score: float  # 1.0 = Custom NNUE Win, 0.5 = Draw, 0.0 = SF NNUE Win
    ply_count: int
    duration_sec: float


def play_game(
    white_engine: Any,
    black_engine: Any,
    fen: str,
    depth: int = 2,
    max_plies: int = 60,
) -> tuple[float, int, float]:
    """Play a single game between white_engine and black_engine.

    Returns (white_score, total_plies, duration_seconds).
    """
    t0 = time.perf_counter()
    white_engine.set_fen(fen)
    black_engine.set_fen(fen)
    board = chess.Board.from_fen(fen)

    for ply in range(max_plies):
        game_state = board.is_game_over()
        if game_state != chess.GameState.ONGOING:
            duration = time.perf_counter() - t0
            if game_state == chess.GameState.CHECKMATE:
                return (0.0 if board.get_side_to_move() else 1.0), ply, duration
            return 0.5, ply, duration

        current_engine = white_engine if board.get_side_to_move() else black_engine
        current_engine.board.set_fen(board.fen())

        _, move = current_engine.find_best_move(depth=depth)
        if not move:
            return 0.5, ply, time.perf_counter() - t0

        board.push(move)

    return 0.5, max_plies, time.perf_counter() - t0


def run_match(
    num_pairs: int = 5,
    depth: int = 2,
    max_plies: int = 60,
    sf_net: str = "models/stockfish.nnue",
    custom_net: str = "latent_threats.nnue",
) -> None:
    """Run paired match between Custom NNUE and Stockfish NNUE."""
    print("=" * 64)
    print("      Moray Evaluation Match: Custom NNUE vs Stockfish NNUE")
    print("=" * 64)
    print(f"Candidate:  Custom NNUE (Latent Threats) [{custom_net}]")
    print(f"Opponent:   Stockfish SFNNv16 [{sf_net}]")
    print(
        f"Settings:   {num_pairs * 2} games ({num_pairs} pairs) | "
        f"Depth {depth} | Max {max_plies} plies"
    )
    print("-" * 64)

    cfg_custom = maximal_config()
    cfg_custom.evaluation = EvaluationConfig(
        backend=EvalBackend.NNUE_CUSTOM, nnue_path=custom_net
    )
    cfg_custom.search_depth = depth
    eng_custom = create_engine(cfg_custom)

    cfg_sf = maximal_config()
    cfg_sf.evaluation = EvaluationConfig(
        backend=EvalBackend.NNUE_STOCKFISH, nnue_path=sf_net
    )
    cfg_sf.search_depth = depth
    eng_sf = create_engine(cfg_sf)

    results: list[GameResult] = []
    wins, draws, losses = 0, 0, 0
    t_start = time.time()

    openings_pool = list(OPENINGS)
    if num_pairs > len(openings_pool):
        openings_pool = openings_pool * (num_pairs // len(openings_pool) + 1)
    selected_openings = openings_pool[:num_pairs]

    for pair_idx, (op_name, fen) in enumerate(selected_openings, 1):
        print(f"\n[Pair {pair_idx}/{num_pairs}] Opening: {op_name}")

        # Game 1: Custom NNUE is White
        score_w, plies_w, dur_w = play_game(
            eng_custom, eng_sf, fen, depth=depth, max_plies=max_plies
        )
        results.append(
            GameResult(
                opening_name=op_name,
                opening_fen=fen,
                custom_is_white=True,
                score=score_w,
                ply_count=plies_w,
                duration_sec=dur_w,
            )
        )
        outcome_w = "WIN" if score_w == 1.0 else ("DRAW" if score_w == 0.5 else "LOSS")
        if score_w == 1.0:
            wins += 1
        elif score_w == 0.5:
            draws += 1
        else:
            losses += 1
        print(
            f"  Game 1 (Custom=White): {outcome_w:<4} ({score_w}) in "
            f"{plies_w} plies ({dur_w:.1f}s)"
        )

        # Game 2: Custom NNUE is Black (SF NNUE is White)
        score_sf, plies_b, dur_b = play_game(
            eng_sf, eng_custom, fen, depth=depth, max_plies=max_plies
        )
        score_custom_b = 1.0 - score_sf
        results.append(
            GameResult(
                opening_name=op_name,
                opening_fen=fen,
                custom_is_white=False,
                score=score_custom_b,
                ply_count=plies_b,
                duration_sec=dur_b,
            )
        )
        outcome_b = (
            "WIN"
            if score_custom_b == 1.0
            else ("DRAW" if score_custom_b == 0.5 else "LOSS")
        )
        if score_custom_b == 1.0:
            wins += 1
        elif score_custom_b == 0.5:
            draws += 1
        else:
            losses += 1
        print(
            f"  Game 2 (Custom=Black): {outcome_b:<4} ({score_custom_b}) in "
            f"{plies_b} plies ({dur_b:.1f}s)"
        )

        total_p = len(results)
        pts = wins + 0.5 * draws
        rate = pts / total_p * 100.0
        print(f"  --> {pts}/{total_p} (+{wins} ={draws} -{losses}) ({rate:.1f}%)")

    total_time = time.time() - t_start
    total_games = len(results)
    total_score = wins + 0.5 * draws
    score_rate = total_score / total_games

    if score_rate <= 0.0:
        elo_diff = -800.0
    elif score_rate >= 1.0:
        elo_diff = 800.0
    else:
        elo_diff = -400.0 * math.log10(1.0 / score_rate - 1.0)

    variance = max(1e-5, (score_rate * (1.0 - score_rate)) / total_games)
    se_score = math.sqrt(variance)
    margin = 1.96 * se_score

    score_low = max(0.001, score_rate - margin)
    score_high = min(0.999, score_rate + margin)
    elo_low = -400.0 * math.log10(1.0 / score_low - 1.0)
    elo_high = -400.0 * math.log10(1.0 / score_high - 1.0)

    print("\n" + "=" * 64)
    print("                     FINAL MATCH REPORT")
    print("=" * 64)
    print(f"Total Games Played : {total_games}")
    pct = score_rate * 100.0
    print(f"Match Score        : {total_score:.1f} / {total_games} ({pct:.1f}%)")
    print(f"Scoreline          : +{wins} ={draws} -{losses}")
    print(f"Estimated Elo Diff : {elo_diff:+.1f} Elo (Custom NNUE vs SF NNUE)")
    err = (elo_high - elo_low) / 2.0
    print(f"95% Conf. Interval : [{elo_low:+.1f}, {elo_high:+.1f}] (±{err:.1f} Elo)")
    spg = total_time / total_games
    print(f"Total Match Time   : {total_time:.1f}s ({spg:.1f}s/game)")
    print("=" * 64)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Match Custom NNUE vs Stockfish NNUE")
    parser.add_argument(
        "--pairs",
        type=int,
        default=5,
        help="Number of opening pairs (default 5 -> 10 games)",
    )
    parser.add_argument("--depth", type=int, default=2, help="Search depth (default 2)")
    parser.add_argument(
        "--max-plies", type=int, default=60, help="Max plies per game (default 60)"
    )
    args = parser.parse_args()

    run_match(num_pairs=args.pairs, depth=args.depth, max_plies=args.max_plies)
