# Panel Execution Blocking Defense

**Author:** Team Lead (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/401
**Branch:** NETWORK_ID/fix/401/panel-execution-timeout

---

## 1. Objective

Prevent the governance pipeline from blocking indefinitely when required panels cannot execute (LLM refusal, rate limiting, timeout). Add timeout, fallback-to-baseline, and circuit breaker mechanisms for panel execution failures.

## 2. Rationale

Currently, if a required panel fails to produce an emission, the pipeline blocks indefinitely with no recovery path. The policy engine treats missing panels as a hard block (`required_panel_missing`). This creates a denial-of-service vector and blocks legitimate merges.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Skip missing panels entirely | Yes | Violates governance policy; panels exist for a reason |
| Fallback to baseline only | Yes | Incomplete — needs timeout detection and circuit breaker too |
| Timeout + fallback + circuit breaker (chosen) | Yes | Comprehensive defense-in-depth approach |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/policy/panel-timeout.yaml` | Timeout and fallback configuration for panel execution |
| `governance/engine/tests/test_panel_timeout.py` | Tests for timeout and fallback logic |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/panel-output.schema.json` | Add optional `execution_status` field (success/timeout/error/fallback) |
| `governance/policy/default.yaml` | Add `panel_execution` section with timeout and fallback config |
| `governance/engine/policy_engine.py` | Handle `execution_status` in emission evaluation; reduce confidence for fallback emissions |
| `governance/prompts/startup.md` | Add timeout handling in Phase 4c panel execution; fallback to baseline emissions on failure |
| `governance/policy/circuit-breaker.yaml` | Extend circuit breaker to cover panel execution failures (not just remediation loops) |

### Files to Delete

| File | Reason |
|------|--------|
| None | N/A |

## 4. Approach

1. **Add `execution_status` to panel-output schema** — New optional enum field: `success`, `timeout`, `error`, `fallback`. Existing emissions without this field default to `success` (backward compatible).

2. **Create `panel-timeout.yaml`** — Configuration:
   - `default_timeout_minutes: 5` — per-panel execution timeout
   - `max_retries: 1` — retry once on timeout before fallback
   - `fallback_strategy: baseline` — use baseline emissions from `governance/emissions/`
   - `fallback_confidence_cap: 0.50` — cap confidence at 0.50 for fallback emissions
   - `per_panel_overrides` — allow panel-specific timeout values

3. **Add `panel_execution` section to `default.yaml`** — Policy rules for timeout handling:
   - Fallback emissions are treated as low-confidence and cannot trigger auto-merge
   - More than 2 fallback emissions in a single PR → `human_review_required`
   - Panel timeout is a distinct failure mode from content quality

4. **Update policy engine** — Handle `execution_status`:
   - `success` → normal evaluation
   - `timeout` or `error` → if fallback available, load baseline with capped confidence
   - `fallback` → apply confidence cap from policy config
   - Log execution failures for retrospective analysis

5. **Update startup.md Phase 4c** — Add panel execution timeout handling:
   - Set a wall-clock timeout for each panel invocation
   - On timeout: attempt retry (1x), then fall back to baseline emission
   - Mark fallback emissions with `execution_status: fallback`
   - Continue evaluation pipeline with reduced confidence

6. **Extend circuit breaker** — Add panel execution failure tracking:
   - Track consecutive panel failures per panel type
   - After `failure_threshold` consecutive failures for same panel: trip circuit
   - Tripped circuit → skip panel, use baseline, escalate to human

7. **Write tests** — Cover timeout logic, fallback loading, confidence capping, circuit breaker tripping

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | policy_engine.py | execution_status handling, confidence capping for fallback emissions |
| Unit | panel-timeout.yaml | Configuration validation, per-panel overrides |
| Unit | circuit-breaker.yaml | Panel failure tracking, circuit trip/reset |
| Integration | startup.md flow | End-to-end timeout → fallback → evaluation flow |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Baseline emissions are stale | Medium | Medium | Confidence cap ensures fallback cannot auto-merge |
| Timeout too aggressive | Low | Medium | Configurable per-panel; default 5 min is generous |
| Circuit breaker masks real failures | Low | Medium | Human escalation on trip; cooldown allows recovery |

## 7. Dependencies

- [ ] Baseline emissions must exist for all required panels — non-blocking (they already exist in governance/emissions/)

## 8. Backward Compatibility

Fully backward compatible. `execution_status` is optional in schema (defaults to `success`). Existing emissions and policy engine behavior unchanged. New functionality is additive.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Policy engine changes |
| security-review | Yes | Required by policy |
| threat-modeling | Yes | Required by policy; this IS a threat mitigation |
| cost-analysis | Yes | Required by policy |
| documentation-review | Yes | Startup.md and policy docs updated |
| data-governance-review | Yes | Required by policy |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | 5-minute default timeout | Generous enough for LLM panel execution; prevents indefinite blocks |
| 2026-02-26 | Confidence cap at 0.50 for fallback | Ensures fallback emissions never auto-merge; requires human review |
| 2026-02-26 | Extend existing circuit breaker vs new file | Reuses proven pattern; consistent configuration location |
