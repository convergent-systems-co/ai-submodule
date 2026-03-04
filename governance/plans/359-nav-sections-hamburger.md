# Fix: Grouped Expandable Nav Sections and Hamburger Positioning

**Author:** Team Lead (agentic)
**Date:** 2026-02-25
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/359
**Branch:** NETWORK_ID/fix/359/nav-sections-hamburger-position

---

## 1. Objective

Make navigation sections collapsed by default with expandable arrows, and position the hamburger menu icon at the far-left of the header with the logo to its right.

## 2. Scope

### Files to Modify

| File | Change |
|------|--------|
| `mkdocs.yml` | Remove `navigation.expand` feature (sections collapse by default) |
| `docs/stylesheets/extra.css` | Add CSS to position hamburger far-left, logo to its right |

## 3. Approach

1. Remove `navigation.expand` from mkdocs.yml features — this makes sections show with `>` arrows that expand on click
2. Keep `navigation.sections` — renders top-level items as bold section headers
3. Add CSS to enforce hamburger → logo ordering in the header via flexbox `order` properties
4. Ensure the hamburger button has no left padding/margin gap

## 4. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking mobile nav | Low | Material theme handles mobile natively |
| Sections too deeply nested | Low | Current nav is max 2 levels deep |
