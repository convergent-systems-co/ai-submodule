# Fix Prompt Catalog Generator Pattern Mismatch

**Author:** Project Manager (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #11
**Branch:** itsfwcp/fix/11/prompt-catalog-generator

---

## 1. Objective

Ensure the prompt catalog generator discovers all prompt files and produces an accurate catalog. Verify the CI workflow produces a non-empty catalog.

## 2. Rationale

The issue reports that `bin/generate-prompt-catalog.py` finds 0 prompts due to searching for `*.prompt.md` instead of `*.md`. Investigation shows the generator now uses `.rglob("*.md")` and produces 74 entries. However, the catalog may be stale and needs regeneration. Additionally, any newly added prompts (e.g., `devops-operations-loop.md`) must be captured.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Fix glob pattern | Yes | Pattern already corrected — generator uses `*.md` |
| Regenerate catalog only | Yes — chosen | Catalog may be stale; regeneration ensures accuracy |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files needed |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `catalog/prompt-catalog.json` | Regenerated with current prompt inventory |
| `bin/generate-prompt-catalog.py` | Fix any remaining issues if found during validation |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Run `python3 bin/generate-prompt-catalog.py --validate` to verify generator works
2. Compare catalog output against actual file inventory
3. If discrepancies exist, fix the generator and regenerate
4. If catalog is accurate, commit the regenerated catalog
5. Verify `.github/workflows/prompt-catalog.yml` references correct paths

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Integration | bin/generate-prompt-catalog.py | Run generator, verify non-zero prompt count |
| Validation | catalog/prompt-catalog.json | Validate against schema |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| False positives in catalog | Low | Low | Exclusion lists filter non-prompt .md files |
| Generator already fixed | High | Low | Verify and close if resolved |

## 7. Dependencies

- [ ] None — self-contained change

## 8. Backward Compatibility

No breaking changes. Catalog is regenerated output.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Python script changes |
| documentation-review | Yes | Catalog is documentation artifact |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Regenerate catalog rather than fix pattern | Pattern already uses *.md correctly |
