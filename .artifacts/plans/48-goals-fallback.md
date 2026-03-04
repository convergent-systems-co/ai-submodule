# Agentic Loop Goals Fallback

**Author:** Team Lead (agentic)
**Date:** 2026-02-21
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/48
**Branch:** NETWORK_ID/feat/48/goals-fallback

---

## 1. Objective

When the agentic loop has no actionable GitHub issues, it should fall back to GOALS.md and pick up unimplemented items as work. Each GOALS.md item is converted to a GitHub issue before work begins, following the existing governance workflow.

## 2. Rationale

Currently the agentic loop exits when no actionable issues remain. GOALS.md contains Phase 4b and Phase 5 items that are designed but not implemented. These should be surfaced as work when the issue backlog is empty.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Work directly from GOALS.md without creating issues | Yes | Violates "every change needs an issue" constraint |
| Add all GOALS.md items as issues upfront | Yes | Creates stale issues; better to create on demand |
| Add a fallback step in startup.md | Yes | Selected — preserves existing flow, adds minimal complexity |

## 3. Scope

### Files to Create

None.

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Modify Step 8 to include Goals fallback logic when no actionable issues remain |
| `GOALS.md` | Update to reflect completed issues #36, #49; add #48 and #50 to completed when done |

### Files to Delete

None.

## 4. Approach

1. Modify Step 8 in startup.md to include Goals fallback logic that scans GOALS.md for unchecked items
2. When found, create a GitHub issue from the GOALS.md item, then enter the normal startup sequence at Step 4
3. Update GOALS.md to reflect current completion status

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual review | startup.md | Verify the new step integrates cleanly with existing flow |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Goals items too vague for direct implementation | Medium | Low | Label as `refine` if unclear, same as for issues |

## 7. Dependencies

None.

## 8. Backward Compatibility

Additive only. Existing startup sequence unchanged; new step only activates when no issues are actionable.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| Code Review | Yes | Modifies governance prompt |
| AI Expert Review | No | Changes to startup prompt affect agent behavior |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Modify Step 8 to include Goals fallback | Keeps the step numbering clean while adding fallback logic |
