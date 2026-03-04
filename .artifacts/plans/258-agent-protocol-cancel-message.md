# feat(agent-protocol): add CANCEL message type and session lifecycle improvements

**Author:** Team Lead (agent)
**Date:** 2026-02-25
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/258
**Branch:** NETWORK_ID/feat/258/agent-protocol-cancel-message

---

## 1. Objective

Add a CANCEL message type to the agent protocol and formalize session lifecycle enforcement rules — cycle limits, message ordering guarantees, and concrete context capacity thresholds — so that the DevOps Engineer can cleanly signal shutdown to all downstream agents.

## 2. Rationale

The agent protocol currently has no mechanism for the DevOps Engineer to signal "stop work" to the Team Lead or for the Team Lead to propagate cancellation to workers. When context pressure triggers shutdown, agents have no structured message to communicate this. Cycle limit enforcement (max 3 FEEDBACK cycles) is implied but not specified as a protocol rule.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Reuse ESCALATE for cancellation | Yes | ESCALATE signals upward (worker→orchestrator); CANCEL signals downward (orchestrator→worker). Different semantics. |
| Add TIMEOUT as separate type | Yes | Redundant with CANCEL — timeout is one reason for cancellation, not a distinct message type. Include `reason` field in CANCEL payload instead. |
| No protocol change, rely on runtime | Yes | Phase B multi-session transport needs explicit cancellation; inline-only workarounds don't scale. |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files needed |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/agent-protocol.md` | Add CANCEL message type section, update valid transition map, add Protocol Enforcement Rules section, add Message Guarantees section |
| `governance/schemas/agent-message.schema.json` | Add `CANCEL` to `message_type` enum |
| `governance/personas/agentic/devops-engineer.md` | Add CANCEL emission logic with concrete numeric thresholds |
| `governance/personas/agentic/team-lead.md` | Add CANCEL handling — propagate to workers, clean up in-flight work |
| `governance/personas/agentic/coder.md` | Add CANCEL response behavior — commit/stash, report partial progress |
| `governance/personas/agentic/tester.md` | Add CANCEL response behavior — abort evaluation, report partial results |
| `governance/personas/agentic/iac-engineer.md` | Add CANCEL response behavior — same pattern as Coder |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. **Update agent-message.schema.json** — Add `CANCEL` to the `message_type` enum
2. **Add CANCEL section to agent-protocol.md** — Define payload schema (`reason`, `context_signal`, `graceful`), valid senders (DE→CM, CM→CO, CM→IAC, CM→TE), and behavior contract
3. **Add Protocol Enforcement Rules section to agent-protocol.md** — Formalize cycle limit enforcement (max 3 FEEDBACK cycles → BLOCK → ESCALATE), CANCEL idempotency, and message priority
4. **Add Message Guarantees section to agent-protocol.md** — Define ordering (CANCEL supersedes in-flight messages), idempotency (deduplicated by correlation_id + source + target), and delivery semantics per transport phase
5. **Update transition map** in agent-protocol.md — Add CANCEL arrows DE→CM, CM→CO, CM→IAC, CM→TE
6. **Update DevOps Engineer persona** — Add concrete context thresholds table (tool calls, chat turns, issues completed) and CANCEL emission trigger
7. **Update Team Lead persona** — Add CANCEL handling: on receipt, propagate CANCEL to all in-flight workers, wait for partial results, enter shutdown
8. **Update worker personas (Coder, IaC Engineer, Tester)** — Add CANCEL response: commit current state, emit partial RESULT, stop

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | `governance/schemas/agent-message.schema.json` | Validate CANCEL message passes schema; validate old messages still pass |
| Manual review | All modified files | Verify transition map is consistent, no orphaned references |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking schema change | Low | Medium | Additive only — adding enum value, not removing |
| Inconsistent persona updates | Medium | Low | Review all 7 persona files for consistent CANCEL handling |

## 7. Dependencies

- [x] No blocking dependencies — all changes are additive to existing protocol

## 8. Backward Compatibility

Fully additive. The CANCEL message type is a new enum value. Existing message types and transitions are unchanged. Agents that don't implement CANCEL handling will simply never receive CANCEL messages (Phase A single-session agents don't need it since the orchestrator controls flow directly).

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Protocol changes affect agent communication security |
| documentation-review | Yes | Core protocol documentation update |
| threat-modeling | Yes | New message type could be misused in Phase B |
| cost-analysis | Yes | Required by default profile |
| data-governance-review | Yes | Required by default profile |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Use CANCEL instead of TIMEOUT | CANCEL is more general; timeout is a reason, not a message type |
| 2026-02-25 | Include `graceful` boolean in payload | Allows differentiation between "finish current step then stop" vs "stop immediately" |
