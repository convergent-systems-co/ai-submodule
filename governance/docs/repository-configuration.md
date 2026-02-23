# Repository Configuration

The governance framework can configure GitHub repository settings to support the autonomous agentic workflow. Settings are declared in `config.yaml` (defaults) and overridden per-project in `project.yaml`.

## Why This Exists

The agentic loop (startup.md) requires specific GitHub repository settings to function: auto-merge must be enabled so PRs merge after CI + approval, CODEOWNERS must be populated so `require_code_owner_review` rulesets work, and branch protection rulesets must be configured for governance enforcement. Without these settings, the autonomous workflow breaks silently.

Previously, these settings were configured manually per-repository. This feature declares them as code in `config.yaml` and applies them during `init.sh` bootstrap.

## Configuration

### Defaults in `config.yaml`

The `repository` section in `config.yaml` provides framework-wide defaults:

```yaml
repository:
  auto_merge: true
  delete_branch_on_merge: true
  allow_squash_merge: true
  allow_merge_commit: true
  allow_rebase_merge: true

  codeowners:
    enabled: true
    default_owner: "@SET-Apps/approvers"
    rules:
      - pattern: "/.github/workflows/"
        owners: ["@SET-Apps/devops_engineers"]
      - pattern: "/infra/"
        owners: ["@SET-Apps/devops_engineers"]
      - pattern: "/.ai"
        owners: ["@SET-Apps/approvers"]

  branch_protection:
    expected_rulesets:
      - name: "Pull Request - Reviewer"
        required_approving_review_count: 1
        require_code_owner_review: true
      - name: "Pull Request - Base"
      - name: "JM Compliance Workflow"
```

### Per-Project Overrides in `project.yaml`

Consuming projects can override any default in their `project.yaml`:

```yaml
repository:
  codeowners:
    rules:
      - pattern: "/src/**/Authentication/"
        owners: ["@SET-Apps/security"]
```

Per-project overrides are merged with defaults. Array fields (like `codeowners.rules`) from `project.yaml` are appended to the defaults, not replaced.

### Schema

The `repository` section is validated against `governance/schemas/project.schema.json`.

## How `init.sh` Applies Settings

When `init.sh` runs, after creating symlinks it:

1. **Checks prerequisites** -- `gh` CLI installed and authenticated
2. **Detects the GitHub repository** from git remotes
3. **Reads configuration** from `config.yaml` (defaults) and `project.yaml` (overrides)
4. **Applies repository settings** via `gh api repos/{owner}/{repo} -X PATCH`
5. **Generates CODEOWNERS** if the file is empty or missing
6. **Validates branch protection** by checking expected rulesets exist (warns on mismatch, does not apply)

### Graceful Degradation

Every step degrades gracefully:

| Condition | Behavior |
|-----------|----------|
| `gh` CLI not installed | Skips repository configuration with instructions to install |
| Not authenticated with `gh` | Skips with instructions to run `gh auth login` |
| Not a GitHub repository | Skips silently |
| Insufficient permissions | Warns and prints manual instructions for a repository admin |
| `config.yaml` has no `repository` section | Skips entirely (backward compatible) |

### Required Permissions

| Operation | Permission Level |
|-----------|-----------------|
| Apply repo settings (auto-merge, merge strategies) | Repository admin |
| Generate CODEOWNERS | Write access (file creation via git) |
| Validate branch protection rulesets | Read access |

## Pre-flight Check in Startup

The agentic startup sequence (`governance/prompts/startup.md`) includes a pre-flight check that verifies repository settings before scanning issues:

1. Checks `allow_auto_merge` is enabled via `gh api`
2. Checks CODEOWNERS file exists and is non-empty
3. If either fails, warns the user and suggests running `bash .ai/init.sh`

This catches misconfiguration before the agentic loop starts, preventing silent failures during PR merge.

## Required Settings for Agentic Loop

| Setting | Required Value | Why |
|---------|---------------|-----|
| `allow_auto_merge` | `true` | PRs auto-merge after CI + approval passes |
| `delete_branch_on_merge` | `true` | Feature branches are cleaned up automatically |
| CODEOWNERS populated | Non-empty file | `require_code_owner_review` rulesets need owners defined |

## Backward Compatibility

The `repository` section is fully optional. If absent from `config.yaml`, `init.sh` skips repository configuration entirely. Existing consuming repos are unaffected until they add the section.
