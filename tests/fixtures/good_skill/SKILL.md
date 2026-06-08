---
name: example-validator
description: Validates YAML configuration files for syntax correctness, schema compliance, and best-practice enforcement in CI pipelines.
---

# Example Validator

A well-structured skill for validating YAML configuration files.

## When to Use

- Before committing YAML configuration changes to a repository
- After modifying `.yaml` or `.yml` files in a CI pipeline
- To check that your YAML follows schema rules before deployment
- When debugging a YAML parsing error in production

## Stage 1: Analysis

Analyze the YAML file structure:

1. Parse the file using PyYAML safe_load
2. Check for duplicate keys
3. Validate indent consistency (2-space default)

## Stage 2: Validation

Validate against schema rules:

1. Check required fields exist
2. Verify field types match schema
3. Ensure no undefined fields present

## Stage 3: Best Practices

Check for common issues:

1. No trailing whitespace in values
2. Lines under 120 characters
3. Consistent quoting style

## Examples

```yaml
# Good configuration
name: my-app
version: "1.0"
dependencies:
  - python: ">=3.10"
```

```yaml
# Bad configuration
name: my-app
version: "1.0"
dependencies:
  - python: ">=3.10"
DuplicateKey: will-error
```

## Limitations

- Does not validate JSON Schema files
- Only supports 2-space indent
- Maximum file size: 10MB

## Do Not

- Do not use on binary files or symlinks
- Avoid running on auto-generated files without review
