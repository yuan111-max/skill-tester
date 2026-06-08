"""Output formatters for skill-tester results.

Provides JSON, table, and human-readable summary output for evaluation reports.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


# ── JSON output ────────────────────────────────────────────────────────────


def output_json(reports: List[Dict[str, Any]], dirs: List[Path]) -> None:
    """Print JSON report array to stdout."""
    output = []
    for report, d in zip(reports, dirs):
        item = {
            "path": str(d),
            "skill": report.get("skill"),
            "description": report.get("description"),
            "issues": report.get("issues", []),
            "evaluation": report.get("evaluation"),
            "elapsed_seconds": report.get("elapsed"),
        }
        if "error" in report:
            item["error"] = report["error"]
        output.append(item)
    print(json.dumps(output, indent=2, ensure_ascii=False))


# ── Table output ───────────────────────────────────────────────────────────


def output_table(reports: List[Dict[str, Any]], dirs: List[Path], use_color: bool) -> None:
    """Print a comparison table for multiple skills."""
    if not reports:
        return

    headers = ["Dimension"] + [r.get("skill", f"skill-{i}") for i, r in enumerate(reports)]

    # Compute column width from headers AND content values so that
    # wide values (e.g. "7.90  POWERFUL") don't overflow.
    all_widths = [len(h) for h in headers]
    for r in reports:
        ev = r.get("evaluation", {})
        for name, score in ev.get("dimensions", {}).items():
            all_widths.append(len(f"{score:.1f}"))
        final = ev.get("final", "-")
        tier = ev.get("tier", "")
        if isinstance(final, (int, float)):
            all_widths.append(len(f"{final:.2f}  {tier}"))
        else:
            all_widths.append(len(str(final)))
    col_width = max(all_widths) + 2
    sep = "-" * col_width

    print(f"\n{'=' * (col_width * len(headers))}")
    print(f"{'SKILL COMPARISON':^{col_width * len(headers)}}")
    print(f"{'=' * (col_width * len(headers))}")

    dims = list(reports[0].get("evaluation", {}).get("dimensions", {}).keys())
    for dim in dims:
        row = [dim]
        for r in reports:
            score = r.get("evaluation", {}).get("dimensions", {}).get(dim, "-")
            row.append(f"{score:.1f}" if isinstance(score, (int, float)) else str(score))
        _print_table_row(row, col_width)

    print(sep * len(headers))

    final_row = ["FINAL"]
    for r in reports:
        final = r.get("evaluation", {}).get("final", "-")
        tier = r.get("evaluation", {}).get("tier", "")
        if isinstance(final, (int, float)):
            final_row.append(f"{final:.2f}  {tier}")
        else:
            final_row.append(str(final))
    _print_table_row(final_row, col_width, bold=use_color)

    issue_row = ["Issues"]
    for r in reports:
        issue_row.append(str(len(r.get("issues", []))))
    _print_table_row(issue_row, col_width)

    elapsed_row = ["Elapsed (s)"]
    for r in reports:
        elapsed_row.append(str(r.get("elapsed", "-")))
    _print_table_row(elapsed_row, col_width)

    print()


def _print_table_row(row: List[str], width: int, bold: bool = False) -> None:
    """Print one table row with fixed-width columns."""
    parts = [f"{cell:{width}}" for cell in row]
    line = "".join(parts)
    if bold:
        print(f"\033[1m{line}\033[0m")
    else:
        print(line)


# ── Summary output ─────────────────────────────────────────────────────────


def output_summary(report: Dict[str, Any], skill_dir: Path, use_color: bool) -> None:
    """Print a human-readable summary report for one skill."""
    if "error" in report:
        print(f"  [!] {report['error']}")
        return

    ev = report.get("evaluation", {})
    dims = ev.get("dimensions", {})
    tier = ev.get("tier", "UNKNOWN")
    final = ev.get("final", 0)
    issues = report.get("issues", [])
    ap_count = len(report.get("anti_patterns", []))
    exec_info = report.get("execution", {})
    exec_summary = exec_info.get("summary", {})
    elapsed = report.get("elapsed", 0)

    name = report.get("skill", "unknown")
    desc = report.get("description", "")

    B = "\033[1m" if use_color else ""
    R = "\033[0m" if use_color else ""

    print(f"\n{'=' * 60}")
    print(f"{B}  Skill Tester Report: {name}{R}")
    print(f"{'=' * 60}")
    print(f"  Path:       {skill_dir}")
    print(f"  Description: {desc[:80]}")
    print(f"  Elapsed:    {elapsed}s")

    if issues:
        print(f"\n  {B}Structural Issues ({len(issues)}){R}")
        for issue in issues[:5]:
            print(f"    [!] {issue}")
        if len(issues) > 5:
            print(f"    ... and {len(issues) - 5} more")
    else:
        print(f"\n  [OK] No structural issues found")

    if ap_count > 0:
        print(f"  [!] {ap_count} anti-pattern(s) detected (see --output json for details)")

    bundle = report.get("bundle", {})
    print(f"\n  Bundle:")
    print(f"    scripts={bundle.get('scripts_count', 0)}  "
          f"references={bundle.get('references_count', 0)}  "
          f"assets={bundle.get('assets_count', 0)}")

    tests = report.get("tests", {})
    print(f"  Tests generated: {tests.get('total_generated', 0)}")

    if exec_info.get("executed"):
        print(f"  Execution: {exec_summary.get('passed', 0)}/{exec_summary.get('total', 0)} passed "
              f"({exec_summary.get('failed', 0)} failed)")
    else:
        print(f"  Execution: SKIPPED (pass --execute to run live tests)")

    print(f"\n  {B}4D Scores:{R}")
    for dim, score in dims.items():
        bar_len = int(score) if score else 0
        bar = "#" * bar_len + "-" * (10 - bar_len)
        print(f"    {dim:<16} {bar} {score:.1f}/10")

    print(f"\n  {'-' * 40}")
    tier_colored = color_tier(tier) if use_color else tier
    print(f"  {B}Final Score: {final:.2f}  ->  {tier_colored}{R}")
    print(f"{'=' * 60}\n")


# ── Terminal helpers ───────────────────────────────────────────────────────


def color_tier(tier: str) -> str:
    """Wrap tier name in ANSI colour codes."""
    colors = {
        "POWERFUL": "\033[32m",
        "STANDARD": "\033[34m",
        "BASIC": "\033[33m",
        "REJECT": "\033[31m",
    }
    color = colors.get(tier, "\033[0m")
    return f"{color}{tier}\033[0m"


def stdout_is_tty() -> bool:
    """Check if stdout is a TTY (for colour support)."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def print_stage(label: str, level: int = 1, use_color: bool = True) -> None:
    """Print a stage header to stderr with indentation."""
    indent = "  " * (level - 1)
    prefix = ">" if level == 1 else "."
    B = "\033[1m" if use_color else ""
    R = "\033[0m" if use_color else ""
    print(f"{indent}{prefix} {B}{label}{R}", file=sys.stderr)
