#!/usr/bin/env python3
"""
4-Stage Skill Evaluation Pipeline
Based on cc-plugin-eval (sjnims) + skill-tester (alirezarezvani)

Usage:
    python3 run_tests.py <skill-dir> [--output json|summary]
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path

# ─── Stage 1: Analysis ────────────────────────────────────────────────────────

def analyze_skill(skill_dir: Path) -> dict:
    """Parse SKILL.md and extract skill metadata."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"error": f"SKILL.md not found in {skill_dir}"}

    content = skill_md.read_text()

    # Parse YAML frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return {"error": "Missing YAML frontmatter delimiter"}

    frontmatter = fm_match.group(1)
    fm = {}
    for line in frontmatter.splitlines():
        if ':' in line:
            key, _, val = line.partition(':')
            fm[key.strip()] = val.strip()

    # Structural checks
    issues = []
    if 'name' not in fm:
        issues.append("Missing 'name' in frontmatter")
    if 'description' not in fm:
        issues.append("Missing 'description' in frontmatter")
    if fm.get('name', '').lower() != fm.get('name', ''):
        issues.append("'name' should be lowercase")
    if '<' in fm.get('description', '') or '>' in fm.get('description', ''):
        issues.append("'description' contains angle brackets (likely folded scalar bug)")
    if len(fm.get('description', '')) < 20:
        issues.append("'description' is too short (< 20 chars)")

    # Check bundle structure
    has_scripts = (skill_dir / "scripts").exists() and any((skill_dir / "scripts").iterdir())
    has_references = (skill_dir / "references").exists() and any((skill_dir / "references").iterdir())
    has_assets = (skill_dir / "assets").exists() and any((skill_dir / "assets").iterdir())

    return {
        "name": fm.get("name", "unknown"),
        "description": fm.get("description", ""),
        "issues": issues,
        "bundle": {
            "scripts": has_scripts,
            "references": has_references,
            "assets": has_assets,
        },
        "has_todo": "[TODO" in content,
    }


# ─── Stage 2: Generation ──────────────────────────────────────────────────────

TRIGGER_KEYWORDS = [
    "when to use", "use when", "trigger", "invoked", "activated",
    "apply when", "run when", "execute when", "call this skill",
]

def generate_trigger_tests(skill_dir: Path) -> list:
    """Extract trigger conditions from SKILL.md and generate test prompts."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return []

    content = skill_md.read_text()
    tests = []

    # Extract "When to Use" sections
    when_sections = re.findall(
        r"(?:##\s+(?:When to Use|Usage|Triggers?).*?\n)(.*?)(?=\n##\s|\Z)",
        content, re.IGNORECASE | re.DOTALL
    )

    for section in when_sections:
        # Find bullet points and code blocks
        bullets = re.findall(r"^\s*[-*]\s+(.+)$", section, re.MULTILINE)
        for b in bullets:
            b = b.strip().rstrip('.')
            if len(b) > 10:
                tests.append({
                    "type": "trigger",
                    "prompt": b,
                    "expected_trigger": True,
                })

    # Find trigger keywords in context
    for match in re.finditer(rf"( {'|'.join(TRIGGER_KEYWORDS)})[:\s]+(.*?)(?:\n\n|\n##)", content, re.IGNORECASE | re.DOTALL):
        phrase = match.group(2).strip()
        if len(phrase) > 10:
            tests.append({
                "type": "trigger",
                "prompt": phrase,
                "expected_trigger": True,
            })

    return tests[:10]  # Cap at 10 tests


# ─── Stage 3: Execution (stub) ────────────────────────────────────────────────

def execute_tests(tests: list) -> list:
    """
    Execute each test. Stub version — full execution requires a sub-agent.
    Returns a list of {test, status, note} dicts.
    """
    results = []
    for t in tests:
        results.append({
            **t,
            "status": "SKIPPED",
            "note": "Execution requires a sub-agent. Run with --execute to enable.",
        })
    return results


# ─── Stage 4: Evaluation ───────────────────────────────────────────────────────

DIMENSION_WEIGHTS = {
    "Documentation": 0.25,
    "Code": 0.25,
    "Completeness": 0.25,
    "Usability": 0.25,
}

def score_dimension(value: float) -> float:
    """Convert raw 0-10 score to weighted contribution."""
    return value / 10.0

def evaluate(analysis: dict, trigger_tests: list) -> dict:
    """Compute 4D scores and final tier."""
    scores = {}

    # Documentation: based on structural issues and description quality
    doc_issues = len(analysis.get("issues", []))
    has_todo = analysis.get("has_todo", False)
    desc_len = len(analysis.get("description", ""))
    scores["Documentation"] = max(0, 10 - doc_issues * 2 - (3 if has_todo else 0) - (2 if desc_len < 50 else 0))

    # Code: based on bundle structure
    bundle = analysis.get("bundle", {})
    code_score = 5  # baseline
    if bundle.get("scripts"):
        code_score += 3
    if bundle.get("references"):
        code_score += 1
    if bundle.get("assets"):
        code_score += 1
    scores["Code"] = min(10, code_score)

    # Completeness: based on trigger test coverage
    n_tests = len(trigger_tests)
    if n_tests >= 8:
        scores["Completeness"] = 9
    elif n_tests >= 5:
        scores["Completeness"] = 7
    elif n_tests >= 2:
        scores["Completeness"] = 5
    else:
        scores["Completeness"] = 3

    # Usability: proxy via structural issues
    scores["Usability"] = max(0, 10 - doc_issues * 3 - (2 if has_todo else 0))

    # Final
    final = sum(score_dimension(v) * DIMENSION_WEIGHTS[k] for k, v in scores.items())

    # Tier
    if final >= 0.85:
        tier = "POWERFUL"
    elif final >= 0.70:
        tier = "STANDARD"
    elif final >= 0.50:
        tier = "BASIC"
    else:
        tier = "REJECT"

    return {
        "dimensions": scores,
        "final": round(final, 3),
        "tier": tier,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="4-Stage Skill Evaluation")
    parser.add_argument("skill_dir", type=Path, help="Path to skill directory")
    parser.add_argument("--output", choices=["json", "summary"], default="summary")
    args = parser.parse_args()

    skill_dir = args.skill_dir.expanduser().resolve()
    if not skill_dir.exists():
        print(f"Error: {skill_dir} does not exist")
        sys.exit(1)

    # Stage 1: Analysis
    analysis = analyze_skill(skill_dir)
    if "error" in analysis:
        print(f"Error: {analysis['error']}")
        sys.exit(1)

    # Stage 2: Generation
    trigger_tests = generate_trigger_tests(skill_dir)

    # Stage 3: Execution (stub)
    results = execute_tests(trigger_tests)

    # Stage 4: Evaluation
    evaluation = evaluate(analysis, trigger_tests)

    report = {
        "skill": analysis["name"],
        "description": analysis["description"],
        "issues": analysis["issues"],
        "bundle": analysis["bundle"],
        "trigger_tests_generated": len(trigger_tests),
        "tests": results,
        "evaluation": evaluation,
    }

    if args.output == "json":
        print(json.dumps(report, indent=2))
    else:
        print_summary(report)

def print_summary(report: dict):
    ev = report["evaluation"]
    dims = ev["dimensions"]
    print(f"\n{'='*60}")
    print(f"Skill Tester Report: {report['skill']}")
    print(f"{'='*60}")
    print(f"Description: {report['description'][:80]}")
    print(f"\nStructural Issues ({len(report['issues'])}):")
    for issue in report["issues"]:
        print(f"  ⚠️  {issue}")
    print(f"\nBundle: scripts={report['bundle']['scripts']}  "
          f"refs={report['bundle']['references']}  "
          f"assets={report['bundle']['assets']}")
    print(f"\n4D Scores:")
    for dim, score in dims.items():
        bar = "█" * int(score) + "░" * (10 - int(score))
        print(f"  {dim:<16} {bar} {score:.1f}/10")
    print(f"\n{'─'*40}")
    print(f"  Final Score: {ev['final']:.3f}  →  {ev['tier']}")
    print(f"  Trigger tests generated: {report['trigger_tests_generated']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
