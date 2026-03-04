# Plan: Add JIT Loading Tier Budget Validation Tests (#542)

## Objective
Create `governance/engine/tests/test_jit_loading.py` to validate token budget constraints for JIT context tiers.

## Approach
- Use `len(text) / 4` heuristic for token estimation (as specified in issue)
- Validate Tier 0: instructions.md under budget
- Validate Tier 1: persona headers aggregate under budget
- Validate Tier 2: review prompts under budget (with documented exceptions)
- Validate documented exceptions (startup.md, threat-modeling.md)
- Verify ANCHOR markers in instructions.md
- Act as regression gate for new files exceeding budgets

## Files
- New: `governance/engine/tests/test_jit_loading.py`
