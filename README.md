# skill-tester

**4 阶段流水线 + 4 维评分，用于 Claude Code 技能评估。**

对任意 Claude Code 技能进行结构有效性、内容质量、配套完整性和触发准确性的全面分析。在将技能部署到生产环境之前，用可量化的指标取代主观判断。

```text
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  阶段 1     │ →  │  阶段 2     │ →  │  阶段 3     │ →  │  阶段 4     │
│  分析       │    │  生成       │    │  执行       │    │  评估       │
│  ─────────  │    │  ─────────  │    │  ─────────  │    │  ─────────  │
│  SKILL.md   │    │  触发条件   │    │  Claude CLI │    │  4 维评分   │
│  配套文件   │    │  能力       │    │  PASS/FAIL  │    │  等级分类   │
│  反模式     │    │  边界情况   │    │  计时       │    │  报告       │
│  检测       │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 功能特性

- **🔍 深度结构分析** — YAML 前置元数据验证、递归扫描配套文件、内容质量指标
- **📋 自动测试生成** — 从 SKILL.md 中提取触发条件、能力和边界情况
- **⚡ 真实执行** — 通过 `claude` CLI 运行测试（使用 `--execute`），测量实际技能激活效果
- **📊 4 维评分** — 可配置的权重、子分数和等级阈值
- **🔎 反模式检测** — 自动捕获 TODO 标记、模板残留、占位符内容和模糊表述
- **📐 跨技能对比** — 使用 `--output table` 将多个技能并排对比
- **⚙️ 完全可配置** — 所有阈值、权重和规则均集中在单个 YAML 配置文件中

---

## 快速开始

```bash
# 1. 安装
git clone https://github.com/topprismdata/skill-tester.git
cd skill-tester
pip install -r requirements.txt

# 2. 运行基础分析（不执行测试）
python scripts/run_tests.py path/to/my-skill

# 3. 完整流水线（含实时代理测试）
python scripts/run_tests.py path/to/my-skill --execute

# 4. 对比两个技能
python scripts/run_tests.py path/to/skill-a path/to/skill-b --output table

# 5. JSON 输出（适用于 CI / 自动化）
python scripts/run_tests.py path/to/my-skill --output json
```

---

## 使用方法

```text
python scripts/run_tests.py <skill-dirs...> [选项]

位置参数：
  skill-dirs              技能目录路径（一个或多个）

选项：
  --output / -o           输出格式：summary（默认）、json、table
  --execute / -e          通过 Claude CLI 启用真实测试执行
  --config / -c           自定义 YAML 配置文件路径
  --quiet / -q            隐藏阶段进度输出
  --no-color              禁用输出中的 ANSI 颜色
```

---

## 评分概览

| 维度         | 权重 | 衡量内容                               |
|-------------|------|----------------------------------------|
| 文档        | 25%  | SKILL.md 的清晰度、结构、示例、触发条件  |
| 代码        | 25%  | 配套脚本的正确性、错误处理               |
| 完整性      | 25%  | 所有声明能力的覆盖情况                   |
| 易用性      | 25%  | 触发的可靠性、指令的可操作性              |

每个维度由 **子分数**（如前置元数据有效性、章节覆盖率、示例密度）计算得出，定义在 `config/default.yaml` 中。

**最终分数**（0–10 分）→ **等级**：

| 分数   | 等级      | 建议行动                               |
|--------|----------|----------------------------------------|
| ≥ 8.5  | POWERFUL | 可立即部署，设为标杆                     |
| ≥ 7.0  | STANDARD | 可以部署，建议修补次要不足                |
| ≥ 5.0  | BASIC    | 可用，但需要改进                        |
| < 5.0  | REJECT   | 需要重大重写                            |

---

## 各阶段详解

### 阶段 1：分析
- 解析 YAML 前置元数据（`name`、`description`、各种校验检查）
- 递归扫描 `scripts/`、`references/`、`assets/` 目录
- 内容质量指标：章节数量、示例密度、行数统计
- 反模式扫描：TODO 标记、模板残留、占位符语言、模糊引用
- Python 脚本语法验证（通过 `py_compile`）

### 阶段 2：测试生成
- **触发测试**：提取所有"何时使用"条款作为测试提示
- **非触发测试**：生成*不应*激活该技能的提示
- **边界情况**：提取"不要"、"限制"、"注意事项"等章节作为测试提示
- **能力测试**：章节标题和面向操作的要点列表

### 阶段 3：执行
- 通过 `claude --non-interactive --print` 运行每个测试提示
- 使用启发式方法检测响应中的技能激活情况
- 根据预期的触发行为对每个测试进行 PASS/FAIL 评分
- 当 CLI 不可用时优雅降级，并给出明确提示信息

### 阶段 4：评估
- 可配置的维度权重（默认各 25%）
- 每个维度的子分数聚合
- 最终分数 → 等级映射
- 各维度详情，便于调试

---

## 项目结构

```
skill-tester/
├── config/
│   └── default.yaml            # 所有阈值、权重和规则
├── scripts/
│   ├── __init__.py
│   ├── run_tests.py             # CLI 入口
│   ├── config.py                # 配置加载器
│   ├── analyze.py               # 阶段 1
│   ├── generate.py              # 阶段 2
│   ├── execute.py               # 阶段 3
│   ├── evaluate.py              # 阶段 4
│   └── formatters.py            # 输出：json、table、summary
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # 共享测试夹具
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
│       └── full_skill/          # .py、.sh、.js + 参考 + 资源
├── references/
│   ├── scoring_guide.md
│   └── trigger_keywords.md
├── .github/workflows/test.yml   # CI（flake8 + mypy + pytest + 自测）
├── .flake8                      # 代码检查配置
├── mypy.ini                     # 类型检查配置
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 配置

所有配置集中在 [`config/default.yaml`](config/default.yaml) 中。可通过以下方式覆盖任意配置：

1. 创建 `config/local.yaml`（自动加载，已被 git 忽略）
2. 传入 `--config path/to/custom.yaml`

### 可配置项

- **评分**：维度权重、子分数定义、等级阈值
- **分析**：最小描述长度、必需章节、脚本扩展名
- **执行**：Claude CLI 命令、超时时间、最大测试数、温度参数
- **反模式**：匹配模式、严重级别、提示消息
- **输出**：格式、颜色、预览长度

---

## 开发

```bash
# 安装开发依赖
pip install -r requirements.txt pytest pytest-cov

# 运行测试
pytest tests/ -v

# 带覆盖率
pytest tests/ --cov=scripts --cov-report=term-missing

# 自测（用 skill-tester 测试自身）
python scripts/run_tests.py .
```

---

## 参考致谢

- 基于 [cc-plugin-eval](https://github.com/sjnims/cc-plugin-eval)（4 阶段流水线）
- 灵感来源于 [claude-skills skill-tester](https://github.com/alirezarezvani/claude-skills)（4 维评分体系）
- 评估方法参考 [Anthropic skill-creator](https://github.com/anthropics/skills)（评估/基准模式）
- 以及 SkillCompass、PluginEval、Caliper 等社区工具的设计思路

---

## 许可证

MIT
