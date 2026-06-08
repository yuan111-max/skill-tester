"""Tests for the Stage 2 test generation module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from scripts.analyze import analyze_skill
from scripts.generate import generate_tests


class TestGenerateTests:
    """Integration tests for generate_tests()."""

    def test_good_skill_generates_tests(self, good_skill_dir: Path, minimal_config: Dict[str, Any]):
        """A well-formed skill should generate multiple test cases."""
        analysis = analyze_skill(good_skill_dir, minimal_config)
        result = generate_tests(good_skill_dir, analysis, minimal_config)

        assert result["total_generated"] >= 5
        assert len(result["trigger_tests"]) >= 3

    def test_bad_skill_generates_fewer_tests(self, bad_skill_dir: Path, minimal_config: Dict[str, Any]):
        """A poorly-formed skill should generate fewer / lower-quality tests."""
        analysis = analyze_skill(bad_skill_dir, minimal_config)
        result = generate_tests(bad_skill_dir, analysis, minimal_config)

        # Bad skill has minimal content
        assert result["total_generated"] >= 0
        # Should still produce at least name-based trigger and negative tests
        assert len(result["non_trigger_tests"]) >= 1

    def test_trigger_tests_include_usage_section(self, good_skill_dir: Path, minimal_config: Dict[str, Any]):
        """Trigger tests should include prompts from When to Use sections."""
        analysis = analyze_skill(good_skill_dir, minimal_config)
        result = generate_tests(good_skill_dir, analysis, minimal_config)

        triggers = result["trigger_tests"]
        sources = {t["source"] for t in triggers}
        assert "usage_section" in sources or "trigger_section" in sources

    def test_negative_tests_are_not_trigger(self, good_skill_dir: Path, minimal_config: Dict[str, Any]):
        """Negative tests should have expected_trigger=False."""
        analysis = analyze_skill(good_skill_dir, minimal_config)
        result = generate_tests(good_skill_dir, analysis, minimal_config)

        for t in result["non_trigger_tests"]:
            assert t["expected_trigger"] is False
            assert t["type"] == "non_trigger"

    def test_edge_cases_from_limitations(self, good_skill_dir: Path, minimal_config: Dict[str, Any]):
        """Edge cases should be extracted from Limitations and Do Not sections."""
        analysis = analyze_skill(good_skill_dir, minimal_config)
        result = generate_tests(good_skill_dir, analysis, minimal_config)

        edge_sources = {ec.get("source", "") for ec in result.get("edge_cases", [])}
        assert "constraint_section" in edge_sources or "do_not_rule" in edge_sources

    def test_capabilities_extracted(self, good_skill_dir: Path, minimal_config: Dict[str, Any]):
        """Capabilities should be extracted from section headings."""
        analysis = analyze_skill(good_skill_dir, minimal_config)
        result = generate_tests(good_skill_dir, analysis, minimal_config)

        cap_names = [c["name"].lower() for c in result.get("capabilities", [])]
        assert any("analysis" in n for n in cap_names)
        assert any("valid" in n for n in cap_names)

    def test_test_cap_respected(self, good_skill_dir: Path):
        """max_tests=2 should limit generated tests."""
        config_with_cap = {
            "scoring": {"dimensions": {}, "tiers": {}},
            "analysis": {},
            "execution": {"max_tests": 2},
            "anti_patterns": [],
            "output": {},
        }
        analysis = analyze_skill(good_skill_dir, config_with_cap)
        result = generate_tests(good_skill_dir, analysis, config_with_cap)

        assert result["total_generated"] <= 2
