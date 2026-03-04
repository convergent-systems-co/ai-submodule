# Fix Migration-Review Panel human_review_required

**Author:** Project Manager (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #693
**Branch:** itsfwcp/fix/693/migration-review-escalation

---

## 1. Objective

Fix the policy engine escalation logic that unconditionally promotes `human_review_required` when any panel has `requires_human_review: true`, even when the panel's verdict is `approve`.

## 2. Rationale

In `governance/engine/policy_engine.py` lines 842-847, the escalation check iterates all emissions and returns `human_review_required` if any has `requires_human_review: true`. The migration-review baseline emission has this set to `true`, causing every PR to trigger human review regardless of actual risk.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Set baseline `requires_human_review: false` | Yes | Band-aid — other panels may have same issue |
| Guard with verdict check | Yes — chosen | Only escalate if panel verdict is NOT approve |
| Remove the check entirely | Yes | Field has valid use cases for non-approve verdicts |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/engine/policy_engine.py` | Guard escalation check: only trigger human_review_required if panel verdict is not `approve` |
| `governance/engine/tests/test_policy_engine.py` | Update test to reflect new conditional logic |

## 4. Approach

1. Modify lines 842-847 in policy_engine.py to add verdict check
2. Only escalate when `requires_human_review: true` AND `aggregate_verdict != "approve"`
3. Update the existing test `test_escalation_requires_human_review`
4. Add new test for the case where `requires_human_review: true` but verdict is `approve` (should NOT escalate)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | policy_engine.py | Test escalation with approve + requires_human_review combo |
| Unit | policy_engine.py | Test escalation with request_changes + requires_human_review combo |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Panels that genuinely need human review get skipped | Low | Medium | Only skip when verdict is approve |

## 7. Dependencies

- [ ] None

## 8. Backward Compatibility

Changes behavior: PRs that were previously escalated to human_review_required may now auto_merge if all panels approve. This is the intended fix.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Policy engine logic change |
| security-review | Yes | Affects governance decision path |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Guard escalation with verdict check | Preserves intent while fixing false positives |
