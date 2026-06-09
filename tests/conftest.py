"""Shared fixtures for skill-tester tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def good_skill_dir() -> Path:
    """Path to the well-formed test skill."""
    return FIXTURES_DIR / "good_skill"


@pytest.fixture
def bad_skill_dir() -> Path:
    """Path to the malformed test skill."""
    return FIXTURES_DIR / "bad_skill"


@pytest.fixture
def full_skill_dir() -> Path:
    """Path to the comprehensive test skill with scripts, references, assets."""
    return FIXTURES_DIR / "full_skill"


@pytest.fixture
def minimal_config() -> Dict[str, Any]:
    """A minimal configuration map for testing."""
    return {
        "scoring": {
            "dimensions": {
                "Documentation": {"weight": 0.25},
                "Code": {"weight": 0.25},
                "Completeness": {"weight": 0.25},
                "Usability": {"weight": 0.25},
            },
            "tiers": {
                "POWERFUL": {"min": 8.5, "action": "Deploy"},
                "STANDARD": {"min": 7.0, "action": "Deploy"},
                "BASIC": {"min": 5.0, "action": "Improve"},
                "REJECT": {"min": 0.0, "action": "Rewrite"},
            },
        },
        "analysis": {
            "min_description_length": 20,
            "check_angle_brackets": True,
            "check_todo_placeholders": True,
            "check_name_format": True,
            "required_sections": ["when to use", "stage"],
            "min_examples": 2,
            "script_extensions": [".py", ".sh", ".js"],
        },
        "execution": {
            "enabled": False,
            "claude_command": "claude",
            "timeout_seconds": 180,
            "max_tests": 10,
        },
        "anti_patterns": [
            {"pattern": "TODO|FIXME|XXX", "type": "placeholder", "severity": "high", "message": "Placeholder marker found"},
            {"pattern": r"your\s+(skill|needs|specific|use.case|scenario)\b", "type": "template_artifact", "severity": "medium", "message": "Template language"},
            {"pattern": r"\b(very|extremely)\s+(simple|easy)\b", "type": "filler", "severity": "low", "message": "Filler language"},
            {"pattern": r"Insert\s+(your|the)\s+.*here", "type": "placeholder", "severity": "high", "message": "Insertion placeholder"},
        ],
        "output": {
            "default_format": "summary",
            "max_description_preview": 80,
        },
    }
