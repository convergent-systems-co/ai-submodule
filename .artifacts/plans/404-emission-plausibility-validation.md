# Emission Plausibility Validation

**Author:** Team Lead (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** #404 — E-5: Policy Engine Bypass via Emission Crafting
**Branch:** NETWORK_ID/fix/404/emission-plausibility-validation

**Author:** Coder (agentic)
**Date:** 2026-02-26
**Status:** in_progress
**Issue:** #404 — E-5: Policy Engine Bypass via Emission Crafting
**Branch:** `NETWORK_ID/fix/404/emission-plausibility-validation`

---

## 1. Objective

Add plausibility validation rules to the policy engine configuration and startup pipeline that detect anomalous panel emissions — emissions that meet auto-merge thresholds but show signs of being crafted or templated rather than genuine analysis.

Add plausibility checks to the default policy profile and startup pipeline to detect anomalous or crafted panel emissions before they can influence auto-merge decisions. This mitigates the risk of an attacker gaming the policy engine by supplying perfectly clean emissions.

## 2. Rationale

Auto-merge conditions require aggregate_confidence >= 0.85, risk_level in ["low", "negligible"], and all verdicts "approve". An attacker influencing LLM output could craft emissions meeting these thresholds. Plausibility checks add a second layer of validation.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| External SAST/DAST alongside LLM panels | Yes | Requires CI integration beyond this repo's scope |
| Hard-disable auto-merge | Yes | Defeats the purpose of autonomous governance |
| Plausibility heuristics in policy profile + startup | Yes | **Selected** — defense-in-depth, configurable, no external deps |

The policy engine evaluates structured emissions deterministically. If an attacker controls emission content, they can craft emissions that satisfy all auto-merge conditions (aggregate_confidence >= 0.85, risk_level in ["low", "negligible"], all verdicts "approve"). There is currently no plausibility checking or baseline comparison to detect suspiciously perfect emissions.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Cryptographic signing of emissions | Yes | Requires infrastructure changes and key management; out of scope for immediate mitigation |
| Baseline statistical comparison | Yes | Requires historical emission data collection not yet available; deferred to future phase |
| Heuristic plausibility checks | Yes | Selected — provides immediate defense with minimal complexity |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |
| `.governance/plans/404-emission-plausibility-validation.md` | This plan file |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/policy/default.yaml` | Add `plausibility_checks` section to auto-merge conditions: minimum findings count for non-trivial PRs, confidence score variance check, execution_trace required when available |
| `governance/prompts/startup.md` | Add plausibility validation step in Phase 4c after panel emissions are collected |
| `governance/policy/default.yaml` | Add `plausibility_checks` section with three heuristic rules; bump version to 1.4.0 |
| `governance/prompts/startup.md` | Add plausibility validation step in Phase 4c before merge decisions |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

N/A — no files are deleted.

## 4. Approach

1. Add `plausibility_checks` to default.yaml auto-merge section:
   - `min_findings_for_nontrivial`: PRs touching >3 files must have at least 1 finding (even informational) — a "zero findings on a large PR" is suspicious
   - `confidence_floor_with_no_trace`: if `execution_trace` is absent, max auto-merge confidence capped at 0.70 (forces human review for emissions without trace evidence)
   - `identical_emission_detection`: flag emissions where all panels produce identical confidence scores (>= 3 panels with same score = anomaly)
2. Add plausibility validation in startup.md Phase 4c:
   - After collecting panel emissions, verify plausibility heuristics before proceeding to merge
   - If anomaly detected: flag for human review, do not auto-merge

1. Add a `plausibility_checks` section to `governance/policy/default.yaml` after the `auto_merge` section, containing three checks:
   - `min_findings_for_nontrivial`: PRs touching >3 files with zero findings are flagged
   - `confidence_cap_without_trace`: Emissions without `execution_trace` get capped confidence at 0.70
   - `identical_score_detection`: 3+ panels with identical confidence scores are flagged as anomalous
2. Bump `profile_version` from 1.3.1 to 1.4.0 (new feature, additive, backward compatible)
3. Add plausibility validation instructions in `governance/prompts/startup.md` Phase 4c, after panel reviews complete and before proceeding to push/merge
4. Create this plan file

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | governance/engine/tests/ | Verify policy engine handles new plausibility fields |
| Manual | default.yaml | Verify heuristics are reasonable and configurable |
| Unit | N/A | No application code; policy is declarative YAML |
| Integration | Policy engine | Future: policy engine should evaluate plausibility_checks when processing emissions |
| E2E | Governance pipeline | Verify that anomalous emissions trigger human review flags during Phase 4c |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Legitimate small PRs flagged | Low | Low | min_findings only applies to >3 file PRs |
| Heuristics too aggressive | Low | Medium | Configurable thresholds; defaults are conservative |
| False positives on legitimate clean PRs | Medium | Low | Thresholds are conservative (3 files, 3 panels); action is flag, not block |
| Plausibility checks not enforced programmatically | Medium | Medium | Checks are documented in policy and startup prompt; programmatic enforcement deferred to policy engine enhancement |
| Backward incompatibility with existing emissions | Low | Low | All changes are additive; existing emissions without execution_trace get capped, not rejected |

## 7. Dependencies

- [ ] #396 execution_trace (merged) — plausibility checks reference execution_trace
- [x] No blocking dependencies — changes are additive to existing policy and startup prompt

## 8. Backward Compatibility

Additive. New fields in policy profile are optional. Existing emissions without execution_trace still work but may trigger human review for high-confidence scores.

All changes are additive. The `plausibility_checks` section is new and does not modify existing policy rules. Existing emissions continue to be evaluated by the standard auto-merge conditions. The plausibility checks add additional validation on top of existing logic.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Policy engine hardening |
| code-review | Yes | Policy profile changes |
| security-review | Yes | This is a security hardening change |
| threat-modeling | Yes | Addresses emission crafting threat |
| cost-analysis | Yes | Required by default profile |
| documentation-review | Yes | Startup prompt changes need review |
| data-governance-review | Yes | Required by default profile |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Heuristic-based over deterministic | Deterministic validation requires external tools; heuristics are deployable now |
| 2026-02-26 | Configurable thresholds | Different repos have different risk profiles |
| 2026-02-26 | Use heuristic plausibility checks rather than cryptographic signing | Immediate mitigation with minimal complexity; signing deferred to future phase |
| 2026-02-26 | Bump profile_version to 1.4.0 | New feature addition per semantic versioning convention for enforcement artifacts |
