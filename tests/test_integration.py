"""End-to-end integration tests for the full 4-stage pipeline.

These tests verify that the stages compose correctly — analysis results
flow into generation, generation into execution, execution into evaluation.
Individual stage behaviour is covered in test_analyze.py, test_generate.py,
test_execute.py, and test_evaluate.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch


from scripts.analyze import analyze_skill
from scripts.evaluate import evaluate
from scripts.execute import execute_tests
from scripts.generate import generate_tests
from scripts.run_tests import _run_pipeline


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
GOOD_SKILL = FIXTURES_DIR / "good_skill"
BAD_SKILL = FIXTURES_DIR / "bad_skill"


def _make_minimal_config() -> Dict[str, Any]:
    """Return a minimal config that matches conftest.minimal_config."""
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
            "enabled": True,
            "claude_command": "claude",
            "timeout_seconds": 30,
            "max_tests": 5,
        },
        "anti_patterns": [
            {"pattern": "TODO|FIXME|XXX", "type": "placeholder", "severity": "high", "message": "Placeholder found"},
            {"pattern": r"your\s+(skill|needs|specific|use.case|scenario)\b", "type": "template_artifact", "severity": "medium", "message": "Template language"},
        ],
        "output": {"default_format": "summary", "max_description_preview": 80},
    }


class TestFullPipeline:
    """End-to-end tests composing all 4 stages."""

    def test_good_skill_full_pipeline(self, good_skill_dir: Path):
        """A well-formed skill should complete all stages without error."""
        config = _make_minimal_config()
        skill_md = good_skill_dir / "SKILL.md"
        skill_body = skill_md.read_text(encoding="utf-8")

        # Stage 1: Analysis
        analysis = analyze_skill(good_skill_dir, config, skill_body)
        assert "error" not in analysis
        analysis["_body"] = skill_body  # Pipeline does this

        # Stage 2: Generation
        test_data = generate_tests(good_skill_dir, analysis, config, skill_body)
        assert test_data["total_generated"] > 0

        # Stage 3: Execution (mocked — no real Claude CLI)
        with patch("scripts.execute._resolve_claude", return_value="claude"):
            with patch("scripts.execute.subprocess.run") as mock_run:
                # Return a response that triggers skill activation
                mock_proc = Mock()
                mock_proc.stdout = "I'll use the example-validator skill to help you"
                mock_proc.stderr = ""
                mock_proc.returncode = 0
                mock_run.return_value = mock_proc

                execution_result = execute_tests(test_data, analysis, config, force=True)

        assert execution_result["executed"] is True
        assert execution_result["summary"]["total"] > 0

        # Stage 4: Evaluation
        ev = evaluate(analysis, test_data, execution_result, config)
        assert "dimensions" in ev
        assert "final" in ev
        assert "tier" in ev
        for dim in ("Documentation", "Code", "Completeness", "Usability"):
            assert dim in ev["dimensions"]
            assert 0 <= ev["dimensions"][dim] <= 10

    def test_bad_skill_pipeline_scores_lower(self, bad_skill_dir: Path):
        """A bad skill should score lower than a good skill."""
        config = _make_minimal_config()
        skill_body = (bad_skill_dir / "SKILL.md").read_text(encoding="utf-8")

        analysis = analyze_skill(bad_skill_dir, config, skill_body)
        analysis["_body"] = skill_body
        test_data = generate_tests(bad_skill_dir, analysis, config, skill_body)

        with patch("scripts.execute._resolve_claude", return_value="claude"):
            with patch("scripts.execute.subprocess.run") as mock_run:
                mock_proc = Mock()
                mock_proc.stdout = "I don't know about that skill"
                mock_proc.stderr = ""
                mock_proc.returncode = 0
                mock_run.return_value = mock_proc
                execution_result = execute_tests(test_data, analysis, config, force=True)

        ev = evaluate(analysis, test_data, execution_result, config)
        assert ev["final"] < 7.5  # Bad skill should not score highly

    def test_body_injection_affects_usability(self, good_skill_dir: Path):
        """The _body injection should be consumed by the Usability scorer."""
        config = _make_minimal_config()
        skill_body = (good_skill_dir / "SKILL.md").read_text(encoding="utf-8")

        # Without _body
        analysis_no_body = analyze_skill(good_skill_dir, config, skill_body)
        test_data = generate_tests(good_skill_dir, analysis_no_body, config, skill_body)
        empty_exec = {"executed": False, "results": [], "summary": {}, "stats": {}}

        # With _body
        analysis_with_body = analyze_skill(good_skill_dir, config, skill_body)
        analysis_with_body["_body"] = skill_body

        ev_no_body = evaluate(analysis_no_body, test_data, empty_exec, config)
        ev_with_body = evaluate(analysis_with_body, test_data, empty_exec, config)

        # With _body, Usability should have better instruction_actionability
        # (since it can parse bullet points from the content)
        no_body_usability = ev_no_body["dimensions"].get("Usability", 0)
        with_body_usability = ev_with_body["dimensions"].get("Usability", 0)

        assert with_body_usability >= no_body_usability, (
            f"Expected _body to improve Usability (was {no_body_usability}, "
            f"got {with_body_usability})"
        )

    def test_execution_results_flow_into_evaluation(self, good_skill_dir: Path):
        """Pass/fail execution results should affect Usability score."""
        config = _make_minimal_config()
        skill_body = (good_skill_dir / "SKILL.md").read_text(encoding="utf-8")

        analysis = analyze_skill(good_skill_dir, config, skill_body)
        analysis["_body"] = skill_body
        test_data = generate_tests(good_skill_dir, analysis, config, skill_body)

        # Mock all executions as PASS
        with patch("scripts.execute._resolve_claude", return_value="claude"):
            with patch("scripts.execute.subprocess.run") as mock_run:
                mock_proc = Mock()
                mock_proc.stdout = "I'll use the example-validator skill"
                mock_proc.stderr = ""
                mock_proc.returncode = 0
                mock_run.return_value = mock_proc

                all_pass = execute_tests(test_data, analysis, config, force=True)

        # Mock all executions as FAIL
        with patch("scripts.execute._resolve_claude", return_value="claude"):
            with patch("scripts.execute.subprocess.run") as mock_run:
                mock_proc = Mock()
                mock_proc.stdout = "I don't know what to do"
                mock_proc.stderr = ""
                mock_proc.returncode = 0
                mock_run.return_value = mock_proc

                all_fail = execute_tests(test_data, analysis, config, force=True)

        ev_pass = evaluate(analysis, test_data, all_pass, config)
        ev_fail = evaluate(analysis, test_data, all_fail, config)

        assert ev_pass["dimensions"]["Usability"] >= ev_fail["dimensions"]["Usability"]

    def test_pipeline_from_run_tests(self):
        """_run_pipeline should produce a valid report with all expected keys."""
        config = _make_minimal_config()
        config["execution"]["enabled"] = True
        config["execution"]["max_tests"] = 3

        with patch("scripts.run_tests.analyze_skill") as mock_a:
            with patch("scripts.run_tests.generate_tests") as mock_g:
                with patch("scripts.run_tests.execute_tests") as mock_e:
                    with patch("scripts.run_tests.evaluate") as mock_ev:
                        mock_a.return_value = {
                            "name": "test-skill",
                            "description": "A test skill",
                            "content": {"sections": ["When to Use", "Stage"], "section_count": 2,
                                        "example_count": 1, "line_count": 50, "missing_required_sections": [], "issues": []},
                            "bundle": {"scripts_count": 0, "references_count": 0, "assets_count": 0,
                                       "scripts": [], "references": [], "assets": [], "orphan_extensions": []},
                            "anti_patterns": [],
                            "trigger_info": {"trigger_phrases": [], "trigger_count": 0},
                            "scripts": {"results": [], "valid_count": 0, "total_count": 0},
                            "issues": [], "has_todo": False,
                        }
                        mock_g.return_value = {
                            "tests": [{"prompt": "test", "expected_trigger": True}],
                            "trigger_tests": [], "non_trigger_tests": [], "edge_cases": [],
                            "capabilities": [], "total_generated": 1,
                        }
                        mock_e.return_value = {
                            "executed": True,
                            "results": [{"status": "PASS"}],
                            "summary": {"total": 1, "passed": 1, "failed": 0, "error": 0, "skipped": 0},
                            "stats": {"total": 1, "passed": 1, "failed": 0, "error": 0, "skipped": 0},
                        }
                        mock_ev.return_value = {
                            "dimensions": {"Documentation": 8.0, "Code": 7.0, "Completeness": 6.0, "Usability": 9.0},
                            "details": {}, "final": 7.50, "tier": "STANDARD",
                        }

                        result = _run_pipeline(
                            GOOD_SKILL, config, execute_enabled=True, quiet=True, use_color=False
                        )

        assert result["skill"] == "test-skill"
        assert result["evaluation"]["final"] == 7.50
        assert result["evaluation"]["tier"] == "STANDARD"
        assert result["execution"]["executed"] is True
        assert "elapsed" in result
        assert isinstance(result["elapsed"], float)

        # Verify _body was set on the analysis
        _call_body = mock_a.call_args[0][2] if len(mock_a.call_args[0]) > 2 else ""
        assert len(_call_body) > 0


class TestPipelineEdgeCases:
    """Edge cases in pipeline composition."""

    def test_analysis_error_propagates(self):
        """When analysis returns an error, no further stages should run."""
        config = _make_minimal_config()
        with patch("scripts.run_tests.analyze_skill", return_value={"error": "SKILL.md not found"}):
            result = _run_pipeline(
                GOOD_SKILL, config, execute_enabled=False, quiet=True, use_color=False
            )
        assert "error" in result
        assert result["error"] == "SKILL.md not found"
        assert "evaluation" not in result

    def test_missing_skill_body_empty_string(self, tmp_path: Path):
        """When SKILL.md doesn't exist, _body should be empty and pipeline errors."""
        empty_dir = tmp_path / "empty-skill"
        empty_dir.mkdir()
        config = _make_minimal_config()
        with patch("scripts.run_tests.analyze_skill") as mock_a:
            mock_a.return_value = {"error": f"SKILL.md not found in {empty_dir}"}
            result = _run_pipeline(
                empty_dir, config, execute_enabled=False, quiet=True, use_color=False
            )
        assert "error" in result

    def test_full_skill_with_bundle(self, full_skill_dir: Path):
        """A skill with scripts, references, and assets should analyze correctly."""
        config = _make_minimal_config()
        skill_body = (full_skill_dir / "SKILL.md").read_text(encoding="utf-8")
        analysis = analyze_skill(full_skill_dir, config, skill_body)

        # Bundle analysis should find all directories
        bundle = analysis["bundle"]
        assert bundle["scripts_count"] == 3  # .py, .sh, .js
        assert bundle["references_count"] == 2
        assert bundle["assets_count"] == 1

        # Script validation should find all scripts
        scripts = analysis["scripts"]
        assert scripts["total_count"] == 3
        # .py file should have syntax_valid=True
        py_results = [r for r in scripts["results"] if r["language"] == "python"]
        assert len(py_results) == 1
        assert py_results[0]["syntax_valid"] is True

        # Test generation should work with full skill
        analysis["_body"] = skill_body
        test_data = generate_tests(full_skill_dir, analysis, config, skill_body)
        assert test_data["total_generated"] > 0

        # Evaluation should score well
        empty_exec = {"executed": False, "results": [], "summary": {}, "stats": {}}
        ev = evaluate(analysis, test_data, empty_exec, config)
        assert "final" in ev
        assert ev["final"] >= 5.0  # Full skill should score at least BASIC

    def test_empty_skill_body(self, tmp_path: Path):
        """A SKILL.md with only frontmatter and no body should not crash."""
        skill_dir = tmp_path / "minimal-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: minimal-skill\ndescription: Minimal skill\n---\n",
            encoding="utf-8",
        )
        config = _make_minimal_config()
        result = _run_pipeline(
            skill_dir, config, execute_enabled=False, quiet=True, use_color=False
        )
        # Should not crash — may have issues but not an error
        if "error" not in result:
            assert "evaluation" in result
