# Slash Commands

The Dark Forge provides slash commands for initiating and managing autonomous workflows. These commands are available in both Claude Code and GitHub Copilot, with platform-specific implementations.

## Available Commands

| Command | Purpose | Availability |
|---------|---------|--------------|
| `/startup` | Initiates the autonomous agentic loop | Claude Code, GitHub Copilot |
| `/checkpoint` | Saves session state and executes context capacity shutdown protocol | Claude Code, GitHub Copilot |
| `/threat-model` | Runs threat model analysis (system-level or PR-level) | Claude Code, GitHub Copilot |
| `/review` | Review panel router — list, run, and inspect governance review panels | Claude Code, GitHub Copilot |
| `/plan` | Governance plan management — list, create, and show plans | Claude Code, GitHub Copilot |
| `/governance` | Pipeline dashboard — status, policy, and emissions | Claude Code, GitHub Copilot |
| `/issue` | Issue triage and planning without the full startup loop | Claude Code, GitHub Copilot |

## `/startup` - Agentic Loop

The `/startup` command begins the autonomous improvement loop, executing the full five-phase governance pipeline.

### What It Does

The `/startup` command instructs the LLM to read `startup.md`, which directs it to call the Python orchestrator CLI (`python -m governance.engine.orchestrator`). The orchestrator is the sole control plane — it holds the program counter, enforces capacity gates, and persists all state to disk.

1. **Init** — `python -m governance.engine.orchestrator init` checks for existing sessions/checkpoints and returns the first phase instruction
2. **Phase 1: Pre-flight & Triage** — Scan and prioritize issues, select work batch
3. **Phase 2: Planning** — Create implementation plans for each selected issue
4. **Phase 3: Dispatch** — Spawn parallel Coder agents per orchestrator's task list
5. **Phase 4: Collect & Review** — Wait for agents, run Test Evaluator evaluation (up to 3 FEEDBACK cycles)
6. **Phase 5: Merge & Loop** — Merge approved PRs; orchestrator decides to loop or finish

The LLM reports capacity signals as it works. The orchestrator enforces gate checks at every phase boundary and triggers shutdown when Orange+ tier is reached.

### Usage

=== "Claude Code"

    ```bash
    /startup
    ```

    The agent will:
    - Read and execute `governance/prompts/startup.md`
    - Call the Python orchestrator CLI between each phase
    - Dispatch parallel Coder agents (up to N = `governance.parallel_coders`, default 5; all issues when N = -1)
    - Process up to N issues per session (unlimited when N = -1)
    - Orchestrator triggers shutdown at 80% context capacity
    - All state persists to disk — survives context resets

    For continuous unattended operation:
    ```bash
    bash bin/auto-clear.sh
    ```

=== "GitHub Copilot"

    ```bash
    /startup
    ```

    The agent will:
    - Read and execute `.ai/governance/prompts/startup.md`
    - Call the Python orchestrator CLI between each phase
    - Follow sequential Coder execution (Copilot does not support parallel Task dispatch)
    - Process up to N issues per session (N = `parallel_coders`, default 5; unlimited when N = -1)
    - Prompt for new chat thread at context capacity threshold

### Constraints

- Maximum N issues per session (N = `parallel_coders`, default 5; unlimited when N = -1)
- Maximum 3 review cycles per PR before escalation
- Plans required before implementation
- Documentation updates mandatory with every change
- Hard stop at 80% context capacity

### Configuration

The number of parallel Coder agents can be configured in `project.yaml`:

```yaml
governance:
  parallel_coders: 5  # Default: 5, Range: 1-10 or -1 (unlimited, context-monitored)
```

## `/checkpoint` - Context Capacity Shutdown

The `/checkpoint` command executes the Context Capacity Shutdown Protocol, preserving session state for later resumption.

### What It Does

1. **Stops execution** - Halts all in-progress tasks immediately
2. **Cleans git state** - Commits WIP changes, aborts merges/rebases, verifies working tree is clean
3. **Writes checkpoint file** - Saves session state to `.artifacts/checkpoints/{timestamp}-{branch}.json`
4. **Reports to user** - Summarizes completed work, remaining work, checkpoint location
5. **Offers context reset** - Prompts for `/clear` (Claude Code) or new chat thread (Copilot)

### Usage

=== "Claude Code"

    ```bash
    /checkpoint
    ```

    The agent will:
    - Write checkpoint to `.artifacts/checkpoints/{timestamp}-{branch}.json`
    - Report summary with completed/remaining work
    - Offer `/clear` to reset context
    - Provide resume command: `Resume from checkpoint: .artifacts/checkpoints/{file}`

=== "GitHub Copilot"

    ```bash
    /checkpoint
    ```

    The agent will:
    - Write checkpoint to `.artifacts/checkpoints/{timestamp}-{branch}.json`
    - Report summary with completed/remaining work
    - Prompt to start new chat thread
    - Provide resume command: `Resume from checkpoint: .artifacts/checkpoints/{file}`

### Checkpoint Format

Checkpoint files contain session state in JSON format:

```json
{
  "timestamp": "2026-02-25T14:30:00Z",
  "branch": "main",
  "issues_completed": ["#123", "#124"],
  "prs_resolved": ["#45", "#46"],
  "issues_remaining": ["#125", "#126"],
  "prs_remaining": ["#47"],
  "current_issue": "#127",
  "current_step": "Phase 3: Implementation in progress",
  "git_state": "clean",
  "pending_work": "Finish implementing #127, run security review",
  "prs_created": ["#48", "#49"],
  "manifests_written": ["manifest-20260225-143000"],
  "branches_touched": ["NETWORK_ID/feat/123/add-feature", "main"],
  "review_cycle": null
}
```

### When to Use

Use `/checkpoint` when:

- Context capacity reaches 80% (hard requirement)
- Conversation exceeds ~30 turns
- Response quality degrades
- You need to pause work and resume later
- Context compaction is imminent

### Important Notes

- Never allow context to compact with dirty git state
- Always clean working tree before checkpoint
- Checkpoints are session-scoped - they do not persist across repository clones

## `/threat-model` - Threat Model Analysis

The `/threat-model` command runs a structured threat model using the 15-section, 9-participant review framework with 5 parallel review tracks.

### Modes

| Argument | Mode | Description |
|----------|------|-------------|
| `system` | System-level | Full platform/application threat model covering all trust boundaries, components, and data flows |
| `pr` | PR-level (current branch) | Threat model scoped to the current branch's PR diff |
| `pr=N` | PR-level (specific PR) | Threat model scoped to a specific PR number (e.g., `pr=345`) |
| *(no args)* | PR-level (current branch) | Defaults to `pr` mode |

### Usage

=== "Claude Code"

    ```bash
    /threat-model system         # Full system threat model
    /threat-model pr             # Current branch PR threat model
    /threat-model pr=345         # Specific PR threat model
    /threat-model                # Defaults to PR mode
    ```

=== "GitHub Copilot"

    ```bash
    /threat-model system         # Full system threat model
    /threat-model pr             # Current branch PR threat model
    /threat-model pr=345         # Specific PR threat model
    /threat-model                # Defaults to PR mode
    ```

### Output

| Mode | Output Location | Emission Location |
|------|----------------|-------------------|
| `system` | `.artifacts/panels/threat-model-system.md` | `.artifacts/emissions/threat-model-system.json` |
| `pr` / `pr=N` | `.artifacts/panels/threat-modeling.md` | `.artifacts/emissions/threat-modeling.json` |

### Review Tracks

Both modes use the same 5-track, 9-participant structure:

| Track | Sub-Moderator | Participants |
|-------|--------------|-------------|
| 1. Infrastructure Security | Infrastructure Security Engineer | Systems Architect, Infrastructure Engineer |
| 2. Supply Chain Security | Supply Chain Security Specialist | MITRE Analyst (ATT&CK), Security Auditor |
| 3. Application Security | Application Security Engineer | MITRE Analyst (STRIDE), Red Team Engineer |
| 4. DevSecOps & AI Safety | DevSecOps & AI Safety Engineer | Purple Team Engineer, Blue Team Engineer |
| 5. Data Privacy & Compliance | Data Privacy & Information Security | Compliance Officer, Security Auditor |

### 15 Output Sections

1. Systems Architect: Architecture Presentation (with Mermaid data flow diagrams)
2. MITRE Analyst: Trust Boundary Crossings
3. MITRE Analyst: STRIDE Threat Catalog (per boundary)
4. Red Team Engineer: Attack Path Validation (ATK-01 through ATK-N)
5. Infrastructure Engineer: Configuration Assessment (INFRA-01 through INFRA-N)
6. Blue Team Engineer: Detection & Response Coverage
7. Purple Team Engineer: MITRE ATT&CK Mapping (with heat map)
8. Security Auditor: Vulnerability Classification (CVSS 3.1 scoring)
9. MITRE Analyst: Threat Actor Profiles
10. MITRE Analyst: Attack Trees (Mermaid graphs)
11. Compliance Officer: Regulatory Impact (SOC 2, GDPR, NIST)
12. Prioritized Threat Register
13. Mitigation Roadmap (with Mermaid Gantt chart)
14. Residual Risk Summary
15. Threat Posture Assessment

**Appendices:** STRIDE Risk Heat Map, Sigma Detection Rules (YAML), Purple Team Validation Exercises

### Key Differences Between Modes

| Aspect | System Mode | PR Mode |
|--------|-------------|---------|
| Scope | Entire system/platform | PR diff only |
| Threat actor profiles | Full profiles for all relevant actors | Only if PR introduces external-facing surface |
| Attack trees | All major objectives | Only for complex PR-introduced paths |
| Configuration assessment | All infrastructure | Only modified configs |
| Sigma rules | Full detection suite | Only new detection needs |
| Governance pipeline | On-demand (not a per-PR gate) | Runs on every PR |
| Panel name | `threat-model-system` | `threat-modeling` |

### Governance Pipeline Integration

The PR-level variant (`threat-modeling`) is included in `required_panels` for 4 of the 5 policy profiles and runs automatically on every PR (excluded from the fast-track profile). The system-level variant (`threat-model-system`) is on-demand only and is not included in any policy profile's required panels.

### Prompt Files

| Mode | Prompt Location (submodule) | Prompt Location (consuming repo) |
|------|---------------------------|--------------------------------|
| System | `governance/prompts/reviews/threat-model-system.md` | `.ai/governance/prompts/reviews/threat-model-system.md` |
| PR | `governance/prompts/reviews/threat-modeling.md` | `.ai/governance/prompts/reviews/threat-modeling.md` |

## `/review` - Review Panel Router

The `/review` command makes governance review panels discoverable and runnable on-demand. It can list available panels, display shared perspectives, run any panel against a PR diff, and show the status of existing panel emissions.

### Modes

| Argument | Mode | Description |
|----------|------|-------------|
| `list` | List panels | List all review prompts with name, purpose, and participant count |
| `perspectives` | List perspectives | List shared perspectives with role and focus area |
| `run <panel>` | Run panel (current branch) | Run a specific panel against the current branch's PR diff |
| `run <panel> pr=N` | Run panel (specific PR) | Run a specific panel against PR #N's diff |
| `status` | Emission status | Show current panel emissions with verdicts and scores |
| *(no args)* | List panels | Defaults to `list` mode |

### Usage

=== "Claude Code"

    ```bash
    /review                          # List all available panels
    /review list                     # List all available panels
    /review perspectives             # List shared perspectives
    /review run code-review          # Run code-review against current branch PR
    /review run security-review pr=42  # Run security-review against PR #42
    /review status                   # Show emission verdicts and scores
    ```

=== "GitHub Copilot"

    ```bash
    /review                          # List all available panels
    /review list                     # List all available panels
    /review perspectives             # List shared perspectives
    /review run code-review          # Run code-review against current branch PR
    /review run security-review pr=42  # Run security-review against PR #42
    /review status                   # Show emission verdicts and scores
    ```

### Output

| Mode | Output Location | Emission Location |
|------|----------------|-------------------|
| `list` | Displayed in conversation | N/A |
| `perspectives` | Displayed in conversation | N/A |
| `run <panel>` / `run <panel> pr=N` | `.artifacts/panels/<panel>.md` | `.artifacts/emissions/<panel>.json` |
| `status` | Displayed in conversation | N/A |

### Available Panels

The 21 review panels in `governance/prompts/reviews/` cover:

- **Code quality:** `code-review`, `testing-review`, `test-generation-review`, `technical-debt-review`
- **Security:** `security-review`, `threat-modeling`, `threat-model-system`
- **Architecture:** `architecture-review`, `api-design-review`, `data-design-review`
- **Operations:** `performance-review`, `production-readiness-review`, `cost-analysis`, `finops-review`
- **Governance:** `documentation-review`, `data-governance-review`, `governance-compliance-review`, `migration-review`
- **Specialized:** `ai-expert-review`, `copilot-review`, `jm-standards-compliance-review`

### Prompt Files

| Resource | Prompt Location (submodule) | Prompt Location (consuming repo) |
|----------|---------------------------|--------------------------------|
| Review prompts | `governance/prompts/reviews/*.md` | `.ai/governance/prompts/reviews/*.md` |
| Shared perspectives | `governance/prompts/shared-perspectives.md` | `.ai/governance/prompts/shared-perspectives.md` |

## `/plan` - Plan Management

The `/plan` command manages governance plans without entering the full startup loop. Plans are mandatory before implementation per governance rules.

### Modes

| Argument | Mode | Description |
|----------|------|-------------|
| `list` | List plans | Lists all plans in `.artifacts/plans/` with issue number, title, status, and date |
| `create <N>` | Create plan | Creates a plan from template for issue #N using `gh issue view` |
| `show <N>` | Show plan | Reads and displays the existing plan for issue #N |
| *(no args)* | Help | Shows help text with available subcommands |

### Usage

=== "Claude Code"

    ```bash
    /plan list               # List all governance plans
    /plan create 42          # Create plan for issue #42
    /plan show 42            # Display plan for issue #42
    /plan                    # Show help text
    ```

=== "GitHub Copilot"

    ```bash
    /plan list               # List all governance plans
    /plan create 42          # Create plan for issue #42
    /plan show 42            # Display plan for issue #42
    /plan                    # Show help text
    ```

### Plan Creation Workflow

The `create <N>` mode:

1. Verifies the issue is open via `gh issue view`
2. Checks for existing plans (warns if one exists)
3. Reads the plan template from `governance/templates/prompts/plan-template.md`
4. Generates a plan populated from the issue body
5. Saves to `.artifacts/plans/{N}-{slug}.md` with `draft` status

### Output

| Mode | What Is Displayed |
|------|-------------------|
| `list` | Table: Issue, Title, Status, Date |
| `create <N>` | Plan file location, confirmation, reminder that status is `draft` |
| `show <N>` | Full plan content |

### Prompt Files

| Resource | Location (submodule) | Location (consuming repo) |
|----------|---------------------|--------------------------|
| Plan template | `governance/templates/prompts/plan-template.md` | `.ai/governance/templates/prompts/plan-template.md` |
| Plans directory | `.artifacts/plans/` | `.artifacts/plans/` |

## `/governance` - Pipeline Dashboard

The `/governance` command displays a read-only dashboard view of the governance pipeline state, including policy configuration, required panels, and panel emission results.

### Modes

| Argument | Mode | Description |
|----------|------|-------------|
| `status` | Pipeline status | Shows policy profile, required vs present panels, compliance gaps |
| `policy` | Policy details | Shows active policy profile requirements, thresholds, scoring |
| `emissions` | List emissions | Lists all emissions in `.artifacts/emissions/` with verdicts and scores |
| *(no args)* | Pipeline status | Defaults to `status` mode |

### Usage

=== "Claude Code"

    ```bash
    /governance status       # Pipeline status dashboard
    /governance policy       # Active policy profile details
    /governance emissions    # List all panel emissions
    /governance              # Defaults to status mode
    ```

=== "GitHub Copilot"

    ```bash
    /governance status       # Pipeline status dashboard
    /governance policy       # Active policy profile details
    /governance emissions    # List all panel emissions
    /governance              # Defaults to status mode
    ```

### What Each Mode Shows

#### `status` (default)

Reads `project.yaml` to determine the active policy profile, loads the policy to get `required_panels`, scans `.artifacts/emissions/` for existing emissions, and displays:

- **Profile**: active policy profile name and version
- **Required Panels**: table showing each panel's presence status, confidence score, risk level, and verdict
- **Compliance Summary**: count of present vs required panels and aggregate compliance state

#### `policy`

Reads and displays the full active policy profile configuration:

- **Profile Identity**: name, version, description
- **Required Panels**: list of mandatory panels
- **Confidence Weighting**: weighting model and per-panel weight table
- **Auto-Merge Conditions**: enabled status and required conditions
- **Escalation Rules**: triggers and actions for human review
- **Block Rules**: hard-block conditions

#### `emissions`

Scans `.artifacts/emissions/*.json` for structured emissions and displays:

- **Emissions Table**: Panel | Version | Confidence | Risk Level | Compliance | Findings | Verdict | Human Review
- **Highlights**: flags panels with `risk_level` of `critical` or `high`
- Reports if no emissions exist yet

### Output

This is a read-only command. No files are written or modified. All output is displayed in the conversation.

### Policy Profile Resolution

The command resolves the active policy profile:

1. `governance.policy_profile` in `project.yaml` (project root)
2. Falls back to `default` if not configured

Policy files are read from `governance/policy/{profile}.yaml` (submodule) or `.ai/governance/policy/{profile}.yaml` (consuming repo).

## `/issue` - Issue Triage & Planning

The `/issue` command provides quick issue triage and planning without entering the full startup loop. It can show the next actionable issue or create a branch and plan for a specific issue.

### Modes

| Argument | Mode | Description |
|----------|------|-------------|
| `next` | Show next issue | Shows highest-priority actionable issue with triage details |
| `plan <N>` | Plan issue | Creates branch and plan for issue #N without implementing |
| *(no args)* | Show next issue | Defaults to `next` mode |

### Usage

=== "Claude Code"

    ```bash
    /issue                   # Show next actionable issue
    /issue next              # Show next actionable issue
    /issue plan 42           # Create branch and plan for issue #42
    ```

=== "GitHub Copilot"

    ```bash
    /issue                   # Show next actionable issue
    /issue next              # Show next actionable issue
    /issue plan 42           # Create branch and plan for issue #42
    ```

### Next Issue Logic

The `next` mode finds the highest-priority actionable issue:

1. Fetches up to 50 open issues via `gh issue list`
2. Filters out non-actionable issues:
   - Issues with existing branches matching `*/feat/*`, `*/fix/*`, `*/chore/*`, or `feature/*` patterns
   - Issues labeled `blocked`, `wontfix`, or `duplicate`
   - Issues assigned to humans (empty assignees or bot-assigned only)
3. Prioritizes by: P0 > P1 > P2 > P3 > P4 (label-based), then creation date (oldest first). Bugs take precedence over enhancements at the same priority level.
4. Displays the top issue with number, title, labels, body summary, and recommended branch name

### Plan Mode Workflow

The `plan <N>` mode:

1. Verifies the issue is open via `gh issue view`
2. Reads issue details (number, title, body, labels)
3. Creates branch: `itsfwcp/{type}/{N}/{slug}` (type derived from labels: `bug` → `fix`, `enhancement` → `feat`, default `feat`)
4. Reads plan template from `governance/templates/prompts/plan-template.md`
5. Creates plan following the template structure
6. Saves to `.artifacts/plans/{N}-{slug}.md`
7. Stops after plan creation — does NOT implement

### Branch Naming

Branches follow the convention: `NETWORK_ID/{type}/{number}/{slug}`

| Label | Branch Type |
|-------|-------------|
| `bug` | `fix` |
| `enhancement` | `feat` |
| *(default)* | `feat` |

The slug is a lowercase kebab-case summary of the issue title, max 40 characters.

### Output

| Mode | What Is Displayed |
|------|-------------------|
| `next` | Issue number, title, labels, body summary, recommended branch name, suggested next step (`/issue plan <N>`) |
| `plan <N>` | Branch name, plan file location, confirmation that implementation is deferred |

## Context Capacity Protocol

Both commands integrate with the framework's context management system. The protocol enforces a hard stop at 80% context capacity to prevent instruction loss during compaction.

### Warning Signs

- Conversation turn count exceeding 30
- Response character count exceeding ~200K
- Degraded response quality
- Repeated clarification requests
- Token budget warnings

### Protocol Steps

1. Agent detects capacity threshold
2. Stops all work immediately
3. Cleans git state (commits WIP, aborts conflicts)
4. Writes checkpoint to persistent storage
5. Reports summary to user
6. Requests context reset

See [Context Management](../architecture/context-management.md) for the full protocol specification.

## Platform Differences

| Feature | Claude Code | GitHub Copilot |
|---------|-------------|----------------|
| Parallel Coder dispatch | Yes (up to N agents) | No (sequential only) |
| Context reset mechanism | `/clear` command | New chat thread |
| Checkpoint directory | `.artifacts/checkpoints/` | `.artifacts/checkpoints/` |
| Task isolation | Worktrees via `Task` tool | Branch switching |
| Max issues per session | 5 | 5 |
| Context capacity threshold | 80% | ~30 turns or 200K chars |

## Implementation Files

The slash commands are implemented in these files:

- **Claude Code:**
  - `.claude/commands/startup.md` - Startup command definition
  - `.claude/commands/checkpoint.md` - Checkpoint command definition
  - `.claude/commands/threat-model.md` - Threat model command definition
  - `.claude/commands/review.md` - Review panel router command definition
  - `.claude/commands/plan.md` - Plan management command definition
  - `.claude/commands/governance.md` - Governance dashboard command definition
  - `.claude/commands/issue.md` - Issue triage and planning command definition

- **GitHub Copilot:**
  - `.github/copilot-chat/startup.md` - Startup command definition
  - `.github/copilot-chat/checkpoint.md` - Checkpoint command definition
  - `.github/copilot-chat/threat-model.md` - Threat model command definition
  - `.github/copilot-chat/review.md` - Review panel router command definition
  - `.github/copilot-chat/plan.md` - Plan management command definition
  - `.github/copilot-chat/governance.md` - Governance dashboard command definition
  - `.github/copilot-chat/issue.md` - Issue triage and planning command definition

- **Core workflow:**
  - `governance/prompts/startup.md` - Agentic loop specification
  - `governance/personas/agentic/` - Agent persona definitions
  - `governance/prompts/agent-protocol.md` - Inter-agent communication protocol

## Related Documentation

- [Agent Architecture](../architecture/agent-architecture.md) - Full agent system design
- [Context Management](../architecture/context-management.md) - Context capacity protocol details
- [Repository Setup](repository-setup.md) - Initial configuration and directory structure
- [Copilot Integration](copilot-integration.md) - Platform-specific Copilot configuration
