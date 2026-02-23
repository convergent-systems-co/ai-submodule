# Fix: Governance workflow skip-review should warn, not silently pass

**Author:** Code Manager (agentic)
**Date:** 2026-02-23
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/146
**Branch:** itsfwcp/fix/146/skip-review-no-approve

---

## 1. Objective

When no panel emissions exist, the governance workflow's skip-review job should post a visible warning comment on the PR instead of silently passing. This ensures developers know governance was skipped and understand they need to configure panels.

## 2. Rationale

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Post --request-changes review | Yes | Too blocking for repos that haven't configured panels yet; prevents merge entirely |
| Post --comment review with warning | Yes | Selected — visible, non-blocking, informative |
| Fail the job (exit 1) | Yes | Would break repos without panels configured; too aggressive |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| `.github/workflows/dark-factory-governance.yml` | Update Job 3 (skip-review) to post a PR comment explaining governance was skipped |
| `governance/docs/repository-configuration.md` | Add warning about stale workflow copies in consuming repos |

### Files to Create

None.

### Files to Delete

None.

## 4. Approach

1. Update Job 3 steps to post a `--comment` review on the PR with a warning body explaining:
   - No panel emissions were found
   - Governance review was skipped
   - How to configure panels
2. Update repository-configuration.md with a section warning about stale workflow copies

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| CI | workflow syntax | GitHub Actions will validate YAML syntax on push |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Comment posted on every PR in repos without panels | Med | Low | Comment is informational, not blocking |
| GITHUB_TOKEN permissions insufficient | Low | Low | Workflow already has pull-requests: write |

## 7. Dependencies

None.

## 8. Backward Compatibility

Additive change. The job currently echoes silently; now it will also post a comment. No breaking behavior.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Workflow modification |
| security-review | Yes | CI/CD change |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Use --comment not --request-changes | Non-blocking is more appropriate for repos still configuring governance |
