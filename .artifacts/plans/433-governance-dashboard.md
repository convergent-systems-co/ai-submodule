# Add Interactive Governance Dashboard and Prompt Catalog on GitHub Pages

**Author:** Team Lead (agent)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/433
**Branch:** NETWORK_ID/feat/433/governance-dashboard

---

## 1. Objective

Create a searchable governance dashboard on GitHub Pages showing panel catalog, policy profile comparison, and prompt index.

## 2. Rationale

The existing MkDocs site documents governance but lacks interactive components. An interactive dashboard improves discoverability and adoption.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Extend MkDocs with plugins | Yes | Limited interactive table support |
| Standalone React app | Yes | Over-engineered for static catalog |
| Auto-generated markdown only | Yes | Not searchable or interactive |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `docs/reference/panel-catalog.md` | Auto-generated panel table |
| `docs/reference/policy-comparison.md` | Side-by-side policy profile comparison |
| `docs/reference/prompt-index.md` | Searchable index of all review panels and workflow templates |
| `governance/bin/generate-catalog.py` | Script to auto-generate catalog pages |
| `.github/workflows/publish-dashboard.yml` | GitHub Actions workflow to auto-update Pages |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `mkdocs.yml` | Add reference section with new pages |
| `GOALS.md` | Mark dashboard as completed |

### Files to Delete

None.

## 4. Approach

1. Create `governance/bin/generate-catalog.py` that scans panels, policies, prompts
2. Create `docs/reference/panel-catalog.md` with panel metadata table
3. Create `docs/reference/policy-comparison.md` with profile comparison
4. Create `docs/reference/prompt-index.md` with filterable catalog
5. Add MkDocs nav entries
6. Create `.github/workflows/publish-dashboard.yml`
7. Update GOALS.md

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | generate-catalog.py | Test produces valid markdown |
| Manual | Generated pages | Verify output matches source data |
| CI | Workflow | Verify Pages deployment succeeds |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MkDocs build breakage | Low | Medium | Test build locally first |
| Stale catalog data | Medium | Low | Auto-generation in CI |

## 7. Dependencies

- [ ] MkDocs configuration (exists)
- [ ] GitHub Pages (existing setup)

## 8. Backward Compatibility

Fully additive. No existing content modified.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Primary documentation change |
| code-review | Yes | New Python script |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Auto-generated markdown | Integrates with existing MkDocs |
| 2026-02-27 | Single generate-catalog.py | All catalog pages from same sources |
