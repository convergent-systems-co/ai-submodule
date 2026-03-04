# Prompt Red-Teaming and Adversarial Canary Validation

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/434
**Branch:** NETWORK_ID/feat/434/red-team-canary-validation

---

## 1. Objective

Create a red-team canary dataset with adversarial code samples to test panel resistance to prompt injection and manipulation, extending the existing canary calibration system.

## 2. Rationale

The canary calibration system tests detection of known issues but not resistance to adversarial manipulation. OWASP LLM01 (Prompt Injection) is the top-ranked LLM risk.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Promptfoo red-team integration | Yes | External dependency |
| Custom adversarial dataset | Yes | **Selected** — extends existing canary system, no new deps |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/evals/red-team/README.md` | Red-team dataset documentation |
| `governance/evals/red-team/fake-approval-comments.yaml` | Adversarial: fake security approval in comments |
| `governance/evals/red-team/misleading-docs.yaml` | Adversarial: misleading docstrings |
| `governance/evals/red-team/obfuscated-vulns.yaml` | Adversarial: obfuscated vulnerabilities |
| `governance/evals/red-team/protocol-injection.yaml` | Adversarial: agent protocol message injection |
| `docs/guides/red-team-validation.md` | User-facing documentation |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/policy/canary-calibration.yaml` | Add red-team section extending existing canary config |

### Files to Delete

None.

## 4. Approach

1. Create `governance/evals/red-team/` directory with README
2. Create 4 adversarial YAML datasets, each with test cases containing adversarial code and expected panel behavior
3. Extend `canary-calibration.yaml` with a `red_team` section for adversarial pass rate tracking
4. Create documentation in `docs/guides/red-team-validation.md`

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Dataset review | Verify adversarial samples are realistic |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Adversarial samples too easy | Medium | Low | Include sophisticated obfuscation patterns |

## 7. Dependencies

- Canary calibration system (existing)

## 8. Backward Compatibility

Additive — new files and optional canary-calibration.yaml section.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Security testing framework |
| documentation-review | Yes | New documentation |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Extend canary system not new framework | Leverage existing infrastructure |
