# Fix Mermaid Diagram Rendering on GitHub Pages

**Author:** Code Manager (agentic)
**Date:** 2026-02-25
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/331
**Branch:** itsfwcp/fix/331/mermaid-rendering

---

## 1. Objective

Fix Mermaid diagrams rendering as raw text on the GitHub Pages site by switching to the correct superfences format handler that enables MkDocs Material's built-in client-side Mermaid rendering.

## 2. Rationale

MkDocs Material has built-in Mermaid.js support. When `fence_mermaid_format` is used, it generates `<pre class="mermaid">` HTML elements. The Material theme's JavaScript detects these elements and invokes Mermaid.js to render them as SVG in the browser — real-time, client-side rendering.

The current config uses `fence_code_format`, which generates standard `<code>` blocks — displaying Mermaid syntax as plain text.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Pre-build SVGs at build time | Yes | User prefers real-time rendering; adds build complexity |
| Add Mermaid JS via extra_javascript | Yes | Material theme handles this automatically with fence_mermaid_format |
| Change markdown fencing syntax | Yes | User explicitly requested no markdown changes |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | N/A |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `mkdocs.yml` | Change `fence_code_format` → `fence_mermaid_format` on line 32 |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | N/A |

## 4. Approach

1. Change the superfences custom fence format from `fence_code_format` to `fence_mermaid_format`
2. No other changes needed — Material theme auto-loads Mermaid.js when it detects the correct HTML output

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Build | MkDocs | `mkdocs build --strict` passes |
| Visual | Site | Diagrams render as graphics after deployment |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Other code blocks affected | None | N/A | Only Mermaid-named fences use this handler |

## 7. Dependencies

- [x] mkdocs-material package (already installed in deploy workflow)

## 8. Backward Compatibility

No breaking changes. Markdown files unchanged. Only the HTML output format changes from `<code>` to `<pre class="mermaid">`.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Always required |
| documentation-review | Yes | Docs config change |
| threat-modeling | Yes | Always required |
| cost-analysis | Yes | Always required |
| data-governance-review | Yes | Always required |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Use fence_mermaid_format (client-side) over pre-built SVGs | User preference for real-time rendering; simpler, no build deps |
