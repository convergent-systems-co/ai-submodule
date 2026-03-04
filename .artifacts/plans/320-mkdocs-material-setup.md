# MkDocs Material Dark Theme with Mermaid Support

**Author:** Coder (agent)
**Date:** 2026-02-25
**Status:** completed
**Issue:** #320
**Branch:** NETWORK_ID/feat/320/mkdocs-material-setup

---

## 1. Objective

Replace raw markdown GitHub Pages deployment with a proper MkDocs Material site featuring dark theme, Mermaid diagram rendering, and a project logo.

## 2. Rationale

MkDocs Material provides a polished documentation experience with built-in dark theme, Mermaid support via pymdownx.superfences, navigation tabs, search, and code copy. This is the standard tooling for project documentation sites.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Raw GitHub Pages markdown | Yes | No theming, no Mermaid rendering, no navigation structure |
| Docusaurus | Yes | Heavier dependency (Node.js), overkill for config/docs-only repo |
| Sphinx | Yes | Python-native but worse markdown support, less modern UI |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `mkdocs.yml` | MkDocs configuration with Material dark theme, Mermaid, nav structure |
| `docs/index.md` | Landing page for the documentation site |
| `docs/assets/logo.svg` | SVG logo (shield + gear, purple/cyan) |
| `docs/stylesheets/extra.css` | Custom dark theme CSS overrides |
| `.github/workflows/deploy-docs.yml` | GitHub Actions workflow for building and deploying to Pages |
| `.plans/320-mkdocs-material-setup.md` | This plan |

### Files to Modify

| File | Change Description |
|------|-------------------|
| None | All existing docs are compatible as-is |

### Files to Delete

| File | Reason |
|------|--------|
| None | N/A |

## 4. Approach

1. Verify all docs referenced in nav structure exist in `docs/`
2. Create `mkdocs.yml` with Material theme (slate scheme), Mermaid fence config, and full nav
3. Create `docs/index.md` landing page based on existing `docs/README.md` content
4. Create SVG logo at `docs/assets/logo.svg`
5. Create custom CSS at `docs/stylesheets/extra.css`
6. Create GitHub Actions deploy workflow at `.github/workflows/deploy-docs.yml`

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Nav structure | Verified all nav entries map to existing files |
| CI | Build | `mkdocs build --strict` in workflow catches broken links/config |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Broken internal links | Low | Low | `--strict` flag catches missing files at build time |
| Mermaid diagrams not rendering | Low | Low | Built-in Material support; no extra plugin needed |

## 7. Dependencies

- [x] mkdocs-material pip package (installed in CI)
- [x] pymdown-extensions pip package (installed in CI)
- [x] GitHub Pages enabled on the repository

## 8. Backward Compatibility

Fully additive. Existing markdown files are unchanged. The `docs/README.md` continues to work for GitHub browsing; `docs/index.md` is the MkDocs landing page.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | New documentation infrastructure |
| security-review | Yes | New GitHub Actions workflow |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Used `assets/logo.svg` (relative to docs/) for theme logo path | MkDocs Material resolves logo relative to docs_dir, not repo root |
