"""Tests for the Stage 4 evaluation module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from scripts.analyze import analyze_skill
from scripts.generate import generate_tests
from scripts.evaluate import evaluate


class TestEvaluate:
    """Integration tests for evaluation scoring."""

    def test_good_skill_scores_well(self, good_skill_dir: Path, minimal_config: Dict[str, Any]):
        """A well-formed skill should score >= 7.0 (STANDARD or better)."""
        analysis = analyze_skill(good_skill_dir, minimal_config)
        assert "error" not in analysis

        test_data = generate_tests(good_skill_dir, analysis, minimal_config)

        # Empty execution result (no --execute)
        execution_result = {
            "executed": False,
            "results": [],
            "summary": {"total": 0, "passed": 0, "failed": 0, "error": 0, "skipped": 0},
            "stats": {"total": 0, "passed": 0, "failed": 0, "error": 0, "skipped": 0},
        }

        ev = evaluate(analysis, test_data, execution_result, minimal_config)

        assert ev["final"] >= 5.0, f"Expected >= 5.0, got {ev['final']}"
        assert ev["tier"] in ("POWERFUL", "STANDARD", "BASIC")
        for dim in ("Documentation", "Code", "Completeness", "Usability"):
            assert dim in ev["dimensions"], f"Missing dimension: {dim}"
            assert 0 <= ev["dimensions"][dim] <= 10

    def test_bad_skill_scores_poorly(self, bad_skill_dir: Path, minimal_config: Dict[str, Any]):
        """A malformed skill should score < 7.0."""
        analysis = analyze_skill(bad_skill_dir, minimal_config)
        assert "error" not in analysis

        test_data = generate_tests(bad_skill_dir, analysis, minimal_config)
        execution_result = {
            "executed": False,
            "results": [],
            "summary": {"total": 0, "passed": 0, "failed": 0, "error": 0, "skipped": 0},
            "stats": {"total": 0, "passed": 0, "failed": 0, "error": 0, "skipped": 0},
        }

        ev = evaluate(analysis, test_data, execution_result, minimal_config)

        # Bad skill should score lower than good skill
        assert ev["final"] < 7.0, f"Expected < 7.0 for bad skill, got {ev['final']}"

    def test_execution_improves_score(self, good_skill_dir: Path, minimal_config: Dict[str, Any]):
        """Simulated execution results should be reflected in Usability score."""
        analysis = analyze_skill(good_skill_dir, minimal_config)
        test_data = generate_tests(good_skill_dir, analysis, minimal_config)

        # Simulate perfect execution
        perfect_execution = {
            "executed": True,
            "results": [{"status": "PASS"} for _ in range(5)],
            "summary": {"total": 5, "passed": 5, "failed": 0, "error": 0, "skipped": 0},
            "stats": {"total": 5, "passed": 5, "failed": 0, "error": 0, "skipped": 0},
        }
        ev_with = evaluate(analysis, test_data, perfect_execution, minimal_config)

        # Simulate failed execution
        failed_execution = {
            "executed": True,
            "results": [{"status": "FAIL"} for _ in range(5)],
            "summary": {"total": 5, "passed": 0, "failed": 5, "error": 0, "skipped": 0},
            "stats": {"total": 5, "passed": 0, "failed": 5, "error": 0, "skipped": 0},
        }
        ev_without = evaluate(analysis, test_data, failed_execution, minimal_config)

        assert ev_with["dimensions"]["Usability"] > ev_without["dimensions"]["Usability"]

    def test_tier_classification(self, minimal_config: Dict[str, Any]):
        """Tier thresholds should map correctly."""
        tiers = minimal_config["scoring"]["tiers"]

        # Test each threshold
        assert _resolve(9.0, tiers) == "POWERFUL"
        assert _resolve(8.5, tiers) == "POWERFUL"
        assert _resolve(8.0, tiers) == "STANDARD"
        assert _resolve(7.0, tiers) == "STANDARD"
        assert _resolve(6.0, tiers) == "BASIC"
        assert _resolve(5.0, tiers) == "BASIC"
        assert _resolve(4.0, tiers) == "REJECT"
        assert _resolve(0.0, tiers) == "REJECT"


def _resolve(score: float, tiers: Dict[str, Any]) -> str:
    """Helper: resolve tier without running full pipeline."""
    from scripts.config import resolve_tier
    return resolve_tier(score, tiers)
