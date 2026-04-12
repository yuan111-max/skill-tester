# skill-tester

Tests and evaluates any Claude Code skill for structural validity, quality, and trigger accuracy. Implements the cc-plugin-eval 4-stage pipeline (Analysis → Generation → Execution → Evaluation) and the 4D scoring rubric (Documentation/Code/Completeness/Usability 25% each).

## 4D Scoring Rubric

| Dimension | Weight | Score Range |
|-----------|--------|-------------|
| **Documentation** | 25% | 0–10 |
| **Code/Scripts** | 25% | 0–10 |
| **Completeness** | 25% | 0–10 |
| **Usability** | 25% | 0–10 |

## Tier Classification

| Final Score | Tier | Action |
|-------------|------|--------|
| ≥ 8.5 | **POWERFUL** | Deploy immediately |
| ≥ 7.0 | **STANDARD** | Good to deploy |
| ≥ 5.0 | **BASIC** | Functional, needs improvement |
| < 5.0 | **REJECT** | Do not deploy |

## Usage

```bash
git clone https://github.com/topprismdata/skill-tester.git
cd skill-tester
chmod +x scripts/run_tests.py
python3 scripts/run_tests.py <skill-dir>
```

## References

- Built on [cc-plugin-eval](https://github.com/sjnims/cc-plugin-eval)
- Inspired by [claude-skills skill-tester](https://github.com/alirezarezvani/claude-skills)
