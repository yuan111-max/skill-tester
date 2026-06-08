"""Tests for the CLI entry point and pipeline orchestrator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from scripts.run_tests import _run_pipeline, build_parser, main


# ── Fixtures & helpers ────────────────────────────────────────────────────────


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
GOOD_SKILL = FIXTURES_DIR / "good_skill"


def _mock_stage_result(name: str) -> Dict[str, Any]:
    """Return a realistic stage result dict."""
    if name == "analysis":
        return {
            "name": "good-skill",
            "description": "A well-formed test skill",
            "frontmatter": {"name": "good-skill", "description": "A well-formed test skill"},
            "content": {
                "sections": ["When to Use", "Stage", "Installation", "Configuration", "Examples", "Troubleshooting"],
                "section_count": 6,
                "example_count": 3,
                "line_count": 120,
                "missing_required_sections": [],
                "issues": [],
            },
            "bundle": {"scripts_count": 1, "references_count": 0, "assets_count": 0},
            "anti_patterns": [],
            "trigger_info": {"trigger_phrases": ["validate json", "check config"], "trigger_count": 2},
            "scripts": {"results": [], "valid_count": 0, "total_count": 0},
            "issues": [],
            "has_todo": False,
        }
    if name == "generate":
        return {
            "tests": [
                {"prompt": "validate my config", "expected_trigger": True, "type": "trigger", "source": "usage_section"},
                {"prompt": "what is the weather", "expected_trigger": False, "type": "non_trigger", "source": "generic_unrelated"},
            ],
            "trigger_tests": [{"prompt": "validate my config", "expected_trigger": True, "type": "trigger"}],
            "non_trigger_tests": [{"prompt": "what is the weather", "expected_trigger": False, "type": "non_trigger"}],
            "edge_cases": [],
            "capabilities": [{"name": "YAML Validation", "source": "section_heading"}],
            "total_generated": 2,
        }
    if name == "execute":
        return {
            "executed": True,
            "results": [
                {"prompt": "validate my config", "status": "PASS", "triggered": True, "elapsed_seconds": 1.2},
                {"prompt": "what is the weather", "status": "PASS", "triggered": False, "elapsed_seconds": 0.8},
            ],
            "summary": {"total": 2, "passed": 2, "failed": 0, "error": 0, "skipped": 0},
            "stats": {"total": 2, "passed": 2, "failed": 0, "error": 0, "skipped": 0},
        }
    if name == "evaluate":
        return {
            "dimensions": {"Documentation": 8.5, "Code": 7.2, "Completeness": 6.8, "Usability": 9.1},
            "details": {},
            "final": 7.90,
            "tier": "STANDARD",
        }
    return {}


def _make_config() -> Dict[str, Any]:
    """Return a minimal config for pipeline testing."""
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
            "script_extensions": [".py", ".sh"],
        },
        "execution": {
            "enabled": False,
            "claude_command": "claude",
            "timeout_seconds": 180,
            "max_tests": 10,
        },
        "anti_patterns": [],
        "output": {"default_format": "summary", "max_description_preview": 80},
    }


# ── Tests: build_parser ─────────────────────────────────────────────────────


class TestBuildParser:
    """Tests for build_parser()."""

    def test_returns_argparse_parser(self):
        """Should return an ArgumentParser instance."""
        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_requires_at_least_one_skill_dir(self):
        """Should require at least one positional argument."""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_accepts_single_skill_dir(self):
        """A single directory should be accepted."""
        parser = build_parser()
        args = parser.parse_args(["/tmp/skill"])
        assert len(args.skill_dirs) == 1
        assert args.skill_dirs[0] == Path("/tmp/skill")

    def test_accepts_multiple_skill_dirs(self):
        """Multiple directories should be accepted."""
        parser = build_parser()
        args = parser.parse_args(["/tmp/a", "/tmp/b", "/tmp/c"])
        assert len(args.skill_dirs) == 3

    def test_output_defaults_to_none(self):
        """--output should default to None (auto-detected later)."""
        parser = build_parser()
        args = parser.parse_args(["/tmp/skill"])
        assert args.output is None

    def test_output_choices(self):
        """--output should only accept valid choices."""
        parser = build_parser()
        args = parser.parse_args(["/tmp/skill", "--output", "json"])
        assert args.output == "json"

        args = parser.parse_args(["/tmp/skill", "-o", "table"])
        assert args.output == "table"

        with pytest.raises(SystemExit):
            parser.parse_args(["/tmp/skill", "--output", "html"])

    def test_execute_default_false(self):
        """--execute should default to False."""
        parser = build_parser()
        args = parser.parse_args(["/tmp/skill"])
        assert args.execute is False

    def test_execute_flag(self):
        """--execute should be settable via --execute or -e."""
        parser = build_parser()
        args = parser.parse_args(["/tmp/skill", "--execute"])
        assert args.execute is True

        args = parser.parse_args(["/tmp/skill", "-e"])
        assert args.execute is True

    def test_config_default_none(self):
        """--config should default to None."""
        parser = build_parser()
        args = parser.parse_args(["/tmp/skill"])
        assert args.config is None

    def test_config_path(self):
        """--config should accept a path."""
        parser = build_parser()
        args = parser.parse_args(["/tmp/skill", "--config", "/tmp/my-config.yaml"])
        assert args.config == Path("/tmp/my-config.yaml")

    def test_quiet_default_false(self):
        """--quiet should default to False."""
        parser = build_parser()
        args = parser.parse_args(["/tmp/skill"])
        assert args.quiet is False

    def test_quiet_flag(self):
        """--quiet should be settable via -q."""
        parser = build_parser()
        args = parser.parse_args(["/tmp/skill", "--quiet"])
        assert args.quiet is True

    def test_no_color_default_false(self):
        """--no-color should default to False."""
        parser = build_parser()
        args = parser.parse_args(["/tmp/skill"])
        assert args.no_color is False

    def test_no_color_flag(self):
        """--no-color should be settable."""
        parser = build_parser()
        args = parser.parse_args(["/tmp/skill", "--no-color"])
        assert args.no_color is True


# ── Tests: _run_pipeline ─────────────────────────────────────────────────────


class TestRunPipeline:
    """Tests for _run_pipeline()."""

    @patch("scripts.run_tests.analyze_skill")
    @patch("scripts.run_tests.generate_tests")
    @patch("scripts.run_tests.execute_tests")
    @patch("scripts.run_tests.evaluate")
    def test_full_pipeline_returns_report(
        self, mock_evaluate, mock_execute, mock_generate, mock_analyze
    ):
        """_run_pipeline should run all 4 stages and return a report dict."""
        mock_analyze.return_value = _mock_stage_result("analysis")
        mock_generate.return_value = _mock_stage_result("generate")
        mock_execute.return_value = _mock_stage_result("execute")
        mock_evaluate.return_value = _mock_stage_result("evaluate")

        config = _make_config()
        result = _run_pipeline(GOOD_SKILL, config, execute_enabled=False, quiet=True, use_color=False)

        assert result["skill"] == "good-skill"
        assert result["description"] == "A well-formed test skill"
        assert "evaluation" in result
        assert result["evaluation"]["final"] == 7.90
        assert result["evaluation"]["tier"] == "STANDARD"
        assert "execution" in result
        assert "tests" in result
        assert "issues" in result
        assert "elapsed" in result
        assert isinstance(result["elapsed"], float)

    @patch("scripts.run_tests.analyze_skill")
    def test_analysis_error_returns_early(self, mock_analyze):
        """When analysis returns an error, the pipeline should abort."""
        mock_analyze.return_value = {"error": "SKILL.md not found"}
        config = _make_config()
        result = _run_pipeline(GOOD_SKILL, config, execute_enabled=False, quiet=True, use_color=False)
        assert "error" in result
        assert result["error"] == "SKILL.md not found"
        assert "evaluation" not in result

    @patch("scripts.run_tests.analyze_skill")
    @patch("scripts.run_tests.evaluate")
    def test_quiet_mode_suppresses_print(self, mock_evaluate, mock_analyze, capsys):
        """When quiet=True, no stage output should appear on stderr."""
        mock_analyze.return_value = _mock_stage_result("analysis")
        mock_evaluate.return_value = _mock_stage_result("evaluate")

        with patch("scripts.run_tests.generate_tests", return_value=_mock_stage_result("generate")):
            with patch("scripts.run_tests.execute_tests", return_value=_mock_stage_result("execute")):
                _run_pipeline(GOOD_SKILL, _make_config(), execute_enabled=False, quiet=True, use_color=False)

        captured = capsys.readouterr()
        assert captured.err == ""

    @patch("scripts.run_tests.analyze_skill")
    def test_analysis_gets_skill_body(self, mock_analyze):
        """The SKILL.md body should be read once and passed to analyze_skill."""
        mock_analyze.return_value = _mock_stage_result("analysis")
        config = _make_config()

        with patch("scripts.run_tests.generate_tests", return_value=_mock_stage_result("generate")):
            with patch("scripts.run_tests.execute_tests", return_value=_mock_stage_result("execute")):
                with patch("scripts.run_tests.evaluate", return_value=_mock_stage_result("evaluate")):
                    _run_pipeline(GOOD_SKILL, config, execute_enabled=False, quiet=True, use_color=False)

        # analyze_skill is called with positional args: (skill_dir, config, content)
        # call_args[0] = positional args tuple, index 2 = content
        _call_content = mock_analyze.call_args[0][2]
        assert isinstance(_call_content, str)
        assert len(_call_content) > 0


# ── Tests: main ──────────────────────────────────────────────────────────────


class TestMain:
    """Tests for main()."""

    def test_exit_code_1_when_dir_not_found(self):
        """When a skill directory does not exist, exit code should be 1."""
        with patch.object(sys, "argv", ["run_tests.py", "/nonexistent/path"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1

    def test_exit_code_0_when_dir_found(self):
        """When a skill directory exists, exit code should be 0."""
        with patch.object(sys, "argv", ["run_tests.py", str(GOOD_SKILL)]):
            with patch("scripts.run_tests.load_config", return_value=_make_config()):
                with patch("scripts.run_tests._run_pipeline", return_value=_mock_stage_result("evaluate")):
                    with patch("scripts.run_tests.output_summary"):
                        with pytest.raises(SystemExit) as exc:
                            main()
                        assert exc.value.code == 0

    def test_invalid_dir_and_valid_dir(self):
        """A mix of invalid and valid dirs should still return exit code 1."""
        with patch.object(sys, "argv", ["run_tests.py", "/nonexistent", str(GOOD_SKILL)]):
            with patch("scripts.run_tests.load_config", return_value=_make_config()):
                with patch("scripts.run_tests._run_pipeline", return_value=_mock_stage_result("evaluate")):
                    with patch("scripts.run_tests.output_summary"):
                        with pytest.raises(SystemExit) as exc:
                            main()
                        assert exc.value.code == 1

    def test_json_output_calls_output_json(self):
        """With --output json, output_json should be called."""
        with patch.object(sys, "argv", ["run_tests.py", str(GOOD_SKILL), "--output", "json"]):
            with patch("scripts.run_tests.load_config", return_value=_make_config()):
                with patch("scripts.run_tests._run_pipeline", return_value=_mock_stage_result("evaluate")):
                    with patch("scripts.run_tests.output_json") as mock_json:
                        with pytest.raises(SystemExit):
                            main()
                        assert mock_json.called

    def test_table_output_for_multi_skill(self):
        """With multiple skills, output should default to table."""
        r1 = _mock_stage_result("evaluate")
        r2 = _mock_stage_result("evaluate")
        r2["skill"] = "another-skill"

        with patch.object(sys, "argv", ["run_tests.py", str(GOOD_SKILL), str(GOOD_SKILL)]):
            with patch("scripts.run_tests.load_config", return_value=_make_config()):
                with patch("scripts.run_tests._run_pipeline", side_effect=[r1, r2]):
                    with patch("scripts.run_tests.output_table") as mock_table:
                        with pytest.raises(SystemExit):
                            main()
                        assert mock_table.called

    def test_summary_output_for_single_skill(self):
        """With one skill, output should default to summary."""
        with patch.object(sys, "argv", ["run_tests.py", str(GOOD_SKILL)]):
            with patch("scripts.run_tests.load_config", return_value=_make_config()):
                with patch("scripts.run_tests._run_pipeline", return_value=_mock_stage_result("evaluate")):
                    with patch("scripts.run_tests.output_summary") as mock_summary:
                        with pytest.raises(SystemExit):
                            main()
                        assert mock_summary.called

    def test_no_color_flag_disables_color(self, monkeypatch):
        """--no-color should result in use_color=False passed to formatters."""
        with patch.object(sys, "argv", ["run_tests.py", str(GOOD_SKILL), "--no-color"]):
            with patch("scripts.run_tests.load_config", return_value=_make_config()):
                with patch("scripts.run_tests._run_pipeline") as mock_pipeline:
                    mock_pipeline.return_value = _mock_stage_result("evaluate")
                    with patch("scripts.run_tests.output_summary"):
                        with patch("scripts.run_tests.stdout_is_tty", return_value=True):
                            with pytest.raises(SystemExit):
                                main()
                            # _run_pipeline is called with positional args:
                            # (skill_dir, config, execute_enabled, quiet, use_color)
                            # use_color is the 5th positional arg (index 4)
                            args, _ = mock_pipeline.call_args
                            assert args[4] is False  # use_color=False
