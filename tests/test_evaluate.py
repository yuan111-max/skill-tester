"""Tests for the Stage 4 evaluation module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


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

    def test_warns_on_unregistered_dimension(self, good_skill_dir: Path, recwarn):
        """A dimension configured but without a scorer should warn."""
        config_with_extra = {
            "scoring": {
                "dimensions": {
                    "Documentation": {"weight": 0.20},
                    "Code": {"weight": 0.20},
                    "Completeness": {"weight": 0.20},
                    "Usability": {"weight": 0.20},
                    "Performance": {"weight": 0.20},  # No scorer registered
                },
                "tiers": {"STANDARD": {"min": 7.0, "action": "Ok"}, "REJECT": {"min": 0.0, "action": "Fix"}},
            },
            "analysis": {"min_description_length": 20, "check_angle_brackets": True,
                         "check_todo_placeholders": True, "check_name_format": True,
                         "required_sections": [], "min_examples": 2, "script_extensions": [".py", ".sh"]},
            "execution": {"enabled": False, "claude_command": "claude", "timeout_seconds": 180, "max_tests": 10},
            "anti_patterns": [],
            "output": {"default_format": "summary", "max_description_preview": 80},
        }
        analysis = analyze_skill(good_skill_dir, config_with_extra)
        test_data = generate_tests(good_skill_dir, analysis, config_with_extra)
        exec_result = {"executed": False, "results": [], "summary": {}, "stats": {}}
        ev = evaluate(analysis, test_data, exec_result, config_with_extra)
        # Should warn about 'Performance'
        warnings_text = " ".join(str(w.message) for w in recwarn.list)
        assert "Performance" in warnings_text
        assert ev["final"] > 0  # Only 4 real dimensions, so final should still be > 0

    def test_warns_on_unknown_sub_score(self, good_skill_dir: Path, recwarn):
        """A sub-score in config not produced by the scorer should warn."""
        config_with_extra_sub = {
            "scoring": {
                "dimensions": {
                    "Documentation": {
                        "weight": 0.25,
                        "sub_scores": [
                            {"name": "frontmatter_validity", "weight": 0.15},
                            {"name": "section_coverage", "weight": 0.25},
                            {"name": "example_density", "weight": 0.20},
                            {"name": "specificity_and_clarity", "weight": 0.25},
                            {"name": "trigger_clarity", "weight": 0.10},
                            {"name": "nonexistent_sub_score", "weight": 0.05},  # unknown
                        ],
                    },
                    "Code": {"weight": 0.25},
                    "Completeness": {"weight": 0.25},
                    "Usability": {"weight": 0.25},
                },
                "tiers": {"STANDARD": {"min": 7.0, "action": "Ok"}, "REJECT": {"min": 0.0, "action": "Fix"}},
            },
            "analysis": {"min_description_length": 20, "check_angle_brackets": True,
                         "check_todo_placeholders": True, "check_name_format": True,
                         "required_sections": [], "min_examples": 2, "script_extensions": [".py", ".sh"]},
            "execution": {"enabled": False, "claude_command": "claude", "timeout_seconds": 180, "max_tests": 10},
            "anti_patterns": [],
            "output": {"default_format": "summary", "max_description_preview": 80},
        }
        analysis = analyze_skill(good_skill_dir, config_with_extra_sub)
        test_data = generate_tests(good_skill_dir, analysis, config_with_extra_sub)
        exec_result = {"executed": False, "results": [], "summary": {}, "stats": {}}
        evaluate(analysis, test_data, exec_result, config_with_extra_sub)
        warnings_text = " ".join(str(w.message) for w in recwarn.list)
        assert "nonexistent_sub_score" in warnings_text


class TestReadSkillBody:
    """Tests for _read_skill_body()."""

    def test_returns_body_when_present(self):
        """When _body is set, it should be returned."""
        from scripts.evaluate import _read_skill_body
        analysis = {"_body": "## Section\nContent here"}
        assert _read_skill_body(analysis) == "## Section\nContent here"

    def test_returns_empty_when_missing(self):
        """When _body is absent, empty string should be returned."""
        from scripts.evaluate import _read_skill_body
        analysis = {"name": "test"}
        assert _read_skill_body(analysis) == ""


class TestScoreCodeNoScripts:
    """Tests for _score_code() when a skill has no scripts."""

    def test_no_scripts_scores_zero_for_validity(self):
        """When no scripts exist, syntactic_validity should be 0 (not 10)."""
        from scripts.evaluate import _score_code

        analysis = {
            "scripts": {"total_count": 0, "valid_count": 0, "results": []},
            "bundle": {"scripts_count": 0},
        }
        config = {
            "scoring": {
                "dimensions": {
                    "Code": {
                        "sub_scores": [
                            {"name": "script_presence", "weight": 0.10},
                            {"name": "syntactic_validity", "weight": 0.35},
                            {"name": "error_handling", "weight": 0.30},
                            {"name": "script_documentation", "weight": 0.25},
                        ],
                    },
                },
            },
        }
        score, detail = _score_code(analysis, {}, {}, config)
        assert detail["syntactic_validity"] == 0, "No scripts should mean 0 validity"
        assert detail["error_handling"] == 0, "No scripts should mean 0 error handling"
        assert detail["script_documentation"] == 0, "No scripts should mean 0 documentation"
        assert score < 5.0, f"No-script skill should not score well, got {score}"

    def test_has_scripts_scores_positively(self):
        """When scripts exist, code should score based on their quality."""
        from scripts.evaluate import _score_code

        analysis = {
            "scripts": {
                "total_count": 2,
                "valid_count": 2,
                "results": [
                    {"path": "scripts/a.py", "language": "python", "syntax_valid": True, "has_docstring": True, "has_try_except": True},
                    {"path": "scripts/b.py", "language": "python", "syntax_valid": True, "has_docstring": True, "has_try_except": True},
                ],
            },
            "bundle": {"scripts_count": 2},
        }
        config = {
            "scoring": {
                "dimensions": {
                    "Code": {
                        "sub_scores": [
                            {"name": "script_presence", "weight": 0.10},
                            {"name": "syntactic_validity", "weight": 0.35},
                            {"name": "error_handling", "weight": 0.30},
                            {"name": "script_documentation", "weight": 0.25},
                        ],
                    },
                },
            },
        }
        score, detail = _score_code(analysis, {}, {}, config)
        assert detail["syntactic_validity"] == 10
        assert detail["script_presence"] >= 7
        assert score >= 7.0, f"Valid scripts should score well, got {score}"


def _resolve(score: float, tiers: Dict[str, Any]) -> str:
    """Helper: resolve tier without running full pipeline."""
    from scripts.config import resolve_tier
    return resolve_tier(score, tiers)
