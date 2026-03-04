# Phase 5a — Self-Proving Systems Governance Artifacts

**Author:** Team Lead (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/158
**Branch:** `NETWORK_ID/feat/158/phase-5a-self-proving`

---

## 1. Objective

Implement Phase 5a governance artifacts: test governance schema, test-generation panel, and proof-of-correctness policy. These define testing expectations that consuming repos enforce via their own CI.

## 2. Rationale

Phase 5a closes a gap in the governance pipeline — test coverage and formal verification are not currently governed. These artifacts establish machine-readable testing requirements that can be evaluated by the policy engine.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Runtime test execution in submodule | Yes | Config-only repo cannot execute tests |
| Test requirements as markdown only | Yes | Not machine-evaluable by policy engine |
| JSON Schema + panel + policy (selected) | Yes | Fits existing governance model — schema for structure, panel for evaluation, policy for enforcement |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/test-governance.schema.json` | JSON Schema for test coverage expectations |
| `governance/personas/panels/test-generation-review.md` | Panel that emits test requirements |
| `governance/emissions/test-generation-review.json` | Baseline emission |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/policy/default.yaml` | Add proof-of-correctness rules as optional panel trigger |
| `GOALS.md` | Check off 5a items, add to completed work |
| `CLAUDE.md` | Update panel count |

## 4. Approach

1. Create test governance schema
2. Create test-generation panel
3. Create baseline emission
4. Add proof-of-correctness policy rules to default.yaml
5. Update documentation

## 5-10. (Standard sections — low risk, no dependencies, additive changes, default policy profile)
