# Prompt Evaluation Framework

This guide covers the prompt regression testing framework used to validate governance review prompts against known-good inputs (golden datasets).

## Overview

The eval framework ensures that changes to review prompts in `governance/prompts/reviews/` do not introduce regressions. It works by maintaining a set of golden test cases -- synthetic code diffs with expected panel behavior -- and validating that all test cases conform to the required structure.

### What It Tests

1. **Structural integrity** -- Every golden test case file has the required JSON fields and correct types.
2. **Directory consistency** -- Each panel directory contains the minimum number of test cases.
3. **Schema compatibility** -- The panel output schema supports quality metrics (`groundedness_score`, `hallucination_indicators`).
4. **Panel alignment** -- Each test case's `panel` field matches the directory it resides in.

### When It Runs

The eval suite runs automatically via CI on pull requests that modify:
- `governance/prompts/reviews/**` (review prompt changes)
- `governance/evals/**` (test case changes)
- `governance/schemas/panel-output.schema.json` (schema changes)
- `governance/engine/tests/test_prompt_eval.py` (test code changes)

## Directory Structure

```
governance/evals/
  README.md
  golden/
    security-review/
      sql-injection.json
      hardcoded-secret.json
      clean-code.json
    code-review/
      missing-error-handling.json
      good-patterns.json
      complexity-violation.json
    documentation-review/
      missing-docs.json
      complete-docs.json
      stale-docs.json
```

Each panel has its own directory under `governance/evals/golden/`. A minimum of 3 test cases per panel is required.

## Test Case JSON Format

Every golden test case is a JSON file with this structure:

```json
{
  "test_id": "<panel>-<scenario>-<sequence>",
  "panel": "<panel-name>",
  "description": "Human-readable description of the scenario",
  "input": {
    "diff": "unified diff content",
    "files_changed": ["path/to/file.py"],
    "change_type": "feat"
  },
  "expected": {
    "min_findings_critical": 0,
    "min_findings_high": 0,
    "min_findings_medium": 0,
    "expected_categories": ["category-tag"],
    "expected_verdict": "approve"
  }
}
```

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `test_id` | string | Yes | Unique identifier: `<panel>-<scenario>-<sequence>` |
| `panel` | string | Yes | Panel name, must match the parent directory name |
| `description` | string | Yes | Human-readable description of what the test case covers |
| `input.diff` | string | Yes | Unified diff representing the code change |
| `input.files_changed` | string[] | Yes | List of file paths affected by the change |
| `input.change_type` | string | Yes | Conventional commit type: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci` |
| `expected.min_findings_critical` | integer | No | Minimum number of critical findings expected |
| `expected.min_findings_high` | integer | No | Minimum number of high findings expected |
| `expected.min_findings_medium` | integer | No | Minimum number of medium findings expected |
| `expected.min_findings_low` | integer | No | Minimum number of low findings expected |
| `expected.expected_categories` | string[] | Yes | Category tags the panel should identify (empty for clean code) |
| `expected.expected_verdict` | string | Yes | Expected aggregate verdict: `approve`, `request_changes`, or `block` |

### Test Case Design Guidelines

- **Diffs should be realistic but concise** -- 10-30 lines is the target range. Enough to demonstrate the pattern, not so much that it obscures the signal.
- **Each case should test one primary concern** -- A SQL injection case should focus on SQL injection, not also test missing docs.
- **Include both positive and negative cases** -- Every panel should have at least one "clean" case that expects `approve`.
- **Use descriptive test IDs** -- The `test_id` should make the scenario obvious without reading the description.

## Adding New Golden Test Cases

### Step 1: Identify the Panel

Determine which panel the test case targets. The panel name must match an existing directory under `governance/evals/golden/` or you must create a new one.

### Step 2: Create the JSON File

Create a new `.json` file in the appropriate panel directory. Use a descriptive filename (e.g., `xss-reflected.json`, `missing-type-hints.json`).

### Step 3: Write the Diff

Write a realistic unified diff that demonstrates the scenario. Include:
- Proper diff headers (`diff --git`, `index`, `---`/`+++`, `@@` hunks)
- Enough context to identify the issue
- File paths that match `input.files_changed`

### Step 4: Define Expectations

Set the `expected` fields based on what a correct panel review should produce:
- For vulnerability cases: set the appropriate `min_findings_*` count and relevant categories
- For clean code cases: set all counts to 0, empty categories, and `expected_verdict: "approve"`

### Step 5: Validate

Run the eval suite locally to confirm the new test case passes structural validation:

```bash
cd governance/engine/tests
python -m pytest test_prompt_eval.py -v --tb=short
```

## Adding a New Panel

To add golden test cases for a panel not yet covered:

1. Create the directory: `governance/evals/golden/<panel-name>/`
2. Add at least 3 test cases (the minimum enforced by the test suite)
3. Add the panel name to the `REQUIRED_PANELS` list in `test_prompt_eval.py`
4. Run the eval suite to verify

## Running the Eval Suite

### Locally

```bash
# From the repository root
cd governance/engine/tests
python -m pytest test_prompt_eval.py -v

# Run only structure tests
python -m pytest test_prompt_eval.py::TestGoldenDirectoryStructure -v

# Run only a specific panel's cases
python -m pytest test_prompt_eval.py -k "security-review" -v

# Run with full output on failures
python -m pytest test_prompt_eval.py -v --tb=long
```

### In CI

The `prompt-eval.yml` workflow runs automatically on PRs that touch review prompts, eval files, or the panel output schema. Check the "Prompt Eval Suite" workflow in the PR checks for results.

## Interpreting Results

### All Tests Pass

The golden test cases are structurally valid and the schema supports quality metrics. This does not guarantee prompt correctness -- it guarantees the test infrastructure is sound.

### Structural Failures

If a test case fails structural validation:
- **Missing fields** -- Add the required field to the JSON file
- **Wrong types** -- Correct the field type (e.g., string vs. integer)
- **Panel mismatch** -- Ensure `panel` matches the directory name
- **Invalid verdict** -- Use one of: `approve`, `request_changes`, `block`

### Schema Failures

If schema compatibility tests fail:
- **Missing quality metrics** -- The `groundedness_score` or `hallucination_indicators` fields were removed from the panel output schema. These must remain as optional fields in the findings items.

## Quality Metrics

The framework adds two optional quality metrics to the panel output schema (in each finding):

### `groundedness_score` (number, 0.0-1.0)

Indicates how well a finding is grounded in actual code evidence. A score of 1.0 means the finding directly references specific code with file paths, line numbers, and snippets. A score near 0.0 suggests the finding is generic or speculative.

### `hallucination_indicators` (string[])

An array of signals suggesting a finding may contain hallucinated content. Examples:
- `"references_nonexistent_file"` -- Finding cites a file not in the diff
- `"line_numbers_outside_diff"` -- Evidence references lines outside the changed range
- `"generic_finding_no_evidence"` -- Finding lacks specific code references
- `"contradicts_diff_content"` -- Finding describes behavior contradicted by the actual code

These fields are optional and backward compatible. Existing emissions without them remain valid.
