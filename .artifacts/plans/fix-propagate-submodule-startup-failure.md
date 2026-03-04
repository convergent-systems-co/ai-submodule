# Fix propagate-submodule workflow startup_failure

**Author:** Claude (Coder persona)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** GitHub Actions run 22363559063 (persistent startup_failure)
**Branch:** NETWORK_ID/fix/propagate-submodule-workflow

---

## 1. Objective

Eliminate the persistent `startup_failure` on the `propagate-submodule.yml` workflow so it runs successfully on every push to main.

## 2. Rationale

The workflow has failed with `startup_failure` on all 15 runs since creation. The YAML is syntactically valid, but GitHub validates all action references at workflow startup — even inside jobs gated with `if: false`. The third-party action `peter-evans/create-pull-request` is likely blocked by an org-level Actions policy (org policies are not readable without admin scope, but the failure pattern is consistent with action allowlist restrictions).

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Remove the workflow entirely | Yes | Loses propagation capability needed when consumers are added |
| Add `peter-evans` to org allowlist | Yes | Requires org admin access; introduces third-party dependency |
| Replace with `gh` CLI commands | Yes | **Selected** — native tooling, no third-party dependency, pre-installed on runners |
| Replace with `actions/github-script` | Yes | More complex than `gh` CLI for a simple PR creation |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | — |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `.github/workflows/propagate-submodule.yml` | Replace `peter-evans/create-pull-request` with `gh` CLI commands; elevate `contents` permission to `write` for the `update-consumers` job (needed for `gh pr create`) |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | — |

## 4. Approach

1. In the `update-consumers` job, replace the `peter-evans/create-pull-request` step with native git + `gh pr create` commands.
2. Add `pull-requests: write` permission (required by `gh pr create`). Keep this scoped to the `update-consumers` job only, or at the workflow level since the `changelog` job only reads.
3. Validate YAML locally.
4. Create branch, push, open PR.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Syntax | Workflow YAML | Validate with `python3 -c "import yaml; ..."` |
| Runtime | Push to main | After merge, next push to main should produce a successful (green) `changelog` job run |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `gh` CLI behavior differs from `peter-evans` action | Low | Low | `update-consumers` is disabled (`if: false`); only `changelog` job runs currently |
| Permissions too broad | Low | Low | Only adding `pull-requests: write` which is needed for PR creation |

## 7. Dependencies

- [x] No blocking dependencies — this is a self-contained CI fix

## 8. Backward Compatibility

No breaking changes. The `update-consumers` job remains disabled (`if: false`). The `changelog` job behavior is unchanged.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Workflow permission changes |
| code-review | Yes | Standard |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Replace third-party action with `gh` CLI | Avoids org action allowlist issues permanently |
