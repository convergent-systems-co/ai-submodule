# OWASP LLM Top 10 Coverage Matrix

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/427
**Branch:** NETWORK_ID/feat/427/owasp-llm-top10-mapping

---

## 1. Objective

Create a documented mapping between OWASP LLM Top 10 (2025) risks and the dark-forge's governance controls, demonstrating compliance coverage and identifying gaps.

## 2. Rationale

The platform addresses several OWASP risks implicitly but has no explicit mapping. This is a low-effort, high-value documentation task for auditors.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Spreadsheet | Yes | Not version-controlled |
| Markdown mapping doc | Yes | **Selected** — auditable, version-controlled, referenceable |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `docs/compliance/owasp-llm-top10-mapping.md` | Full mapping of all 10 risks to governance controls |

### Files to Modify

None.

### Files to Delete

None.

## 4. Approach

1. Create `docs/compliance/owasp-llm-top10-mapping.md` mapping each of the 10 OWASP LLM risks to specific governance controls:
   - For each risk: panels that detect it, policy rules that enforce it, schema fields that capture it, persona guardrails that prevent it
   - Identify gaps with mitigation recommendations
2. Cross-reference from existing docs

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Review | Verify accuracy of control mappings |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Incomplete mapping | Low | Low | Follow OWASP checklist systematically |

## 7. Dependencies

None.

## 8. Backward Compatibility

Documentation only — no compatibility concerns.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Security documentation |
| documentation-review | Yes | New documentation |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Single comprehensive doc | All 10 risks in one referenceable file |
