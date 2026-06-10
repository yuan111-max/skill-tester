<div align="center">

[![🇨🇳 简体中文](https://img.shields.io/badge/🇨🇳-简体中文-red?style=for-the-badge&labelColor=red&color=white)](#中文)
[![🇬🇧 English](https://img.shields.io/badge/🇬🇧-English-blue?style=for-the-badge&labelColor=blue&color=white)](#english)

<br>

# 🧪 Skill-Tester

**4-Stage Pipeline · 4-Dimension Scoring · Quantified Skill Quality**

[![CI](https://img.shields.io/github/actions/workflow/status/topprismdata/skill-tester/.github/workflows/test.yml?branch=main&label=CI&logo=github)](https://github.com/topprismdata/skill-tester/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Code Style](https://img.shields.io/badge/code%20style-flake8-brightgreen)](https://github.com/PyCQA/flake8)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?logo=github)](https://github.com/topprismdata/skill-tester/pulls)

</div>

---

<a id="中文"></a>

<div align="center">

# 🇨🇳 中文

**停止猜测 — 开始度量。**

用严格的全自动评估取代主观技能审查。从 4 个维度量化技能质量，自信地将技能部署到生产中。

</div>

---

## ✨ 一目了然

```text
╭──────────────────────────────────────────────────────────╮
│                                                          │
│   📂 my-skill/                                           │
│   ├── SKILL.md                                           │
│   ├── scripts/                                           │
│   └── references/                                        │
│                                                          │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   │
│   │  阶段 1     │ → │  阶段 2     │ → │  阶段 3     │   │
│   │  ─────────  │   │  ─────────  │   │  ─────────  │   │
│   │  结构分析   │   │  20+ 测试   │   │  真实执行   │   │
│   │  元数据     │   │  边界情况   │   │  Claude CLI │   │
│   │  反模式     │   │  能力提取   │   │  PASS/FAIL  │   │
│   └──────┬───────┘   └──────┬──────┘   └──────┬──────┘   │
│          │                  │                  │          │
│          └──────────────────┴──────────────────┘          │
│                                                           │
│                                       ┌──────────────┐   │
│                                   ↓   │  阶段 4      │   │
│                                       │  ─────────   │   │
│                                       │  4 维评分    │   │
│                                       │  等级报告    │   │
│                                       └──────────────┘   │
│                                                           │
│   ════════════════════════════════════════════════════    │
│   结果:  POWERFUL  ████████░░  8.7 / 10                  │
│   ════════════════════════════════════════════════════    │
│                                                          │
╰──────────────────────────────────────────────────────────╯
```

---

## 🚀 快速开始

```bash
# 1. 安装
git clone https://github.com/topprismdata/skill-tester.git
cd skill-tester
pip install -r requirements.txt

# 2. 分析技能（无需 Claude CLI）
python scripts/run_tests.py path/to/my-skill

# 3. 完整流水线（含实时代理测试）
python scripts/run_tests.py path/to/my-skill --execute

# 4. 并排对比多个技能
python scripts/run_tests.py path/to/skill-a path/to/skill-b --output table

# 5. JSON 输出（适用于 CI / 自动化）
python scripts/run_tests.py path/to/my-skill --output json
```

---

## 📊 4 维评分体系

所有技能通过 **4 个等权维度**（各 25%）评估，得出 **0–10 最终分**，并附带可操作的等级分类。

```text
                    文档 (Documentation)
                    ◄──────────►
                 ▲                ▲
                 │                │
   代码 (Code)   │     ★          │  完整性 (Completeness)
   ◄─────────────┤   8.7/10      ├─────────────►
                 │   POWERFUL    │
                 ▼                ▼
                 ◄──────────►
                 可用性 (Usability)
```

| 维度 | 权重 | 衡量内容 |
|------|:----:|----------|
| 📝 **文档** | 25% | SKILL.md 的清晰度、结构、示例、触发条件 |
| 💻 **代码** | 25% | 配套脚本的正确性、错误处理、文档字符串 |
| 📋 **完整性** | 25% | 所有声明能力的覆盖情况 |
| 🎯 **可用性** | 25% | 触发可靠性、指令可操作性 |

### 🏆 评级阈值

| 分数 | 等级 | 建议行动 |
|:----:|:----:|----------|
| **≥ 8.5** | 🔥 **POWERFUL** | 可立即部署，设为标杆 |
| **≥ 7.0** | ✅ **STANDARD** | 可以部署，建议修补次要不足 |
| **≥ 5.0** | ⚠️ **BASIC** | 可用但需要改进 |
| **< 5.0** | ❌ **REJECT** | 需要重大重写 |

### 🧩 子分数详情

每个维度拆分为加权子分数（可在 [`config/default.yaml`](config/default.yaml) 中配置）：

#### 📝 文档 (Documentation)
```
frontmatter_validity    15%   10 - 3 × 前置元数据问题数
section_coverage        25%   ≥6 节→10, ≥4→8, ...
example_density         20%   ≥6 示例→10, 含 TODO→-3
specificity_clarity     25%   10 - 2 × 反模式数
trigger_clarity         15%   ≥5 触发短语→10, ≥3→8, ...
```

#### 💻 代码 (Code)
```
script_presence         10%   ≥3 脚本→10, 无脚本→2
syntactic_validity      35%   (有效数/总数)×10  |  无脚本基准:5
error_handling          30%   2+(I/O 已覆盖/I/O 总数)×8  |  纯逻辑→8
script_documentation    25%   (有文档脚本/总数)×10  |  无脚本基准:5
```

> **🔑 关键洞察：** 错误处理只计 **I/O 脚本**（执行文件/网络/Shell 操作的脚本）——纯逻辑脚本不 penalize 技能。无脚本技能在三个子分数上获得中性基准分 5。

#### 📋 完整性 (Completeness)
```
capability_coverage     40%   ≥8 个能力→10, ≥5→8, ...
edge_case_coverage      30%   min(10, 边界情况×2 + 非触发测试数)
section_completeness    30%   (1 - 缺失必需节数/总必需节数)×10
```

#### 🎯 可用性 (Usability)
```
trigger_accuracy        30%   (通过/总数)×10  |  代理:min(10, 短语数×2)
instruction_actionability 30%  ≥15 子弹点→10, ≥10→8, ...
edge_case_handling      20%   有 caution 章节→8, 否则→4
progressive_disclosure  20%   有 H1+≥4 H2+≥2 H3→10, ...
```

---

## 🧪 使用方法

```text
python scripts/run_tests.py <技能目录...> [选项]

位置参数：
  skill-dirs               技能目录路径（一个或多个）

选项：
  -o, --output FORMAT      输出格式：summary（默认）、json、table
  -e, --execute            通过 Claude CLI 启用真实测试执行
  -c, --config PATH        自定义 YAML 配置文件路径
  -q, --quiet              隐藏阶段进度输出
      --no-color           禁用输出中的 ANSI 颜色
  -V, --version            显示版本号并退出
```

### 示例

```bash
# 最简模式 — 仅结构分析
python scripts/run_tests.py ./skills/json-validator

# 完整模式 — 分析→生成→执行→评分
python scripts/run_tests.py ./skills/json-validator --execute

# 对比模式 — 并排表格，不执行
python scripts/run_tests.py skills/* --output table

# CI 流水线 — JSON 输出、静默模式
python scripts/run_tests.py ./skills/json-validator --output json --quiet
```

---

## 🏗️ 项目结构

```
skill-tester/
├── 📁 config/
│   └── 📄 default.yaml            ← 所有阈值、权重和规则
├── 📁 scripts/
│   ├── run_tests.py               ← CLI 入口
│   ├── config.py                  ← 配置加载器
│   ├── utils.py                   ← 共享工具函数
│   ├── analyze.py                 ← 阶段 1：深度分析
│   ├── generate.py                ← 阶段 2：测试生成
│   ├── execute.py                 ← 阶段 3：真实执行
│   ├── evaluate.py                ← 阶段 4：4 维评分
│   └── formatters.py              ← 输出：json / table / summary
├── 📁 tests/
│   ├── conftest.py                ← 共享测试夹具
│   ├── test_analyze.py
│   ├── test_generate.py
│   ├── test_execute.py
│   ├── test_evaluate.py
│   ├── test_config.py
│   ├── test_formatters.py
│   ├── test_run_tests.py
│   ├── test_integration.py
│   └── 📁 fixtures/
│       ├── good_skill/            ← 正确技能参考
│       ├── bad_skill/             ← 缺陷技能参考
│       └── full_skill/            ← 端到端：.py、.sh、.js + 参考 + 资产
├── 📁 references/
│   ├── scoring_guide.md           ← 详细评分指南
│   └── trigger_keywords.md        ← 触发模式参考
├── 📁 .github/workflows/
│   └── test.yml                   ← CI：flake8 + mypy + pytest + 自测
├── 📄 .flake8
├── 📄 mypy.ini
├── 📄 requirements.txt
├── 📄 pyproject.toml
└── 📄 README.md
```

---

## ⚙️ 配置

所有阈值集中在 [`config/default.yaml`](config/default.yaml)。无需修改代码即可覆盖任意配置：

| 方式 | 文件 | 持久性 |
|------|------|:------:|
| 本地覆盖 | `config/local.yaml` | ✅ 已 git-ignore |
| 自定义路径 | `--config path/to/custom.yaml` | ✅ 任意位置 |

### 可配置项

| 类别 | 示例 |
|------|------|
| **评分** | 维度权重、子分数定义、等级阈值 |
| **分析** | 最小描述长度、必需章节、脚本扩展名 |
| **执行** | Claude CLI 命令、超时时间、最大测试数、温度参数 |
| **反模式** | 正则模式、严重级别、自定义消息 |
| **输出** | 格式、颜色、预览长度 |

---

## 🔬 CI 集成

项目内置**即开即用的 CI 工作流**（`.github/workflows/test.yml`），每次推送自动运行：

```yaml
# CI 检查内容：
✅ flake8      — 代码风格与代码检查
✅ mypy        — 静态类型检查
✅ pytest      — 完整测试套件（220+ 测试）
✅ 自测        — 用 skill-tester 测试自身 → POWERFUL ✓
```

在你的 CI 中添加：
```bash
python scripts/run_tests.py ./my-skill --output json --quiet
```

---

## 🧑‍💻 开发

```bash
# 安装开发依赖
pip install -r requirements.txt pytest pytest-cov

# 运行测试套件
pytest tests/ -v

# 带覆盖率
pytest tests/ --cov=scripts --cov-report=term-missing

# 自测（元测试！— 用 skill-tester 测试自身）
python scripts/run_tests.py .
```

> **当前自测结果：** 🔥 **POWERFUL** — 该项目在其自身评分标准上得分 ≥8.5/10。

---

## 🙏 致谢

本项目借鉴了 Claude Code 技能生态中的多种优秀思想：

| 项目 | 影响 |
|------|------|
| [cc-plugin-eval](https://github.com/sjnims/cc-plugin-eval) | 4 阶段流水线架构 |
| [claude-skills skill-tester](https://github.com/alirezarezvani/claude-skills) | 4 维评分体系 |
| [Anthropic skill-creator](https://github.com/anthropics/skills) | 评估与基准模式 |
| SkillCompass / PluginEval / Caliper | 社区设计洞察 |

---

<div align="center">

**🧪 为 Claude Code 技能社区打造**

`MIT License` · 欢迎贡献 — 提交 [Issue](https://github.com/topprismdata/skill-tester/issues) 或 [PR](https://github.com/topprismdata/skill-tester/pulls)

</div>

<br>

---

<a id="english"></a>

<div align="center">

# 🇬🇧 English

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
│   │  Analyze    │ → │  Generate   │ → │  Execute    │   │
│   │  ─────────  │   │  ─────────  │   │  ─────────  │   │
│   │  structure  │   │  20+ tests  │   │  real       │   │
│   │  metadata   │   │  edge cases │   │  Claude CLI │   │
│   │  anti-      │   │  capabilities│  │  PASS/FAIL  │   │
│   │  patterns   │   │            │   │             │   │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   │
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
