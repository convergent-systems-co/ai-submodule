# Track Copilot Review Recommendations as Issues

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/438
**Branch:** NETWORK_ID/feat/438/copilot-recommendation-tracking

---

## 1. Objective

Enhance Phase 4e of startup.md to create trackable GitHub issues for each Copilot review recommendation, with documented resolution (implemented, dismissed, or deferred) and a summary audit trail on the PR.

## 2. Rationale

Copilot recommendations currently lack an audit trail. Each recommendation needs documented resolution to maintain governance completeness.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Track in PR comments only | Yes | No structured tracking, easily lost |
| Track in panel emissions | Yes | Copilot recommendations are external, not panel-native |
| Create GitHub sub-issues | Yes | **Selected** — provides full audit trail with issue lifecycle |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `docs/governance/copilot-recommendation-tracking.md` | Documentation for recommendation tracking workflow |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Add Phase 4e-bis: Copilot Recommendation Triage sub-phase |

### Files to Delete

None.

## 4. Approach

1. Add Phase 4e-bis to startup.md after Phase 4e with:
   - For each Copilot recommendation: create a sub-issue with title `copilot-rec: <summary> (PR #N)`, labels, severity
   - Resolution tracking: closed as completed (with commit SHA) or closed as not planned (with rationale)
   - PR comment with recommendation summary table
   - DevOps Engineer pre-merge verification of all recommendation issues
2. Create documentation explaining the tracking workflow
3. Define the recommendation issue template format

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Workflow | Verify startup.md Phase 4e-bis instructions are clear and complete |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Issue spam from trivial recommendations | Medium | Low | Severity threshold — only create issues for medium+ |
| Increased per-PR overhead | Medium | Medium | Summary table reduces cognitive load |

## 7. Dependencies

- None — extends existing Phase 4e

## 8. Backward Compatibility

Additive change to startup.md. Existing workflows unaffected.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Startup.md is a critical governance artifact |
| code-review | Yes | Workflow logic changes |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Medium+ severity threshold for issue creation | Prevents noise from info/low recommendations |
