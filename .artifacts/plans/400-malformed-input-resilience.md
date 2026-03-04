# Malformed Input Resilience — Graceful Degradation for Bad Issue Bodies and Plans

**Author:** Team Lead (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** #400 — D-3: Malformed Issue or Plan Crashing the Pipeline
**Branch:** NETWORK_ID/fix/400/malformed-input-resilience

---

## 1. Objective

Add input validation and graceful degradation rules to the startup pipeline so that malformed issue bodies or corrupted plan files cause the affected issue to be skipped with a warning rather than crashing the entire pipeline.

Prevent malformed issue bodies and invalid plan files from crashing the agentic pipeline. Ensure that input validation failures are isolated to the affected work unit and do not cascade to other issues or plans being processed in the same session.

## 2. Rationale

A malformed issue body (missing required sections, invalid encoding) or a corrupted plan file (invalid markdown, missing required sections) can cause the agent to enter an error state. Currently, there's no graceful degradation — a parse failure in one issue can halt all work.

The pipeline currently lacks input sanitization on issue body content, has no schema validation for plan files, and has no graceful degradation for parse failures. A single malformed issue or tampered plan can put the agent into an error state, blocking all remaining work in the session.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| JSON Schema for plan files | Yes | Plans are markdown; schema validation adds tool dependency |
| Strict input sanitization | Yes | Overly aggressive; destroys legitimate content |
| Structural validation + skip-on-failure | Yes | **Selected** — lightweight, preserves pipeline continuity |
| JSON schema validation for issue bodies | Yes | Issue bodies are freeform markdown — schema validation is not applicable. Content validation (non-empty, no control characters, readable content) is more appropriate. |
| Strict plan schema enforcement via JSON Schema | Yes | Plans are markdown files, not JSON. Section-header validation is the right level of enforcement for markdown-based plans. |
| Retry with exponential backoff | Yes | Malformed input is not a transient failure — retrying the same bad input will produce the same error. A cap of 2 attempts with BLOCK is more appropriate. |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |
| `.governance/plans/400-malformed-input-resilience.md` | This plan file |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Add error isolation rules in Phase 1d (issue validation) and Phase 2b (intent validation): malformed issues are labeled `malformed-input` and skipped. Add plan file structural validation in Phase 2d. |
| `governance/prompts/agent-protocol.md` | Add "Error Isolation" section: a failure on one work unit must not cascade to other work units |
| `governance/prompts/startup.md` | Add issue body validation in Phase 1d (after size check); add plan structural validation in Phase 2d (after plan creation) |
| `governance/prompts/agent-protocol.md` | Add "Error Isolation" section defining mandatory rules for failure isolation across work units |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |
| N/A | No files to delete |

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

1. **Add Issue Body Validation to Phase 1d** — Insert a new "Issue Body Validation" subsection after the existing "Issue Body Size Check" in `startup.md`. Validate that the body is not empty/null, contains no null bytes or control characters, and has at least one readable sentence (>10 non-whitespace characters). On failure: label `malformed-input`, comment, skip, and continue to next issue.

2. **Add Plan Validation to Phase 2d** — After the plan creation step in Phase 2d, add structural validation checking for required sections (Objective, Scope, Approach). On failure: warn and re-create. After 2 failed attempts: emit BLOCK and skip to next issue.

3. **Add Error Isolation section to agent-protocol.md** — Define five mandatory rules: independent processing, unrecoverable error handling (BLOCK + label), no single-input crashes, parallel dispatch failure isolation, and a 2-retry cap per work unit.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | startup.md | Verify validation rules are clear and ordered correctly |
| Manual | agent-protocol.md | Verify error isolation rules are unambiguous |
| Manual review | All modified files | Verify that the new sections are syntactically correct markdown and logically consistent with existing content |
| Integration | Pipeline behavior | The next agentic session encountering a malformed issue will exercise the new validation rules |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Legitimate issues with unusual formatting skipped | Low | Low | Validation targets clear malformation, not style |
| Label creation fails | Low | Low | Non-blocking; issue is still skipped |
| Overly aggressive validation skips valid issues | Low | Medium | Validation checks are conservative (null bytes, truly empty bodies) — normal issues will not be affected |
| Label creation fails if `malformed-input` label does not exist | Medium | Low | Labeling is advisory and non-blocking — failure to label does not block the skip |

## 7. Dependencies

- [ ] None — self-contained
- [ ] None — all changes are additive to existing cognitive artifacts

## 8. Backward Compatibility

Additive. New validation rules and error isolation. No existing behavior changes for well-formed inputs.

All changes are additive. No existing behavior is removed or altered. Existing issues with valid bodies and existing plans with correct structure are unaffected. The new validation steps only activate for inputs that would previously have caused errors.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Input validation is a security concern |
| code-review | Yes | Pipeline resilience changes |
| security-review | Yes | This is a security hardening change addressing input validation |
| documentation-review | Yes | Cognitive artifacts (prompts) are being modified |
| threat-modeling | Yes | Addresses a specific threat (malformed input crashing pipeline) |
| cost-analysis | Yes | Required by default policy |
| data-governance-review | Yes | Required by default policy |

**Policy Profile:** default
**Expected Risk Level:** low

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Skip-on-failure over halt-on-failure | Pipeline continuity is more valuable than strict validation |
| 2026-02-26 | Label + comment on malformed issues | Provides visibility without blocking legitimate work |
| 2026-02-26 | Use content validation (not schema) for issue bodies | Issue bodies are freeform markdown; schema validation is not applicable |
| 2026-02-26 | Cap retries at 2 per work unit | Malformed input is not transient; unlimited retries waste context |
| 2026-02-26 | Make labeling advisory (non-blocking) | Permission errors on label operations should not block the pipeline |
