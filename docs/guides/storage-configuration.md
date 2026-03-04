# Storage Configuration Guide

## Overview

The governance framework supports configurable storage backends for transient state (sessions, checkpoints, agent logs) and archived artifacts (historical plans, panel reports). By default, transient state is stored locally using XDG-compliant paths, keeping the repository clean.

## Default Behavior (Zero Configuration)

Out of the box, the framework uses **local storage** for transient state:

| Platform | Default Path |
|----------|-------------|
| Linux | `~/.local/state/dark-governance/` |
| macOS | `~/Library/Application Support/dark-governance/` |
| Windows | `%LOCALAPPDATA%/dark-governance/` |

No configuration is needed. The `XDG_STATE_HOME` environment variable overrides the default path on all platforms.

## Configuration

Storage is configured in `project.yaml` under `governance.storage`:

```yaml
governance:
  storage:
    # Where transient state lives during active sessions
    # "local" = XDG-compliant local directory (default, zero config)
    # "repo"  = .artifacts/ in the repo (backward compat)
    state: local

    # Where archived artifacts go after PR merge
    archive: local

    # Backend-specific configuration
    config:
      # Override base directory for local adapter:
      # base_dir: /custom/path/to/state

    # What to keep in-repo vs externalize
    retention:
      plans_in_repo: active_only  # active_only | all | none
      emissions_in_repo: true     # small, static — keep in repo
      panels_in_repo: false       # archive after PR merge
      logs_in_repo: false         # never commit
```

### Storage Backends

| Backend | Key | Description |
|---------|-----|-------------|
| Local | `local` | XDG-compliant local filesystem. Default, zero-config. |
| Repository | `repo` | `.artifacts/` in the repo. Full backward compatibility. |

### Retention Settings

| Setting | Values | Default | Description |
|---------|--------|---------|-------------|
| `plans_in_repo` | `active_only`, `all`, `none` | `active_only` | Plans for open issues stay in repo; archived after merge |
| `emissions_in_repo` | `true`, `false` | `true` | Emission templates are small and static |
| `panels_in_repo` | `true`, `false` | `false` | Panel reports move to archive after merge |
| `logs_in_repo` | `true`, `false` | `false` | Agent logs are never committed |

## Backward Compatibility

To reproduce the current behavior (everything in `.artifacts/`):

```yaml
governance:
  storage:
    state: repo
    archive: repo
    retention:
      plans_in_repo: all
      emissions_in_repo: true
      panels_in_repo: true
      logs_in_repo: true
```

## Programmatic Usage

### Creating an Adapter

```python
from governance.engine.storage import create_adapter

# Default: local XDG storage
adapter = create_adapter()

# From project.yaml config
adapter = create_adapter({"state": "local"})

# Repo-based storage
adapter = create_adapter({
    "state": "repo",
    "config": {"repo_root": "/path/to/repo"}
})
```

### Using the Adapter

```python
# Store data
adapter.put("sessions/s1.json", data_bytes, metadata={"session_id": "s1"})

# Retrieve data
data, metadata = adapter.get("sessions/s1.json")

# List keys
keys = adapter.list("sessions/")

# Delete
adapter.delete("sessions/s1.json")
```

### SessionStore with Adapter

```python
from governance.engine.storage import create_adapter
from governance.engine.orchestrator.session import SessionStore

adapter = create_adapter({"state": "local"})
store = SessionStore.from_adapter(adapter, namespace="sessions")

# Use store as normal
store.save(session)
loaded = store.load("session-id")
latest = store.load_latest()
```

## Migration from Current Layout

When switching from `state: repo` to `state: local`:

1. Existing sessions in `.artifacts/state/sessions/` are not automatically migrated.
2. New sessions will be created in the local storage directory.
3. The orchestrator's `load_latest()` will find sessions in the new location.
4. Old sessions can be manually copied or will age out naturally.

No data loss occurs — the old sessions remain in the repo until manually cleaned up.

## Custom Adapters

To implement a custom storage backend, create a class that implements the `StorageAdapter` protocol:

```python
from governance.engine.storage import StorageAdapter

class MyAdapter:
    def put(self, key: str, data: bytes, metadata: dict | None = None) -> str:
        ...

    def get(self, key: str) -> tuple[bytes, dict]:
        ...

    def list(self, prefix: str = "") -> list[str]:
        ...

    def delete(self, key: str) -> bool:
        ...
```

The adapter must handle:
- Forward-slash-separated keys (e.g., `sessions/s1.json`)
- Metadata as JSON-serializable dicts
- `KeyNotFoundError` for missing keys
- Safe behavior under typical orchestrator usage (e.g., multiple agents/tasks in a single process). Note: the built-in filesystem adapters do not provide cross-process locking or strong atomicity guarantees; if you need stronger concurrency guarantees, implement an appropriate locking/transaction mechanism in your adapter.

## Related

- [Project YAML Configuration](project-yaml-configuration.md)
- [Architecture: Governance Model](../architecture/governance-model.md)
