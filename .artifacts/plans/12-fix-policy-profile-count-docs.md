# Fix Policy Profile Count in Documentation

**Author:** Code Manager (Claude)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #12
**Branch:** itsfwcp/fix/12/policy-profile-count-docs

---

## 1. Objective

Ensure all documentation accurately reflects the 5 policy profiles and 18 supporting policy configurations in `governance/policy/`, and that `docs/reference/policy-comparison.md` includes the `fast-track` profile.

## 2. Rationale

CLAUDE.md already states "Five policy profiles and 18 supporting policy configurations" (correct). The issue title says "4 policy profiles" but CLAUDE.md was already updated. The real remaining gap is `docs/reference/policy-comparison.md` which only shows 4 profiles in its comparison table, omitting `fast-track.yaml`.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Regenerate via generate-catalog.py | Yes | Script may not exist or may need updating; manual fix is simpler and more reliable |
| Manual update of policy-comparison.md | Yes | Selected — straightforward and verifiable |

## 3. Scope

### Files to Create

None.

### Files to Modify

| File | Change Description |
|------|-------------------|
| `docs/reference/policy-comparison.md` | Add `fast-track` profile column to comparison table |

### Files to Delete

None.

## 4. Approach

1. Read `governance/policy/fast-track.yaml` to extract all comparable settings
2. Read `docs/reference/policy-comparison.md` to understand table structure
3. Add `fast-track` column to every row in the comparison table
4. Verify all 5 profiles are represented

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | docs/reference/policy-comparison.md | Verify table has all 5 profiles |
| Grep | All docs | Verify no remaining "four policy" references |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Incorrect fast-track values | Low | Low | Read actual YAML source |

## 7. Dependencies

None.

## 8. Backward Compatibility

Documentation-only change. No behavior impact.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Doc accuracy fix |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Focus on policy-comparison.md table | CLAUDE.md already correct; this is the remaining gap |
