# ADR-003: Agent Persona Model

**Status:** Accepted
**Date:** 2024-06-01 (retroactive)
**Author:** Dark Forge Team

---

## Context

The governance platform required an execution model for autonomous software delivery. Work items (GitHub issues, design intents) must flow from triage through implementation, review, and merge without manual intervention. This demands specialized capabilities: infrastructure awareness differs from code implementation; test evaluation requires independence from the code author; orchestration logic should not be entangled with execution logic.

The design needed to map cleanly onto Anthropic's documented agentic patterns (Routing, Orchestrator-Workers, Evaluator-Optimizer) while operating within the constraints of Claude Code's single-session architecture. The system also needed to enforce separation of concerns -- no agent should self-approve its own work, and every work item must flow through at least three agents before merge.

A typed inter-agent communication protocol was needed to ensure structured handoffs between agents, support future multi-session execution, and maintain audit trails of agent interactions.

## Decision

The platform uses a six-agent prompt-chained architecture defined in `governance/personas/agentic/`. Each agent has a distinct role, bounded authority, and communicates via a typed protocol (`governance/prompts/agent-protocol.md`):

1. **Project Manager** (`project-manager.md`) -- Portfolio-level orchestrator implementing the Orchestrator-Workers pattern. Multiplexes Tech Leads, spawns background DevOps Engineer, coordinates cross-batch work. Opt-in via `governance.use_project_manager: true`.

2. **DevOps Engineer** (`devops-engineer.md`) -- Session entry point implementing Anthropic's Routing pattern. Owns pre-flight checks, issue triage, prioritization, and session lifecycle. Determines *what* work needs to be done but never *how*.

3. **Tech Lead** (`tech-lead.md`) -- Pipeline orchestrator implementing the Orchestrator-Workers pattern. Validates intent, selects review panels, dispatches parallel Coders, collects results, coordinates merge.

4. **Coder** (`coder.md`) -- Execution agent (Worker). Implements code changes, writes tests, updates documentation. Operates in isolated worktrees via `Task` tool with `isolation: "worktree"`.

5. **IaC Engineer** (`iac-engineer.md`) -- Infrastructure execution agent (Worker). Handles Bicep/Terraform changes with security-first defaults. Dispatched conditionally for infrastructure-only changes.

6. **Tester** (`test-evaluator.md`) -- Independent evaluator implementing the Evaluator-Optimizer pattern. Runs test coverage gates, verifies documentation, produces structured feedback. Cannot be the same agent that wrote the code.

The protocol defines nine message types: ASSIGN, STATUS, RESULT, FEEDBACK, ESCALATE, APPROVE, BLOCK, CANCEL, and WATCH. Valid sender/receiver pairs are explicitly constrained (e.g., only orchestrators send ASSIGN; only evaluators send APPROVE).

## Consequences

### Positive

- Clear separation of concerns: triage, orchestration, execution, and evaluation are distinct roles with bounded authority
- No self-approval: the three-agent minimum (Tech Lead assigns, Coder implements, Tester evaluates) prevents any agent from approving its own work
- Parallel execution: Tech Lead dispatches up to N Coders simultaneously (`governance.parallel_coders`, default 5), each in isolated worktrees
- The typed protocol enables future multi-session execution without changing the communication contract
- Pattern alignment: each agent maps directly to an Anthropic agentic pattern, making behavior predictable

### Negative

- Six agent definitions add cognitive overhead for contributors understanding the system
- Prompt-chaining in a single session means agent "handoffs" are simulated via context loading rather than true process isolation
- The Project Manager mode introduces nested parallelism (PM -> CM -> Coder) that increases coordination complexity

### Neutral

- The architecture distinguishes between agentic personas (these seven agents with decision authority) and review personas (perspectives within panel prompts) -- they serve different purposes and live in different directories
- The WATCH message type enables the DevOps Engineer to emit new work discovered during background polling, but this requires continuous-session support not yet universal across AI coding tools

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| Single omniscient agent | No separation of concerns; self-approval risk; context window overload from loading all capabilities simultaneously |
| Two-agent model (planner + executor) | Insufficient for the triage-plan-execute-evaluate-merge pipeline; no independent evaluation step |
| Unrestricted agent communication (any-to-any) | Creates coordination chaos; typed protocol with constrained sender/receiver pairs prevents invalid state transitions |
| Human-in-the-loop at every handoff | Defeats autonomous delivery; introduces bottleneck that scales linearly with issue count |

## References

- `governance/personas/agentic/devops-engineer.md` -- Routing pattern agent
- `governance/personas/agentic/tech-lead.md` -- Orchestrator-Workers agent
- `governance/personas/agentic/coder.md` -- Worker agent
- `governance/personas/agentic/iac-engineer.md` -- Infrastructure Worker agent
- `governance/personas/agentic/test-evaluator.md` -- Evaluator-Optimizer agent
- `governance/personas/agentic/project-manager.md` -- Portfolio orchestrator
- `governance/prompts/agent-protocol.md` -- typed inter-agent communication contract
- `docs/architecture/agent-architecture.md` -- full architecture documentation with system diagrams
- `docs/architecture/project-manager-architecture.md` -- Project Manager mode details
