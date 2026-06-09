"""Tests for the Stage 1 analysis module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


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

    def test_full_skill_bundle(self, full_skill_dir: Path, minimal_config: Dict[str, Any]):
        """Bundle analysis should find scripts/references/assets."""
        result = analyze_skill(full_skill_dir, minimal_config)
        bundle = result["bundle"]
        assert bundle["scripts_count"] == 3
        assert bundle["references_count"] == 2
        assert bundle["assets_count"] == 1

    def test_full_skill_script_validation(self, full_skill_dir: Path, minimal_config: Dict[str, Any]):
        """Script validation should handle multiple languages."""
        result = analyze_skill(full_skill_dir, minimal_config)
        scripts = result["scripts"]
        assert scripts["total_count"] == 3
        languages = {r["language"] for r in scripts["results"]}
        assert "python" in languages
        assert "shell" in languages
        assert "js" in languages

    def test_trigger_analysis(self, good_skill_dir: Path, minimal_config: Dict[str, Any]):
        """Trigger analysis should extract trigger phrases."""
        result = analyze_skill(good_skill_dir, minimal_config)

        trig = result["trigger_info"]
        assert trig["trigger_count"] >= 3
        assert any("commit" in p.lower() for p in trig["trigger_phrases"])


# ── Internal function tests ───────────────────────────────────────────────


class TestFindLineNumber:
    """Tests for _find_line_number()."""

    def test_first_line(self):
        """Position 0 should return line 1."""
        from scripts.analyze import _find_line_number
        assert _find_line_number("hello\nworld", 0) == 1

    def test_second_line(self):
        """Position after first newline should return line 2."""
        from scripts.analyze import _find_line_number
        assert _find_line_number("hello\nworld", 7) == 2  # 'w' is at pos 6, 'o' at 7

    def test_end_of_text(self):
        """Position at end of text should return correct line."""
        from scripts.analyze import _find_line_number
        assert _find_line_number("line1\nline2\nline3", 17) == 3  # 'line3' starts at 12


class TestCheckPythonSyntax:
    """Tests for _check_python_syntax()."""

    def test_valid_syntax(self, tmp_path: Path):
        """A syntactically valid Python file should pass."""
        from scripts.analyze import _check_python_syntax
        f = tmp_path / "test.py"
        f.write_text("x = 1\ny = 2\nprint(x + y)\n")
        assert _check_python_syntax(f) is True

    def test_invalid_syntax(self, tmp_path: Path):
        """A syntactically invalid Python file should fail."""
        from scripts.analyze import _check_python_syntax
        f = tmp_path / "bad.py"
        f.write_text("x = 1\ny = 2\nprint(x +\n")
        assert _check_python_syntax(f) is False

    def test_empty_file_valid(self, tmp_path: Path):
        """An empty Python file should pass syntax check."""
        from scripts.analyze import _check_python_syntax
        f = tmp_path / "empty.py"
        f.write_text("")
        assert _check_python_syntax(f) is True

    def test_with_content_arg(self, tmp_path: Path):
        """When content is passed as string, file on disk is ignored."""
        from scripts.analyze import _check_python_syntax
        f = tmp_path / "ignored.py"
        f.write_text("syntax error!!!")
        assert _check_python_syntax(f, content="x = 42") is True

    def test_import_statements_valid(self, tmp_path: Path):
        """Files with imports and function defs should pass."""
        from scripts.analyze import _check_python_syntax
        f = tmp_path / "imports.py"
        f.write_text("import os\nimport sys\n\ndef foo():\n    return os.getcwd()\n")
        assert _check_python_syntax(f) is True


class TestCheckPythonDocstring:
    """Tests for _check_python_docstring()."""

    def test_has_docstring_double_quotes(self):
        """Module-level docstring with triple double-quotes should be detected."""
        from scripts.analyze import _check_python_docstring
        code = '"""My module docstring."""\nimport os\n'
        assert _check_python_docstring(code) is True

    def test_has_docstring_single_quotes(self):
        """Module-level docstring with triple single-quotes should be detected."""
        from scripts.analyze import _check_python_docstring
        code = "'''My module docstring.'''\nimport os\n"
        assert _check_python_docstring(code) is True

    def test_no_docstring(self):
        """Code without a docstring should return False."""
        from scripts.analyze import _check_python_docstring
        code = "import os\nimport sys\n"
        assert _check_python_docstring(code) is False

    def test_shebang_before_docstring(self):
        """A shebang line before the docstring should not interfere."""
        from scripts.analyze import _check_python_docstring
        code = "#!/usr/bin/env python3\n\"\"\"Shebang + docstring.\"\"\"\nimport os\n"
        assert _check_python_docstring(code) is True

    def test_docstring_on_second_line_no_shebang(self):
        """Just whitespace before docstring should not count as docstring."""
        from scripts.analyze import _check_python_docstring
        code = "\n\n\"\"\"Docstring after blank lines.\"\"\"\n"
        assert _check_python_docstring(code) is True

    def test_no_false_positive_on_inline_string(self):
        """A string that looks like a docstring but isn't at the start."""
        from scripts.analyze import _check_python_docstring
        code = "x = 1\n'''not a docstring'''\n"
        assert _check_python_docstring(code) is False


class TestValidateScripts:
    """Tests for _validate_scripts()."""

    def test_no_scripts_dir_returns_empty(self, tmp_path: Path):
        """Missing scripts directory should return zero counts."""
        from scripts.analyze import _validate_scripts
        config = {"analysis": {"script_extensions": [".py", ".sh"]}}
        result = _validate_scripts(tmp_path, config)
        assert result["total_count"] == 0
        assert result["valid_count"] == 0
        assert result["results"] == []

    def test_finds_python_and_shell_scripts(self, tmp_path: Path):
        """Scripts with .py and .sh extensions should be found."""
        from scripts.analyze import _validate_scripts
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test.py").write_text("print('hello')")
        (scripts_dir / "run.sh").write_text("#!/bin/bash\necho hi")
        config = {"analysis": {"script_extensions": [".py", ".sh"]}}
        result = _validate_scripts(tmp_path, config)
        assert result["total_count"] == 2
        assert result["valid_count"] == 2

    def test_detects_syntax_errors(self, tmp_path: Path):
        """Python files with syntax errors should be flagged."""
        from scripts.analyze import _validate_scripts
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "bad.py").write_text("print(\n")
        config = {"analysis": {"script_extensions": [".py", ".sh"]}}
        result = _validate_scripts(tmp_path, config)
        assert result["total_count"] == 1
        assert result["valid_count"] == 0
        assert result["results"][0]["syntax_valid"] is False

    def test_ignores_non_configured_extensions(self, tmp_path: Path):
        """Files without configured extensions shoul not be validated."""
        from scripts.analyze import _validate_scripts
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "data.json").write_text('{"key": "value"}')
        (scripts_dir / "script.py").write_text("x = 1")
        config = {"analysis": {"script_extensions": [".py"]}}
        result = _validate_scripts(tmp_path, config)
        assert result["total_count"] == 1  # only .py
        assert result["results"][0]["path"].endswith(".py")


class TestAnalyzeTriggers:
    """Tests for _analyze_triggers()."""

    def test_extracts_from_when_to_use_section(self):
        """Bullets under When to Use section should be extracted."""
        from scripts.analyze import _analyze_triggers
        content = "## When to Use\n- Validate JSON files before commit\n- Check YAML syntax\n"
        result = _analyze_triggers(content)
        assert result["trigger_count"] >= 1
        assert any("Validate JSON" in p for p in result["trigger_phrases"])

    def test_extracts_from_trigger_section(self):
        """Bullets under a Triggers section should be extracted."""
        from scripts.analyze import _analyze_triggers
        content = "## Triggers\n- When a config file is modified\n- On every pull request\n"
        result = _analyze_triggers(content)
        assert result["trigger_count"] >= 1
        assert any("config file is modified" in p for p in result["trigger_phrases"])

    def test_short_bullets_skipped(self):
        """Bullets shorter than 10 characters should be skipped."""
        from scripts.analyze import _analyze_triggers
        content = "## When to Use\n- short\n"
        result = _analyze_triggers(content)
        assert result["trigger_count"] == 0

    def test_keyword_mention_detected(self):
        """'trigger when' / 'triggers when' phrases should be detected."""
        from scripts.analyze import _analyze_triggers
        content = "This skill triggers when the user asks about YAML files.\n\n## Next"
        result = _analyze_triggers(content)
        assert result["trigger_count"] >= 1

    def test_empty_content(self):
        """Content with no trigger info should return zero."""
        from scripts.analyze import _analyze_triggers
        result = _analyze_triggers("Just a normal paragraph without triggers.")
        assert result["trigger_count"] == 0


class TestCheckAntiPatterns:
    """Tests for _check_anti_patterns()."""

    def test_detects_todo_in_body(self):
        """TODO markers in the body (after frontmatter) should be detected."""
        from scripts.analyze import _check_anti_patterns
        config = {"anti_patterns": [
            {"pattern": "TODO|FIXME", "type": "placeholder", "severity": "high", "message": "Placeholder found"},
        ]}
        content = "---\nname: test\n---\nSome text\nTODO: finish this"
        results = _check_anti_patterns(content, config)
        assert len(results) >= 1
        assert results[0]["type"] == "placeholder"

    def test_skips_frontmatter(self):
        """TODO-like text in frontmatter should NOT be detected."""
        from scripts.analyze import _check_anti_patterns
        config = {"anti_patterns": [
            {"pattern": "TODO|FIXME", "type": "placeholder", "severity": "high", "message": "Placeholder found"},
        ]}
        content = "---\nname: TODO-skill\ndescription: TODO\n---\nNormal body text"
        results = _check_anti_patterns(content, config)
        assert len(results) == 0

    def test_multiple_patterns(self):
        """Multiple anti-pattern rules should all be checked."""
        from scripts.analyze import _check_anti_patterns
        config = {"anti_patterns": [
            {"pattern": "TODO", "type": "placeholder", "severity": "high", "message": "Placeholder"},
            {"pattern": r"your\s+skill", "type": "template", "severity": "medium", "message": "Template"},
        ]}
        content = "---\nname: test\n---\nTODO: fix this\nUse your skill here"
        results = _check_anti_patterns(content, config)
        types = {r["type"] for r in results}
        assert "placeholder" in types
        assert "template" in types

    def test_malformed_pattern_skipped(self):
        """A regex that fails to compile should be skipped without crashing."""
        from scripts.analyze import _check_anti_patterns
        config = {"anti_patterns": [
            {"pattern": "[invalid", "type": "bad", "severity": "low", "message": "Bad pattern"},
        ]}
        content = "---\nname: test\n---\nSome text"
        results = _check_anti_patterns(content, config)
        assert results == []

    def test_empty_content_no_match(self):
        """Content with no anti-patterns should return empty list."""
        from scripts.analyze import _check_anti_patterns
        config = {"anti_patterns": [
            {"pattern": "TODO", "type": "placeholder", "severity": "high", "message": "Placeholder"},
        ]}
        content = "---\nname: test\n---\nClean content with no issues."
        results = _check_anti_patterns(content, config)
        assert results == []


class TestStripFrontmatter:
    """Tests for _strip_frontmatter()."""

    def test_strips_full_frontmatter(self):
        """YAML frontmatter block should be removed."""
        from scripts.analyze import _strip_frontmatter
        content = "---\nname: test\n---\n# Body\nContent here"
        assert _strip_frontmatter(content) == "# Body\nContent here"

    def test_strips_dotdotdot_delimiter(self):
        """The ... end delimiter should also be handled."""
        from scripts.analyze import _strip_frontmatter
        content = "---\nname: test\n...\n# Body"
        assert _strip_frontmatter(content) == "# Body"

    def test_no_frontmatter_returns_unchanged(self):
        """Content without frontmatter should be returned unchanged."""
        from scripts.analyze import _strip_frontmatter
        content = "# Just body\nNo frontmatter here"
        assert _strip_frontmatter(content) == content

    def test_empty_content_returns_empty(self):
        """Empty content should return empty string."""
        from scripts.analyze import _strip_frontmatter
        assert _strip_frontmatter("") == ""


class TestAnalyzeBundle:
    """Tests for _analyze_bundle()."""

    def test_empty_dir_returns_zero_counts(self, tmp_path: Path):
        """A skill dir with no sub-directories should return zeros."""
        from scripts.analyze import _analyze_bundle
        config = {"analysis": {"script_extensions": [".py", ".sh"]}}
        result = _analyze_bundle(tmp_path, config)
        assert result["scripts_count"] == 0
        assert result["references_count"] == 0
        assert result["assets_count"] == 0

    def test_ignores_hidden_files(self, tmp_path: Path):
        """Hidden files (dotfiles) in bundle dirs should be skipped."""
        from scripts.analyze import _analyze_bundle
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / ".hidden.py").write_text("x=1")
        (tmp_path / "scripts" / "visible.py").write_text("x=2")
        config = {"analysis": {"script_extensions": [".py", ".sh"]}}
        result = _analyze_bundle(tmp_path, config)
        paths = [e["path"] for e in result["scripts"]]
        visible_path = str(Path("scripts") / "visible.py")
        assert visible_path in paths
        assert not any(".hidden" in p for p in paths)

    def test_references_and_assets(self, tmp_path: Path):
        """References and assets directories should be scanned."""
        from scripts.analyze import _analyze_bundle
        (tmp_path / "references").mkdir()
        (tmp_path / "assets").mkdir()
        (tmp_path / "references" / "guide.md").write_text("# Guide")
        (tmp_path / "assets" / "logo.png").write_text("fake")
        config = {"analysis": {"script_extensions": [".py", ".sh"]}}
        result = _analyze_bundle(tmp_path, config)
        assert result["references_count"] == 1
        assert result["assets_count"] == 1
        assert any("guide.md" in e["path"] for e in result["references"])
        assert any("logo.png" in e["path"] for e in result["assets"])
