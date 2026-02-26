# Move .plans/ and .checkpoints/ Under governance/

**Author:** Coder (agent)
**Date:** 2026-02-25
**Status:** in_progress
**Issue:** #316
**Branch:** itsfwcp/refactor/316/move-plans-checkpoints

---

## 1. Objective

Move `.plans/` and `.checkpoints/` directories from the project root to `governance/plans/` and `governance/checkpoints/`, consolidating governance artifacts under the `governance/` namespace.

## 2. Rationale

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep at root as hidden dirs | Yes | Clutters root namespace; inconsistent with governance artifact location |
| Move under `.workspace/` | Yes | Adds a new top-level directory; governance/ already exists |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| All files referencing `.plans/` or `.checkpoints/` | Update paths to `governance/plans/` and `governance/checkpoints/` |
| `config.yaml` | Update project_directories paths |
| `bin/init.sh` | Update directory creation paths |

## 4. Approach

1. Create `governance/plans/` and `governance/checkpoints/`
2. `git mv` all tracked files from `.plans/` and `.checkpoints/`
3. Update every reference across the codebase
4. Verify no old references remain

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Grep verification | All file types | Confirm no `.plans/` or `.checkpoints/` references remain |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Consuming repos break on update | Medium | Medium | init.sh creates new paths; old paths left as-is in consuming repos |
| Missed reference | Low | Low | Comprehensive grep-based search |

## 7. Dependencies

- None

## 8. Backward Compatibility

This changes paths that consuming repos reference. The `init.sh` script will create the new directory paths on next run. Consuming repos with existing `.plans/` directories will need to migrate manually or on next submodule update.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Many documentation files are affected |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Move to governance/ prefix (not .governance/) | Consistency with existing governance/ directory structure |
