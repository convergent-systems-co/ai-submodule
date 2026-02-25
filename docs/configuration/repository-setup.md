# Repository Configuration

The governance framework can configure GitHub repository settings to support the autonomous agentic workflow. Settings are declared in `config.yaml` (defaults) and overridden per-project in `project.yaml`.

## Why This Exists

The agentic loop (startup.md) requires specific GitHub repository settings to function: auto-merge must be enabled so PRs merge after CI + approval, CODEOWNERS must be populated so `require_code_owner_review` rulesets work, and branch protection rulesets must be configured for governance enforcement. Without these settings, the autonomous workflow breaks silently.

Previously, these settings were configured manually per-repository. This feature declares them as code in `config.yaml` and applies them during `bin/init.sh` bootstrap.

## Configuration

### Defaults in `config.yaml`

The `repository` section in `config.yaml` provides framework-wide defaults:

```yaml
repository:
  auto_merge: false  # opt-in: set to true in project.yaml to enable
  delete_branch_on_merge: true
  allow_squash_merge: true
  allow_merge_commit: true
  allow_rebase_merge: true

  codeowners:
    enabled: true
    default_owner: "@SET-Apps/approvers @github-actions[bot]"
    rules:
      - pattern: "/.github/workflows/"
        owners: ["@SET-Apps/devops_engineers", "@github-actions[bot]"]
      - pattern: "/infra/"
        owners: ["@SET-Apps/devops_engineers", "@github-actions[bot]"]
      - pattern: "/.ai"
        owners: ["@SET-Apps/approvers", "@github-actions[bot]"]

  branch_protection:
    expected_rulesets:
      - name: "Pull Request - Reviewer"
        required_approving_review_count: 1
        require_code_owner_review: true
      - name: "Pull Request - Base"
      - name: "JM Compliance Workflow"

workflows:
  required:
    - dark-factory-governance.yml
  optional:
    - issue-monitor.yml
    - plan-archival.yml
    - propagate-submodule.yml
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
4. **Creates project directories** (`.plans/`, `.panels/`) with `.gitkeep` files
5. **Applies repository settings** via `gh api repos/{owner}/{repo} -X PATCH`
6. **Generates or merges CODEOWNERS** — if the file is empty or missing, generates from config; if it already exists, merges governance-required entries (adds missing patterns and owners)
7. **Validates branch protection** by checking expected rulesets exist (warns on mismatch, does not apply)

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

## Governance Workflows

The `workflows` section in `config.yaml` declares which governance workflows should be symlinked into consuming repos:

```yaml
workflows:
  required:
    - dark-factory-governance.yml    # Policy engine + auto-approve PRs
  optional:
    - issue-monitor.yml              # Issue lifecycle monitoring
    - plan-archival.yml              # Plan file management
    - propagate-submodule.yml        # Submodule update propagation
```

**Required** workflows are always symlinked; a warning is emitted if the source file is missing. **Optional** workflows are symlinked if present but silently skipped if the source file does not exist.

`init.sh` creates symlinks (not copies) so that submodule updates flow automatically without re-running the script. If a consuming repo already has a regular file at the target path, it is not overwritten — a message instructs the user to remove it to use the symlink.

### Stale Workflow Copies

If a consuming repo copied (rather than symlinked) the governance workflow, the copy will not receive updates when the `.ai` submodule is updated. Stale copies may contain outdated behavior — for example, earlier versions of `dark-factory-governance.yml` auto-approved PRs when no panel emissions were detected.

**To check if your workflow is a symlink or a copy:**

```bash
# Unix/macOS
ls -la .github/workflows/dark-factory-governance.yml
# If it starts with "l" (lrwxr-xr-x), it's a symlink. Otherwise, it's a copy.

# PowerShell
(Get-Item .github\workflows\dark-factory-governance.yml).Attributes
# If it includes "ReparsePoint", it's a symlink.
```

**To fix a stale copy:**

```bash
# Remove the copy and re-run init to create a symlink
rm .github/workflows/dark-factory-governance.yml
bash .ai/bin/init.sh
```

### Backward Compatibility

The legacy `workflows_to_copy` flat list is still supported. If `config.yaml` uses the old key, `init.sh` treats all listed workflows as required.

## Ruleset Validation

`init.sh` validates that expected org/repo rulesets are active by reading `repository.branch_protection.expected_rulesets` from config and checking against `gh api repos/{owner}/{repo}/rulesets`. This is informational — rulesets are validated, not applied (they are typically configured at the org level).

If the API call fails (insufficient permissions), validation is skipped with a warning. Missing rulesets are reported but do not block the script.

## Pre-flight Check in Startup

The agentic startup sequence (`governance/prompts/startup.md`) includes a pre-flight check that verifies repository settings before scanning issues:

1. Checks `allow_auto_merge` is enabled via `gh api`
2. Checks CODEOWNERS file exists and is non-empty
3. Checks governance workflow (`dark-factory-governance.yml`) exists in `.github/workflows/`
4. If any check fails, warns the user and suggests running `bash .ai/bin/init.sh`

This catches misconfiguration before the agentic loop starts, preventing silent failures during PR merge.

## Required Settings for Agentic Loop

| Setting | Required Value | Why |
|---------|---------------|-----|
| `allow_auto_merge` | `true` | PRs auto-merge after CI + approval passes |
| `delete_branch_on_merge` | `true` | Feature branches are cleaned up automatically |
| CODEOWNERS populated | Non-empty file | `require_code_owner_review` rulesets need owners defined |

## Project Directories

`init.sh` creates standard directories in consuming repos for storing governance artifacts. These directories are created in the project root (not inside the `.ai` submodule) so that plans and panel reports are tracked in the consuming repo's own git history.

### Default Directories

| Directory | Purpose | Retention |
|-----------|---------|-----------|
| `.plans/` | Implementation plans for issues and features | Accumulated — all plans retained |
| `.panels/` | Panel review reports | Latest only — overwrite per panel type |

### Configuration

Directories are declared in `config.yaml` under `project_directories`:

```yaml
project_directories:
  - path: .plans
    description: "Implementation plans for issues and features"
  - path: .panels
    description: "Panel reports — only latest per panel type"
```

Consuming projects can add additional directories in their `project.yaml`. Directory lists from both files are merged (appended).

### Behavior

- Directories are only created in submodule context (consuming repos, not the ai-submodule itself)
- Each directory gets a `.gitkeep` file so git tracks the empty directory
- Idempotent — existing directories are left untouched
- If Python is not available, falls back to the hardcoded defaults (`.plans/` and `.panels/`)

### Panel Report Convention

Panel reports in `.panels/` follow an overwrite strategy: each panel type writes to a fixed filename (e.g., `.panels/security-review.json`), replacing the previous report. This keeps only the latest report per panel type, avoiding repository bloat from accumulated review artifacts.

## CODEOWNERS and Governance Workflow Interaction

The Dark Factory governance workflow (`dark-factory-governance.yml`) approves PRs as `github-actions[bot]`. As of v1.0.0, `@github-actions[bot]` is included in all CODEOWNERS entries generated by `init.sh`, so the governance workflow is listed as a code owner.

### How init.sh Manages CODEOWNERS

`init.sh` handles CODEOWNERS in two modes:

- **New file:** If CODEOWNERS is missing or empty, generates the full file from `config.yaml` settings
- **Existing file:** If CODEOWNERS already exists, merges governance-required entries — adds missing patterns and appends missing owners (like `@github-actions[bot]`) to existing patterns. User-added rules are preserved.

This ensures consuming repos that already have a CODEOWNERS file get the governance entries merged in without losing their project-specific rules.

### `require_code_owner_review` Interaction

Even though `@github-actions[bot]` is listed as a code owner, GitHub's behavior with bot approvals and `require_code_owner_review` depends on the repository's ruleset configuration. Choose the approach that fits your organization's security posture:

| Approach | Tradeoff |
|----------|----------|
| **Add bypass actor to branch ruleset** (recommended) | Configure the branch protection ruleset to grant `github-actions[bot]` bypass permissions. The governance workflow can merge after completing panel review. Requires org admin access. |
| **Disable `require_code_owner_review`** | Simplest. Governance workflow approval is sufficient. Loses code ownership enforcement. |
| **Add a machine user as code owner** | Create a GitHub user account (not bot) for the agentic workflow. Add it to CODEOWNERS. The workflow must authenticate as this user (via PAT or SSH key). Maintains code ownership but requires credential management. |
| **Require human code owner review** | Keep `require_code_owner_review` as-is. The governance workflow provides automated review, but a human code owner must also approve before merge. This is the most conservative approach and aligns with `fin_pii_high` and `infrastructure_critical` policy profiles. |

### Recommended Setup by Policy Profile

| Profile | Recommendation |
|---------|---------------|
| `default` | Bypass actor (recommended) or disable `require_code_owner_review` — agentic loop operates autonomously |
| `fin_pii_high` | Require human code owner review — auto-merge is already disabled, human approval is expected |
| `infrastructure_critical` | Require human code owner review — mandatory architecture and SRE review already in policy |

### ai-submodule Repository

The ai-submodule itself uses `require_code_owner_review: true` in its org ruleset. CODEOWNERS includes `@github-actions[bot]` alongside `@SET-Apps/approvers` on all patterns. The branch ruleset grants bypass permissions to the governance workflow, allowing the agentic loop to merge PRs after panel review.

### Bot Identity

The governance workflow runs as `github-actions[bot]`, which is a GitHub system account. It cannot be renamed. If a custom bot identity (e.g., "Dark Factory Governance") is desired, a custom GitHub App would need to be created and configured as the workflow's authentication mechanism. This is outside the scope of the governance framework.

## Backward Compatibility

The `repository` section is fully optional. If absent from `config.yaml`, `init.sh` skips repository configuration entirely. Existing consuming repos are unaffected until they add the section.

The `project_directories` section is also optional. If absent, `init.sh` falls back to creating `.plans/` and `.panels/` with hardcoded defaults. Existing consuming repos that already have these directories are unaffected (idempotent).
