# Multi-Model Execution Backend Abstraction and Cost Routing

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/431
**Branch:** NETWORK_ID/feat/431/multi-model-execution

---

## 1. Objective

Add a multi-model execution backend abstraction with per-persona model routing, cost tracking fields in panel output schema, and a cost optimization policy profile.

## 2. Rationale

The system is tightly coupled to Claude Code. Supporting multiple LLM backends enables cost optimization, resilience, and task-appropriate model selection.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Hard-code model list | Yes | Not extensible — new models require code changes |
| Schema-driven backend config | Yes | **Selected** — flexible, declarative, version-controlled |
| Runtime model selection | Yes | Too complex for initial implementation |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/execution-backend.schema.json` | Backend interface definition |
| `governance/policy/cost-optimization.yaml` | Budget threshold rules |
| `docs/architecture/multi-model-execution.md` | Architecture documentation |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/panel-output.schema.json` | Add `token_count` and `estimated_cost_usd` to execution_context |
| `governance/engine/tests/test_schema_validation.py` | Add tests for new schema fields |

### Files to Delete

None.

## 4. Approach

1. Create `governance/schemas/execution-backend.schema.json` defining the backend interface (model_id, provider, context_window, cost_per_1k_input_tokens, cost_per_1k_output_tokens, capabilities)
2. Add `token_count` and `estimated_cost_usd` fields to `execution_context` in panel-output.schema.json
3. Create `governance/policy/cost-optimization.yaml` with budget thresholds per session, per issue, and per panel
4. Create `docs/architecture/multi-model-execution.md` documenting the abstraction layer
5. Add schema validation tests

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | Schema | Validate execution-backend.schema.json accepts valid configs |
| Unit | Panel output | Validate token_count and cost fields work |
| Unit | Cost policy | Validate budget threshold rules |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Schema breaking change | Low | High | New fields are optional in panel-output |
| Cost estimates inaccurate | Medium | Low | Estimates are advisory, not enforcement |

## 7. Dependencies

- None

## 8. Backward Compatibility

All schema additions are optional. Existing emissions remain valid.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Schema changes |
| cost-analysis | Yes | Cost-related changes |
| documentation-review | Yes | Architecture documentation |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Schema-driven not runtime selection | Simpler, declarative, version-controlled |
