# Plan: Mechanical Containment Policy Enforcement (#570)

## Summary
Add a pre-commit hook and CI check that validates file change boundaries
per branch pattern. Branches matching `*/coder/*` cannot change governance
infrastructure files.

## Changes

### 1. New file: `governance/engine/containment_hook.py`
- Pre-commit hook logic that validates staged files against containment rules
- Branch pattern matching (*/coder/* restricted from governance/policy/**, governance/schemas/**)
- Can be used as a git pre-commit hook or CI check
- Returns exit code 0 (pass) or 1 (violation)

### 2. New file: `governance/engine/tests/test_containment_hook.py`
- Tests for branch pattern matching
- Tests for file restriction validation
- Tests for allowed/denied combinations

## Test Plan
- `python -m pytest governance/engine/ -x --tb=short`
