---
name: skill-tester
description: Tests and evaluates any Claude Code skill for structural validity, content quality, bundle completeness, and trigger accuracy. Implements a 4-stage pipeline (Analysis → Generation → Execution → Evaluation) with configurable 4D scoring and tier classification.
---

# Skill Tester

Validate, test, and score Claude Code skills using a rigorous 4-stage evaluation pipeline with configurable scoring dimensions and anti-pattern detection.

## When to Use

- Before packaging a newly created or upgraded skill for deployment
- After modifying any skill's SKILL.md, scripts, or bundle resources
- During skill development to catch structural issues and anti-patterns early
- To compare the quality of two or more competing skill implementations
- As part of a CI pipeline to gate skill deployment on quality thresholds
- Triggered by `/skill-tester <skill-dir>` when debugging or auditing a skill

## Stage 1: Analysis

**Goal**: Deep structural and content analysis of the skill.

1. Parse YAML frontmatter — validate `name`, `description`, angle brackets, length
2. Recursively scan bundle directories — `scripts/`, `references/`, `assets/`
3. Analyze content structure — section count, example density, line count, required sections
4. Detect anti-patterns — `TODO`/`FIXME`/`XXX` placeholders, template artifacts, filler language, vague references
5. Validate scripts — Python syntax check via `py_compile`, shebang check for shell scripts, docstring presence

**Key checks:**
- `name` must be lowercase-hyphenated (e.g. `my-skill`)
- `description` must not contain `>` or `<` characters (folded-scalar bug)
- `description` must be ≥ 20 characters
- SKILL.md should have ≥ 2 sections and mention trigger conditions
- No `TODO`/`FIXME`/`XXX` markers should remain in the body

## Stage 2: Test Generation

**Goal**: Automatically generate test cases from the skill's own content.

1. **Trigger tests**: Extract every "When to Use" clause and trigger keyword match as a concrete prompt that *should* invoke the skill
2. **Non-trigger tests**: Generate prompts that should *not* invoke the skill (negative testing)
3. **Edge cases**: Extract "Do Not", "Avoid", "Limitations", "Warnings" sections as test prompts
4. **Capabilities**: Extract section headings and action-oriented bullet points as declared capabilities

Tests are deduplicated and capped to `max_tests` (default 10), prioritised as: trigger > non-trigger > edge case.

## Stage 3: Execution

**Goal**: Run each test prompt through the `claude` CLI and score responses.

For each test prompt:
1. Execute in a subprocess via `claude --non-interactive --print <prompt>`
2. Capture the full response and measure elapsed time
3. Detect skill activation via heuristics (skill name mention, activation phrases, structured output indicators)
4. Score PASS if activation status matches expected; FAIL otherwise

Requires `--execute` flag or `execution.enabled: true` in config.
Falls back gracefully with a SKIPPED report when the CLI is unavailable.

## Stage 4: Evaluation

**Goal**: Aggregate all analysis, test, and execution data into 4D scores and a deployment tier.

**4D Scoring Dimensions:**

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Documentation | 25% | SKILL.md clarity, structure, examples, trigger clarity |
| Code | 25% | Script correctness, error handling, documentation |
| Completeness | 25% | Capability coverage, edge case coverage, section completeness |
| Usability | 25% | Trigger accuracy, instruction actionability, edge case handling |

Each dimension is computed from weighted sub-scores defined in `config/default.yaml`. The final score (0–10) maps to a tier:

| Score | Tier | Action |
|-------|------|--------|
| ≥ 8.5 | POWERFUL | Deploy immediately; set as benchmark |
| ≥ 7.0 | STANDARD | Good to deploy; address minor gaps |
| ≥ 5.0 | BASIC | Functional; needs improvement |
| < 5.0 | REJECT | Major rewrites required |

## Configuration

All thresholds, weights, and rules live in `config/default.yaml`. Customize via:
1. `config/local.yaml` (auto-loaded, git-ignored)
2. `--config path/to/custom.yaml` CLI flag

Configurable items: dimension weights, sub-score definitions, tier thresholds,
anti-pattern patterns, script extensions, execution settings, output formatting.

## Examples

### Basic structural analysis:
```bash
python scripts/run_tests.py ../my-skill
```

### Full pipeline with live tests:
```bash
python scripts/run_tests.py ../my-skill --execute
```

### Compare two skills:
```bash
python scripts/run_tests.py ../skill-a ../skill-b --output table
```

### JSON output for CI:
```bash
python scripts/run_tests.py ../my-skill --output json
```

### Custom config:
```bash
python scripts/run_tests.py ../my-skill --config ./strict.yaml
```

## Limitations

- Stage 3 execution requires the `claude` CLI to be installed in PATH
- Python syntax validation only works for `.py` files (not shell/JS/TS)
- Non-trigger test prompts are generated heuristically and may not match real-world usage
- Scoring is structural-quality focused and does not measure skill effectiveness on real tasks
- Anti-pattern detection uses regex patterns and may produce false positives

## Do Not

- Do not run `--execute` without reviewing the test prompts first (each execution costs API tokens)
- Do not rely solely on the final score — review individual dimension details and issues
- Avoid modifying `config/default.yaml` directly — use `config/local.yaml` or `--config` instead

## Bundle Resources

### scripts/
- `run_tests.py` — CLI entry point and pipeline orchestrator
- `config.py` — Configuration loader (default.yaml → local.yaml → CLI overrides)
- `analyze.py` — Stage 1: structural and content analysis
- `generate.py` — Stage 2: automatic test case generation
- `execute.py` — Stage 3: subprocess-based test execution via Claude CLI
- `evaluate.py` — Stage 4: multi-dimensional scoring and tier classification
- `__init__.py` — Package marker

### references/
- `scoring_guide.md` — Full rubric per dimension with sub-score definitions
- `trigger_keywords.md` — Common skill trigger phrases for test generation

### config/
- `default.yaml` — All scoring weights, analysis thresholds, anti-pattern rules, and execution settings

## Relationship to Other Skills

- **skill-creator**: skill-tester validates and scores skills produced by skill-creator
- **cc-plugin-eval** (GitHub: sjnims/cc-plugin-eval): Conceptual foundation — 4-stage pipeline + LLM judgment
- **claude-skills** (GitHub: alirezarezvani/claude-skills): Scoring framework — 4D rubric + tier system

---

*Built on cc-plugin-eval (sjnims) + claude-skills (alirezarezvani) frameworks, with evaluation methodology from Anthropic skill-creator (Eval/Benchmark modes)*
