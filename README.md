<div align="center">

# 🧪 Skill-Tester

**Quantified Skill Quality · 4-Dimensional Scoring · Automated Pipeline**

[![简体中文](https://img.shields.io/badge/简体中文-555?style=flat-square)](README.zh-CN.md)
[![CI](https://img.shields.io/github/actions/workflow/status/topprismdata/skill-tester/.github/workflows/test.yml?branch=main&label=CI&logo=github&style=flat-square)](https://github.com/topprismdata/skill-tester/actions)
[![Self-Test: POWERFUL](https://img.shields.io/badge/Self--Test-POWERFUL-brightgreen?style=flat-square)]()
[![License MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

> *Replace subjective skill reviews with rigorous, automated evaluation across 4 dimensions.*

</div>

---

## ✨ Features

| | | |
|---|---|---|
| ⚡ **Zero-Config Analysis** | 📊 **4-Dimension Score** | 🔄 **Full Pipeline** |
| Run without Claude CLI — structural analysis in seconds, no setup | Weighted: Documentation, Code, Completeness, Usability | Analyze → Generate → Execute → Evaluate, one command |
| 🎯 **Actionable Tiers** | ⚙️ **Fully Customizable** | 📈 **CI/CD Ready** |
| POWERFUL / STANDARD / BASIC / REJECT — clear next steps | All thresholds, weights & rules in a single YAML file | JSON output, quiet mode, works in any CI pipeline |

---

## 🔄 Pipeline Overview

| Stage | What It Does | Key Output |
|-------|-------------|------------|
| **1. Analyze** | Parse YAML frontmatter, check required sections, detect anti-patterns, extract trigger info | Structured skill analysis |
| **2. Generate** | Build trigger tests, non-trigger tests, edge cases; map capabilities from section headings | 20+ test prompts |
| **3. Execute** | Run generated tests through Claude CLI (requires `--execute`) | PASS / FAIL per test |
| **4. Evaluate** | Score across 4 equally-weighted dimensions, produce tier with actionable guidance | Score + tier report |

```text
╭──────────────────────────────────────────────────────────╮
│                       Pipeline Flow                      │
├────────────┬────────────┬────────────┬───────────────────┤
│   Analyze  │  Generate  │  Execute   │    Evaluate       │
│  ────────  │ ─────────  │ ─────────  │  ─────────────    │
│ front-     │ 20+ tests  │ Claude CLI │  Documentation    │
│ matter     │ trigger &  │ real       │  (25%)            │
│ sections   │ non-       │ execution  │  Code (25%)       │
│ anti-      │ trigger    │ per test   │  Completeness     │
│ patterns   │ edge cases │ PASS/FAIL  │  (25%)            │
│ triggers   │ capabili-  │ result     │  Usability (25%)  │
│            │ ties       │            │                   │
├────────────┴────────────┴────────────┴───────────────────┤
│                    ★  8.7 / 10  POWERFUL                  │
╰──────────────────────────────────────────────────────────╯
```

---

## 🚀 Quick Start

```bash
# Install
git clone https://github.com/topprismdata/skill-tester.git
cd skill-tester
pip install -r requirements.txt

# Analyze a skill (no Claude CLI needed)
python scripts/run_tests.py path/to/my-skill

# Full pipeline with live execution
python scripts/run_tests.py path/to/my-skill --execute

# Compare multiple skills side-by-side
python scripts/run_tests.py path/to/skill-a path/to/skill-b --output table
```

---

## 📊 The 4D Scoring System

Every skill is evaluated across **4 equally-weighted dimensions** (25% each), producing a **0–10 final score** with actionable tier guidance.

```text
╭────────────────────┬────────────────────╮
│ 📝 Documentation   │ 💻 Code            │
│ Weight: 25%        │ Weight: 25%        │
│ Clarity, structure,│ Correctness, error │
│ examples, triggers │ handling, docs     │
├────────────────────┼────────────────────┤
│ 📋 Completeness    │ 🎯 Usability       │
│ Weight: 25%        │ Weight: 25%        │
│ Capability coverage│ Trigger accuracy,  │
│ edge case coverage │ instruction action │
├────────────────────┴────────────────────┤
│           ★  8.7 / 10  POWERFUL          │
╰─────────────────────────────────────────╯
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
| **< 5.0** | ❌ **REJECT** | Requires major rewrite |

### 🧩 Sub-Score Breakdown

Each dimension breaks down into weighted sub-scores (configurable in [`config/default.yaml`](config/default.yaml)):

**📝 Documentation**

| Sub-Score | Weight | Calculation |
|-----------|:------:|-------------|
| `frontmatter_validity` | 15% | 10 − 3 × issues |
| `section_coverage` | 25% | ≥6 sections → 10, ≥4 → 8, … |
| `example_density` | 20% | ≥6 examples → 10, has TODO → −3 |
| `specificity_clarity` | 25% | 10 − 2 × anti-patterns |
| `trigger_clarity` | 15% | ≥5 phrases → 10, ≥3 → 8, … |

**💻 Code**

| Sub-Score | Weight | Calculation |
|-----------|:------:|-------------|
| `script_presence` | 10% | ≥3 scripts → 10, none → 2 |
| `syntactic_validity` | 35% | (valid / total) × 10; baseline 5 if no scripts |
| `error_handling` | 30% | 2 + (I/O covered / I/O total) × 8; 8 if pure-logic |
| `script_documentation` | 25% | (documented / total) × 10; baseline 5 if no scripts |

> **Key insight:** Error handling only counts **I/O scripts** (file/network/shell operations) — pure-logic scripts don't penalize. No-script skills get a neutral baseline of 5 on three sub-scores.

**📋 Completeness**

| Sub-Score | Weight | Calculation |
|-----------|:------:|-------------|
| `capability_coverage` | 40% | ≥8 capabilities → 10, ≥5 → 8, … |
| `edge_case_coverage` | 30% | min(10, edge_cases × 2 + non_triggers) |
| `section_completeness` | 30% | (1 − missing / required) × 10 |

**🎯 Usability**

| Sub-Score | Weight | Calculation |
|-----------|:------:|-------------|
| `trigger_accuracy` | 30% | (passed / total) × 10; proxy: min(10, phrases × 2) |
| `instruction_actionability` | 30% | ≥15 bullets → 10, ≥10 → 8, … |
| `edge_case_handling` | 20% | 8 if caution sections exist, else 4 |
| `progressive_disclosure` | 20% | H1 + ≥4 H2 + ≥2 H3 → 10, … |

---

## 🧪 CLI Usage

```text
python scripts/run_tests.py <skill-dirs...> [options]
```

| Option | Description |
|--------|-------------|
| `skill-dirs` | One or more skill directory paths (positional) |
| `-o, --output FORMAT` | Output: `summary` (default), `json`, `table` |
| `-e, --execute` | Enable live execution via Claude CLI |
| `-c, --config PATH` | Custom YAML config file path |
| `-q, --quiet` | Suppress stage progress output |
| `--no-color` | Disable ANSI colors in output |
| `-V, --version` | Show version and exit |

### Examples

```bash
# Quick structural analysis
python scripts/run_tests.py ./my-skill

# Full pipeline — analyze, generate, execute, score
python scripts/run_tests.py ./my-skill --execute

# CI-friendly JSON (silent)
python scripts/run_tests.py ./my-skill --output json --quiet

# Side-by-side comparison of multiple skills
python scripts/run_tests.py skills/* --output table
```

---

## 📁 Project Structure

```
skill-tester/
├── 📁 config/
│   └── default.yaml              ← All thresholds, weights & rules
├── 📁 scripts/
│   ├── run_tests.py               ← CLI entry point
│   ├── config.py                  ← Config loader
│   ├── utils.py                   ← Shared utilities
│   ├── analyze.py                 ← Stage 1: deep analysis
│   ├── generate.py                ← Stage 2: test generation
│   ├── execute.py                 ← Stage 3: real execution
│   ├── evaluate.py                ← Stage 4: 4D scoring
│   └── formatters.py              ← Output: JSON / table / summary
├── 📁 tests/
│   ├── conftest.py                ← Shared fixtures
│   ├── test_analyze.py, test_generate.py, test_execute.py,
│   │   test_evaluate.py, test_config.py, test_formatters.py,
│   │   test_run_tests.py, test_integration.py
│   └── 📁 fixtures/
│       ├── good_skill/            ← Well-formed skill reference
│       ├── bad_skill/             ← Poorly-formed skill reference
│       └── full_skill/            ← E2E: .py, .sh, .js + refs + assets
├── 📁 references/
│   ├── scoring_guide.md           ← Detailed rubric
│   └── trigger_keywords.md        ← Trigger pattern reference
├── 📁 .github/workflows/
│   └── test.yml                   ← CI: flake8 + mypy + pytest + self-test
├── 📄 .flake8, mypy.ini, requirements.txt, pyproject.toml
└── 📄 README.md / README.zh-CN.md
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

Built-in CI workflow (`.github/workflows/test.yml`) runs on every push:

```yaml
✅ flake8      — Code style & linting
✅ mypy        — Static type checking
✅ pytest      — Full test suite (220+ tests)
✅ Self-test   — Tests skill-tester against itself → POWERFUL ✓
```

Add to **your** pipeline:
```bash
python scripts/run_tests.py ./my-skill --output json --quiet
```

---

## 📚 Learn More

| Resource | Description |
|----------|-------------|
| [Scoring Guide](references/scoring_guide.md) | Detailed rubric with worked examples |
| [Trigger Keywords](references/trigger_keywords.md) | Trigger pattern reference |
| [Default Config](config/default.yaml) | All settings in one place |
| [CI Workflow](.github/workflows/test.yml) | Pipeline configuration |

---

## 🙏 Acknowledgements

| Project | Influence |
|---------|-----------|
| [cc-plugin-eval](https://github.com/sjnims/cc-plugin-eval) | 4-stage pipeline architecture |
| [claude-skills skill-tester](https://github.com/alirezarezvani/claude-skills) | 4D scoring system |
| [Anthropic skill-creator](https://github.com/anthropics/skills) | Evaluation & benchmarking patterns |

---

<div align="center">

**Made with 🧪 for the Claude Code skills community**

`MIT License` · Contributions welcome —
[open an issue](https://github.com/topprismdata/skill-tester/issues) or
[submit a PR](https://github.com/topprismdata/skill-tester/pulls)

</div>
