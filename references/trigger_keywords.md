# Common Skill Trigger Keywords

Reference list of trigger phrases used by ``generate.py`` to construct
test prompts from a skill's **When to Use** sections and body content.

## Direct Trigger Phrases

These keywords signal that a section describes **when the skill should activate**:

| Phrase | Source |
|--------|--------|
| "When to use" | Convention in skill-creator template |
| "Use when" | Alternative phrasing |
| "Trigger" | Explicit trigger documentation |
| "Invoked when" | Describes activation conditions |
| "Activated when" | Describes activation conditions |
| "Apply when" | Domain-specific trigger |
| "Run when" | Workflow trigger |
| "Execute when" | Workflow trigger |
| "Call this skill" | Documentation-style trigger |

## Negative Trigger Contexts

These keywords identify sections describing **when the skill should NOT activate**:

| Phrase | Source |
|--------|--------|
| "Do not" | Constraint documentation |
| "Avoid" | Anti-pattern guidance |
| "Never" | Safety constraint |
| "Must not" | Hard constraint |
| "Warning" | Caution section |
| "Caution" | Caution section |
| "Limitation" | Scope boundary |
| "Caveat" | Edge-case note |
| "Troubleshooting" | Error recovery |

## Usage

These keywords drive the ``generate_tests()`` function in Stage 2 of the
pipeline, which extracts trigger conditions from SKILL.md and constructs
structured test prompts for Stage 3 execution.
