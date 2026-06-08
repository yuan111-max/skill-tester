---
name: full-skill
description: A complete skill fixture with scripts, references, and assets for integration testing
---

# When to Use

Use this skill when you need to:

- Validate JSON configuration files
- Check YAML syntax and schema compliance
- Analyze log files for error patterns
- Generate summary reports from structured data

# Stage

This skill operates in three stages:

1. **Parse** — Read and validate input format
2. **Analyze** — Check content against rules
3. **Report** — Generate structured output

# Usage

## Parse JSON

The skill can parse and validate JSON files for structural correctness.

## Check YAML

Schema validation for YAML files with custom rule sets.

## Analyze Logs

Pattern matching against known error signatures.

## Generate Reports

Summary and detailed report generation in markdown format.

# Configuration

```yaml
rules:
  strict_mode: true
  max_file_size: 1048576
  allowed_formats:
    - json
    - yaml
    - log
```

# Examples

## Example 1: Validate a JSON file

```python
import json

with open("config.json") as f:
    data = json.load(f)
print(f"Valid JSON with {len(data)} keys")
```

## Example 2: Check YAML syntax

```python
import yaml

with open("config.yaml") as f:
    data = yaml.safe_load(f)
print(f"Valid YAML with {len(data)} keys")
```

## Example 3: Analyze a log file

```bash
grep -E "ERROR|FATAL" application.log | wc -l
```

# Triggers

- Validate a configuration file
- Check my YAML for errors
- Analyze this log file
- Generate a report from this data
- Parse this JSON structure

# Limitations

- Does not execute arbitrary code from configuration files
- Maximum file size is 10 MB for analysis
- Only supports UTF-8 encoded files
- Network access is not available during analysis

# Do Not

- Do not use this skill with binary files
- Do not attempt to validate encrypted configurations
- Do not use with files larger than 10 MB
