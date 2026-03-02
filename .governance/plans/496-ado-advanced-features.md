# ADO Sync Advanced Features — Hierarchy, Comments, Area/Iteration Mapping, Bulk Sync

**Author:** Code Manager (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/496
**Branch:** NETWORK_ID/feat/496/ado-advanced-features

---

## 1. Objective

Extend bidirectional ADO sync with parent-child hierarchy mapping, comment synchronization, area/iteration path mapping, and a bulk initial sync command for onboarding existing projects.

## 2. Rationale

The core sync (#494, #495) handles basic field/state sync. Enterprise teams need hierarchy (epics→features→stories), comments for cross-platform collaboration, area/iteration mapping for sprint management, and bulk import for onboarding.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| All features in one module | Yes | Selected — features share config and ledger infrastructure |
| Separate repos per feature | Yes | Over-engineered for closely related capabilities |
| Attachment sync included | Yes | Deferred — bandwidth-heavy, lower priority per issue |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/integrations/ado/hierarchy.py` | Parent-child hierarchy sync logic |
| `governance/integrations/ado/comments_sync.py` | Bidirectional comment sync with prefix filtering |
| `governance/integrations/ado/area_iteration.py` | Area path ↔ label and iteration path ↔ milestone mapping |
| `governance/integrations/ado/bulk_sync.py` | Bulk initial sync engine for onboarding |
| `governance/integrations/ado/tests/test_hierarchy.py` | Hierarchy sync tests |
| `governance/integrations/ado/tests/test_comments_sync.py` | Comment sync tests |
| `governance/integrations/ado/tests/test_area_iteration.py` | Area/iteration mapping tests |
| `governance/integrations/ado/tests/test_bulk_sync.py` | Bulk sync tests |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/integrations/ado/sync_engine.py` | Integrate hierarchy and comment sync into event dispatch |
| `governance/integrations/ado/reverse_sync.py` | Integrate reverse hierarchy, comment, area/iteration sync |
| `governance/integrations/ado/cli.py` | Add `initial-sync` subcommand with `--dry-run`, `--limit`, `--since`, `--reverse` flags |
| `bin/ado-sync.py` | Wire `initial-sync` CLI command |
| `governance/integrations/ado/__init__.py` | Export new modules |
| `governance/schemas/ado-integration.schema.json` | Add `area_path_mapping`, `iteration_mapping`, `sync_comments`, `comment_prefix` fields |
| `governance/schemas/ado-sync-ledger.schema.json` | Add `comment_mappings` array to mapping entries |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | N/A |

## 4. Approach

1. **Hierarchy sync (`hierarchy.py`)**:
   - Parse `parent: #N` from GitHub issue body metadata block
   - Look up parent's ADO work item ID in ledger
   - Add `System.LinkTypes.Hierarchy-Reverse` relation on child work item
   - Reverse: when ADO adds child link, update GitHub issue body with parent reference
   - Validate type hierarchy (Epic→Feature→Story→Task), warn on violations

2. **Comment sync (`comments_sync.py`)**:
   - GitHub→ADO: sync comments prefixed with `[ado-sync]` (configurable prefix)
   - ADO→GitHub: sync comments tagged with `[github-sync]`
   - Store comment ID mappings in ledger entry's `comment_mappings` array
   - Attribution format: `[From GitHub — @user]: body` / `[From ADO — User Name]: body`
   - ADO comments are HTML-only — convert markdown to basic HTML

3. **Area/iteration mapping (`area_iteration.py`)**:
   - `map_label_to_area_path(labels, config)` — match `area:*` labels to configured paths
   - `map_area_path_to_label(area_path, config)` — reverse lookup for ADO→GitHub
   - `map_milestone_to_iteration(milestone, config)` — GitHub milestone → ADO iteration
   - `map_iteration_to_milestone(iteration_path, config)` — reverse lookup
   - Support `@CurrentIteration` macro

4. **Bulk sync (`bulk_sync.py`)**:
   - `initial_sync(config, direction, dry_run, limit, since)` — main entry
   - GitHub→ADO: paginate all open issues via `gh issue list`, create ADO items for unmapped ones
   - ADO→GitHub (`--reverse`): WIQL query for active items, create GitHub issues for unmapped ones
   - Respect rate limiting with exponential backoff
   - Progress output: `[42/128] Created ADO User Story #12345 for GitHub #42`

5. **Schema updates**: Add new config fields and ledger fields with backward-compatible defaults

6. **Write comprehensive tests** for all new modules

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | hierarchy.py | Parent parsing, relation creation, type validation, reverse sync |
| Unit | comments_sync.py | Prefix filtering, attribution format, markdown→HTML, ID mapping |
| Unit | area_iteration.py | Label↔area path, milestone↔iteration, @CurrentIteration |
| Unit | bulk_sync.py | Dry-run output, limit/since filtering, progress tracking, rate limit handling |
| Integration | sync_engine.py | Hierarchy/comment dispatch integration |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Comment sync creates noise | Medium | Medium | Opt-in prefix filtering, disabled by default |
| Hierarchy type violations | Low | Low | Warning-only, don't block sync |
| Bulk sync rate limiting | Medium | Medium | Exponential backoff, --limit flag for testing |
| Schema migration for existing ledgers | Low | Medium | Backward-compatible defaults, no required new fields |

## 7. Dependencies

- [x] #491 — ADO API client library (closed)
- [x] #492 — ADO schemas (closed)
- [x] #494 — GitHub→ADO sync engine (closed)
- [ ] #495 — ADO→GitHub reverse sync (open — needed for bidirectional comment/hierarchy sync)

## 8. Backward Compatibility

Fully backward compatible. All new features are opt-in via configuration. Existing ledger entries without `comment_mappings` are handled gracefully. Schema changes add optional fields with defaults.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Comment sync processes user content |
| code-review | Yes | New feature implementation |
| documentation-review | Yes | Schema changes, new config options |
| data-governance-review | Yes | Comment content sync across platforms |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Comment sync opt-in with prefix | Prevents noise, gives users control |
| 2026-02-27 | Hierarchy warnings not blocks | Don't break sync for non-standard hierarchies |
| 2026-02-27 | Defer attachment sync | Lower priority, bandwidth concerns — per issue guidance |
