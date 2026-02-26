# Cleanup Root — Reduce Submodule Filesystem Cruft

**Author:** Code Manager (agentic)
**Date:** 2026-02-25
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/222
**Branch:** `itsfwcp/feat/222/cleanup-root`

---

## 1. Objective

Reduce the root-level file count of the ai-submodule from 18 non-hidden items to 13 by consolidating scattered scripts, docs, and research artifacts into their natural parent directories. Eliminate two top-level directories (`scripts/`, `docs/`) and one orphaned research file.

## 2. Rationale

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Move init.sh/init.ps1 to bin/ | Yes | Breaks `bash .ai/init.sh` in every consuming repo, CLAUDE.md, README.md. A shim adds 2 files where there was 1 — anti-consolidation. |
| Move GOALS.md/DEVELOPER_GUIDE.md under governance/docs/ | Yes | These are high-discoverability items. Root placement is convention for project-level docs. Moving them loses discoverability for minimal gain. |
| Consolidate .checkpoints/.plans/.governance into .workspace/ | Yes | Changes config.yaml `project_directories`, breaks all startup.md references, breaks consuming repos on next submodule update. High risk, low reward. |
| Remove startup.md/init.md convenience files | Yes | PR #56 added them for discoverability. They're small pointer files (5 lines each). The discoverability value outweighs the clutter cost. |

**Chosen approach:** Move scattered content into existing directories. Create `bin/` for executables. Keep backward-compatible root entry points.

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `bin/issue-monitor.sh` | Moved from `scripts/issue-monitor.sh` |
| `bin/issue-monitor.ps1` | Moved from `scripts/issue-monitor.ps1` |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `README.md` | Update file structure tree, remove `scripts/` and `docs/` entries, add `bin/`, update TECHNIQUE_COMPARE.md path |
| `CLAUDE.md` | Update any references to moved files |
| `DEVELOPER_GUIDE.md` | Update references to scripts/, TECHNIQUE_COMPARE.md |
| `GOALS.md` | Update any references if present |
| `governance/docs/DECISIONS.md` | Update TECHNIQUE_COMPARE.md path in references |
| `governance/docs/RESEARCH.md` | Update TECHNIQUE_COMPARE.md path reference |
| `.github/workflows/issue-monitor.yml` | Update script path from `scripts/` to `bin/` |

### Files to Delete

| File | Reason |
|------|--------|
| `scripts/issue-monitor.sh` | Moved to `bin/issue-monitor.sh` |
| `scripts/issue-monitor.ps1` | Moved to `bin/issue-monitor.ps1` |
| `scripts/` (directory) | Empty after moves |
| `docs/onboarding/*.html` | Moved to `governance/docs/onboarding/` |
| `docs/` (directory) | Empty after moves |
| `TECHNIQUE_COMPARE.md` (root) | Moved to `governance/docs/TECHNIQUE_COMPARE.md` |

## 4. Approach

1. Create `bin/` directory
2. Move `scripts/issue-monitor.sh` → `bin/issue-monitor.sh` (git mv)
3. Move `scripts/issue-monitor.ps1` → `bin/issue-monitor.ps1` (git mv)
4. Move `docs/onboarding/` → `governance/docs/onboarding/` (git mv)
5. Move `TECHNIQUE_COMPARE.md` → `governance/docs/TECHNIQUE_COMPARE.md` (git mv)
6. Update all references across documentation and workflows
7. Update README.md file structure tree

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Reference check | All .md files | Grep for old paths, verify zero stale references |
| Workflow check | issue-monitor.yml | Verify script path is updated |
| Config check | config.yaml | Verify no config references to old paths |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Stale references to old paths | Medium | Low | Comprehensive grep for old paths before commit |
| Consuming repo breakage | Low | Low | Only moving internal files; init.sh path unchanged |
| Git history fragmentation | Low | Negligible | Using `git mv` preserves rename tracking |

## 7. Dependencies

- [x] No blocking dependencies — purely internal reorganization

## 8. Backward Compatibility

No breaking changes for consuming repos:
- `bash .ai/init.sh` path unchanged
- `config.yaml` unchanged
- `governance/` structure unchanged
- Only internal organization files move

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Standard for all changes |
| documentation-review | Yes | Documentation paths change |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Keep init.sh at root | Backward compatibility with consuming repos |
| 2026-02-25 | Keep convenience entry points (startup.md, init.md) | PR #56 added for discoverability |
| 2026-02-25 | Create bin/ instead of merging into existing dirs | Clean separation of executables from config |
| 2026-02-25 | **Reversed:** Move init.sh/init.ps1 to bin/ | Decision reversed in #226 — low adoption makes this the right time for the breaking change. Announced to consumers. |
