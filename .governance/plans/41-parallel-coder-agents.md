# Parallel Coder Agents — Agentic Speedup

**Author:** Code Manager (agentic)
**Date:** 2026-02-25
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/41
**Branch:** itsfwcp/feat/41/parallel-coder-agents

---

## 1. Objective

Replace the sequential one-issue-at-a-time startup loop with parallel execution where the Code Manager spawns up to 5 concurrent Coder agents, each working on a different issue in an isolated git worktree. This eliminates the bottleneck of serializing independent issues.

## 2. Rationale

The current loop processes issues one at a time: triage → plan → implement → review → merge → next. With 30+ open issues, this is too slow. Issues are typically independent (different files, different scopes), so they can safely run concurrently in isolated worktrees without merge conflicts.

Claude Code's `Task` tool with `isolation: "worktree"` provides exactly this capability — each subagent gets its own copy of the repo, its own branch, and its own context window. The Code Manager orchestrates from the main session.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Sequential loop (status quo) | Yes | Too slow for 30+ issues |
| Multiple Claude Code sessions | Yes | Requires external orchestration outside the governance framework |
| Task tool with worktree isolation | Yes | **Selected** — native to Claude Code, fits Orchestrator-Workers pattern |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Replace sequential Phase 2-5 with parallel dispatch; update constraints, session cap, and flow diagram |
| `governance/personas/agentic/code-manager.md` | Add parallel dispatch responsibilities, worktree coordination |
| `governance/prompts/agent-protocol.md` | Add worktree-based parallel transport section |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. **Update `startup.md`**:
   - Phase 1 remains unchanged (triage)
   - Phase 2 becomes "Parallel Planning" — Code Manager validates and plans all issues (up to session cap)
   - Phase 3 becomes "Parallel Dispatch" — spawn Coder subagents via Task tool with worktree isolation
   - Phase 4 becomes "Collect & Review" — as each Coder completes, evaluate, push PR, monitor CI
   - Phase 5 remains merge & checkpoint but handles multiple PRs
   - Update constraints: remove "Sequential execution — one issue at a time", add parallelism rules
   - Raise session cap from 3 to 5 (parallel is more context-efficient)

2. **Update `code-manager.md`**:
   - Add "Spawn parallel Coder agents" to responsibilities
   - Add worktree coordination to decision authority
   - Update interaction model diagram

3. **Update `agent-protocol.md`**:
   - Add "Phase A+: Parallel Single-Session" transport mode
   - Describe worktree-based parallel execution

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Startup loop | Run /startup and verify parallel dispatch |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Merge conflicts between parallel branches | Low | Medium | Issues at same priority level typically touch different files; rebase on merge |
| Context window pressure from many subagents | Low | Low | Subagents have their own context windows; main session stays light |
| Subagent failure leaves orphan worktree | Medium | Low | Worktrees auto-clean if no changes; manual cleanup otherwise |

## 7. Dependencies

- [x] No blocking dependencies

## 8. Backward Compatibility

Additive change. The sequential fallback remains available (single-issue dispatch). The parallel pattern only activates when multiple independent issues are identified.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Cognitive artifact change |
| documentation-review | Yes | Prompt and persona updates |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Session cap raised from 3 to 5 | Parallel execution is more context-efficient — subagents don't consume main context |
| 2026-02-25 | Code Manager stays in main session, Coders in worktrees | Code Manager needs to orchestrate and monitor; Coders can be fully autonomous |
| 2026-02-25 | Phase 4 collects results as they arrive, doesn't wait for all | Maximizes throughput — PRs can be created and monitored as soon as each Coder finishes |
