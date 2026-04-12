---
name: skill-tester
description: Tests and evaluates any Claude Code skill for structural validity, quality, and trigger accuracy. Implements the cc-plugin-eval 4-stage pipeline (Analysis → Generation → Execution → Evaluation) and the 4D scoring rubric (Documentation/Code/Completeness/Usability 25% each). Use before packaging or deploying any skill.
---

# Skill Tester

Validate, test, and score Claude Code skills using a rigorous 4-stage evaluation pipeline.

## When to Use

- Before packaging a newly created or upgraded skill (`package_skill.py`)
- After modifying any skill's SKILL.md or scripts
- During skill development to catch structural issues early
- To compare the quality of two competing skill implementations
- Triggered automatically by `/skill-test <skill-name>` or when debugging a skill trigger failure

## 4-Stage Evaluation Pipeline

### Stage 1: Analysis

**Goal**: Understand skill structure and extract trigger conditions.

1. Read the skill's `SKILL.md` fully.
2. Parse YAML frontmatter — extract `name`, `description`, and any `when_to_use` fields.
3. Identify bundled resources:
   ```
   ls <skill-dir>/
   # Expected: SKILL.md + optional scripts/, references/, assets/
   ```
4. Check for common structural issues:
   - Missing closing `---` after frontmatter
   - `description` field contains `>` or `<` characters (folded scalar bug)
   - Empty or generic description (< 20 chars)
   - Missing required frontmatter keys

### Stage 2: Generation

**Goal**: Generate test cases from the skill's own content.

1. **Trigger test cases**: Extract every "when to use" clause from SKILL.md. Convert each into a concrete prompt that should invoke the skill.
2. **Coverage test cases**: Identify every distinct capability mentioned. Write one test per capability.
3. **Edge cases**: Identify boundary conditions, error paths, and "do NOT do X" rules.

Example generation from a skill with `submit_alpha` workflow:

| Capability | Test Prompt |
|-----------|------------|
| IS PASS → submit | "Simulation IS just passed with Sharpe=1.8, should I submit?" |
| IS FAIL → diagnose | "Simulation got LOW_SHARPE FAIL, what do I do?" |
| Async wait | "I called submit_alpha and got success:true, how do I verify?" |

### Stage 3: Execution

**Goal**: Run each test case and collect outcomes.

For each test prompt:
1. Execute in a fresh sub-agent with the skill loaded.
2. Capture the full response.
3. Score pass/fail per test case:
   - **PASS**: Response correctly addressed the prompt using the skill's instructions
   - **FAIL**: Response missed, contradicted, or ignored the skill's guidance
   - **N/A**: Skill does not cover this scenario

### Stage 4: Evaluation

**Goal**: Aggregate scores into the 4D rubric.

## 4D Scoring Rubric

| Dimension | Weight | What It Measures | Score Range |
|-----------|--------|-----------------|-------------|
| **Documentation** | 25% | SKILL.md clarity, completeness, examples, structure | 0–10 |
| **Code/Scripts** | 25% | Bundled scripts correctness, error handling, determinism | 0–10 |
| **Completeness** | 25% | All declared capabilities covered, no critical gaps | 0–10 |
| **Usability** | 25% | Skill triggers correctly, instructions are actionable, edge cases handled | 0–10 |

### Dimension Scoring Guide

**Documentation (0–10):**
- 9–10: SKILL.md has clear sections, concrete examples, decision trees, and explicit WHEN-to-use
- 7–8: Well-structured with most key scenarios covered
- 5–6: Functional but missing examples or ambiguous trigger conditions
- <5: Generic template content, no real skill-specific guidance

**Code/Scripts (0–10):**
- 9–10: Scripts are executable, handle errors, have docstrings, and are deterministic
- 7–8: Functional scripts with minor issues
- 5–6: Scripts exist but have bugs or unclear purpose
- <5: No scripts or all scripts are broken

**Completeness (0–10):**
- 9–10: Every declared capability has corresponding instructions; no dead-end scenarios
- 7–8: >80% coverage; minor gaps in edge cases
- 5–6: 50–80% coverage; some declared features have no implementation
- <5: Less than half of declared capabilities are implemented

**Usability (0–10):**
- 9–10: Skill triggers reliably on the right prompts; instructions are unambiguous
- 7–8: Usually triggers correctly; some prompts need refinement
- 5–6: Trigger conditions are vague; user often needs to invoke manually
- <5: Skill rarely triggers on relevant prompts

### Final Score

```
final = (Documentation × 0.25) + (Code × 0.25) + (Completeness × 0.25) + (Usability × 0.25)
```

### Tier Classification

| Final Score | Tier | Action |
|-------------|------|--------|
| ≥ 8.5 | **POWERFUL** | Deploy immediately; set as benchmark |
| ≥ 7.0 | **STANDARD** | Good to deploy; address minor gaps |
| ≥ 5.0 | **BASIC** | Functional but needs improvement |
| < 5.0 | **REJECT** | Do not deploy; major rewrites needed |

## Structural Validation Checklist

Run before scoring:

```
[ ] YAML frontmatter closes correctly (--- after frontmatter)
[ ] description field is single-line, no > or < characters
[ ] name field is lowercase-with-hyphens
[ ] SKILL.md has at least one real section beyond "Overview"
[ ] All scripts are syntactically valid (python3 -m py_compile)
[ ] references/ files exist only if SKILL.md references them
[ ] assets/ files exist only if SKILL.md references them
[ ] No TODO placeholders remain in SKILL.md body
```

## Quick Validate Script

Use the skill-creator's built-in validator:

```bash
python3 ~/.claude/skills/skill-creator/scripts/quick_validate.py <skill-dir>/SKILL.md
```

Common validation failures:
- `Description cannot contain angle brackets` → Convert folded scalar (`description: >`) to single-line `description: text here`
- `Missing closing ---` → Add `---` after YAML frontmatter
- `name must be lowercase` → Rename `My-Skill` → `my-skill`

## Package Before Deployment

After passing validation and scoring:

```bash
python3 ~/.claude/skills/skill-creator/scripts/package_skill.py <skill-dir>
```

Packaging validates automatically. Fix all validation errors before zipping.

## Relationship to Other Skills

- **skill-creator**: skill-tester validates output from skill-creator. Always run after upgrading.
- **brain-compound**: Produces new skills; skill-tester validates them before use.
- **cc-plugin-eval** (GitHub: sjnims/cc-plugin-eval): The conceptual foundation — 4-stage pipeline + LLM judgment.
- **skill-tester** (GitHub: alirezarezvani/claude-skills): The scoring framework — 4D rubric + tier system.

## Bundle Resources

### scripts/

The main test execution script goes here:

- `run_tests.py` — 4-stage pipeline orchestrator. Accepts skill path and outputs JSON report.

### references/

- `scoring_guide.md` — Full rubric with examples of each score level (0–10) per dimension.
- `trigger_keywords.md` — Common skill trigger phrases for generating test cases.

---
*Built on cc-plugin-eval (sjnims) + skill-tester (alirezarezvani) frameworks*
