# Activate Multi-Model Validation in Production

**Author:** Team Lead (batch-scoped PM mode)
**Date:** 2026-03-02
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/706
**Branch:** itsfwcp/feat/706/multi-model-validation-production

---

## 1. Objective

Activate multi-model validation as a production-ready, opt-in feature. The aggregator and model router already exist but are disabled by default. This change wires them together with the policy engine so that multi-model consensus verdicts contribute to confidence scoring and merge decisions.

## 2. Rationale

The multi_model_aggregator.py and model_router.py already implement the core logic. What is missing is:
- Integration with the policy engine's confidence calculation
- project.yaml-level configuration for consuming repos
- A production multi-model policy profile that is enabled
- Documentation

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Build new aggregator from scratch | Yes | Existing aggregator is well-tested and functional |
| Enable by default for all repos | Yes | Breaking change; opt-in is safer |
| External model orchestration service | Yes | Over-engineering for current needs |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/policy/multi-model.yaml` | Policy profile with multi-model validation enabled (extends default) |
| `governance/engine/multi_model_integration.py` | Integration layer connecting aggregator with policy engine confidence |
| `governance/engine/tests/test_multi_model_integration.py` | Tests for the integration layer |
| `docs/configuration/multi-model-validation.md` | Configuration guide for consuming repos |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/engine/policy_engine.py` | Add hook to call multi-model aggregator when processing emissions; integrate aggregated verdicts into confidence calculation |
| `governance/policy/default.yaml` | Add documentation comments about multi-model config section (keep disabled) |
| `governance/engine/orchestrator/model_router.py` | Add `resolve_multi_model_panel` method that returns list of models for a given panel when multi-model is enabled |
| `governance/engine/multi_model_aggregator.py` | Add `confidence_adjustment` method that applies consensus results to the base confidence score |

### Files to Delete

None.

## 4. Approach

1. **Create `multi_model_integration.py`** — Bridge between `MultiModelAggregator` and the policy engine. Provides a `process_multi_model_emissions()` function that:
   - Takes raw emissions and the `MultiModelConfig`
   - Groups by panel, runs aggregation
   - Returns adjusted confidence scores and verdicts for the policy engine
   - Handles fallback when models are unavailable (cap confidence at 0.7)

2. **Extend `model_router.py`** — Add `resolve_multi_model_panel(panel_name)` method that returns `list[str]` of model IDs when multi-model validation is enabled for that panel

3. **Extend `multi_model_aggregator.py`** — Add `confidence_adjustment()` that returns a multiplier based on consensus strength (unanimous = 1.0, supermajority = 0.95, majority = 0.90, no consensus = 0.7)

4. **Integrate into `policy_engine.py`** — Add a post-processing step after loading emissions that detects multi-model emissions, aggregates them, and adjusts the confidence scores before the standard policy evaluation runs

5. **Create `multi-model.yaml` policy profile** — Copy of default.yaml with `multi_model.enabled: true`, models set to `["claude-opus-4-6", "claude-sonnet-4-6"]`, consensus `majority`, min_models `2`

6. **Write tests** — Cover integration: emissions in -> aggregated confidence out, fallback behavior, policy engine with multi-model profile

7. **Write configuration documentation** — How to enable, configure models, set consensus strategy

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `multi_model_integration.py` | Test confidence adjustment calculations, fallback behavior |
| Unit | `model_router.py` | Test `resolve_multi_model_panel` returns correct model lists |
| Unit | `multi_model_aggregator.py` | Test `confidence_adjustment` method (existing tests + new) |
| Integration | policy engine + aggregator | Test end-to-end: multi-model emissions -> aggregated verdict -> policy decision |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing single-model behavior | Low | High | Disabled by default; integration only activates when config enables it |
| Model API unavailability | Medium | Medium | Fallback to single-model with confidence cap |
| Consensus deadlock | Low | Medium | Non-consensus defaults to human_review_required |

## 7. Dependencies

- [x] `governance/engine/multi_model_aggregator.py` exists (non-blocking)
- [x] `governance/engine/orchestrator/model_router.py` exists (non-blocking)
- [ ] Policy engine must support post-processing hook (will be added)

## 8. Backward Compatibility

Fully backward compatible. Multi-model validation is disabled by default. Existing single-model behavior is unchanged. The new `multi-model.yaml` profile is opt-in.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Core engine changes |
| security-review | Yes | Policy engine modifications affect security decisions |
| threat-modeling | Yes | New trust boundary between models |
| documentation-review | Yes | New configuration documentation |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Opt-in via separate policy profile | Avoid breaking existing consuming repos |
| 2026-03-02 | Default to 2 models minimum | Matches DACH's operational setup while being achievable |
