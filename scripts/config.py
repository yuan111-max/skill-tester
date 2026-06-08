"""Configuration loader for skill-tester.

Loads from config/default.yaml, merges with optional config/local.yaml,
and applies CLI overrides.  All magic numbers live here — nowhere else.
"""

from __future__ import annotations

import copy
import os
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default.yaml"

# ── Sentinel default (used when YAML is unavailable or file is missing) ──

_FALLBACK_CONFIG: Dict[str, Any] = {
    "scoring": {
        "dimensions": {
            "Documentation": {"weight": 0.25},
            "Code": {"weight": 0.25},
            "Completeness": {"weight": 0.25},
            "Usability": {"weight": 0.25},
        },
        "tiers": {
            "POWERFUL": {"min": 8.5, "action": "Deploy immediately; set as benchmark"},
            "STANDARD": {"min": 7.0, "action": "Good to deploy; address minor gaps"},
            "BASIC": {"min": 5.0, "action": "Functional; needs improvement"},
            "REJECT": {"min": 0.0, "action": "Major rewrites required"},
        },
    },
    "analysis": {
        "min_description_length": 20,
        "check_angle_brackets": True,
        "check_todo_placeholders": True,
        "check_name_format": True,
        "required_sections": ["when to use", "stage"],
        "min_examples": 2,
        "script_extensions": [".py", ".sh"],
    },
    "execution": {
        "enabled": False,
        "claude_command": "claude",
        "timeout_seconds": 180,
        "max_tests": 10,
    },
    "anti_patterns": [
        {
            "pattern": "TODO|FIXME|XXX|HACK",
            "type": "placeholder",
            "severity": "high",
            "message": "Placeholder marker found",
        },
        {
            "pattern": r"your\s+(skill|needs|specific|use.case|scenario)\b",
            "type": "template_artifact",
            "severity": "medium",
            "message": "Generic template language",
        },
    ],
    "output": {
        "default_format": "summary",
        "max_description_preview": 80,
    },
}


# ── Public API ───────────────────────────────────────────────────────────


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration, merging defaults → default.yaml → local.yaml.

    Later sources take precedence (deep-merge).
    """
    config: Dict[str, Any] = copy.deepcopy(_FALLBACK_CONFIG)

    if yaml is None:
        return config  # pragma: no cover

    # 1. Ship-default config
    _merge_from_file(config, _DEFAULT_CONFIG_PATH)

    # 2. User-supplied config
    if config_path is not None:
        _merge_from_file(config, config_path)

    # 3. Local overrides (always loaded if exists, lowest CLI priority)
    local_path = _DEFAULT_CONFIG_PATH.parent / "local.yaml"
    _merge_from_file(config, local_path)

    # Validate dimension weights sum to 1.0
    validate_dimension_weights(config.get("scoring", {}).get("dimensions", {}))

    return config


def resolve_tier(final_score: float, tiers: Dict[str, Any]) -> str:
    """Map a 0-10 final score to a tier label."""
    # Iterate in descending min order so the highest matching tier wins
    sorted_tiers = sorted(
        tiers.items(), key=lambda kv: kv[1].get("min", 0), reverse=True
    )
    for label, spec in sorted_tiers:
        if final_score >= spec.get("min", 0):
            return label
    return "REJECT"


def validate_dimension_weights(dimensions: Dict[str, Any]) -> None:
    """Ensure dimension weights sum to 1.0 (with tolerance for float math).

    Prints a warning with each dimension's current weight if the total is off.
    """
    total = sum(d.get("weight", 0) for d in dimensions.values())
    if abs(total - 1.0) > 0.001:
        details = ", ".join(
            f"{dim}={spec.get('weight', 0):.2f}"
            for dim, spec in dimensions.items()
        )
        warnings.warn(
            f"Dimension weights sum to {total:.3f}, expected 1.0. "
            f"Current weights: [{details}]"
        )


# ── Internal helpers ────────────────────────────────────────────────────


def _merge_from_file(config: Dict[str, Any], path: Path) -> None:
    """Deep-merge YAML file contents into *config* (in-place)."""
    if not path.exists() or yaml is None:
        return
    try:
        with open(path, encoding="utf-8") as f:
            overrides = yaml.safe_load(f) or {}
        _deep_merge(config, overrides)
    except yaml.YAMLError as exc:
        warnings.warn(f"YAML parse error in {path}: {exc}")
    except OSError as exc:
        warnings.warn(f"Could not read config file {path}: {exc}")


def _deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> None:
    """Recursively merge *overrides* into *base* (in-place)."""
    for key, value in overrides.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
