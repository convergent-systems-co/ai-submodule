# Add FinOps Review as Default Required Panel

**Author:** Team Lead (agent)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/455
**Branch:** NETWORK_ID/feat/455/finops-review-panel

---

## 1. Objective

Add a FinOps review panel (`finops-review`) as a default required panel across all policy profiles, providing cost optimization recommendations including safe shutdown/destruction guidance with mandatory human approval guardrails.

## 2. Rationale

The existing `cost-analysis` panel focuses on change-level cost impact. Teams need holistic FinOps recommendations: right-sizing, reserved instances, idle resource detection, and safe shutdown/destruction options.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Extend cost-analysis panel | Yes | Would overload the existing panel's scope; FinOps is a distinct concern |
| Make FinOps optional | Yes | Issue explicitly requires it as a default required panel |
| Automate shutdown actions | Yes | NON-NEGOTIABLE safety constraint — panel recommends, humans decide |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/prompts/reviews/finops-review.md` | FinOps review panel with 5 perspectives |
| `governance/emissions/finops-review.json` | Baseline emission for fallback scenarios |
| `docs/governance/finops-review.md` | Documentation for the FinOps review panel |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/policy/default.yaml` | Add `finops-review` to `required_panels` and `weighting`, add destruction safety rules |
| `governance/policy/fin_pii_high.yaml` | Add `finops-review` to `required_panels` |
| `governance/policy/infrastructure_critical.yaml` | Add `finops-review` to `required_panels` |
| `governance/policy/reduced_touchpoint.yaml` | Add `finops-review` to `required_panels` |
| `governance/schemas/panel-output.schema.json` | Add optional `destruction_recommended` and `requires_human_approval` fields |
| `governance/engine/tests/test_policy_engine.py` | Add tests for FinOps panel and destruction blocking rules |
| `GOALS.md` | Mark FinOps review panel as completed |

### Files to Delete

None.

## 4. Approach

1. Create `governance/prompts/reviews/finops-review.md` following the cost-analysis.md pattern with 5 perspectives: FinOps Strategist, Resource Optimizer, Shutdown/Decommission Analyst, Savings Plan Advisor, Cost Allocation Auditor
2. Add optional `destruction_recommended` (boolean) and `requires_human_approval` (boolean) fields to `panel-output.schema.json`
3. Create baseline emission `governance/emissions/finops-review.json`
4. Add `finops-review` to `required_panels` in all 5 policy profiles (excluding fast-track)
5. Add `finops-review` weight (0.04) to `default.yaml` weighting model
6. Add destruction safety block rule to `default.yaml`: when `destruction_recommended == true`, block auto-merge
7. Write policy engine tests for destruction blocking and FinOps panel requirement
8. Create `docs/governance/finops-review.md` documentation
9. Update GOALS.md

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `test_policy_engine.py` | Test destruction_recommended blocks auto-merge |
| Schema | `test_schema_validation.py` | Validate baseline emission against updated schema |
| Integration | `test_policy_integration.py` | Full policy evaluation with finops-review emission |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing emissions | Low | High | New fields are optional with defaults |
| Weight redistribution | Low | Medium | Small weight (0.04) |
| Destruction flag misuse | Low | High | requires_human_approval enforced by block rule |

## 7. Dependencies

- [ ] None — additive change

## 8. Backward Compatibility

Fully backward compatible. New schema fields are optional. Existing emissions without `destruction_recommended` default to `false`.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Destruction safety guardrails |
| documentation-review | Yes | New panel documentation |
| code-review | Yes | Policy profile changes |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Separate panel from cost-analysis | FinOps operational focus differs from change-level cost analysis |
| 2026-02-27 | 5 perspectives for FinOps panel | Covers strategy, optimization, decommission, savings plans, cost allocation |
