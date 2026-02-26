# Fix Incorrect Persona and Panel Counts

**Author:** Code Manager (agentic)
**Date:** 2026-02-21
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/50
**Branch:** itsfwcp/fix/50/correct-persona-panel-counts

---

## 1. Objective

Correct hard-coded persona and panel counts across all documentation files to match actual filesystem counts.

## 2. Rationale

The documentation references 48 personas and 13 panels, but the actual counts are 42 non-agentic personas across 11 categories (44 including agentic) and 15 panels. This was discovered during the #36 retrospective.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Dynamic count generation | Yes | Config-only repo, no build system to generate counts |
| Remove counts entirely | Yes | Counts provide useful quick reference for readers |
| Update counts to match filesystem | Yes | Selected — simple, accurate, minimal risk |

## 3. Scope

### Files to Create

None.

### Files to Modify

| File | Change Description |
|------|-------------------|
| `CLAUDE.md` | Update persona count 48→42, categories 10→11, panel count 13→15 |
| `governance/docs/dark-factory-governance-model.md` | Update persona count 48→42, categories 8→11, add missing categories to table |

### Files to Delete

None.

## 4. Approach

1. Update CLAUDE.md line 49: "48 role definitions across 10 categories" → "42 role definitions across 11 categories"
2. Update CLAUDE.md line 50: "13 multi-persona review workflows" → "15 multi-persona review workflows"
3. Update governance model doc line 97: "48 across 8 categories" → "42 across 11 categories"
4. Add missing categories (documentation, finops, governance) to the governance model table and fix incorrect counts (compliance 3→4, leadership 4→5)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual verification | All modified files | Grep for old counts to ensure none remain |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Missing a file with old counts | Low | Low | Grep-based verification |

## 7. Dependencies

None.

## 8. Backward Compatibility

No breaking changes. Documentation-only update.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Documentation change |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Use 42 (non-agentic) in Personas bullet since agentic has its own bullet | Avoids double-counting with the separate "Agentic personas" line |
| 2026-02-21 | Update governance model doc table to include all 11 categories | Table was missing documentation, finops, governance categories |
