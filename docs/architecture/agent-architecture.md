# Agent Architecture

## Overview

The Dark Factory Governance Platform uses a 4-agent prompt-chained architecture for autonomous software delivery. Each agent has a distinct role, bounded authority, and communicates via a structured protocol. The architecture implements three Anthropic agent patterns: Routing, Orchestrator-Workers with Parallelization, and Evaluator-Optimizer.

No agent can self-approve its own work. Every work item flows through at least three agents before merge.

---

## System Diagram

```mermaid
flowchart TD
    subgraph "Phase 1 — Pre-flight & Triage"
        DE[DevOps Engineer<br/><i>Routing pattern</i>]
    end

    subgraph "Phase 2 — Planning"
        CM_PLAN[Code Manager<br/><i>Orchestrator</i>]
    end

    subgraph "Phase 3 — Parallel Dispatch"
        CM_DISPATCH[Code Manager<br/><i>Parallelization</i>]
        C1[Coder Agent 1<br/><i>Worker</i>]
        C2[Coder Agent 2<br/><i>Worker</i>]
        CN[Coder Agent N<br/><i>Worker</i>]
    end

    subgraph "Phase 4 — Evaluation & Review"
        CM_COLLECT[Code Manager<br/><i>Orchestrator</i>]
        T[Tester<br/><i>Evaluator-Optimizer</i>]
    end

    subgraph "Phase 5 — Merge & Loop"
        CM_MERGE[Code Manager + DevOps Engineer]
    end

    DE -->|"ASSIGN (batch)"| CM_PLAN
    CM_PLAN -->|"Plans created"| CM_DISPATCH
    CM_DISPATCH -->|"Task(worktree)"| C1
    CM_DISPATCH -->|"Task(worktree)"| C2
    CM_DISPATCH -->|"Task(worktree)"| CN
    C1 -->|RESULT| CM_COLLECT
    C2 -->|RESULT| CM_COLLECT
    CN -->|RESULT| CM_COLLECT
    CM_COLLECT -->|"ASSIGN (evaluate)"| T
    T -->|APPROVE| CM_MERGE
    T -->|FEEDBACK| CM_COLLECT
    CM_COLLECT -->|"Relay FEEDBACK"| CM_DISPATCH
    CM_MERGE -->|"Loop or shutdown"| DE
```

---

## The Four Agents

### 1. DevOps Engineer

**Pattern:** Anthropic's Routing pattern
**Source:** [`governance/personas/agentic/devops-engineer.md`](../../governance/personas/agentic/devops-engineer.md)

The DevOps Engineer is the session entry point. It owns session lifecycle and determines *what* work needs to be done, but never *how*.

**Responsibilities:**

- Session lifecycle management (context capacity enforcement, shutdown protocol, checkpoints)
- Pre-flight checks (submodule freshness, repository configuration, workflow health)
- Open PR resolution (existing PRs before new issues)
- Issue triage, filtering, and prioritization (P0-P4, bugs over enhancements)
- GOALS.md fallback when no issues remain
- Cross-repository escalation
- Checkpoint restore and issue state validation

**Authority boundaries:**

| Domain | Authority |
|--------|-----------|
| Session lifecycle | Full |
| Issue routing and prioritization | Full |
| Pre-flight checks | Full |
| Cross-repo escalation | Full |
| Implementation, code review, merge | None |

**Key constraint:** The DevOps Engineer never communicates directly with the Coder or Tester. All routing goes through the Code Manager.

---

### 2. Code Manager

**Pattern:** Anthropic's Orchestrator-Workers with Parallelization
**Source:** [`governance/personas/agentic/code-manager.md`](../../governance/personas/agentic/code-manager.md)

The Code Manager is the primary orchestrator. It manages the lifecycle of work from intent validation through merge, delegating execution to the Coder and evaluation to the Tester. It does not write code directly.

**Responsibilities:**

- Receive routed issues from DevOps Engineer
- Validate intent (completeness, clarity, acceptance criteria)
- Select context-appropriate review panels based on codebase analysis
- Create implementation plans for all issues before dispatch
- Spawn parallel Coder agents via the `Task` tool with `isolation: "worktree"`
- Collect results from Coder agents as they arrive
- Route Coder output to Tester for evaluation
- Relay Tester feedback back to the Coder
- Invoke security review after Tester approval
- Execute context-specific panel reviews
- Monitor CI checks, Copilot recommendations, and review threads
- Execute merge when policy engine approves
- Maintain `project.yaml` and run manifests

**Authority boundaries:**

| Domain | Authority |
|--------|-----------|
| Intent validation | Full |
| Coder and Tester assignment | Full |
| Parallel dispatch strategy | Full |
| Panel selection | Full |
| Recommendation disposition | Full |
| Merge execution | Full (after policy engine approval + Tester APPROVE + security review) |
| Override policy engine | None (escalates to human) |
| Session lifecycle | None (owned by DevOps Engineer) |

**Key constraint:** The Code Manager cannot merge without (1) Tester APPROVE, (2) a passing security review, and (3) policy engine approval. Maximum 3 review cycles per PR before human escalation.

---

### 3. Coder

**Pattern:** Worker in Anthropic's Orchestrator-Workers pattern
**Source:** [`governance/personas/agentic/coder.md`](../../governance/personas/agentic/coder.md)

The Coder is the execution agent. It implements changes as directed by the Code Manager, following established plans and conventions. Each Coder instance runs in its own git worktree with its own context window.

**Responsibilities:**

- Receive ASSIGN messages from Code Manager with plan, constraints, and acceptance criteria
- Create feature branches following naming conventions
- Implement changes according to the approved plan
- Write tests meeting coverage targets (80% minimum)
- Run the Test Coverage Gate before signaling completion
- Update documentation with every change
- Respond to Tester feedback (must-fix items)
- Implement Copilot and panel recommendations as directed
- Maintain atomic commits with conventional commit style
- Emit structured RESULT messages on completion

**Authority boundaries:**

| Domain | Authority |
|--------|-----------|
| Implementation approach (within plan) | Full |
| Technical decisions (with rationale) | Full |
| Branch creation | Full |
| Test strategy | Full |
| Self-approval | None |
| Push authorization | Conditional (requires Tester APPROVE) |
| Architectural changes | None (escalates to Code Manager) |
| Merge | None |

**Key constraint:** The Coder cannot self-approve and cannot push without Tester approval. It communicates only with the Code Manager, never directly with the DevOps Engineer or Tester.

---

### 4. Tester

**Pattern:** Anthropic's Evaluator-Optimizer pattern
**Source:** [`governance/personas/agentic/tester.md`](../../governance/personas/agentic/tester.md)

The Tester is the independent evaluator. It reviews the Coder's implementation, runs the Test Coverage Gate, verifies documentation, and provides structured feedback. The Tester never writes implementation code.

**Responsibilities:**

- Evaluate implementation against acceptance criteria and approved plan
- Execute the Test Coverage Gate independently
- Verify documentation completeness across all mandatory categories
- Provide structured feedback with file paths, line numbers, and priority classification
- Emit APPROVE when all must-fix items are resolved
- Emit BLOCK after 3 evaluation cycles without resolution
- Escalate to Code Manager when deadlocked

**Authority boundaries:**

| Domain | Authority |
|--------|-----------|
| Test execution and quality evaluation | Full |
| Push approval (gate) | Full |
| Documentation completeness | Full |
| Feedback priority classification | Full |
| Code changes | None |
| Merge decisions | None |
| Plan approval | None |

**Feedback priority levels:**

| Priority | Meaning |
|----------|---------|
| `must-fix` | Blocks approval; must be resolved before push |
| `should-fix` | Strongly recommended; requires documented rationale to skip |
| `nice-to-have` | Optional improvement; may be deferred |

**Key constraint:** Maximum 3 evaluation cycles. After 3 cycles with unresolved must-fix items, the Tester escalates to the Code Manager rather than continuing to reject.

---

## Agent Protocol

Full specification: [`governance/prompts/agent-protocol.md`](../../governance/prompts/agent-protocol.md)

### Message Types

All inter-agent communication uses structured JSON messages with these types:

| Type | Purpose | Valid Senders |
|------|---------|---------------|
| `ASSIGN` | Delegate a work unit | DevOps Engineer -> Code Manager, Code Manager -> Coder, Code Manager -> Tester |
| `STATUS` | Progress update | Coder -> Code Manager, Code Manager -> DevOps Engineer |
| `RESULT` | Report completion | Coder -> Code Manager, Code Manager -> DevOps Engineer |
| `FEEDBACK` | Structured evaluation feedback | Tester -> Code Manager (relayed to Coder) |
| `ESCALATE` | Escalate beyond authority | Any agent -> its orchestrator |
| `APPROVE` | Approve for next phase | Tester -> Code Manager |
| `BLOCK` | Reject; must fix before proceeding | Tester -> Code Manager |

### Message Schema

Every message includes:

```json
{
  "message_type": "ASSIGN | STATUS | RESULT | FEEDBACK | ESCALATE | APPROVE | BLOCK | CANCEL",
  "source_agent": "devops-engineer | code-manager | coder | tester",
  "target_agent": "devops-engineer | code-manager | coder | tester",
  "correlation_id": "issue-42",
  "payload": {},
  "feedback": {}
}
```

### Valid Transition Map

```mermaid
flowchart LR
    DE[DevOps Engineer] -->|ASSIGN| CM[Code Manager]
    CM -->|STATUS / RESULT / ESCALATE| DE

    CM -->|ASSIGN| CO[Coder]
    CO -->|STATUS / RESULT / ESCALATE| CM

    CM -->|ASSIGN| TE[Tester]
    TE -->|FEEDBACK / APPROVE / BLOCK / ESCALATE| CM

    CM -->|"FEEDBACK (relayed)"| CO
```

Agents must not send message types not listed in their valid transitions. The DevOps Engineer never communicates directly with the Coder or Tester.

---

## Transport Phases

The protocol defines three transport mechanisms with identical message semantics. Only the delivery mechanism changes.

### Phase A: Sequential Single-Session (Fallback)

All agents run sequentially within one context window. Messages are logged inline using markers:

```markdown
<!-- AGENT_MSG_START -->
{ "message_type": "ASSIGN", ... }
<!-- AGENT_MSG_END -->
```

The markers serve as structured logging for auditability. The "sending" and "receiving" agent are the same AI model switching personas.

### Phase A+: Parallel Single-Session (Default)

The Code Manager spawns multiple Coder agents using the `Task` tool with `isolation: "worktree"`. Each Coder runs in its own git worktree and context window.

```mermaid
flowchart TD
    CM[Code Manager<br/>Main session] -->|"Task(worktree, background)"| W1[Coder 1<br/>Worktree 1]
    CM -->|"Task(worktree, background)"| W2[Coder 2<br/>Worktree 2]
    CM -->|"Task(worktree, background)"| WN[Coder N<br/>Worktree N]
    W1 -->|"Result (branch, changes)"| CM
    W2 -->|"Result (branch, changes)"| CM
    WN -->|"Result (branch, changes)"| CM
```

Key properties:
- Each Coder gets its own git worktree (isolated file system copy)
- Up to N concurrent Coder agents (N = `governance.parallel_coders` from `project.yaml`, default 5)
- The Code Manager is notified as each agent completes; results are processed as they arrive
- Coders commit to their worktree branch; the Code Manager pushes after evaluation
- No inline markers needed; the `Task` tool handles transport

### Phase B: Multi-Session (Future -- Phase 5d)

When a multi-agent orchestrator exists, messages are written to the file system:

```
.governance/state/agent-messages/
  {correlation_id}/
    {timestamp}-{source}-{target}-{type}.json
```

Each file contains the full message schema as JSON. The orchestrator reads the directory to dispatch work and track state. This transport is defined but not yet implemented.

### Transport Comparison

| Capability | Sequential (Fallback) | Parallel (Default) | Multi-Session (Future) |
|------------|----------------------|-------------------|----------------------|
| Message logging | Inline markers | Task tool dispatch/return | File-based |
| Agent switching | Persona load in same context | Task tool with worktree isolation | Separate agent processes |
| Parallelism | One issue at a time | Up to N concurrent Coders | Fully concurrent |
| State sharing | Shared context window | Code Manager in main, Coders in worktrees | `.governance/state/` directory |
| Failure recovery | Checkpoint + resume | Code Manager retries or skips failed agents | Orchestrator retry with message replay |

---

## Pipeline Phases

The startup sequence (`governance/prompts/startup.md`) chains the four agents through five phases:

| Phase | Agent(s) | What Happens |
|-------|----------|--------------|
| 1 | DevOps Engineer | Pre-flight checks, resolve open PRs, triage and prioritize issues |
| 2 | Code Manager | Validate intent for all issues, select review panels, create plans |
| 3 | Code Manager + Coders | Parallel dispatch: spawn up to N Coder agents in worktrees |
| 4 | Code Manager + Tester | Collect results, Tester evaluates, security review, PR monitoring |
| 5 | Code Manager + DevOps Engineer | Merge PRs, retrospective, loop or shutdown |

### Phase Flow

```mermaid
sequenceDiagram
    participant DE as DevOps Engineer
    participant CM as Code Manager
    participant CO as Coder (x N)
    participant TE as Tester
    participant PE as Policy Engine

    Note over DE: Phase 1 — Pre-flight & Triage
    DE->>DE: Submodule freshness, repo config, workflow health
    DE->>DE: Resolve open PRs
    DE->>DE: Scan, filter, prioritize issues
    DE->>CM: ASSIGN (batch of up to N issues)

    Note over CM: Phase 2 — Planning
    CM->>CM: Validate intent for each issue
    CM->>CM: Select review panels per issue
    CM->>CM: Create plans in .governance/plans/

    Note over CM,CO: Phase 3 — Parallel Dispatch
    CM->>CO: Task(worktree, background) per issue
    CO->>CO: Implement, test, document
    CO->>CM: RESULT (branch, changes, test results)

    Note over CM,TE: Phase 4 — Evaluation & Review
    CM->>TE: ASSIGN (evaluate Coder output)
    alt Approved
        TE->>CM: APPROVE
        CM->>CM: Security review
        CM->>CM: Context-specific panel reviews
        CM->>CM: Push PR, monitor CI + Copilot
        CM->>PE: Request merge decision
        PE->>CM: APPROVE / BLOCK
    else Needs work
        TE->>CM: FEEDBACK (must-fix items)
        CM->>CO: Relay FEEDBACK
        CO->>CM: RESULT (updated)
        Note right of TE: Max 3 cycles
    end

    Note over CM,DE: Phase 5 — Merge & Loop
    CM->>CM: Merge PR, close issue
    CM->>DE: RESULT (issue complete)
    DE->>DE: Check hard-stop conditions
    alt More work and no hard-stop
        DE->>DE: Return to Phase 1
    else Session cap or context pressure
        DE->>DE: Shutdown protocol + checkpoint
    end
```

---

## Failure Modes and Recovery

### Coder Agent Failure

If a Coder agent fails or times out during parallel dispatch:
1. The Code Manager logs the failure
2. Creates a follow-up issue for the failed work
3. Continues processing results from other Coder agents
4. The failed issue is picked up in the next session

### Tester Rejection Loop

If the Tester rejects a Coder's work repeatedly:
1. Cycles 1-3: Structured FEEDBACK is relayed to Coder for fixes
2. After cycle 3: Tester emits ESCALATE to Code Manager
3. Code Manager escalates to human review with full feedback history

### Context Capacity Exhaustion

When any context pressure signal is detected (80% threshold):
1. Stop all work immediately
2. Clean git state (commit, stash, or abort)
3. Write checkpoint to `.governance/checkpoints/`
4. Report to user and request `/clear`
5. Next session restores from checkpoint with issue state re-validation

### Worktree Unavailability

If the `Task` tool with `isolation: "worktree"` is unavailable:
1. The Code Manager falls back to sequential execution
2. Issues are processed one at a time through Phases 3-5
3. All protocol semantics remain identical; only parallelism is lost

### Policy Engine Block

If the policy engine blocks a merge:
1. Code Manager posts the block reason on the PR
2. Escalates to human reviewers
3. Does not override the policy engine decision

---

## Extension Points

### Adding a New Agent

To add a fifth agent to the pipeline:

1. Create a persona file in `governance/personas/agentic/` defining role, responsibilities, authority, and anti-patterns
2. Define its valid message transitions in `governance/prompts/agent-protocol.md`
3. Update `governance/prompts/startup.md` to include the new agent in the appropriate phase
4. Update this document and `CLAUDE.md` to reflect the new agent

### Custom Review Panels

The Code Manager dynamically selects review panels based on the change type and codebase analysis. To add a new panel:

1. Create a review prompt in `governance/prompts/reviews/`
2. Define the structured emission schema
3. The Code Manager will discover and invoke it when the codebase requires it

### Transport Migration

The protocol is transport-agnostic. To add a new transport:

1. Implement the message read/write mechanism
2. The message schema and valid transitions remain unchanged
3. Update the graceful degradation table to include the new transport mode

### Parallel Coder Configuration

The number of concurrent Coder agents is configurable via `project.yaml`:

```yaml
governance:
  parallel_coders: 5  # default
```

This controls the maximum number of `Task` tool dispatches in Phase 3.

---

## Related Documents

- [Agent Protocol](../../governance/prompts/agent-protocol.md) -- Full message schema and transport specification
- [Startup Loop](../../governance/prompts/startup.md) -- The 5-phase pipeline that chains the agents
- [Governance Model](governance-model.md) -- The five governance layers the agents operate within
- [Context Management](context-management.md) -- JIT loading tiers and shutdown protocol
- [Mass Parallelization](mass-parallelization.md) -- Multi-agent collision domains (Phase 5e)
- [DevOps Engineer Persona](../../governance/personas/agentic/devops-engineer.md)
- [Code Manager Persona](../../governance/personas/agentic/code-manager.md)
- [Coder Persona](../../governance/personas/agentic/coder.md)
- [Tester Persona](../../governance/personas/agentic/tester.md)
