# Plan: Move APPROVE verification into deterministic orchestrator (#551)

## Objective

Move the APPROVE structural integrity checks from the Team Lead persona (prompt-based) into deterministic Python code in the orchestrator, making the most critical governance decision code-based rather than prompt-based.

## Rationale

The merge/approve decision is currently governed by prompt instructions. This is a security gap: in single-context sessions where the Coder and Tester share the same LLM context, prompt injection is a viable self-approval vector. Deterministic code eliminates this risk.

## Scope

| File | Action |
|------|--------|
| `governance/engine/orchestrator/approve_verification.py` | Create — APPROVE payload validator |
| `governance/engine/orchestrator/runner.py` | Modify — integrate verification into Phase 4 |
| `governance/engine/orchestrator/step_runner.py` | Modify — add verification to step interface |
| `governance/engine/orchestrator/__init__.py` | Modify — export new module |
| `governance/engine/tests/test_approve_verification.py` | Create — tests |

## Approach

1. Create `approve_verification.py` with deterministic validation:
   - Validate required fields (`test_gate_passed`, `files_reviewed`, `acceptance_criteria_met`, `coverage_percentage`)
   - Cross-reference `files_reviewed` against a provided file list (from `git diff --name-only`)
   - Validate `acceptance_criteria_met` covers all issue criteria
   - Validate coverage percentage is within expected range
2. Integrate into runner.py Phase 4 collect
3. Add to step_runner.py for CLI access
4. Write comprehensive tests

## Testing Strategy

- Unit tests for validation logic
- Tests for edge cases (missing fields, mismatched files, etc.)
- Integration with existing test suite

## Risk Assessment

- Low: additive code, no destructive changes to existing runner logic
- Verification is additional validation, not replacing existing flow
