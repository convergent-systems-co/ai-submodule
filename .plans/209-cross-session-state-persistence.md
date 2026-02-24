# Cross-Session State Persistence Schema and Storage Strategy

**Author:** Code Manager (agentic)
**Date:** 2026-02-24
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/209
**Branch:** itsfwcp/feat/209/cross-session-state-persistence

---

## 1. Objective

Define the governance artifacts for cross-session state persistence (Phase 5c): a JSON Schema for persistent governance state and a storage strategy document. This completes the last unchecked item in Phase 5c — Always-On Orchestration.

## 2. Rationale

The checkpoint system (PR #189) handles per-session save/restore. Cross-session state persistence is about accumulated governance memory — metrics trends, persona effectiveness history, threshold tuning decisions, and work queue state that makes each session more informed than the last.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Extend checkpoint schema | Yes | Checkpoints are ephemeral (per-session); persistent state has different lifecycle (accumulated, versioned, long-lived) |
| Database-backed storage | Yes | This repo is config-only; a file-based approach aligns with git-tracked artifacts |
| Single monolithic state file | Yes | Separate concerns (metrics, thresholds, queue) have different update frequencies; a structured document with sections is better than N files |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/session-state.schema.json` | JSON Schema for persistent cross-session governance state |
| `governance/docs/session-state-persistence.md` | Storage strategy: location, retention, concurrent access, migration |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off the cross-session state persistence item in Phase 5c |
| `CLAUDE.md` | Update schema count (23 → 24) |
| `README.md` | Update schema count if referenced; note Phase 5c completion status |

### Files to Delete

None.

## 4. Approach

1. Design the `session-state.schema.json` — sections for accumulated metrics snapshots, threshold tuning history, persona weight history, work queue state, and governance version tracking. Reference existing schemas via `$ref` where appropriate.
2. Write the storage strategy document — file location (`.governance-state/`), git-tracking rationale, retention policy, concurrent session access (file locking), migration strategy for schema version changes.
3. Update GOALS.md — check off the Phase 5c item, add to completed work table.
4. Update CLAUDE.md and README.md — schema count, Phase 5c status.
5. Commit, push, create PR.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | session-state.schema.json | Validate example instance against schema (manual or via `ajv`) |

No automated tests — this is a config-only repo.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Schema design doesn't cover future needs | Low | Low | Schema is versioned (1.0.0); additive changes via minor versions |
| Overlap with existing schemas | Low | Low | Reviewed checkpoint, autonomy-metrics, persona-effectiveness, retrospective-aggregation — session-state references them rather than duplicating |

## 7. Dependencies

- [x] Checkpoint schema (PR #189) — non-blocking, already complete
- [x] Autonomy metrics schema (PR #101) — non-blocking, already complete
- [x] Persona effectiveness schema (PR #143) — non-blocking, already complete

## 8. Backward Compatibility

Fully additive — new schema and new document. No breaking changes.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | New doc + doc updates |
| code-review | Yes | Schema correctness |
| security-review | Yes | Default required panel |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Single schema with sections vs. multiple schemas | Single schema keeps cross-session state as one logical unit; sections reference existing schemas for detailed metrics |
| 2026-02-24 | File-based in `.governance-state/` | Aligns with git-tracked config-only approach; consuming repos create this directory via init.sh |
