# CI-Native Agentic Convergence Loop Workflow

**Author:** Claude (Coder persona)
**Date:** 2026-02-27
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/471
**Branch:** NETWORK_ID/feat/471/agentic-loop-workflow

---

## 1. Objective

Create a reusable GitHub Actions workflow (`.github/workflows/agentic-loop.yml`) that runs an AI CLI agent in a convergence loop with configurable exit criteria, multi-model backend support, checkpoint save/restore, judge evaluation, and JSONL manifest logging.

## 2. Rationale

The governance platform needs a CI-native mechanism to run agentic loops that iterate toward task completion with structured feedback, rate limiting, and auditability. This replaces ad-hoc agent dispatch with a production-quality reusable workflow.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Extend issue-monitor.yml | Yes | issue-monitor is issue-triage-specific; convergence loop is a general-purpose primitive |
| External orchestrator (e.g., Temporal) | Yes | Adds infrastructure dependency; GitHub Actions is already available in all consuming repos |
| Single-shot agent dispatch | Yes | No iteration, no convergence checking, no checkpoint/resume |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.github/workflows/agentic-loop.yml` | Reusable convergence loop workflow with workflow_call and workflow_dispatch triggers |

### Files to Modify

| File | Change Description |
|------|-------------------|
| N/A | No existing files modified |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files deleted |

## 4. Approach

1. Define workflow_call inputs (task_prompt, success_command, validation_prompt, max_iterations, model, backend, branch_name, issue_number, create_pr, human_feedback, resume_from_checkpoint) and outputs (completed, iterations, has_changes, judge_feedback)
2. Define workflow_dispatch inputs for manual triggering (task_prompt, max_iterations, model, backend)
3. Set permissions (contents: write, pull-requests: write, issues: write, actions: read)
4. Configure concurrency per issue number
5. Implement single job with steps: checkout, setup runtimes, install CLI, git identity, branch management, checkpoint restore, convergence loop (bash), judge evaluation, commit + push, PR creation, checkpoint save

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| YAML validation | Workflow syntax | Validated via actionlint or manual review |
| Integration | Full workflow | Triggered via workflow_dispatch in a test repo |
| Smoke | CLI install steps | Verify npm/pip install commands succeed |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Workflow syntax errors | Low | Med | Follow existing workflow conventions from this repo |
| API key not configured in consuming repo | Med | High | Validate API key presence early; fail with clear error message |
| Infinite loop if success_command never passes | Low | High | Hard cap via max_iterations input with default 15 |
| Rate limiting from AI provider | Med | Med | 30-second delay between iterations |

## 7. Dependencies

- [x] GitHub Actions runner (ubuntu-latest) — non-blocking
- [x] Node.js 22 availability on actions/setup-node — non-blocking
- [x] Python 3.12 availability on actions/setup-python — non-blocking

## 8. Backward Compatibility

This is a new file with no existing consumers. Fully additive change.

## 9. Governance

Expected panel reviews and policy profile:

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New workflow file |
| security-review | Yes | Handles API keys and git push |
| threat-modeling | Yes | CI execution of AI agents |
| cost-analysis | Yes | AI API costs per iteration |
| documentation-review | Yes | Workflow documentation |
| data-governance-review | Yes | No PII but agent outputs logged |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Single job design | Reduces complexity; all steps are sequential within the convergence loop |
| 2026-02-27 | Backend abstraction (claude/copilot) | Supports multi-model strategy per issue requirements |
| 2026-02-27 | JSONL manifest logging | Append-only audit trail per governance conventions |
