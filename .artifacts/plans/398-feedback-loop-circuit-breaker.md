# Feedback Loop Circuit Breaker

**Author:** Team Lead (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** #398 — D-1: Infinite Feedback Loop
**Branch:** NETWORK_ID/fix/398/feedback-circuit-breaker

---

## 1. Objective

Add a hard limit on total ASSIGN/FEEDBACK cycles across escalation boundaries to prevent unbounded re-assignment loops. Introduce a per-PR circuit breaker that caps total evaluation cycles at 5 (3 Tester cycles + 2 post-escalation re-assignments).

## 2. Rationale

The current protocol limits Tester feedback to 3 cycles, after which BLOCK is emitted. However, the Team Lead can re-assign after escalation, and there is no limit on re-assignments. This creates a potential infinite loop bounded only by context window exhaustion.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Rely on context capacity as backstop | Yes | Context exhaustion is a DoS condition, not a designed safeguard |
| Hard 3-cycle global limit | Yes | Too restrictive; some issues genuinely need a re-attempt after escalation feedback |
| 5-cycle total with mandatory human escalation | Yes | **Selected** — allows 2 post-escalation attempts before hard stop |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/agent-protocol.md` | Add `total_evaluation_cycles` counter (max 5) to the protocol. Add rule: after 5 total cycles across all agents for a single work unit, emit BLOCK with `"reason": "circuit_breaker"` and escalate to human. No further re-assignments permitted. |
| `governance/personas/agentic/team-lead.md` | Add instruction: track total evaluation cycles per work unit. After cycle 5, do not re-assign; escalate to human with full feedback history. |
| `governance/prompts/startup.md` | Add circuit breaker constant and reference in Phase 4 instructions. |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Add `MAX_TOTAL_EVALUATION_CYCLES = 5` constant to agent-protocol.md
2. Define cycle counting: Tester FEEDBACK = +1, Team Lead re-ASSIGN after BLOCK = +1
3. At cycle 5: mandatory BLOCK with `circuit_breaker` reason, human escalation, no further automation
4. Update Team Lead persona to track and enforce the counter
5. Update startup.md Phase 4 to reference the circuit breaker

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | agent-protocol.md | Verify circuit breaker rules are unambiguous |
| Review | team-lead.md | Verify tracking instruction is actionable |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Legitimate issues blocked at cycle 5 | Low | Medium | Human escalation preserves path forward; 5 cycles is generous |
| Agent loses count (prompt compliance) | Medium | Medium | Counter is simple enough for reliable tracking |

## 7. Dependencies

- [ ] None — self-contained

## 8. Backward Compatibility

Additive. New constant and tracking rule. The existing 3-cycle Tester limit is unchanged; this adds a global cap on top.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | DoS defense mechanism |
| code-review | Yes | Protocol change |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | 5-cycle limit chosen | 3 Tester + 2 re-assignments = reasonable exhaustion before human takeover |
