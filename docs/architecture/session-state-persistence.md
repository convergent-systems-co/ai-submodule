# Cross-Session State Persistence

## Purpose

Cross-session state persistence provides governance memory that accumulates across multiple agentic sessions. While checkpoints (`.governance/checkpoints/`) handle per-session save/restore, persistent state captures long-lived context: metrics trends, threshold tuning history, persona weight adjustments, work queue state, and governance decisions.

This document defines the storage strategy for cross-session state. The data format is defined in `governance/schemas/session-state.schema.json`.

## Storage Location

Persistent state is stored in **`.governance/state/`** in the consuming repository root (not inside the `.ai` submodule). This directory is:

- **Created by `init.sh`** alongside `.governance/plans/` and `.governance/panels/`
- **Git-tracked** — state changes are committed as part of the governance lifecycle
- **One file per state type**: `state.json` (the primary state document)

```
.governance/state/
└── state.json          # Cross-session governance state
```

> **Migration:** Legacy path `.governance-state/` is automatically migrated to `.governance/state/` by `init.sh`.

### Why Git-Tracked?

| Alternative | Rejected Because |
|-------------|------------------|
| External database | This is a config-only governance repo; no runtime infrastructure |
| GitHub Actions artifacts | Ephemeral (90-day retention), not queryable, not version-controlled |
| Branch-based storage | Complicates merge flow; state needs to be on the working branch |
| Environment variables | Too limited for structured data; not portable across sessions |

Git tracking provides: version history, merge conflict visibility, diff-based review, and zero additional infrastructure. State updates are committed by the agent as part of the session lifecycle (during Phase 5c checkpoint or at session end).

## Lifecycle

### Initialization

When `init.sh` runs (or an agent bootstraps a consuming repo), if `.governance/state/` does not exist:

1. Create the directory
2. Generate an initial `state.json` with empty collections and a new `state_id`
3. Commit as part of the bootstrap commit

### Session Start (Read)

At the beginning of each agentic session (startup.md Phase 1):

1. Read `.governance/state/state.json` if it exists
2. Load `known_issues` to provide context for issue scanning
3. Load `current_weights` to apply persona weight adjustments
4. Load `current_overrides` to apply threshold tuning
5. If the file is missing or corrupt, warn and continue with defaults — state loss is non-blocking

### Session End (Write)

At session shutdown (Phase 5c checkpoint or Context Capacity Shutdown Protocol):

1. Update `metrics_history.snapshots` with the current session's metrics summary
2. Update `work_queue.known_issues` with context from issues processed this session
3. Increment `session_counter`
4. Update `last_updated` and `governance_version`
5. Apply retention policy — prune snapshots exceeding `max_snapshots` or `max_age_days`
6. Commit the updated `state.json` alongside the checkpoint

### Threshold and Weight Updates

When the threshold auto-tuning policy or persona effectiveness scoring recommends changes:

1. Apply the change to `current_overrides` or `current_weights`
2. Append an entry to the corresponding `history` array
3. Commit as an isolated change (not bundled with implementation commits)

## Concurrent Access

Multiple agent sessions may run concurrently (Phase 5d). The state file uses a **last-writer-wins with merge** strategy:

1. Each session reads state at startup and works from its local copy
2. At session end, before writing:
   - `git pull --rebase` to incorporate any state changes from other sessions
   - If `state.json` has a merge conflict: use a JSON-aware merge (arrays are concatenated, objects are deep-merged, scalars use the newer value)
   - If JSON-aware merge fails: write the session's state to `.governance/state/state-{session-id}.json` as a sidecar and log a warning for manual reconciliation
3. Commit and push

### Conflict Resolution Rules

| Field | Merge Strategy |
|-------|---------------|
| `session_counter` | Take the higher value + 1 |
| `metrics_history.snapshots` | Concatenate, sort by `period_end`, apply retention |
| `threshold_tuning.current_overrides` | Take the most recent `applied_at` per key |
| `threshold_tuning.history` | Concatenate, sort by `timestamp` |
| `persona_weights.current_weights` | Take the most recent change per persona |
| `persona_weights.history` | Concatenate, sort by `timestamp` |
| `work_queue.known_issues` | Merge by `issue_number`, take the most recent `last_interaction` |
| `governance_decisions` | Concatenate arrays, deduplicate by key fields |

## Retention Policy

Retention is configured within the state document itself (`metrics_history.retention_policy`):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_snapshots` | 52 | One year of weekly reports |
| `max_age_days` | 365 | Prune snapshots older than one year |

History arrays (`threshold_tuning.history`, `persona_weights.history`) are unbounded — they provide audit trail and should not be pruned automatically. If they grow excessively (>500 entries), a human should archive older entries.

## Migration Strategy

The schema uses `schema_version` (currently `1.0.0`) for forward compatibility:

| Version Change | Migration Approach |
|----------------|-------------------|
| Patch (1.0.x) | No migration needed — additive optional fields |
| Minor (1.x.0) | Additive required fields — migration script adds defaults |
| Major (x.0.0) | Breaking change — migration script transforms the document; old version archived |

Migration scripts (when needed) will be placed in `bin/migrate-session-state.py` and referenced from `bin/init.sh`. The agent should check `schema_version` on read and warn if it's older than the current schema.

## Integration with Existing Systems

| System | Integration Point |
|--------|-------------------|
| **Checkpoints** (`.governance/checkpoints/`) | Session end writes both a checkpoint and a state update |
| **Autonomy metrics** (`autonomy-metrics.schema.json`) | Metrics reports are referenced by `report_id` in `metrics_history.snapshots` |
| **Persona effectiveness** (`persona-effectiveness.schema.json`) | Effectiveness reports trigger `persona_weights` updates |
| **Retrospective aggregation** (`retrospective-aggregation.schema.json`) | Retrospectives trigger `threshold_tuning` updates |
| **Startup sequence** (`startup.md`) | Session start reads state; session end writes state |
| **Policy engine** | Reads `current_overrides` and `current_weights` to adjust evaluation |

## Security Considerations

- State files should not contain secrets, tokens, or credentials
- `suppressed_findings` must include human attribution — automated suppression is not allowed
- `policy_exceptions` require `granted_by` (human username) — agents cannot grant policy exceptions
- State files are committed to git and visible in repository history — treat all content as semi-public
