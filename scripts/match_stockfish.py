"""Benchmark Moray against Stockfish 18 at higher Elo settings."""

from __future__ import annotations

import argparse
import math
import random
import time
from dataclasses import dataclass

import chess
import chess.engine

from engine.config import EngineConfig, EvalBackend
from engine.factory import create_engine

STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"

OPENINGS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1",
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2",
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
    "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    "rnbqk2r/pppp1ppp/4pn2/8/2PP4/2P5/P3PPPP/R1BQKBNR w KQkq - 0 4",
    "r1bqk2r/pppp1ppp/2n2n2/4p3/2B1P3/2P2N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
    "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 3",
    "r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 4 4",
    "rnbqkb1r/pp1ppppp/5n2/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq c6 0 2",
    "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    "rnbqkbnr/pp2pppp/3p4/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 2",
]


@dataclass
class MatchResult:
    """Dataclass storing the outcome of a single match game."""

    fen: str
    moray_is_white: bool
    score: float  # 1.0 = Moray Win, 0.5 = Draw, 0.0 = Stockfish Win
    plies: int
    reason: str


def play_game(
    moray_engine,
    sf_engine: chess.engine.SimpleEngine,
    fen: str,
    moray_is_white: bool,
    moray_depth: int = 5,
    max_plies: int = 160,
) -> tuple[float, int, str]:
    """Play a single game between Moray and Stockfish with error protection."""
    board = chess.Board(fen)
    moray_engine.set_fen(fen)

    for ply in range(max_plies):
        if board.is_game_over():
            result = board.result()
            if result == "1-0":
                score = 1.0 if moray_is_white else 0.0
            elif result == "0-1":
                score = 0.0 if moray_is_white else 1.0
            else:
                score = 0.5
            return score, ply, f"game_over_{result}"

        is_moray_turn = (board.turn == chess.WHITE and moray_is_white) or (
            board.turn == chess.BLACK and not moray_is_white
        )

        if is_moray_turn:
            moray_engine.board.set_fen(board.fen())
            _, move_obj = moray_engine.find_best_move(depth=moray_depth)
            if not move_obj:
                return 0.5, ply, "moray_no_move"
            move = chess.Move.from_uci(move_obj.uci())
        else:
            try:
                sf_result = sf_engine.play(board, chess.engine.Limit(time=0.05))
                if not sf_result.move:
                    return 0.5, ply, "stockfish_no_move"
                move = sf_result.move
            except Exception as e:  # noqa: BLE001
                return 0.5, ply, f"sf_error_{e}"

        board.push(move)

    return 0.5, max_plies, "max_plies"


def run_benchmark_suite(  # noqa: C901, PLR0912
    target_elo: int = 1700,
    num_pairs: int = 30,
    moray_depth: int = 5,
    backend: str = "handcrafted",
    nnue_path: str | None = None,
) -> None:
    """Run benchmark match against Stockfish 18 at a specific UCI_Elo setting."""
    print("\n============================================================")
    print(f"   MORAY vs STOCKFISH 18 ({target_elo} ELO MATCH)")
    print("============================================================")

    moray_config = EngineConfig()
    moray_config.search_depth = moray_depth
    moray_config.evaluation.backend = EvalBackend(backend)
    if nnue_path:
        moray_config.evaluation.nnue_path = nnue_path
    moray = create_engine(moray_config)

    rng = random.Random(1337 + target_elo)
    results: list[MatchResult] = []
    wins, draws, losses = 0, 0, 0
    start_time = time.time()

    total_games = num_pairs * 2
    print(
        f"Target: {total_games} games ({num_pairs} pairs) | "
        f"Moray Search Depth = {moray_depth}"
    )
    print(f"Opponent: Stockfish 18 (UCI_Elo = {target_elo})\n")

    for i in range(num_pairs):
        fen = rng.choice(OPENINGS)

        try:
            sf = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
            sf.configure(
                {"UCI_LimitStrength": True, "UCI_Elo": target_elo, "Threads": 1}
            )

            # Game 1: Moray as White
            s1, p1, r1 = play_game(
                moray, sf, fen, moray_is_white=True, moray_depth=moray_depth
            )
            results.append(MatchResult(fen, True, s1, p1, r1))  # noqa: FBT003
            if s1 == 1.0:
                wins += 1
            elif s1 == 0.5:
                draws += 1
            else:
                losses += 1

            # Game 2: Moray as Black
            s2, p2, r2 = play_game(
                moray, sf, fen, moray_is_white=False, moray_depth=moray_depth
            )
            results.append(MatchResult(fen, False, s2, p2, r2))  # noqa: FBT003
            if s2 == 1.0:
                wins += 1
            elif s2 == 0.5:
                draws += 1
            else:
                losses += 1

            sf.quit()
        except Exception as e:  # noqa: BLE001
            print(
                f"Warning: Pair {i + 1} encountered engine error ({e}), skipping pair."
            )

        played = len(results)
        if played > 0 and (played % 10 == 0 or played == total_games):
            rate = (wins + 0.5 * draws) / played
            print(
                f"Progress: {played:3d}/{total_games:3d} games | "
                f"Moray Record: +{wins} ={draws} -{losses} ({rate * 100:.1f}%)"
            )

    elapsed = time.time() - start_time
    total_played = len(results)
    tot_score = wins + 0.5 * draws
    score_rate = tot_score / total_played if total_played > 0 else 0.5

    # Elo Difference calculation
    if score_rate <= 0.001:
        delta_elo = -800.0
    elif score_rate >= 0.999:
        delta_elo = +800.0
    else:
        delta_elo = -400.0 * math.log10(1.0 / score_rate - 1.0)

    estimated_moray_elo = target_elo + delta_elo

    # Standard error & tight confidence interval
    variance = max(1e-5, (score_rate * (1.0 - score_rate)) / total_played)
    se = math.sqrt(variance)
    margin = 1.96 * se

    s_low = max(0.001, score_rate - margin)
    s_high = min(0.999, score_rate + margin)
    d_low = -400.0 * math.log10(1.0 / s_low - 1.0)
    d_high = -400.0 * math.log10(1.0 / s_high - 1.0)

    print("\n================ FINAL ELO REPORT ================")
    print(f"Moray Engine       : Search Depth {moray_depth} (Full Engine)")
    print(f"Stockfish Baseline : Stockfish 18 (UCI_Elo = {target_elo})")
    print(
        f"Match Results      : +{wins} ={draws} -{losses} "
        f"({score_rate * 100:.1f}% score rate)"
    )
    print(
        f"Time Elapsed       : {elapsed:.2f} seconds "
        f"({total_played / elapsed:.1f} games/sec)"
    )
    print(f"Relative Delta Elo : {delta_elo:+.1f} Elo vs {target_elo} Elo Opponent")
    print(
        f"Estimated Moray Elo: ~{estimated_moray_elo:.0f} Elo "
        f"(95% CI: [{target_elo + d_low:.0f}, {target_elo + d_high:.0f}] Elo)"
    )
    print("==================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Stockfish 18 benchmark match against Moray"
    )
    parser.add_argument(
        "--elo",
        type=int,
        default=1700,
        help="Stockfish UCI_Elo setting (default: 1700)",
    )
    parser.add_argument(
        "--pairs",
        type=int,
        default=30,
        help="Number of opening pairs (default: 30 = 60 games)",
    )
    parser.add_argument(
        "--depth", type=int, default=5, help="Moray search depth (default: 5)"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="handcrafted",
        choices=["handcrafted", "nnue_stockfish", "nnue_custom"],
        help="Evaluation backend to benchmark",
    )
    parser.add_argument(
        "--nnue-path",
        type=str,
        default=None,
        help="Path to NNUE weights file",
    )

    args = parser.parse_args()
    run_benchmark_suite(
        target_elo=args.elo,
        num_pairs=args.pairs,
        moray_depth=args.depth,
        backend=args.backend,
        nnue_path=args.nnue_path,
    )
