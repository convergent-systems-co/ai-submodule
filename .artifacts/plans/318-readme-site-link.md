# Add Documentation Site Link to README

**Author:** Coder (agentic)
**Date:** 2026-02-25
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/318
**Branch:** NETWORK_ID/docs/318/readme-site-link

---

## 1. Objective

Add a prominent link to the documentation site (https://probable-adventure-7e9l4jw.pages.github.io/) near the top of README.md so that users can quickly find the full documentation.

## 2. Rationale

The documentation site exists but is not referenced from the README. Users arriving at the repository need a clear path to the hosted documentation.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add link in Documentation Index section only | Yes | Not prominent enough — users may not scroll that far |
| Add link near top as a blockquote callout | Yes | Selected — visible immediately, consistent with existing "New here?" callout style |
| Add a badge/shield | Yes | Less consistent with existing README style |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.plans/318-readme-site-link.md` | This plan file |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `README.md` | Add documentation site link as a blockquote callout after the opening description paragraph |

### Files to Delete

N/A — no files are deleted.

## 4. Approach

1. Read README.md to identify the best insertion point
2. Insert a blockquote link after the opening description, before the "New here?" callout
3. Commit with conventional commit format

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | README.md | Verify the link renders correctly in GitHub Markdown preview |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Broken URL | Low | Low | URL verified before insertion |
| Merge conflict | Low | Low | Change is additive, single-line insertion |

## 7. Dependencies

N/A — no blocking dependencies.

## 8. Backward Compatibility

Fully backward compatible. This is an additive documentation change only.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Documentation change |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Place link as blockquote before "New here?" callout | Matches existing README style, maximally visible |
