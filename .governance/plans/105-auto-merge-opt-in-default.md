# Plan: Change auto_merge Default to Opt-In (false)

**Author:** Claude Code (Coder persona)
**Date:** 2026-02-23
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/105
**Branch:** itsfwcp/feat/105/auto-merge-opt-in-default

---

## 1. Objective

Change the `auto_merge` default in `config.yaml` from `true` to `false` so consuming repos must explicitly opt in to auto-merge. This is a safety measure — auto-merge should be a conscious choice by a repo admin, not silently enabled during bootstrap.

## 2. Rationale

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep default as `true` | Yes | Issue #105 explicitly requires `false` as default; safety concern for onboarding repos |
| **Change default to `false`** | **Selected** | Matches issue requirements; aligns with principle of least surprise |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `config.yaml` | Change `auto_merge: true` to `auto_merge: false` |
| `governance/schemas/project.schema.json` | Change default for `auto_merge` from `true` to `false` |
| `governance/docs/repository-configuration.md` | Update documentation to reflect opt-in default |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. Change `auto_merge` default in config.yaml from `true` to `false`
2. Update project.schema.json default value
3. Update repository-configuration.md docs to note auto_merge is opt-in

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | config.yaml | Verify default is false |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Existing repos lose auto-merge | Low | Low | Config change only affects new init runs; existing repo settings are unaffected |

## 7. Dependencies

- [x] Repository configuration feature already implemented (PR #104)

## 8. Backward Compatibility

Fully backward compatible. Only changes the default; existing repos with explicit `auto_merge: true` in their project.yaml are unaffected.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Docs update |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Change default only, no structural changes | Feature already exists; this is a policy default adjustment |
