# Add Structured JSON Logging to Orchestrator Engine

**Author:** Project Manager (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #683
**Branch:** itsfwcp/feat/683/structured-json-logging

---

## 1. Objective

Extend the existing AuditLog infrastructure to produce structured JSON logs for all orchestrator operations, enabling debugging and observability.

## 2. Rationale

The orchestrator already has `AuditLog` with hash-chained JSONL but it's not fully activated across all operations. Need to add log points at phase transitions, signal processing, dispatch, and gate evaluations.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| New logging framework | Yes | AuditLog already exists and is well-designed |
| Extend existing AuditLog | Yes — chosen | Minimal new code, leverages hash-chaining |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/engine/orchestrator/step_runner.py` | Add audit logging at all phase transitions, signal recording, dispatch events |
| `governance/engine/orchestrator/audit.py` | Add convenience methods for common event types |

## 4. Approach

1. Add typed event helper methods to AuditLog (e.g., `log_phase_transition`, `log_signal`, `log_dispatch`)
2. Instrument step_runner with logging at every state change
3. Ensure logs persist to `.governance/state/agent-log/`

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | audit.py | New helper methods |
| Unit | step_runner.py | Verify events are recorded |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Performance impact of logging | Low | Low | JSONL append is fast |

## 7. Dependencies

- [ ] None

## 8. Backward Compatibility

Additive only — no existing behavior changes.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Engine modification |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Extend AuditLog rather than new framework | Avoids duplication |
