"""Stage 4: Evaluation — multi-dimensional scoring and tier classification.

Computes a 0-10 score per dimension using configurable sub-scores,
aggregates to a weighted final score, and maps it to a deployment tier.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import resolve_tier


# ── Public API ───────────────────────────────────────────────────────────


def evaluate(
    analysis: Dict[str, Any],
    test_data: Dict[str, Any],
    execution_result: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute dimension scores, final score, and tier.

    Parameters
    ----------
    analysis:
        Output from ``analyze_skill()``.
    test_data:
        Output from ``generate_tests()``.
    execution_result:
        Output from ``execute_tests()``.
    config:
        Full skill-tester configuration dict.

    Returns
    -------
    dict with keys: dimensions (per-dimension scores),
                     final (0-10 float), tier (str)
    """
    scoring_cfg = config.get("scoring", {})
    dimensions_cfg = scoring_cfg.get("dimensions", {})

    # Compute each dimension
    scores: Dict[str, float] = {}
    details: Dict[str, Any] = {}

    for dim_name, dim_cfg in dimensions_cfg.items():
        score_fn = _SCORERS.get(dim_name)
        if score_fn is None:
            continue
        score, detail = score_fn(analysis, test_data, execution_result, config)
        scores[dim_name] = round(score, 2)
        details[dim_name] = detail

    # Weighted final score (0-10 scale)
    final = sum(
        scores.get(dim, 0) * dim_cfg.get("weight", 0)
        for dim, dim_cfg in dimensions_cfg.items()
    )
    final = round(final, 2)

    tiers_cfg = scoring_cfg.get("tiers", {})
    tier = resolve_tier(final, tiers_cfg)

    return {
        "dimensions": scores,
        "details": details,
        "final": final,
        "tier": tier,
    }


# ── Scorer registry ──────────────────────────────────────────────────────

_SCORERS = {}


def _scorer(name: str):
    """Decorator to register a dimension scorer."""
    def wrapper(fn):
        _SCORERS[name] = fn
        return fn
    return wrapper


# ── Documentation (25%) ──────────────────────────────────────────────────


@_scorer("Documentation")
def _score_documentation(
    analysis: Dict[str, Any],
    test_data: Dict[str, Any],
    execution_result: Dict[str, Any],
    config: Dict[str, Any],
) -> tuple:
    """Score SKILL.md clarity, structure, and examples.

    Sub-scores (weights from config, or these defaults):
        frontmatter_validity  (15%)
        section_coverage      (25%)
        example_density       (20%)
        specificity_clarity   (25%)
        trigger_clarity       (15%)
    """
    content = analysis.get("content", {})
    issues = analysis.get("issues", [])
    desc = analysis.get("description", "")
    anti_patterns = analysis.get("anti_patterns", [])

    # 1. Frontmatter validity (0-10)
    fm_issues = [i for i in issues if "frontmatter" in i.lower() or "description" in i.lower() or "name" in i.lower()]
    fm_score = max(0, 10 - len(fm_issues) * 3)

    # 2. Section coverage (0-10)
    sections = content.get("sections", [])
    sec_count = len(sections)
    if sec_count >= 6:
        sec_score = 10
    elif sec_count >= 4:
        sec_score = 8
    elif sec_count >= 2:
        sec_score = 6
    elif sec_count >= 1:
        sec_score = 4
    else:
        sec_score = 2

    # 3. Example density (0-10)
    examples = content.get("example_count", 0)
    min_ex = config.get("analysis", {}).get("min_examples", 2)
    if examples >= min_ex * 3:
        ex_score = 10
    elif examples >= min_ex * 2:
        ex_score = 8
    elif examples >= min_ex:
        ex_score = 6
    elif examples >= 1:
        ex_score = 4
    else:
        ex_score = 2

    # Penalty for TODO / placeholders
    if analysis.get("has_todo"):
        ex_score = max(0, ex_score - 3)

    # 4. Specificity & clarity (0-10)
    vague_count = sum(1 for ap in anti_patterns if ap.get("type") in ("template_artifact", "filler"))
    specific_score = max(0, 10 - vague_count * 2)

    # 5. Trigger clarity (0-10)
    trigger_count = analysis.get("trigger_info", {}).get("trigger_count", 0)
    if trigger_count >= 5:
        trig_score = 10
    elif trigger_count >= 3:
        trig_score = 8
    elif trigger_count >= 1:
        trig_score = 5
    else:
        trig_score = 2

    # Weighted combination
    subs = {
        "frontmatter_validity": fm_score,
        "section_coverage": sec_score,
        "example_density": ex_score,
        "specificity_and_clarity": specific_score,
        "trigger_clarity": trig_score,
    }
    weights = _sub_weights(config, "Documentation", subs)

    total = sum(subs[k] * weights.get(k, 0.2) for k in subs)

    detail = {**subs, "weights": weights, "anti_patterns_penalised": vague_count}
    return total, detail


# ── Code (25%) ───────────────────────────────────────────────────────────


@_scorer("Code")
def _score_code(
    analysis: Dict[str, Any],
    test_data: Dict[str, Any],
    execution_result: Dict[str, Any],
    config: Dict[str, Any],
) -> tuple:
    """Score bundled scripts for correctness, error handling, documentation.

    Sub-scores:
        script_presence     (10%)
        syntactic_validity  (35%)
        error_handling      (30%)
        script_documentation (25%)
    """
    scripts = analysis.get("scripts", {})
    bundle = analysis.get("bundle", {})

    total_count = scripts.get("total_count", 0)
    valid_count = scripts.get("valid_count", 0)
    script_list = scripts.get("results", [])

    # 1. Script presence (0-10)
    if total_count >= 3:
        presence = 10
    elif total_count >= 1:
        presence = 7
    else:
        presence = 2  # No scripts

    # 2. Syntactic validity (0-10)
    if total_count > 0:
        validity = (valid_count / total_count) * 10
    else:
        validity = 10  # No scripts = no syntax errors = N/A treated as full score

    # 3. Error handling proxy (0-10)
    # Count scripts that actually contain try/except (pre-computed in analyze.py)
    eh_score = 5  # baseline
    for r in script_list:
        if r.get("has_try_except"):
            eh_score += 1
    eh_score = min(10, eh_score)

    # 4. Script documentation (0-10)
    if total_count > 0:
        doc_count = sum(1 for r in script_list if r.get("has_docstring") or r.get("has_shebang"))
        doc_score = (doc_count / total_count) * 10
    else:
        doc_score = 10

    subs = {
        "script_presence": round(presence, 1),
        "syntactic_validity": round(validity, 1),
        "error_handling": round(eh_score, 1),
        "script_documentation": round(doc_score, 1),
    }
    weights = _sub_weights(config, "Code", subs)
    total = sum(subs[k] * weights.get(k, 0.25) for k in subs)

    return total, subs


# ── Completeness (25%) ───────────────────────────────────────────────────


@_scorer("Completeness")
def _score_completeness(
    analysis: Dict[str, Any],
    test_data: Dict[str, Any],
    execution_result: Dict[str, Any],
    config: Dict[str, Any],
) -> tuple:
    """Score coverage of declared capabilities.

    Sub-scores:
        capability_coverage (40%)
        edge_case_coverage  (30%)
        section_completeness (30%)
    """
    capabilities = test_data.get("capabilities", [])
    sections = analysis.get("content", {}).get("sections", [])

    # 1. Capability coverage (0-10)
    cap_count = len(capabilities)
    if cap_count >= 8:
        cap_score = 10
    elif cap_count >= 5:
        cap_score = 8
    elif cap_count >= 3:
        cap_score = 6
    elif cap_count >= 1:
        cap_score = 4
    else:
        cap_score = 2

    # 2. Edge case coverage (0-10)
    edge_count = len(test_data.get("edge_cases", []))
    non_trigger_count = len(test_data.get("non_trigger_tests", []))
    edge_score = min(10, edge_count * 2 + non_trigger_count)

    # 3. Section completeness (0-10): ratio of content sections to required
    required = config.get("analysis", {}).get("required_sections", [])
    if required:
        missing = analysis.get("content", {}).get("missing_required_sections", [])
        completeness_ratio = 1 - (len(missing) / len(required))
        sec_complete = completeness_ratio * 10
    else:
        sec_complete = 10

    subs = {
        "capability_coverage": round(cap_score, 1),
        "edge_case_coverage": min(10, round(edge_score, 1)),
        "section_completeness": round(sec_complete, 1),
    }
    weights = _sub_weights(config, "Completeness", subs)
    total = sum(subs[k] * weights.get(k, 0.33) for k in subs)

    return total, subs


# ── Usability (25%) ──────────────────────────────────────────────────────


@_scorer("Usability")
def _score_usability(
    analysis: Dict[str, Any],
    test_data: Dict[str, Any],
    execution_result: Dict[str, Any],
    config: Dict[str, Any],
) -> tuple:
    """Score how usable the skill is.

    Sub-scores:
        trigger_accuracy        (30%) — uses execution results if available
        instruction_actionability (30%)
        edge_case_handling      (20%)
        progressive_disclosure  (20%)
    """
    issues = analysis.get("issues", [])

    # 1. Trigger accuracy (0-10)
    was_executed = execution_result.get("executed", False)
    if was_executed:
        exec_summary = execution_result.get("summary", {})
        exec_total = exec_summary.get("total", 0)
        exec_passed = exec_summary.get("passed", 0)
        if exec_total > 0:
            trig_accuracy = (exec_passed / exec_total) * 10
        else:
            trig_accuracy = 5  # neutral score for empty execution
    else:
        # Without execution, score based on trigger info quality
        trigger_count = analysis.get("trigger_info", {}).get("trigger_count", 0)
        trig_accuracy = min(10, trigger_count * 2)

    # 2. Instruction actionability (0-10)
    # Proxy: bullet-list density in SKILL.md body
    content = _read_skill_body(analysis)
    bullets = len(re.findall(r"^\s*[-*]\s+", content, re.MULTILINE)) if content else 0
    if bullets >= 15:
        actionable = 10
    elif bullets >= 10:
        actionable = 8
    elif bullets >= 5:
        actionable = 6
    elif bullets >= 2:
        actionable = 4
    else:
        actionable = 2

    # 3. Edge case handling (0-10)
    has_do_not = bool(re.search(r"(?:do not|avoid|warning|caution|limitation)", content, re.IGNORECASE)) if content else False
    edge_handling = 8 if has_do_not else 4

    # 4. Progressive disclosure (0-10)
    # Check for well-structured heading hierarchy
    headers = re.findall(r"^(#{1,3})\s", content, re.MULTILINE) if content else []
    h1_count = sum(1 for h in headers if h == "#")
    h2_count = sum(1 for h in headers if h == "##")
    h3_count = sum(1 for h in headers if h == "###")
    if h1_count >= 1 and h2_count >= 4 and h3_count >= 2:
        progressive = 10
    elif h2_count >= 3:
        progressive = 7
    elif h2_count >= 1:
        progressive = 5
    else:
        progressive = 2

    subs = {
        "trigger_accuracy": round(trig_accuracy, 1),
        "instruction_actionability": round(actionable, 1),
        "edge_case_handling": round(edge_handling, 1),
        "progressive_disclosure": round(progressive, 1),
    }
    weights = _sub_weights(config, "Usability", subs)
    total = sum(subs[k] * weights.get(k, 0.25) for k in subs)

    return total, subs


# ── Helpers ──────────────────────────────────────────────────────────────


def _sub_weights(config: Dict[str, Any], dim_name: str, subs: Dict[str, float]) -> Dict[str, float]:
    """Extract sub-score weights from config, falling back to uniform."""
    dim_cfg = config.get("scoring", {}).get("dimensions", {}).get(dim_name, {})
    sub_cfgs = dim_cfg.get("sub_scores", [])
    if sub_cfgs:
        weights = {}
        for sc in sub_cfgs:
            if sc.get("name") in subs:
                weights[sc["name"]] = sc.get("weight", 0)
        # Normalise
        total_w = sum(weights.values())
        if total_w > 0:
            return {k: v / total_w for k, v in weights.items()}
    # Uniform fallback
    return {k: 1.0 / len(subs) for k in subs}


def _read_skill_body(analysis: Dict[str, Any]) -> str:
    """Read SKILL.md body stashed by the pipeline in analysis['_body']."""
    return analysis.get("_body", "")
