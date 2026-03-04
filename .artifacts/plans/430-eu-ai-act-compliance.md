# EU AI Act Risk Classification and Regulatory Compliance Mapping

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/430
**Branch:** NETWORK_ID/feat/430/eu-ai-act-compliance

---

## 1. Objective

Add EU AI Act risk tier classification to panel output schema, model provenance fields, and create compliance mapping documentation for EU AI Act, NIST AI RMF, and ISO/IEC 42001.

## 2. Rationale

EU AI Act enforcement for high-risk AI systems is August 2, 2026 — 5 months away. The platform's risk levels don't map to the Act's four-tier system. This is a P0 compliance deadline.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Separate compliance schema | Yes | Fragments the audit trail |
| Add to panel-output.schema.json | Yes | **Selected** — keeps compliance data with the assessment |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `docs/compliance/eu-ai-act-mapping.md` | EU AI Act risk tier mapping |
| `docs/compliance/nist-ai-rmf-mapping.md` | NIST AI RMF function mapping |
| `docs/compliance/iso-42001-mapping.md` | ISO/IEC 42001 clause mapping |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/panel-output.schema.json` | Add `ai_act_risk_tier` field; add model provenance to execution_context |

### Files to Delete

None.

## 4. Approach

1. Add `ai_act_risk_tier` (enum: unacceptable, high, limited, minimal) to panel-output.schema.json
2. Add model provenance fields to execution_context: `model_hash`, `provider`, `version_date`
3. Create EU AI Act mapping doc with risk tier table
4. Create NIST AI RMF mapping doc (Govern, Map, Measure, Manage → governance layers)
5. Create ISO 42001 mapping doc (clauses 4-10 → governance artifacts)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | Schema | Validate new fields accept valid values |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Mapping inaccuracies | Medium | Medium | Cross-reference official Act text |

## 7. Dependencies

None.

## 8. Backward Compatibility

All schema additions are optional. Fully backward compatible.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Schema changes |
| documentation-review | Yes | Compliance documentation |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Add to panel-output not separate schema | Keeps compliance data co-located |
