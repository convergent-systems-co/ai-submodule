# Create Project Manager Persona to Multiplex Team Leads

**Author:** Team Lead (agent)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/456
**Branch:** NETWORK_ID/feat/456/project-manager-persona

---

## 1. Objective

Add a Project Manager persona that sits above the DevOps Engineer in the hierarchy, enabling:
1. **Multiplexed Team Leads** — spawn 0-N Team Leads, each orchestrating their own batch of Coders
2. **Change-type grouping** — DevOps Engineer groups issues by change type (docs, infra, code, security) and assigns batches to specialized Team Leads
3. **Background issue polling** — DevOps Engineer runs persistently in the background, watching for new issues and launching the pipeline dynamically as work arrives

## 2. Rationale

The current architecture uses a single Team Lead as a bottleneck orchestrator. For large repos or high issue throughput, one Team Lead's context window limits parallelism. A Project Manager layer enables:
- Multiple Team Leads working in parallel on separate issue batches
- Grouping related issues for a single Team Lead to plan more coherently
- A persistent DevOps Engineer that can react to new issues without requiring a new `/startup` invocation

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Scale `parallel_coders` higher | Yes | Doesn't address the Team Lead context bottleneck — one Team Lead still plans/reviews all issues |
| Multiple sequential Team Lead batches | Yes | Sequential = slow; no parallelism at the orchestrator level |
| Project Manager as new top-level persona | Yes — **selected** | Clean separation: PM owns portfolio, DevOps owns infra/triage, CM owns plan/review per batch |
| Make DevOps Engineer the multiplexer | Yes | Overloads DevOps with orchestration responsibilities; violates single-responsibility |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/personas/agentic/project-manager.md` | New Project Manager persona definition: portfolio-level orchestration, Team Lead dispatch, cross-batch dependency detection |
| `docs/architecture/project-manager-architecture.md` | Architecture docs for the new persona layer and dispatch model |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Restructure phases: PM becomes session entry point (new Phase 0.5); DevOps becomes PM-dispatched background agent; Team Leads spawned per issue-group batch; add background polling loop for DevOps |
| `governance/prompts/agent-protocol.md` | Add Project Manager as valid sender/receiver; add PM→CM and PM→DevOps message routes; add new POLL message type for background issue watching |
| `governance/personas/agentic/devops-engineer.md` | Update to support background polling mode; add issue-grouping-by-change-type logic; update hierarchy to report to PM |
| `governance/personas/agentic/team-lead.md` | Update to accept batch assignments from PM (not just DevOps); add batch-scoped context management |
| `CLAUDE.md` (root `.ai/CLAUDE.md`) | Update architecture section: add PM to persona table, update pipeline phases, update dispatch model description |
| `project.yaml` | Add `governance.parallel_team_leads` config (default: 3) |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions — additive change |

## 4. Approach

1. **Create Project Manager persona** (`governance/personas/agentic/project-manager.md`):
   - Role: Portfolio-level orchestrator, session entry point
   - Responsibilities: spawn DevOps Engineer (background), receive triaged+grouped issue batches, spawn N Team Leads (one per group), collect cross-batch results, manage session lifecycle
   - Context management: PM runs in main session context; Team Leads run as Task agents with `isolation: "worktree"` or in background
   - Configurable via `governance.parallel_team_leads` in `project.yaml`

2. **Update agent protocol** (`governance/prompts/agent-protocol.md`):
   - Add Project Manager to valid senders/receivers table
   - Message routes: PM→DevOps (ASSIGN for triage), DevOps→PM (RESULT with grouped issues), PM→CM (ASSIGN per batch), CM→PM (RESULT/STATUS/ESCALATE)
   - Add WATCH message type for background polling: DevOps emits WATCH when new issues detected

3. **Restructure startup.md phases**:
   - Phase 0: Checkpoint recovery (unchanged)
   - Phase 1: Project Manager initializes, spawns DevOps Engineer as background Task agent for pre-flight + triage
   - Phase 1b (background): DevOps runs pre-flight, scans issues, groups by change type, returns RESULT to PM
   - Phase 2: PM receives grouped issues, spawns N Team Leads (one per group) as background Task agents
   - Phase 2b (parallel): Each Team Lead plans its batch of issues
   - Phase 3 (parallel): Each Team Lead dispatches its Coders (nested parallelism: PM→CM→Coder)
   - Phase 4: Results flow up: Coder→CM→PM; PM coordinates cross-batch dependencies
   - Phase 5: PM merges all PRs, DevOps continues background polling for new issues
   - Phase 5b (loop): If DevOps WATCH detects new issues, PM spawns new CM batch without restarting the full pipeline

4. **Update DevOps Engineer persona** for background mode:
   - Add "background polling" operating mode: periodic `gh issue list` checks (configurable interval, default 60s)
   - Add issue grouping logic: categorize by labels, file patterns, and change type (docs, infra, code, security, mixed)
   - Emit WATCH message to PM when new actionable issues detected

5. **Update Team Lead persona** for batch-scoped operation:
   - Accept batch ASSIGN from PM (not just DevOps)
   - Scope planning to assigned batch only
   - Report RESULT/STATUS to PM (not DevOps)

6. **Update CLAUDE.md** with new architecture:
   - Add PM to persona table
   - Update pipeline phase diagram
   - Document `parallel_team_leads` config

7. **Create architecture documentation** (`docs/architecture/project-manager-architecture.md`)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Persona prompts | Validate persona instructions are complete and consistent |
| Integration | startup.md | Execute `/startup` with new PM flow; verify PM→DevOps→CM→Coder chain works |
| E2E | Multi-issue session | Test with 10+ issues to verify multiplexed Team Leads reduce latency |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Increased context overhead from PM layer | Med | Med | PM stays lightweight — delegates immediately, doesn't read code |
| Background polling burns API rate limits | Low | Low | Configurable interval; default 60s; skip if no new issues |
| Cross-batch dependency conflicts | Med | High | PM detects file-level conflicts before dispatch; serializes conflicting issues |
| Backward compatibility with existing startup | Low | High | Support both modes: `governance.use_project_manager: true/false` (default false) |

## 7. Dependencies

- [x] #462 (read issue comments) — non-blocking but should be included in the updated startup.md

## 8. Backward Compatibility

**Fully backward compatible.** The Project Manager layer is opt-in via `governance.use_project_manager: true` in `project.yaml`. When disabled (default), the existing DevOps→Team Lead→Coder chain operates as-is. This allows consuming repos to adopt the new architecture at their own pace.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | New persona with elevated privileges |
| threat-modeling | Yes | New orchestration layer — attack surface analysis needed |
| documentation-review | Yes | Major architecture change |
| cost-analysis | Yes | Multiple Team Leads = more API calls/tokens |
| data-governance-review | Yes | Always required |
| code-review | Yes | Multiple files modified |

**Policy Profile:** default
**Expected Risk Level:** high

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Opt-in via `governance.use_project_manager` flag | Backward compatibility — existing repos should not break |
| 2026-02-27 | DevOps Engineer background polling via Task tool | User explicitly requested "always looking for new issues" |
| 2026-02-27 | Group issues by change type for CM batches | User requirement: "group issues by change types to assign to the team-lead" |
