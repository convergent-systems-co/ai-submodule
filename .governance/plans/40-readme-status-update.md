# Update README and Create Goals.md

**Author:** Coder (agentic)
**Date:** 2026-02-21
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/40
**Branch:** itsfwcp/docs/40/readme-status-update

---

## 1. Objective

Update the README to accurately reflect the current state of the platform, and create a Goals.md tracking phase status and open work.

## 2. Rationale

The README's repository structure section is missing recently added files (governance workflows, policy engine, startup prompt, issue templates, checkpoints). The phase table is accurate but could better reflect progress within Phase 4a/4b.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Only update README | Yes | Issue suggests a separate Goals.md for tracking |
| Replace README with Goals.md | Yes | README serves a different purpose (onboarding) |
| Update README + create Goals.md | **Selected** | Serves both onboarding and tracking needs |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `GOALS.md` | Phase status tracker with completed and open work |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `README.md` | Update repo structure, phase table, add link to GOALS.md |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Update README.md:
   - Update repository structure tree with all current files
   - Update phase table with more granular progress
   - Add link to GOALS.md

2. Create GOALS.md:
   - Phase status with sub-items
   - Completed work (closed issues/PRs)
   - Open enhancements and known gaps

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual review | Both files | Verify accuracy against actual repo state |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| GOALS.md becomes stale | Medium | Low | Living document, updated as part of retrospective |

## 7. Dependencies

- [x] No blocking dependencies

## 8. Backward Compatibility

Additive only.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Documentation changes |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | GOALS.md separate from README | Different audiences — README for onboarding, GOALS for tracking |
