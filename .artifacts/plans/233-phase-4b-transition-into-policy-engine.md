# Move Phase 4b Transition Logic into Policy Engine

**Author:** Team Lead (agentic)
**Date:** 2026-02-25
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/233
**Branch:** NETWORK_ID/fix/233/phase-4b-transition-into-policy-engine

---

## 1. Objective

Move the Phase 4b transition logic from the CI workflow into the policy engine so that all merge decisions are made by the engine, not the CI layer. This eliminates a policy bypass where the CI overrides `block` to a non-standard `approve` value via string matching on rationale text.

## 2. Rationale

The current CI workflow (lines 125-142) overrides the policy engine's `block` decision by checking `'missing' in rationale.lower()`, all present panels approving, and confidence >= 0.70. This violates:
1. "AI models never interpret policy rules" — uses string matching on prose
2. "Policies are evaluated programmatically" — CI layer makes a policy decision
3. The `approve` value is not a valid policy engine output
4. No audit trail in the manifest

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add `approve` as a valid decision | Yes | `approve` is ambiguous — engine already has `auto_merge` and `human_review_required` |
| Profile-level `phase_4b_transition` config | Yes | Adds complexity to all 4 profiles for what is standard engine behavior |
| Handle in `evaluate()` with engine-level logic | Yes | **Selected** — keeps all decisions in the engine with full audit trail |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files required |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/bin/policy-engine.py` | Add Phase 4b transition logic in `evaluate()` between missing panel check and block evaluation |
| `.github/workflows/dark-factory-governance.yml` | Remove Phase 4b override (lines 125-142), remove `approve` catch-all step (lines 188-192) |
| `tests/test_policy_engine.py` | Add unit tests for Phase 4b transition |
| `tests/test_policy_integration.py` | Add integration tests for Phase 4b through full pipeline |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. **Modify `evaluate()` in policy-engine.py**: After computing aggregate confidence (Step 5) and before evaluating block conditions (Step 8), add Phase 4b transition check:
   - If `missing_required` is non-empty AND `missing_panel_behavior != "block"`:
     - Check if all present panel verdicts are `approve`
     - Check if aggregate confidence >= 0.70
     - If both: log the Phase 4b transition, clear `missing_required` so block evaluation continues normally
     - If not: proceed to block evaluation which will trigger the missing panel block
   - Record the transition in the evaluation log (which is part of the manifest)

2. **Remove CI override from workflow**: Delete lines 125-142 (Phase 4b inline Python) and lines 188-192 (catch-all `approve` step that handled the non-standard decision value).

3. **Add unit tests**: Test Phase 4b transition conditions directly in `test_policy_engine.py`.

4. **Add integration tests**: Test Phase 4b through the full `evaluate()` pipeline with real profiles.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `evaluate()` Phase 4b transition | Test that missing panels with all-approve + high confidence proceeds normally instead of blocking |
| Unit | `evaluate()` Phase 4b not triggered | Test that missing panels with low confidence or non-approve verdicts still block |
| Integration | default profile Phase 4b | Test full pipeline: missing panel + high confidence + all approve → auto_merge or human_review (not block) |
| Integration | fin_pii_high profile | Test that `missing_panel_behavior=block` still hard-blocks regardless of Phase 4b |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Phase 4b transition too permissive | Low | Medium | Confidence threshold of 0.70 matches existing CI logic; all present panels must approve |
| Breaking fin_pii_high hard-block | Low | High | Phase 4b explicitly skipped when `missing_panel_behavior=block`; integration test verifies |
| Existing tests regressing | Low | Low | Run full test suite before and after |

## 7. Dependencies

- [x] No blocking dependencies

## 8. Backward Compatibility

Additive change to policy engine. The CI workflow produces the same effective behavior but now all decisions flow through the engine. No consuming repo changes needed.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | CI workflow changes affect security boundary |
| code-review | Yes | Policy engine logic change |
| documentation-review | Yes | CLAUDE.md mentions Phase 4b |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Use 0.70 confidence threshold | Matches existing CI logic to maintain behavioral parity |
| 2026-02-25 | Phase 4b transition logged in evaluation log, not as separate manifest field | Avoids schema change while providing full audit trail via existing `policy_rules_evaluated` |
