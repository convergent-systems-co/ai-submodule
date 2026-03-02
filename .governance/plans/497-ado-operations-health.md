# ADO Sync Operations — Health Monitoring, Retry Handling, and Documentation

**Author:** Code Manager (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/497
**Branch:** NETWORK_ID/feat/497/ado-operations-health

---

## 1. Objective

Build the operational layer for ADO sync: comprehensive health checks, error retry with dead-letter queue, sync dashboard emission, and full documentation covering setup, configuration, troubleshooting, and runbooks.

## 2. Rationale

The sync engine (#494, #495) handles data flow but lacks observability and self-healing. Operations teams need health checks, automated retry, and clear documentation to manage the integration at scale.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Health checks + retry + docs in one issue | Yes | **Selected** — these are operationally coupled |
| Separate monitoring service | Yes | Over-engineered for file-based sync |
| External observability (Datadog, etc.) | Yes | Out of scope — can integrate later via emissions |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/integrations/ado/health.py` | Health check engine — connection, fields, ledger, errors, hooks |
| `governance/integrations/ado/retry.py` | Error queue retry processor with dead-letter handling |
| `governance/integrations/ado/dashboard.py` | Sync status dashboard emission generator |
| `governance/integrations/ado/tests/test_health.py` | Health check tests |
| `governance/integrations/ado/tests/test_retry.py` | Retry processor tests |
| `governance/integrations/ado/tests/test_dashboard.py` | Dashboard emission tests |
| `docs/guides/ado-integration.md` | Comprehensive integration guide (14 sections per issue spec) |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/integrations/ado/cli.py` | Add `health`, `retry-failed`, `dashboard` subcommands |
| `bin/ado-sync.py` | Wire new CLI commands |
| `governance/integrations/ado/__init__.py` | Export new modules |
| `governance/integrations/ado/tests/test_cli.py` | Add tests for new CLI commands |
| `CLAUDE.md` | Update ADO integration section with operations documentation |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | N/A |

## 4. Approach

1. **Health check engine (`health.py`)**:
   - `run_health_checks(config) -> list[HealthCheckResult]`
   - Checks: ADO connection, custom fields exist, ledger integrity (no orphans), ledger recency (<24h), error queue (unresolved count), service hooks active
   - Each check returns `HealthCheckResult(name, status: PASS|FAIL|WARN, details)`
   - Aggregate exit code: 0 if all pass, 1 if any fail

2. **Retry processor (`retry.py`)**:
   - `retry_failed(config, dry_run=False) -> list[RetryResult]`
   - Read `.governance/state/ado-sync-errors.json`
   - For each unresolved error with `retry_count < max_retries`: attempt operation
   - Exponential backoff between retries
   - Mark as `resolved=true` on success, increment `retry_count` on failure
   - Errors exceeding `max_retries` are dead-lettered (flagged, not retried)
   - `--dry-run` lists what would be retried without executing

3. **Dashboard emission (`dashboard.py`)**:
   - `generate_dashboard_emission(config) -> dict`
   - Reads ledger and error log, computes: total/active/error/paused mappings, last sync times, conflicts, errors today, dead-letter count
   - Output is a structured JSON emission consumable by governance dashboard

4. **CLI commands**:
   - `health` — runs all checks, table output, JSON output with `--json`
   - `retry-failed [--dry-run]` — processes error queue
   - `dashboard` — outputs sync status emission

5. **Documentation (`docs/guides/ado-integration.md`)** — 14 sections as specified in the issue:
   Overview, Prerequisites, Quick Start, Configuration Reference, Authentication, State Mapping, Type Mapping, Field Mapping, Hierarchy Sync, Comment Sync, Initial Sync, Service Hooks, Troubleshooting, FAQ

6. **Write tests** for all new modules

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | health.py | Each check independently — pass, fail, warn scenarios |
| Unit | retry.py | Successful retry, max retries exceeded, dry-run, empty queue |
| Unit | dashboard.py | Emission generation with various ledger/error states |
| Unit | cli.py | All 3 new subcommands with JSON and table output |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Health check false positives | Medium | Low | Conservative thresholds, WARN vs FAIL distinction |
| Retry processor causes duplicate work items | Low | Medium | Idempotent operations, ledger check before retry |
| Documentation becomes stale | Medium | Low | Version in same repo, update with code changes |

## 7. Dependencies

- [x] #491 — ADO API client library (closed)
- [x] #492 — ADO schemas (closed)
- [x] #494 — GitHub→ADO sync engine (closed)
- [ ] #495 — ADO→GitHub reverse sync (open — health checks verify service hooks)

## 8. Backward Compatibility

Fully backward compatible. New files and CLI commands only. Health checks work with existing ledger/error log formats. Documentation is purely additive.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Error retry handles potentially sensitive payloads |
| code-review | Yes | New feature implementation |
| documentation-review | Yes | Comprehensive documentation deliverable |
| cost-analysis | Yes | Health checks make API calls — should be bounded |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Conservative health check thresholds | Better to warn than false-alarm |
| 2026-02-27 | Dead-letter on max_retries exceeded | Prevents infinite retry loops |
| 2026-02-27 | Documentation in docs/guides/ not README | Keeps README focused, guide is comprehensive |
