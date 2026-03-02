# Goals and Status — Dark Factory Governance Platform

This document tracks the maturity phases, completed work, and open enhancements for the governance platform. Updated as part of the implementation commit (Step 6.4) and verified during the post-merge retrospective.

## Phase Status

| Phase | Name | Description | Status | Key Deliverables |
|-------|------|-------------|--------|------------------|
| 3 | Agentic Orchestration | Personas, panels, workflows with human gates | **Implemented** | Governance personas and panels, agentic workflows, Code Manager + Coder personas |
| 4a | Policy-Bound Autonomy | Deterministic merge decisions, structured emissions | **Implemented** | Governance CI workflow, structured emissions, run manifests, policy profiles |
| 4b | Autonomous Remediation | Auto-fix, drift detection, remediation loops | **Implemented** | Policy engine runtime; drift detection schemas and policy config (PR #69); auto-remediation schemas and workflow (PR #81); incident-to-DI generation schemas and workflow (PR #87) |
| 5 | Dark Factory | Full automation with runtime feedback and self-evolution | **Phase 5a-5e defined** | Sub-phases decomposed with achievability assessment; see Phase 5 section below |
| 6 | Azure DevOps Integration | Bidirectional GitHub Issues to ADO Work Items sync | **Implemented** | ADO API client, sync engine, reverse sync, hierarchy/comments, health/retry/dashboard |

## Completed Work

### Phase 4a — Policy-Bound Autonomy

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #9 | #28 | Policy engine runtime | Deterministic evaluation engine in Python, integrated into governance CI |
| #10 | #31 | Governance CI workflow | `dark-factory-governance.yml` — detect, evaluate, review |
| #11 | #17 | Instruction decomposition | Composable context units per JIT loading strategy |
| #12 | #18 | Auto-propagation workflow | Submodule update propagation to consuming repos |
| #21 | #24 | AI Expert Review panel | Governance-aware panel triggers |
| #22 | #23 | Fix agentic loop | Full PR monitoring, Copilot review handling, merge lifecycle |

### Agentic Infrastructure

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #34 | #37 | Plan tracking best practices | Plan archival to GitHub Releases, retrospective prompt |
| #35 | #39 | Issue templates | Structured feature request and bug report forms |
| #43 | #44 | Context management enforcement | 3-issue cap, mandatory checkpoints, two-tier capacity thresholds |
| #26 | #29 | Branch naming convention | `NETWORK_ID/{type}/{number}/{name}` standard |
| #32 | #33 | Issue labeling | Governance labels (refine, blocked, P0-P4, chore, refactor, ci) |
| #48 | #55 | Agentic loop goals fallback | Startup sequence falls back to GOALS.md when no actionable issues remain |

### Documentation & Structure

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #40 | #45 | README and Goals status update | Comprehensive README rewrite, GOALS.md creation |
| #38 | #46 | Filesystem structure collapse | Consolidated 7 top-level directories under `governance/` |
| #36 | #47 | Dark Factory Next Steps | Goals section in README, Developer Quick Guide, GOALS.md cleanup |
| #49 | #52 | Missing panel emissions | Added security-review and ai-expert-review baseline emissions |
| #50 | #57 | Fix persona/panel counts | Corrected counts in CLAUDE.md and governance model doc |
| #56 | #62 | Root-level convenience files | Added startup.md and init.md at repo root for discoverability |
| #59 | #66 | Windows support | PowerShell bootstrap (init.ps1) with dependency checks and symlink/copy fallback |

### Personas and Panels

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #51 | #60 | Panel pass/fail criteria | Standardized scoring, schema, and local override system for all 15 panels |
| #53 | #64 | Evaluate personas and panels | Added language, platform, and LLM review perspectives + Cost Analysis panel; all non-agentic personas later consolidated into 21 self-contained review prompts (Issue #220) and the 58 separate persona files removed (Issue #257). Only 6 agentic personas remain in `governance/personas/agentic/`. |
| #5 | #13 | Agile Coach persona | Sprint planning, velocity, retrospective guidance (consolidated into review prompts in #220; persona file removed in #257) |
| #6 | #15 | FinOps group | FinOps Engineer and FinOps Analyst personas (consolidated into review prompts in #220; persona files removed in #257) |
| #7 | #16 | MITRE Specialist | Threat modeling panel and MITRE ATT&CK mapping (consolidated into review prompts in #220; persona file removed in #257) |

### Governance Infrastructure

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #68 | #69 | Drift detection schemas and policy config | 2 JSON schemas + 8 YAML policy files for Phase 4b drift detection |
| #71 | #72 | Simplify install with single-command setup | Streamlined bootstrap with venv support |
| #73 | #74 | Issue monitor (local scripts + GitHub Actions) | GitHub Actions workflow + local shell/PowerShell scripts for autonomous issue dispatch |
| #81 | #83 | Auto-remediation loops | 2 JSON schemas (remediation action + verification) + agentic workflow prompt for Phase 4b autonomous remediation |
| #85 | #86 | Fix archive-plans workflow | Branch + PR strategy for plan archival instead of direct push to main |
| #87 | #89 | Incident-to-DI generation | Runtime DI schema, template, and 6-step agentic workflow for Phase 4b |
| #92 | #93 | Backward compatibility enforcement | Breaking change schema + 6-step backward compatibility workflow for Phase 5 |
| #90 | #91 | Template consolidation | Moved plan-template into templates/, updated all references, fixed stale architecture doc paths |
| #80 | #94 | Copilot context management parity | Expanded Copilot detection strategies, Tier 1 instruction module, refine label re-evaluation in startup |
| #96 | #97 | Copilot review hardening | Defense-in-depth jq filters, pre-merge thread verification gate, diagnostic pre-fetch |
| #98 | #99 | Signal adapter configurations | Signal-adapters directory with example polling adapter configs for Phase 5 runtime feedback |
| #100 | #101 | Autonomy metrics and weekly reporting | Metrics schema, health thresholds, and weekly report template for Phase 5 |
| #102 | #104 | Fix agentic loop for PR resolution | Step 0 in startup.md — resolve all open PRs before scanning new issues |
| #105 | #106 | Opt-in auto-merge repository config | Changed auto_merge default to opt-in (false) in config.yaml |
| #107 | #108 | Governance workflow symlinks for consuming repos | init.sh copies governance workflows to consuming repo .github/workflows/ |
| #109 | #111 | Agentic bootstrap prompt (init.md) | Interactive setup prompt for consuming repos — language template, repo settings, dependencies |
| #110 | #121 | governance/plans/ and .panels/ project directories | init.sh creates governance/plans/ and .panels/ directories in consuming repos |
| #112 | #125 | Copilot auto-fix configuration guide | Documentation for configuring GitHub Copilot auto-fix in governance workflow |
| #113 | #115 | Retrospective aggregation schema | JSON Schema for aggregating panel accuracy and override frequency (Phase 5b) |
| #116 | #123 | Auto-update .ai submodule | Startup and init.sh auto-update .ai submodule when behind remote |
| #117 | #118 | Threshold auto-tuning policy | Policy rules for adjusting confidence thresholds from retrospective data (Phase 5b) |
| #120 | #131 | Consuming repo governance review flow | Auto-detect governance root in CI workflow, SSH→HTTPS URL conversion in init.sh |
| #119 | #134 | CODEOWNERS setup | Populated CODEOWNERS, documented governance workflow interaction with code owner reviews |
| #127 | #129 | Reconcile documentation drift | Fixed phase status, added missing completed work, updated file structure across all docs |
| #136 | #137 | Fix init.sh PYTHON_CMD crash | Moved Python detection before symlinks section; fixed `local` outside function |

### Governance Enforcement

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #155 | #156 | Enforce Dark Governance Framework | Mandatory governance pipeline in all modes, CI blocks on missing panels, GOALS.md template in init.sh |
| #126 | #157 | Data Governance Standards enforcement | data-governance-review panel, canonical model compliance, missing-canonical workflow, dach-canonical-models integration |
| #158 | — | Phase 5a Self-Proving Systems | Test governance schema, test-generation panel, proof-of-correctness policy |
| #167 | #168 | Reduced human touchpoint model (Phase 5e) | Near-full-autonomy policy profile; completes Phase 5e Spec-Driven Interface |
| #170 | #171 | Conflict detection schema (Phase 5d) | JSON Schema for multi-agent conflict detection; first Phase 5d governance artifact |
| #173 | #174 | Merge sequencing policy (Phase 5d) | PR ordering rules for multi-agent coordination; second Phase 5d governance artifact |
| #178 | #179 | Governance workflow health check | Startup pre-flight checks verify governance workflow is enabled and healthy |
| #181 | #182 | Parallel session protocol (Phase 5d) | Session lifecycle, work assignment, coordination, and handoff rules; completes Phase 5d governance artifacts |
| #184 | #187 | Cross-repo issue escalation | Escalation schema, workflow prompt, detection criteria, dedup mechanism, project.yaml config extension, policy rules |
| #186 | #188 | Issue state validation | Agents verify issues are still open before starting/resuming work; rule in ANCHOR block propagates to all AI tooling |
| #189 | — | Checkpoint resumption schema and workflow | Formalized checkpoint schema + resumption workflow for Phase 5c |
| #191 | #192 | Event-driven webhook trigger (Phase 5c) | GitHub Actions workflow dispatching governance sessions on issue/deployment events |
| #193 | #194 | Documentation review and README cross-linking | Documentation Index in README, GOALS.md accuracy, DEVELOPER_GUIDE.md links |
| #195 | #197 | Panel tool execution capabilities | Platform-agnostic tool capabilities for all 19 panels |
| #198 | — | Mass parallelization model (Phase 5e) | Orchestrator config, collision domains, integration strategy, integration manifest |
| #200 | #201 | Developer Guide usage patterns and recovery | Recovery & re-entry patterns, diagnostic commands, troubleshooting FAQ |
| #203 | #204 | Simplify Developer Guide | Extracted framework detail to linked pages, 56% line reduction |
| #209 | #211 | Cross-session state persistence (Phase 5c) | Session state schema and storage strategy; completes Phase 5c governance artifacts |
| #220 | — | Persona consolidation — 19 consolidated review prompts, shared perspectives, deprecation notices |

### FinOps and Cost Governance

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #455 | #457 | FinOps review panel | Default required panel across all policy profiles with 5 perspectives (FinOps Strategist, Resource Optimizer, Shutdown/Decommission Analyst, Savings Plan Advisor, Cost Allocation Auditor), destruction safety guardrails requiring human approval, schema extension for destruction_recommended and requires_human_approval fields |

### Schema and Tooling

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #435 | #459 | Schema evolution tooling and emission migration CLI | Schema versioning (`schema_version` field), migration rules directory, chained migration CLI (`governance/bin/migrate-emissions.py`), 25 pytest tests |

### Documentation Site & Tooling

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #336 | #343 | Nord Dark theme for GitHub Pages site | Darkened Polar Night backgrounds by 20% for deeper dark theme |
| #336 | #344 | Hamburger drawer navigation menu | Replaced top tabs with CSS hamburger drawer for all screen sizes |
| #339 | #349 | Consolidate consumer governance outputs | Moved plans, panels, checkpoints, state under unified `.governance/` directory |
| #340 | #341 | Onboarding HTML to MkDocs pages | Converted onboarding HTML to MkDocs pages + AI-assisted install guide |
| #345 | #350 | GitHub repo link in site header | Added repository link to MkDocs site header |
| #347 | #351 | Slash commands reference page | Reference guide for AI tooling chain commands (`/startup`, `/checkpoint`) |
| #348 | #352 | Contributing guide | How-to-contribute page for the governance framework |
| #353 | #354 | Remove Cursor tooling references | Removed all Cursor IDE references; supported tools are now Claude Code and GitHub Copilot |
| #433 | — | Governance dashboard and prompt catalog | Panel catalog, policy comparison, prompt index reference pages; catalog generator script; publish-dashboard CI workflow |

### Developer Experience

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #432 | #461 | Simplify init.sh into modular scripts | Refactored 1,113-line init.sh into 165-line orchestrator + 10 modular scripts in governance/bin/; added --dry-run, --debug flags; quick-install.sh for one-line setup; troubleshooting guide |

### Platform Infrastructure

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #464 | #464 | Project Manager persona | Opt-in portfolio-level orchestrator with multiplexed Code Managers; 6-agent architecture |
| #469 | #486 | Developer prompt library | 12 global prompts in `prompts/global/` for code review, debugging, PR creation, refactoring, test writing |
| — | — | Prompt catalog system | `bin/generate-prompt-catalog.py`, `catalog/prompt-catalog.json`, `prompt-catalog.schema.json`, `prompt-catalog.yml` CI workflow |
| — | — | Skills system | `.skill.md` format in `mcp-server/skills/`, Zod validation, MCP tool registration, `governance-review` skill |
| — | — | MCP server enhancements | Hybrid fetch, IDE auto-installer, `--no-cache`/`--refresh`/`--validate-hash`/`--offline` CLI options, Docker support |
| — | — | Agentic CI workflows | `agentic-issue-worker.yml` (issue-to-PR pipeline) and `agentic-loop.yml` (reusable AI convergence loop) |
| — | — | Self-repair workflows | `auto-rebase.yml`, `branch-cleanup.yml`, `self-repair-lint.yml` |
| — | — | Publishing workflows | `prompt-catalog.yml`, `publish-mcp.yml` (npm + Docker) |
| — | — | Retroactive ADRs | 5 architectural decision records (001-005) in `docs/decisions/` |
| — | — | MIT License | Repository licensed under MIT |
| — | — | Documentation updates | project.yaml configuration guide, CI workflows reference, prompt library guide, skills development guide |
| #432 | #461 | Modular init.sh | 1,113-line script refactored to 165-line orchestrator + 10 modular scripts; `--dry-run`, `--debug` flags; `quick-install.sh` |

### Phase 6 — Azure DevOps Integration

| Issue | PR | Title | Impact |
|-------|----|-------|--------|
| #490 | — | Phase 6 ADO Integration epic | Epic closed — all sub-phases complete |
| #491 | #504 | ADO API client library | Python module wrapping ADO REST API 7.1 |
| #492 | #510 | ADO integration and sync schemas | 3 JSON schemas for config, ledger, errors |
| #493 | #513 | ADO sync CLI tool | `bin/ado-sync.py` with manual sync operations |
| #494 | #514 | GitHub-to-ADO sync engine | Sync engine + GitHub Action workflow |
| #495 | #518 | ADO-to-GitHub reverse sync | Service hooks, reverse mapping, echo prevention |
| #496 | #519 | ADO advanced features | Hierarchy, comments, area/iteration, bulk sync |
| #497 | #520 | ADO operations and health | Health check, retry, dashboard, documentation |

## TODO

- [x] ~~**MkDocs strict build mode** (#366) — Add `mkdocs build --strict` to CI pipeline.~~ (Closed)

## Phase 6 — Azure DevOps Integration

Bidirectional synchronization between GitHub Issues and Azure DevOps Work Items (Epics, Features, Stories, Tasks, Bugs). This enables organizations running ADO for portfolio management to use Dark Factory's GitHub-native governance pipeline while maintaining a single source of truth for project tracking in ADO.

### Problem Statement

Many enterprise teams track work in Azure DevOps Boards (sprints, epics, capacity planning) while using GitHub for code, PRs, and CI/CD. Dark Factory's governance pipeline is GitHub-native — issues drive the agentic loop, PRs carry panel emissions, and the policy engine evaluates merge decisions on GitHub Actions. Without integration, teams must manually duplicate work items across both platforms, leading to drift, stale items, and wasted effort.

### Architecture

```
┌──────────────────┐                           ┌──────────────────┐
│   GitHub Issues   │                           │  ADO Work Items  │
│   (source of      │◄─── Sync Engine ────►    │  (Epics, Stories, │
│    agentic work)  │     (bidirectional)       │   Tasks, Bugs)   │
└────────┬─────────┘                           └────────┬─────────┘
         │                                              │
    Webhooks                                     Service Hooks
    (issue events)                          (workitem.created/updated)
         │                                              │
         ▼                                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                        Sync Mediator                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ Sync Ledger │  │ State Mapper │  │ Conflict Resolution    │  │
│  │ (GH↔ADO ID  │  │ (labels ↔    │  │ (echo prevention,      │  │
│  │  mapping)   │  │  ADO states) │  │  last-write-wins)      │  │
│  └─────────────┘  └──────────────┘  └────────────────────────┘  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ Type Mapper │  │ Hierarchy    │  │ Field Mapper           │  │
│  │ (labels ↔   │  │ Sync (Epic → │  │ (title, desc, assign,  │  │
│  │  WI types)  │  │  Feature →   │  │  priority, area path,  │  │
│  └─────────────┘  │  Story/Task) │  │  iteration, custom)    │  │
│                   └──────────────┘  └────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Authentication Strategy

| Method | Use Case | Security |
|--------|----------|----------|
| **Managed Identity** | Azure-hosted sync (Azure Functions, AKS) | Automatic credential rotation, no secrets to manage |
| **Service Principal (Entra ID OAuth)** | CI/CD pipelines, GitHub Actions | Hourly token expiry, supports Conditional Access |
| **Personal Access Token (PAT)** | Local development, prototyping, CLI tool | Scoped to `vso.work_write`; rotate regularly |

Production deployments should use Managed Identity or Service Principal. PATs are acceptable for development and the CLI tool.

### ADO REST API Integration Points

| Operation | Endpoint | Method | Purpose |
|-----------|----------|--------|---------|
| Create work item | `/_apis/wit/workitems/${type}` | `POST` | Sync new GitHub issue to ADO |
| Update work item | `/_apis/wit/workitems/{id}` | `PATCH` | Sync field changes (title, state, assignment) |
| Get work item | `/_apis/wit/workitems/{id}` | `GET` | Fetch ADO data for reverse sync |
| Query (WIQL) | `/_apis/wit/wiql` | `POST` | Find work items by criteria |
| Batch get | `/_apis/wit/workitemsbatch` | `POST` | Bulk fetch after WIQL query (IDs only then details) |
| Add relation | `/_apis/wit/workitems/{id}` | `PATCH` | Create parent-child links (Epic to Feature to Story) |
| List fields | `/_apis/wit/fields` | `GET` | Discover custom fields |
| Create field | `/_apis/wit/fields` | `POST` | Create `Custom.GitHubIssueUrl` cross-reference field |

API version: **7.1** (stable). All work item mutations use JSON Patch (`application/json-patch+json`).

### Sync Ledger

A persistent mapping between GitHub Issues and ADO Work Items, preventing duplicate creation and enabling bidirectional updates:

```json
{
  "mappings": [
    {
      "github_issue_number": 42,
      "github_repo": "SET-Apps/my-project",
      "ado_work_item_id": 12345,
      "ado_project": "MyProject",
      "ado_work_item_type": "User Story",
      "sync_direction": "github_to_ado",
      "last_synced_at": "2026-02-27T18:00:00Z",
      "last_sync_source": "github",
      "created_at": "2026-02-20T10:00:00Z",
      "sync_status": "active"
    }
  ]
}
```

Storage options: `.governance/state/ado-sync-ledger.json` (git-tracked, simple), Azure Table Storage (scalable), or SQLite (local).

### State Mapping (Agile Process)

| GitHub State | GitHub Labels | ADO State | Direction |
|-------------|---------------|-----------|-----------|
| `open` | (none) | `New` | Bidirectional |
| `open` | `ado:active` | `Active` | Bidirectional |
| `open` | `ado:resolved` | `Resolved` | ADO to GitHub |
| `closed` | (any) | `Closed` | Bidirectional |
| `closed` | `wontfix` | `Removed` | GitHub to ADO |

State mapping is configurable per-project via `project.yaml` to support Agile, Scrum, and CMMI process templates.

### Work Item Type Mapping

| GitHub Signal | ADO Work Item Type | Rationale |
|---------------|-------------------|-----------|
| Issue with `epic` label | Epic | Portfolio-level grouping |
| Issue with `feature` label | Feature | Feature-level tracking |
| Issue (default) | User Story | Standard work item |
| Issue with `task` label | Task | Sub-story breakdown |
| Issue with `bug` label | Bug | Defect tracking |

### Field Mapping

| GitHub Field | ADO Field | Sync Direction |
|-------------|-----------|----------------|
| Title | `System.Title` | Bidirectional |
| Body (description) | `System.Description` | Bidirectional |
| Assignees | `System.AssignedTo` | Bidirectional (first assignee) |
| Labels (priority) | `Microsoft.VSTS.Common.Priority` | GitHub to ADO (`P0`=1, `P1`=2, `P2`=3, `P3`=4) |
| Milestone | `System.IterationPath` | GitHub to ADO |
| Issue URL | `Custom.GitHubIssueUrl` | GitHub to ADO (custom field) |
| Work item URL | Issue comment | ADO to GitHub (pinned comment) |
| State | `System.State` | Bidirectional (via state mapping) |
| Labels (area) | `System.AreaPath` | Configurable |
| Story points (label) | `Microsoft.VSTS.Scheduling.StoryPoints` | Configurable |

### Conflict Resolution

When both platforms update the same item within a configurable grace period:

1. **Echo detection** — If a sync write triggers a webhook on the target platform, the mediator recognizes the `last_sync_source` in the ledger and ignores the echo (default grace period: 5 seconds)
2. **Last-write-wins** — Outside the grace period, the most recent timestamp wins
3. **Field-level merge** — Title and state changes from ADO; description and label changes from GitHub (configurable ownership per field)
4. **Conflict log** — All conflict resolutions are logged to `.governance/state/ado-sync-conflicts.json` for audit

### Hierarchy Sync

ADO's parent-child relationships (Epic to Feature to Story to Task) map to GitHub via:

1. **Issue references** — `parent: #42` in issue body metadata block
2. **ADO link types** — `System.LinkTypes.Hierarchy-Forward` (parent to child) and `System.LinkTypes.Hierarchy-Reverse` (child to parent)
3. **Sync behavior** — When a GitHub issue references a parent, the sync engine creates the ADO hierarchy link. When an ADO work item gains a child, the sync engine adds the reference to the GitHub issue body.

### Configuration (`project.yaml` Extension)

```yaml
ado_integration:
  enabled: true
  organization: "https://dev.azure.com/my-org"
  project: "MyProject"
  auth_method: "service_principal"     # service_principal | managed_identity | pat
  auth_secret_name: "ADO_PAT"         # GitHub secret or env var name

  sync:
    direction: "bidirectional"         # bidirectional | github_to_ado | ado_to_github
    auto_create: true                  # Create ADO items for new GitHub issues
    auto_close: true                   # Close ADO items when GitHub issues close
    grace_period_seconds: 5            # Echo detection window
    conflict_strategy: "last_write"    # last_write | field_ownership | github_wins | ado_wins

  state_mapping:                       # Agile process (default)
    open: "New"
    "open+ado:active": "Active"
    "open+ado:resolved": "Resolved"
    closed: "Closed"
    "closed+wontfix": "Removed"

  type_mapping:
    default: "User Story"
    epic: "Epic"
    feature: "Feature"
    task: "Task"
    bug: "Bug"

  field_mapping:
    area_path: "MyProject\\TeamA"      # Default area path for new items
    iteration_path: "@CurrentIteration" # ADO macro or explicit path

  filters:
    include_labels: []                 # Empty = all issues synced
    exclude_labels: ["internal", "governance"]
    ado_area_path_filter: ""           # Only sync ADO items under this area path
```

### Sub-Phases

**Epic:** #490

| Sub-Phase | Name | Issues | Dependencies | Status |
|-----------|------|--------|--------------|--------|
| 6a | Foundation — Data In/Out | #491 (API client), #492 (Schemas), #493 (CLI tool) | None | **Complete** |
| 6b | GitHub to ADO Sync | #494 (Sync engine + GitHub Action) | 6a | **Complete** |
| 6c | ADO to GitHub Sync | #495 (Service Hook receiver + reverse mapping) | 6a, 6b | **Complete** |
| 6d | Advanced Features | #496 (Hierarchy, comments, area/iteration, bulk sync) | 6b, 6c | **Complete** |
| 6e | Operations and Observability | #497 (Health, retry, dashboard, documentation) | 6b, 6c | **Complete** |

### 6a — Foundation: Data In/Out

The foundation layer provides the core ability to read from and write to Azure DevOps. Everything else builds on this.

- [x] **ADO API client library** — Python module (`governance/integrations/ado/client.py`) wrapping ADO REST API 7.1. Supports work item CRUD, WIQL queries, batch operations, field management, and classification node (area/iteration) queries. Handles authentication (PAT, Service Principal, Managed Identity), rate limiting (TSTU-aware with `Retry-After` header respect), pagination (continuation tokens), and error handling. Full test suite with mocked HTTP responses.
- [x] **Configuration schema** — JSON Schema (`governance/schemas/ado-integration.schema.json`) defining the `ado_integration` section of `project.yaml`. Validates organization URL, auth method, sync direction, state/type/field mappings, filters, and all configurable parameters. Policy engine extended to load and validate ADO config.
- [x] **Sync ledger schema** — JSON Schema (`governance/schemas/ado-sync-ledger.schema.json`) defining the mapping store format. Fields: `github_issue_number`, `github_repo`, `ado_work_item_id`, `ado_project`, `ado_work_item_type`, `sync_direction`, `last_synced_at`, `last_sync_source`, `created_at`, `sync_status`. Storage at `.governance/state/ado-sync-ledger.json`.
- [x] **CLI tool** — `bin/ado-sync.py` providing manual operations: `test-connection` (verify auth), `list-projects`, `list-work-item-types`, `query` (WIQL), `get` (fetch work item), `create` (create work item), `sync-status` (show ledger), `initial-sync` (bulk import). Uses the API client library. Supports `--dry-run` and `--verbose` flags.
- [x] **Custom field provisioning** — Script or CLI subcommand to create `Custom.GitHubIssueUrl` and `Custom.GitHubRepo` custom fields on the ADO organization/process, and add them to relevant work item types. Idempotent (skips if fields already exist).

### 6b — GitHub to ADO Sync

- [x] **Sync engine core** — Python module (`governance/integrations/ado/sync_engine.py`) implementing the mapping logic: state mapping, type mapping, field mapping, ledger management, echo detection. Stateless per-invocation; reads ledger, processes event, writes ledger.
- [x] **GitHub Action workflow** — `.github/workflows/ado-sync.yml` triggered on `issues: [opened, edited, closed, reopened, labeled, unlabeled, assigned, unassigned, milestoned, demilestoned]`. Loads project.yaml config, invokes sync engine, commits ledger updates.
- [x] **Work item creation** — When a GitHub issue is opened and no ledger entry exists: create ADO work item with mapped type, title, description, state, assignment, area/iteration path. Store cross-reference in `Custom.GitHubIssueUrl`. Add pinned comment on GitHub issue with ADO work item link.
- [x] **Work item updates** — When a GitHub issue is edited, closed, reopened, labeled, or assigned: update the corresponding ADO work item fields via JSON Patch. Respect field ownership rules from conflict resolution config.
- [x] **Filter enforcement** — Apply `include_labels` and `exclude_labels` filters before syncing. Issues matching `exclude_labels` are skipped entirely (no ledger entry created).

### 6c — ADO to GitHub Sync

- [x] **Service Hook receiver** — Lightweight HTTP endpoint (Azure Function or GitHub Actions `repository_dispatch` via ADO webhook) that receives ADO `workitem.created`, `workitem.updated`, and `workitem.deleted` events. Validates payload signature, extracts work item ID, invokes sync engine in reverse direction.
- [x] **Reverse state mapping** — ADO state changes update GitHub issue state and `ado:*` labels. `Closed`/`Removed` close the issue. `New`/`Active` reopen it (if closed). `Resolved` adds `ado:resolved` label.
- [x] **Reverse field mapping** — ADO title/description changes update GitHub issue title/body. ADO assignment changes update GitHub assignees (requires user mapping: ADO email to GitHub username).
- [x] **User mapping configuration** — `ado_integration.user_mapping` in `project.yaml`: dictionary mapping ADO user emails to GitHub usernames for assignment sync.
- [x] **Echo prevention** — Before processing an ADO webhook, check ledger `last_sync_source` and `last_synced_at`. If the last sync was from GitHub and within the grace period, skip the update to prevent infinite loops.

### 6d — Advanced Features

- [x] **Hierarchy sync** — When a GitHub issue references `parent: #N` in its body, create `System.LinkTypes.Hierarchy-Reverse` link in ADO pointing to the parent work item. When ADO adds a child link, add the parent reference to the GitHub issue body.
- [x] **Comment sync** — Bidirectional comment sync with attribution (`[Synced from GitHub — @username]` / `[Synced from ADO — User Name]`). Configurable: `sync_comments: true/false` in `project.yaml`. Only sync comments with `[ado-sync]` prefix to avoid noise (opt-in per comment).
- [x] **Area path mapping** — Map GitHub labels prefixed with `area:` to ADO area paths. Example: `area:backend` maps to `MyProject\Backend`. Configurable mapping table in `project.yaml`.
- [x] **Iteration path mapping** — Map GitHub milestones to ADO iteration paths. When an issue is added to a milestone, set the ADO iteration path. Supports `@CurrentIteration` macro.
- [x] **Bulk initial sync** — CLI command `bin/ado-sync.py initial-sync` that reads all open GitHub issues and creates corresponding ADO work items (with ledger entries). Supports `--dry-run`, `--limit`, and `--since` flags. Handles rate limiting gracefully.
- [x] **Attachment sync** — When GitHub issue body contains image links or file attachments, download and attach to the ADO work item (and vice versa). Configurable: `sync_attachments: true/false`.

### 6e — Operations and Observability

- [x] **Health check** — `bin/ado-sync.py health` command that verifies: ADO connection works, custom fields exist, service hooks are configured, ledger is consistent (no orphaned entries), and last sync was recent.
- [x] **Sync dashboard** — Structured emission for sync health: items synced, conflicts resolved, errors, last sync timestamp. Consumable by the governance dashboard.
- [x] **Retry and dead-letter** — Failed sync operations are logged to `.governance/state/ado-sync-errors.json` with full context. CLI command `bin/ado-sync.py retry-failed` processes the error queue.
- [x] **Documentation** — `docs/guides/ado-integration.md` covering: setup, configuration, authentication, state/type mapping, hierarchy sync, troubleshooting, FAQ.
- [x] **ADO Service Hook setup guide** — Step-by-step guide for configuring ADO Service Hooks to point to the receiver endpoint, with filtering by area path and work item type.

## Phase 4b — Remaining Work

The following Phase 4b capabilities are designed but not yet implemented:

- [x] **Drift detection** — Schemas and policy configuration files created (PR #69); runtime implementation pending
- [x] **Auto-remediation loops** — Governance artifacts for autonomous drift remediation (PR #81): remediation action schema, verification schema, and agentic workflow prompt
- [x] **Incident-to-DI generation** — Runtime anomalies automatically create Design Intents (PR #87)

## Phase 5 — Dark Factory (Future)

Architecture is documented in `docs/architecture/runtime-feedback.md`.

### Industry Context

The Phase 5 roadmap is informed by industry maturity models for autonomous software delivery — primarily [Dan Shapiro's 5 Levels of Agentic Coding](https://www.linkedin.com/pulse/5-levels-agentic-coding-dan-shapiro/) and the [Mars Shot MSV-CMM](https://www.mars-shot.dev/) capability maturity model. These frameworks describe a progression from AI-assisted coding (Level 1-2) through autonomous orchestration (Level 3-4) to fully self-evolving systems (Level 5). Dark Factory currently operates at Level 3-4 for governance: autonomous issue-to-merge with policy gates, but without runtime self-evolution or multi-agent coordination. The gap between L3-4 and L5 includes capabilities that require runtime infrastructure beyond what a config-only governance repo can provide.

### Completed Phase 5 Prerequisites

- [x] Runtime feedback loop (anomaly → signal → DI → implementation → deploy) — All governance artifacts implemented: schemas (PR #69), policies (PR #69), templates (PR #89), workflows (PR #83, #89), signal adapters (PR #99)
- [x] Backward compatibility enforcement for governance changes (PR #93)
- [x] Autonomy metrics and weekly reporting dashboard — Metrics schema, health thresholds, and weekly report template (PR #101)

### Sub-Phase Decomposition

| Sub-Phase | Name | Achievable Now? | Rationale |
|-----------|------|-----------------|-----------|
| 5a | Self-Proving Systems | Partially | Can create test governance schemas, test-generation panel definition, proof-of-correctness policy. Cannot build runtime test execution — requires consuming repo integration. |
| 5b | Self-Evolution | Yes (governance artifacts) | Retrospective aggregation schema, threshold auto-tuning policy, persona effectiveness scoring schema, governance change proposal workflow. All are config/schema artifacts. |
| 5c | Always-On Orchestration | Yes (governance artifacts) | All governance artifacts complete: event-driven triggers (PR #192), checkpoint resumption (PR #189), cross-session state persistence (PR #209). Partial CI-native runtime achieved via `agentic-issue-worker` + `agentic-loop` workflows. |
| 5d | Multi-Agent Coordination | Governance artifacts complete; single-session prompt-chaining implemented | All governance artifacts defined. Single-session multi-agent architecture implemented: 6-agent prompt-chained pipeline (Project Manager, DevOps Engineer, Code Manager, Coder, IaC Engineer, Tester) with structured agent protocol. Cross-session parallelism still blocked by AI tooling. |
| 5e | Spec-Driven Interface | Yes (governance artifacts) | Formal spec schema (richer than GitHub issues), acceptance verification workflow, reduced human touchpoint model. All are config artifacts. |

### 5a — Self-Proving Systems (Partially Achievable)

- [x] Test governance schema — JSON Schema defining test coverage expectations, mutation testing thresholds, and proof-of-correctness criteria per policy profile (PR #158)
- [x] Test-generation panel definition — Panel that emits test requirements as structured JSON; consuming repos execute tests via their own CI (PR #158)
- [x] Proof-of-correctness policy — Policy rules that gate merge on formal verification artifacts (type proofs, property tests, contract checks) (PR #158)

### 5b — Self-Evolution (Achievable — Governance Artifacts)

- [x] Retrospective aggregation schema — JSON Schema for collecting panel accuracy, false positive rates, and override frequency across runs (PR #115)
- [x] Threshold auto-tuning policy — Policy that adjusts confidence thresholds based on retrospective data (e.g., lower security threshold after repeated false positives) (PR #118)
- [x] Persona effectiveness scoring schema — Schema tracking per-persona signal-to-noise ratio, enabling automated persona weight adjustment (PR #143)
- [x] Governance change proposal workflow — Agentic workflow where the system proposes governance config changes (new thresholds, persona adjustments) for human approval (PR #147)

### 5c — Always-On Orchestration (Governance Artifacts Complete; Partial CI-Native Runtime)

- [x] Event-driven webhook trigger — GitHub Actions workflow dispatching governance sessions on issue creation, labeling, and deployment status changes (PR #191)
- [x] Automatic checkpoint resumption — Checkpoint schema and resumption workflow for reliable session recovery after context resets (PR #189)
- [x] Cross-session state persistence — Schema and storage strategy for maintaining governance context across multiple agentic sessions (PR #209)
- [x] CI-native agentic runtime — `agentic-issue-worker.yml` (issue-to-PR pipeline with complexity assessment, plan generation, `/agentic-retry:` human feedback loop) and `agentic-loop.yml` (reusable AI convergence loop with checkpoint/resume, judge evaluation, manifest logging)

> **Partially runtime:** All governance artifacts for Phase 5c are complete. CI-native runtime is now partially achieved via `agentic-issue-worker` + `agentic-loop` workflows — issues labeled `agentic-ready` trigger autonomous issue-to-PR pipelines within GitHub Actions. Full always-on orchestration (persistent daemon across sessions) still requires platform capabilities beyond current AI tooling.

### 5d — Multi-Agent Coordination (Single-Session Implemented)

- [x] Conflict detection schema — JSON Schema for detecting when multiple agents modify overlapping files or governance state (PR #171)
- [x] Merge sequencing policy — Policy rules for ordering concurrent agent PRs to avoid conflicts and maintain governance consistency (PR #174)
- [x] Parallel agent session protocol — Specification for spawning, coordinating, and reconciling multiple concurrent agent sessions (PR #181)
- [x] Single-session multi-agent architecture — 6-agent prompt-chained pipeline (Project Manager, DevOps Engineer, Code Manager, Coder, IaC Engineer, Tester) with structured agent protocol, implementing Anthropic's Routing, Orchestrator-Workers, and Evaluator-Optimizer patterns (PR #228, #464)

> **Partially runtime:** Single-session multi-agent coordination is implemented via prompt-chaining (six agents execute within one context window with parallel Coder dispatch). Project Manager mode enables multiplexed Code Managers for higher throughput. Cross-session parallelism (multiple concurrent agent processes) still requires a multi-agent orchestrator, which does not exist in current AI tooling.

### 5e — Spec-Driven Interface (Achievable — Governance Artifacts)

- [x] Formal spec schema — JSON Schema richer than GitHub issue templates: structured acceptance criteria, dependency declarations, risk pre-classification, and machine-verifiable completion conditions (PR #163)
- [x] Acceptance verification workflow — Agentic workflow that validates implementation against spec-defined acceptance criteria before triggering review panels (PR #165)
- [x] Reduced human touchpoint model — Policy profile variant that requires human approval only for policy-override scenarios, with all other decisions fully automated (PR #168)
- [x] Mass parallelization model — Orchestrator config schema, collision domains, integration strategy, integration manifest, and DevOps Integration Agent protocol for multi-agent orchestration (PR #198)

### Sources

- [Dan Shapiro — 5 Levels of Agentic Coding](https://www.linkedin.com/pulse/5-levels-agentic-coding-dan-shapiro/) — Framework defining progression from AI-assisted to fully autonomous coding
- [Mars Shot — MSV-CMM](https://www.mars-shot.dev/) — Capability maturity model for machine-speed software verification
- [Bessemer Venture Partners — Roadmap to AI Coding Agents](https://www.bvp.com/atlas/roadmap-to-ai-coding-agents) — Autonomy scale for AI coding from autocomplete to full agency
- [Addy Osmani — The 70% Problem: Hard Truths About AI-Assisted Coding](https://addyo.substack.com/p/the-70-problem-hard-truths-about) — Analysis of where AI coding agents stall and what's needed to reach full autonomy
