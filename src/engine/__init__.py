"""Single-source package metadata."""

from __future__ import annotations

__version__ = "0.1.0"

from engine.config import EngineConfig
from engine.config_registry import FEATURE_REGISTRY, PARAMETER_REGISTRY
from engine.configurations import (
    ablation_pair,
    iter_valid_search_configs,
    maximal_config,
    minimal_config,
    pairwise_search_configs,
)
from engine.factory import EngineRuntime, create_engine_runtime

__all__ = [
    "FEATURE_REGISTRY",
    "PARAMETER_REGISTRY",
    "EngineConfig",
    "EngineRuntime",
    "__version__",
    "ablation_pair",
    "create_engine_runtime",
    "iter_valid_search_configs",
    "maximal_config",
    "minimal_config",
    "pairwise_search_configs",
]
