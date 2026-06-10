<div align="center">

# 🧪 Skill-Tester

**4-Stage Pipeline · 4-Dimension Scoring · Quantified Skill Quality**

[![CI](https://img.shields.io/github/actions/workflow/status/topprismdata/skill-tester/.github/workflows/test.yml?branch=main&label=CI&logo=github)](https://github.com/topprismdata/skill-tester/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Code Style](https://img.shields.io/badge/code%20style-flake8-brightgreen)](https://github.com/PyCQA/flake8)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?logo=github)](https://github.com/topprismdata/skill-tester/pulls)

**Stop guessing — start measuring.**

Replace subjective skill reviews with rigorous, automated evaluation across 4 dimensions. Ship skills to production with confidence.

</div>

---

## ✨ At a Glance

```text
╭──────────────────────────────────────────────────────────╮
│                                                          │
│   📂 my-skill/                                           │
│   ├── SKILL.md                                           │
│   ├── scripts/                                           │
│   └── references/                                        │
│                                                          │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   │
│   │  Analyze     │ → │  Generate   │ → │  Execute    │   │
│   │  ─────────   │   │  ─────────  │   │  ─────────  │   │
│   │  structure   │   │  20+ tests  │   │  real       │   │
│   │  metadata    │   │  edge cases │   │  Claude CLI │   │
│   │  anti-       │   │  capabilities│  │  PASS/FAIL  │   │
│   │  patterns    │   │            │   │             │   │
│   └──────┬───────┘   └──────┬──────┘   └──────┬──────┘   │
│          │                  │                  │          │
│          └──────────────────┴──────────────────┘          │
│                                                           │
│                                       ┌──────────────┐   │
│                                   ↓   │  Evaluate    │   │
│                                       │  4D Score    │   │
│                                       │  Tier Report │   │
│                                       └──────────────┘   │
│                                                           │
│   ════════════════════════════════════════════════════    │
│   RESULT:  POWERFUL  ████████░░  8.7 / 10               │
│   ════════════════════════════════════════════════════    │
│                                                          │
╰──────────────────────────────────────────────────────────╯
```

---

## 🚀 Quick Start

```bash
# 1. Install
git clone https://github.com/topprismdata/skill-tester.git
cd skill-tester
pip install -r requirements.txt

# 2. Analyze a skill (no Claude CLI needed)
python scripts/run_tests.py path/to/my-skill

# 3. Full pipeline with live execution
python scripts/run_tests.py path/to/my-skill --execute

# 4. Compare multiple skills side-by-side
python scripts/run_tests.py path/to/skill-a path/to/skill-b --output table

# 5. JSON output (CI-friendly)
python scripts/run_tests.py path/to/my-skill --output json
```

---

## 📊 The 4D Scoring System

Every skill is evaluated across **4 equally-weighted dimensions** (25% each), producing a **0–10 final score** with actionable tier classifications.

```text
                  Documentation
                  ◄──────────►
               ▲                ▲
               │                │
         Code  │     ★          │  Completeness
         ◄─────┤   8.7/10      ├─────►
               │   POWERFUL    │
               ▼                ▼
               ◄──────────►
                  Usability
```

| Dimension | Weight | What It Measures |
|-----------|:------:|------------------|
| 📝 **Documentation** | 25% | SKILL.md clarity, structure, examples, trigger clarity |
| 💻 **Code** | 25% | Script correctness, error handling, docstrings |
| 📋 **Completeness** | 25% | Coverage of all declared capabilities |
| 🎯 **Usability** | 25% | Trigger reliability, instruction actionability |

### 🏆 Tier Thresholds

| Score | Tier | Action |
|:-----:|:----:|--------|
| **≥ 8.5** | 🔥 **POWERFUL** | Deploy immediately — benchmark quality |
| **≥ 7.0** | ✅ **STANDARD** | Good to deploy — minor gaps acceptable |
| **≥ 5.0** | ⚠️ **BASIC** | Functional — needs improvement |
| **< 5.0** | ❌ **REJECT** | Requires major rewrites |

### 🧩 Sub-Score Detail

Each dimension breaks down into weighted sub-scores (configurable in [`config/default.yaml`](config/default.yaml)):

#### 📝 Documentation
```
frontmatter_validity    15%   10 - 3 × issues
section_coverage        25%   ≥6 sections → 10, ≥4 → 8, ...
example_density         20%   ≥6 examples → 10, has TODO → -3
specificity_clarity     25%   10 - 2 × anti-patterns
trigger_clarity         15%   ≥5 phrases → 10, ≥3 → 8, ...
```

#### 💻 Code
```
script_presence         10%   ≥3 scripts → 10, none → 2
syntactic_validity      35%   (valid / total) × 10  |  baseline: 5 if no scripts
error_handling          30%   2 + (I/O covered / I/O total) × 8  |  8 if pure-logic
script_documentation    25%   (documented / total) × 10  |  baseline: 5 if no scripts
```

> **🔑 Key insight:** Error handling only counts **I/O scripts** (ones that do file/network/shell operations) — pure-logic scripts don't penalize the skill. No-script skills get a neutral baseline of 5 on three sub-scores.

#### 📋 Completeness
```
capability_coverage     40%   ≥8 capabilities → 10, ≥5 → 8, ...
edge_case_coverage      30%   min(10, edge_cases × 2 + non_triggers)
section_completeness    30%   (1 - missing / required) × 10
```

#### 🎯 Usability
```
trigger_accuracy        30%   (passed / total) × 10  |  proxy: min(10, phrases × 2)
instruction_actionability 30%  ≥15 bullets → 10, ≥10 → 8, ...
edge_case_handling      20%   8 if do-not/avoid/limitation sections, else 4
progressive_disclosure  20%   10 if H1 + ≥4 H2 + ≥2 H3, ...
```

---

## 🧪 Usage

```text
python scripts/run_tests.py <skill-dirs...> [options]

Positional Arguments:
  skill-dirs              One or more skill directory paths

Options:
  -o, --output FORMAT     Output: summary (default), json, table
  -e, --execute           Enable live execution via Claude CLI
  -c, --config PATH       Custom YAML config file
  -q, --quiet             Suppress stage progress output
      --no-color          Disable ANSI colors in output
  -V, --version           Show version and exit
```

### Examples

```bash
# Minimal — structure-only analysis
python scripts/run_tests.py ./skills/json-validator

# Full — analyze, generate tests, execute, score
python scripts/run_tests.py ./skills/json-validator --execute

# Compare — side-by-side table, no execution
python scripts/run_tests.py skills/* --output table

# CI pipeline — JSON output, quiet mode
python scripts/run_tests.py ./skills/json-validator --output json --quiet
```

---

## 🏗️ Project Structure

```
skill-tester/
├── 📁 config/
│   └── 📄 default.yaml            ← All thresholds, weights & rules
├── 📁 scripts/
│   ├── run_tests.py               ← CLI entry point
│   ├── config.py                  ← Config loader
│   ├── utils.py                   ← Shared utilities
│   ├── analyze.py                 ← Stage 1: Deep analysis
│   ├── generate.py                ← Stage 2: Test generation
│   ├── execute.py                 ← Stage 3: Real execution
│   ├── evaluate.py                ← Stage 4: 4D scoring
│   └── formatters.py              ← Output: json / table / summary
├── 📁 tests/
│   ├── conftest.py                ← Shared fixtures
│   ├── test_analyze.py
│   ├── test_generate.py
│   ├── test_execute.py
│   ├── test_evaluate.py
│   ├── test_config.py
│   ├── test_formatters.py
│   ├── test_run_tests.py
│   ├── test_integration.py
│   └── 📁 fixtures/
│       ├── good_skill/            ← Reference: well-formed skill
│       ├── bad_skill/             ← Reference: poorly-formed skill
│       └── full_skill/            ← E2E: .py, .sh, .js + refs + assets
├── 📁 references/
│   ├── scoring_guide.md           ← Detailed rubric
│   └── trigger_keywords.md        ← Trigger pattern reference
├── 📁 .github/workflows/
│   └── test.yml                   ← CI: flake8 + mypy + pytest + self-test
├── 📄 .flake8
├── 📄 mypy.ini
├── 📄 requirements.txt
├── 📄 pyproject.toml
└── 📄 README.md
```

---

## ⚙️ Configuration

All thresholds live in [`config/default.yaml`](config/default.yaml). Override any setting without touching code:

| Method | File | Persistence |
|--------|------|:-----------:|
| Local override | `config/local.yaml` | ✅ Git-ignored |
| Custom path | `--config path/to/custom.yaml` | ✅ Anywhere |

### What You Can Configure

| Category | Examples |
|----------|----------|
| **Scoring** | Dimension weights, sub-score definitions, tier thresholds |
| **Analysis** | Min description length, required sections, script extensions |
| **Execution** | Claude CLI command, timeout, max tests, temperature |
| **Anti-Patterns** | Regex patterns, severity levels, custom messages |
| **Output** | Format, color, preview length |

---

## 🔬 CI Integration

The project includes a **batteries-included CI workflow** (`.github/workflows/test.yml`) that runs on every push:

```yaml
# What CI checks:
✅ flake8      — Code style & linting
✅ mypy        — Static type checking
✅ pytest      — Full test suite (220+ tests)
✅ Self-test   — Tests skill-tester against itself → POWERFUL ✓
```

Add to **your** CI pipeline:
```bash
python scripts/run_tests.py ./my-skill --output json --quiet
```

---

## 🧑‍💻 Development

```bash
# Install dev dependencies
pip install -r requirements.txt pytest pytest-cov

# Run the test suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=scripts --cov-report=term-missing

# Self-test (meta! — tests skill-tester with itself)
python scripts/run_tests.py .
```

> **Current self-test result:** 🔥 **POWERFUL** — the project scores ≥8.5/10 on its own rubric.

---

## 🙏 Acknowledgements

This project builds on ideas from the Claude Code skills ecosystem:

| Project | Influence |
|---------|-----------|
| [cc-plugin-eval](https://github.com/sjnims/cc-plugin-eval) | 4-stage pipeline architecture |
| [claude-skills skill-tester](https://github.com/alirezarezvani/claude-skills) | 4-dimension scoring system |
| [Anthropic skill-creator](https://github.com/anthropics/skills) | Evaluation & benchmarking patterns |
| SkillCompass / PluginEval / Caliper | Community design insights |

---

<div align="center">

**Made with 🧪 for the Claude Code skills community**

`MIT License` · Contributions welcome — open an [issue](https://github.com/topprismdata/skill-tester/issues) or [PR](https://github.com/topprismdata/skill-tester/pulls)

</div>
