# Fix Agentic Loop: PR Monitoring, Copilot Review Handling, and Merge Lifecycle

**Author:** Coder (agentic)
**Date:** 2026-02-21
**Status:** completed
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/22
**Branch:** NETWORK_ID/22-fix-agentic-loop

---

## 1. Objective

Complete the agentic startup loop so the agent follows the full PR lifecycle: push, monitor checks, parse Copilot recommendations, implement or dismiss each recommendation, update the issue, get the branch merge-ready, merge, and repeat. Also ensure in-session work creates issues before execution.

## 2. Rationale

The current startup.md Step 7 "Review Loop" is skeletal — it says "invoke the appropriate panel" but has no implementation for monitoring PR checks, handling Copilot feedback, iterating on recommendations, updating issues, or executing merges. This means the agent creates PRs and abandons them.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Create a separate workflow file for PR monitoring | Yes | The monitoring logic belongs in the agentic loop itself, not a CI workflow — the agent must be the actor |
| Add monitoring only to startup.md | Yes | Insufficient — the personas also need updated responsibilities to match |
| Rewrite the entire governance system | Yes | Over-engineering — the framework is sound, only the loop execution is incomplete |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files needed |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `prompts/startup.md` | Expand Steps 6-8 into a full PR lifecycle with monitoring, recommendation handling, issue updates, merge execution. Add in-session work handling. |
| `personas/agentic/team-lead.md` | Add PR monitoring, Copilot recommendation review, recommendation disposition, and merge execution to responsibilities and interaction model |
| `personas/agentic/coder.md` | Add recommendation implementation, branch update pushing, and issue commenting to responsibilities |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. **Update `prompts/startup.md`**:
   - Add Step 0: In-session work handling (create issue first if no issue exists)
   - Expand Step 6 to include explicit PR creation with issue reference
   - Replace Step 7 with a detailed PR Monitoring & Review Loop containing sub-steps:
     - 7a: Poll CI checks until complete or timeout
     - 7b: Fetch and parse Copilot review comments
     - 7c: Fetch and parse panel emissions
     - 7d: For each recommendation — implement fix OR dismiss with rationale comment
     - 7e: Update the issue with all actions taken
     - 7f: Push updated branch
     - 7g: Re-run governance (loop back to 7a)
     - 7h: Once approved — merge to main
     - 7i: Update and close issue
   - Adjust Step 8 "Continue" to reference the complete cycle

2. **Update `personas/agentic/team-lead.md`**:
   - Add to Responsibilities: PR check monitoring, Copilot recommendation review, recommendation disposition decisions, merge execution
   - Add to Evaluate For: PR check status, Copilot recommendation severity, recommendation resolution completeness
   - Add to Output Format: recommendation disposition log, merge execution confirmation
   - Update Interaction Model diagram to include the monitoring loop

3. **Update `personas/agentic/coder.md`**:
   - Add to Responsibilities: implementing Copilot/panel recommendations, pushing branch updates, commenting on issues with changes made
   - Add to Evaluate For: recommendation implementation completeness
   - Add to Anti-patterns: ignoring Copilot recommendations without documented rationale

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual review | All 3 files | Verify the loop is complete and unambiguous — every step has explicit commands or actions |
| Governance review | Panel output | Run through governance-review.yml to validate |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Startup.md becomes too long for context loading | Low | Medium | Keep steps concise with command examples, not prose |
| Copilot API polling adds latency | Medium | Low | Define timeout (10 min) and fallback behavior |
| Merge conflicts from concurrent human work | Low | Medium | Check for conflicts before merge, abort if found |

## 7. Dependencies

- [x] No blocking dependencies — all files exist and are editable

## 8. Backward Compatibility

All changes are additive. The existing 8-step structure is preserved (numbering adjusted). No consuming repos are affected since this is cognitive artifact (versioned by git SHA).

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Core agentic workflow change |
| documentation-review | No | These are cognitive artifacts, not docs |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Keep existing step numbering, expand in-place | Backward compatibility and minimal disruption |
| 2026-02-21 | Add in-session work handling as a preamble, not a numbered step | It's a mode of entry, not a loop step |
