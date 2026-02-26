# Slash Commands

The Dark Factory Governance Framework provides slash commands for initiating and managing autonomous workflows. These commands are available in both Claude Code and GitHub Copilot, with platform-specific implementations.

## Available Commands

| Command | Purpose | Availability |
|---------|---------|--------------|
| `/startup` | Initiates the autonomous agentic loop | Claude Code, GitHub Copilot |
| `/checkpoint` | Saves session state and executes context capacity shutdown protocol | Claude Code, GitHub Copilot |

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
    - Dispatch parallel Coder agents (up to N = `governance.parallel_coders`, default 5)
    - Process up to 5 issues per session
    - Execute shutdown protocol at 80% context capacity

=== "GitHub Copilot"

    ```bash
    /startup
    ```

    The agent will:
    - Read and execute `.ai/governance/prompts/startup.md`
    - Follow sequential Coder execution (Copilot does not support parallel Task dispatch)
    - Process up to 5 issues per session
    - Prompt for new chat thread at context capacity threshold

### Constraints

- Maximum 5 issues per session
- Maximum 3 review cycles per PR before escalation
- Plans required before implementation
- Documentation updates mandatory with every change
- Hard stop at 80% context capacity

### Configuration

The number of parallel Coder agents can be configured in `project.yaml`:

```yaml
governance:
  parallel_coders: 5  # Default: 5, Range: 1-10
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

- **GitHub Copilot:**
  - `.github/copilot-chat/startup.md` - Startup command definition
  - `.github/copilot-chat/checkpoint.md` - Checkpoint command definition

- **Core workflow:**
  - `governance/prompts/startup.md` - Agentic loop specification
  - `governance/personas/agentic/` - Agent persona definitions
  - `governance/prompts/agent-protocol.md` - Inter-agent communication protocol

## Related Documentation

- [Agent Architecture](../architecture/agent-architecture.md) - Full agent system design
- [Context Management](../architecture/context-management.md) - Context capacity protocol details
- [Repository Setup](repository-setup.md) - Initial configuration and directory structure
- [Copilot Integration](copilot-integration.md) - Platform-specific Copilot configuration
