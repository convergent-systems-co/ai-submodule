# Move project.yaml to project root + jm-compliance guardrail

**Author:** Team Lead (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/160
**Branch:** NETWORK_ID/fix/160/project-yaml-root

---

## 1. Objective

Move `project.yaml` out of the `.ai` submodule directory to the project root so consuming repos don't need to write inside `.ai`. Add a `jm-compliance.yml` enterprise-locked guardrail to instructions.

## 2. Rationale

The `.ai` submodule should be read-only for consuming repos. Placing `project.yaml` inside `.ai/` forces consumers to modify the submodule, which creates dirty submodule state and complicates updates.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Move project.yaml to root only (break backward compat) | Yes | Existing consumers would break on update |
| Three-level merge chain (config.yaml → .ai/project.yaml → ./project.yaml) | Yes | **Selected** — additive, backward compatible |
| Symlink approach | Yes | Symlinks inside submodules are fragile across platforms |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.plans/160-project-yaml-root.md` | This plan |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `init.sh` | Add `$PROJECT_ROOT/project.yaml` to all Python for-loops (5 locations); add `root_project_file` to `parse_yaml_field`; add migration warning; update copy destination |
| `init.ps1` | Add `AI_PROJECT_ROOT` env var to Python config snippet; add migration warning; update copy destination |
| `.github/workflows/dark-factory-governance.yml` | Check root `project.yaml` first for opt-out; update remediation text |
| `instructions.md` | Update `.ai/project.yaml` reference to `project.yaml (project root)`; add jm-compliance guardrail section |
| `DEVELOPER_GUIDE.md` | Update cp command and description |
| `README.md` | Update cp command |
| `governance/prompts/init.md` | Update all 6 `.ai/project.yaml` references |
| `templates/project.yaml` + 7 language templates | Update comment header to `Copy to project.yaml in your project root` |
| `.gitignore` | Add explanatory comment for legacy `project.yaml` entry |
| `CLAUDE.md` | Update project.yaml reference; add jm-compliance convention |

### Files to Delete

N/A — no files deleted.

## 4. Approach

1. Add `$PROJECT_ROOT/project.yaml` to all Python config-reading for-loops in `init.sh` (5 locations)
2. Add `root_project_file` variable to `parse_yaml_field` function and include in its for-loop
3. Add migration warning block to `init.sh` (shown when `.ai/project.yaml` exists but `./project.yaml` doesn't)
4. Update `init.sh` "Next steps" copy destination
5. Mirror changes in `init.ps1` (Python env var, migration warning, copy destination)
6. Update governance workflow to check root `project.yaml` first for opt-out detection
7. Update all documentation references from `.ai/project.yaml` to `project.yaml`
8. Update all template comment headers
9. Add jm-compliance guardrail to `instructions.md` and `CLAUDE.md`

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | init.sh | Run with project.yaml at `.ai/` only → backward compat + migration warning |
| Manual | init.sh | Run with project.yaml at root only → new path works |
| Manual | init.sh | Run with both → root takes precedence |
| Manual | init.sh | Run with neither → config.yaml defaults apply |
| Grep | All files | Verify no stale `.ai/project.yaml` references remain in docs |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Consumers with `.ai/project.yaml` break on update | Low | Medium | Three-level merge chain preserves backward compat; migration warning guides users |
| Python snippet fails when env var is missing | Low | Low | `os.environ.get()` returns None; `os.path.exists()` handles None gracefully |

## 7. Dependencies

- [x] No external dependencies

## 8. Backward Compatibility

Fully backward compatible. The three-level merge chain reads `.ai/project.yaml` as before, with `./project.yaml` as an additive override. Existing consumers continue working without changes. A migration warning encourages moving to the new location.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Script logic changes |
| security-review | Yes | Default required panel |
| documentation-review | Yes | Multiple doc updates |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Three-level merge chain instead of hard migration | Backward compatibility is a core convention |
| 2026-02-24 | Add jm-compliance guardrail to instructions.md | User requested enterprise lock protection |
