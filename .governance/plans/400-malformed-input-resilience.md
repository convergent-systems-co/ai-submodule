# Malformed Input Resilience — Graceful Degradation for Bad Issue Bodies and Plans

**Author:** Code Manager (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** #400 — D-3: Malformed Issue or Plan Crashing the Pipeline
**Branch:** itsfwcp/fix/400/malformed-input-resilience

---

## 1. Objective

Add input validation and graceful degradation rules to the startup pipeline so that malformed issue bodies or corrupted plan files cause the affected issue to be skipped with a warning rather than crashing the entire pipeline.

## 2. Rationale

A malformed issue body (missing required sections, invalid encoding) or a corrupted plan file (invalid markdown, missing required sections) can cause the agent to enter an error state. Currently, there's no graceful degradation — a parse failure in one issue can halt all work.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| JSON Schema for plan files | Yes | Plans are markdown; schema validation adds tool dependency |
| Strict input sanitization | Yes | Overly aggressive; destroys legitimate content |
| Structural validation + skip-on-failure | Yes | **Selected** — lightweight, preserves pipeline continuity |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Add error isolation rules in Phase 1d (issue validation) and Phase 2b (intent validation): malformed issues are labeled `malformed-input` and skipped. Add plan file structural validation in Phase 2d. |
| `governance/prompts/agent-protocol.md` | Add "Error Isolation" section: a failure on one work unit must not cascade to other work units |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Add issue body validation in startup.md Phase 1d:
   - Check for empty body: skip and label `malformed-input`
   - Check for encoding issues (null bytes, control characters): skip and label
   - Check for minimum structure: body must contain at least one sentence describing the problem
   - Validation failures: label issue, comment explaining the problem, skip to next issue
2. Add plan structural validation in startup.md Phase 2d:
   - Before dispatching to Coder, verify plan file has required sections (Objective, Scope, Approach)
   - If plan is malformed: warn and re-create the plan
3. Add "Error Isolation" to agent-protocol.md:
   - Rule: a failure processing one work unit (issue, PR, plan) must not prevent processing of other work units
   - Rule: on unrecoverable error for a work unit, emit BLOCK with reason, label the issue, and continue with remaining work
   - Rule: never allow a single bad input to crash the pipeline or exhaust the context window

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | startup.md | Verify validation rules are clear and ordered correctly |
| Manual | agent-protocol.md | Verify error isolation rules are unambiguous |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Legitimate issues with unusual formatting skipped | Low | Low | Validation targets clear malformation, not style |
| Label creation fails | Low | Low | Non-blocking; issue is still skipped |

## 7. Dependencies

- [ ] None — self-contained

## 8. Backward Compatibility

Additive. New validation rules and error isolation. No existing behavior changes for well-formed inputs.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Input validation is a security concern |
| code-review | Yes | Pipeline resilience changes |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Skip-on-failure over halt-on-failure | Pipeline continuity is more valuable than strict validation |
| 2026-02-26 | Label + comment on malformed issues | Provides visibility without blocking legitimate work |
