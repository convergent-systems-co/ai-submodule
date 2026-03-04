# Self-Approval Prevention — Structural APPROVE Verification

**Author:** Team Lead (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** #402 — E-1: Coder Self-Approval via Prompt Injection
**Branch:** NETWORK_ID/fix/402/self-approval-prevention

---

## 1. Objective

Add structural verification requirements to the APPROVE message that make it programmatically distinguishable from a prompt-injected approval, by requiring the Tester to include specific verifiable evidence in every APPROVE emission.

## 2. Rationale

In Phase A (sequential), the Coder and Tester are the same LLM. A prompt injection in code under review could instruct the LLM to emit APPROVE when operating as Tester. Current defenses are prompt-level only. This adds structural requirements to APPROVE that are verifiable by the Team Lead.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Separate LLM instances for Coder and Tester | Yes | Requires infrastructure changes beyond repo scope |
| Cryptographic signing of APPROVE | Yes | LLM cannot hold secrets; not implementable |
| Structural evidence requirements in APPROVE | Yes | **Selected** — verifiable by Team Lead, no infrastructure changes |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/agent-protocol.md` | Add "APPROVE Verification Requirements" section: every APPROVE must include a test_gate_output hash, files_reviewed list, and acceptance_criteria_checklist |
| `governance/personas/agentic/tester.md` | Add structural emission requirements to the APPROVE output format |
| `governance/personas/agentic/team-lead.md` | Add APPROVE verification step: Team Lead must cross-reference APPROVE evidence against actual artifacts before accepting |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Add "APPROVE Verification Requirements" to agent-protocol.md:
   - APPROVE payload must include: `test_gate_passed` (boolean), `files_reviewed` (array, must match PR diff), `acceptance_criteria_met` (array of criteria with pass/fail), `coverage_percentage` (number from actual gate output)
   - Team Lead must verify: `files_reviewed` matches `git diff --name-only`, `acceptance_criteria_met` covers all issue acceptance criteria, `test_gate_passed` is consistent with CI status
   - An APPROVE missing any required field is treated as invalid and rejected
2. Update Tester persona:
   - Add required fields to the APPROVE emission format
   - Add instruction: "The APPROVE payload must be grounded in actual tool output. Do not emit APPROVE without having run the Test Coverage Gate and verified each acceptance criterion."
3. Update Team Lead persona:
   - Add verification step before accepting APPROVE: cross-reference files_reviewed against PR diff, verify acceptance criteria coverage
   - If verification fails, treat as FEEDBACK (request re-evaluation), not APPROVE

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | agent-protocol.md | Verify requirements are unambiguous |
| Manual | tester.md | Verify emission format is complete |
| Review | team-lead.md | Verify verification logic is actionable |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM fabricates evidence in APPROVE | Medium | High | Team Lead cross-references against actual artifacts |
| Legitimate APPROVE rejected due to strict format | Low | Medium | Clear format specification reduces ambiguity |

## 7. Dependencies

- [ ] None — self-contained

## 8. Backward Compatibility

Additive. Extends existing APPROVE format with required fields. Existing protocol behavior unchanged.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Core security hardening |
| code-review | Yes | Protocol changes |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Structural evidence over cryptographic | LLM cannot hold secrets; structural evidence is verifiable |
| 2026-02-26 | Team Lead as verifier | Team Lead already orchestrates; natural verification point |
