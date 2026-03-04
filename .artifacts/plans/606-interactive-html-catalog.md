# Interactive HTML Prompt Catalog

**Author:** Team Lead (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/606
**Branch:** itsfwcp/feat/606/interactive-html-catalog

---

## 1. Objective

Create an interactive, self-contained HTML catalog page for the governance prompt library (21 review panels + 12 developer prompts) with search, filtering, and version tracking. Deploy via GitHub Pages.

## 2. Rationale

Platform evaluation scored AI-Submodule at 3/5 for Developer Experience, with a key gap being discoverability. DACH has an interactive HTML catalog with search and filtering for 72 prompts. AI-Submodule's 33 prompts have no browsable catalog.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| MkDocs Material catalog page | Yes | Requires MkDocs build pipeline; HTML catalog is self-contained |
| JSON API + SPA | Yes | Over-engineered; single HTML file is simpler to deploy |
| Self-contained HTML with embedded data | Yes | **Selected** — zero dependencies, deploys anywhere |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `bin/generate-html-catalog.py` | Python script that reads all prompts and generates self-contained HTML catalog |
| `.github/workflows/generate-catalog.yml` | CI workflow to regenerate catalog on prompt changes and deploy to GitHub Pages |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `catalog.json` | Enrich with perspectives, categories, pass/fail criteria, content hashes for each prompt |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | |

## 4. Approach

1. Create `bin/generate-html-catalog.py` that:
   - Reads all `.md` files from `governance/prompts/reviews/` and `prompts/global/`
   - Extracts metadata: name, type (review/developer/operational), perspectives used, confidence scoring, pass/fail criteria
   - Generates content hashes (SHA-256) for version tracking
   - Outputs a self-contained HTML file with embedded CSS (Nord theme) and JavaScript
   - Includes search by name/category/tags, filter by panel type, and detail view
2. Enrich `catalog.json` with structured metadata for each prompt (perspectives, categories, scoring criteria).
3. Create `.github/workflows/generate-catalog.yml` that:
   - Triggers on changes to `governance/prompts/reviews/**` and `prompts/global/**`
   - Runs `generate-html-catalog.py`
   - Deploys output to GitHub Pages
4. Validate catalog schema in CI to ensure all prompts are represented.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `generate-html-catalog.py` | Verify script produces valid HTML with all 33 prompts represented |
| Unit | `catalog.json` | Validate enriched catalog matches schema |
| Integration | CI workflow | Verify workflow triggers on prompt changes and produces artifact |
| E2E | GitHub Pages | Verify deployed page loads, search works, filters function |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| HTML generation fails on edge cases in prompt content | Medium | Low | Escape all content; test with actual prompts |
| GitHub Pages not enabled for repo | Low | Low | Document setup requirement; workflow handles deployment |
| Large HTML file size | Low | Low | Prompts are small; total HTML should be under 500KB |

## 7. Dependencies

- [ ] None blocking

## 8. Backward Compatibility

Purely additive. No existing files are modified in breaking ways. The catalog is a new artifact.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New Python script and CI workflow |
| documentation-review | Yes | Developer experience improvement |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Self-contained HTML over SPA | Zero dependencies, simpler deployment, matches DACH pattern |
| 2026-03-02 | Nord theme | Consistent with existing documentation styling |
