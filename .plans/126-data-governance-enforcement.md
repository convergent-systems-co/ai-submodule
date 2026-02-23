# Data Governance Standards Enforcement

**Author:** Code Manager (agentic)
**Date:** 2026-02-23
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/126
**Branch:** `itsfwcp/feat/126/data-governance-enforcement`

---

## 1. Objective

Integrate data governance standards from SET-Apps/dach-canonical-models into the Dark Factory governance framework. Create a data-governance-review panel as a required default, enforce canonical model standards on every PR, and implement a workflow for handling missing canonical models (cross-repo issue creation).

## 2. Rationale

The dach-canonical-models repository defines enterprise data standards (naming conventions, schema validation, external reference discipline, deployment governance). These must be enforced automatically through the governance pipeline so that consuming repos cannot merge data changes that violate canonical standards.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Extend data-design-review panel | Yes | Different scope — data-design covers DB schemas; data-governance covers canonical model standards |
| GitHub Actions webhook in canonical repo | Yes | Out of scope — governance framework is config-only |
| Data governance panel + workflow prompt (selected) | Yes | Fits the governance framework model — cognitive artifact + enforcement config |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/personas/panels/data-governance-review.md` | Panel definition for data governance review |
| `governance/emissions/data-governance-review.json` | Baseline emission for the panel |
| `governance/prompts/data-governance-workflow.md` | Agentic workflow for missing canonical handling |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/policy/default.yaml` | Add data-governance-review to required panels and weighting |
| `instructions/governance.md` | Add data governance to default panel list |
| `instructions.md` | Add data governance to required panel list |
| `GOALS.md` | Track issue #126 |
| `CLAUDE.md` | Update panel counts and required panel list |

### Files to Delete

None.

## 4. Approach

1. Create `data-governance-review` panel definition based on canonical model standards
2. Create baseline emission JSON
3. Create missing-canonical workflow prompt
4. Update `default.yaml` — add to required panels, add weight, update version
5. Update instructions with new required panel
6. Update documentation (GOALS.md, CLAUDE.md)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| CI | Workflow | Governance workflow runs on the PR and validates the new emission |
| Manual | Panel definition | Review panel criteria match canonical model standards |
| Schema | Emission | Verify emission conforms to panel-output.schema.json |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Consuming repos blocked by new required panel | Medium | Medium | Phase 4b transition allows missing panels when present panels approve |
| Canonical repo integration complexity | Low | Low | Workflow is a cognitive artifact (prompt), not runtime code |

## 7. Dependencies

- [x] dach-canonical-models repo analysis — completed
- [x] Understanding of panel system — completed

## 8. Backward Compatibility

Adding a new required panel is additive. Existing consuming repos will see it as a missing panel, handled by `missing_panel_behavior: redistribute` in the Phase 4b transition until they configure the panel.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New panel and policy config |
| security-review | Yes | Required by policy |
| documentation-review | Yes | Significant doc changes |
| threat-modeling | Yes | Required by policy |
| cost-analysis | Yes | Required by policy |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Separate panel from data-design-review | Different governance domains — DB design vs. canonical model compliance |
| 2026-02-23 | Weight at 0.10 (reallocated from others) | Data governance is enterprise-critical per issue P0 label |
