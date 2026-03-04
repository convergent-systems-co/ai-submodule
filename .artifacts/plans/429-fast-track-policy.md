# Fast-Track Policy Profile and Change-Type-Aware Panel Selection

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/429
**Branch:** NETWORK_ID/feat/429/fast-track-policy

---

## 1. Objective

Create a lightweight governance profile for trivial changes (docs, typos, chores) and add change-type-aware panel filtering so the full 6-panel ceremony is reserved for substantive changes.

## 2. Rationale

Every change currently triggers all required panels regardless of type. A README fix goes through the same pipeline as a security-critical code change, creating unnecessary overhead.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Skip governance for small changes | Yes | Violates governance-always principle |
| Reduce panels globally | Yes | Weakens security posture for real changes |
| Change-type-aware filtering | Yes | **Selected** — right-sizes ceremony to change type |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/policy/fast-track.yaml` | Lightweight policy profile for trivial changes |
| `governance/prompts/templates/plan-template-light.md` | Lightweight plan template (~50 lines) |
| `docs/guides/ceremony-decision-tree.md` | Flowchart for ceremony level selection |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/policy/default.yaml` | Add `panel_overrides_by_change_type` section |
| `governance/engine/tests/test_policy_engine.py` | Add tests for change-type panel selection |

### Files to Delete

None.

## 4. Approach

1. Create `governance/policy/fast-track.yaml` with reduced panel requirements (code-review + security-review only), auto-merge at 0.75 confidence, no plan required if < 3 files changed
2. Add `panel_overrides_by_change_type` section to `default.yaml`:
   - `docs_only`: documentation-review only
   - `chore`: code-review only
   - `test_only`: testing-review + code-review
3. Create `plan-template-light.md` — streamlined template for small changes
4. Create `docs/guides/ceremony-decision-tree.md` with decision flowchart
5. Add policy engine tests for change-type panel selection logic

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | Policy engine | Test fast-track rules apply correctly |
| Unit | Panel selection | Test change-type overrides select correct panels |
| Integration | End-to-end | Test docs_only change gets only documentation-review |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Misclassification bypasses security | Medium | High | Security-review always required in fast-track |
| Developers game the system | Low | Medium | Clear criteria for change type classification |

## 7. Dependencies

- None

## 8. Backward Compatibility

Additive. `fast-track.yaml` is a new profile. `panel_overrides_by_change_type` is optional in default.yaml.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Policy changes need security review |
| code-review | Yes | Policy and test changes |
| documentation-review | Yes | New documentation |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Security-review always required even in fast-track | Prevents security bypass |
