# Emission Plausibility Validation

**Author:** Code Manager (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** #404 — E-5: Policy Engine Bypass via Emission Crafting
**Branch:** itsfwcp/fix/404/emission-plausibility-validation

---

## 1. Objective

Add plausibility validation rules to the policy engine configuration and startup pipeline that detect anomalous panel emissions — emissions that meet auto-merge thresholds but show signs of being crafted or templated rather than genuine analysis.

## 2. Rationale

Auto-merge conditions require aggregate_confidence >= 0.85, risk_level in ["low", "negligible"], and all verdicts "approve". An attacker influencing LLM output could craft emissions meeting these thresholds. Plausibility checks add a second layer of validation.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| External SAST/DAST alongside LLM panels | Yes | Requires CI integration beyond this repo's scope |
| Hard-disable auto-merge | Yes | Defeats the purpose of autonomous governance |
| Plausibility heuristics in policy profile + startup | Yes | **Selected** — defense-in-depth, configurable, no external deps |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/policy/default.yaml` | Add `plausibility_checks` section to auto-merge conditions: minimum findings count for non-trivial PRs, confidence score variance check, execution_trace required when available |
| `governance/prompts/startup.md` | Add plausibility validation step in Phase 4c after panel emissions are collected |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Add `plausibility_checks` to default.yaml auto-merge section:
   - `min_findings_for_nontrivial`: PRs touching >3 files must have at least 1 finding (even informational) — a "zero findings on a large PR" is suspicious
   - `confidence_floor_with_no_trace`: if `execution_trace` is absent, max auto-merge confidence capped at 0.70 (forces human review for emissions without trace evidence)
   - `identical_emission_detection`: flag emissions where all panels produce identical confidence scores (>= 3 panels with same score = anomaly)
2. Add plausibility validation in startup.md Phase 4c:
   - After collecting panel emissions, verify plausibility heuristics before proceeding to merge
   - If anomaly detected: flag for human review, do not auto-merge

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | governance/engine/tests/ | Verify policy engine handles new plausibility fields |
| Manual | default.yaml | Verify heuristics are reasonable and configurable |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Legitimate small PRs flagged | Low | Low | min_findings only applies to >3 file PRs |
| Heuristics too aggressive | Low | Medium | Configurable thresholds; defaults are conservative |

## 7. Dependencies

- [ ] #396 execution_trace (merged) — plausibility checks reference execution_trace

## 8. Backward Compatibility

Additive. New fields in policy profile are optional. Existing emissions without execution_trace still work but may trigger human review for high-confidence scores.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Policy engine hardening |
| code-review | Yes | Policy profile changes |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Heuristic-based over deterministic | Deterministic validation requires external tools; heuristics are deployable now |
| 2026-02-26 | Configurable thresholds | Different repos have different risk profiles |
