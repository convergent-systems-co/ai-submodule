# Reconcile GOALS.md, README.md, and DEVELOPER_GUIDE.md Documentation Drift

**Author:** Coder (agentic)
**Date:** 2026-02-23
**Status:** in_progress
**Issue:** #127
**Branch:** itsfwcp/fix/127/reconcile-docs

---

## 1. Objective

Eliminate conflicting information across GOALS.md, README.md, and DEVELOPER_GUIDE.md so all three documents agree on current phase status, feature availability, and architecture descriptions. Add governance enforcement to prevent future drift.

## 2. Rationale

Single-pass reconciliation is the correct approach — the discrepancies are factual inconsistencies, not design disagreements. Each doc has a different audience (GOALS.md = tracking, README.md = comprehensive reference, DEVELOPER_GUIDE.md = quick onboarding), so they should agree on facts while varying in depth.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Merge all three into one doc | Yes | Each serves a different audience/purpose |
| Auto-generate from single source | Yes | Over-engineering for a config-only repo |

## 3. Scope

### Files to Create

None.

### Files to Modify

| File | Change Description |
|------|-------------------|
| GOALS.md | Add 9 missing issues to completed work tables; fix 3 incorrect PR numbers in Phase 5 prerequisites |
| README.md | Fix Phase 4b status ("Partial" → "Implemented"); update repository structure (schemas, policy files, docs) |
| DEVELOPER_GUIDE.md | Update policy file description; align file structure listing |
| governance/prompts/startup.md | Make Step 7h.2 explicitly name all four doc files |

### Files to Delete

None.

## 4. Approach

1. Fix GOALS.md: add missing completed work, fix PR number references
2. Fix README.md: Phase 4b status, update repository structure tree
3. Fix DEVELOPER_GUIDE.md: align policy description and file structure
4. Update startup.md Step 7h.2: explicitly name docs for cross-verification

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | All modified files | Verify facts match across all docs |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Missing an issue from completed work | Low | Low | Cross-referenced git log with issue tracker |
| Introducing new inconsistencies | Low | Medium | Final cross-doc review before commit |

## 7. Dependencies

N/A — no blocking dependencies.

## 8. Backward Compatibility

Pure documentation change. No behavioral impact.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Documentation-only change |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Group missing issues by category rather than chronologically | Matches existing GOALS.md table structure |
| 2026-02-23 | Update README.md file tree to reflect actual state rather than keeping it minimal | Accuracy over brevity for the comprehensive reference doc |
