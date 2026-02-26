# Fix: Compound 'and' Block Conditions Always Return False

**Author:** Code Manager (agentic)
**Date:** 2026-02-25
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/230
**Branch:** itsfwcp/fix/230/compound-and-block-conditions

---

## 1. Objective

Fix the policy engine so that compound `and` conditions in block rules are correctly evaluated instead of silently returning False. This restores the intended safety behavior where critical policy violations without remediation paths are blocked.

## 2. Rationale

The current implementation at line 374 returns False for ANY condition containing " and ", which silently disables 6+ block rules across all 4 policy profiles. This is a P1 security bug — critical policy violations can bypass the block gate.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Full expression parser (AST) | Yes | Over-engineering for current condition patterns; only `and` and `not` operators are used |
| Split on `and`, evaluate sub-conditions | Yes | **Selected** — handles all current patterns with minimal complexity |
| Remove compound conditions from YAML | Yes | Reduces policy expressiveness; doesn't fix the root cause |

## 3. Scope

### Files to Create

None.

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/bin/policy-engine.py` | Implement compound condition parsing in `_evaluate_block_condition`; apply same pattern to `_evaluate_escalation_condition` |
| `tests/test_policy_engine.py` | Add unit tests for compound block conditions |
| `tests/test_policy_integration.py` | Add integration tests using real profiles with compound conditions |

### Files to Delete

None.

## 4. Approach

1. In `_evaluate_block_condition`, replace the `if " and " in cond: return False` catch-all with a compound parser:
   - Split condition on ` and `
   - For each sub-condition, strip `not ` prefix if present
   - Evaluate each sub-condition using existing pattern matching
   - Negate result for `not`-prefixed sub-conditions
   - Return logical AND of all results
2. Handle the specific sub-condition patterns needed:
   - `any_policy_flag_severity == "critical"` — already handled
   - `not auto_remediable` — check that at least one flag has `auto_remediable: false`
   - Context-dependent sub-conditions (`panel_missing(...)`, `data_files_changed`, etc.) — return False with warning log
3. Add unit tests for compound conditions
4. Add integration tests against real policy profiles

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `_evaluate_block_condition` | Compound `and` with critical flag + not auto_remediable |
| Unit | `_evaluate_block_condition` | Compound `and` with critical flag + auto_remediable=True (should NOT block) |
| Unit | `_evaluate_block_condition` | Compound with context-dependent sub-condition |
| Integration | default.yaml | Critical non-remediable flag triggers block via full pipeline |
| Integration | reduced_touchpoint.yaml | Same compound condition in different profile |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing block behavior | Low | High | Existing tests verify current single-condition behavior still works |
| Missing a sub-condition pattern | Medium | Medium | Test all patterns used in current YAML profiles |

## 7. Dependencies

None.

## 8. Backward Compatibility

Additive change — previously-ignored conditions now evaluate. Behavior changes from "never block on compound conditions" to "correctly evaluate compound conditions." This is a bug fix, not a behavior change.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Core policy engine change |
| security-review | Yes | Block conditions are security-critical |
| testing-review | Yes | New test coverage |
| documentation-review | Yes | May need CLAUDE.md update |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Split-on-and approach over AST parser | Sufficient for current condition patterns; minimizes complexity |
