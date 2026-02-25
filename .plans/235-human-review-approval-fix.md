# Fix human_review_required Auto-Approval

**Author:** Code Manager (agentic)
**Date:** 2026-02-25
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/235
**Branch:** itsfwcp/fix/235/human-review-approval-fix

---

## 1. Objective

Fix the CI workflow so that `human_review_required` decisions post a comment instead of auto-approving the PR, which contradicted the policy engine's determination that human review is needed.

## 2. Rationale

When the policy engine returns `human_review_required`, the CI workflow was approving the PR with `gh pr review --approve`. This effectively bypasses the human review requirement if the bot is a CODEOWNER.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Use `--comment` for human_review_required | Yes | **Selected** — straightforward, doesn't auto-approve |
| Add separate status check | Yes | Over-engineering; comment is sufficient to not auto-approve |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| `.github/workflows/dark-factory-governance.yml` | Change `--approve` to `--comment` for `human_review_required`; move all `${{ }}` from run blocks to env vars |

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Change the `human_review_required` step from `--approve` to `--comment`
2. Move all `${{ }}` expressions from `run:` blocks to `env:` blocks (addresses part of #238)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| CI | Workflow syntax | GitHub Actions will validate on push |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Branch protection may require approval | Medium | Medium | Repos should use status checks, not approval, for governance |

## 7. Dependencies

- [x] No blocking dependencies

## 8. Backward Compatibility

Behavioral change: PRs requiring human review will no longer be auto-approved. This is intentional and correct.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | CI workflow security change |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Also sanitize ${{ }} expressions | Opportunity to address part of #238 while modifying the same file |
