# Issue Monitor — Local Scripts + GitHub Actions Workflow

**Author:** Team Lead (agentic)
**Date:** 2026-02-21
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/73
**Branch:** NETWORK_ID/feat/73/issue-monitor

---

## 1. Objective

Create an issue-monitoring system with two modes: (1) a local background script for developers actively working, and (2) a GitHub Actions workflow that triggers on issue creation. Both modes evaluate issues for actionability and dispatch them to Claude or Copilot for autonomous processing.

## 2. Rationale

The current agentic startup loop (`governance/prompts/startup.md`) requires manual invocation. Automating issue detection and dispatch reduces latency between issue creation and work starting.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Cron-based workflow only | Yes | Users want immediate local feedback; cron has minimum 5-min granularity |
| Local script only | Yes | Misses the always-on benefit of workflow automation |
| Both local + workflow | Yes (chosen) | Covers both active development and passive monitoring scenarios |
| Custom webhook server | Yes | Overengineered for a config-only repo; GitHub Actions is the native event system |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `scripts/issue-monitor.sh` | Local background monitor for Linux/macOS |
| `scripts/issue-monitor.ps1` | Local background monitor for Windows |
| `.github/workflows/issue-monitor.yml` | GitHub Actions workflow triggered on issue events |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `.gitignore` | Add `scripts/*.log` for monitor log files |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

### 4a: GitHub Actions Workflow (`.github/workflows/issue-monitor.yml`)

1. **Triggers**: `issues.opened`, `issues.labeled`
2. **Job: evaluate** — Runs on `ubuntu-latest`:
   - Checks if issue is actionable (not `blocked`, `wontfix`, `duplicate`, `refine`; not assigned to human; no existing branch)
   - If not actionable, exits early
3. **Job: dispatch-claude** — Uses `anthropics/claude-code-base-action@v1`:
   - Loads `governance/prompts/startup.md` as the system prompt
   - Prompt tells Claude to process the specific issue starting at Step 4
   - Requires `ANTHROPIC_API_KEY` repository secret
   - Configurable model (default: `claude-sonnet-4-20250514` for cost efficiency in CI)
4. **Job: dispatch-copilot** (optional, parallel) — Assigns issue to Copilot via API:
   - Uses `gh` CLI to assign the issue to Copilot coding agent
   - Only runs if a repository variable `ENABLE_COPILOT_AGENT` is set to `true`

### 4b: Local Script (`scripts/issue-monitor.sh` / `scripts/issue-monitor.ps1`)

1. **Configuration** via environment variables:
   - `AI_MONITOR_INTERVAL` — poll interval in seconds (default: 300)
   - `AI_MONITOR_BACKEND` — `claude` or `copilot` (default: `claude`)
   - `AI_MONITOR_REPO` — repository in `owner/repo` format (auto-detected from git remote)
   - `AI_MONITOR_LOG` — log file path (default: `scripts/issue-monitor.log`)
2. **Main loop**:
   - Polls `gh issue list` for open issues
   - Filters for actionable issues (same criteria as startup.md Step 2-3)
   - For each new actionable issue (not previously seen):
     - If backend is `claude`: invokes `claude --prompt "..." --allowedTools ...` in a subshell
     - If backend is `copilot`: assigns issue to Copilot via `gh` CLI
   - Tracks seen issues in a state file to avoid re-processing
   - Logs all activity to the log file
3. **Background execution**: Script runs in a loop; user starts it with `nohup` or `&`
4. **Graceful shutdown**: Traps SIGINT/SIGTERM for clean exit

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Workflow | Create test issue, verify workflow triggers and evaluates correctly |
| Manual | Local script | Run locally, verify it detects new issues and logs output |
| Dry-run | Both | Both support a dry-run mode that logs what would happen without invoking AI |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| API key exposure in workflow logs | Low | High | API key is a secret; never echoed; workflow uses action's built-in key handling |
| Runaway CI costs | Medium | High | Model defaults to Sonnet (not Opus) in CI; max_turns limit; workflow concurrency group prevents parallel runs |
| Race condition between local and workflow | Low | Medium | Local script checks for existing branches before dispatching; workflow does same |
| Copilot agent assignment unreliable | Medium | Low | Copilot dispatch is opt-in (`ENABLE_COPILOT_AGENT`); Claude is primary |

## 7. Dependencies

- [ ] `ANTHROPIC_API_KEY` repository secret (for workflow Claude dispatch)
- [ ] Claude Code CLI installed locally (for local script Claude backend)
- [ ] `gh` CLI authenticated (for both local and workflow)
- [x] No blocking code dependencies

## 8. Backward Compatibility

Fully additive. No existing files are changed in behavior. The workflow and scripts are opt-in.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New scripts and workflow need review |
| security-review | Yes | Workflow handles API keys and has write permissions |

**Policy Profile:** default
**Expected Risk Level:** medium (new CI integration with API key handling)

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Use `claude-code-base-action` not `claude-code-action` | Base action gives full control over prompt and tools; the interactive action is designed for @claude mentions in comments, not programmatic dispatch |
| 2026-02-21 | Default to Sonnet in CI, Opus locally | Cost optimization — Sonnet is cheaper and faster for CI; local users can choose Opus for complex issues |
| 2026-02-21 | Copilot dispatch is opt-in | Copilot agent assignment via API has rough edges; Claude path is more reliable |
| 2026-02-21 | Separate evaluate job from dispatch | Prevents burning API tokens on non-actionable issues |
