# docs: Fix documentation inconsistencies across CLAUDE.md, README.md, DEVELOPER_GUIDE.md

**Author:** Code Manager (agent)
**Date:** 2026-02-25
**Status:** approved
**Issue:** #261
**Branch:** itsfwcp/docs/261/documentation-fixes

---

## 1. Objective

Resolve persona count inconsistencies, fix duplicate governance/ entry in README, update CLAUDE.md to acknowledge pytest/tests/, and ensure consistent language across all documentation.

## 2. Rationale

Multiple docs disagree on persona counts (58 vs 62 vs 63), README lists governance/ twice, and CLAUDE.md says "no test runner" despite pytest running in CI with a tests/ directory.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Single canonical count | Yes | Selected — use "58 core + 5 agentic = 63 total" consistently |
| Remove persona counts from docs | Yes | Counts are useful for understanding scope |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `CLAUDE.md` | Fix persona count (58 → "58 core role definitions across 13 categories"), add IaC Engineer to agentic table, update "four personas" → "five personas", acknowledge pytest and tests/ |
| `README.md` | Fix persona count to 63 (including 5 agentic), remove duplicate governance/ entry, add tests/ to repo structure |
| `DEVELOPER_GUIDE.md` | Fix persona count, add IaC Engineer to agentic list |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. **CLAUDE.md** line 55: Update "58 role definitions" to clarify "58 core role definitions across 13 categories" (deprecated personas)
2. **CLAUDE.md** line ~57-62: Verify IaC Engineer is in agentic personas list (it is)
3. **CLAUDE.md** line 108: Change "chains four personas" → "chains five personas" to include IaC Engineer
4. **CLAUDE.md** line 13: Update "no test runner" claim to mention pytest for policy engine tests
5. **README.md** line 377: Update persona count to "63 personas (including 5 agentic)" and list all 5
6. **README.md**: Remove duplicate governance/ in repo structure or consolidate
7. **README.md**: Add `tests/` to repo structure section
8. **DEVELOPER_GUIDE.md** line 201: Update to "63 personas (including 5 agentic: DevOps Engineer, Code Manager, Coder, IaC Engineer, Tester)"

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Documentation review | Verify consistency across all modified files |
| N/A | No automated tests | Documentation-only change |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Incorrect count | Low | Low | Verify by counting files in governance/personas/ |

## 7. Dependencies

- None

## 8. Backward Compatibility

Documentation-only changes. No behavioral impact.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Primary documentation change |
| security-review | Yes | Always required |
| cost-analysis | Yes | Always required |
| threat-modeling | Yes | Always required |
| data-governance-review | Yes | Always required |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Use "58 core + 5 agentic" formula | Accurate and accounts for deprecated status of core personas |
