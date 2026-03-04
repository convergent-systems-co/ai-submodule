# Auto-Restart Agentic Loop After /clear Context Reset

**Author:** Team Lead (agent)
**Date:** 2026-02-26
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/380
**Branch:** NETWORK_ID/feat/380/auto-restart-after-clear

---

## 1. Objective

Make the agentic loop resume automatically after a context reset by enhancing startup.md checkpoint auto-detection and documenting the approach for both Claude Code and Copilot.

## 2. Rationale

After a checkpoint + /clear, the user must manually run `/startup` to resume. Option D from the issue (startup prompt auto-detection) is the most practical: modify startup.md to check for existing checkpoints on launch and auto-resume.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Shell wrapper (Option A) | Yes | Requires external tooling; not portable to Copilot |
| Claude Code hooks (Option B) | Yes | Hook system doesn't support auto-injecting slash commands on session start |
| Copilot instructions (Option C) | Yes | Copilot instructions are static; can't conditionally trigger startup |
| Startup auto-detection (Option D, chosen) | Yes | — Works on both platforms, self-contained in startup.md |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files needed |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Add checkpoint auto-detection at the top of Phase 1 — scan `.artifacts/checkpoints/` for the most recent checkpoint, validate issue state, and resume from that point if found. Add clear instructions for both platforms. |
| `docs/architecture/context-management.md` | Document the auto-restart flow: checkpoint → /clear → /startup → auto-detect → resume. Add platform-specific reset instructions (Claude Code: /clear, Copilot: new thread). |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Add a "Phase 0: Checkpoint Recovery" section to startup.md before Phase 1
2. This phase scans `.artifacts/checkpoints/` for the most recent JSON file
3. If found: validate all issues are still open, remove closed ones, resume from the checkpoint's `current_step`
4. If not found or all issues closed: proceed to normal Phase 1
5. Update context-management.md with the auto-restart documentation
6. Add platform-specific handoff instructions (Claude Code: `/clear` then `/startup`, Copilot: new thread + paste checkpoint path)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual review | startup.md | Verify auto-detection logic handles: no checkpoint, valid checkpoint, stale checkpoint (all issues closed) |
| Cross-reference | context-management.md | Verify documentation matches implementation |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Auto-resume picks up stale checkpoint | Low | Medium | Issue state validation removes closed issues; stale checkpoints with no remaining work trigger fresh scan |
| Multiple checkpoint files cause confusion | Low | Low | Always use most recent by timestamp |

## 7. Dependencies

- None

## 8. Backward Compatibility

Fully backward compatible. Without a checkpoint, startup.md behaves exactly as before.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Documentation changes |
| security-review | Yes | Default policy requirement |
| threat-modeling | Yes | Default policy requirement |
| cost-analysis | Yes | Default policy requirement |
| data-governance-review | Yes | Default policy requirement |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Option D (auto-detection in startup.md) | Most portable approach; works on both Claude Code and Copilot without external tooling |
