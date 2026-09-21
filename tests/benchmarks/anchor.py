"""Machine-independent relative benchmark anchor and JSON normalization.

Measures host machine's native chess NPS using an immutable C++ perft(4) anchor.
Scales benchmark statistics in output.json so that performance tracking in CI
(github-action-benchmark) measures machine-independent Relative Machine Efficiency (RMS)
ratios instead of volatile cloud VM wall-clock seconds.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from engine.factory import create_core_adapter

_KIWIPETE_FEN = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def _run_anchor_perft(board: Any, depth: int) -> int:
    if depth == 0:
        return 1
    moves = board.generate_legal_moves()
    if depth == 1:
        return len(moves)
    nodes = 0
    for move in moves:
        board.push(move)
        nodes += _run_anchor_perft(board, depth - 1)
        board.pop()
    return nodes


def measure_chess_anchor_nps() -> float:
    """Measure native chess NPS using an immutable C++ perft(4) anchor."""
    adapter = create_core_adapter(_KIWIPETE_FEN)
    board = adapter.board

    # Warmup run
    _run_anchor_perft(board, 2)

    start = time.perf_counter()
    nodes = _run_anchor_perft(board, 4)
    elapsed = time.perf_counter() - start

    return nodes / max(0.0001, elapsed)


def normalize_benchmark_json(json_path: str | Path) -> None:
    """Post-process output.json to normalize metrics against chess anchor NPS."""
    path = Path(json_path)
    if not path.exists():
        return

    anchor_nps = measure_chess_anchor_nps()
    anchor_unit_sec = 1.0 / max(1.0, anchor_nps)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data["machine_anchor_nps"] = anchor_nps

    for bench in data.get("benchmarks", []):
        stats = bench.get("stats", {})
        if "ops" in stats and anchor_nps > 0:
            raw_ops = stats["ops"]
            relative_efficiency = raw_ops / anchor_nps

            bench["extra_info"] = bench.get("extra_info", {})
            bench["extra_info"]["anchor_nps"] = anchor_nps
            bench["extra_info"]["relative_efficiency"] = relative_efficiency

            # Scale mean and median so time metrics represent normalized anchor units
            if "mean" in stats and stats["mean"] > 0:
                stats["mean"] = stats["mean"] / anchor_unit_sec
            if "median" in stats and stats["median"] > 0:
                stats["median"] = stats["median"] / anchor_unit_sec
            stats["ops"] = relative_efficiency

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
