# Enforce 80% Context Capacity Shutdown Protocol

**Author:** Coder (agentic)
**Date:** 2026-02-21
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/43
**Branch:** itsfwcp/fix/43/context-management

---

## 1. Objective

Make the context capacity shutdown protocol enforceable by: reducing the session cap, adding mandatory checkpoints between every issue, adding concrete detection instructions, and ensuring Tier 0 includes the shutdown trigger.

## 2. Rationale

The current protocol says "check context capacity" but provides no concrete guidance on how to detect it. The agent previously ran 5 issues in a session without checkpointing, consuming excessive context. The user should never have to manually manage context.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep 5-issue cap with better monitoring | Yes | 5 issues reliably exhausts context before warnings fire |
| Reduce to 1 issue per session | Yes | Too conservative, wastes human time on /clear cycles |
| 3-issue hard cap with mandatory checkpoints | **Selected** | Balances throughput with safety |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `prompts/startup.md` | Reduce cap to 3, add mandatory checkpoint step, add detection heuristics |
| `docs/context-management.md` | Add platform-specific detection section, update shutdown protocol |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Update `prompts/startup.md`:
   - Change max issues from 5 to 3
   - Add a new Step 7.5 (mandatory checkpoint) between each issue completion and the next issue
   - Add concrete context pressure detection heuristics to the shutdown protocol
   - Make the shutdown protocol the FIRST section (before the startup sequence) so it survives partial context loading

2. Update `docs/context-management.md`:
   - Add a "Context Pressure Detection" section with platform-specific signals
   - Update the Capacity Shutdown Protocol with the new mandatory checkpoint rules

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Behavioral | Agent compliance | This session demonstrates the new protocol by checkpointing after this issue |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| 3-issue cap too conservative for trivial issues | Medium | Low | Trivial issues consume less context; 3 is a safety net, not a target |
| Instructions still lost on compaction | Low | High | Moving shutdown protocol to top of file increases survival odds |

## 7. Dependencies

- [x] No blocking dependencies

## 8. Backward Compatibility

Additive changes to existing files. No breaking changes.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Prompt and doc changes |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | 3-issue hard cap | Balances throughput with context safety |
| 2026-02-21 | Mandatory checkpoint after every issue | Eliminates "optional" monitoring that gets skipped |
| 2026-02-21 | Move shutdown protocol before startup sequence | Increases odds of surviving partial context load |
