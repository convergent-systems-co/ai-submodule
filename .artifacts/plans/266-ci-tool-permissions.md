# fix(ci): Minimize issue-monitor tool permissions and document propagate-submodule security

**Author:** Team Lead (agent)
**Date:** 2026-02-25
**Status:** approved
**Issue:** #266
**Branch:** NETWORK_ID/fix/266/ci-tool-permissions

---

## 1. Objective

Remove overly broad tool permissions (`curl`, `pip`, `npm`) from the issue-monitor workflow's Claude dispatch configuration and replace `--force` with `--force-with-lease` in propagate-submodule workflow. Document security rationale for both workflows.

## 2. Rationale

The issue-monitor workflow dispatches Claude Code with `Bash(curl:*)`, `Bash(pip:*)`, and `Bash(npm:*)` — these enable data exfiltration and supply chain attacks. The workflow only needs git, gh, python, and file operations. The propagate-submodule workflow uses `git push --force` which can silently overwrite concurrent changes.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Remove all Bash tools | Yes | git/gh/python needed for governance |
| Keep curl for API calls | Yes | gh CLI covers GitHub API; curl is too broad |
| Scope git to safe subcommands | Yes | Not feasible in allowed_tools syntax; document risk instead |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files needed |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `.github/workflows/issue-monitor.yml` | Remove `Bash(curl:*)`, `Bash(pip:*)`, `Bash(npm:*)` from allowed_tools |
| `.github/workflows/propagate-submodule.yml` | Replace `--force` with `--force-with-lease`; add security comment |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Edit `issue-monitor.yml` line ~159: remove `Bash(pip:*)`, `Bash(npm:*)`, `Bash(curl:*)` from the `allowed_tools` string
2. Edit `propagate-submodule.yml` line ~85: change `git push -u origin "$BRANCH" --force` to `git push -u origin "$BRANCH" --force-with-lease`
3. Add inline comment in propagate-submodule.yml explaining force-with-lease rationale
4. Verify no other workflow files reference the removed tools

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Workflow YAML | Verify YAML is valid after edits |
| N/A | No automated tests | This is a configuration-only change |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Issue monitor needs curl for some operation | Low | Low | gh CLI covers all GitHub API needs |
| force-with-lease fails on stale ref | Low | Low | Workflow already closes existing PR first |

## 7. Dependencies

- None

## 8. Backward Compatibility

No breaking changes. Removing unused tool permissions is additive security.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Security-focused change |
| documentation-review | Yes | Always required |
| cost-analysis | Yes | Always required |
| threat-modeling | Yes | Always required |
| data-governance-review | Yes | Always required |

**Policy Profile:** default
**Expected Risk Level:** low
**Risk Classification:** Low — removing permissions is a security improvement

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Remove curl/pip/npm only, keep python | Python needed for policy engine execution in governance workflows |
