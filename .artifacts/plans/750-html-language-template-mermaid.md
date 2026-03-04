# Add HTML Language Template with Mermaid.js

**Author:** Claude (PM Agent)
**Date:** 2026-03-03
**Status:** draft
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/750
**Branch:** itsfwcp/feat/750/html-language-template-mermaid

---

## 1. Objective

Add Mermaid.js as the standard diagramming solution for the HTML language template. This involves updating the existing `governance/templates/languages/html/project.yaml` with Mermaid conventions, creating a missing `instructions.md` for the HTML template, updating the Document Writer persona to prefer Mermaid fenced blocks over static images, and adding Mermaid references to the Markdown-JSON template instructions.

## 2. Rationale

Mermaid.js renders diagrams from plain-text definitions embedded in Markdown or HTML. This eliminates binary image artifacts (PNGs, SVGs exported from draw.io or Lucidchart) from version control, keeps diagrams in sync with code changes, and requires no external tooling. GitHub natively renders ` ```mermaid ` blocks in Markdown, and standalone HTML pages can include Mermaid via a single CDN script tag.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Static images (PNG/SVG) committed to repo | Yes | Binary files bloat git history, drift from code, require external tools to edit |
| draw.io / Lucidchart exports | Yes | External tool dependency, binary artifacts, no inline rendering |
| PlantUML | Yes | Requires Java runtime or server; Mermaid is JavaScript-native and GitHub-supported |
| D2 (Terrastruct) | Yes | Smaller ecosystem; not natively supported in GitHub Markdown |
| Mermaid.js via CDN in HTML + fenced blocks in Markdown | Yes | **Selected** -- zero dependencies, version-controllable text, GitHub-native rendering |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/templates/languages/html/instructions.md` | HTML + Mermaid usage guide with conventions, examples, and accessibility guidance |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/templates/languages/html/project.yaml` | Add Mermaid conventions (`diagrams: mermaid`, `mermaid_version`, `mermaid_auto_include`), add `linter: htmlhint`, change `indent_size` from 4 to 2 to match issue spec, add `doctype: html5` |
| `governance/personas/agentic/document-writer.md` | Add instruction to always use Mermaid fenced blocks for diagrams; never generate image placeholders or static image links |
| `governance/templates/languages/markdown-json/instructions.md` | Add a "Diagrams" section referencing Mermaid as the standard for diagrams in Markdown content |

### Files to Delete

N/A

## 4. Approach

### Step 1: Update `governance/templates/languages/html/project.yaml`

The existing file defines an HTML reporting template with basic style and architecture conventions. Modifications:

- Add `diagrams: "mermaid"` under `conventions.architecture`
- Add `mermaid_version: "latest"` (with comment noting pin option)
- Add `mermaid_auto_include: true` to signal that HTML boilerplate includes Mermaid CDN
- Add `linter: "htmlhint"` under `conventions.style`
- Add `doctype: "html5"` under `conventions.style`
- Update `indent_size` from 4 to 2 per issue specification
- Add Mermaid-specific instructions to the inline `instructions` block

Preserve the existing structure (personas, panels, repository, governance sections) to maintain consistency with other language templates (Python, Go, React, C#).

### Step 2: Create `governance/templates/languages/html/instructions.md`

Follow the established pattern from `python/instructions.md`, `go/instructions.md`, and `react/instructions.md`:

- Opening line: "Extends the base AI instructions with HTML-specific conventions."
- Sections covering: HTML5 structure, semantic markup, Mermaid.js usage (CDN inclusion, fenced block syntax, supported diagram types with examples), integration with docs frameworks (MkDocs, Docusaurus), accessibility for diagrams, common pitfalls
- Closing line: "Extends .ai/instructions.md with HTML-specific conventions."

The Mermaid section should include:
- CDN script tag: `<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>`
- Initialization call: `mermaid.initialize({ startOnLoad: true })`
- Fenced block syntax for Markdown contexts
- Supported diagram types: flowchart, sequence, class, state, ER, gantt, pie, git graph, mindmap, timeline
- Accessibility: `aria-label` on diagram containers, `<div class="mermaid" role="img" aria-label="...">`

### Step 3: Update Document Writer persona

Add a new subsection under the "Principles" or "Guardrails" section of `governance/personas/agentic/document-writer.md`:

- When generating diagrams in documentation, always use Mermaid fenced blocks (` ```mermaid `)
- Never generate `![image](path)` links for architecture, flow, sequence, or ER diagrams
- For HTML output, include the Mermaid CDN script and use `<div class="mermaid">` containers
- Reference the HTML template conventions for CDN version and initialization

This change is additive -- it adds a constraint to the persona without modifying existing behavior.

### Step 4: Update Markdown-JSON template instructions

Add a "Diagrams" section to `governance/templates/languages/markdown-json/instructions.md` (before the "Common Pitfalls" section):

- All diagrams in Markdown files must use ` ```mermaid ` fenced blocks
- Supported diagram types and when to use each
- For docs sites (MkDocs), configure `pymdownx.superfences` with a custom Mermaid fence
- Reference `governance/templates/languages/html/instructions.md` for standalone HTML diagram usage

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | `project.yaml` | Verify updated HTML `project.yaml` parses as valid YAML and follows the established template structure |
| Content verification | `instructions.md` | Confirm the Mermaid CDN URL is valid and returns a 200 status |
| Cross-reference check | Document Writer persona | Verify the added Mermaid guidance does not conflict with existing persona guardrails |
| Staleness check | All modified docs | Run `bin/check-doc-staleness.py` to confirm no new staleness introduced |
| Template consistency | All language templates | Verify HTML template follows the same structural pattern as Python, Go, React, and C# templates |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Mermaid CDN URL changes or becomes unavailable | Low | Medium | Use jsDelivr CDN (highly reliable); document version pinning option in instructions |
| Document Writer persona change causes unintended behavior | Low | Low | Change is additive (new constraint); does not remove existing behavior |
| `indent_size` change from 4 to 2 breaks existing consuming repos | Low | Low | Templates are copied, not linked -- existing repos are unaffected; only new scaffolds use the updated value |
| Mermaid rendering inconsistencies across browsers | Low | Low | Mermaid is widely tested; document known limitations in instructions |

## 7. Dependencies

- None blocking. All changes are to template and persona files within the governance submodule.
- Mermaid.js is loaded via CDN at runtime in consuming repos -- no build-time dependency.

## 8. Backward Compatibility

Fully backward compatible. All changes are additive:

- The `project.yaml` update adds new keys (`diagrams`, `mermaid_version`, `mermaid_auto_include`, `linter`, `doctype`) without removing existing ones. The `indent_size` change from 4 to 2 affects only newly scaffolded projects; existing consumers who copied the template retain their local copy.
- The new `instructions.md` file fills a gap -- the HTML template is the only language template missing an instructions file.
- Document Writer persona changes add a new guideline; they do not alter existing guardrails, containment policies, or output formats.
- Markdown-JSON instructions gain a new section; existing sections are unchanged.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Template structure changes and new file |
| security-review | Yes | CDN script inclusion requires SRI/CSP review |
| documentation-review | Yes | Persona and instructions changes affect documentation pipeline |
| threat-modeling | Yes | External CDN dependency in HTML boilerplate |
| cost-analysis | Yes | Required by default policy (zero cost impact expected) |
| data-governance-review | Yes | Required by default policy (no data impact) |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| | | |
