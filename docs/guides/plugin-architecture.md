# Plugin Architecture

The plugin system allows consuming repos to extend the orchestrator without forking or modifying framework source code. Extensions are declared in `project.yaml` and loaded at orchestrator init time.

## Extension Types

### Custom Phases

Scripts that execute as additional orchestrator phases. They run within the same containment and capacity constraints as built-in phases.

```yaml
governance:
  extensions:
    phases:
      - name: deploy
        script: scripts/deploy-phase.py
        after_phase: 5           # Run after Phase 5 (Merge)
        timeout_seconds: 300     # Max execution time (default: 300)
        required: true           # Failure blocks pipeline (default: true)
```

Fields:
- **name** (required): Unique identifier for the phase.
- **script** (required): Path to the script, relative to repo root.
- **after_phase**: Phase number (0-7) after which this plugin runs. Default: 5.
- **timeout_seconds**: Maximum execution time in seconds. Default: 300.
- **required**: If `true`, failure blocks the pipeline. If `false`, advisory only. Default: `true`.

### Custom Panel Types

Prompts that act as additional review panels in the governance pipeline. The policy engine includes their emissions in confidence aggregation.

```yaml
governance:
  extensions:
    panel_types:
      - name: custom-security
        prompt: prompts/custom-security-review.md
        weight: 0.10             # Policy engine weight (default: 0.05)
        required: false          # Required for merge? (default: false)
```

Fields:
- **name** (required): Panel identifier (e.g., `custom-security`).
- **prompt** (required): Path to the prompt markdown file, relative to repo root.
- **weight**: Confidence weight for policy engine aggregation. Range: 0.0-1.0. Default: 0.05.
- **required**: If `true`, emission is required for merge decisions. Default: `false`.

### Lifecycle Hooks

Scripts triggered at specific lifecycle points. All hook scripts receive the repo root as their working directory.

```yaml
governance:
  extensions:
    hooks:
      post_merge:
        - scripts/post-merge.sh
      pre_dispatch:
        - scripts/pre-dispatch.sh
      post_review:
        - scripts/post-review.sh
      on_shutdown:
        - scripts/shutdown.sh
```

Hook points:
- **post_merge**: Runs after a PR is merged.
- **pre_dispatch**: Runs before agent dispatch (Phase 3).
- **post_review**: Runs after review collection (Phase 4).
- **on_shutdown**: Runs on orchestrator shutdown.

## Validation

Extensions are validated at orchestrator init time. Validation checks:

1. **Script/prompt existence**: All referenced files must exist in the repo.
2. **Unique names**: Phase and panel names must be unique within their type.
3. **Range constraints**: `after_phase` must be 0-7, `weight` must be 0.0-1.0, `timeout_seconds` must be non-negative.
4. **Required fields**: `name` and `script`/`prompt` are required for phases and panels.

If validation fails, the orchestrator reports errors and halts.

## Usage

### Programmatic API

```python
from governance.engine.orchestrator.plugins import (
    ExtensionsConfig,
    PluginRegistry,
    validate_extensions,
    execute_hooks,
)

# Parse from project.yaml data
config = ExtensionsConfig.from_dict(project_data["governance"]["extensions"])

# Validate
errors = validate_extensions(config, repo_root="/path/to/repo")
if errors:
    for e in errors:
        print(f"ERROR: {e}")

# Create registry
registry = PluginRegistry(config)

# Look up plugins
phase_plugins = registry.get_phase_plugins(after_phase=5)
panel_plugins = registry.get_panel_plugins()
panel = registry.get_panel_by_name("custom-security")

# Execute hooks
results = execute_hooks("post_merge", registry, repo_root="/path/to/repo")
for result in results:
    print(f"{result.script}: {'OK' if result.success else 'FAILED'}")
```

### Dry-Run Mode

Pass `dry_run=True` to `execute_hooks` or `execute_hook` to simulate execution without actually running scripts. Useful for testing configuration.

```python
results = execute_hooks("post_merge", registry, repo_root, dry_run=True)
```

## Full Example

```yaml
# project.yaml
name: my-service
language: python
governance:
  policy_profile: default
  parallel_coders: 5
  extensions:
    phases:
      - name: e2e-tests
        script: scripts/run-e2e.sh
        after_phase: 4
        timeout_seconds: 600
        required: true
      - name: notify-slack
        script: scripts/slack-notify.py
        after_phase: 5
        required: false
    panel_types:
      - name: performance-review
        prompt: governance/prompts/reviews/performance-review.md
        weight: 0.10
        required: false
      - name: accessibility-review
        prompt: governance/prompts/reviews/a11y-review.md
        weight: 0.05
    hooks:
      post_merge:
        - scripts/update-changelog.sh
      pre_dispatch:
        - scripts/check-dependencies.sh
      on_shutdown:
        - scripts/cleanup.sh
```

## Constraints

- Extension scripts run within the same timeout and containment constraints as built-in phases.
- Hook scripts execute sequentially in the order listed.
- A failing hook does not block subsequent hooks (all hooks in a lifecycle point execute).
- Extension phase failures block the pipeline only if `required: true`.
- The plugin system does not support hot-reloading; extensions are loaded once at init time.
