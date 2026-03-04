# Prompt Catalog System with CI Auto-Generation

**Author:** Claude (Coder persona)
**Date:** 2026-02-27
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/470
**Branch:** NETWORK_ID/feat/470/prompt-catalog-system

---

## 1. Objective

Add a machine-readable prompt catalog system that automatically indexes all `*.prompt.md` files, produces a JSON catalog validated against a schema, and regenerates on every push to main via CI. This enables downstream tooling (search, drift detection, analytics) to consume prompt metadata programmatically.

## 2. Rationale

The governance platform manages an expanding set of prompt files across directories. Without a structured catalog, prompt discovery requires manual file-system traversal. A JSON catalog with content hashes enables automated drift detection, search interfaces, and integration with the governance dashboard.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Extend existing generate-catalog.py | Yes | That script generates Markdown reference docs; a JSON catalog is a different artifact type with different consumers |
| YAML catalog instead of JSON | Yes | JSON aligns with existing schema validation tooling (panel-output.schema.json pattern) |
| No CI — manual generation only | Yes | Manual generation drifts; CI ensures catalog stays current with prompt changes |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/prompt-catalog.schema.json` | JSON Schema for catalog validation |
| `bin/generate-prompt-catalog.py` | CLI tool to scan prompts and produce catalog JSON |
| `.github/workflows/prompt-catalog.yml` | CI workflow to auto-regenerate on push |
| `catalog/.gitkeep` | Placeholder for the catalog output directory |

### Files to Modify

| File | Change Description |
|------|-------------------|
| N/A | No existing files modified |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files deleted |

## 4. Approach

1. Create the JSON schema defining the catalog structure (version, generated_at, prompt_count, prompts array with id/name/description/status/tags/model/file_path/content_hash/last_modified)
2. Create the catalog generator script that scans `prompts/` for `*.prompt.md` files, parses YAML frontmatter, computes SHA-256 hashes, resolves last-modified from git, and writes validated JSON
3. Create the CI workflow triggered on push to main (path filter: `prompts/**`) and workflow_dispatch
4. Create the `catalog/` directory with `.gitkeep`
5. Test the generator locally to verify correct output and schema validation

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Generator CLI | Run with --validate flag, verify JSON output structure |
| Manual | Empty directory | Verify 0-prompt catalog is valid against schema |
| Manual | Sample prompt | Create test *.prompt.md, verify all fields populated correctly |
| Manual | Custom paths | Verify --prompts-dir and --output flags work |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PyYAML not installed in CI | Low | Med | Script includes regex fallback; CI step explicitly installs pyyaml |
| No prompts/ directory yet (Issue #469) | High | Low | Generator handles missing directory gracefully (returns empty catalog) |
| Schema breaks downstream consumers | Low | Med | Schema uses semantic versioning; catalog version field enables migration |

## 7. Dependencies

- [ ] Issue #469 (prompts/global/ directory) — non-blocking; generator works with empty or missing directory

## 8. Backward Compatibility

Fully additive change. No existing files are modified. The catalog/ directory and schema are new artifacts. The CI workflow only triggers on prompts/** changes, which is a new path.

## 9. Governance

Expected panel reviews and policy profile:

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New Python script and JSON schema |
| security-review | Yes | CI workflow with write permissions |
| documentation-review | Yes | New tooling needs discoverable docs |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Use PyYAML with regex fallback | Robust parsing without hard dependency on external packages |
| 2026-02-27 | Schema allows null for model field | Not all prompts are model-specific; null represents model-agnostic |
| 2026-02-27 | Catalog version starts at 1.0.0 | Clean starting point; schema uses semver pattern for future evolution |
| 2026-02-27 | CI uses [skip ci] in commit message | Prevents infinite loop when catalog commit triggers workflow again |
