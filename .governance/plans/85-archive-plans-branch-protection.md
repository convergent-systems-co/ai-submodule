# Fix archive-plans workflow branch protection violation

**Author:** Code Manager (agentic) / Coder (agentic)
**Date:** 2026-02-21
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/85
**Branch:** itsfwcp/fix/85/archive-plans-branch-protection

---

## 1. Objective

Fix the `plan-archival.yml` workflow's "Remove archived plans from repo" step to comply with branch protection rules by creating a temporary branch and auto-merged PR instead of pushing directly to `main`.

## 2. Rationale

The current workflow attempts `git push origin main` which fails because the repo has branch protection requiring all changes through PRs. Creating a cleanup PR is the correct pattern for protected branches.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Use PAT with bypass permissions | Yes | Requires secret configuration and reduces security |
| Skip removal entirely | Yes | Plan files accumulate in the repo tree indefinitely |
| Use GitHub API to create commit | Yes | API commits also respect branch protection rules |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| `.github/workflows/plan-archival.yml` | Replace direct push with branch creation + PR creation + auto-merge |

### Files to Create

None.

### Files to Delete

None.

## 4. Approach

1. Modify the "Remove archived plans from repo" step to:
   - Create a temporary branch `chore/archive-plans-pr-{PR_NUMBER}`
   - Commit the plan file removals to the branch
   - Push the branch
   - Create a PR with auto-merge enabled
2. Add a job-level condition to skip when the PR author is `github-actions[bot]` (prevent infinite loop)
3. Use `gh pr merge --auto --squash` for cleanup PRs

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| N/A | No runtime tests | Configuration-only repo — CI pipeline validates on next run |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Infinite loop from cleanup PRs | Medium | Medium | Skip workflow when PR author is github-actions[bot] |
| Auto-merge fails | Low | Low | PR stays open for human merge; non-blocking |

## 7. Dependencies

- [ ] No blocking dependencies

## 8. Backward Compatibility

Fully backward compatible. The workflow achieves the same outcome (plan files removed from repo) through a compliant mechanism.

## 9. Governance

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Branch + PR instead of direct push | Only approach that respects branch protection without elevated tokens |
| 2026-02-21 | Skip on github-actions[bot] PRs | Prevents infinite loop from cleanup PRs triggering the workflow |
