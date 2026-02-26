# test(policy-engine): Close coverage gaps in edge cases and error paths

**Author:** Code Manager (agent)
**Date:** 2026-02-25
**Status:** approved
**Issue:** #263
**Branch:** itsfwcp/test/263/policy-engine-coverage

---

## 1. Objective

Increase policy engine test coverage to 99%+ by adding tests for uncovered error paths, edge cases, and boundary values. Use the manifest_schema fixture. Address the specific gaps identified in the issue.

## 2. Rationale

Current coverage is 96% (29 uncovered lines). Critical paths like escalation-block flow, schema load failure, and compound conditions with negation lack integration tests. Boundary values (confidence 0.0/1.0) are untested.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Ignore edge cases | Yes | Policy engine is deterministic enforcement — all paths must be tested |
| Unit tests only | Yes | Integration tests needed for escalation-through-evaluate flow |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | Tests added to existing files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `tests/test_policy_engine.py` | Add unit tests for error paths, boundary values, malformed inputs |
| `tests/test_policy_integration.py` | Add integration tests for escalation-block flow, schema load failure |
| `tests/test_scenarios.py` | Add scenario tests for compound escalation conditions |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. **Escalation block integration test** — test where block conditions pass but escalation rules return "block", flowing through evaluate() to produce correct manifest (lines 1210-1214)
2. **Schema load failure test** — mock missing schema directory to test FileNotFoundError path (lines 1048-1051)
3. **Escalation compound with NOT** — test `condition and not sub_condition` in escalation context (lines 690-698)
4. **Boundary confidence values** — test confidence exactly 0.0 and 1.0 against thresholds
5. **Malformed YAML profile** — test invalid YAML syntax and missing required keys
6. **Timestamp parsing exception** — test malformed ISO timestamp in freshness validation (lines 214-215)
7. **Model version extraction** — test manifest.model_version extracted from emission execution_context (lines 984-985)
8. **Use manifest_schema fixture** — add explicit manifest field validation test using the existing unused fixture
9. Run coverage and verify 99%+ reached

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | Error paths | Schema load failure, malformed YAML, bad timestamps |
| Unit | Boundary values | Confidence 0.0, 1.0 |
| Integration | Escalation flow | Escalation-block through evaluate() |
| Integration | Compound conditions | Negated sub-conditions in escalation |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| New tests expose latent bugs | Low | Medium | Fix any bugs found; they indicate real issues |
| Tests are brittle | Low | Low | Use existing fixture patterns |

## 7. Dependencies

- None

## 8. Backward Compatibility

Test-only changes. No behavioral changes to the policy engine.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Always required |
| documentation-review | Yes | Always required |
| cost-analysis | Yes | Always required |
| threat-modeling | Yes | Always required |
| data-governance-review | Yes | Always required |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Add to existing test files rather than create new ones | Follows project test organization pattern |
