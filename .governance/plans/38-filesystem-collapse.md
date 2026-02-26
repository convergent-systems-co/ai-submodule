# Collapse Filesystem Structure

**Author:** Claude (Code Manager)
**Date:** 2026-02-21
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/38
**Branch:** itsfwcp/feat/38/collapse-filesystem-structure

---

## 1. Objective

Reduce top-level directory clutter from 9 visible directories to 3 by consolidating governance-internal directories under a single `governance/` directory. Consuming developers who don't understand the agentic loop see a clean, understandable top-level layout.

**Before** (9 visible directories):
```
docs/  emissions/  instructions/  manifests/  personas/  policy/  prompts/  schemas/  templates/
```

**After** (3 visible directories):
```
governance/  instructions/  templates/
```

## 2. Rationale

The top-level currently exposes internal governance machinery (personas, panels, policy, schemas, emissions, manifests, prompts, docs) at the same level as developer-facing content (instructions, templates). A consuming developer adding `.ai/` as a submodule sees 16+ items and has no idea what most of them are.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Single `governance/` rollup | Yes — **selected** | — |
| Two-tier split (`core/` + `data/`) | Yes | Adds an extra abstraction with no real clarity gain; "core" vs "data" is ambiguous for this domain |
| Dotfile-hide everything (`._internal/`) | Yes | Hides too aggressively; governance directory should be visible and explorable, just grouped |
| Status quo | Yes | Fails the issue's stated goal — top level is cluttered and confusing |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files — this is a restructure of existing content |

### Files to Modify (path reference updates)

| File | Change Description |
|------|-------------------|
| `CLAUDE.md` | Update 14 path references to prefix with `governance/` |
| `README.md` | Update directory tree listing and ~20 inline references |
| `GOALS.md` | Update 1 reference to `docs/` |
| `init.sh` | Update template path references |
| `config.yaml` | No changes needed (only references `instructions.md` and root-level symlinks) |
| `instructions.md` | No changes needed (only references `.checkpoints/` and `project.yaml`) |
| `instructions/governance.md` | Update 2 references (`schemas/` paths) |
| `.github/workflows/dark-factory-governance.yml` | Update `emissions/`, `.governance/`, `policy/`, `schemas/` paths |
| `.github/workflows/plan-archival.yml` | No changes needed (references `.plans/` which stays put) |
| `.governance/policy-engine.py` | Update `policy/` and `schemas/` references |
| `.governance/README.md` | Update path references |
| `governance/policy/default.yaml` | Update panel trigger path patterns |
| `governance/personas/panels/ai-expert-review.md` | Update artifact scope references |
| `governance/personas/agentic/code-manager.md` | Update delegation references |
| `governance/prompts/startup.md` | Update plan-template, persona, panel references |
| `governance/docs/artifact-classification.md` | Update artifact location references |
| `governance/docs/migration-summary.md` | Update artifact catalog paths |
| `.claude/commands/startup.md` | Update startup.md reference path |
| All `.plans/*.md` files | Update path references in existing plans |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | Directories are moved, not deleted |

### Directories Moved

| From | To |
|------|-----|
| `personas/` | `governance/personas/` |
| `policy/` | `governance/policy/` |
| `schemas/` | `governance/schemas/` |
| `emissions/` | `governance/emissions/` |
| `manifests/` | `governance/manifests/` |
| `prompts/` | `governance/prompts/` |
| `docs/` | `governance/docs/` |

### Directories That Stay

| Directory | Reason |
|-----------|--------|
| `instructions/` | Developer-facing (code quality, security, testing standards) |
| `templates/` | Developer-facing (language conventions) |
| `.checkpoints/` | Hidden, operational |
| `.claude/` | Hidden, tool config |
| `.cursor/` | Hidden, tool config |
| `.github/` | Hidden, GitHub requires this location |
| `.governance/` | Hidden, runtime engine |
| `.plans/` | Hidden, operational |

## 4. Approach

1. **Create `governance/` directory** and move the 7 directories into it using `git mv`
2. **Update all path references** in files that reference the moved directories (systematic find-and-replace)
3. **Update CI workflow** paths in `.github/workflows/`
4. **Update policy trigger paths** in `governance/policy/default.yaml`
5. **Update README.md** directory tree listing
6. **Update CLAUDE.md** architecture documentation
7. **Verify** init.sh still works (symlink paths reference root-level files, should be unaffected)
8. **Verify** no broken cross-references remain

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Path references | Grep for old paths to verify none remain |
| Manual | init.sh | Verify script references are correct |
| CI | Workflows | Verify workflow file paths resolve |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Consuming repos break on submodule update | High | Medium | Document in migration notes; consuming repos must re-run init.sh |
| Missed path reference causes silent failure | Medium | Medium | Systematic grep for old paths after all moves |
| `git mv` loses history tracking | Low | Low | Git tracks renames; single commit keeps history intact |

## 7. Dependencies

- [x] No blocking dependencies — this is a standalone restructure

## 8. Backward Compatibility

**This is a breaking change for consuming repos.** Consuming repos that reference governance artifact paths directly (unlikely — they typically only interact via `instructions.md` and `CLAUDE.md`) would need path updates. The `init.sh` bootstrap and symlink chain (`instructions.md` → `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`) is unaffected since those files stay at the root.

Migration: consuming repos run `git submodule update --remote .ai` followed by `bash .ai/init.sh` to pick up the new structure.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| AI Expert Review | No | This is a structural refactor of the governance repo itself, not a policy or persona change |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Keep `instructions/` at top level, not in `governance/` | Instructions define developer-facing standards (code quality, testing, security) that consuming devs may want to read/customize. They're not governance-internal. |
| 2026-02-21 | Keep `templates/` at top level | Templates are developer-facing language conventions, not governance machinery |
| 2026-02-21 | Use `governance/` not `core/` or `engine/` | "Governance" matches the project's domain language and is self-explanatory |
