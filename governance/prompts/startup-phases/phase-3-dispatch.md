# Phase 3: Parallel Dispatch

**Persona:** Tech Lead (`governance/personas/agentic/tech-lead.md`)

> **Context Gate -- Phase 3 Entry:** Execute the Context Gate protocol from startup.md before proceeding. Yellow tier: do NOT dispatch new Coder agents -- skip to Phase 4 for in-flight work only. Orange/Red: execute Shutdown Protocol.

The Tech Lead spawns **parallel worker agents** (Coder or IaC Engineer) using the `Task` tool with `isolation: "worktree"`. Each worker runs in its own git worktree with its own context window, working on a single issue independently.

### 3a: Spawn Worker Agents

Read `governance.parallel_coders` from `project.yaml` (default: 5) to determine the maximum number of concurrent worker agents. If the value is -1 (unlimited), spawn agents for all planned issues -- the context gate remains the sole dispatch constraint.

For each planned issue, determine the appropriate worker persona:
- **IaC Engineer** (`governance/personas/agentic/iac-engineer.md`) -- when the issue involves infrastructure: Bicep, Terraform, ARM templates, cloud resource provisioning, networking, or identity configuration
- **Coder** (`governance/personas/agentic/coder.md`) -- for all other implementation work

Spawn a background Task agent per issue:

```
Task(
  subagent_type: "general-purpose",
  isolation: "worktree",
  run_in_background: true,
  prompt: <full worker persona prompt with plan, acceptance criteria, and constraints>
)
```

**The worker prompt must include:**
1. The full persona instructions (Coder or IaC Engineer as appropriate)
2. The plan content (from `.artifacts/plans/{number}-{description}.md`)
3. The issue body and acceptance criteria
4. Branch name to use
5. Instructions to commit, run tests/validation, and report results -- but NOT push (the Tech Lead pushes)
6. Session ID for agent audit logging (from Phase 0f)
7. Panel selections (from Phase 2c) -- inform the Coder which reviews will run so they can preemptively address known panel concerns

**Dispatch rules:**
- Spawn up to N Coder agents concurrently (N = `governance.parallel_coders` from `project.yaml`, default 5; all planned issues when N = -1)
- All independent issues are dispatched in a **single message** with multiple Task tool calls
- Each agent gets `run_in_background: true` so they execute concurrently
- The Tech Lead continues to the next phase without waiting

### 3b: Monitor Progress

After dispatching, the Tech Lead is notified as each Coder agent completes. As each result arrives, the Tech Lead immediately enters Phase 4 for that issue. There is no need to wait for all Coders to finish -- results are processed as they arrive.

If a Coder agent fails or times out:
- Log the failure
- Create a follow-up issue or retry in the next session
- Continue processing other completed agents

### 3c: Sequential Fallback

If the `Task` tool with `isolation: "worktree"` is unavailable (e.g., not in a git repo, worktree creation fails), fall back to sequential execution: process one issue at a time through Phases 3-5 before starting the next.

---

## Phase 3-Sequential: Implementation (Fallback)

**Persona:** Coder (`governance/personas/agentic/coder.md`)

> **Context Gate -- Phase 3-Sequential Entry:** Execute the Context Gate protocol from startup.md before proceeding. Yellow tier: proceed with current issue only -- do not start additional issues. Orange/Red: execute Shutdown Protocol.

Used only when parallel dispatch is unavailable. The Coder receives an ASSIGN message from the Tech Lead and executes the approved plan in the main session.

### 3s-a: Implement

1. Implement the plan following project conventions
2. Write tests meeting coverage targets
3. **Update documentation (mandatory)** -- check each category:
   - `GOALS.md`, `CLAUDE.md` (root + `.ai/`), `README.md`, `DEVELOPER_GUIDE.md`
   - `docs/**/*.md`, schema files, policy files, `instructions/*.md`
   - If no docs affected, note in commit message: `Docs: no updates required -- [reason]`
4. Commit with conventional commit messages (Git Commit Isolation)

### 3s-b: Test Coverage Gate

**Run before every push.** Execute `governance/prompts/test-coverage-gate.md`:
- All tests must pass
- Coverage must meet 80% minimum
- If gate blocks after 3 attempts, ESCALATE to Tech Lead

### 3s-c: Emit RESULT

Return a structured RESULT to Tech Lead with summary, artifacts, test results, and documentation updates per the agent protocol.
