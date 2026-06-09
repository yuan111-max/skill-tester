"""Stage 1: Skill Analysis — deep structural and content analysis.

Produces a structured AnalysisResult dict consumed by Stages 2–4.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from scripts.utils import strip_frontmatter


# ── Public API ───────────────────────────────────────────────────────────


def analyze_skill(skill_dir: Path, config: Dict[str, Any], content: str = "") -> Dict[str, Any]:
    """Perform comprehensive analysis of a skill directory.

    Parameters
    ----------
    skill_dir:
        Path to the skill directory containing SKILL.md.
    config:
        Full skill-tester configuration dict.
    content:
        Optional pre-read SKILL.md content.  If empty (default), the file
        is read from disk.

    Returns
    -------
    dict with keys: name, description, frontmatter, content, bundle,
                    anti_patterns, trigger_info, scripts, issues, has_todo
    or dict with key ``error`` if SKILL.md is missing.
    """
    if not content:
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            return {"error": f"SKILL.md not found in {skill_dir}"}
        content = skill_md.read_text(encoding="utf-8")

    frontmatter, frontmatter_issues = _parse_frontmatter(content, config)
    content_analysis = _analyze_content_structure(content, config)
    bundle_analysis = _analyze_bundle(skill_dir, config)
    anti_patterns_found = _check_anti_patterns(content, config)
    trigger_info = _analyze_triggers(content)
    script_analysis = _validate_scripts(skill_dir, config)

    all_issues: List[str] = (
        frontmatter_issues
        + content_analysis.get("issues", [])
        + [ap["message"] for ap in anti_patterns_found if ap["severity"] == "high"]
    )

    return {
        "name": frontmatter.get("name", "unknown"),
        "description": frontmatter.get("description", ""),
        "frontmatter": frontmatter,
        "content": content_analysis,
        "bundle": bundle_analysis,
        "anti_patterns": anti_patterns_found,
        "trigger_info": trigger_info,
        "scripts": script_analysis,
        "issues": list(dict.fromkeys(all_issues)),  # deduplicate, preserve order
        "has_todo": bool(re.search(r"TODO|FIXME|XXX|HACK", _strip_code_blocks(strip_frontmatter(content)))),
    }


# ── Frontmatter parsing ──────────────────────────────────────────────────


def _parse_frontmatter(content: str, config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Parse YAML frontmatter between ``---`` delimiters."""
    issues: List[str] = []
    fm: Dict[str, Any] = {}

    fm_match = re.match(r"^---\n(.*?)\n(?:---|\.\.\.)", content, re.DOTALL)
    if not fm_match:
        return fm, ["Missing YAML frontmatter — SKILL.md must start with ``---``"]

    raw = fm_match.group(1)

    try:
        fm = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        issues.append(f"YAML parse error: {exc}")

    analysis_cfg = config.get("analysis", {})

    # Validate known fields
    if not fm.get("name"):
        issues.append("Missing or empty 'name' in frontmatter")
    elif analysis_cfg.get("check_name_format", True) and not re.match(
        r"^[a-z0-9][a-z0-9_-]*[a-z0-9]$", str(fm["name"])
    ):
        issues.append(f"'name' should be lowercase-hyphenated, got '{fm['name']}'")

    desc = fm.get("description", "")
    if not desc:
        issues.append("Missing or empty 'description' in frontmatter")
    elif analysis_cfg.get("check_angle_brackets", True) and ("<" in desc or ">" in desc):
        issues.append("'description' contains angle brackets (folded-scalar bug?)")
    elif len(desc) < analysis_cfg.get("min_description_length", 20):
        issues.append(
            f"'description' too short ({len(desc)} < "
            f"{analysis_cfg.get('min_description_length', 20)} chars)"
        )

    return fm, issues


# ── Content structure analysis ───────────────────────────────────────────


def _analyze_content_structure(content: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate SKILL.md body structure and quality."""
    sections = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
    section_count = len(sections)

    # Count code blocks (examples)
    examples = re.findall(r"```", content)
    example_count = len(examples) // 2  # each block has opening + closing

    # Check for required section keywords (word-boundary match prevents
    # "stage" from matching "Staging" or "Stagecoach", though "Stage 1"
    # still counts as a Stage section — intentional).
    required = config.get("analysis", {}).get("required_sections", [])
    missing_required = [
        req for req in required
        if not any(
            re.search(rf"\b{re.escape(req)}\b", s, re.IGNORECASE)
            for s in sections
        )
    ]

    # Line count
    lines = content.splitlines()
    line_count = len(lines)

    issues: List[str] = []
    if section_count < 2:
        issues.append("Too few sections (< 2) in SKILL.md body")
    if missing_required:
        issues.append(f"Missing recommended section(s): {', '.join(missing_required)}")
    if line_count > 500:
        issues.append(f"SKILL.md is very long ({line_count} lines, recommended < 500)")

    return {
        "sections": sections,
        "section_count": section_count,
        "example_count": example_count,
        "line_count": line_count,
        "missing_required_sections": missing_required,
        "issues": issues,
    }


# ── Bundle analysis ──────────────────────────────────────────────────────


def _analyze_bundle(skill_dir: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively scan bundle directories for supported script files."""
    extensions = config.get("analysis", {}).get("script_extensions", [".py", ".sh"])

    def _scan(subdir: str) -> List[Dict[str, Any]]:
        path = skill_dir / subdir
        if not path.is_dir():
            return []
        entries: List[Dict[str, Any]] = []
        for item in path.rglob("*"):
            if not item.is_file():
                continue
            # Skip hidden files, __pycache__ contents, and .pyc bytecode
            if item.name.startswith("."):
                continue
            if "__pycache__" in item.parts:
                continue
            if item.suffix == ".pyc":
                continue
            entries.append({
                "path": str(item.relative_to(skill_dir)),
                "size": item.stat().st_size,
                "ext": item.suffix,
            })
        return entries

    scripts = _scan("scripts")
    references = _scan("references")
    assets = _scan("assets")

    # Detect non-recognised script extensions (warn about orphans)
    orphan_extensions = {
        e["ext"] for e in scripts if e["ext"] and e["ext"] not in extensions
    }

    return {
        "scripts": scripts,
        "scripts_count": len(scripts),
        "references": references,
        "references_count": len(references),
        "assets": assets,
        "assets_count": len(assets),
        "orphan_extensions": list(orphan_extensions),
    }


# ── Anti-pattern detection ──────────────────────────────────────────────


_FENCED_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]+`")


def _strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks (```...```) and inline backtick code from *text*."""
    text = _FENCED_CODE_BLOCK_RE.sub("", text)
    text = _INLINE_CODE_RE.sub("", text)
    return text


def _check_anti_patterns(content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scan SKILL.md body for known anti-patterns.

    Fenced code blocks and inline backtick code are stripped before scanning
    to avoid false positives when keywords appear in examples or feature
    descriptions.
    """
    patterns = config.get("anti_patterns", [])
    matches: List[Dict[str, Any]] = []

    body = _strip_code_blocks(strip_frontmatter(content))

    for rule in patterns:
        try:
            for m in re.finditer(rule["pattern"], body, re.IGNORECASE):
                matches.append({
                    "type": rule.get("type", "unknown"),
                    "severity": rule.get("severity", "low"),
                    "message": rule.get("message", "Anti-pattern match"),
                    "match": m.group(0).strip()[:80],
                    "line": _find_line_number(body, m.start()),
                })
        except re.error:
            continue  # skip malformed patterns

    return matches


def _find_line_number(text: str, pos: int) -> int:
    """Return 1-based line number for character position *pos* in *text*."""
    return text[:pos].count("\n") + 1


# ── Trigger section analysis ─────────────────────────────────────────────


def _analyze_triggers(content: str) -> Dict[str, Any]:
    """Extract trigger-related information from SKILL.md."""
    trigger_phrases: List[str] = []

    # Find "When to Use" / "Usage" sections
    for match in re.finditer(
        r"(?:##\s+(?:When to Use|Usage|Triggers?).*?)\n(.*?)(?=\n##\s|\Z)",
        content,
        re.IGNORECASE | re.DOTALL,
    ):
        bullets = re.findall(r"^\s*[-*]\s+(.+)$", match.group(1), re.MULTILINE)
        trigger_phrases.extend(b.strip().rstrip(".") for b in bullets if len(b.strip()) > 10)

    # Find explicit trigger keyword mentions in body
    for match in re.finditer(
        r"(?:triggers? when|invoked when|activated when|use when)[:\s]+(.*?)(?:\n\n|\n##|\Z)",
        content,
        re.IGNORECASE | re.DOTALL,
    ):
        phrase = match.group(1).strip()
        if len(phrase) > 10:
            trigger_phrases.append(phrase)

    return {
        "trigger_phrases": trigger_phrases,
        "trigger_count": len(trigger_phrases),
    }


# ── Script validation ────────────────────────────────────────────────────


def _validate_scripts(skill_dir: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    """Syntax-check bundled scripts for all configured extensions."""
    extensions = config.get("analysis", {}).get("script_extensions", [".py", ".sh"])
    results: List[Dict[str, Any]] = []

    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        return {"results": [], "valid_count": 0, "total_count": 0}

    for ext in extensions:
        for f in sorted(scripts_dir.rglob(f"*{ext}")):
            if "__pycache__" in f.parts:
                continue
            if f.suffix == ".py":
                content = f.read_text(encoding="utf-8")
                syntax_valid = _check_python_syntax(f, content)
                has_docstring = _check_python_docstring(content)
                has_try_except = bool(re.search(r"\btry\b", content))
                results.append({
                    "path": str(f.relative_to(skill_dir)),
                    "language": "python",
                    "syntax_valid": syntax_valid,
                    "has_docstring": has_docstring,
                    "has_try_except": has_try_except,
                })
            elif f.suffix == ".sh":
                content = f.read_text(encoding="utf-8")
                results.append({
                    "path": str(f.relative_to(skill_dir)),
                    "language": "shell",
                    "has_shebang": content.startswith("#!"),
                    "syntax_valid": True,
                })
            else:
                content = f.read_text(encoding="utf-8")
                results.append({
                    "path": str(f.relative_to(skill_dir)),
                    "language": f.suffix.lstrip("."),
                    "syntax_valid": True,
                    "has_shebang": content.startswith("#!"),
                })

    return {
        "results": results,
        "valid_count": sum(1 for r in results if r.get("syntax_valid", False)),
        "total_count": len(results),
    }


def _check_python_syntax(path: Path, content: str = "") -> bool:
    """Return True if the Python file compiles without syntax errors.

    Uses the built-in ``compile()`` instead of a subprocess — ~10x faster.
    """
    try:
        if not content:
            content = path.read_text(encoding="utf-8")
        compile(content, path.name, "exec")
        return True
    except SyntaxError:
        return False


def _check_python_docstring(content: str) -> bool:
    """Return True if the Python source has a module-level docstring."""
    cleaned = re.sub(r"^#!.*\n", "", content)
    return bool(re.match(r'^\s*(?:"""|\'\'\')', cleaned))
