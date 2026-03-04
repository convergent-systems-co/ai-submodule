# Escalation Audit Trail and Human Decision Capture

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/436
**Branch:** NETWORK_ID/feat/436/escalation-audit-trail

---

## 1. Objective

Add an `escalation_chain` array to `run-manifest.schema.json` that captures every automated-to-human handoff with timestamps, reasons, and human decisions. Create supporting documentation for escalation audit trail governance.

## 2. Rationale

SOC 2 compliance requires defensible audit trails for automated decisions. GDPR Article 22 requires meaningful information about automated decision logic. The current run manifest schema lacks escalation chain tracking.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Separate escalation log file | Yes | Fragments the audit trail — escalations should live with the merge decision |
| Add to panel-output.schema.json | Yes | Escalations are merge-level events, not panel-level |
| Add to run-manifest.schema.json | Yes | **Selected** — escalations are part of the merge decision record |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `docs/governance/escalation-audit-trail.md` | Documentation for escalation chain recording and compliance |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/run-manifest.schema.json` | Add `escalation_chain` array with escalation event schema |
| `governance/engine/tests/test_schema_validation.py` | Add tests for escalation chain in manifest validation |

### Files to Delete

None.

## 4. Approach

1. Add `escalation_chain` property to `run-manifest.schema.json` with typed escalation events (timestamp, source_agent, target_role, reason, human_decision, justification, decision_timestamp)
2. Add `override_tracking` sub-object for when humans override policy engine decisions
3. Write tests validating escalation chain schema structure
4. Create documentation explaining the escalation audit trail

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | Schema validation | Validate escalation_chain accepts valid events, rejects malformed |
| Unit | Policy engine | Test escalation events are recorded during evaluation |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Schema breaking change | Low | High | Additive only — escalation_chain is optional |
| Missing escalation events | Medium | Medium | Documentation clearly defines when events must be created |

## 7. Dependencies

- None — additive schema change

## 8. Backward Compatibility

Fully backward compatible. `escalation_chain` is optional in the schema. Existing manifests without it remain valid.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Schema changes need security review |
| documentation-review | Yes | New documentation |
| code-review | Yes | Schema and test changes |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Add to run-manifest not panel-output | Escalations are merge-level events |
