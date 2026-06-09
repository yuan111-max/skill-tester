#!/usr/bin/env python3
"""
skill-tester — 4-Stage pipeline + 4D scoring for Claude Code skill evaluation.

Usage
-----
    python scripts/run_tests.py <skill-dir> [options]

Examples
--------
    # Basic structural analysis and scoring
    python scripts/run_tests.py ../my-skill

    # Full pipeline with real test execution
    python scripts/run_tests.py ../my-skill --execute

    # JSON output for programmatic consumption
    python scripts/run_tests.py ../my-skill --output json

    # Compare two skills side by side
    python scripts/run_tests.py ../skill-a ../skill-b --output table

    # Custom configuration
    python scripts/run_tests.py ../my-skill --config ./my-config.yaml
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add parent dir so ``scripts`` is importable when run as ``python scripts/run_tests.py``
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR.parent))

from scripts.config import load_config  # noqa: E402
from scripts.analyze import analyze_skill  # noqa: E402
from scripts.generate import generate_tests  # noqa: E402
from scripts.execute import execute_tests  # noqa: E402
from scripts.evaluate import evaluate  # noqa: E402
from scripts.formatters import (  # noqa: E402
    output_json,
    output_summary,
    output_table,
    print_stage,
    stdout_is_tty,
)


# ── CLI ──────────────────────────────────────────────────────────────────


def build_parser():
    import argparse

    parser = argparse.ArgumentParser(
        description="4-Stage Skill Evaluation Pipeline for Claude Code skills. "
                    "Supports --execute (live CLI tests), --config (custom YAML), "
                    "--output json|table|summary, and multi-skill comparison.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "skill_dirs",
        type=Path,
        nargs="+",
        help="Path(s) to skill directory (one or more for comparison)",
    )
    parser.add_argument(
        "--output", "-o",
        choices=["summary", "json", "table"],
        default=None,
        help="Output format (default: summary; table for multi-skill)",
    )
    parser.add_argument(
        "--execute", "-e",
        action="store_true",
        default=False,
        help="Enable real test execution via Claude CLI (disabled by default)",
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=None,
        help="Path to custom YAML configuration file",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        default=False,
        help="Suppress stage progress output",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour in output",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Resolve output format
    output_format = args.output
    if output_format is None:
        output_format = "table" if len(args.skill_dirs) > 1 else "summary"

    # Resolve colour
    use_color = not args.no_color and stdout_is_tty()

    # Process each skill
    reports: List[Dict[str, Any]] = []
    exit_code = 0

    for skill_dir in args.skill_dirs:
        resolved = skill_dir.expanduser().resolve()
        if not resolved.exists():
            print(f"Error: {resolved} does not exist", file=sys.stderr)
            exit_code = 1
            continue

        if not args.quiet:
            print_stage(f"Analyzing: {resolved.name}", 1, use_color)

        report = _run_pipeline(resolved, config, args.execute, args.quiet, use_color)
        reports.append(report)

        if report.get("error"):
            print(f"  [!] {report['error']}", file=sys.stderr)

    # Output
    if output_format == "json":
        output_json(reports, args.skill_dirs)
    elif output_format == "table":
        output_table(reports, args.skill_dirs, use_color)
    else:
        for i, report in enumerate(reports):
            output_summary(report, args.skill_dirs[i], use_color)
            if i < len(reports) - 1:
                print()  # blank line between skills

    sys.exit(exit_code)


# ── Pipeline ─────────────────────────────────────────────────────────────


def _run_pipeline(
    skill_dir: Path,
    config: Dict[str, Any],
    execute_enabled: bool,
    quiet: bool,
    use_color: bool,
) -> Dict[str, Any]:
    """Run the full 4-stage pipeline for one skill."""
    start = time.monotonic()

    # Read SKILL.md body once (shared across stages)
    skill_md_path = skill_dir / "SKILL.md"
    skill_body = ""
    if skill_md_path.exists():
        skill_body = skill_md_path.read_text(encoding="utf-8")

    # ── Stage 1: Analysis ──────────────────────────────────────────────
    if not quiet:
        print_stage("Stage 1: Analysis", 2, use_color)

    analysis = analyze_skill(skill_dir, config, skill_body)
    if "error" in analysis:
        elapsed = time.monotonic() - start
        return {"error": analysis["error"], "elapsed": round(elapsed, 2)}
    analysis["_body"] = skill_body

    if not quiet:
        issues = analysis.get("issues", [])
        print(f"    Frontmatter: name='{analysis['name']}', "
              f"issues={len(issues)}")

    # ── Stage 2: Generation ────────────────────────────────────────────
    if not quiet:
        print_stage("Stage 2: Test Generation", 2, use_color)

    test_data = generate_tests(skill_dir, analysis, config, skill_body)

    if not quiet:
        trig = len(test_data.get("trigger_tests", []))
        nontrig = len(test_data.get("non_trigger_tests", []))
        edge = len(test_data.get("edge_cases", []))
        print(f"    {trig} trigger + {nontrig} non-trigger + {edge} edge = "
              f"{test_data['total_generated']} total tests")

    # ── Stage 3: Execution ─────────────────────────────────────────────
    if not quiet:
        print_stage("Stage 3: Execution", 2, use_color)

    execution_result = execute_tests(test_data, analysis, config, force=execute_enabled)

    if not quiet:
        summary = execution_result.get("summary", {})
        if execution_result.get("executed"):
            print(f"    {summary.get('passed', 0)}/{summary.get('total', 0)} passed "
                  f"({summary.get('failed', 0)} failed, {summary.get('error', 0)} errors)")
        else:
            print(f"    SKIPPED - {execution_result.get('skip_reason', 'use --execute to enable')}")

    # ── Stage 4: Evaluation ────────────────────────────────────────────
    if not quiet:
        print_stage("Stage 4: Evaluation", 2, use_color)

    evaluation = evaluate(analysis, test_data, execution_result, config)

    elapsed = time.monotonic() - start

    return {
        "skill": analysis.get("name", "unknown"),
        "description": analysis.get("description", ""),
        "issues": analysis.get("issues", []),
        "bundle": analysis.get("bundle", {}),
        "anti_patterns": analysis.get("anti_patterns", []),
        "tests": test_data,
        "execution": execution_result,
        "evaluation": evaluation,
        "elapsed": round(elapsed, 2),
    }


# ── Entry ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
