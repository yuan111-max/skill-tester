<div align="center">

# 🧪 Skill-Tester

**量化技能质量 · 4 维评分 · 全自动流水线**

[![English](https://img.shields.io/badge/English-555?style=flat-square)](README.md)
[![CI](https://img.shields.io/github/actions/workflow/status/topprismdata/skill-tester/.github/workflows/test.yml?branch=main&label=CI&logo=github&style=flat-square)](https://github.com/topprismdata/skill-tester/actions)
[![Self-Test: POWERFUL](https://img.shields.io/badge/Self--Test-POWERFUL-brightgreen?style=flat-square)]()
[![License MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

> *用严格的全自动评估取代主观技能审查，从 4 个维度量化技能质量。*

</div>

---

## ✨ 功能亮点

| | | |
|---|---|---|
| ⚡ **零配置分析** | 📊 **四维评分** | 🔄 **全自动流水线** |
| 无需 Claude CLI 即可运行 — 数秒完成结构分析 | 加权评分：文档、代码、完整性、可用性 | 分析 → 生成 → 执行 → 评分，一条命令 |
| 🎯 **清晰分级** | ⚙️ **完全可定制** | 📈 **支持 CI/CD** |
| POWERFUL / STANDARD / BASIC / REJECT — 明确的改进方向 | 所有阈值、权重和规则集中在单个 YAML 文件中 | JSON 输出、静默模式，适用于任何 CI 流水线 |

---

## 🔄 流水线概览

| 阶段 | 功能 | 产出 |
|------|------|------|
| **1. 分析** | 解析 YAML 前置元数据、检查必需章节、检测反模式、提取触发信息 | 结构化技能分析报告 |
| **2. 生成** | 构建触发测试、非触发测试、边界情况；从章节标题映射能力 | 20+ 测试提示 |
| **3. 执行** | 通过 Claude CLI 运行生成的测试（需 `--execute` 参数） | 每个测试 PASS / FAIL |
| **4. 评分** | 4 个等权维度评分，生成等级和可操作建议 | 分数 + 等级报告 |

```text
分析  ──→  生成  ──→  执行  ──→  评分
                                       ↓
                                ★ 8.7 / 10
                                POWERFUL
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
```

---

## 📊 4 维评分体系

所有技能通过 **4 个等权维度**（各 25%）评估，得出 **0–10 最终分**，并附带可操作的等级分类。

| 📝 **文档** (25%) | 💻 **代码** (25%) |
|:------------------|:------------------|
| 清晰度、结构、示例、触发条件 | 正确性、错误处理、文档字符串 |

| 📋 **完整性** (25%) | 🎯 **可用性** (25%) |
|:--------------------|:-------------------|
| 能力覆盖范围、边界情况覆盖 | 触发准确性、指令可操作性 |

> **★  8.7 / 10  →  🔥 POWERFUL**

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

**📝 文档**

| 子分数 | 权重 | 计算方式 |
|--------|:----:|----------|
| `frontmatter_validity` | 15% | 10 − 3 × 问题数 |
| `section_coverage` | 25% | ≥6 节 → 10, ≥4 → 8, … |
| `example_density` | 20% | ≥6 示例 → 10, 含 TODO → −3 |
| `specificity_clarity` | 25% | 10 − 2 × 反模式数 |
| `trigger_clarity` | 15% | ≥5 触发短语 → 10, ≥3 → 8, … |

**💻 代码**

| 子分数 | 权重 | 计算方式 |
|--------|:----:|----------|
| `script_presence` | 10% | ≥3 脚本 → 10, 无脚本 → 2 |
| `syntactic_validity` | 35% | (有效数 / 总数) × 10；无脚本基准 5 |
| `error_handling` | 30% | 2 + (I/O 已覆盖 / I/O 总数) × 8；纯逻辑 → 8 |
| `script_documentation` | 25% | (有文档脚本 / 总数) × 10；无脚本基准 5 |

> **关键洞察：** 错误处理只计 **I/O 脚本**（执行文件/网络/Shell 操作的脚本）——纯逻辑脚本不会对技能扣分。无脚本技能在三个子分数上获得中性基准分 5。

**📋 完整性**

| 子分数 | 权重 | 计算方式 |
|--------|:----:|----------|
| `capability_coverage` | 40% | ≥8 个能力 → 10, ≥5 → 8, … |
| `edge_case_coverage` | 30% | min(10, 边界情况 × 2 + 非触发测试数) |
| `section_completeness` | 30% | (1 − 缺失必需节数 / 总必需节数) × 10 |

**🎯 可用性**

| 子分数 | 权重 | 计算方式 |
|--------|:----:|----------|
| `trigger_accuracy` | 30% | (通过数 / 总数) × 10；代理: min(10, 短语数 × 2) |
| `instruction_actionability` | 30% | ≥15 子弹点 → 10, ≥10 → 8, … |
| `edge_case_handling` | 20% | 存在 caution 章节 → 8, 否则 → 4 |
| `progressive_disclosure` | 20% | 有 H1 + ≥4 H2 + ≥2 H3 → 10, … |

---

## 🧪 命令行使用

```text
python scripts/run_tests.py <技能目录...> [选项]
```

| 选项 | 说明 |
|------|------|
| `skill-dirs` | 技能目录路径（位置参数，可多个） |
| `-o, --output FORMAT` | 输出格式：`summary`（默认）、`json`、`table` |
| `-e, --execute` | 通过 Claude CLI 启用真实测试执行 |
| `-c, --config PATH` | 自定义 YAML 配置文件路径 |
| `-q, --quiet` | 隐藏阶段进度输出 |
| `--no-color` | 禁用 ANSI 颜色输出 |
| `-V, --version` | 显示版本号并退出 |

### 示例

```bash
# 快速结构分析
python scripts/run_tests.py ./my-skill

# 完整流水线 — 分析、生成、执行、评分
python scripts/run_tests.py ./my-skill --execute

# CI 友好的 JSON 输出（静默模式）
python scripts/run_tests.py ./my-skill --output json --quiet

# 并排对比多个技能
python scripts/run_tests.py skills/* --output table
```

---

## 📁 项目结构

```
skill-tester/
├── 📁 config/
│   └── default.yaml              ← 所有阈值、权重和规则
├── 📁 scripts/
│   ├── run_tests.py               ← CLI 入口
│   ├── config.py                  ← 配置加载器
│   ├── utils.py                   ← 共享工具函数
│   ├── analyze.py                 ← 阶段 1：深度分析
│   ├── generate.py                ← 阶段 2：测试生成
│   ├── execute.py                 ← 阶段 3：真实执行
│   ├── evaluate.py                ← 阶段 4：4 维评分
│   └── formatters.py              ← 输出：JSON / table / summary
├── 📁 tests/
│   ├── conftest.py                ← 共享测试夹具
│   ├── test_analyze.py, test_generate.py, test_execute.py,
│   │   test_evaluate.py, test_config.py, test_formatters.py,
│   │   test_run_tests.py, test_integration.py
│   └── 📁 fixtures/
│       ├── good_skill/            ← 正确技能参考
│       ├── bad_skill/             ← 缺陷技能参考
│       └── full_skill/            ← 端到端：.py, .sh, .js + 参考 + 资产
├── 📁 references/
│   ├── scoring_guide.md           ← 详细评分指南
│   └── trigger_keywords.md        ← 触发模式参考
├── 📁 .github/workflows/
│   └── test.yml                   ← CI：flake8 + mypy + pytest + 自测
├── 📄 .flake8, mypy.ini, requirements.txt, pyproject.toml
└── 📄 README.md / README.zh-CN.md
```

---

## ⚙️ 配置

所有阈值集中在 [`config/default.yaml`](config/default.yaml)。无需修改代码即可覆盖任意配置：

| 方式 | 文件 | 持久性 |
|------|------|:------:|
| 本地覆盖 | `config/local.yaml` | ✅ Git-ignore |
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

内置 CI 工作流（`.github/workflows/test.yml`）每次推送自动运行：

```yaml
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

## 📚 了解更多

| 资源 | 说明 |
|------|------|
| [评分指南](references/scoring_guide.md) | 带示例的详细评分标准 |
| [触发关键词](references/trigger_keywords.md) | 触发模式参考 |
| [默认配置](config/default.yaml) | 所有设置一览 |
| [CI 工作流](.github/workflows/test.yml) | 流水线配置 |

---

## 🙏 致谢

| 项目 | 影响 |
|------|------|
| [cc-plugin-eval](https://github.com/sjnims/cc-plugin-eval) | 4 阶段流水线架构 |
| [claude-skills skill-tester](https://github.com/alirezarezvani/claude-skills) | 4 维评分体系 |
| [Anthropic skill-creator](https://github.com/anthropics/skills) | 评估与基准模式 |

---

<div align="center">

**🧪 为 Claude Code 技能社区打造**

`MIT License` · 欢迎贡献 —
[提交 Issue](https://github.com/topprismdata/skill-tester/issues) 或
[提交 PR](https://github.com/topprismdata/skill-tester/pulls)

</div>
