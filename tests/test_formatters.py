"""Tests for output formatters."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch


from scripts.formatters import (
    _print_table_row,
    color_tier,
    output_json,
    output_summary,
    output_table,
    print_stage,
    stdout_is_tty,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _make_report(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
    """Build a standard evaluation report dict."""
    report = {
        "skill": "test-skill",
        "description": "A test skill for validating formatters",
        "issues": ["Missing examples section"],
        "anti_patterns": [
            {"type": "placeholder", "severity": "high", "message": "TODO found", "match": "TODO", "line": 10},
        ],
        "bundle": {"scripts_count": 2, "references_count": 1, "assets_count": 0},
        "tests": {"total_generated": 5},
        "execution": {
            "executed": True,
            "summary": {"total": 5, "passed": 4, "failed": 1, "error": 0, "skipped": 0},
        },
        "evaluation": {
            "dimensions": {
                "Documentation": 8.5,
                "Code": 7.2,
                "Completeness": 6.8,
                "Usability": 9.1,
            },
            "final": 7.90,
            "tier": "STANDARD",
        },
        "elapsed": 3.45,
    }
    if overrides:
        report.update(overrides)
    return report


def _make_second_report() -> Dict[str, Any]:
    """A second report for table comparisons."""
    return {
        "skill": "another-skill",
        "description": "Another skill for comparison",
        "issues": [],
        "anti_patterns": [],
        "bundle": {"scripts_count": 1, "references_count": 0, "assets_count": 0},
        "tests": {"total_generated": 3},
        "execution": {
            "executed": False,
            "summary": {"total": 3, "passed": 0, "failed": 0, "error": 0, "skipped": 3},
            "skip_reason": "Execution disabled",
        },
        "evaluation": {
            "dimensions": {
                "Documentation": 6.0,
                "Code": 5.5,
                "Completeness": 5.0,
                "Usability": 6.5,
            },
            "final": 5.75,
            "tier": "BASIC",
        },
        "elapsed": 2.10,
    }


# ── Tests: output_json ───────────────────────────────────────────────────────


class TestOutputJson:
    """Tests for output_json()."""

    def test_single_report_prints_valid_json(self, capsys):
        """A single report should produce valid JSON with expected keys."""
        report = _make_report()
        output_json([report], [Path("/tmp/skill")])
        captured = capsys.readouterr().out
        data = json.loads(captured)
        assert isinstance(data, list)
        assert len(data) == 1
        item = data[0]
        assert item["skill"] == "test-skill"
        # Path on Windows uses backslashes
        assert "tmp" in item["path"] and "skill" in item["path"]
        assert "evaluation" in item
        assert "elapsed_seconds" in item

    def test_multiple_reports(self, capsys):
        """Multiple reports should all appear in the JSON array."""
        r1 = _make_report()
        r2 = _make_second_report()
        output_json([r1, r2], [Path("/tmp/a"), Path("/tmp/b")])
        captured = capsys.readouterr().out
        data = json.loads(captured)
        assert len(data) == 2
        assert data[0]["skill"] == "test-skill"
        assert data[1]["skill"] == "another-skill"

    def test_report_with_error_includes_error_key(self, capsys):
        """A report with an 'error' key should include it in JSON output."""
        report = _make_report({"error": "SKILL.md not found"})
        output_json([report], [Path("/tmp/skill")])
        captured = capsys.readouterr().out
        data = json.loads(captured)
        assert data[0]["error"] == "SKILL.md not found"

    def test_ensure_ascii_false_allows_unicode(self, capsys):
        """Unicode characters should not be escaped."""
        report = _make_report({"skill": "中文技能"})
        output_json([report], [Path("/tmp/skill")])
        captured = capsys.readouterr().out
        assert "中文技能" in captured


# ── Tests: output_table ──────────────────────────────────────────────────────


class TestOutputTable:
    """Tests for output_table()."""

    def test_single_skill_still_prints_table(self, capsys):
        """Even a single skill should produce a table."""
        report = _make_report()
        output_table([report], [Path("/tmp/skill")], use_color=False)
        captured = capsys.readouterr().out
        assert "SKILL COMPARISON" in captured
        assert "Documentation" in captured
        assert "FINAL" in captured
        assert "STANDARD" in captured

    def test_multiple_skills_comparison(self, capsys):
        """Two skills should show rows for each dimension plus final row."""
        r1 = _make_report()
        r2 = _make_second_report()
        output_table([r1, r2], [Path("/tmp/a"), Path("/tmp/b")], use_color=False)
        captured = capsys.readouterr().out
        assert "SKILL COMPARISON" in captured
        assert "Documentation" in captured
        assert "Completeness" in captured
        assert "FINAL" in captured
        assert "7.90" in captured
        assert "STANDARD" in captured
        assert "BASIC" in captured
        assert "Issues" in captured
        assert "Elapsed (s)" in captured

    def test_empty_reports_prints_nothing(self, capsys):
        """Empty report list should produce no output."""
        output_table([], [], use_color=False)
        captured = capsys.readouterr().out
        assert captured == ""


# ── Tests: output_summary ────────────────────────────────────────────────────


class TestOutputSummary:
    """Tests for output_summary()."""

    def test_error_report_prints_error(self, capsys):
        """A report with an 'error' key should print the error message."""
        report = _make_report({"error": "Something went wrong"})
        output_summary(report, Path("/tmp/skill"), use_color=False)
        captured = capsys.readouterr().out
        assert "Something went wrong" in captured
        assert "Skill Tester Report" not in captured  # no normal header

    def test_normal_report_contains_all_sections(self, capsys):
        """A normal report should contain name, scores, bundle info, etc."""
        report = _make_report()
        output_summary(report, Path("/tmp/skill"), use_color=False)
        captured = capsys.readouterr().out
        assert "Skill Tester Report: test-skill" in captured
        assert "8.5" in captured  # Documentation score
        assert "7.90" in captured  # Final score
        assert "STANDARD" in captured
        assert "scripts=2" in captured
        assert "Tests generated: 5" in captured
        assert "4/5" in captured  # execution passed/total
        assert "Missing examples section" in captured  # issues list
        assert "anti-pattern" in captured.lower()

    def test_summary_shows_skipped_when_not_executed(self, capsys):
        """A report without execution should say SKIPPED."""
        report = _make_report()
        report["execution"]["executed"] = False
        report["execution"]["skip_reason"] = "use --execute to enable"
        output_summary(report, Path("/tmp/skill"), use_color=False)
        captured = capsys.readouterr().out
        assert "SKIPPED" in captured

    def test_no_issues_shows_ok(self, capsys):
        """A report with zero issues should show [OK]."""
        report = _make_report({"issues": []})
        output_summary(report, Path("/tmp/skill"), use_color=False)
        captured = capsys.readouterr().out
        assert "[OK] No structural issues found" in captured

    def test_many_issues_truncated(self, capsys):
        """More than 5 issues should be truncated with a note."""
        report = _make_report({"issues": [f"Issue {i}" for i in range(10)]})
        output_summary(report, Path("/tmp/skill"), use_color=False)
        captured = capsys.readouterr().out
        assert "... and 5 more" in captured

    def test_uses_color_when_requested(self, capsys):
        """With use_color=True, ANSI escape codes should appear."""
        report = _make_report()
        output_summary(report, Path("/tmp/skill"), use_color=True)
        captured = capsys.readouterr().out
        assert "\033[" in captured  # some ANSI code present


# ── Tests: _print_table_row ──────────────────────────────────────────────────


class TestPrintTableRow:
    """Tests for _print_table_row()."""

    def test_prints_fixed_width_columns(self, capsys):
        """Each cell should be padded to the given width."""
        _print_table_row(["A", "B"], width=10)
        captured = capsys.readouterr().out
        # Each cell takes 10 chars: "A         " + "B         "
        # But no explicit separator, just concatenation
        assert len(captured.rstrip("\n")) == 20

    def test_bold_wraps_in_ansi(self, capsys):
        """When bold=True, ANSI bold codes should wrap the line."""
        _print_table_row(["Hi"], width=5, bold=True)
        captured = capsys.readouterr().out
        assert "\033[1m" in captured
        assert "\033[0m" in captured

    def test_no_bold_no_ansi(self, capsys):
        """When bold=False, no ANSI codes should appear."""
        _print_table_row(["Hi"], width=5, bold=False)
        captured = capsys.readouterr().out
        assert "\033[" not in captured


# ── Tests: color_tier ────────────────────────────────────────────────────────


class TestColorTier:
    """Tests for color_tier()."""

    def test_powerful_is_green(self):
        """POWERFUL should have green ANSI code."""
        result = color_tier("POWERFUL")
        assert "\033[32m" in result
        assert "POWERFUL" in result
        assert result.endswith("\033[0m")

    def test_standard_is_blue(self):
        """STANDARD should have blue ANSI code."""
        result = color_tier("STANDARD")
        assert "\033[34m" in result

    def test_basic_is_yellow(self):
        """BASIC should have yellow ANSI code."""
        result = color_tier("BASIC")
        assert "\033[33m" in result

    def test_reject_is_red(self):
        """REJECT should have red ANSI code."""
        result = color_tier("REJECT")
        assert "\033[31m" in result

    def test_unknown_tier_no_color_change(self):
        """Unknown tier should use reset code only."""
        result = color_tier("UNKNOWN")
        assert result == "\033[0mUNKNOWN\033[0m"


# ── Tests: stdout_is_tty ────────────────────────────────────────────────────


class TestStdoutIsTty:
    """Tests for stdout_is_tty()."""

    def test_returns_true_when_isatty(self, monkeypatch):
        """When sys.stdout.isatty() returns True, return True."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        assert stdout_is_tty() is True

    def test_returns_false_when_not_isatty(self, monkeypatch):
        """When sys.stdout.isatty() returns False, return False."""
        monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
        assert stdout_is_tty() is False

    def test_handles_missing_isatty_attr(self, monkeypatch):
        """When isatty attribute is removed, return False safely."""
        monkeypatch.delattr(sys.stdout, "isatty", raising=False)
        # Without isatty, fall back to False
        with patch("scripts.formatters.hasattr", return_value=False):
            assert stdout_is_tty() is False


# ── Tests: print_stage ───────────────────────────────────────────────────────


class TestPrintStage:
    """Tests for print_stage()."""

    def test_prints_to_stderr(self, capsys):
        """print_stage should output to stderr, not stdout."""
        print_stage("Test Stage", level=1, use_color=False)
        captured = capsys.readouterr()
        assert "Test Stage" in captured.err
        assert captured.out == ""

    def test_level_one_uses_greater_than_prefix(self, capsys):
        """Level 1 should use '>' prefix."""
        print_stage("Main Stage", level=1, use_color=False)
        captured = capsys.readouterr().err
        assert "> Main Stage" in captured

    def test_level_two_uses_dot_prefix(self, capsys):
        """Level 2 should use '.' prefix."""
        print_stage("Sub Stage", level=2, use_color=False)
        captured = capsys.readouterr().err
        assert ". Sub Stage" in captured

    def test_indents_based_on_level(self, capsys):
        """Indentation should increase with level."""
        print_stage("Deep", level=3, use_color=False)
        captured = capsys.readouterr().err
        # 4 spaces per level (2 * (level-1) = 4 for level 3)
        assert "    " in captured

    def test_color_adds_ansi_bold(self, capsys):
        """With use_color=True, ANSI bold should wrap the label."""
        print_stage("Colored", level=1, use_color=True)
        captured = capsys.readouterr().err
        assert "\033[1m" in captured
        assert "\033[0m" in captured
