# Plan: Copy Governance Workflows to Consuming Repos

**Author:** Claude Code (Coder persona)
**Date:** 2026-02-23
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/107
**Branch:** itsfwcp/feat/107/copy-governance-workflows

---

## 1. Objective

Extend `init.sh` to copy governance workflows from `.ai/.github/workflows/` to the consuming repo's `.github/workflows/`, so consuming repos get the Dark Factory Governance review workflow that provides the approving review needed for branch protection rulesets.

## 2. Rationale

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Copy all workflows | Yes | Some workflows are ai-submodule-specific (propagate, plan-archival) |
| Hardcode governance workflow only | Yes | Not extensible; config.yaml pattern already exists |
| **Configurable list in config.yaml** | **Selected** | Consistent with existing config-as-code pattern; extensible |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `init.sh` | Add workflow copy section after issue template copy, using configurable list |
| `config.yaml` | Add `workflows` list under `symlinks` or as new top-level section specifying which workflows to copy |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. Add `workflows_to_copy` list to config.yaml with default of `dark-factory-governance.yml`
2. Add workflow copy block in init.sh after the issue template copy block, following the same skip-if-exists pattern
3. Only copy when in submodule context (same guard as issue templates)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | init.sh | Verify workflow copy in submodule context |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Consuming repo has customized governance workflow | Medium | Low | Skip-if-exists prevents overwrite |

## 7. Dependencies

- [x] init.sh infrastructure exists

## 8. Backward Compatibility

Fully backward compatible. New workflows are only copied in submodule context and only if the file doesn't already exist.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Bootstrap process change |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Only copy dark-factory-governance.yml by default | Other workflows are ai-submodule-specific |
| 2026-02-23 | Make list configurable in config.yaml | Extensibility without code changes |
| 2026-02-23 | Use symlinks instead of copies | Submodule updates flow automatically; init.sh never needs re-running. Consistent with CLAUDE.md symlink pattern. Regular files are not overwritten (skip with message). |
