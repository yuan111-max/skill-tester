"""Configuration loader for skill-tester.

Loads from config/default.yaml, merges with optional config/local.yaml,
and applies CLI overrides.  All magic numbers live here — nowhere else.
"""

from __future__ import annotations

import copy
import warnings
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default.yaml"

# ── Sentinel default (used when YAML is unavailable or file is missing) ──

_tier_validated: bool = False

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
        "check_name_format": True,
        "required_sections": ["when to use", "stage"],
        "min_examples": 2,
        "script_extensions": [".py", ".sh", ".js", ".ts", ".rb", ".go"],
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
    },
}


# ── Public API ───────────────────────────────────────────────────────────


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration, merging defaults → default.yaml → local.yaml.

    Later sources take precedence (deep-merge).
    """
    config: Dict[str, Any] = copy.deepcopy(_FALLBACK_CONFIG)

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
    _validate_tier_ordering(sorted_tiers)
    for label, spec in sorted_tiers:
        if final_score >= spec.get("min", 0):
            return label
    return "REJECT"


def _validate_tier_ordering(sorted_tiers: list) -> None:
    """Warn once if tier thresholds are not in strict descending order.

    A misconfigured tier set (e.g. POWERFUL.min=7.0, STANDARD.min=8.5) means
    the intended-higher tier may never match because a lower one intercepts.
    """
    global _tier_validated
    if _tier_validated:
        return
    _tier_validated = True

    for i in range(len(sorted_tiers) - 1):
        current_min = sorted_tiers[i][1].get("min", 0)
        next_min = sorted_tiers[i + 1][1].get("min", 0)
        current_label = sorted_tiers[i][0]
        next_label = sorted_tiers[i + 1][0]
        if current_min <= next_min:
            warnings.warn(
                f"Tier threshold overlap: '{current_label}' (min={current_min}) "
                f"should be > '{next_label}' (min={next_min}). "
                f"The '{next_label}' tier may never be reached. "
                f"Check your tier configuration."
            )


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
    if not path.exists():
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
