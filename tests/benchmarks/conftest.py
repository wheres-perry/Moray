"""Benchmark fixtures and calibration anchor configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.benchmarks.anchor import measure_chess_anchor_nps
from tests.benchmarks.infrastructure import BaselineManager

BASELINES_DIR = Path(".benchmarks")


@pytest.fixture(scope="session")
def anchor_nps() -> float:
    """Provide session-wide host machine chess CPU anchor NPS."""
    return measure_chess_anchor_nps()


@pytest.fixture
def baseline_manager() -> BaselineManager:
    """Provide a ``BaselineManager`` rooted in the project ``.benchmarks/`` dir."""
    return BaselineManager(BASELINES_DIR)
