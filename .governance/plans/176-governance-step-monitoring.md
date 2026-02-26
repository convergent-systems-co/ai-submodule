# Governance Step Monitoring

**Author:** Code Manager (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/176
**Branch:** itsfwcp/feat/176/governance-step-monitoring

---

## 1. Objective

Implement a governance step observer that detects when governance steps are skipped — missing plans, missing panel evaluations, skipped Copilot reviews, missing documentation updates — and reports violations. Delivered as governance artifacts (schema, panel, checklist) that the existing pipeline evaluates.

Note: This PR addresses only the governance step monitoring component of #176. Cross-repo issue escalation will be tracked as a separate follow-up issue.

## 2. Rationale

The governance pipeline defines required steps (startup.md), but there is no mechanism to verify compliance after the fact. An agent or human could skip panels, omit Copilot review, or push PRs without plans. This observer closes that gap by adding a compliance review panel that evaluates evidence of governance step completion.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Real-time session monitor (daemon) | Yes | Requires a long-running process outside the AI context; not feasible as a governance artifact |
| Post-merge audit only | Yes | Too late to block; useful for retrospective but not preventive |
| PR-time compliance panel (chosen) | Yes | Evaluates compliance evidence at PR time, can block merge if steps are missing |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/governance-compliance.schema.json` | Schema for compliance evidence (what steps were executed) |
| `governance/personas/panels/governance-compliance-review.md` | Panel that evaluates governance step compliance |
| `governance/prompts/governance-compliance-checklist.md` | Checklist of required steps with evidence requirements |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/policy/default.yaml` | Add governance-compliance-review as optional panel |
| `governance/docs/repository-configuration.md` | Document the new compliance monitoring capability |
| `CLAUDE.md` | Update panel count (18 -> 19) |

### Files to Delete

None.

## 4. Approach

1. Define the compliance evidence schema — what evidence each governance step produces
2. Create the compliance checklist prompt — enumerate required steps and their verification method
3. Create the compliance review panel — evaluates PR against the checklist
4. Register the panel as optional in the default policy profile
5. Update documentation
6. Create follow-up issue for cross-repo escalation

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | governance-compliance.schema.json | Verify schema is valid JSON Schema |
| Manual review | Panel definition | Verify panel covers all startup.md steps |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| False positives (flagging compliant work) | Medium | Low | Panel classifies findings by severity; low/info items don't block |
| Panel adds overhead to every PR | Low | Low | Optional panel, triggered only when governance context exists |

## 7. Dependencies

None.

## 8. Backward Compatibility

Fully backward compatible. New panel is optional. Consuming repos can opt in via project.yaml.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New schema and panel definitions |
| documentation-review | Yes | Documentation changes included |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | PR-time evaluation over real-time daemon | Governance artifacts don't require long-running processes |
| 2026-02-24 | Split cross-repo escalation to separate issue | Human approved splitting; keeps scope manageable |
