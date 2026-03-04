# Prompt Regression Testing Framework

This directory contains the evaluation framework for governance review prompts. It provides golden test datasets that validate prompt behavior against known inputs, ensuring that changes to review prompts do not introduce regressions.

## Directory Structure

```
governance/evals/
  README.md                          # This file
  golden/                            # Golden test datasets
    security-review/                 # Test cases for security-review panel
      sql-injection.json
      hardcoded-secret.json
      clean-code.json
    code-review/                     # Test cases for code-review panel
      missing-error-handling.json
      good-patterns.json
      complexity-violation.json
    documentation-review/            # Test cases for documentation-review panel
      missing-docs.json
      complete-docs.json
      stale-docs.json
```

## How It Works

Each golden test case is a JSON file containing:
- A synthetic code diff (input)
- Expected panel behavior (expected findings, verdicts, severity levels)

The pytest suite in `governance/engine/tests/test_prompt_eval.py` validates:
1. All golden test case files conform to the required JSON schema
2. All required fields are present and correctly typed
3. Test cases cover the declared panel

## Adding New Test Cases

See `docs/guides/prompt-eval-framework.md` for the full guide on adding test cases and running the eval suite.

## Test Case Format

```json
{
  "test_id": "<panel>-<scenario>-<sequence>",
  "panel": "<panel-name>",
  "description": "Human-readable description of the scenario",
  "input": {
    "diff": "unified diff content",
    "files_changed": ["path/to/file.py"],
    "change_type": "feat|fix|refactor|docs|test"
  },
  "expected": {
    "min_findings_critical": 0,
    "min_findings_high": 0,
    "min_findings_medium": 0,
    "expected_categories": ["category-tag"],
    "expected_verdict": "approve|request_changes|block"
  }
}
```
