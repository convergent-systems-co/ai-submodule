# Emission Trust Boundary — Semantic Consistency and PR-Branch Detection

**Author:** Code Manager (agentic)
**Date:** 2026-02-25
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/234
**Branch:** itsfwcp/fix/234/emission-trust-boundary

---

## 1. Objective

Add semantic consistency validation to the policy engine and detect PR-supplied emissions in CI, preventing malicious or compromised AI agents from crafting emissions that bypass safety checks.

## 2. Rationale

Currently, emissions are only validated structurally (JSON Schema). A malicious emission can set `aggregate_verdict: "approve"` while having `block` findings, or set `risk_level: "negligible"` with critical policy flags. The CI also reads emissions from the PR branch, meaning a PR can include pre-crafted approving emissions.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Schema-only validation | Yes | Schema validates structure, not semantic consistency |
| Full cryptographic provenance | Yes | Too complex for this phase; deferred to future work |
| Semantic checks in engine + PR-branch emission detection in CI | Yes | **Selected** — practical, implementable, addresses core risks |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/bin/policy-engine.py` | Add `validate_emission_consistency()` function, call it during emission loading |
| `.github/workflows/dark-factory-governance.yml` | Add step to detect and flag PR-modified emissions |
| `tests/test_policy_engine.py` | Add unit tests for semantic consistency validation |
| `tests/test_policy_integration.py` | Add integration tests for consistency rejection |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. Add `validate_emission_consistency(emission)` to policy-engine.py:
   - If any finding has `verdict: "block"`, `aggregate_verdict` must not be `"approve"`
   - If critical/high `policy_flags` exist, `risk_level` must not be `"negligible"`
   - Warnings are logged and emission is flagged (not rejected outright, to avoid blocking legitimate edge cases)

2. Integrate consistency validation into `load_emissions()` — flag inconsistent emissions in the evaluation log.

3. Add CI step to detect PR-modified emissions in `governance/emissions/`.

4. Add tests.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `validate_emission_consistency` | Test all consistency rules |
| Integration | Full pipeline | Test that inconsistent emissions are flagged |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| False positives on legitimate emissions | Low | Low | Warn rather than hard-block on consistency violations |
| CI step adds latency | Low | Low | Simple git diff check, minimal overhead |

## 7. Dependencies

- [x] No blocking dependencies

## 8. Backward Compatibility

Additive — new warnings in evaluation log, no behavior change for valid emissions.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Trust boundary change |
| code-review | Yes | Engine logic change |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Warn rather than block on consistency violations | Avoid false positives on legitimate edge cases; policy engine already catches critical flags via block conditions |
| 2026-02-25 | Emission freshness deferred to issue #240 | Separate concern; this issue focuses on semantic consistency and PR-branch detection |
