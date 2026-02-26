# Add Auto-propagation Workflow

**Author:** Code Manager (agentic)
**Date:** 2026-02-20
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/12
**Branch:** itsfwcp/12-auto-propagation

---

## 1. Objective

Create a GitHub Actions workflow that opens PRs in consuming repos to update the .ai submodule pointer on push to main.

## 2. Rationale

Consuming repos currently must manually update their .ai submodule pointer. Auto-propagation ensures governance updates flow to all consuming repos with a PR-based review gate.

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.github/workflows/propagate-submodule.yml` | GitHub Action that opens PRs in consuming repos |

### Files to Modify

None.

## 4. Approach

1. Create workflow triggered on push to main
2. Use matrix strategy with a configurable list of consuming repos
3. For each repo: checkout with submodules, update .ai pointer, create PR
4. Include changelog of what changed in .ai in the PR body
5. Use peter-evans/create-pull-request action as specified in the issue
6. Require a PAT secret (`SUBMODULE_PROPAGATION_TOKEN`) with repo scope for cross-repo access

## 5. Testing Strategy

Manual — requires actual push to main and consuming repos to test.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PAT token missing | Medium | Workflow fails silently | Fail fast with clear error message |
| Consuming repo list stale | Medium | PRs to wrong repos | Document how to update the list |

## 7. Dependencies

- `SUBMODULE_PROPAGATION_TOKEN` secret must be configured in the repo
- Consuming repos must have .ai as a submodule
