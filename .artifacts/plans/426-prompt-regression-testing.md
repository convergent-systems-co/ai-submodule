# Prompt Regression Testing Framework with Golden Datasets

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/426
**Branch:** NETWORK_ID/feat/426/prompt-regression-testing

---

## 1. Objective

Create an evaluation framework with golden test datasets for review panels, enabling regression testing when prompts are modified. Establish the `governance/evals/` directory structure and pytest integration.

## 2. Rationale

Prompt modifications currently have no quality gate. Changes to review prompts can silently degrade panel output quality. Industry standard (Promptfoo, Evidently) is to run prompt regression tests in CI.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Promptfoo integration | Yes | External dependency, complex setup |
| Custom eval framework | Yes | **Selected** — lightweight, pytest-native, fits existing test infra |
| Manual review only | Yes | Does not scale, misses regressions |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/evals/README.md` | Eval framework documentation |
| `governance/evals/golden/security-review/` | Golden test cases for security review panel |
| `governance/evals/golden/code-review/` | Golden test cases for code review panel |
| `governance/evals/golden/documentation-review/` | Golden test cases for documentation review panel |
| `governance/engine/tests/test_prompt_eval.py` | Pytest integration for prompt evaluation |
| `docs/guides/prompt-eval-framework.md` | User-facing documentation |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/panel-output.schema.json` | Add optional `groundedness_score` and `hallucination_indicators` fields |

### Files to Delete

None.

## 4. Approach

1. Create `governance/evals/` directory structure with README
2. Create golden test datasets for 3 panels (security-review, code-review, documentation-review) with at least 3 test cases each — each case has a sample code diff and expected verdicts/findings
3. Add `groundedness_score` (number 0-1) and `hallucination_indicators` (array of strings) as optional fields to panel-output.schema.json findings
4. Create `test_prompt_eval.py` with pytest fixtures that load golden datasets and validate panel outputs against expected results
5. Create `docs/guides/prompt-eval-framework.md` explaining how to add new test cases

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | Golden datasets | Validate dataset format and completeness |
| Unit | Schema | Validate new fields in panel-output.schema.json |
| Integration | Eval framework | Test the eval runner produces correct pass/fail results |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Golden datasets become stale | Medium | Medium | Version datasets alongside prompts |
| False positives in eval | Medium | Low | Start with high-confidence test cases only |

## 7. Dependencies

- None

## 8. Backward Compatibility

All schema additions are optional. Existing emissions remain valid. New test files don't affect existing tests.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Test infrastructure changes |
| code-review | Yes | New test framework |
| documentation-review | Yes | New documentation |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Custom framework over Promptfoo | Lightweight, no external deps |
| 2026-02-27 | Start with 3 panels | Prove concept before expanding to all 19 |
