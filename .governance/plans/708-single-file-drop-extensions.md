# Match DACH Extensibility with Single-File-Drop for All Extension Types

**Author:** Team Lead (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/708
**Branch:** itsfwcp/feat/708/single-file-drop-extensions

---

## 1. Objective

Achieve extensibility score 5/5 by enabling true single-file-drop extensibility for custom phases, panels, and hooks. Users should be able to add an extension by dropping a file into a convention directory — no configuration changes required. Auto-generate an extension catalog for discoverability.

## 2. Rationale

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep extension config in project.yaml (#611) | Yes | Requires config editing — not a true file-drop experience |
| Convention-only (auto-discover all) | Yes | Selected — matches DACH's model; most frictionless |
| Hybrid: convention + optional config override | Yes | Adds complexity without clear benefit over pure convention |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/engine/orchestrator/extension_discovery.py` | Auto-discover extensions from convention directories |
| `governance/engine/tests/test_extension_discovery.py` | Tests for extension discovery |
| `governance/schemas/extension-catalog.schema.json` | JSON Schema for the auto-generated catalog |
| `docs/guides/extension-authoring.md` | Guide for authoring custom extensions |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/engine/orchestrator/config.py` | Add `extensions_dirs` config with convention directory paths |
| `governance/engine/orchestrator/step_runner.py` | Call extension discovery at init; execute discovered hooks/phases |

### Files to Delete

None.

## 4. Approach

1. **Define convention directories** — extensions live in the consuming repo under `.governance/extensions/`:
   - `.governance/extensions/panels/` — custom review panel prompts (`.md` files)
   - `.governance/extensions/phases/` — custom orchestrator phase scripts (`.sh` or `.py`)
   - `.governance/extensions/hooks/pre_dispatch/` — hooks run before Coder dispatch
   - `.governance/extensions/hooks/post_merge/` — hooks run after PR merge
   - `.governance/extensions/hooks/post_review/` — hooks run after panel reviews

2. **Create `extension_discovery.py`**:
   - `discover_extensions(base_dir)` — scans convention directories, returns `DiscoveredExtensions` dataclass
   - `discover_panels(panels_dir)` — finds `.md` files, parses frontmatter for name/description
   - `discover_phases(phases_dir)` — finds `.sh`/`.py` files, parses shebang/docstring for metadata
   - `discover_hooks(hooks_dir)` — finds executable files in hook subdirectories
   - `generate_catalog(extensions)` — produces `catalog.json` with all discovered extensions
   - Each discovery function validates the extension file format (frontmatter for panels, shebang for scripts)

3. **Integrate into step_runner.py**:
   - At session init, call `discover_extensions()` to build the extension registry
   - Merge discovered panels with built-in panels (discovered panels do not replace built-in required panels)
   - Execute phase scripts at appropriate orchestrator phases
   - Execute hooks at lifecycle transition points

4. **Auto-generate catalog** — `catalog.json` is written to `.governance/extensions/catalog.json` whenever discovery runs, listing all available extensions with metadata

5. **Write extension authoring documentation** explaining the convention directories, file formats, and frontmatter schema

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `extension_discovery.py` | Test discovery with mock directories containing various extension files |
| Unit | Panel discovery | Test frontmatter parsing, validation of panel format |
| Unit | Phase discovery | Test script detection, metadata extraction |
| Unit | Hook discovery | Test hook directory scanning, executable validation |
| Unit | Catalog generation | Test catalog.json output matches schema |
| Integration | step_runner | Test discovered extensions are loaded and available at runtime |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Malicious extension in convention dir | Med | High | Extensions run within agent containment; document security model |
| Extension conflicts with built-in panels | Low | Med | Built-in required panels cannot be overridden; discovered panels are additive |
| Performance impact of scanning at init | Low | Low | Convention dirs are small; scanning is fast |

## 7. Dependencies

- [ ] #611 (plugin architecture) — non-blocking. #611 provides project.yaml-declared extensions; this issue adds convention-based auto-discovery as a complementary mechanism. Both can coexist.

## 8. Backward Compatibility

Fully backward compatible. Convention directories do not exist by default in consuming repos. When absent, discovery returns empty results and the orchestrator behaves identically to current behavior. Extensions from #611's project.yaml config continue to work.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New engine module |
| security-review | Yes | Extension execution model |
| architecture-review | Yes | New extensibility pattern |
| documentation-review | Yes | Extension authoring guide |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Convention-based discovery, not config-based | Matches DACH's single-file-drop model; zero config changes |
| 2026-03-02 | Discovered panels are additive, not replacements | Built-in required panels must always run for governance compliance |
| 2026-03-02 | Catalog is auto-generated, not manually maintained | Removes maintenance burden; always accurate |
