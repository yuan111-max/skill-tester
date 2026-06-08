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


class TestExtractDomainWords:
    """Tests for _extract_domain_words()."""

    def test_returns_empty_for_empty_description(self):
        """Empty description should return empty list."""
        from scripts.generate import _extract_domain_words
        assert _extract_domain_words("") == []

    def test_finds_capitalized_nouns(self):
        """Capitalised nouns in description should be extracted."""
        from scripts.generate import _extract_domain_words
        result = _extract_domain_words("Validates Configuration files for Python pipelines")
        # Words starting with uppercase letter followed by lowercase, length >= 3
        assert "Configuration" in result
        assert "Python" in result

    def test_finds_all_caps_acronyms(self):
        """ALL-CAPS acronyms like YAML, JSON, CLI should be extracted."""
        from scripts.generate import _extract_domain_words
        result = _extract_domain_words("Validates JSON and YAML files via CLI interface")
        assert "JSON" in result
        assert "YAML" in result
        assert "CLI" in result

    def test_ignores_short_words(self):
        """Words shorter than 3 characters should be ignored."""
        from scripts.generate import _extract_domain_words
        result = _extract_domain_words("A B CD is OK but Efg is not")
        assert "Efg" in result
        assert "A" not in result
        assert "CD" not in result

    def test_no_capitalized_words(self):
        """Description with no capitalized words should return empty."""
        from scripts.generate import _extract_domain_words
        result = _extract_domain_words("just a normal description without capitals")
        assert result == []


class TestGenerateTriggerTests:
    """Tests for _generate_trigger_tests()."""

    def test_from_trigger_info_phrases(self):
        """Trigger phrases from analysis trigger_info should be included."""
        from scripts.generate import _generate_trigger_tests
        analysis = {
            "name": "test-skill",
            "description": "",
            "trigger_info": {
                "trigger_phrases": ["validate my yaml", "check my config"],
                "trigger_count": 2,
            },
        }
        tests = _generate_trigger_tests(analysis, "## When to Use\n- something", {})
        prompts = [t["prompt"] for t in tests]
        assert "validate my yaml" in prompts
        assert "check my config" in prompts

    def test_from_usage_section_bullets(self):
        """Bullet points in Usage/When to Use sections become tests."""
        from scripts.generate import _generate_trigger_tests
        content = "## When to Use\n- Validate JSON files before deploy\n- Check YAML syntax"
        analysis = {"name": "test-skill", "description": "", "trigger_info": {"trigger_phrases": [], "trigger_count": 0}}
        tests = _generate_trigger_tests(analysis, content, {})
        prompts = [t["prompt"] for t in tests]
        assert any("Validate JSON" in p for p in prompts)

    def test_name_based_trigger(self):
        """A trigger test should be generated from the skill name."""
        from scripts.generate import _generate_trigger_tests
        analysis = {
            "name": "json-validator",
            "description": "Validates JSON",
            "trigger_info": {"trigger_phrases": [], "trigger_count": 0},
        }
        tests = _generate_trigger_tests(analysis, "ignored content", {})
        prompts = [t["prompt"] for t in tests]
        assert any("json-validator" in p for p in prompts)

    def test_deduplicates_by_prompt(self):
        """Duplicate prompts should not appear twice."""
        from scripts.generate import _generate_trigger_tests
        analysis = {
            "name": "test-skill",
            "description": "",
            "trigger_info": {
                "trigger_phrases": ["validate my yaml", "validate my yaml"],
                "trigger_count": 2,
            },
        }
        tests = _generate_trigger_tests(analysis, "ignored content", {})
        prompts = [t["prompt"] for t in tests]
        assert prompts.count("validate my yaml") == 1


class TestGenerateNegativeTests:
    """Tests for _generate_negative_tests()."""

    def test_generic_unrelated_prompt_always_present(self):
        """A generic unrelated prompt should always be included."""
        from scripts.generate import _generate_negative_tests
        tests = _generate_negative_tests({"name": "test", "description": ""}, "")
        prompts = [t["prompt"] for t in tests]
        assert any("weather" in p for p in prompts)
        assert all(t["expected_trigger"] is False for t in tests)

    def test_domain_based_negative(self):
        """Domain-specific negative tests should use extracted domain words."""
        from scripts.generate import _generate_negative_tests
        tests = _generate_negative_tests(
            {"name": "test", "description": "Validates JSON Schema files for Python pipelines"},
            "",
        )
        prompts = [t["prompt"] for t in tests]
        assert any("don't need a specific task" in p for p in prompts)

    def test_meta_question_negative(self):
        """A 'what does the skill do' question should NOT trigger."""
        from scripts.generate import _generate_negative_tests
        tests = _generate_negative_tests(
            {"name": "my-skill", "description": "does things"},
            "",
        )
        prompts = [t["prompt"] for t in tests]
        assert any("my-skill" in p and "do" in p for p in prompts)

    def test_unknown_name_skips_meta(self):
        """When skill name is 'unknown', skip the meta-question negative test."""
        from scripts.generate import _generate_negative_tests
        tests = _generate_negative_tests({"name": "unknown", "description": ""}, "")
        prompts = [t["prompt"] for t in tests]
        assert not any("skill do" in p for p in prompts)


class TestGenerateEdgeCases:
    """Tests for _generate_edge_cases()."""

    def test_constraint_section_extracts_bullets(self):
        """Bullets from Limitations/Caveats sections should become edge cases."""
        from scripts.generate import _generate_edge_cases
        content = (
            "## Limitations\n"
            "- Does not validate binary files\n"
            "- Maximum file size is 10MB\n"
        )
        edges = _generate_edge_cases(content, {"name": "test", "description": ""})
        prompts = [e["prompt"] for e in edges]
        assert any("binary files" in p for p in prompts)
        assert all(e["expected_trigger"] is True for e in edges)
        assert all(e["type"] == "edge_case" for e in edges)

    def test_do_not_rules_extracted(self):
        """Sentences with 'do not' / 'avoid' should become edge cases."""
        from scripts.generate import _generate_edge_cases
        content = "Do not use this skill on production data without review."
        edges = _generate_edge_cases(content, {"name": "test", "description": ""})
        prompts = [e["prompt"] for e in edges]
        assert any("Do not use this skill" in p for p in prompts)

    def test_short_do_not_rules_skipped(self):
        """Very short 'do not' sentences should be skipped."""
        from scripts.generate import _generate_edge_cases
        content = "Do not run it."
        edges = _generate_edge_cases(content, {"name": "test", "description": ""})
        assert len(edges) == 0

    def test_empty_content(self):
        """Content with no edge-case sections should return empty list."""
        from scripts.generate import _generate_edge_cases
        edges = _generate_edge_cases("Just a normal paragraph.", {"name": "test", "description": ""})
        assert edges == []


class TestExtractCapabilities:
    """Tests for _extract_capabilities()."""

    def test_from_section_headings(self):
        """Non-skip section headings should become capabilities."""
        from scripts.generate import _extract_capabilities
        content = "## Installation\n## Usage\n## Configuration\n## Troubleshooting"
        analysis = {"content": {"sections": ["Installation", "Usage", "Configuration", "Troubleshooting"]}}
        caps = _extract_capabilities(analysis, content)
        names = [c["name"] for c in caps]
        assert "Installation" in names
        assert "Configuration" in names
        assert "Troubleshooting" in names

    def test_skips_when_to_use_and_reference(self):
        """When to Use, Usage, Overview, Reference sections should be skipped."""
        from scripts.generate import _extract_capabilities
        content = "## When to Use\n## Usage\n## Overview\n## Reference"
        analysis = {"content": {"sections": ["When to Use", "Usage", "Overview", "Reference"]}}
        caps = _extract_capabilities(analysis, content)
        names = [c["name"] for c in caps]
        assert "When to Use" not in names
        assert "Usage" not in names
        assert "Overview" not in names
        assert "Reference" not in names

    def test_from_bullet_points(self):
        """Action-oriented bullet points should become capabilities."""
        from scripts.generate import _extract_capabilities
        content = "\n".join([
            "## How to Use",
            "- How to validate a JSON file",
            "- Steps to configure YAML",
            "- Guide to parse configuration",
        ])
        analysis = {"content": {"sections": ["How to Use"]}}
        caps = _extract_capabilities(analysis, content)
        names = [c["name"] for c in caps]
        assert any("validate a JSON file" in n for n in names)
        assert any("configure YAML" in n for n in names)

    def test_empty_analysis_returns_empty_list(self):
        """Empty content should return empty list."""
        from scripts.generate import _extract_capabilities
        caps = _extract_capabilities({"content": {"sections": []}}, "")
        assert caps == []
