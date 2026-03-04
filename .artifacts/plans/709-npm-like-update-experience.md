# npm-like Update Experience for Governance Framework

**Author:** Team Lead (batch-scoped PM mode)
**Date:** 2026-03-02
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/709
**Branch:** itsfwcp/feat/709/npm-like-update-experience

---

## 1. Objective

Create a single-command update experience (`bash .ai/bin/update.sh`) that pulls the latest submodule, shows a changelog, detects drift from upstream, and validates for breaking changes -- reducing the maintenance burden score from 3/5 to 4/5.

## 2. Rationale

Currently updating requires `git submodule update --remote .ai && bash .ai/bin/init.sh --refresh`. Developers must understand submodule mechanics. DACH provides npm version bump with automatic build.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| npm package distribution | Yes | Would require fundamental architecture change away from submodule model |
| Auto-update on every git pull | Yes | Too aggressive; updates should be intentional |
| GitHub App for automated PRs | Yes | Over-engineering; workflow-based approach is simpler |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `bin/update.sh` | Single-command update script with changelog, drift detection, and breaking change detection |
| `governance/bin/drift-detection.sh` | Detect local customizations that diverge from upstream (content hash comparison) |
| `governance/bin/breaking-change-check.sh` | Check for schema/API changes between versions |
| `governance/schemas/version-manifest.schema.json` | Schema for version tracking metadata |
| `docs/guides/updating.md` | Update guide for consuming repos |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `bin/init.sh` | Add `--update` flag as alias for `update.sh`; add version display on init |
| `.github/workflows/propagate-submodule.yml` | Enhance to include changelog in PR body, add breaking change detection step |
| `governance/bin/vendor-engine.sh` | Add version comparison output for changelog generation |

### Files to Delete

None.

## 4. Approach

1. **Create `bin/update.sh`** — Main update script:
   - Check current submodule SHA
   - Pull latest: `git submodule update --remote .ai`
   - Generate changelog: `git -C .ai log --oneline OLD_SHA..NEW_SHA`
   - Run `init.sh --refresh` automatically
   - Run breaking change detection
   - Run drift detection
   - Display summary with color-coded output
   - Exit codes: 0=success, 1=breaking changes detected, 2=drift detected (warnings)

2. **Create `governance/bin/drift-detection.sh`** — Content hash tracking:
   - On each update, compute SHA256 hashes of key governance files (policy profiles, schemas, personas)
   - Store hashes in `.governance/state/upstream-hashes.json`
   - On next update, compare local files against stored upstream hashes
   - Report files that were locally modified (drift from upstream)
   - Inspired by DACH's template hash drift detection

3. **Create `governance/bin/breaking-change-check.sh`** — Schema/API change detection:
   - Compare `governance/schemas/*.json` before and after update
   - Detect removed fields, changed types, new required fields
   - Compare `governance/policy/*.yaml` for removed or renamed keys
   - Output warnings for breaking changes, suggest migration steps

4. **Enhance `propagate-submodule.yml`** — Add changelog and breaking change info to auto-generated PRs:
   - Include `git log --oneline` diff in PR body
   - Run breaking-change-check and include results
   - Add labels for breaking changes

5. **Create version manifest schema** — Track version metadata for consuming repos

6. **Write documentation** — Update guide explaining the new workflow

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `drift-detection.sh` | Test hash generation and comparison with known fixtures |
| Unit | `breaking-change-check.sh` | Test detection of schema field removal, type changes |
| Integration | `update.sh` | Test full update flow in a mock submodule setup |
| Manual | Consuming repo | Test update from a real consuming repo |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Update script fails mid-way | Low | Medium | Atomic: submodule update + refresh in sequence with rollback on failure |
| False positive breaking changes | Medium | Low | Conservative detection; flag as warnings, not errors |
| Drift detection too noisy | Medium | Low | Only track key files (policies, schemas); ignore generated files |

## 7. Dependencies

- [x] `bin/init.sh` exists with `--refresh` support (non-blocking)
- [x] `propagate-submodule.yml` exists (non-blocking)
- [x] `vendor-engine.sh` exists with version tracking (non-blocking)

## 8. Backward Compatibility

Fully backward compatible. The `update.sh` is a new script; existing `git submodule update` + `init.sh --refresh` workflow continues to work. The `--update` flag on `init.sh` is additive.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New scripts |
| security-review | Yes | Git operations, submodule integrity |
| documentation-review | Yes | New update guide |
| cost-analysis | No | No infrastructure cost impact |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Separate update.sh rather than extending init.sh | Clearer intent; init.sh is already complex |
| 2026-03-02 | Drift detection uses content hashes not git diff | Works even when local customizations are committed |
| 2026-03-02 | Breaking changes are warnings, not blockers | Consuming repos may need time to migrate |
