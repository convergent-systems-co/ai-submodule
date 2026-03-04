# Governance Decision Auditability — Persistent Agent Message Log

**Author:** Team Lead (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** #397 — R-1: Governance Decision Auditability Gap
**Branch:** NETWORK_ID/fix/397/agent-message-audit-log

---

## 1. Objective

Create a durable agent message log that persists agent protocol messages (ASSIGN, APPROVE, FEEDBACK, BLOCK, ESCALATE, etc.) to `.governance/state/agent-log/` as JSONL files, providing a persistent audit trail that survives context window compaction.

## 2. Rationale

Agent protocol messages currently exist only as inline HTML comment markers in the LLM context window. When the session ends or context compacts, these messages are lost. This means an APPROVE decision has no durable record.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Log to issue comments | Yes | Pollutes issue threads; rate-limited by GitHub API |
| Log to git commits | Yes | Too many commits; clutters history |
| JSONL file per session in .governance/state/ | Yes | **Selected** — lightweight, append-only, git-tracked, queryable |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/agent-log-entry.schema.json` | JSON Schema for agent log entries |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/agent-protocol.md` | Add Phase A persistent logging instruction: after emitting each agent message, append a JSONL entry to `.governance/state/agent-log/{session-id}.jsonl` |
| `governance/prompts/startup.md` | Add session-id generation at Phase 0 (timestamp-based). Add log file creation. Add instruction to commit agent log with PR. |
| `config.yaml` | Add `.governance/state/agent-log` to project_directories if not already covered |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Create `agent-log-entry.schema.json` defining: `timestamp`, `session_id`, `message_type`, `source_agent`, `target_agent`, `correlation_id`, `summary` (truncated payload, max 500 chars)
2. Update `agent-protocol.md` to add a "Persistent Logging" section instructing agents to append to the session log file after each message emission
3. Update `startup.md` Phase 0 to generate a session ID (`YYYYMMDD-session-N`) and create the log file
4. Update `startup.md` Phase 5 to commit the agent log file with the PR or as part of the merge commit

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema | agent-log-entry.schema.json | Validate schema is well-formed JSON Schema |
| Manual | agent-protocol.md | Verify logging instruction is clear and positioned correctly |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Log file grows large in long sessions | Medium | Low | Truncate payload to 500 chars; JSONL is line-based and streamable |
| Agent forgets to log (prompt compliance) | Medium | Medium | This is a prompt-level defense; schema validation on commit can catch missing logs |

## 7. Dependencies

- [ ] None — self-contained

## 8. Backward Compatibility

Additive. New schema file, new directory, new instructions. No existing behavior changes.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Audit trail is a security feature |
| code-review | Yes | Schema and prompt changes |
| documentation-review | Yes | Protocol documentation update |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | JSONL over structured JSON | Append-only, line-oriented, git-friendly |
| 2026-02-26 | 500 char payload truncation | Prevents log bloat while preserving decision context |
