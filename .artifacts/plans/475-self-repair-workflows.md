# Self-Repair CI Workflows

**Author:** Claude (Coder persona)
**Date:** 2026-02-27
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/475
**Branch:** NETWORK_ID/feat/475/self-repair-workflows

---

## 1. Objective

Add three self-repair CI workflows that maintain repository hygiene autonomously: workflow lint detection and issue creation, automatic rebasing of agent-created PRs, and cleanup of merged/stale branches.

## 2. Rationale

As the Dark Forge platform runs more autonomous agents, the repository accumulates workflow lint errors, stale branches, and out-of-date PR branches. Manual maintenance does not scale. Automated self-repair workflows keep the repository healthy without human intervention, aligning with Phase 4b (Autonomous Remediation) goals.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Manual lint checks | Yes | Does not scale with autonomous agent output |
| External CI service (e.g., Renovate for rebasing) | Yes | Adds external dependency; gh CLI is sufficient |
| Single monolithic workflow | Yes | Separation of concerns — each workflow has distinct triggers and responsibilities |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.github/workflows/self-repair-lint.yml` | Detect actionlint errors in workflow files and create issues for fixes |
| `.github/workflows/auto-rebase.yml` | Keep agent-created PRs rebased on main |
| `.github/workflows/branch-cleanup.yml` | Delete merged and stale remote branches |
| `.governance/plans/475-self-repair-workflows.md` | This plan |

### Files to Modify

| File | Change Description |
|------|-------------------|
| None | No existing files modified |

### Files to Delete

| File | Reason |
|------|--------|
| None | No files deleted |

## 4. Approach

1. Create the governance plan (this document)
2. Implement `self-repair-lint.yml` — actionlint installation, error detection, issue creation with lint results
3. Implement `auto-rebase.yml` — find agent PRs, attempt rebase, comment on conflicts
4. Implement `branch-cleanup.yml` — delete merged branches and stale branches with configurable threshold
5. Review all workflows for YAML validity, proper error handling, and production readiness
6. Commit and create PR

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | All workflows | Trigger via `workflow_dispatch` to validate execution |
| Dry-run | branch-cleanup | `dry_run: true` input validates logic without destructive action |
| CI | YAML syntax | GitHub Actions validates YAML on push |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Auto-rebase introduces conflicts | Medium | Low | Abort rebase on conflict, comment on PR |
| Branch cleanup deletes needed branch | Low | Medium | Protected branch patterns, dry-run mode, only targets merged or stale branches |
| Lint workflow creates duplicate issues | Low | Low | Each run creates at most one issue; can be improved later with dedup |
| jm-compliance.yml modification | None | Critical | Workflows do not touch jm-compliance.yml; lint is read-only |

## 7. Dependencies

- [x] GitHub Actions runner with `ubuntu-latest` — non-blocking
- [x] `gh` CLI available in runners — non-blocking (pre-installed)
- [x] `actionlint` binary available via GitHub releases — non-blocking

## 8. Backward Compatibility

Fully additive. Three new workflow files are created. No existing workflows are modified. No breaking changes.

## 9. Governance

Expected panel reviews and policy profile:

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New CI workflow code |
| security-review | Yes | Workflows use GITHUB_TOKEN, push --force-with-lease, branch deletion |
| threat-modeling | Yes | Evaluate risk of automated branch operations |
| cost-analysis | Yes | Scheduled workflows consume CI minutes |
| documentation-review | Yes | Plan document serves as documentation |
| data-governance-review | Yes | Standard requirement |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Use `jq -s` with file-based lint output instead of pipe | More reliable error counting with actionlint JSON format |
| 2026-02-27 | Skip `release/*` branches in cleanup | Release branches are long-lived and should not be auto-deleted |
| 2026-02-27 | Use `--force-with-lease` for rebase push | Safer than `--force`; fails if remote has unexpected commits |
| 2026-02-27 | Exclude `jm-compliance.yml` from lint-triggered fixes | Enterprise-locked file must never be modified |
