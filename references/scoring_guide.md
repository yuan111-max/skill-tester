# 4D Scoring Rubric — Detailed Guide

## Documentation (weight: 25%)

Measures: SKILL.md clarity, structure, examples, and trigger clarity.

| Score | Level | Indicators |
|-------|-------|-----------|
| 10 | Exemplary | Every capability has a concrete example; decision trees for branches; explicit "When to Use"; no ambiguity |
| 8–9 | Strong | Well-structured sections; most scenarios have examples; trigger conditions clearly stated |
| 6–7 | Adequate | Functional but generic; some sections have no examples; trigger conditions vague |
| 4–5 | Weak | Template content; "TODO" placeholders; no real examples; user must infer intent |
| 0–3 | Failing | No SKILL.md or completely generic; no actionable guidance |

**Deductions:**
- `-2` per structural issue (missing `---`, angle brackets in description, etc.)
- `-3` if `[TODO` placeholders remain in body
- `-2` if description < 20 chars

---

## Code/Scripts (weight: 25%)

Measures: Quality of bundled scripts — correctness, error handling, determinism.

| Score | Level | Indicators |
|-------|-------|-----------|
| 10 | Exemplary | All scripts executable; comprehensive error handling; docstrings; deterministic output |
| 8–9 | Strong | Scripts work correctly; minor edge-case issues; basic docstrings |
| 6–7 | Adequate | Scripts functional but incomplete error handling; no docstrings |
| 4–5 | Weak | Scripts have bugs; crash on valid input; unclear purpose |
| 0–3 | Failing | No scripts or all scripts broken |

**Checklist:**
- [ ] `python3 -m py_compile` passes for all `.py` scripts
- [ ] Scripts handle missing input gracefully (exit with error, not crash)
- [ ] Scripts produce deterministic output
- [ ] Each script has a docstring or `--help` flag

---

## Completeness (weight: 25%)

Measures: Coverage of all declared capabilities — no critical gaps.

| Score | Level | Indicators |
|-------|-------|-----------|
| 10 | Exemplary | Every declared capability has implementation; edge cases covered; no gaps |
| 8–9 | Strong | >90% coverage; minor edge-case gaps |
| 6–7 | Adequate | 70–90% coverage; some declared features missing |
| 4–5 | Partial | 40–70% coverage; significant gaps |
| 0–3 | Incomplete | <40% coverage; most declared features not implemented |

**Method:**
1. Extract every capability from the skill's frontmatter `description` and body
2. Check if each capability has corresponding instructions
3. Score based on % coverage

---

## Usability (weight: 25%)

Measures: Skill triggers correctly; instructions are actionable; edge cases handled.

| Score | Level | Indicators |
|-------|-------|-----------|
| 10 | Exemplary | Skill always triggers on correct prompts; instructions unambiguous; edge cases explicit |
| 8–9 | Strong | Usually triggers correctly; one-prompt edge cases need minor work |
| 6–7 | Adequate | Triggers ~75% of time; some prompts need manual invocation |
| 4–5 | Weak | Trigger conditions vague; user often bypasses skill |
| 0–3 | Unusable | Skill rarely triggers; instructions contradictory or missing |

**A/B Test for Trigger Accuracy:**
- Run 10 representative prompts — 5 should trigger, 5 should not
- Score: `(true_positives + true_negatives) / 10`
- Convert to 0–10 scale

---

## Final Score Formula

```
final = (Doc/10 × 0.25) + (Code/10 × 0.25) + (Comp/10 × 0.25) + (Usable/10 × 0.25)
```

## Tier Thresholds

| Score | Tier | Deployment |
|-------|------|-----------|
| ≥ 0.85 | **POWERFUL** | Deploy immediately; benchmark for others |
| ≥ 0.70 | **STANDARD** | Good to deploy; address minor gaps |
| ≥ 0.50 | **BASIC** | Functional; needs improvement |
| < 0.50 | **REJECT** | Major rewrites required |
