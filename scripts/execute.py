"""Stage 3: Test Execution.

Runs generated test prompts through the ``claude`` CLI and scores each
response for skill activation and correctness.  Falls back gracefully when
the CLI is unavailable or ``--execute`` was not passed.
"""

from __future__ import annotations

import concurrent.futures
import shutil
import subprocess
import sys
import time
import re
from typing import Any, Dict, List, Optional


# ── Public API ───────────────────────────────────────────────────────────


def execute_tests(
    test_data: Dict[str, Any],
    analysis: Dict[str, Any],
    config: Dict[str, Any],
    force: bool = False,
    quiet: bool = False,
) -> Dict[str, Any]:
    """Execute generated tests or return a skipped report.

    Parameters
    ----------
    test_data:
        Output from ``generate_tests()``.
    analysis:
        Output from ``analyze_skill()``.
    config:
        Full skill-tester configuration dict.
    force:
        Override ``execution.enabled`` check (set by ``--execute`` flag).
    quiet:
        Suppress progress output to stderr.

    Returns
    -------
    dict with keys: executed, results, summary, stats
    """
    exec_cfg = config.get("execution", {})
    enabled = force or exec_cfg.get("enabled", False)

    if not enabled:
        return _skipped_report(test_data, "Execution disabled. Pass --execute to enable.")

    claude_cmd = _resolve_claude(exec_cfg.get("claude_command", "claude"))
    if claude_cmd is None:
        return _skipped_report(
            test_data,
            f"CLI '{exec_cfg.get('claude_command', 'claude')}' not found in PATH.",
        )

    return _run_tests(test_data, claude_cmd, exec_cfg, analysis, quiet=quiet)


# ── Internal execution helpers ───────────────────────────────────────────


def _resolve_claude(command: str) -> Optional[str]:
    """Return the resolved path to the Claude CLI, or None."""
    # On Windows, check both the command and command.cmd
    candidates = [command]
    if sys.platform == "win32":
        candidates.append(f"{command}.cmd")
        candidates.append(f"{command}.exe")

    for cmd in candidates:
        resolved = _which(cmd)
        if resolved:
            return resolved
    return None


def _which(program: str) -> Optional[str]:
    """Resolve *program* path via ``shutil.which()``."""
    return shutil.which(program)


def _run_tests(
    test_data: Dict[str, Any],
    claude_cmd: str,
    exec_cfg: Dict[str, Any],
    analysis: Dict[str, Any],
    quiet: bool = False,
) -> Dict[str, Any]:
    """Execute each test through the Claude CLI subprocess in parallel.

    Uses a thread pool (max 4 workers) so that N tests with a 3-minute
    timeout complete in ~3 minutes instead of N × 3 minutes.
    """
    tests = test_data.get("tests", [])
    max_tests = exec_cfg.get("max_tests", 10)
    timeout = exec_cfg.get("timeout_seconds", 180)
    claude_args = exec_cfg.get("claude_args", ["--non-interactive", "--print"])

    if 0 < max_tests < len(tests):
        tests = tests[:max_tests]

    skill_name = analysis.get("name", "the skill") or "the skill"

    n = len(tests)
    results: List[Optional[Dict[str, Any]]] = [None] * n  # ordered result slots
    stats = {"total": n, "passed": 0, "failed": 0, "error": 0, "skipped": 0}

    if n == 0:
        return {"executed": True, "results": [], "summary": stats, "stats": stats}

    # Track whether we're still "live" — if ALL tests FileNotFoundError we abort
    live_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, n)) as pool:
        future_to_idx = {
            pool.submit(
                _run_single_test, i, test, claude_cmd, claude_args, timeout, skill_name
            ): i
            for i, test in enumerate(tests)
        }

        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                result = future.result()
            except FileNotFoundError:
                return _skipped_report(
                    test_data,
                    f"CLI '{claude_cmd}' not found at execution time.",
                )

            results[idx] = result
            status = result["status"]
            if status == "PASS":
                stats["passed"] += 1
            elif status == "FAIL":
                stats["failed"] += 1
            else:
                stats["error"] += 1

            elapsed = result.get("elapsed_seconds", 0)
            if not quiet:
                print(
                    f"  [{live_count + 1}/{n}] {status:6s} {elapsed:4.1f}s  "
                    f"{result.get('prompt', '')[:50]}",
                    file=sys.stderr,
                )
            live_count += 1

    return {
        "executed": True,
        "results": results,
        "summary": stats,
        "stats": stats,
    }


def _run_single_test(
    index: int,
    test: Dict[str, Any],
    claude_cmd: str,
    claude_args: List[str],
    timeout: int,
    skill_name: str,
) -> Dict[str, Any]:
    """Execute a single test prompt and return its result dict.

    This function is designed to run in a thread (CPython GIL makes
    subprocess calls non-blocking), so keep it self-contained.
    """
    prompt = test["prompt"]
    expected = test.get("expected_trigger", True)

    start = time.monotonic()
    try:
        cmd = [claude_cmd] + claude_args + [prompt]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.monotonic() - start
        response = proc.stdout or proc.stderr or ""

        triggered = _detect_skill_activation(response, skill_name)
        passed = triggered == expected
        status = "PASS" if passed else "FAIL"

        return {
            **test,
            "status": status,
            "response_preview": response[:200].strip(),
            "triggered": triggered,
            "elapsed_seconds": round(elapsed, 2),
            "note": None,
        }

    except FileNotFoundError:
        raise  # Propagated to caller which returns a skipped report
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        return {
            **test,
            "status": "TIMEOUT",
            "response_preview": "",
            "triggered": None,
            "elapsed_seconds": round(elapsed, 2),
            "note": f"Timed out after {timeout}s",
        }
    except Exception as exc:
        return {
            **test,
            "status": "ERROR",
            "response_preview": "",
            "triggered": None,
            "elapsed_seconds": 0,
            "note": str(exc),
        }


def _detect_skill_activation(response: str, skill_name: str) -> bool:
    """Heuristic: detect if the skill was activated in the response.

    Looks for:
    - References to the skill's name or instructions
    - Structured output matching the skill's domain
    - Section headers or keywords from the skill
    """
    response_lower = response.lower()
    indicators: List[str] = []

    # 1. Skill name mention
    if skill_name and skill_name != "unknown":
        indicators.append(skill_name.lower())

    # 2. Common skill-activation phrases
    indicators.extend([
        "i'll use the", "according to the skill", "based on the skill",
        "following the", "as per the", "the skill provides",
        "skill instructions", "skill guidance",
    ])

    # 3. Section-like headers in response (suggests structured output)
    has_sections = bool(re.search(r"^#{1,3}\s", response, re.MULTILINE))

    # 4. Code blocks in response (another heuristic)
    has_code = "```" in response

    # Score: check if any indicator phrase appears
    phrase_match = any(indicator in response_lower for indicator in indicators)

    # Combined heuristic: phrase match OR (sections AND code)
    return phrase_match or (has_sections and has_code)


# ── Skipped report ───────────────────────────────────────────────────────


def _skipped_report(test_data: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Return a report with all tests marked SKIPPED."""
    tests = test_data.get("tests", [])
    results = [
        {**t, "status": "SKIPPED", "note": reason}
        for t in tests
    ]
    return {
        "executed": False,
        "results": results,
        "summary": {
            "total": len(tests),
            "passed": 0,
            "failed": 0,
            "error": 0,
            "skipped": len(tests),
        },
        "stats": {"total": len(tests), "passed": 0, "failed": 0, "error": 0, "skipped": len(tests)},
        "skip_reason": reason,
    }
