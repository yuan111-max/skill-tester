# skill-tester

**4-Stage pipeline + 4D scoring for Claude Code skill evaluation.**

Analyzes any Claude Code skill for structural validity, content quality,
bundle completeness, and trigger accuracy.  Replaces guesswork with
actionable metrics before you deploy a skill to production.

```text
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Stage 1    │ →  │  Stage 2    │ →  │  Stage 3    │ →  │  Stage 4    │
│  Analysis   │    │  Generation │    │  Execution  │    │  Evaluation │
│  ─────────  │    │  ─────────  │    │  ─────────  │    │  ─────────  │
│  SKILL.md   │    │  Trigger    │    │  Claude CLI │    │  4D Scoring  │
│  Bundle     │    │  Capability │    │  PASS/FAIL  │    │  Tier Class  │
│  Anti-      │    │  Edge cases │    │  Timing     │    │  Report      │
│  patterns   │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## Features

- **🔍 Deep structural analysis** — YAML frontmatter validation, recursive bundle scanning, content quality metrics
- **📋 Automatic test generation** — Extract trigger conditions, capabilities, and edge cases from SKILL.md
- **⚡ Real execution** — Run tests via `claude` CLI (with `--execute`) to measure actual skill activation
- **📊 4D Scoring** — Configurable weights, sub-scores, and tier thresholds
- **🔎 Anti-pattern detection** — Catches TODOs, template artifacts, placeholder content, vague language
- **📐 Cross-skill comparison** — Compare multiple skills side-by-side with `--output table`
- **⚙️ Fully configurable** — All thresholds, weights, and patterns live in a single YAML config file

---

## Quick Start

```bash
# 1. Install
git clone https://github.com/topprismdata/skill-tester.git
cd skill-tester
pip install -r requirements.txt

# 2. Run basic analysis (no execution)
python scripts/run_tests.py path/to/my-skill

# 3. Full pipeline with live tests
python scripts/run_tests.py path/to/my-skill --execute

# 4. Compare two skills
python scripts/run_tests.py path/to/skill-a path/to/skill-b --output table

# 5. JSON output for CI / automation
python scripts/run_tests.py path/to/my-skill --output json
```

---

## Usage

```text
python scripts/run_tests.py <skill-dirs...> [options]

Positional:
  skill-dirs              Path(s) to skill directories (one or more)

Options:
  --output / -o           Output format: summary (default), json, table
  --execute / -e          Enable real test execution via Claude CLI
  --config / -c           Path to custom YAML configuration
  --quiet / -q            Suppress stage progress output
  --no-color              Disable ANSI colour in output
```

---

## Scoring Overview

| Dimension     | Weight | What It Measures                               |
|---------------|--------|------------------------------------------------|
| Documentation | 25%    | SKILL.md clarity, structure, examples, triggers |
| Code          | 25%    | Bundled script correctness, error handling      |
| Completeness  | 25%    | Coverage of all declared capabilities           |
| Usability     | 25%    | Trigger reliability, instruction actionability  |

Each dimension is computed from **sub-scores** (e.g. frontmatter_validity,
section_coverage, example_density) defined in `config/default.yaml`.

**Final score** (0–10) → **Tier**:

| Score  | Tier       | Action                                   |
|--------|------------|------------------------------------------|
| ≥ 8.5  | POWERFUL   | Deploy immediately; set as benchmark      |
| ≥ 7.0  | STANDARD   | Good to deploy; address minor gaps        |
| ≥ 5.0  | BASIC      | Functional; needs improvement             |
| < 5.0  | REJECT     | Major rewrites required                   |

---

## Stage Details

### Stage 1: Analysis
- Parses YAML frontmatter (`name`, `description`, validation checks)
- Recursive scan of `scripts/`, `references/`, `assets/` directories
- Content quality metrics: section count, example density, line count
- Anti-pattern scanning: TODOs, template artifacts, placeholder language, vague references
- Python script syntax validation via `py_compile`

### Stage 2: Test Generation
- **Trigger tests**: Extract every "When to Use" clause as a test prompt
- **Non-trigger tests**: Generate prompts that should *not* activate the skill
- **Edge cases**: Extract "Do Not", "Limitations", "Caveats" sections as test prompts
- **Capabilities**: Section headings and action-oriented bullet points

### Stage 3: Execution
- Runs each test prompt through `claude --non-interactive --print`
- Detects skill activation in the response using heuristics
- Scores each test PASS/FAIL based on expected trigger behavior
- Falls back gracefully with a clear message when CLI is unavailable

### Stage 4: Evaluation
- Configurable dimension weights (default 25% each)
- Sub-score aggregation per dimension
- Final score → tier mapping
- Per-dimension detail for debugging

---

## Project Structure

```
skill-tester/
├── config/
│   └── default.yaml            # All thresholds, weights, and rules
├── scripts/
│   ├── __init__.py
│   ├── run_tests.py             # CLI entry point
│   ├── config.py                # Config loader
│   ├── analyze.py               # Stage 1
│   ├── generate.py              # Stage 2
│   ├── execute.py               # Stage 3
│   ├── evaluate.py              # Stage 4
│   └── formatters.py            # Output: json, table, summary
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_analyze.py
│   ├── test_generate.py
│   ├── test_execute.py
│   ├── test_evaluate.py
│   ├── test_config.py
│   ├── test_formatters.py
│   ├── test_run_tests.py
│   ├── test_integration.py
│   └── fixtures/
│       ├── good_skill/
│       ├── bad_skill/
│       └── full_skill/          # .py, .sh, .js + refs + assets
├── references/
│   ├── scoring_guide.md
│   └── trigger_keywords.md
├── .github/workflows/test.yml   # CI (flake8 + mypy + pytest + self-test)
├── .flake8                      # Linter config
├── mypy.ini                     # Type checker config
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Configuration

All configuration lives in [`config/default.yaml`](config/default.yaml).
Override any setting by:

1. Creating `config/local.yaml` (auto-loaded, git-ignored)
2. Passing `--config path/to/custom.yaml`

### What you can configure

- **Scoring**: dimension weights, sub-score definitions, tier thresholds
- **Analysis**: minimum description length, required sections, script extensions
- **Execution**: Claude CLI command, timeout, max tests, temperature
- **Anti-patterns**: patterns, severity levels, messages
- **Output**: format, colour, preview length

---

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt pytest pytest-cov

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=scripts --cov-report=term-missing

# Self-test (validate skill-tester against itself)
python scripts/run_tests.py .
```

---

## References

- Based on [cc-plugin-eval](https://github.com/sjnims/cc-plugin-eval) (4-stage pipeline)
- Inspired by [claude-skills skill-tester](https://github.com/alirezarezvani/claude-skills) (4D rubric)
- Evaluation methodology from [Anthropic skill-creator](https://github.com/anthropics/skills) (Eval/Benchmark modes)
- Additional patterns from SkillCompass, PluginEval, Caliper, and other community tools

---

## License

MIT
