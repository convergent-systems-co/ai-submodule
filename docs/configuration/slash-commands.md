# Slash Commands

The Dark Factory Governance Framework provides slash commands for initiating and managing autonomous workflows. These commands are available in both Claude Code and GitHub Copilot, with platform-specific implementations.

## Available Commands

| Command | Purpose | Availability |
|---------|---------|--------------|
| `/startup` | Initiates the autonomous agentic loop | Claude Code, GitHub Copilot |
| `/checkpoint` | Saves session state and executes context capacity shutdown protocol | Claude Code, GitHub Copilot |
| `/threat-model` | Runs threat model analysis (system-level or PR-level) | Claude Code, GitHub Copilot |

## `/startup` - Agentic Loop

The `/startup` command begins the autonomous improvement loop, executing the full five-phase governance pipeline.

### What It Does

1. **Phase 1: Pre-flight & Triage** - Validates repository configuration, resolves open PRs, scans and prioritizes GitHub issues
2. **Phase 2: Planning** - Validates issue state, selects review panels, creates implementation plans
3. **Phase 3: Implementation** - Executes code changes, writes tests, updates documentation
4. **Phase 4: Review & PR** - Runs security and context-specific reviews, creates pull requests, monitors CI
5. **Phase 5: Merge & Loop** - Merges approved PRs, closes issues, loops or shuts down based on capacity

### Usage

=== "Claude Code"

    ```bash
    /startup
    ```

    The agent will:
    - Read and execute `governance/prompts/startup.md`
    - Follow the Code Manager persona orchestration
    - Dispatch parallel Coder agents (up to N = `governance.parallel_coders`, default 5; all issues when N = -1)
    - Process up to N issues per session (unlimited when N = -1)
    - Execute shutdown protocol at 80% context capacity

=== "GitHub Copilot"

    ```bash
    /startup
    ```

    The agent will:
    - Read and execute `.ai/governance/prompts/startup.md`
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
3. **Writes checkpoint file** - Saves session state to `.governance/checkpoints/{timestamp}-{branch}.json`
4. **Reports to user** - Summarizes completed work, remaining work, checkpoint location
5. **Offers context reset** - Prompts for `/clear` (Claude Code) or new chat thread (Copilot)

### Usage

=== "Claude Code"

    ```bash
    /checkpoint
    ```

    The agent will:
    - Write checkpoint to `.governance/checkpoints/{timestamp}-{branch}.json`
    - Report summary with completed/remaining work
    - Offer `/clear` to reset context
    - Provide resume command: `Resume from checkpoint: .governance/checkpoints/{file}`

=== "GitHub Copilot"

    ```bash
    /checkpoint
    ```

    The agent will:
    - Write checkpoint to `.governance/checkpoints/{timestamp}-{branch}.json`
    - Report summary with completed/remaining work
    - Prompt to start new chat thread
    - Provide resume command: `Resume from checkpoint: .governance/checkpoints/{file}`

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
  "branches_touched": ["itsfwcp/feat/123/add-feature", "main"],
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
| `system` | `.governance/panels/threat-model-system.md` | `.governance/panels/threat-model-system.json` |
| `pr` / `pr=N` | `.governance/panels/threat-modeling.md` | `.governance/panels/threat-modeling.json` |

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

The PR-level variant (`threat-modeling`) is included in `required_panels` for all 4 policy profiles and runs automatically on every PR. The system-level variant (`threat-model-system`) is on-demand only and is not included in any policy profile's required panels.

### Prompt Files

| Mode | Prompt Location (submodule) | Prompt Location (consuming repo) |
|------|---------------------------|--------------------------------|
| System | `governance/prompts/reviews/threat-model-system.md` | `.ai/governance/prompts/reviews/threat-model-system.md` |
| PR | `governance/prompts/reviews/threat-modeling.md` | `.ai/governance/prompts/reviews/threat-modeling.md` |

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
| Checkpoint directory | `.governance/checkpoints/` | `.governance/checkpoints/` |
| Task isolation | Worktrees via `Task` tool | Branch switching |
| Max issues per session | 5 | 5 |
| Context capacity threshold | 80% | ~30 turns or 200K chars |

## Implementation Files

The slash commands are implemented in these files:

- **Claude Code:**
  - `.claude/commands/startup.md` - Startup command definition
  - `.claude/commands/checkpoint.md` - Checkpoint command definition
  - `.claude/commands/threat-model.md` - Threat model command definition

- **GitHub Copilot:**
  - `.github/copilot-chat/startup.md` - Startup command definition
  - `.github/copilot-chat/checkpoint.md` - Checkpoint command definition
  - `.github/copilot-chat/threat-model.md` - Threat model command definition

- **Core workflow:**
  - `governance/prompts/startup.md` - Agentic loop specification
  - `governance/personas/agentic/` - Agent persona definitions
  - `governance/prompts/agent-protocol.md` - Inter-agent communication protocol

## Related Documentation

- [Agent Architecture](../architecture/agent-architecture.md) - Full agent system design
- [Context Management](../architecture/context-management.md) - Context capacity protocol details
- [Repository Setup](repository-setup.md) - Initial configuration and directory structure
- [Copilot Integration](copilot-integration.md) - Platform-specific Copilot configuration
