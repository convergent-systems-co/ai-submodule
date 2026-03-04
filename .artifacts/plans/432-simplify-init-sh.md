# Simplify init.sh into Modular Scripts with One-Line Install

**Author:** Team Lead (agent)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/432
**Branch:** NETWORK_ID/feat/432/simplify-init-sh

---

## 1. Objective

Refactor the 1,113-line `bin/init.sh` into a thin orchestrator (< 200 lines) delegating to focused modular scripts, and add `bin/quick-install.sh`, `--dry-run`/`--debug` flags, and a troubleshooting guide.

## 2. Rationale

init.sh is the adoption entry point but at 1,113 lines creates a high barrier for understanding and debugging. Modularization improves maintainability and onboarding DX.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Rewrite in Python | Yes | Shell is appropriate for bootstrap; Python may not be available yet |
| Keep monolith with comments | Yes | Does not address maintainability |
| Package manager approach | Yes | Over-engineered |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/bin/lib/common.sh` | Shared functions (logging, config reading) |
| `governance/bin/check-python.sh` | Python version detection (~30 lines) |
| `governance/bin/update-submodule.sh` | Submodule freshness check (~50 lines) |
| `governance/bin/create-symlinks.sh` | Symlink creation (~40 lines) |
| `governance/bin/setup-workflows.sh` | Workflow symlink management (~50 lines) |
| `governance/bin/setup-codeowners.sh` | CODEOWNERS generation (~50 lines) |
| `governance/bin/setup-directories.sh` | Project directory creation with migration (~40 lines) |
| `governance/bin/validate-emissions.sh` | Panel emission validation (~40 lines) |
| `governance/bin/setup-repo-config.sh` | Repository settings via gh API (~80 lines) |
| `governance/bin/install-deps.sh` | Python venv + dependency installation (~40 lines) |
| `bin/quick-install.sh` | One-line curl-pipe-bash installer (~30 lines) |
| `docs/troubleshooting/init-failures.md` | Common failure resolutions |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `bin/init.sh` | Refactor to thin orchestrator (< 200 lines) |
| `CLAUDE.md` | Update init.sh documentation |
| `GOALS.md` | Mark simplification as completed |

### Files to Delete

None — init.sh is refactored, not deleted.

## 4. Approach

1. Extract each major section of init.sh into standalone scripts in `governance/bin/`
2. Create `governance/bin/lib/common.sh` for shared logging and config functions
3. Each modular script is independently executable with proper error handling
4. Refactor `bin/init.sh` to parse arguments and call modular scripts in order
5. Add `--dry-run` flag (preview actions without executing)
6. Add `--debug` flag (verbose logging)
7. Create `bin/quick-install.sh` for one-line adoption
8. Write `docs/troubleshooting/init-failures.md`
9. Verify all existing functionality is preserved

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | init.sh orchestrator | All modular scripts execute correctly |
| Manual | Individual scripts | Each governance/bin/*.sh works standalone |
| Manual | --dry-run | No side effects |
| Regression | Existing behavior | Compare output before/after |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing consumers | Medium | High | Preserve all existing flags and behaviors |
| Path resolution | Medium | Medium | Scripts resolve paths relative to own location |

## 7. Dependencies

- [ ] None — refactoring existing functionality

## 8. Backward Compatibility

Fully backward compatible. All existing flags preserved. Modular scripts are internal.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Major refactoring of critical bootstrap script |
| security-review | Yes | Shell scripts with system operations |
| documentation-review | Yes | New troubleshooting docs |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Shell over Python | Bootstrap must work before Python is installed |
| 2026-02-27 | governance/bin/ for modules, bin/ for entry points | Internal vs public API separation |
| 2026-02-27 | common.sh for shared functions | DRY logging and config parsing |
