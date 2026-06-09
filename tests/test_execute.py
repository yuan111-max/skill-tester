"""Tests for Stage 3: Test Execution."""

from __future__ import annotations

import copy
import subprocess
from typing import Any, Dict
from unittest.mock import Mock, patch


from scripts.execute import (
    _detect_skill_activation,
    _resolve_claude,
    _skipped_report,
    execute_tests,
)


# ── Fixtures ───────────────────────────────────────────────────────────────

def _make_test_data(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
    """Build a standard test_data dict."""
    data = {
        "tests": [
            {"prompt": "validate my config file", "expected_trigger": True, "type": "trigger"},
            {"prompt": "what is the weather", "expected_trigger": False, "type": "non_trigger"},
        ],
        "trigger_tests": [{"prompt": "validate my config file", "expected_trigger": True, "type": "trigger"}],
        "non_trigger_tests": [{"prompt": "what is the weather", "expected_trigger": False, "type": "non_trigger"}],
        "edge_cases": [],
        "capabilities": [{"name": "YAML Validation", "source": "section_heading"}],
        "total_generated": 2,
    }
    if overrides:
        data.update(overrides)
    return data


def _make_analysis(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
    data = {"name": "example-validator", "description": "Validates YAML files"}
    if overrides:
        data.update(overrides)
    return data


def _make_config(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
    data = {
        "execution": {
            "enabled": False,
            "claude_command": "claude",
            "timeout_seconds": 180,
            "max_tests": 10,
            "temperature": 0.0,
            "claude_args": ["--non-interactive", "--print"],
        },
    }
    if overrides:
        _deep_merge(data, overrides)
    return data


def _deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> None:
    for key, value in overrides.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)


def _mock_subprocess(stdout: str = "", returncode: int = 0):
    """Return a Mock that simulates subprocess.run success."""
    proc = Mock()
    proc.stdout = stdout
    proc.stderr = ""
    proc.returncode = returncode
    return Mock(return_value=proc)


# ── Tests ────────────────────────────────────────────────────────────────────

class TestExecuteTests:
    """Tests for execute_tests()."""

    def test_skipped_when_disabled(self):
        """Execution should be skipped when force=False and enabled=False."""
        result = execute_tests(
            _make_test_data(),
            _make_analysis(),
            _make_config(),
            force=False,
        )
        assert result["executed"] is False
        assert result["skip_reason"] is not None
        assert result["summary"]["skipped"] == 2
        assert result["summary"]["passed"] == 0

    def test_force_overrides_disabled(self, monkeypatch):
        """force=True should execute even when enabled=False."""
        config = _make_config({"execution": {"enabled": False}})
        # Mock subprocess.run AND _resolve_claude
        monkeypatch.setattr("scripts.execute._resolve_claude", lambda cmd: cmd)
        monkeypatch.setattr(
            "scripts.execute.subprocess.run",
            _mock_subprocess("I'll use the YAML validator skill"),
        )

        result = execute_tests(_make_test_data(), _make_analysis(), config, force=True)
        assert result["executed"] is True
        assert result["summary"]["total"] == 2

    def test_missing_cli_returns_skipped(self, monkeypatch):
        """When the Claude CLI is not found, return skipped report."""
        monkeypatch.setattr("scripts.execute._resolve_claude", lambda cmd: None)
        config = _make_config({"execution": {"enabled": True}})

        result = execute_tests(_make_test_data(), _make_analysis(), config)
        assert result["executed"] is False
        assert "not found" in result.get("skip_reason", "").lower()

    def test_file_not_found_at_runtime(self, monkeypatch):
        """CLI disappears between resolve and run."""
        monkeypatch.setattr("scripts.execute._resolve_claude", lambda cmd: cmd)
        monkeypatch.setattr(
            "scripts.execute.subprocess.run",
            Mock(side_effect=FileNotFoundError("no such file")),
        )
        config = _make_config({"execution": {"enabled": True}})

        result = execute_tests(_make_test_data(), _make_analysis(), config)
        assert result["executed"] is False
        assert "not found" in result.get("skip_reason", "").lower()

    def test_timeout_handling(self, monkeypatch):
        """TimeoutExpired should be caught and reported."""
        monkeypatch.setattr("scripts.execute._resolve_claude", lambda cmd: cmd)
        monkeypatch.setattr(
            "scripts.execute.subprocess.run",
            Mock(side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=1)),
        )
        config = _make_config({"execution": {"enabled": True}})

        result = execute_tests(_make_test_data(), _make_analysis(), config)
        assert result["executed"] is True
        assert result["summary"]["error"] == 2
        assert all(r["status"] == "TIMEOUT" for r in result["results"])

    def test_all_pass_when_activation_matches(self, monkeypatch):
        """Test every prompt PASSes when activation status matches expected."""
        monkeypatch.setattr("scripts.execute._resolve_claude", lambda cmd: cmd)

        # Return activation for trigger test, non-activation for non-trigger test
        responses = iter([
            Mock(stdout="I'll use the example-validator skill", stderr="", returncode=0),
            Mock(stdout="I don't know about that.", stderr="", returncode=0),
        ])
        monkeypatch.setattr("scripts.execute.subprocess.run", lambda *a, **kw: next(responses))

        config = _make_config({"execution": {"enabled": True}})

        result = execute_tests(_make_test_data(), _make_analysis(), config)
        assert result["executed"] is True
        assert result["summary"]["passed"] == 2
        assert result["summary"]["failed"] == 0

    def test_cap_respects_max_tests(self, monkeypatch):
        """max_tests should limit how many prompts are executed."""
        monkeypatch.setattr("scripts.execute._resolve_claude", lambda cmd: cmd)
        monkeypatch.setattr(
            "scripts.execute.subprocess.run",
            _mock_subprocess("response"),
        )
        # 10 tests in data, max_tests=3
        many_tests = [{"prompt": f"test {i}", "expected_trigger": True, "type": "trigger"} for i in range(10)]
        config = _make_config({"execution": {"enabled": True, "max_tests": 3}})
        data = _make_test_data({"tests": many_tests})

        result = execute_tests(data, _make_analysis(), config)
        assert result["executed"] is True
        assert result["summary"]["total"] == 3


class TestDetectSkillActivation:
    """Tests for _detect_skill_activation()."""

    def test_skill_name_in_response(self):
        """Response containing skill name should trigger."""
        assert _detect_skill_activation(
            "Use the example-validator skill to check YAML",
            "example-validator",
        ) is True

    def test_activation_phrase_detected(self):
        """Response with 'I'll use the' should trigger."""
        assert _detect_skill_activation(
            "I'll use the skill to validate your config",
            "unknown",
        ) is True

    def test_sections_and_code_detected(self):
        """Response with sections AND code should trigger."""
        response = "# Analysis\nSome text\n```\ncode\n```"
        assert _detect_skill_activation(response, "unknown") is True

    def test_code_alone_not_enough(self):
        """Code block ALONE (without sections) should NOT trigger."""
        response = "Here is some code:\n```\nprint('hello')\n```"
        assert _detect_skill_activation(response, "unknown") is False

    def test_sections_alone_not_enough(self):
        """Section headers ALONE (without code) should NOT trigger."""
        response = "# Title\n## Subtitle\nSome text"
        assert _detect_skill_activation(response, "unknown") is False

    def test_no_match_returns_false(self):
        """Totally unrelated response should not trigger."""
        response = "I don't know what you're talking about."
        assert _detect_skill_activation(response, "unknown") is False

    def test_empty_response(self):
        """Empty response should not trigger."""
        assert _detect_skill_activation("", "unknown") is False

    def test_according_to_the_skill(self):
        """'according to the skill' should trigger."""
        assert _detect_skill_activation(
            "According to the skill instructions, I should...",
            "unknown",
        ) is True

    def test_based_on_the_skill(self):
        """'Based on the skill' should trigger."""
        assert _detect_skill_activation(
            "Based on the skill guidance, here's what to do",
            "unknown",
        ) is True


class TestResolveClaude:
    """Tests for _resolve_claude()."""

    def test_returns_none_when_not_found(self):
        """When no variant is on PATH, return None."""
        # Mock _which to return None for all candidates
        with patch("scripts.execute._which", return_value=None):
            assert _resolve_claude("claude") is None

    def test_returns_command_when_found(self):
        """When command is found, return its name."""
        with patch("scripts.execute._which", return_value="claude"):
            assert _resolve_claude("claude") == "claude"

    def test_tries_windows_variants(self):
        """On Windows, also try .cmd and .exe variants."""
        # Mock _which to fail on first call (claude), succeed on second (claude.cmd)
        call_count = [0]

        def mock_which(cmd):
            call_count[0] += 1
            if call_count[0] == 2:  # Second call
                return "claude.cmd"
            return None

        with patch("scripts.execute._which", side_effect=mock_which):
            result = _resolve_claude("claude")
            # Should find claude.cmd
            assert result == "claude.cmd"


class TestWhich:
    """Tests for _which()."""

    def test_finds_python(self):
        """_which('python') should resolve successfully."""
        from scripts.execute import _which
        result = _which("python")
        assert result is not None  # python is always on PATH

    def test_returns_none_for_nonexistent(self):
        """_which('nonexistent-command-abc123') should return None."""
        from scripts.execute import _which
        result = _which("nonexistent-command-abc123")
        assert result is None

    def test_finds_exe_suffixed_program(self):
        """_which should handle .exe suffixed programs."""
        from scripts.execute import _which
        # 'cmd.exe' exists on Windows
        result = _which("cmd.exe")
        if result is not None:
            assert isinstance(result, str)


class TestSkippedReport:
    """Tests for _skipped_report()."""

    def test_all_tests_marked_skipped(self):
        """All tests should be marked SKIPPED with the reason."""
        test_data = _make_test_data({"tests": [{"prompt": "test", "expected_trigger": True}]})
        result = _skipped_report(test_data, "No CLI available")
        assert result["executed"] is False
        assert result["summary"]["skipped"] == 1
        assert all(r["status"] == "SKIPPED" for r in result["results"])
        assert all(r["note"] == "No CLI available" for r in result["results"])
        assert result["skip_reason"] == "No CLI available"
