# 4D Scoring Rubric — Detailed Guide

---

## Documentation (weight: 25%)

Measures SKILL.md clarity, structure, examples, and trigger clarity.

| Score | Level | Indicators |
|-------|-------|------------|
| 10 | Exemplary | Every capability has concrete examples; decision trees for branches; explicit "When to Use"; no ambiguity |
| 8–9 | Strong | Well-structured sections; most scenarios have examples; trigger conditions clearly stated; 4+ sections |
| 6–7 | Adequate | Functional but generic; some sections have no examples; trigger conditions vague |
| 4–5 | Weak | Template content; "TODO" placeholders; no real examples; user must infer intent |
| 0–3 | Failing | No SKILL.md or completely generic; no actionable guidance |

### Scoring Method (sub-scores)

| Sub-score | Weight | Calculation |
|-----------|--------|-------------|
| frontmatter_validity | 15% | 10 - 3 × (frontmatter issues). Clamped 0–10 |
| section_coverage | 25% | 10 if ≥6 sections; 8 if ≥4; 6 if ≥2; else 2 |
| example_density | 20% | 10 if ≥6 examples; 8 if ≥4; 6 if ≥2; 4 if ≥1; else 2. -3 if TODOs exist |
| specificity_and_clarity | 25% | 10 - 2 × (template_artifact + filler anti-patterns). Clamped 0–10 |
| trigger_clarity | 15% | 10 if ≥5 trigger phrases; 8 if ≥3; 5 if ≥1; else 2 |

### Deduction Rules
- Every frontmatter issue (missing name, missing description, angle brackets, too short): **-3**
- Every "TODO"/"FIXME"/"XXX" placeholder: **-3 from example_density**
- Every template artifact or filler anti-pattern: **-2 from specificity**

---

## Code (weight: 25%)

Measures quality of bundled scripts — correctness, error handling, determinism.

| Score | Level | Indicators |
|-------|-------|------------|
| 10 | Exemplary | All scripts executable; comprehensive error handling; docstrings; deterministic output |
| 8–9 | Strong | Scripts work correctly; minor edge-case issues; basic docstrings |
| 6–7 | Adequate | Scripts functional but incomplete error handling; no docstrings |
| 4–5 | Weak | Scripts have bugs; crash on valid input; unclear purpose |
| 0–3 | Failing | No scripts or all scripts broken |

### Scoring Method (sub-scores)

| Sub-score | Weight | Calculation |
|-----------|--------|-------------|
| script_presence | 10% | 10 if ≥3 scripts; 7 if ≥1; 2 if none |
| syntactic_validity | 35% | (valid_count / total_count) × 10. 5 baseline if no scripts |
| error_handling | 30% | 2 + (I/O scripts with try/except / I/O scripts) × 8. 8 if all pure-logic scripts. 5 baseline if no scripts |
| script_documentation | 25% | (scripts_with_docstring_or_shebang / total) × 10. 5 baseline if no scripts |

### Key Distinctions

- **I/O vs pure-logic scripts**: Scripts performing file I/O, network calls,
  or subprocess execution are flagged as `needs_error_handling`. Only these
  scripts count toward the error_handling denominator — pure-logic scripts
  (config readers, formatters, pure functions) do not penalise the skill.
- **No-script baseline**: Skills without bundled scripts receive a neutral
  baseline of 5 for validity, error_handling, and documentation, so
  documentation-only skills are not unreasonably penalised. The
  script_presence sub-score still signals the absence (2/10).

### Checklist
- [ ] `python3 -m py_compile` passes for all `.py` scripts
- [ ] Scripts handle missing input gracefully (exit with error, not crash)
- [ ] Scripts produce deterministic output
- [ ] Each script has a docstring or `--help` flag
- [ ] Shell scripts have a shebang line (`#!/usr/bin/env bash`)

---

## Completeness (weight: 25%)

Measures coverage of all declared capabilities — no critical gaps.

| Score | Level | Indicators |
|-------|-------|------------|
| 10 | Exemplary | Every declared capability has implementation; edge cases covered; no gaps |
| 8–9 | Strong | >90% coverage; minor edge-case gaps |
| 6–7 | Adequate | 70–90% coverage; some declared features missing |
| 4–5 | Partial | 40–70% coverage; significant gaps |
| 0–3 | Incomplete | <40% coverage; most declared features not implemented |

### Scoring Method (sub-scores)

| Sub-score | Weight | Calculation |
|-----------|--------|-------------|
| capability_coverage | 40% | 10 if ≥8 capabilities; 8 if ≥5; 6 if ≥3; 4 if ≥1; else 2 |
| edge_case_coverage | 30% | min(10, edge_cases × 2 + non_trigger_tests) |
| section_completeness | 30% | (1 - missing_required / total_required) × 10 |

### Method
1. Extract every capability from the skill's section headings and action-oriented bullets
2. Count edge case sections (Limitations, Caveats, Warnings, Do Not, Avoid)
3. Check for required section coverage vs. actual sections
4. Score based on sub-score weighted average

---

## Usability (weight: 25%)

Measures skill triggers correctly; instructions are actionable; edge cases handled.

| Score | Level | Indicators |
|-------|-------|------------|
| 10 | Exemplary | Skill always triggers on correct prompts; instructions unambiguous; edge cases explicit |
| 8–9 | Strong | Usually triggers correctly; one-prompt edge cases need minor work |
| 6–7 | Adequate | Triggers ~75% of time; some prompts need manual invocation |
| 4–5 | Weak | Trigger conditions vague; user often bypasses skill |
| 0–3 | Unusable | Skill rarely triggers; instructions contradictory or missing |

### Scoring Method (sub-scores)

| Sub-score | Weight | Calculation |
|-----------|--------|-------------|
| trigger_accuracy | 30% | (passed_tests / total_tests) × 10 if executed; else min(10, trigger_phrases × 2) |
| instruction_actionability | 30% | 10 if ≥15 bullet points; 8 if ≥10; 6 if ≥5; 4 if ≥2; else 2 |
| edge_case_handling | 20% | 8 if "do not/avoid/warning/caution/limitation" sections exist; else 4 |
| progressive_disclosure | 20% | 10 if H1 + ≥4 H2 + ≥2 H3; 7 if ≥3 H2; 5 if ≥1 H2; else 2 |

### A/B Test for Trigger Accuracy (with --execute)
- Run 10 representative prompts — 5 should trigger, 5 should not
- Score: `(true_positives + true_negatives) / total` × 10
- This replaces the structural proxy when execution data is available

---

## Final Score Formula

```
final = (Documentation × 0.25) + (Code × 0.25) + (Completeness × 0.25) + (Usability × 0.25)
```

All dimensions scored 0–10. Final is a weighted average, also 0–10.

## Tier Thresholds

| Score   | Tier       | Deployment                                   |
|---------|------------|----------------------------------------------|
| ≥ 8.5   | POWERFUL   | Deploy immediately; benchmark for others      |
| ≥ 7.0   | STANDARD   | Good to deploy; address minor gaps            |
| ≥ 5.0   | BASIC      | Functional; needs improvement                 |
| < 5.0   | REJECT     | Major rewrites required                       |

---

## Updating Thresholds

All thresholds, weights, and deduction rules are defined in
[`config/default.yaml`](../config/default.yaml).  Edit that file (or
create a `config/local.yaml` override) to tune the scoring for your
use case without modifying any Python code.
