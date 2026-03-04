# Governance Workflow Health Check in Startup Pre-flight

**Author:** Team Lead (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/178
**Branch:** NETWORK_ID/feat/178/governance-workflow-health-check

---

## 1. Objective

Enhance the startup.md pre-flight section to verify that the Dark Forge governance workflow (`dark-factory-governance.yml`) is not only present but actively enabled and healthy — checking recent workflow run status and providing actionable warnings when the pipeline is non-functional.

## 2. Rationale

The current pre-flight check only verifies the workflow file exists on disk. This is insufficient because:
- The workflow could be disabled in GitHub Actions settings
- The workflow could be broken (syntax errors, missing secrets, etc.)
- The governance pipeline could be producing failures consistently

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| File-only check (current) | Yes | Does not detect disabled or broken workflows |
| GitHub Actions API health check | Yes | Selected — uses `gh api` to check workflow status and recent runs |
| Webhook-based health monitoring | No | Over-engineered for a pre-flight check |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| None | — |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Expand pre-flight step 3 to include workflow enabled check and recent run health check |

### Files to Delete

| File | Reason |
|------|--------|
| None | — |

## 4. Approach

1. **Expand pre-flight step 3** in `startup.md` to add three sub-checks after the file existence check:
   - **3a: Workflow file exists** (existing check, keep as-is)
   - **3b: Workflow is enabled** — Query `gh api repos/{owner}/{repo}/actions/workflows` to verify the governance workflow has `state: active`
   - **3c: Recent run health** — Query the last 5 workflow runs for the governance workflow. If all 5 are failures (or no runs exist), warn that the governance pipeline is non-functional
   - **3d: Failure handling** — If the workflow is disabled, suggest re-enabling; if broken, suggest investigating the failure logs

2. **Update documentation** — The changes are self-documenting within startup.md itself since startup.md IS the documentation.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | startup.md execution | Run the agentic loop and verify the new checks execute correctly |

N/A — this is a cognitive artifact (markdown prompt), not executable code. Testing is via manual execution of the startup sequence.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| GitHub API rate limiting | Low | Low | These are lightweight API calls (2 extra per session) |
| False negatives (workflow reported healthy but broken) | Low | Low | Checking last 5 runs provides reasonable signal |
| Network failure during API calls | Low | Low | All checks are non-blocking (warn and continue) |

## 7. Dependencies

- None — uses existing `gh api` tooling

## 8. Backward Compatibility

Fully additive change. Existing pre-flight checks are preserved; new sub-steps are added. No breaking changes.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Changes to a core governance prompt |
| code-review | Yes | Standard review |
| security-review | Yes | Standard review |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Check last 5 runs instead of last 1 | Single failure could be transient; 5 consecutive failures indicates a real problem |
| 2026-02-24 | Keep checks non-blocking | Pre-flight failures should warn, not halt — the agent may still be able to do useful work even with degraded governance |
