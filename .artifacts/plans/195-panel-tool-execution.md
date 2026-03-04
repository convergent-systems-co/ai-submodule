# Panel Tool Execution Capabilities

**Author:** Team Lead (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/195
**Branch:** NETWORK_ID/feat/195/panel-tool-execution

---

## 1. Objective

Add tool execution capabilities to panel definitions so panels can explore code, read files, and run analysis when invoked by an AI agent — moving panels from pure reasoning to evidence-based review.

## 2. Rationale

Panels currently contain zero tool access — they're reasoning-only templates. This means AI agents executing panels can't actually read the code they're reviewing, search for patterns, or run analysis tools. Adding tool access per panel enables evidence-based review.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Global tool access for all panels | Yes | Over-permissive; security-review doesn't need write access |
| Per-panel tool definitions in YAML config | Yes | Adds a new config file; simpler to embed in panel markdown |
| Per-panel tool section in panel markdown (chosen) | Yes | Keeps tool access co-located with the panel definition; easy to audit |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/panels.schema.json` | Add `allowed_tools` field to panel configuration schema |
| `governance/schemas/panels.defaults.json` | Add default tool access per panel |
| `governance/personas/panels/*.md` | Add Tools section to each panel definition |

## 4. Approach

1. Define tool access tiers (read-only, read+analyze, full)
2. Add `allowed_tools` to panel schema
3. Add default tool access to `panels.defaults.json`
4. Update panel markdown files with a ## Tools section
5. Update documentation

## 5-10. Low risk, no breaking changes, additive only.
