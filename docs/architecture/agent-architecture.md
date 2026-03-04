# Agent Architecture

## Overview

The Dark Forge uses a 7-agent prompt-chained architecture for autonomous software delivery. Each agent has a distinct role, bounded authority, and communicates via a structured protocol. The architecture implements three Anthropic agent patterns: Routing, Orchestrator-Workers with Parallelization, and Evaluator-Optimizer.

No agent can self-approve its own work. Every work item flows through at least three agents before merge.

The seven agents operate in two modes:
- **Standard mode** (default) — DevOps Engineer is the session entry point, dispatching to Tech Lead, which orchestrates Coder, IaC Engineer (conditional), and Tester
- **Project Manager mode** (opt-in via `governance.use_project_manager: true`) — Project Manager replaces DevOps Engineer as entry point, multiplexing multiple Tech Leads for higher throughput

---

## System Diagram

### Standard Mode (Default)

```mermaid
flowchart TD
    subgraph "Phase 1 — Pre-flight and Triage"
        DE["DevOps Engineer<br/><i>Routing pattern</i>"]
    end

    subgraph "Phase 2 — Planning"
        CM_PLAN["Tech Lead<br/><i>Orchestrator</i>"]
    end

    subgraph "Phase 3 — Parallel Dispatch"
        CM_DISPATCH["Tech Lead<br/><i>Parallelization</i>"]
        C1["Coder Agent 1<br/><i>Worker</i>"]
        C2["Coder Agent 2<br/><i>Worker</i>"]
        CN["Coder Agent N<br/><i>Worker</i>"]
        IAC["IaC Engineer<br/><i>Worker, conditional</i>"]
    end

    subgraph "Phase 4 — Evaluation and Review"
        CM_COLLECT["Tech Lead<br/><i>Orchestrator</i>"]
        T["Tester<br/><i>Evaluator-Optimizer</i>"]
    end

    subgraph "Phase 5 — Merge and Loop"
        CM_MERGE["Tech Lead + DevOps Engineer"]
    end

    DE -->|"ASSIGN (batch)"| CM_PLAN
    CM_PLAN -->|"Plans created"| CM_DISPATCH
    CM_DISPATCH -->|"Task(worktree)"| C1
    CM_DISPATCH -->|"Task(worktree)"| C2
    CM_DISPATCH -->|"Task(worktree)"| CN
    CM_DISPATCH -->|"Task(worktree, infra)"| IAC
    C1 -->|RESULT| CM_COLLECT
    C2 -->|RESULT| CM_COLLECT
    CN -->|RESULT| CM_COLLECT
    IAC -->|RESULT| CM_COLLECT
    CM_COLLECT -->|"ASSIGN (evaluate)"| T
    T -->|APPROVE| CM_MERGE
    T -->|FEEDBACK| CM_COLLECT
    CM_COLLECT -->|"Relay FEEDBACK"| CM_DISPATCH
    CM_MERGE -->|"Loop or shutdown"| DE
```

### Project Manager Mode (Opt-In)

```mermaid
flowchart TD
    subgraph "PM Phase 0-1"
        PM["Project Manager<br/><i>Portfolio Orchestrator</i>"]
        DE_BG["DevOps Engineer<br/><i>Background Agent</i>"]
    end

    subgraph "PM Phase 2 — Multiplexed Managers"
        CM1["Tech Lead 1<br/><i>Code batch</i>"]
        CM2["Tech Lead 2<br/><i>Docs batch</i>"]
        CMM["Tech Lead M<br/><i>Infra batch</i>"]
    end

    subgraph "Nested Workers"
        C1A[Coder 1a]
        C1B[Coder 1b]
        C2A[Coder 2a]
        IAC_M[IaC Engineer]
    end

    PM -->|"spawn (background)"| DE_BG
    DE_BG -->|"RESULT (grouped batches)"| PM
    DE_BG -.->|"WATCH (new issues)"| PM
    PM -->|"ASSIGN (code group)"| CM1
    PM -->|"ASSIGN (docs group)"| CM2
    PM -->|"ASSIGN (infra group)"| CMM
    CM1 -->|"Task(worktree)"| C1A
    CM1 -->|"Task(worktree)"| C1B
    CM2 -->|"Task(worktree)"| C2A
    CMM -->|"Task(worktree)"| IAC_M
    CM1 -->|RESULT| PM
    CM2 -->|RESULT| PM
    CMM -->|RESULT| PM
```

---

## The Seven Agents

### 1. Project Manager (Opt-In)

**Pattern:** Anthropic's Orchestrator-Workers at portfolio level
**Source:** [`governance/personas/agentic/project-manager.md`](../../governance/personas/agentic/project-manager.md)
**Activation:** `governance.use_project_manager: true` in `project.yaml`

The Project Manager is an opt-in portfolio-level orchestrator that replaces the DevOps Engineer as the session entry point. It multiplexes multiple Tech Leads for higher throughput.

**Responsibilities:**

- Session initialization and checkpoint recovery (PM-specific state)
- Spawn DevOps Engineer as a background agent for pre-flight and triage
- Receive grouped issue batches from DevOps Engineer
- Spawn M Tech Leads (one per group, M = `governance.parallel_tech_leads`, default 3)
- Coordinate cross-batch dependencies
- Process WATCH messages from DevOps Engineer for new issues discovered mid-session
- Manage lifecycle: CANCEL propagation, context capacity monitoring, checkpoint writing

**Authority boundaries:**

| Domain | Authority |
|--------|-----------|
| Session lifecycle | Full (supersedes DevOps Engineer in PM mode) |
| Tech Lead spawning and assignment | Full |
| Cross-batch coordination | Full |
| CANCEL propagation | Full |
| Implementation, code review, merge | None (delegated to Tech Leads) |

**Context thresholds:**

| Level | Tool Calls | Chat Turns | Active CMs | Token Usage |
|-------|-----------|------------|------------|-------------|
| Green | < 40 | < 60 | < M-1 | < 60% |
| Yellow | 40-55 | 60-100 | M-1 | 60-70% |
| Orange | 55-80 | 100-150 | M | 70-80% |
| Red | > 80 | > 150 | M | >= 80% |

**Key constraint:** The Project Manager never writes code, reviews PRs, or merges. It only spawns and coordinates Tech Leads.

---

### 2. DevOps Engineer

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

**Key constraint:** The DevOps Engineer never communicates directly with the Coder or Tester. All routing goes through the Tech Lead.

---

In Project Manager mode, the DevOps Engineer runs as a background agent, continuously polling for new issues and emitting WATCH messages to the Project Manager when new actionable work is discovered.

---

### 3. Tech Lead

**Pattern:** Anthropic's Orchestrator-Workers with Parallelization
**Source:** [`governance/personas/agentic/tech-lead.md`](../../governance/personas/agentic/tech-lead.md)

The Tech Lead is the primary orchestrator. It manages the lifecycle of work from intent validation through merge, delegating execution to the Coder and evaluation to the Test Evaluator. It does not write code directly.

**Responsibilities:**

- Receive routed issues from DevOps Engineer
- Validate intent (completeness, clarity, acceptance criteria)
- Select context-appropriate review panels based on codebase analysis
- Create implementation plans for all issues before dispatch
- Spawn parallel Coder agents via the `Task` tool with `isolation: "worktree"`
- Collect results from Coder agents as they arrive
- Route Coder output to Test Evaluator for evaluation
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
| Coder and Test Evaluator assignment | Full |
| Parallel dispatch strategy | Full |
| Panel selection | Full |
| Recommendation disposition | Full |
| Merge execution | Full (after policy engine approval + Test Evaluator APPROVE + security review) |
| Override policy engine | None (escalates to human) |
| Session lifecycle | None (owned by DevOps Engineer) |

**Key constraint:** The Tech Lead cannot merge without (1) Test Evaluator APPROVE, (2) a passing security review, and (3) policy engine approval. Maximum 3 review cycles per PR before human escalation.

---

### 4. Coder

**Pattern:** Worker in Anthropic's Orchestrator-Workers pattern
**Source:** [`governance/personas/agentic/coder.md`](../../governance/personas/agentic/coder.md)

The Coder is the execution agent. It implements changes as directed by the Tech Lead, following established plans and conventions. Each Coder instance runs in its own git worktree with its own context window.

**Responsibilities:**

- Receive ASSIGN messages from Tech Lead with plan, constraints, and acceptance criteria
- Create feature branches following naming conventions
- Implement changes according to the approved plan
- Write tests meeting coverage targets (80% minimum)
- Run the Test Coverage Gate before signaling completion
- Update documentation with every change
- Respond to Test Evaluator feedback (must-fix items)
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
| Push authorization | Conditional (requires Test Evaluator APPROVE) |
| Architectural changes | None (escalates to Tech Lead) |
| Merge | None |

**Key constraint:** The Coder cannot self-approve and cannot push without Tester approval. It communicates only with the Tech Lead, never directly with the DevOps Engineer or Tester.

---

### 5. IaC Engineer (Conditional)

**Pattern:** Worker in Anthropic's Orchestrator-Workers pattern
**Source:** [`governance/personas/agentic/iac-engineer.md`](../../governance/personas/agentic/iac-engineer.md)

The IaC Engineer is a conditional execution agent dispatched only for infrastructure changes. It follows JM Paved Roads standards for Azure resource provisioning.

**Dispatch trigger:** Issues involving `.bicep`, `.tf`, `infra/**`, `bicep/**`, `terraform/**`, `*.bicepparam`, `*.tfvars`.

**Responsibilities:**

- Implement infrastructure changes using Bicep or Terraform
- Follow JM Paved Roads naming conventions and module registry
- Apply security-first defaults and mandatory tagging (Application, Environment, ManagedBy)
- Configure per-environment parameter files
- Emit structured RESULT messages

**Authority boundaries:**

| Domain | Authority |
|--------|-----------|
| Infrastructure implementation | Full (within allowed paths) |
| Naming convention compliance | Full |
| Module registry selection | Full |
| Application code changes | None |
| Policy/schema/persona modification | None |

**Containment limits:** Max 20 files/PR, 800 lines/commit, 10 new files/PR, 15 commits/PR.

**Allowed paths:** `infra/**`, `bicep/**`, `terraform/**`, `*.bicep`, `*.bicepparam`, `*.tf`, `*.tfvars`, `parameters.json`, `.artifacts/plans/**`, `docs/**`.

---

### 6. Tester

**Pattern:** Anthropic's Evaluator-Optimizer pattern
**Source:** [`governance/personas/agentic/test-evaluator.md`](../../governance/personas/agentic/test-evaluator.md)

The Test Evaluator is the independent evaluator. It reviews the Coder's implementation, runs the Test Coverage Gate, verifies documentation, and provides structured feedback. The Test Evaluator never writes implementation code.

**Responsibilities:**

- Evaluate implementation against acceptance criteria and approved plan
- Execute the Test Coverage Gate independently
- Verify documentation completeness across all mandatory categories
- Provide structured feedback with file paths, line numbers, and priority classification
- Emit APPROVE when all must-fix items are resolved
- Emit BLOCK after 3 evaluation cycles without resolution
- Escalate to Tech Lead when deadlocked

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

**Key constraint:** Maximum 3 evaluation cycles. After 3 cycles with unresolved must-fix items, the Test Evaluator escalates to the Tech Lead rather than continuing to reject.

---

### 7. Document Writer

**Pattern:** Worker in Anthropic's Orchestrator-Workers pattern
**Source:** [`governance/personas/agentic/document-writer.md`](../../governance/personas/agentic/document-writer.md)

The Document Writer is the documentation maintenance agent. It runs during Phase 4 (Collect & Review) to analyze code changes and update all affected documentation, ensuring documentation never drifts from implementation.

**Responsibilities:**

- Receive ASSIGN messages from Tech Lead with branch diffs and staleness scope
- Analyze changed files and identify affected documentation
- Run `bin/check-doc-staleness.py` to detect stale numeric claims, path references, and descriptions
- Update stale references in all affected documentation files
- Verify counts match actual file counts (personas, prompts, policies)
- Verify path references point to existing files
- Emit structured RESULT messages on completion

**Authority boundaries:**

| Domain | Authority |
|--------|-----------|
| Documentation content | Full (within factual accuracy) |
| Staleness detection | Full |
| Path and count corrections | Full |
| Documentation structure | Limited (reorganize, not restructure) |
| Source code changes | None |
| Test changes | None |
| Push authorization | None (Tech Lead controls push) |

**Containment limits:** Max 20 files/PR, 500 lines/commit, 10 new files/PR.

**Allowed paths:** `*.md`, `docs/**`, `CLAUDE.md`, `README.md`, `GOALS.md`, `CONTRIBUTING.md`, `.artifacts/plans/**`.

**Key constraint:** The Document Writer never modifies source code, tests, or governance infrastructure. All documentation updates must be grounded in actual repository state — no assertions without verification.

---

## Agent Protocol

Full specification: [`governance/prompts/agent-protocol.md`](../../governance/prompts/agent-protocol.md)

### Message Types

All inter-agent communication uses structured JSON messages with these types:

| Type | Purpose | Valid Senders |
|------|---------|---------------|
| `ASSIGN` | Delegate a work unit | Project Manager -> Tech Lead, DevOps Engineer -> Tech Lead, Tech Lead -> Coder/IaC Engineer, Tech Lead -> Tester |
| `STATUS` | Progress update | Coder -> Tech Lead, Tech Lead -> DevOps Engineer/Project Manager |
| `RESULT` | Report completion | Coder/IaC Engineer -> Tech Lead, Tech Lead -> DevOps Engineer/Project Manager, DevOps Engineer -> Project Manager |
| `FEEDBACK` | Structured evaluation feedback | Tester -> Tech Lead (relayed to Coder/IaC Engineer) |
| `ESCALATE` | Escalate beyond authority | Any agent -> its orchestrator |
| `APPROVE` | Approve for next phase | Tester -> Tech Lead |
| `BLOCK` | Reject; must fix before proceeding | Tester -> Tech Lead |
| `CANCEL` | Stop work immediately | Any orchestrator -> its workers (cascading) |
| `WATCH` | Notify of new actionable work | DevOps Engineer -> Project Manager (background polling mode) |

### Message Schema

Every message includes:

```json
{
  "message_type": "ASSIGN | STATUS | RESULT | FEEDBACK | ESCALATE | APPROVE | BLOCK | CANCEL | WATCH",
  "source_agent": "project-manager | devops-engineer | tech-lead | coder | iac-engineer | tester",
  "target_agent": "project-manager | devops-engineer | tech-lead | coder | iac-engineer | tester",
  "correlation_id": "issue-42",
  "payload": {},
  "feedback": {}
}
```

### Valid Transition Map

```mermaid
flowchart LR
    PM[Project Manager] -->|"ASSIGN, CANCEL"| CM[Tech Lead]
    CM -->|"STATUS, RESULT, ESCALATE"| PM

    DE[DevOps Engineer] -->|"ASSIGN, RESULT"| PM
    DE -.->|WATCH| PM
    DE -->|ASSIGN| CM

    CM -->|"STATUS, RESULT, ESCALATE"| DE

    CM -->|"ASSIGN, CANCEL"| CO[Coder]
    CO -->|"STATUS, RESULT, ESCALATE"| CM

    CM -->|"ASSIGN, CANCEL"| IAC[IaC Engineer]
    IAC -->|"STATUS, RESULT, ESCALATE"| CM

    CM -->|ASSIGN| TE[Tester]
    TE -->|"FEEDBACK, APPROVE, BLOCK, ESCALATE"| CM

    CM -->|"FEEDBACK relayed"| CO
    CM -->|"FEEDBACK relayed"| IAC
```

Agents must not send message types not listed in their valid transitions. The DevOps Engineer never communicates directly with the Coder, IaC Engineer, or Tester. The Project Manager communicates only with DevOps Engineer and Tech Leads.

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

The Tech Lead spawns multiple Coder agents using the `Task` tool with `isolation: "worktree"`. Each Coder runs in its own git worktree and context window.

```mermaid
flowchart TD
    CM["Tech Lead<br/>Main session"] -->|"Task worktree, background"| W1["Coder 1<br/>Worktree 1"]
    CM -->|"Task worktree, background"| W2["Coder 2<br/>Worktree 2"]
    CM -->|"Task worktree, background"| WN["Coder N<br/>Worktree N"]
    W1 -->|"Result: branch, changes"| CM
    W2 -->|"Result: branch, changes"| CM
    WN -->|"Result: branch, changes"| CM
```

Key properties:
- Each Coder gets its own git worktree (isolated file system copy)
- Up to N concurrent Coder agents (N = `governance.parallel_coders` from `project.yaml`, default 5)
- The Tech Lead is notified as each agent completes; results are processed as they arrive
- Coders commit to their worktree branch; the Tech Lead pushes after evaluation
- No inline markers needed; the `Task` tool handles transport

### Phase B: Multi-Session (Future -- Phase 5d)

When a multi-agent orchestrator exists, messages are written to the file system:

```
.artifacts/state/agent-messages/
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
| State sharing | Shared context window | Tech Lead in main, Coders in worktrees | `.artifacts/state/` directory |
| Failure recovery | Checkpoint + resume | Tech Lead retries or skips failed agents | Orchestrator retry with message replay |

---

## Pipeline Phases

The startup sequence (`governance/prompts/startup.md`) chains the seven agents through five phases (standard mode):

| Phase | Agent(s) | What Happens |
|-------|----------|--------------|
| 1 | DevOps Engineer | Pre-flight checks, resolve open PRs, triage and prioritize issues |
| 2 | Tech Lead | Validate intent for all issues, select review panels, create plans |
| 3 | Tech Lead + Coders + IaC Engineer | Parallel dispatch: spawn up to N Coder agents in worktrees; IaC Engineer for infrastructure changes |
| 4 | Tech Lead + Tester | Collect results, Tester evaluates, security review, PR monitoring |
| 5 | Tech Lead + DevOps Engineer | Merge PRs, retrospective, loop or shutdown |

### Phase Flow

```mermaid
sequenceDiagram
    participant DE as DevOps Engineer
    participant CM as Tech Lead
    participant CO as Coder x N
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
    CM->>CM: Create plans in .artifacts/plans/

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
1. The Tech Lead logs the failure
2. Creates a follow-up issue for the failed work
3. Continues processing results from other Coder agents
4. The failed issue is picked up in the next session

### Tester Rejection Loop

If the Test Evaluator rejects a Coder's work repeatedly:
1. Cycles 1-3: Structured FEEDBACK is relayed to Coder for fixes
2. After cycle 3: Test Evaluator emits ESCALATE to Tech Lead
3. Tech Lead escalates to human review with full feedback history

### Context Capacity Exhaustion

When any context pressure signal is detected (80% threshold):
1. Stop all work immediately
2. Clean git state (commit, stash, or abort)
3. Write checkpoint to `.artifacts/checkpoints/`
4. Report to user and request `/clear`
5. Next session restores from checkpoint with issue state re-validation

### Worktree Unavailability

If the `Task` tool with `isolation: "worktree"` is unavailable:
1. The Tech Lead falls back to sequential execution
2. Issues are processed one at a time through Phases 3-5
3. All protocol semantics remain identical; only parallelism is lost

### Policy Engine Block

If the policy engine blocks a merge:
1. Tech Lead posts the block reason on the PR
2. Escalates to human reviewers
3. Does not override the policy engine decision

---

## Extension Points

### Adding a New Agent

To add a new agent to the pipeline:

1. Create a persona file in `governance/personas/agentic/` defining role, responsibilities, authority, and anti-patterns
2. Define its valid message transitions in `governance/prompts/agent-protocol.md`
3. Update `governance/prompts/startup.md` to include the new agent in the appropriate phase
4. Update this document and `CLAUDE.md` to reflect the new agent

### Custom Review Panels

The Tech Lead dynamically selects review panels based on the change type and codebase analysis. To add a new panel:

1. Create a review prompt in `governance/prompts/reviews/`
2. Define the structured emission schema
3. The Tech Lead will discover and invoke it when the codebase requires it

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

### Coder Scaling: Min/Max Range

In addition to `parallel_coders`, fine-grained scaling is available via `coder_min` and `coder_max`:

```yaml
governance:
  coder_min: 1    # Minimum agents per batch (default: 1)
  coder_max: 5    # Maximum agents per batch (default: 5, -1 for unlimited)
  require_worktree: true  # Mandatory worktree isolation (default: true)
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `coder_min` | integer (1-20) | 1 | Minimum number of Coder agents dispatched per batch. The orchestrator will not proceed with fewer tasks than this threshold. |
| `coder_max` | integer (-1 to 20) | 5 | Maximum number of Coder agents dispatched per batch. Set to -1 for unlimited (bounded only by context pressure). |
| `require_worktree` | boolean | true | When true, all Coder agents must run in isolated git worktrees. The primary repository always stays on the main branch. |

**Validation:** The orchestrator validates that `coder_min <= coder_max` at config load time (unless `coder_max` is -1 for unlimited). Invalid configurations raise a `ValueError` before any work begins.

**Worktree isolation enforcement:** When `require_worktree` is true (the default), Phase 3 dispatch includes `require_worktree: true` in the step result instructions. The LLM must use `isolation: worktree` for every Task tool call. If worktree isolation is unavailable at runtime, the Tech Lead falls back to sequential execution but never modifies the primary repo working tree directly.

**Relationship to `parallel_coders`:** `coder_max` supplements `parallel_coders`. The `parallel_coders` field controls the capacity signal thresholds in the state machine, while `coder_min`/`coder_max` control the actual dispatch batch size in Phase 3. Both are read from the governance section of `project.yaml`.

---

## Context Boundary Model

Each agentic persona operates within a defined context boundary that specifies exactly what information enters its context window. This prevents context leakage between agents and enforces the principle of least privilege.

### Boundary Specification

Per-persona boundaries are defined in `governance/policy/agent-context-boundaries.yaml`. Each persona has:

- **`receives`**: Explicit list of content types the persona is authorized to see (persona definition, specific protocol message types, scoped plan files, config sections).
- **`never_receives`**: Explicit list of content categories that must never enter the persona's context (other agent reasoning, unscoped plans, triage details).

### Envelope-Based Dispatch

In Phase A+ (parallel dispatch), the Tech Lead constructs a **message envelope** for each worker agent. The envelope is the sole input — the agent's context is built exclusively from:

1. **Persona definition** — loaded from the declared path
2. **Protocol message** — the ASSIGN/FEEDBACK/CANCEL message
3. **Context attachments** — declared files with SHA-256 content hashes

The envelope conforms to `governance/schemas/agent-envelope.schema.json` and is validated against the target persona's boundary spec before dispatch.

### Enforcement Mechanism

```
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  Orchestrator │───>│ Envelope Builder  │───>│  Dispatcher   │
│  (Tech Lead)  │    │ + Validator       │    │  (Task tool)  │
└──────────────┘    └──────────────────┘    └──────────────┘
                           │
                    1. Build envelope from ASSIGN
                    2. Validate against boundaries
                    3. Strip unauthorized content
                    4. Sign with HMAC
                    5. Log context hash for audit
```

Steps:
1. **Build**: The orchestrator constructs an envelope with the protocol message and declared attachments.
2. **Validate**: The envelope is checked against the target persona's boundary specification. Unauthorized content types are flagged.
3. **Strip**: Any content not in the `receives` list is removed. Content in `never_receives` triggers a violation log.
4. **Sign**: The envelope is signed with the source persona's HMAC key (derived from the session secret).
5. **Dispatch**: The validated, signed envelope is delivered to the agent.

### Phase A vs Phase A+ Enforcement

| Aspect | Phase A (Sequential) | Phase A+ (Parallel) |
|--------|---------------------|-------------------|
| Boundary spec | Same YAML file | Same YAML file |
| Enforcement | Audit-only (log violations) | Hard enforcement (strip + reject) |
| Transport | Inline markers in shared context | Envelope via Task tool |
| Isolation | Best-effort (shared context window) | Full (separate worktree + context) |
| Signing | Logged but not cryptographically verified | HMAC-verified per message |

In Phase A (single-session), context boundaries are best-effort because all personas share one context window. Violations are logged for audit but not blocked. In Phase A+ and Phase B, boundaries are hard-enforced because each agent runs in its own context.

### Implementation

- **Boundary spec**: `governance/policy/agent-context-boundaries.yaml`
- **Envelope schema**: `governance/schemas/agent-envelope.schema.json`
- **Envelope builder**: `governance/engine/envelope.py`
- **Message signing**: `governance/engine/message_signing.py`
- **Tests**: `governance/engine/tests/test_envelope.py`

---

## Related Documents

- [Agent Protocol](../../governance/prompts/agent-protocol.md) -- Full message schema and transport specification
- [Startup Loop](../../governance/prompts/startup.md) -- The 5-phase pipeline that chains the agents
- [Governance Model](governance-model.md) -- The five governance layers the agents operate within
- [Context Management](context-management.md) -- JIT loading tiers and shutdown protocol
- [Mass Parallelization](mass-parallelization.md) -- Multi-agent collision domains (Phase 5e)
- [Project Manager Persona](../../governance/personas/agentic/project-manager.md)
- [DevOps Engineer Persona](../../governance/personas/agentic/devops-engineer.md)
- [Tech Lead Persona](../../governance/personas/agentic/tech-lead.md)
- [Coder Persona](../../governance/personas/agentic/coder.md)
- [IaC Engineer Persona](../../governance/personas/agentic/iac-engineer.md)
- [Tester Persona](../../governance/personas/agentic/test-evaluator.md)
- [Document Writer Persona](../../governance/personas/agentic/document-writer.md)
- [Project Manager Architecture](project-manager-architecture.md)
