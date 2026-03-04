# Fix Policy Profile Count Documentation

**Author:** Project Manager (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #12
**Branch:** itsfwcp/fix/12/policy-profile-count-docs

---

## 1. Objective

Correct documentation that misrepresents the number of policy profiles and supporting configurations. CLAUDE.md states "Five policy profiles and 18 supporting policy configurations" — the 5 profiles is correct, but "18 supporting" conflates 4 active configs with 14 future/Phase 5 configs.

## 2. Rationale

Accurate documentation prevents confusion when developers reference policy counts. The "18" number is misleading because 14 of those files are in `governance/policy/future/` and are not yet active.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Count all 23 as "policy files" | Yes | Conflates profiles, active config, and future config |
| Separate active vs future counts | Yes — chosen | Accurate and clear |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `CLAUDE.md` | Update "18 supporting policy configurations" to "4 supporting policy configurations (plus 14 Phase 5 future configurations)" |
| `docs/decisions/002-panel-based-review-system.md` | Fix "18 supporting" reference |
| Any other docs referencing "18 supporting" | Grep and fix all references |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Grep for "18 supporting" and "18 policy" across all docs
2. Update each reference to accurately distinguish active vs future
3. Verify 5 profiles, 4 active configs, 14 future configs

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Documentation files | Grep verification of no stale references |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Missing a reference | Low | Low | Comprehensive grep |
| Count changes again | Low | Low | Run bin/check-doc-staleness.py |

## 7. Dependencies

- [ ] None

## 8. Backward Compatibility

Documentation-only change. No code impact.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Documentation accuracy fix |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Distinguish active vs future configs | More accurate than lumping all together |
