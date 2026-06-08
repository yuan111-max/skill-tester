"""Tests for the Stage 1 analysis module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from scripts.analyze import analyze_skill


class TestAnalyzeSkill:
    """Integration-level tests for analyze_skill()."""

    def test_good_skill_analysis(self, good_skill_dir: Path, minimal_config: Dict[str, Any]):
        """A well-formed skill should produce no critical issues."""
        result = analyze_skill(good_skill_dir, minimal_config)

        assert "error" not in result
        assert result["name"] == "example-validator"
        assert "YAML" in result["description"]
        assert len(result["issues"]) == 0
        assert result["has_todo"] is False

    def test_bad_skill_analysis(self, bad_skill_dir: Path, minimal_config: Dict[str, Any]):
        """A malformed skill should produce issues."""
        result = analyze_skill(bad_skill_dir, minimal_config)

        assert "error" not in result
        assert result["name"] == "BAD-SKILL"
        assert len(result["issues"]) > 0
        assert result["has_todo"] is True

    def test_missing_skill_dir(self, tmp_path: Path, minimal_config: Dict[str, Any]):
        """Missing SKILL.md should return an error dict."""
        result = analyze_skill(tmp_path / "nonexistent", minimal_config)
        assert "error" in result

    def test_content_structure(self, good_skill_dir: Path, minimal_config: Dict[str, Any]):
        """Content structure analysis should identify sections and examples."""
        result = analyze_skill(good_skill_dir, minimal_config)

        content = result["content"]
        assert content["section_count"] >= 5
        assert content["example_count"] >= 2
        assert "when to use" in (s.lower() for s in content["sections"])

    def test_bundle_analysis(self, good_skill_dir: Path, minimal_config: Dict[str, Any]):
        """Bundle analysis should report bundle dir contents."""
        result = analyze_skill(good_skill_dir, minimal_config)
        bundle = result["bundle"]
        assert isinstance(bundle["scripts_count"], int)
        assert isinstance(bundle["references_count"], int)
        assert isinstance(bundle["assets_count"], int)

    def test_anti_pattern_detection(self, bad_skill_dir: Path, minimal_config: Dict[str, Any]):
        """Anti-pattern scanner should catch placeholders and template artifacts."""
        result = analyze_skill(bad_skill_dir, minimal_config)

        aps = result["anti_patterns"]
        types_found = {ap["type"] for ap in aps}

        assert "placeholder" in types_found
        assert result["has_todo"] is True

    def test_frontmatter_validation(self, bad_skill_dir: Path, minimal_config: Dict[str, Any]):
        """Frontmatter validator should catch naming issues."""
        result = analyze_skill(bad_skill_dir, minimal_config)

        name_issues = [i for i in result["issues"] if "name" in i.lower()]
        assert len(name_issues) > 0  # BAD-SKILL is not lowercase-hyphenated

    def test_trigger_analysis(self, good_skill_dir: Path, minimal_config: Dict[str, Any]):
        """Trigger analysis should extract trigger phrases."""
        result = analyze_skill(good_skill_dir, minimal_config)

        trig = result["trigger_info"]
        assert trig["trigger_count"] >= 3
        assert any("commit" in p.lower() for p in trig["trigger_phrases"])
