# Panels and Plans Directories in Subprojects

**Author:** Code Manager (agentic)
**Date:** 2026-02-23
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/110
**Branch:** itsfwcp/feat/110/panels-in-subprojects

---

## 1. Objective

Ensure that consuming repos (subprojects) have `.plans/` and `.panels/` directories created during `init.sh` bootstrap. Plans and panel reports are stored in the project repo (not the submodule), with `.panels/` keeping only the latest panel output per panel type.

## 2. Rationale

Currently, `init.sh` creates symlinks and configures repository settings, but does not create the `.plans/` or `.panels/` directories that the agentic workflow expects. Plans are already written to `.plans/` by convention, but the directory isn't bootstrapped for new consuming repos. Panel reports have no standard storage location in consuming repos.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Store in submodule | Yes | Issue explicitly requires storage in project repo, not submodule |
| Accumulate all panel reports | Yes | Issue specifies "only the latest" — overwrite strategy is simpler and avoids repo bloat |
| Config-driven directory names | Yes | Over-engineering for current scope; `.plans/` and `.panels/` are sufficient conventions |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | Directories are created by init.sh, not as files in this repo |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `init.sh` | Add directory creation for `.plans/` and `.panels/` with `.gitkeep` files in consuming repos (submodule context only) |
| `config.yaml` | Add `directories` configuration section listing directories to create in consuming repos |
| `governance/docs/repository-configuration.md` | Document the new directories and their purpose |
| `CLAUDE.md` (root `.ai/`) | Update architecture section to mention `.plans/` and `.panels/` in consuming repos |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. Add a `directories` section to `config.yaml` listing `.plans/` and `.panels/` as directories to create in consuming repos
2. Add a `create_project_directories()` function in `init.sh` that reads the directory list and creates them with `.gitkeep` files (only in submodule context)
3. Update `governance/docs/repository-configuration.md` to document the directories
4. Update `CLAUDE.md` to reference the new convention

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | init.sh | Run init.sh in a test context and verify directories are created |

This is a configuration-only repo with no test runner.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| init.sh creates dirs in wrong location | Low | Low | Use existing `$PROJECT_ROOT` variable, guard with submodule context check |
| Existing consuming repos already have .plans/ | Low | None | init.sh checks before creating, idempotent behavior |

## 7. Dependencies

- None — no blocking dependencies

## 8. Backward Compatibility

Fully backward compatible. New directories are only created if missing. Existing repos with `.plans/` already present are unaffected.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Shell script changes |
| documentation-review | Yes | Doc updates |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Use `.gitkeep` files | Ensures empty directories are tracked by git |
| 2026-02-23 | Config-driven directory list | Allows consuming repos to customize via project.yaml |
| 2026-02-23 | Only create in submodule context | Prevents accidental creation when running init.sh in the ai-submodule repo itself |
