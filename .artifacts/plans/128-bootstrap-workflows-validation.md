# Bootstrap Workflows & Validation for Consuming Projects

**Author:** Team Lead (agentic)
**Date:** 2026-02-23
**Status:** completed
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/128
**Branch:** NETWORK_ID/feat/128/bootstrap-workflows-validation

---

## 1. Objective

Complete the remaining acceptance criteria from issue #128: add org ruleset validation to `init.sh`, add workflow presence pre-flight to `startup.md`, and restructure the workflows config from a flat list to required/optional categories.

Most of #128 is already implemented on main (workflow symlinks, repo settings via gh api, CODEOWNERS generation, repository-configuration.md, DEVELOPER_GUIDE.md). This plan addresses the gaps.

## 2. Rationale

The agentic loop depends on org rulesets and governance workflows being present. Without validation, failures are silent — PRs can't auto-merge, reviews aren't enforced, and the agent only discovers the problem mid-cycle. Adding explicit validation at bootstrap and startup catches misconfiguration early.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Validate only at startup (not init.sh) | Yes | init.sh is the bootstrap entry point; catching issues there prevents repeated startup failures |
| Keep flat workflows_to_copy config | Yes | Issue #128 explicitly requests required/optional distinction; optional workflows shouldn't be mandatory for consuming repos |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files needed |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `config.yaml` | Restructure `workflows_to_copy` → `workflows.required` + `workflows.optional` |
| `init.sh` | Update workflow copy to read new config structure; add `validate_rulesets()` function |
| `governance/prompts/startup.md` | Add workflow presence pre-flight check |
| `governance/docs/repository-configuration.md` | Document new config structure and ruleset validation |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. **Restructure config.yaml** — Replace `workflows_to_copy: [...]` with `workflows.required: [...]` and `workflows.optional: [...]`. Maintain backward compatibility in init.sh (if old key exists, treat it as required).

2. **Update init.sh workflow copy** — Modify the Python snippet that reads workflow list to handle the new structure. Required workflows are always copied/symlinked. Optional workflows are copied/symlinked if they exist in `.ai/.github/workflows/` but missing ones only produce a warning.

3. **Add ruleset validation to init.sh** — New function `validate_rulesets()` that reads `repository.branch_protection.expected_rulesets` from config and checks each against `gh api repos/{owner}/{repo}/rulesets`. Report matches/mismatches as informational output.

4. **Add workflow pre-flight to startup.md** — After the existing CODEOWNERS check, add a check that `dark-factory-governance.yml` exists in `.github/workflows/`. If missing, warn and suggest running `bash .ai/init.sh`.

5. **Update repository-configuration.md** — Add section documenting the new config structure, ruleset validation behavior, and startup pre-flight.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | init.sh | Run init.sh in submodule and non-submodule contexts to verify idempotency |
| Manual | startup.md | Verify pre-flight check catches missing workflows |

No automated tests — this is a configuration-only repo with no test runner.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing init.sh behavior | Low | Medium | Backward-compatible: old `workflows_to_copy` key still works |
| Ruleset API requires admin permissions | Medium | Low | Graceful degradation: skip if unauthorized, warn user |
| Startup pre-flight blocks unnecessarily | Low | Low | Warning only, non-blocking |

## 7. Dependencies

- [x] No blocking dependencies — all changes are within this repo

## 8. Backward Compatibility

Fully backward compatible. The old `workflows_to_copy` key is still supported — init.sh treats it as `workflows.required` if the new structure isn't found. Consuming repos with existing `project.yaml` files are unaffected.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Standard review for all changes |
| security-review | Yes | Default required panel |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Use symlinks not copies for workflows | Submodule updates flow automatically |
| 2026-02-23 | Ruleset validation is informational only | Cannot apply rulesets via API (org-level) |
