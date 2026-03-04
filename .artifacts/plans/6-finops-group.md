# Create FinOps Group

**Author:** Team Lead (agentic)
**Date:** 2026-02-20
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/6
**Branch:** NETWORK_ID/6-finops-group

---

## 1. Objective

Add a FinOps category with two personas: finops-engineer (infrastructure cost governance) and finops-analyst (financial reporting and forecasting).

## 2. Rationale

FinOps is a distinct discipline from general operations cost optimization. The existing Cost Optimizer persona focuses on tactical cloud spend reduction. FinOps personas cover the broader practice: showback/chargeback, unit economics, forecasting, and organizational cost accountability.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add to operations/ | Yes | FinOps is a cross-functional discipline, not a subset of ops |
| Merge with Cost Optimizer | Yes | Cost Optimizer is tactical; FinOps is strategic and organizational |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `personas/finops/finops-engineer.md` | Cloud cost governance, tagging, budget enforcement |
| `personas/finops/finops-analyst.md` | Financial reporting, forecasting, unit economics |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `personas/index.md` | Add FinOps section with both personas |

## 4. Approach

1. Create `personas/finops/` directory
2. Create `finops-engineer.md` — focuses on tagging standards, budget alerts, rightsizing governance, waste detection
3. Create `finops-analyst.md` — focuses on showback/chargeback, unit cost tracking, forecasting, anomaly detection
4. Add FinOps section to `personas/index.md`
5. Commit, push, create PR

## 5. Testing Strategy

Manual verification of persona format consistency with existing personas.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Overlap with Cost Optimizer | Low | Low | Distinct scope: strategic (FinOps) vs tactical (Cost Optimizer) |

## 7. Dependencies

None.
