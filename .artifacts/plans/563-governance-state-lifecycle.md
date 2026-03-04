# Implement Governance State Lifecycle Management (#563)

**Author:** Claude (Coder)
**Date:** 2026-03-01
**Status:** approved
**Issue:** #563
**Branch:** itsfwcp/feat/563/governance-state-lifecycle

---

## 1. Objective

Create a cleanup mechanism for accumulated governance state files (agent logs, checkpoints) with configurable retention periods.

## 2. Rationale

At 10 sessions/week, agent logs and checkpoints accumulate indefinitely — 520+ files/year tracked by git. No existing cleanup mechanism.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Git-based archival (tags/releases) | Yes | Complex; files are ephemeral state, not artifacts worth archiving |
| Cron job | Yes | Requires infrastructure; script is simpler and portable |
| Shell script with retention | Yes | Selected — simple, configurable, runs in startup or standalone |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| governance/bin/cleanup-state.sh | Cleanup script with configurable retention |
| .governance/.gitignore | Exclude ephemeral state from git tracking |

### Files to Modify

None.

## 4. Approach

1. Create `governance/bin/cleanup-state.sh` with `--dry-run`, `--agent-log-days`, `--checkpoint-days` options
2. Default retention: agent logs 30 days, checkpoints 7 days
3. Create `.governance/.gitignore` for ephemeral files
4. Plans are not cleaned (accumulated by design for audit trail)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | cleanup-state.sh | Dry-run mode tested, help output verified |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Premature deletion of needed checkpoint | Low | Medium | 7-day default is generous; --dry-run for preview |

## 7. Dependencies

None.

## 8. Backward Compatibility

Additive only. Existing files are not affected unless the script is explicitly run.

## 9. Governance

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-01 | Don't clean plans | Plans are the audit trail — accumulated by design |
| 2026-03-01 | Default 30/7 retention | Balances disk usage with recovery window |
