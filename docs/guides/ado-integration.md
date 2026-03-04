# Azure DevOps Integration

Synchronise GitHub issues with Azure DevOps work items. The integration is part of the Dark Forge and lives in `governance/integrations/ado/`.

## Architecture

```
  GitHub                        Dark Forge                       Azure DevOps
  ------                        ------------                       ------------

  Issues  ──webhook──>  SyncEngine  ──REST API 7.1──>  Work Items
  Labels                  |    |                        States
  State                   |    |                        Fields
  Assignees               |    |                        Area/Iteration
                          v    v
                     Ledger  Error Log
                  (.artifacts/state/)
```

The sync engine processes GitHub issue webhook events, maps fields according to `project.yaml` configuration, and creates or updates ADO work items via the REST API. A ledger tracks active mappings and an error log records failures for retry.

## Prerequisites

1. **Azure DevOps organisation and project** -- you need a project where work items will be created.
2. **Personal Access Token (PAT)** -- with at least these scopes:
   - `vso.work_write` -- create and update work items
   - `vso.work_full` -- required if using custom fields or relation management
3. **GitHub repository** -- with webhook delivery enabled (for automated sync) or manual CLI access.
4. **Python 3.10+** with `requests` and `pyyaml` packages.

## Quick Start

Five-minute setup with a PAT:

### 1. Add configuration to `project.yaml`

```yaml
ado_integration:
  schema_version: "1.0.0"
  enabled: true
  organization: https://dev.azure.com/your-org
  project: YourProject
  auth_method: pat
  auth_secret_name: ADO_PAT
  sync:
    direction: github_to_ado
    auto_create: true
    auto_close: true
  state_mapping:
    open: New
    closed: Closed
    "closed+label:bug": Resolved
  type_mapping:
    default: User Story
    bug: Bug
    enhancement: Feature
```

### 2. Set the PAT environment variable

```bash
export ADO_PAT="your-personal-access-token"
```

### 3. Set up custom fields

```bash
python bin/ado-sync.py setup-custom-fields
```

This creates `Custom.GitHubIssueUrl` and `Custom.GitHubRepo` fields in your ADO project (idempotent).

### 4. Test the connection

```bash
python bin/ado-sync.py test-connection
```

### 5. Run a health check

```bash
python bin/ado-sync.py health
```

Expected output:

```
Health Checks:
  [OK] ado_connection: Connected to project 'YourProject'
  [OK] custom_fields: All required custom fields present
  [OK] ledger_integrity: No ledger file (no syncs performed yet)
  [OK] ledger_recency: No ledger file (no syncs performed yet)
  [OK] error_queue: No error log (clean)
  [OK] service_hooks: Sync direction is 'github_to_ado'; no service hooks required

All checks passed.
```

## Configuration Reference

All configuration lives in the `ado_integration` section of `project.yaml`. Validated against `governance/schemas/ado-integration.schema.json`.

### Top-level fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `schema_version` | `string` | `"1.0.0"` | Schema version (must be `"1.0.0"`) |
| `enabled` | `boolean` | `true` | Master on/off switch for the integration |
| `organization` | `string` | (required) | ADO org URL, e.g. `https://dev.azure.com/contoso` |
| `project` | `string` | (required) | ADO project name |
| `auth_method` | `string` | `"pat"` | One of: `pat`, `service_principal`, `managed_identity` |
| `auth_secret_name` | `string` | `"ADO_PAT"` | Environment variable or GitHub secret name for the credential |

### `sync` section

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `direction` | `string` | `"github_to_ado"` | Sync direction: `github_to_ado`, `ado_to_github`, `bidirectional`, `disabled` |
| `auto_create` | `boolean` | `true` | Auto-create ADO work items when GitHub issues are opened |
| `auto_close` | `boolean` | `true` | Auto-close ADO work items when GitHub issues are closed |
| `grace_period_seconds` | `integer` | `5` | Debounce window to prevent echo loops |
| `conflict_strategy` | `string` | `"last_write"` | Conflict resolution: `last_write`, `field_ownership`, `github_wins`, `ado_wins` |
| `sync_comments` | `boolean` | `false` | Sync comments between systems (see [Comment Sync](#comment-sync)) |
| `sync_attachments` | `boolean` | `false` | Sync file attachments |

### `state_mapping` section

Maps GitHub issue states to ADO work item states. Supports compound keys for label-aware mapping.

```yaml
state_mapping:
  open: New                      # GitHub open -> ADO New
  closed: Closed                 # GitHub closed -> ADO Closed
  "closed+label:bug": Resolved   # GitHub closed with 'bug' label -> ADO Resolved
  "open+label:in-progress": Active  # Open with 'in-progress' -> ADO Active
```

Compound keys follow the format `<github_state>+label:<label_name>` and take priority over plain state keys.

### `type_mapping` section

Maps GitHub issue labels to ADO work item types.

```yaml
type_mapping:
  default: User Story   # Fallback when no label matches
  bug: Bug
  enhancement: Feature
  task: Task
  epic: Epic
```

The `default` key is required. When an issue has multiple matching labels, the first match wins.

### `field_mapping` section

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `area_path` | `string` | `""` | Default area path (e.g. `Project\\TeamA`) |
| `iteration_path` | `string` | `"@CurrentIteration"` | Default iteration path |
| `priority_labels` | `object` | `{}` | Label-to-priority mapping (1=Critical, 2=High, 3=Medium, 4=Low) |

```yaml
field_mapping:
  area_path: "MyProject\\Backend"
  iteration_path: "MyProject\\Sprint 1"
  priority_labels:
    P1: 1
    P2: 2
    P3: 3
    P4: 4
```

### `user_mapping` section

Maps GitHub usernames to ADO user email addresses for assignee sync.

```yaml
user_mapping:
  octocat: octocat@example.com
  developer1: dev1@contoso.com
```

### `filters` section

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `include_labels` | `string[]` | `[]` | Only sync issues with these labels (empty = all) |
| `exclude_labels` | `string[]` | `["internal", "governance"]` | Never sync issues with these labels |
| `ado_area_path_filter` | `string` | `""` | Only sync ADO items under this area path (for `ado_to_github`) |

Exclude labels take priority over include labels.

## Authentication

### Personal Access Token (PAT)

The simplest method. Set `auth_method: pat` and provide the token via environment variable.

```yaml
ado_integration:
  auth_method: pat
  auth_secret_name: ADO_PAT  # reads $ADO_PAT
```

Required PAT scopes:
- **Work Items (Read & Write)** -- `vso.work_write`
- **Work Items (Full)** -- `vso.work_full` (for custom fields and relations)

For GitHub Actions, store the PAT as a repository secret named `ADO_PAT`.

### Service Principal (Entra ID)

For automated pipelines. Set `auth_method: service_principal` and provide OAuth2 client credentials.

```yaml
ado_integration:
  auth_method: service_principal
  auth_secret_name: ADO_CLIENT_SECRET
```

Required environment variables:
- `AZURE_TENANT_ID` -- Entra ID tenant
- `AZURE_CLIENT_ID` -- App registration client ID
- `ADO_CLIENT_SECRET` -- Client secret value

The service principal must be added to the ADO project with appropriate permissions.

### Managed Identity

For Azure-hosted compute (App Service, Container Apps, AKS). Set `auth_method: managed_identity`.

```yaml
ado_integration:
  auth_method: managed_identity
```

The `azure-identity` package is imported lazily and only required for this auth method. The managed identity must be assigned to the ADO organisation.

## State Mapping

GitHub issues have two states (`open`/`closed`). ADO work items have process-dependent states. The state mapping bridges this gap.

| GitHub State | Labels | ADO State | Example Config Key |
|-------------|--------|-----------|-------------------|
| `open` | (any) | `New` | `open` |
| `open` | `in-progress` | `Active` | `open+label:in-progress` |
| `open` | `blocked` | `On Hold` | `open+label:blocked` |
| `closed` | (any) | `Closed` | `closed` |
| `closed` | `bug` | `Resolved` | `closed+label:bug` |
| `closed` | `wontfix` | `Removed` | `closed+label:wontfix` |

State mapping evaluation order:
1. Compound keys (`state+label:name`) checked first, all labels tested
2. Plain state key as fallback
3. Built-in default: `open` -> `New`, `closed` -> `Closed`

## Type Mapping

ADO work item types are determined by GitHub issue labels at creation time.

| Label | ADO Type | Notes |
|-------|----------|-------|
| `bug` | `Bug` | |
| `enhancement` | `Feature` | Some processes use "Product Backlog Item" |
| `task` | `Task` | |
| `epic` | `Epic` | |
| (no match) | `User Story` | Configurable via `default` key |

## Field Mapping

| GitHub Field | ADO Field | Notes |
|-------------|-----------|-------|
| `title` | `System.Title` | Always synced |
| `body` | `System.Description` | HTML content |
| `state` | `System.State` | Via state_mapping |
| `assignee` | `System.AssignedTo` | Via user_mapping |
| `labels` (priority) | `Microsoft.VSTS.Common.Priority` | Via priority_labels |
| `milestone.title` | `System.IterationPath` | Used as iteration suffix |
| `html_url` | Hyperlink relation | Added as a linked artifact |
| (computed) | `System.AreaPath` | From field_mapping.area_path |
| `html_url` | `Custom.GitHubIssueUrl` | Custom field |
| `repository.full_name` | `Custom.GitHubRepo` | Custom field |

## Hierarchy Sync

> **Coming soon** -- hierarchy sync (parent-child relationships between ADO work items) is planned for #496. This will allow GitHub issue hierarchies (via task lists) to map to ADO parent-child relations.

## Comment Sync

> **Coming soon** -- comment synchronisation is planned for #496. When `sync.sync_comments: true`, comments will be synced bidirectionally with prefix filtering to prevent echo loops. ADO comments are HTML-only.

## Initial Sync

> **Coming soon** -- the `bin/ado-sync.py initial-sync` command for bulk-syncing existing GitHub issues to ADO is planned for #496.

For now, individual issues can be synced manually:

```bash
python bin/ado-sync.py sync-one 42
```

## Service Hooks (ADO to GitHub)

> **Coming soon** -- full ADO-to-GitHub reverse sync via service hooks is planned for #495.

To prepare for reverse sync:

1. Set `sync.direction: bidirectional` in `project.yaml`
2. In ADO, navigate to **Project Settings > Service Hooks**
3. Create a webhook for "Work item updated" events
4. Point it at your GitHub Actions webhook endpoint

The health check command will warn when bidirectional sync is configured but cannot verify service hooks (requires ADO admin access).

## Operations

### Health Checks

Run the full health check battery:

```bash
python bin/ado-sync.py health
python bin/ado-sync.py health --json   # JSON output
```

Six checks are performed:

| Check | PASS | FAIL | WARN |
|-------|------|------|------|
| `ado_connection` | Connected to project | Auth error or timeout | No client available |
| `custom_fields` | `Custom.GitHubIssueUrl` + `Custom.GitHubRepo` exist | Missing fields | No client available |
| `ledger_integrity` | All entries have required keys, no duplicates | Missing keys or duplicates | - |
| `ledger_recency` | Most recent sync within 24h | - | Stale (>24h) or no timestamps |
| `error_queue` | 0 unresolved errors | Malformed error log | Unresolved errors exist |
| `service_hooks` | Direction is `github_to_ado` | - | Reverse sync configured, verify manually |

Exit code 0 if no FAIL checks; exit code 1 if any FAIL.

### Retry Failed Operations

Process the error queue at `.artifacts/state/ado-sync-errors.json`:

```bash
python bin/ado-sync.py retry-failed              # Retry all
python bin/ado-sync.py retry-failed --dry-run     # Preview only
python bin/ado-sync.py retry-failed --max-retries 5   # Custom limit
python bin/ado-sync.py retry-failed --json        # JSON output
```

Behaviour:
- Unresolved errors with `retry_count < max_retries` are re-attempted
- On success: error is marked `resolved`
- On failure: `retry_count` is incremented
- When `retry_count >= max_retries`: error is marked `dead_letter` and skipped on future runs
- Dry run shows what would happen without executing

### Sync Dashboard

View a summary of sync status:

```bash
python bin/ado-sync.py dashboard
python bin/ado-sync.py dashboard --json   # JSON for programmatic consumption
```

Dashboard metrics:
- **Mappings**: total, active, error, paused
- **Last sync timestamps**: per direction
- **Errors**: today, unresolved, dead-lettered, total

The JSON output structure (under the `ado_sync_status` key) is suitable for embedding in governance emissions or CI dashboards.

### Sync Status (Ledger Detail)

View individual ledger entries:

```bash
python bin/ado-sync.py sync-status
python bin/ado-sync.py sync-status --json
```

## Troubleshooting

### Authentication failures

**Symptom**: `[FAIL] ado_connection: Authentication failed: 401 Unauthorized`

**Fixes**:
1. Verify `ADO_PAT` environment variable is set: `echo $ADO_PAT | head -c 5`
2. Check PAT has not expired in ADO > User Settings > Personal Access Tokens
3. Verify PAT scopes include `vso.work_write`
4. Ensure the PAT was created for the correct organisation

### Rate limiting

**Symptom**: `AdoRateLimitError: 429 Too Many Requests`

The client includes built-in exponential backoff retry (configurable via `max_retries`, `base_delay`, `max_delay` in `AdoConfig`). If you hit persistent rate limits:
1. Reduce sync frequency
2. Increase `sync.grace_period_seconds`
3. Contact your ADO admin about rate limit policies

### Echo loops

**Symptom**: Work items bounce updates back and forth between GitHub and ADO.

The sync engine includes echo detection using the `grace_period_seconds` window and `last_sync_source` tracking. If you see echo loops:
1. Increase `sync.grace_period_seconds` (default: 5)
2. Ensure only one sync direction is active unless you need bidirectional
3. Check that service hooks are not triggering on bot-initiated changes

### Stale ledger

**Symptom**: `[!!] ledger_recency: Most recent sync was 48.0h ago`

This means no sync operations have run recently. Check:
1. GitHub webhook delivery is working (Settings > Webhooks > Recent Deliveries)
2. The GitHub Actions workflow is running
3. The integration is not disabled (`enabled: true`)

### Custom fields not found

**Symptom**: `[FAIL] custom_fields: Missing custom fields: Custom.GitHubIssueUrl`

Run the setup command:
```bash
python bin/ado-sync.py setup-custom-fields
```

If this fails, the PAT may lack `vso.work_full` scope. Custom field creation requires elevated permissions.

### Ledger corruption

**Symptom**: `[FAIL] ledger_integrity: Ledger JSON is malformed`

The ledger at `.artifacts/state/ado-sync-ledger.json` may have been manually edited or corrupted. Options:
1. Fix the JSON manually
2. Delete the file and re-sync (mappings will be recreated)
3. Check git history for the last good version

## End-to-End Testing

The E2E test suite (`governance/integrations/ado/tests/test_bidirectional_e2e.py`) validates the complete bidirectional sync pipeline across 9 phases. It runs in two modes:

- **Mock mode** -- no credentials required, runs in every CI pipeline
- **Live mode** -- requires a real ADO test org, scheduled daily

### Running Mock Tests Locally

```bash
python3 -m pytest governance/integrations/ado/tests/test_bidirectional_e2e.py -x --tb=short -v
```

All mock tests run without any environment variables or ADO credentials. They use mocked ADO and GitHub API responses with isolated temporary ledger and error log files.

### Running Live Tests

Live tests require a dedicated ADO test organisation. Set these environment variables:

```bash
export ADO_PAT="your-e2e-test-pat"
export ADO_ORGANIZATION="SET-Apps-Test"
export ADO_PROJECT="GitHub-ADO-Sync-E2E-Test"
export GITHUB_TOKEN="ghp_your_token"

python3 -m pytest governance/integrations/ado/tests/test_bidirectional_e2e.py -x -m ado_live -v
```

Live tests are marked with `@pytest.mark.ado_live` and are automatically skipped when credentials are not present.

### CI Workflow

The `.github/workflows/test-ado-e2e.yml` workflow runs:

- **Mock tests** on every push/PR that touches `governance/integrations/ado/`
- **Live tests** on a daily schedule (02:00 UTC) and via manual dispatch

Required GitHub Secrets for live tests:

| Secret | Description |
|--------|-------------|
| `ADO_PAT_E2E_TEST` | ADO PAT with `vso.work_write` + `vso.work_full` scopes |
| `ADO_ORGANIZATION` | ADO org name (e.g. `SET-Apps-Test`) |
| `ADO_PROJECT` | ADO project name (e.g. `GitHub-ADO-Sync-E2E-Test`) |

### Test Phases

The E2E suite covers 9 phases:

| Phase | Description | Credentials Required |
|-------|-------------|---------------------|
| 1. Connection & Configuration | Config loading, health checks | No (mock) |
| 2. Forward Sync (GitHub -> ADO) | Create, update, close, reopen, labels, assignees, milestones | No (mock) |
| 3. Reverse Sync (ADO -> GitHub) | State, title, assignee changes; deletion handling | No (mock) |
| 4. Echo Detection | Grace period enforcement, last_sync_source tracking | No (mock) |
| 5. Comments Sync | Bidirectional with prefix filtering, duplicate prevention | No (mock) |
| 6. Bulk Sync | Dry-run, actual sync, duplicate skipping, error handling | No (mock) |
| 7. Error Recovery | Retry logic, dead-lettering, retry_count tracking | No (mock) |
| 8. Health & Dashboard | Populated state validation, metric accuracy, JSON schema | No (mock) |
| 9. Ledger Integrity | Cross-phase consistency, no duplicates, monotonic timestamps | No (mock) |

### Test Configuration

The test configuration lives at `governance/integrations/ado/tests/fixtures/e2e_config.yaml`. It includes bidirectional sync settings, state/type/field/user mappings, and filters. Environment variables override org/project values at runtime.

### Test Fixtures

Webhook payload templates for test scenarios:

- `governance/integrations/ado/tests/fixtures/github_webhook_templates.json` -- GitHub issue events (opened, edited, closed, reopened, labeled, unassigned, milestoned, comments)
- `governance/integrations/ado/tests/fixtures/ado_webhook_templates.json` -- ADO work item events (updated state/title/assignee/priority, deleted, state transitions)

### Setting Up an ADO Test Organisation

1. Create a new ADO organisation (e.g. `SET-Apps-Test`) or use an existing test org
2. Create a project (e.g. `GitHub-ADO-Sync-E2E-Test`) with the Agile process
3. Generate a PAT with `vso.work_write` + `vso.work_full` scopes
4. Run `python bin/ado-sync.py setup-custom-fields` to create custom fields
5. For reverse sync testing: configure a service hook in ADO Project Settings > Service Hooks

### Troubleshooting E2E Tests

**Tests skip with "Live ADO E2E tests require..."**: Set the required environment variables (`ADO_PAT`, `ADO_ORGANIZATION`, `ADO_PROJECT`).

**Mock tests fail with import errors**: Ensure `pyyaml` and `requests` are installed: `pip install pyyaml requests`.

**Live tests fail with 401 errors**: Verify the PAT has not expired and has the required scopes. Check the org/project names match exactly.

**Echo detection tests fail**: Check that the grace period in the test config (`grace_period_seconds: 10`) is sufficient for your environment.

## FAQ

**Q: Can I sync only specific issues?**
A: Yes. Use `filters.include_labels` to whitelist labels, or `filters.exclude_labels` to blacklist them. Exclude takes priority.

**Q: What happens if ADO is down during a sync?**
A: The error is logged to `.artifacts/state/ado-sync-errors.json` with full context. Use `retry-failed` to re-attempt once ADO is back.

**Q: Can I use different ADO work item types for different issue labels?**
A: Yes. Configure `type_mapping` with label-to-type entries. The `default` key provides the fallback.

**Q: Does this support ADO on-premises (Azure DevOps Server)?**
A: The client targets `dev.azure.com` URLs (cloud). On-premises support would require custom `base_url` configuration.

**Q: How do I test without making real ADO changes?**
A: Use `--dry-run` on any write command. The health check also works without a live ADO connection (connection and field checks become WARN).

**Q: What is dead-lettering?**
A: When a failed sync operation exceeds `max_retries` (default: 3), it is marked as `dead_letter` and excluded from future retry runs. This prevents infinite retry loops. Dead-lettered errors should be investigated manually.

**Q: How do I reset the error queue?**
A: Delete `.artifacts/state/ado-sync-errors.json`. A new empty log will be created on the next error.
