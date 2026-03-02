# ADO→GitHub Reverse Sync — Service Hook Receiver and Reverse State Mapping

**Author:** Code Manager (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/495
**Branch:** NETWORK_ID/feat/495/ado-reverse-sync

---

## 1. Objective

Enable ADO work item changes to propagate back to GitHub issues, completing the bidirectional sync loop. Implement a `repository_dispatch`-based receiver (Option A from the issue), reverse state/field mapping, user mapping lookups, echo prevention for the ADO→GitHub direction, and a Service Hook setup CLI command.

## 2. Rationale

The GitHub→ADO sync engine (#494) is complete. Without reverse sync, ADO changes are lost — teams updating work items in ADO Boards see their changes ignored on GitHub. This closes the loop.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| GitHub Actions `repository_dispatch` (Option A) | Yes | **Selected** — no Azure infrastructure needed, uses existing GitHub Actions runner |
| Azure Function (Option B) | Yes | Requires Azure resource provisioning, more ops overhead for initial release |
| Polling-based sync | Yes | Higher latency, unnecessary API calls, doesn't scale |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/integrations/ado/reverse_sync.py` | ReverseSyncEngine class — processes ADO webhook payloads, updates GitHub issues |
| `governance/integrations/ado/reverse_mappers.py` | ADO→GitHub state, field, and user reverse mapping functions |
| `.github/workflows/ado-reverse-sync.yml` | GitHub Actions workflow triggered on `repository_dispatch` event type `ado-sync` |
| `governance/integrations/ado/tests/test_reverse_sync.py` | ReverseSyncEngine tests |
| `governance/integrations/ado/tests/test_reverse_mappers.py` | Reverse mapper tests |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/integrations/ado/cli.py` | Add `setup-service-hooks` subcommand |
| `bin/ado-sync.py` | Wire `setup-service-hooks` CLI command |
| `governance/integrations/ado/sync_engine.py` | Update ledger writes to set `last_sync_source` for echo detection |
| `governance/integrations/ado/__init__.py` | Export ReverseSyncEngine |
| `governance/integrations/ado/tests/test_cli.py` | Add tests for `setup-service-hooks` command |
| `CLAUDE.md` | Document reverse sync in Architecture section |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | N/A |

## 4. Approach

1. **Create `reverse_mappers.py`** — Implement reverse mapping functions:
   - `map_ado_state_to_github(ado_state, config)` → returns `{action: "reopen"|"close", labels_add: [...], labels_remove: [...]}`
   - `map_ado_fields_to_github(changed_fields, config)` → returns dict of GitHub issue update fields
   - `map_ado_user_to_github(ado_email, config)` → reverse lookup in user_mapping
   - `map_ado_priority_to_github(priority_int, config)` → returns priority label string

2. **Create `reverse_sync.py`** — Implement `ReverseSyncEngine`:
   - Constructor takes config (from `project.yaml`), GitHub token, ledger path, error log path
   - `sync(payload: dict) -> SyncResult` — main entry point for ADO webhook payloads
   - Echo detection: check ledger `last_sync_source == "github"` within grace period → skip
   - Dispatch by changed field: state changes, title, description, assignee, iteration, priority
   - Update ledger with `last_sync_source = "ado"` on success
   - Log errors to error log on failure

3. **Create `.github/workflows/ado-reverse-sync.yml`**:
   - Trigger on `repository_dispatch` with event type `ado-sync`
   - Extract ADO payload from `client_payload`
   - Run ReverseSyncEngine with GitHub token
   - Commit updated ledger if changed

4. **Add `setup-service-hooks` CLI command**:
   - Creates ADO Service Hook subscriptions for `workitem.created`, `workitem.updated`, `workitem.deleted`
   - Configures webhook URL pointing to GitHub `repository_dispatch` endpoint
   - Applies area path filters from config
   - `--dry-run` flag for preview
   - Idempotent (checks existing subscriptions)

5. **Update existing sync engine** to consistently set `last_sync_source = "github"` in ledger entries

6. **Write tests** for all new modules

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | reverse_mappers.py | All state transitions, field mappings, user lookups (found/not found), priority mapping |
| Unit | reverse_sync.py | Event dispatch, echo detection, ledger updates, error handling |
| Unit | cli.py (setup-service-hooks) | Dry-run output, idempotency check |
| Integration | ado-reverse-sync.yml | Workflow structure validation |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Echo loops (ADO→GH→ADO→...) | Medium | High | Grace period + last_sync_source tracking in ledger |
| ADO Service Hook payload format changes | Low | Medium | Pin to API 7.1, validate payload schema |
| GitHub token permissions insufficient | Low | Medium | Document required scopes (issues:write) |
| Rate limiting on GitHub API | Low | Medium | Batch updates, respect rate limit headers |

## 7. Dependencies

- [x] #491 — ADO API client library (closed)
- [x] #492 — ADO schemas (closed)
- [x] #494 — GitHub→ADO sync engine (closed)

## 8. Backward Compatibility

Fully backward compatible. New files only. The sync engine modification (setting `last_sync_source`) is additive — existing ledger entries without this field are handled gracefully (treated as "unknown" source, no echo skip).

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Webhook processing, GitHub token handling |
| code-review | Yes | New feature implementation |
| documentation-review | Yes | Standard requirement |
| threat-modeling | Yes | External webhook receiver (ADO→GitHub attack surface) |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Use repository_dispatch (Option A) | Simpler, no Azure infra needed, sufficient for initial release |
| 2026-02-27 | Echo detection via ledger, not webhook signatures | Consistent with existing forward sync pattern |
