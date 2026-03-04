# Move Language Templates Under Governance

**Author:** Team Lead (agentic)
**Date:** 2026-02-24
**Status:** completed
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/216
**Branch:** NETWORK_ID/refactor/216/move-templates-to-governance

---

## 1. Objective

Move the root-level `templates/` directory (language-specific scaffolding for consuming repos) to `governance/templates/`, and update all references across the codebase.

## 2. Rationale

The repo owner has determined that language templates do not belong at the root level. Moving them under `governance/` consolidates all governance machinery in one place.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep at root (status quo) | Yes | Owner explicitly requested the move (issue #216) |
| Move to `governance/prompts/templates/` | Yes | That directory already exists for cognitive prompt templates (plan-template, runtime-di-template, weekly-report-template) — mixing language scaffolding with prompt templates would conflate two distinct purposes |
| Move to `governance/language-templates/` | Yes | `governance/templates/` is the simplest path and matches the issue request |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | Git mv preserves files — no new files created |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `init.sh` | Update `GOALS_TEMPLATE` path from `templates/GOALS.md` to `governance/templates/GOALS.md`; update help text |
| `init.ps1` | Update help text referencing `templates/` |
| `governance/prompts/init.md` | Update template paths in table and commands |
| `README.md` | Update directory structure listing and project config section |
| `DEVELOPER_GUIDE.md` | Update `cp .ai/templates/` command |
| `CLAUDE.md` | No changes needed (doesn't reference root templates/) |
| `governance/docs/artifact-classification.md` | Update `templates/` directory mapping |
| `governance/docs/context-management.md` | Update `templates/{language}/instructions.md` reference |
| `governance/docs/dark-factory-governance-model.md` | Update `templates/` classification line |
| `governance/docs/end-to-end-walkthrough.md` | Update `templates/` references in installation section |
| `governance/policy/collision-domains.yaml` | Update `templates/**` path to `governance/templates/**` |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | `git mv` handles the move |

## 4. Approach

1. `git mv templates/ governance/templates/` — move the directory
2. Update `init.sh` — fix GOALS_TEMPLATE path and help text
3. Update `init.ps1` — fix help text
4. Update `governance/prompts/init.md` — fix template path table and copy commands
5. Update `README.md` — fix directory structure listing and project config section
6. Update `DEVELOPER_GUIDE.md` — fix cp command
7. Update `governance/docs/artifact-classification.md` — fix directory mapping
8. Update `governance/docs/context-management.md` — fix Tier 1 loading reference
9. Update `governance/docs/dark-factory-governance-model.md` — fix classification
10. Update `governance/docs/end-to-end-walkthrough.md` — fix installation references
11. Update `governance/policy/collision-domains.yaml` — fix path patterns
12. Commit all changes in a single logical commit

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Grep verification | All files | `grep -r "templates/"` to confirm no stale references remain pointing to root-level templates |
| Path validation | Moved files | Confirm all files exist at new location |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Consuming repos break on submodule update | Medium | Medium | This is a breaking change for consuming repos using `cp .ai/templates/...`. However, consuming repos pin to a submodule SHA and re-run init.sh on update. Update docs to reflect new path. |
| Missed references | Low | Low | Comprehensive grep after changes to catch stragglers |

## 7. Dependencies

- [ ] None — standalone refactoring task

## 8. Backward Compatibility

This is a breaking path change for consuming repos that reference `templates/` directly. However:
- Consuming repos pin the submodule version and update deliberately
- The `init.sh` / `init.ps1` scripts will be updated atomically with the move
- All documentation will reflect the new path

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Standard review |
| documentation-review | Yes | Multiple doc files affected |
| security-review | Yes | Required by default policy |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Target path: `governance/templates/` | Distinguishes from `governance/prompts/templates/` (prompt templates) while keeping language templates under governance/ |
| 2026-02-24 | Overrides prior PR #46 decision | Repo owner explicitly requested the move in issue #216 |
