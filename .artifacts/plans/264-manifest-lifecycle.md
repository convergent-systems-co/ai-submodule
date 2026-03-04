# fix(data): Manifest immutability enforcement, retention policy, and schema versioning documentation

**Author:** Team Lead (agent)
**Date:** 2026-02-25
**Status:** approved
**Issue:** #264
**Branch:** NETWORK_ID/fix/264/manifest-lifecycle

---

## 1. Objective

Establish at least one immutability enforcement mechanism for manifests, document a manifest retention policy, create a schema versioning policy, and add version history to `governance/policy/README.md`.

## 2. Rationale

Manifests are classified as immutable audit artifacts but have no enforcement mechanism. Schema versions exist but lack a documented lifecycle. Policy profiles have versions but no changelog.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Pre-commit hook for manifest protection | Yes | Too invasive for a submodule — consuming repos may not install hooks |
| CI-only enforcement | Yes | Selected — governance workflow already runs on all PRs |
| Content hashing in manifests | Yes | Deferred — CI check is simpler first step |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/policy/README.md` | Version history and schema versioning policy documentation |
| `docs/governance/manifest-lifecycle.md` | Manifest retention policy and immutability enforcement docs |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `CODEOWNERS` | Add explicit `governance/manifests/` ownership rule |
| `docs/governance/artifact-classification.md` | Add retention policy details and enforcement reference |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Create `governance/policy/README.md` with:
   - Version history table for all policy profiles (default 1.3.1, others 1.0.1)
   - Schema versioning policy (semver for enforcement artifacts, git SHA for cognitive)
   - Breaking change process documentation
2. Create `docs/governance/manifest-lifecycle.md` with:
   - Manifest retention policy (permanent in git, 90-day CI artifacts)
   - Immutability enforcement description (CODEOWNERS + future CI check)
   - Panel name validation note (panels.schema.json vs panel-output.schema.json)
3. Add `governance/manifests/` rule to CODEOWNERS
4. Update `docs/governance/artifact-classification.md` with retention specifics and cross-reference to new lifecycle doc

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | CODEOWNERS syntax | Verify rule is valid |
| N/A | Documentation-only | No automated tests for docs |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| CODEOWNERS rule blocks legitimate manifest commits | Low | Low | Rule uses same owners as .ai directory |

## 7. Dependencies

- None

## 8. Backward Compatibility

Additive only — new documentation and CODEOWNERS rule. No breaking changes.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Primary documentation change |
| data-governance-review | Yes | Data lifecycle policy |
| security-review | Yes | Always required |
| cost-analysis | Yes | Always required |
| threat-modeling | Yes | Always required |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | CODEOWNERS + documentation first, CI enforcement deferred | Simplest enforcement mechanism; CI check can follow as separate issue |
