# Deterministic Orchestrator — Civilization-Grade Agentic Governance Control Plane

**Author:** Code Manager (agentic)
**Date:** 2026-03-01
**Status:** approved
**Issue:** #549
**Branch:** NETWORK_ID/feat/549/deterministic-orchestrator

---

## 1. Objective

Build a deterministic Python orchestrator that replaces prompt-chaining as the agentic loop's control plane. The orchestrator holds the program counter, enforces phase gates, manages checkpoints, tracks circuit breakers, and dispatches agents for bounded cognitive tasks. Agents never see the full loop — they receive a task, return a result, and the orchestrator decides what happens next.

The outcome: enforcement is independent of agent compliance. Safety properties (tier classification, gate enforcement, circuit breakers, checkpoint lifecycle) are testable, auditable, and model-agnostic.

## 2. Rationale

The current agentic loop is a 1,200-line markdown prompt (`startup.md`) that an AI agent reads and self-executes. The safety properties depend on the agent:
- Counting its own tool calls accurately
- Self-classifying into the correct capacity tier
- Voluntarily stopping at Orange/Red tier
- Writing checkpoints before context exhaustion
- Enforcing circuit breakers on evaluation cycles

This works in practice but fails the civilization-grade test: the governed entity is its own enforcement mechanism. A non-compliant agent (or a model regression that changes compliance behavior) silently bypasses all safety.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep prompt-chaining, add more enforcement prose | Yes | More prose doesn't create enforcement — it creates longer instructions the agent may ignore |
| MCP server for orchestration | Yes | Over-engineered for single-session; adds network dependency; MCP is for tool exposure, not control flow |
| Full application framework (LangGraph, CrewAI) | Yes | External dependency; opinionated; doesn't integrate with existing policy engine; vendor lock-in |
| Deterministic Python orchestrator (internal) | Yes | **Selected** — leverages existing policy engine patterns, no external deps, incrementally adoptable, testable |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/engine/orchestrator/__init__.py` | Package init, exports public API |
| `governance/engine/orchestrator/capacity.py` | Tier classification (Green/Yellow/Orange/Red), gate action computation |
| `governance/engine/orchestrator/state_machine.py` | Phase state machine, valid transitions, gate enforcement at boundaries |
| `governance/engine/orchestrator/checkpoint.py` | Deterministic checkpoint read/write/validate, Phase 0 recovery logic |
| `governance/engine/orchestrator/circuit_breaker.py` | Per-work-unit evaluation cycle tracking, max enforcement |
| `governance/engine/orchestrator/audit.py` | Structured event logging (JSONL), deterministic (not agent-written) |
| `governance/engine/orchestrator/dispatcher.py` | Platform-agnostic agent dispatch interface (abstract base + Claude Code impl) |
| `governance/engine/orchestrator/runner.py` | Entry point — executes Phase 0-5 loop using state machine |
| `governance/engine/orchestrator/config.py` | Reads project.yaml + startup.md thresholds into typed config |
| `governance/engine/tests/test_capacity.py` | Tier classification tests |
| `governance/engine/tests/test_state_machine.py` | Phase transition and gate enforcement tests |
| `governance/engine/tests/test_checkpoint_orchestrator.py` | Checkpoint lifecycle tests |
| `governance/engine/tests/test_circuit_breaker.py` | Evaluation cycle tracking tests |
| `governance/engine/tests/test_audit.py` | Event logging tests |
| `governance/engine/tests/test_runner.py` | Integration tests for full loop |
| `governance/schemas/orchestrator-state.schema.json` | JSON schema for orchestrator runtime state |
| `docs/architecture/orchestrator.md` | Architecture documentation |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Add structured metadata comments (thresholds, transitions) parseable by orchestrator config loader. Retain full prose for prompt-chained fallback mode. |
| `governance/engine/pyproject.toml` | Add orchestrator to package, no new external dependencies |
| `CLAUDE.md` | Document orchestrator architecture, runner entry point |
| `docs/architecture/context-management.md` | Update to reference orchestrator as primary enforcement, prompt gates as fallback |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions — prompt-chained mode preserved as fallback |

## 4. Approach

### Step 1: `capacity.py` — Tier Classification (Supersedes #546)

Extract the tier classification logic from startup.md into deterministic Python:

```python
from enum import Enum
from dataclasses import dataclass

class Tier(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"

class Action(Enum):
    PROCEED = "proceed"
    SKIP_DISPATCH = "skip-dispatch"
    FINISH_CURRENT = "finish-current"
    CHECKPOINT = "checkpoint"
    EMERGENCY_STOP = "emergency-stop"

@dataclass
class CapacitySignals:
    tool_calls: int = 0
    turns: int = 0
    issues_completed: int = 0
    parallel_coders: int = 5       # -1 = unlimited
    system_warning: bool = False
    degraded_recall: bool = False

def classify_tier(signals: CapacitySignals) -> Tier:
    """Deterministic tier classification. Any single Red signal → Red."""

# Phase-tier-action matrix (from startup.md lines 117-157)
GATE_ACTIONS: dict[tuple[int, Tier], Action] = {
    (0, Tier.GREEN): Action.PROCEED,
    (0, Tier.YELLOW): Action.PROCEED,
    (0, Tier.ORANGE): Action.EMERGENCY_STOP,
    (0, Tier.RED): Action.EMERGENCY_STOP,
    (1, Tier.GREEN): Action.PROCEED,
    (1, Tier.YELLOW): Action.PROCEED,
    (1, Tier.ORANGE): Action.EMERGENCY_STOP,
    (1, Tier.RED): Action.EMERGENCY_STOP,
    (2, Tier.GREEN): Action.PROCEED,
    (2, Tier.YELLOW): Action.PROCEED,
    (2, Tier.ORANGE): Action.EMERGENCY_STOP,
    (2, Tier.RED): Action.EMERGENCY_STOP,
    (3, Tier.GREEN): Action.PROCEED,
    (3, Tier.YELLOW): Action.SKIP_DISPATCH,
    (3, Tier.ORANGE): Action.EMERGENCY_STOP,
    (3, Tier.RED): Action.EMERGENCY_STOP,
    (4, Tier.GREEN): Action.PROCEED,
    (4, Tier.YELLOW): Action.FINISH_CURRENT,
    (4, Tier.ORANGE): Action.FINISH_CURRENT,
    (4, Tier.RED): Action.EMERGENCY_STOP,
    (5, Tier.GREEN): Action.PROCEED,
    (5, Tier.YELLOW): Action.PROCEED,  # merge but don't loop
    (5, Tier.ORANGE): Action.EMERGENCY_STOP,
    (5, Tier.RED): Action.EMERGENCY_STOP,
}

def gate_action(phase: int, tier: Tier) -> Action:
    """Deterministic gate action lookup."""
    return GATE_ACTIONS[(phase, tier)]

def format_gate_block(phase: int, signals: CapacitySignals) -> str:
    """Produce the mandatory context gate output block."""
```

**Thresholds** (extracted from startup.md):

| Signal | Green | Yellow | Orange | Red |
|--------|-------|--------|--------|-----|
| tool_calls | < 50 | 50-65 | 65-80 | > 80 |
| turns | < 60 | 60-100 | 100-140 | > 140 |
| issues_completed (N != -1) | < N-2 | N-2 | N-1 | >= N |
| system_warning | — | — | — | Red |
| degraded_recall | — | — | — | Red |

### Step 2: `state_machine.py` — Phase Transitions

Define the state machine that enforces valid phase transitions:

```python
@dataclass
class PhaseState:
    phase: int                    # 0-5
    sub_phase: str | None = None  # e.g., "4a", "4e"

VALID_TRANSITIONS: dict[int, set[int]] = {
    0: {1, 2, 3, 4, 5},  # Phase 0 can resume to any phase
    1: {2},                # Pre-flight → Planning
    2: {3},                # Planning → Dispatch
    3: {4},                # Dispatch → Review
    4: {3, 5},             # Review → Re-dispatch (feedback) or Merge
    5: {1},                # Merge → Loop back to Pre-flight
}

class StateMachine:
    def __init__(self, config: OrchestratorConfig):
        self.state = PhaseState(phase=0)
        self.config = config
        self.signals = CapacitySignals(parallel_coders=config.parallel_coders)
        self.gates_passed: list[dict] = []

    def transition(self, target_phase: int) -> Action:
        """Attempt phase transition. Returns action after gate check.
        Raises InvalidTransition if transition is not valid."""
        if target_phase not in VALID_TRANSITIONS[self.state.phase]:
            raise InvalidTransition(self.state.phase, target_phase)

        tier = classify_tier(self.signals)
        action = gate_action(target_phase, tier)
        self.gates_passed.append({
            "phase": target_phase,
            "tier": tier.value,
            "action": action.value,
            "tool_calls": self.signals.tool_calls,
            "turns": self.signals.turns,
        })

        if action in (Action.EMERGENCY_STOP, Action.CHECKPOINT):
            raise ShutdownRequired(tier, action, self.gates_passed)

        self.state = PhaseState(phase=target_phase)
        return action

    def record_tool_call(self) -> Tier:
        """Increment and return current tier."""
        self.signals.tool_calls += 1
        return classify_tier(self.signals)

    def record_turn(self) -> Tier:
        """Increment and return current tier."""
        self.signals.turns += 1
        return classify_tier(self.signals)

    def record_issue_completed(self) -> Tier:
        """Increment and return current tier."""
        self.signals.issues_completed += 1
        return classify_tier(self.signals)
```

The key guarantee: **`transition()` raises `ShutdownRequired` if the gate check fails.** The caller cannot proceed. This is enforcement, not suggestion.

### Step 3: `checkpoint.py` — Deterministic Lifecycle

```python
class CheckpointManager:
    def __init__(self, checkpoint_dir: str, schema_path: str):
        self.checkpoint_dir = checkpoint_dir
        self.schema = load_schema(schema_path)

    def write(self, state: StateMachine, work: WorkTracker) -> str:
        """Write checkpoint. Called by orchestrator on every state transition
        and mandatory on shutdown. Returns checkpoint file path."""

    def load_latest(self) -> dict | None:
        """Load most recent checkpoint file. Returns None if no checkpoints."""

    def validate(self, checkpoint: dict) -> list[str]:
        """Validate checkpoint against schema. Returns list of errors."""

    def validate_issues(self, checkpoint: dict) -> dict:
        """Check issue states via gh CLI. Returns updated checkpoint
        with closed issues removed."""

    def determine_resume_phase(self, checkpoint: dict) -> int:
        """Deterministic phase selection based on checkpoint state."""
```

Checkpoint writes happen on every `StateMachine.transition()` call, not just shutdown. This means every phase boundary produces a recovery point. The checkpoint is always consistent because the state machine is the single source of truth.

### Step 4: `circuit_breaker.py` — Evaluation Cycle Tracking

```python
@dataclass
class WorkUnit:
    correlation_id: str          # "issue-42"
    eval_cycles: int = 0         # Tracks FEEDBACK + re-ASSIGN
    max_cycles: int = 5          # From agent-protocol.md
    feedback_cycles: int = 0     # Tracks Tester FEEDBACK only
    max_feedback: int = 3        # From agent-protocol.md
    blocked: bool = False

class CircuitBreaker:
    def __init__(self, max_eval_cycles: int = 5, max_feedback_cycles: int = 3):
        self.work_units: dict[str, WorkUnit] = {}

    def record_feedback(self, correlation_id: str) -> WorkUnit:
        """Record a FEEDBACK cycle. Raises CircuitBreakerTripped
        if either limit is exceeded."""

    def record_reassign(self, correlation_id: str) -> WorkUnit:
        """Record a re-ASSIGN after BLOCK/ESCALATE."""

    def can_dispatch(self, correlation_id: str) -> bool:
        """Check if work unit can accept more cycles."""
```

### Step 5: `audit.py` — Structured Event Logging

```python
@dataclass
class AuditEvent:
    timestamp: str           # ISO 8601
    session_id: str
    event_type: str          # "gate_check", "phase_transition", "dispatch", "checkpoint", etc.
    phase: int
    tier: str
    correlation_id: str | None
    detail: dict

class AuditLog:
    def __init__(self, log_path: str):
        self.log_path = log_path

    def record(self, event: AuditEvent) -> None:
        """Append event to JSONL file. Called by orchestrator, not agent."""
```

The critical difference from today: the audit log is written by the orchestrator (deterministic code), not by agents (honor system). Every state transition, gate check, dispatch, and checkpoint is logged regardless of agent behavior.

### Step 6: `dispatcher.py` — Platform-Agnostic Agent Dispatch

```python
from abc import ABC, abstractmethod

@dataclass
class AgentTask:
    persona: str             # Path to persona .md file
    plan: str                # Path to plan .md file
    issue_body: str          # Issue content
    branch: str              # Target branch
    constraints: dict        # Timeout, resource limits
    correlation_id: str

@dataclass
class AgentResult:
    correlation_id: str
    success: bool
    branch: str | None       # Worktree branch with commits
    summary: str
    test_results: dict | None
    error: str | None

class Dispatcher(ABC):
    @abstractmethod
    def dispatch(self, tasks: list[AgentTask]) -> list[str]:
        """Dispatch agents. Returns task IDs for tracking."""

    @abstractmethod
    def collect(self, task_ids: list[str], timeout: int) -> list[AgentResult]:
        """Collect results. Blocks until all complete or timeout."""

class ClaudeCodeDispatcher(Dispatcher):
    """Dispatches via Claude Code Task tool with worktree isolation."""

    def dispatch(self, tasks: list[AgentTask]) -> list[str]:
        """Produces Task tool invocations. In practice, this generates
        the prompt payloads that the runner feeds to the Task tool."""

    def collect(self, task_ids: list[str], timeout: int) -> list[AgentResult]:
        """Reads Task tool results as they arrive."""
```

The dispatcher abstraction is what makes the orchestrator model-agnostic. A `CopilotDispatcher` or `APIDispatcher` implements the same interface with different transport.

### Step 7: `runner.py` — Entry Point

```python
class OrchestratorRunner:
    def __init__(self, config: OrchestratorConfig):
        self.machine = StateMachine(config)
        self.checkpoints = CheckpointManager(config.checkpoint_dir, config.schema_path)
        self.breaker = CircuitBreaker()
        self.audit = AuditLog(config.audit_log_path)
        self.dispatcher = ClaudeCodeDispatcher()

    def run(self) -> None:
        """Execute the Phase 0-5 loop.

        Phase 0: Check for checkpoint, validate, determine resume phase
        Phase 1: Pre-flight and triage (agent-driven, bounded)
        Phase 2: Planning (agent-driven, bounded)
        Phase 3: Dispatch workers (orchestrator-controlled concurrency)
        Phase 4: Collect results, evaluate (policy engine + agent review)
        Phase 5: Merge and loop decision (deterministic)
        """

    def _phase_0(self) -> int:
        """Checkpoint recovery. Returns resume phase."""
        action = self.machine.transition(0)
        self.audit.record(...)
        checkpoint = self.checkpoints.load_latest()
        if checkpoint:
            checkpoint = self.checkpoints.validate_issues(checkpoint)
            return self.checkpoints.determine_resume_phase(checkpoint)
        return 1

    def _phase_3(self, plans: list[Plan]) -> list[str]:
        """Dispatch workers with orchestrator-controlled concurrency."""
        action = self.machine.transition(3)
        if action == Action.SKIP_DISPATCH:
            return []  # Yellow tier — no new dispatches

        tasks = [self._build_agent_task(plan) for plan in plans]
        # Respect parallel_coders limit
        tasks = tasks[:self.config.parallel_coders]
        task_ids = self.dispatcher.dispatch(tasks)
        self.audit.record(...)
        return task_ids

    def _phase_5_loop_decision(self) -> bool:
        """Deterministic: should we loop back to Phase 1?"""
        tier = classify_tier(self.machine.signals)
        if tier in (Tier.ORANGE, Tier.RED):
            raise ShutdownRequired(tier, Action.CHECKPOINT, self.machine.gates_passed)
        if self.machine.signals.issues_completed >= self.config.parallel_coders:
            if self.config.parallel_coders != -1:
                raise ShutdownRequired(tier, Action.CHECKPOINT, self.machine.gates_passed)
        return True  # Loop
```

### Step 8: Integration with startup.md

Add structured metadata to startup.md that the orchestrator can parse:

```markdown
<!-- ORCHESTRATOR_CONFIG
thresholds:
  green: {tool_calls: 50, turns: 60}
  yellow: {tool_calls: 65, turns: 100}
  orange: {tool_calls: 80, turns: 140}
  red: {tool_calls: 80, turns: 140}
transitions:
  0: [1, 2, 3, 4, 5]
  1: [2]
  2: [3]
  3: [4]
  4: [3, 5]
  5: [1]
circuit_breaker:
  max_feedback_cycles: 3
  max_total_eval_cycles: 5
ORCHESTRATOR_CONFIG -->
```

The prose remains for prompt-chained fallback. The structured comments are the orchestrator's configuration source. One source of truth, two consumers.

### Step 9: Documentation and Migration Guide

- Write `docs/architecture/orchestrator.md` covering architecture, API, migration path
- Update `docs/architecture/context-management.md` to reference orchestrator as primary enforcement
- Update CLAUDE.md with runner entry point instructions
- Document fallback: platforms without Python still use prompt-chained mode

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `capacity.py` | All tier classification paths, edge cases (exactly-on-boundary), unlimited mode, single-Red-signal escalation |
| Unit | `state_machine.py` | All valid transitions accepted, invalid transitions rejected, gate enforcement at each boundary |
| Unit | `checkpoint.py` | Schema validation, round-trip (write→read), resume phase determination, closed-issue removal |
| Unit | `circuit_breaker.py` | Feedback cycle limit (3), total eval cycle limit (5), per-work-unit isolation |
| Unit | `audit.py` | JSONL append, event schema validation, concurrent write safety |
| Integration | `runner.py` | Full Phase 0→5 loop with mocked dispatcher, verify gate checks fire at every boundary |
| Integration | `runner.py` | Shutdown protocol: simulate Orange tier mid-Phase-4, verify checkpoint written |
| Property | `capacity.py` | Hypothesis: random signal values always produce valid tier; Red signals always dominate |
| Property | `state_machine.py` | Hypothesis: random transition sequences never reach invalid state |

Target: >80% coverage across all orchestrator modules.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Orchestrator state drifts from agent's perception of state | Med | Med | Orchestrator is authoritative — agents receive bounded tasks, not loop state |
| Runner can't replicate all startup.md edge cases | Med | Low | Prompt-chained fallback mode preserved; runner covers the 95% path |
| Python unavailable on some platforms | Low | Med | Orchestrator is optional enhancement; prompt-chained mode is always available |
| Dispatcher abstraction too leaky for non-Claude platforms | Med | Low | Start with ClaudeCodeDispatcher only; extend when needed |
| Checkpoint-on-every-transition creates too many files | Low | Low | Rotate: keep last 3 checkpoints, delete older ones |
| startup.md structured metadata drifts from prose | Med | Med | CI test validates structured metadata matches prose thresholds |

## 7. Dependencies

- [x] No external dependencies — uses only Python stdlib + existing jsonschema (already in policy engine deps)
- [ ] #540 (context management tests) — complementary; orchestrator makes these tests easier
- [ ] #541 (agentic protocol tests) — protocol validation can use circuit_breaker.py
- [ ] #546 (capacity tracker) — **superseded** by capacity.py in this plan

## 8. Backward Compatibility

**Fully backward compatible.** The orchestrator is additive:

- **Prompt-chained mode** (current): startup.md continues to work as-is. Platforms without Python or without the orchestrator installed fall back to agent self-governance.
- **Orchestrator mode** (new): Runner executes the loop. Agents are called for bounded tasks. startup.md provides configuration via structured metadata comments.
- **Migration**: No consuming repo changes required. The orchestrator is opt-in — activated by invoking `runner.py` instead of reading startup.md directly.
- **Coexistence**: The structured metadata comments in startup.md are invisible to prompt-chained agents (HTML comments). The prose is ignored by the orchestrator (reads only structured config).

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New Python package with safety-critical logic |
| security-review | Yes | Orchestrator controls agent dispatch and checkpoint access |
| architecture-review | Yes | Architectural inversion from prompt-chained to code-driven |
| threat-modeling | Yes | New control plane — attack surface analysis needed |
| documentation-review | Yes | New architecture docs |
| cost-analysis | Yes | Default required |
| data-governance-review | Yes | Default required |

**Policy Profile:** default
**Expected Risk Level:** medium (architectural change, but additive and backward compatible)

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-01 | Moderate+ extraction (not full) | Cognitive plane (personas, reviews) stays as prompts — only safety/enforcement logic becomes code |
| 2026-03-01 | No external framework dependencies | LangGraph/CrewAI add vendor lock-in and don't integrate with existing policy engine |
| 2026-03-01 | Structured metadata in startup.md (not separate config) | Single source of truth — prose and structured config coexist in one file |
| 2026-03-01 | Checkpoint on every transition (not just shutdown) | Every phase boundary is a recovery point — more resilient than shutdown-only checkpoints |
| 2026-03-01 | Dispatcher as abstract base | Enables future Copilot, API, and CI dispatchers without changing orchestrator core |
| 2026-03-01 | Supersede #546 and #547 | Capacity tracker (#546) is absorbed into capacity.py; delivery mechanism (#547) is answered by this plan |
