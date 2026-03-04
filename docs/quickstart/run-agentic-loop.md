# Quickstart: Run the Agentic Loop

**Time:** 5 minutes to start | **Prerequisites:** Governance installed with dependencies (`bash .ai/bin/init.sh --install-deps`)

---

## What Is the Agentic Loop?

The agentic loop is an automated pipeline that takes GitHub issues from assignment to merged PR:

1. **Selects** open issues assigned for the session
2. **Plans** implementation for each issue
3. **Dispatches** AI coders to implement in parallel (each in its own git worktree)
4. **Reviews** implementations with automated testing and governance panels
5. **Creates PRs** and monitors them through merge

## Step 1: Ensure Dependencies Are Installed

```bash
bash .ai/bin/init.sh --install-deps
```

This creates a Python virtual environment with the policy engine and orchestrator.

## Step 2: Create an Issue

Create a GitHub issue for the agentic loop to work on:

```bash
gh issue create --title "feat: add health check endpoint" --body "Add a /health endpoint that returns HTTP 200."
```

Note the issue number (e.g., #42).

## Step 3: Start the Agentic Loop

In Claude Code:

```
/startup
```

Or manually initialize the orchestrator:

```bash
source .ai/.venv/bin/activate
python -m governance.engine.orchestrator init --config project.yaml
```

## Step 4: Watch the Pipeline

The agentic loop will:

```
Phase 1: Pre-flight checks
  - Validate project.yaml
  - Check branch protection
  - Select issues for this session

Phase 2: Planning
  - Create implementation plans in .artifacts/plans/
  - Validate plans against governance policy

Phase 3: Implementation
  - Dispatch Coder agents (one per issue)
  - Each Coder works in its own git worktree
  - Tests and governance panels run per-change

Phase 4: Review and Merge
  - Tester validates each implementation
  - Security review runs on approved changes
  - PRs created, CI monitored, merged on approval
```

## Step 5: Check Progress

```bash
python -m governance.engine.orchestrator status
```

Or check governance status:

```bash
bash .ai/bin/governance-status.sh
```

## Key Concepts

### Personas

The agentic loop uses specialized AI personas:

| Persona | Job |
|---------|-----|
| Tech Lead | Plans work, dispatches coders, reviews results |
| Coder | Implements features and fixes |
| Test Evaluator | Validates implementations |

### Worktrees

Each Coder works in an isolated git worktree. This means:
- Multiple issues can be worked on in parallel
- No merge conflicts during implementation
- Each branch is clean and self-contained

### Context Management

The loop manages AI context automatically:
- Checkpoints are saved at key milestones
- If context fills up, work is saved and can be resumed
- Use `/startup` after a context reset to resume

## Troubleshooting

**"No issues selected":** Ensure issues exist and match the session's selection criteria in project.yaml.

**"Python not found":** Run `bash .ai/bin/init.sh --install-deps` first.

**"Orchestrator error":** Check the session state:
```bash
ls -la .artifacts/state/sessions/
```

---

## Next Steps

- [Customize policy profiles](customize-policy.md) - Tune governance rules
- [Architecture overview](../onboarding/architecture.html) - Understand the full system
- [Agentic protocol](../../governance/prompts/agent-protocol.md) - How agents communicate
