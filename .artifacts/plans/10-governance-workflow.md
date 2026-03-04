# Add dark-factory-governance.yml GitHub Actions Workflow

**Author:** Coder (agentic)
**Date:** 2026-02-21
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/10
**Branch:** NETWORK_ID/feat/10/governance-workflow

---

## 1. Objective

Create the full `dark-factory-governance.yml` CI workflow with 4 jobs per the CI blueprint, replacing the inline Python in the existing `governance-review.yml` with calls to the policy engine. The workflow runs alongside `jm-compliance.yml` without modifying it.

## 2. Rationale

The existing `governance-review.yml` has inline Python that does basic evaluation against `default.yaml` only. It lacks Copilot review gate, manifest generation, proper job separation, and profile selection. The policy engine (`.governance/policy-engine.py`) now handles the core evaluation.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep governance-review.yml and add separate workflow | Yes | Duplicate reviews on same PR |
| Full Node.js tooling per blueprint | Yes | Massive scope; Python engine already built |
| Replace governance-review.yml entirely | **Selected** | Clean, single workflow, reuses policy engine |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.github/workflows/dark-factory-governance.yml` | Full 4-job governance workflow |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `.github/workflows/governance-review.yml` | Remove — replaced by dark-factory-governance.yml |

### Files to Delete

| File | Reason |
|------|--------|
| `.github/workflows/governance-review.yml` | Replaced by the new workflow |

## 4. Approach

1. Create `dark-factory-governance.yml` with 4 jobs:
   - **detect**: Detect changed files and determine which panels should trigger
   - **validate**: Validate panel emissions against schema
   - **evaluate**: Run policy engine, produce manifest
   - **review**: Post PR review based on policy decision

2. Remove `governance-review.yml`

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Workflow syntax | YAML | Verify workflow parses correctly |
| PR test | Full workflow | Workflow runs on this PR |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Removing governance-review.yml breaks existing checks | Low | Medium | New workflow produces same status check names |
| Policy engine not found in CI | Low | High | Script is committed to repo, pip deps installed in workflow |

## 7. Dependencies

- [x] Policy engine: `.governance/policy-engine.py` (done in #9)
- [x] Schemas: `panel-output.schema.json`, `run-manifest.schema.json`

## 8. Backward Compatibility

The new workflow produces the same `review` status check name as the old one. The `detect` job name also matches. No branch protection changes needed.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | CI workflow change |
| security-review | Yes | Required |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Replace governance-review.yml instead of adding alongside | Avoid duplicate reviews |
| 2026-02-21 | Python over Node.js for CI tooling | Matches policy engine, no npm infra needed |
