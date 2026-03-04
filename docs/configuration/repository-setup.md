# Repository Configuration

The governance framework can configure GitHub repository settings to support the autonomous agentic workflow. Settings are declared in `config.yaml` (defaults) and overridden per-project in `project.yaml`.

## Installation Methods

There are two supported installation paths. All other entry points (`quick-install.sh`) are deprecated and redirect to these.

### Path 1 (Primary): Agentic Bootstrap

Tell your AI assistant: "Read and execute `.ai/governance/prompts/init.md`"

This interactively configures the project with zero shell commands. The agent reads the repo, asks about configuration, and sets everything up — including writing instruction files directly (not symlinks), installing PreCompact hooks, and creating governance directories.

### Path 2 (Fallback): Shell Script

```bash
bash .ai/bin/init.sh --quick            # Add submodule (HTTPS) + full init
bash .ai/bin/init.sh --quick --install-deps --mcp  # Full setup with deps + MCP server
bash .ai/bin/init.sh                    # Standard init (submodule already added)
bash .ai/bin/init.sh --install-deps     # Standard init + Python deps
bash .ai/bin/init.sh --mcp             # Also install MCP server for IDE integration
bash .ai/bin/init.sh --uninstall       # Clean removal of governance artifacts
```

The `--quick` flag replaces the deprecated `quick-install.sh` and defaults to HTTPS URLs (no SSH key required). The `--mcp` flag installs the MCP server for IDE prompt distribution. The `--uninstall` flag removes symlinks and the virtual environment.

### Self-Repair

The agentic startup loop (`/startup`) automatically detects and repairs:
- Missing or stale CLAUDE.md / copilot-instructions.md
- Missing PreCompact hooks
- Missing .artifacts/ directories

See `governance/prompts/startup.md` Phase 1a-bis for details.

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
4. **Creates project directories** (`.artifacts/plans/`, `.artifacts/panels/`, `.artifacts/checkpoints/`, `.artifacts/state/`) with `.gitkeep` files, migrating contents from legacy paths if present
5. **Applies repository settings** via `gh api repos/{owner}/{repo} -X PATCH`
6. **Generates or merges CODEOWNERS** — if the file is empty or missing, generates from config; if it already exists, merges governance-required entries (adds missing patterns and owners)
7. **Validates branch protection** by checking expected rulesets exist (warns on mismatch, does not apply)

### Refresh Mode (`--refresh`)

When called with `--refresh`, `init.sh` skips the submodule freshness check and SSH-to-HTTPS conversion (already handled by the caller) but runs all other steps. The agentic startup loop calls this after every submodule state check. Idempotent — a no-op when nothing has changed.

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

## Branch Protection Detection

The `--check-branch-protection` flag queries the GitHub API to determine if the default branch requires pull requests before merging. It outputs a machine-readable result: `REQUIRES_PR=true` or `REQUIRES_PR=false`.

**Detection order:**
1. **Config override** — `repository.branch_protection.require_pr_for_structural_commits` in `config.yaml` or `project.yaml`. If set to `true` or `false`, uses that value directly. Default: `auto`.
2. **Rulesets API** (modern) — queries `gh api repos/{owner}/{repo}/rules/branches/{default_branch}` for a `pull_request` rule type.
3. **Legacy branch protection API** (fallback) — queries `gh api repos/{owner}/{repo}/branches/{default_branch}/protection` for `required_pull_request_reviews`.
4. **Default** — if all API calls fail or return no protection, defaults to `false` (direct commits allowed).

**Usage:**
```bash
REQUIRES_PR=$(bash .ai/bin/init.sh --check-branch-protection 2>/dev/null | grep '^REQUIRES_PR=' | cut -d= -f2)
```

**Behavior when `REQUIRES_PR=true`:**

| Operation | Without Protection | With Protection |
|-----------|-------------------|-----------------|
| Submodule pointer update | `git commit` on main | branch → commit → push → PR → merge |
| CODEOWNERS changes | `git commit` on main | branch → commit → push → PR → merge |
| `project.yaml` updates | `git commit` on main | branch → commit → push → PR → merge |

The agentic startup loop detects this during pre-flight and caches the result for the session. All downstream phases reference the cached flag without re-querying the API.

## Pre-flight Check in Startup

The agentic startup sequence (`governance/prompts/startup.md`) includes a pre-flight check that verifies repository settings before scanning issues:

1. Updates the `.ai` submodule (if not pinned and clean)
2. Runs `bash .ai/bin/init.sh --refresh` to re-apply structural setup (symlinks, workflows, directories, CODEOWNERS, repo settings)
3. Checks `allow_auto_merge` is enabled via `gh api`
4. Checks CODEOWNERS file exists and is non-empty
5. Checks governance workflow (`dark-factory-governance.yml`) exists in `.github/workflows/`
6. If any check fails, warns the user and suggests running `bash .ai/bin/init.sh`

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
| `.artifacts/plans/` | Implementation plans for issues and features | Accumulated — all plans retained |
| `.artifacts/panels/` | Panel review reports | Latest only — overwrite per panel type |
| `.artifacts/checkpoints/` | Context capacity checkpoints (session state) | Session lifecycle |
| `.artifacts/state/` | Cross-session governance state persistence | Accumulated |

### Resource Locations — AI Submodule vs. Consuming Repos

Emitted output uses identical `.artifacts/` paths everywhere. Read-only governance sources differ by the `.ai/` submodule prefix in consumers:

| Resource | AI Submodule | Consuming Repo |
|----------|-------------|----------------|
| Plans | `.artifacts/plans/` | `.artifacts/plans/` |
| Panel reports | `.artifacts/panels/` | `.artifacts/panels/` |
| Checkpoints | `.artifacts/checkpoints/` | `.artifacts/checkpoints/` |
| Cross-session state | `.artifacts/state/` | `.artifacts/state/` |
| Worktrees | `../{repo}-worktree-issue-{N}/` | `../{repo}-worktree-issue-{N}/` |
| Personas | `governance/personas/agentic/` | `.ai/governance/personas/agentic/` (read-only) |
| Review prompts | `governance/prompts/reviews/` | `.ai/governance/prompts/reviews/` (read-only) |
| Policy profiles | `governance/policy/` | `.ai/governance/policy/` (read-only) |
| Schemas | `governance/schemas/` | `.ai/governance/schemas/` (read-only) |
| Instructions | `instructions.md` | `CLAUDE.md` ← `.ai/instructions.md` (file copy, preferred) or symlink (legacy) |

See [Project Structure](../onboarding/project-structure.md) for a detailed breakdown of every directory and file created by `init.sh`.

### Configuration

Directories are declared in `config.yaml` under `project_directories`:

```yaml
project_directories:
  - path: .artifacts/plans
    description: "Implementation plans for issues and features (accumulated)"
  - path: .artifacts/panels
    description: "Panel review reports (latest only per panel type, overwrite strategy)"
  - path: .artifacts/checkpoints
    description: "Context capacity checkpoints (session state)"
  - path: .artifacts/state
    description: "Cross-session governance state persistence (accumulated)"
```

Consuming projects can add additional directories in their `project.yaml`. Directory lists from both files are merged (appended).

### Behavior

- Directories are only created in submodule context (consuming repos, not the Dark Forge repository itself)
- Each directory gets a `.gitkeep` file so git tracks the empty directory
- Idempotent — existing directories are left untouched
- If Python is not available, falls back to the hardcoded defaults (`.artifacts/plans/`, `.artifacts/panels/`, `.artifacts/checkpoints/`, `.artifacts/state/`)
- Automatically migrates contents from legacy paths (`governance/plans/`, `.panels/`, `governance/checkpoints/`, `.governance-state/`) to the new `.artifacts/` structure, preserving old directories for manual cleanup

### Panel Report Convention

Panel reports in `.artifacts/panels/` follow an overwrite strategy: each panel type writes to a fixed filename (e.g., `.artifacts/panels/security-review.json`), replacing the previous report. This keeps only the latest report per panel type, avoiding repository bloat from accumulated review artifacts.

## CODEOWNERS and Governance Workflow Interaction

The Dark Forge governance workflow (`dark-factory-governance.yml`) approves PRs as `github-actions[bot]`. As of v1.0.0, `@github-actions[bot]` is included in all CODEOWNERS entries generated by `init.sh`, so the governance workflow is listed as a code owner.

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

### Dark Forge Repository

The Dark Forge repository itself uses `require_code_owner_review: true` in its org ruleset. CODEOWNERS includes `@github-actions[bot]` alongside `@SET-Apps/approvers` on all patterns. The branch ruleset grants bypass permissions to the governance workflow, allowing the agentic loop to merge PRs after panel review.

### Bot Identity

The governance workflow runs as `github-actions[bot]`, which is a GitHub system account. It cannot be renamed. If a custom bot identity (e.g., "Dark Forge") is desired, a custom GitHub App would need to be created and configured as the workflow's authentication mechanism. This is outside the scope of the governance framework.

## Consuming Repo CI

The `dark-factory-governance.yml` workflow automatically detects consuming repositories and adapts its behavior accordingly.

### Auto-Detection

The workflow uses a three-tier detection strategy:

1. **Directory check** -- looks for `governance/emissions/` (dark-forge repo) or `.ai/governance/emissions/` (consuming repo with cloned submodule)
2. **`.gitmodules` fallback** -- if directory checks fail, the workflow checks `.gitmodules` for a `.ai` submodule entry. This handles the common case where the `.ai` submodule is a private repo and CI lacks credentials to clone it (the submodule appears as a gitlink, not a directory).
3. **Local emissions path** -- consuming repos detected via `.gitmodules` have their emissions checked in `.artifacts/panels/` (the standard local emissions directory created by `init.sh`).

The workflow sets `is_consuming_repo=true` when detection falls through to the `.gitmodules` check.

### Behavior Differences for Consuming Repos

| Feature | AI Submodule Repo | Consuming Repo |
|---------|------------------|----------------|
| Policy engine tests | Runs `pytest governance/engine/tests/` | Skipped (submodule content unavailable) |
| Policy engine evaluation | Full `policy-engine.py` execution | Lightweight emission-only validation |
| Emission location | `governance/emissions/` | `.artifacts/panels/` |
| Policy profiles | Resolved from `governance/policy/` | Fallback to lightweight validation |

### Lightweight Emission Validation

When the full policy engine is unavailable (consuming repo without submodule content), the workflow falls back to a lightweight validator that:

1. Reads JSON emission files from `.artifacts/panels/`
2. Validates required fields (`panel_name`, `verdict`, `confidence_score`) in each emission
3. Computes average confidence across all panels
4. Produces an `auto_merge` decision if all panels pass and average confidence is at or above 0.70, otherwise `human_review_required`

### Configuration Options

Consuming repos have three options for the governance workflow:

- **Vendored policy engine (recommended)** -- During `init.sh` or `init.sh --refresh`, the full policy engine is automatically copied to `.artifacts/engine/` in the consuming repo. This allows cross-org repos to run Tier 1 evaluation in CI without needing to clone the private submodule. The vendored copy includes the policy engine, policy profiles, and schemas. Staleness is tracked via a `VERSION` file and refreshed automatically.
- **Provide local emissions** -- run governance panels locally (via the agentic loop or MCP skills) and commit emission JSON files to `.artifacts/panels/`. The workflow will validate them using the lightweight fallback (Tier 2).
- **Opt out of panel validation** -- set `governance.skip_panel_validation: true` in `project.yaml` (project root). The workflow will auto-approve with a warning instead of blocking.

### Cross-Org CI: Vendored Policy Engine

Consuming repos in different GitHub organizations (e.g., `SET-Sandbox/`) cannot clone `convergent-systems-co/dark-forge` in CI because the `GITHUB_TOKEN` is scoped to the consuming repo's org. Without the submodule, the full Python policy engine is unavailable.

The vendored engine solves this by copying the policy engine into `.artifacts/engine/` during `init.sh`. The governance workflow automatically detects and uses the vendored copy when the submodule is unavailable.

**How it works:**

1. `bash .ai/bin/init.sh` vendors the engine during initial setup
2. `bash .ai/bin/init.sh --refresh` updates the vendored copy when the submodule is updated
3. The CI workflow checks for `.artifacts/engine/policy-engine.py` as a fallback
4. `bash .ai/bin/init.sh --verify` reports vendored engine presence and staleness

**Staleness detection:**

```bash
# Check if the vendored engine is stale
bash .ai/governance/bin/vendor-engine.sh --check

# Force re-vendor even if up-to-date
bash .ai/governance/bin/vendor-engine.sh --force
```

### skip_panel_validation in PRs

The `skip_panel_validation` setting is read from the PR merge commit (not the base branch). This means adding `skip_panel_validation: true` to `project.yaml` in a PR takes effect immediately on that PR -- no need to merge the setting first.

## Backward Compatibility

The `repository` section is fully optional. If absent from `config.yaml`, `init.sh` skips repository configuration entirely. Existing consuming repos are unaffected until they add the section.

The `project_directories` section is also optional. If absent, `init.sh` falls back to creating `.artifacts/plans/`, `.artifacts/panels/`, `.artifacts/checkpoints/`, and `.artifacts/state/` with hardcoded defaults. Existing consuming repos with legacy directory paths (`governance/plans/`, `.panels/`, `governance/checkpoints/`, `.governance-state/`) will have contents migrated automatically to the new `.artifacts/` structure.
