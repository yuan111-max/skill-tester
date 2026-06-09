"""Stage 2: Test Case Generation.

Extracts trigger conditions, capabilities, and edge cases from SKILL.md
and produces structured test prompts for Stage 3 execution.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from scripts.utils import strip_frontmatter


# ── Public API ───────────────────────────────────────────────────────────


def generate_tests(
    skill_dir: Path,
    analysis: Dict[str, Any],
    config: Dict[str, Any],
    content: str = "",
) -> Dict[str, Any]:
    """Generate test cases from skill analysis.

    Parameters
    ----------
    skill_dir:
        Path to the skill directory.
    analysis:
        Output from ``analyze_skill()``.
    config:
        Full skill-tester configuration dict.
    content:
        Optional pre-read SKILL.md content.  If empty, reads from disk.

    Returns
    -------
    dict with keys:
        trigger_tests  — prompts that SHOULD trigger the skill
        non_trigger_tests — prompts that should NOT trigger it (negative tests)
        capabilities   — declared capabilities extracted from sections
        edge_cases     — boundary/error-case prompts
    """
    if not content:
        skill_md = skill_dir / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8") if skill_md.exists() else ""

    trigger_tests = _generate_trigger_tests(analysis, content, config)
    non_trigger_tests = _generate_negative_tests(analysis, content)
    capabilities = _extract_capabilities(analysis, content)
    edge_cases = _generate_edge_cases(content, analysis)

    # Deduplicate by prompt text
    seen: set = set()
    all_tests = []
    for t in trigger_tests + non_trigger_tests + edge_cases:
        key = t["prompt"].strip().lower()
        if key not in seen:
            seen.add(key)
            all_tests.append(t)

    # Apply max_tests cap
    max_tests = config.get("execution", {}).get("max_tests", 10)
    if 0 < max_tests < len(all_tests):
        # Prioritise: trigger > non-trigger > edge case
        priority = {"trigger": 0, "non_trigger": 1, "edge_case": 2}
        all_tests.sort(key=lambda t: (priority.get(t.get("type", ""), 9), t["prompt"]))
        all_tests = all_tests[:max_tests]

    # Also return structured capability list
    return {
        "tests": all_tests,
        "trigger_tests": trigger_tests,
        "non_trigger_tests": non_trigger_tests,
        "edge_cases": edge_cases,
        "capabilities": capabilities,
        "total_generated": len(all_tests),
    }


# ── Trigger tests ────────────────────────────────────────────────────────


_TRIGGER_KEYWORDS = [
    "when to use", "use when", "trigger", "invoked", "activated",
    "apply when", "run when", "execute when", "call this skill",
]


def _generate_trigger_tests(
    analysis: Dict[str, Any], content: str, config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate prompts that should trigger the skill."""
    tests: List[Dict[str, Any]] = []

    # 1. From trigger_info phrases (most reliable)
    seen_prompts: set = set()
    for phrase in analysis.get("trigger_info", {}).get("trigger_phrases", []):
        if phrase not in seen_prompts:
            seen_prompts.add(phrase)
            tests.append({
                "type": "trigger",
                "prompt": phrase,
                "expected_trigger": True,
                "source": "trigger_section",
            })

    # 2. From "When to Use" / usage sections
    for match in re.finditer(
        r"(?:##\s+(?:When to Use|Usage|Triggers?).*?\n)(.*?)(?=\n##\s|\Z)",
        content, re.IGNORECASE | re.DOTALL,
    ):
        bullets = re.findall(r"^\s*[-*]\s+(.+)$", match.group(1), re.MULTILINE)
        for b in bullets:
            b = b.strip().rstrip(".")
            if len(b) > 10 and not any(t["prompt"] == b for t in tests):
                tests.append({
                    "type": "trigger",
                    "prompt": b,
                    "expected_trigger": True,
                    "source": "usage_section",
                })

    # 3. From trigger keyword mentions in body
    for match in re.finditer(
        rf"(?:{'|'.join(_TRIGGER_KEYWORDS)})[:\s]+(.*?)(?:\n\n|\n##|\Z)",
        content, re.IGNORECASE | re.DOTALL,
    ):
        phrase = match.group(1).strip()
        if len(phrase) > 10 and not any(t["prompt"] == phrase for t in tests):
            tests.append({
                "type": "trigger",
                "prompt": phrase,
                "expected_trigger": True,
                "source": "keyword_match",
            })

    # 4. From skill name and description
    skill_name = analysis.get("name", "")
    if skill_name and skill_name != "unknown":
        tests.append({
            "type": "trigger",
            "prompt": f"I need to use the {skill_name} skill to handle this situation",
            "expected_trigger": True,
            "source": "name_based",
        })

    return tests


def _generate_negative_tests(analysis: Dict[str, Any], content: str) -> List[Dict[str, Any]]:
    """Generate prompts that should NOT trigger the skill."""
    skill_name = analysis.get("name", "this")
    skill_desc = analysis.get("description", "")

    # Generic unrelated prompts based on skill context
    negatives: List[Dict[str, Any]] = [
        {
            "type": "non_trigger",
            "prompt": "What is the weather like today?",
            "expected_trigger": False,
            "source": "generic_unrelated",
        },
    ]

    # If skill has a specific domain, add negative tests in that domain
    # but mentioning the wrong task
    domain_words = _extract_domain_words(skill_desc)
    if domain_words:
        domain_preview = " ".join(domain_words[:3])
        negatives.append({
            "type": "non_trigger",
            "prompt": f"Tell me about {domain_preview} generally, I don't need a specific task",
            "expected_trigger": False,
            "source": "domain_general_knowledge",
        })

    # Add skill-name-based negative (mentioning the name but not needing it)
    if skill_name != "unknown":
        negatives.append({
            "type": "non_trigger",
            "prompt": f"What does the {skill_name} skill do? Explain it to me.",
            "expected_trigger": False,
            "source": "meta_question",
        })

    return negatives


def _extract_domain_words(description: str) -> List[str]:
    """Extract domain-specific nouns from a description string."""
    # Simple heuristic: capitalised nouns and words after "for" / "in"
    # Matches both TitleCase and ALL-CAPS acronyms
    words = re.findall(r"\b[A-Z][a-z]{2,}\b", description)
    words += re.findall(r"\b[A-Z]{3,}\b", description)
    return words


# ── Capabilities extraction ──────────────────────────────────────────────


def _extract_capabilities(analysis: Dict[str, Any], content: str) -> List[Dict[str, str]]:
    """Extract declared capabilities from section headings and bullet points."""
    capabilities: List[Dict[str, str]] = []

    sections = analysis.get("content", {}).get("sections", [])
    for section in sections:
        section_lower = section.lower()
        if any(skip in section_lower for skip in ["when to use", "usage", "overview", "reference"]):
            continue
        capabilities.append({
            "name": section.strip(),
            "source": "section_heading",
        })

    # Also extract capability-like bullet points (verb phrases)
    body = strip_frontmatter(content)

    how_re = r"^\s*[-*]\s+(?:How to|Steps? to|Process for|Guide to)\s(.+)$"
    for match in re.finditer(how_re, body, re.MULTILINE | re.IGNORECASE):
        cap = match.group(1).strip().rstrip(".")
        if cap and not any(c["name"] == cap for c in capabilities):
            capabilities.append({"name": cap, "source": "bullet_point"})

    # Also match action-verb bullets (e.g. "Validate JSON files", "Generate reports")
    for match in re.finditer(r"^\s*[-*]\s+([A-Z].{9,})$", body, re.MULTILINE):
        cap = match.group(1).strip().rstrip(".")
        if cap and not any(c["name"] == cap for c in capabilities):
            # Skip bullets that look like trigger conditions
            skip_prefixes = ("when", "if", "before", "after", "to ", "for ", "in ", "on ")
            if not cap.lower().startswith(skip_prefixes):
                capabilities.append({"name": cap, "source": "bullet_point"})

    return capabilities


# ── Edge cases ───────────────────────────────────────────────────────────


def _generate_edge_cases(content: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate edge-case and error-path test prompts."""
    edge_cases: List[Dict[str, Any]] = []

    # Find "do not", "avoid", "warning", "caution", "limitation" sections
    for match in re.finditer(
        (
            r"(?:##\s+(?:Limitations?|Caveats?|Warnings?|Do Not|Avoid|Troubleshooting).*?\n)"
            r"(.*?)(?=\n##\s|\Z)"
        ),
        content, re.IGNORECASE | re.DOTALL,
    ):
        bullets = re.findall(r"^\s*[-*]\s+(.+)$", match.group(1), re.MULTILINE)
        for b in bullets:
            b = b.strip().rstrip(".")
            if len(b) > 10:
                edge_cases.append({
                    "type": "edge_case",
                    "prompt": b,
                    "expected_trigger": True,
                    "source": "constraint_section",
                })

    # Find explicit "do not" / "avoid" sentences in body
    for match in re.finditer(
        r"\b(?:do not|don't|avoid|never|must not)\b[^.]*\.",
        content, re.IGNORECASE,
    ):
        sentence = match.group(0).strip()
        if 20 < len(sentence) < 200 and not any(e["prompt"] == sentence for e in edge_cases):
            edge_cases.append({
                "type": "edge_case",
                "prompt": sentence,
                "expected_trigger": True,
                "source": "do_not_rule",
            })

    return edge_cases
