# LLM Eval/Deployment Distinction Detection

**Author:** Team Lead (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/407
**Branch:** NETWORK_ID/fix/407/eval-deployment-canary

---

## 1. Objective

Detect when an LLM behaves differently during evaluation (panel review execution) versus normal operation by introducing canary tests, behavioral consistency checks, and calibration tracking into the panel emission pipeline.

## 2. Rationale

LLMs may pattern-match to produce "good" results when they detect they're being evaluated. The existing plausibility checks (#404) and hallucination detection (#406) catch output-level anomalies but not behavioral-level shifts. Canary inputs with known-correct answers serve as calibration signals.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Statistical comparison across runs only | Yes | Requires large sample; too slow for per-PR detection |
| Canary tests + behavioral consistency (chosen) | Yes | Provides immediate signal per-panel execution |
| Prompt-level sandboxing | Yes | Cannot prevent LLM from detecting evaluation context |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/policy/canary-calibration.yaml` | Canary test configuration — known inputs with expected outputs |
| `governance/engine/tests/test_canary_calibration.py` | Tests for canary validation logic |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/panel-output.schema.json` | Add optional `canary_results` object to emission schema |
| `governance/policy/default.yaml` | Add `canary_calibration` section with scoring rules |
| `governance/engine/policy_engine.py` | Validate canary results in emissions; flag deviations |
| `governance/prompts/startup.md` | Add canary injection in Phase 4b/4c panel execution |
| `governance/prompts/reviews/security-review.md` | Add canary input section with known vulnerability pattern |
| `governance/prompts/reviews/code-review.md` | Add canary input section with known code quality issue |

### Files to Delete

| File | Reason |
|------|--------|
| None | N/A |

## 4. Approach

1. **Define canary calibration config** (`canary-calibration.yaml`):
   - Known code snippets with predetermined correct findings (e.g., a deliberate SQL injection, an obvious unused variable)
   - Expected severity level and finding type for each canary
   - Tolerance threshold for deviation (how different can the response be)
   - Rotation schedule — canaries rotate to prevent memorization

2. **Extend panel-output schema** — Add optional `canary_results`:
   ```json
   "canary_results": {
     "canary_id": "string",
     "expected_finding": "string",
     "actual_finding": "string or null",
     "severity_match": true/false,
     "detection_latency_ms": integer
   }
   ```

3. **Update review prompts** — Inject canary code snippets into security-review and code-review panels:
   - The canary is a small, known-vulnerable code block appended to the review context
   - The panel must identify the known issue; failure to detect it signals evaluation gaming
   - Canary snippets are rotated per `canary-calibration.yaml`

4. **Update startup.md Phase 4** — After collecting panel emissions:
   - Validate canary results against expected findings
   - If a panel misses a canary: flag as potential evaluation gaming
   - If canary detection rate drops below threshold: require human review
   - Track canary results historically for behavioral consistency

5. **Update policy engine** — Process canary results:
   - `canary_pass_rate < 0.70` → `requires_human_review: true`
   - Canary failures are informational (not blocking) in initial rollout
   - Graduate to enforcement after baseline data collected

6. **Write tests** — Validate canary matching logic, pass rate calculation, schema validation

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | policy_engine.py | Canary result validation, pass rate calculation |
| Unit | canary-calibration.yaml | Config schema validation |
| Unit | panel-output schema | canary_results field validation |
| Integration | End-to-end canary flow | Inject canary → panel execution → result validation |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Canary patterns become stale | Medium | Medium | Rotation schedule prevents memorization |
| False positives from canary mismatch | Medium | Low | Advisory-only in initial rollout; threshold tuning |
| LLM adapts to canary detection | Low | High | Canary rotation + varied difficulty levels |

## 7. Dependencies

- [ ] Hallucination detection (#406) — non-blocking (already implemented)
- [ ] Plausibility validation (#404) — non-blocking (already implemented)

## 8. Backward Compatibility

Fully backward compatible. `canary_results` is optional in schema. Existing emissions remain valid. Canary validation is advisory-only initially.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Policy engine and schema changes |
| security-review | Yes | Required by policy; this IS a security mitigation |
| threat-modeling | Yes | Required by policy; addresses LLM behavioral risk |
| cost-analysis | Yes | Required by policy |
| documentation-review | Yes | Startup.md, review prompts, and policy docs updated |
| data-governance-review | Yes | Required by policy |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Advisory-only initial rollout | Need baseline data before enforcement; avoids false-positive blocking |
| 2026-02-26 | Canary rotation over static patterns | Prevents LLM memorization of test inputs |
| 2026-02-26 | Start with security + code review only | Highest value panels; expand after validation |
