# Plan: Standardize confidence score formula across all review panels (#559)

## Objective

Standardize all 21 review prompts to use the same per-finding deduction confidence score formula, making scores comparable across panels.

## Rationale

Two different deduction models exist: per-finding and per-participant highest. This makes confidence scores incomparable across panels and breaks the policy engine's aggregation logic.

## Scope

All 21 files in `governance/prompts/reviews/*.md` -- update the Confidence Score Calculation section to use the canonical per-finding formula.

## Approach

1. Define the canonical formula (per-finding deduction with base 0.85)
2. Update all review prompts that use the per-participant model to per-finding
3. Ensure consistent wording across all 21 prompts

## Canonical Formula

```
Base confidence: 0.85
Per-finding deductions: Critical -0.25, High -0.15, Medium -0.05, Low -0.01
Formula: final = base - sum(severity_penalties)
Dedup: If multiple perspectives flag the same issue, count once at highest severity.
Floor: 0.0, Cap: 1.0
```
