# Fix: Policy Profile Weights and Missing data-governance-review

**Author:** Team Lead (agentic)
**Date:** 2026-02-25
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/231, https://github.com/convergent-systems-co/dark-forge/issues/232
**Branch:** NETWORK_ID/fix/231-232/policy-weights-and-panels

---

## 1. Objective

Fix two policy profiles so that (a) `data-governance-review` is included per CLAUDE.md's mandate, and (b) all weights sum to exactly 1.0.

## 2. Rationale

Both profiles have inflated weight sums (1.10 and 1.15) which can inflate aggregate confidence scores past escalation/auto-merge thresholds. Both are missing `data-governance-review` which CLAUDE.md declares mandatory.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add data-governance-review with 0 weight | Yes | Defeats the purpose — panel wouldn't influence decisions |
| Only fix weights, skip data-governance-review | Yes | Doesn't satisfy the mandate in CLAUDE.md |
| Fix both issues together | Yes | **Selected** — same root cause, minimal scope |

## 3. Scope

### Files to Create

None.

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/policy/fin_pii_high.yaml` | Add data-governance-review to required_panels and weights; rebalance weights to 1.0 |
| `governance/policy/infrastructure_critical.yaml` | Add data-governance-review to optional_panels and weights; rebalance weights to 1.0 |

### Files to Delete

None.

## 4. Approach

1. **fin_pii_high.yaml**: Add `data-governance-review: 0.10` to weights, add to required_panels. Rebalance: reduce code-review to 0.10, security-review to 0.25, architecture-review to 0.05, testing-review to 0.10. Sum = 1.00.
2. **infrastructure_critical.yaml**: Add `data-governance-review: 0.05` to weights, add to optional_panels with data trigger. Rebalance: reduce code-review to 0.10, security-review to 0.18, architecture-review to 0.20, performance-review to 0.07, production-readiness-review to 0.10. Sum = 1.00.
3. Verify existing integration tests still pass with the new required_panels.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Integration | fin_pii_high profile | Existing test with updated panel list |
| Integration | infrastructure_critical profile | Existing test still passes |
| All profiles | Weight sum validation | Verify all 4 profiles sum to 1.0 |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Existing integration tests break with new required panels | Medium | Low | Update test fixtures to include data-governance-review |
| Weight rebalancing changes existing behavior | Low | Low | Changes are small and proportional |

## 7. Dependencies

None.

## 8. Backward Compatibility

Additive change — adding a new required/optional panel. Consuming repos that don't emit data-governance-review will see it as a missing panel (behavior depends on missing_panel_behavior setting).

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | YAML configuration change |
| documentation-review | Yes | CLAUDE.md consistency |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Batch #231 and #232 into one PR | Same root cause, adjacent files |
| 2026-02-25 | Add data-governance-review to required for fin_pii_high, optional for infra_critical | Infra profile less data-focused |
