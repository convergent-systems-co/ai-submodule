# Deterministic Orchestrator Architecture

## Overview

The deterministic orchestrator (`governance/engine/orchestrator/`) is a Python control plane that holds the program counter for the agentic governance loop. It replaces self-governing prompt chains with code-enforced phase transitions, capacity gates, and circuit breakers.

**Key inversion:** Code calls agent, not agent self-governing. Safety-critical decisions (when to stop, what to skip, when to checkpoint) are enforced by deterministic Python logic. Creative work (planning, coding, reviewing) stays with AI agents.

## Architecture

```
┌─────────────────────────────────────────────┐
│              OrchestratorRunner              │
│  (entry point — manages Phase 0→5 loop)     │
├─────────────────────────────────────────────┤
│  StateMachine    │  CheckpointManager        │
│  (phase gates)   │  (write/load/validate)    │
├──────────────────┼──────────────────────────┤
│  CircuitBreaker  │  AuditLog                 │
│  (per-work-unit) │  (append-only JSONL)      │
├──────────────────┼──────────────────────────┤
│  Dispatcher      │  OrchestratorConfig       │
│  (agent spawn)   │  (from project.yaml)      │
├──────────────────┴──────────────────────────┤
│              capacity.py                     │
│  (Tier classification + Gate action matrix)  │
└─────────────────────────────────────────────┘
```

## Modules

| Module | Purpose | Lines |
|--------|---------|-------|
| `capacity.py` | Tier classification (Green/Yellow/Orange/Red), gate actions, thresholds | ~120 |
| `state_machine.py` | Phase transitions with gate enforcement, `ShutdownRequired` | ~70 |
| `checkpoint.py` | Write/load/validate/cleanup checkpoints, resume phase determination | ~110 |
| `circuit_breaker.py` | Per-work-unit eval cycle tracking (max 3 feedback, max 5 total) | ~65 |
| `audit.py` | Append-only JSONL event logging | ~50 |
| `dispatcher.py` | Abstract dispatch interface + `DryRunDispatcher` for testing | ~60 |
| `config.py` | Configuration loader from `project.yaml` | ~35 |
| `runner.py` | Entry point — Phase 0→5 loop with checkpoints on every transition | ~130 |

## Capacity Model

### Four Tiers

| Tier | Tool Calls | Turns | Issues Completed (N=parallel_coders) |
|------|-----------|-------|--------------------------------------|
| Green | 0–49 | 0–59 | 0 to N-3 |
| Yellow | 50–64 | 60–99 | N-2 |
| Orange | 65–79 | 100–139 | N-1 |
| Red | 80+ | 140+ | N+ |

Additional Red triggers: `system_warning=True`, `degraded_recall=True`.

Highest tier across all signals wins. When `parallel_coders=-1` (unlimited mode), issue completion signal is disabled.

### Phase-Tier-Action Matrix

| Phase | Green | Yellow | Orange | Red |
|-------|-------|--------|--------|-----|
| 0 (Recovery) | proceed | proceed | emergency-stop | emergency-stop |
| 1 (Triage) | proceed | proceed | emergency-stop | emergency-stop |
| 2 (Planning) | proceed | proceed | emergency-stop | emergency-stop |
| 3 (Dispatch) | proceed | skip-dispatch | emergency-stop | emergency-stop |
| 4 (Collect) | proceed | finish-current | finish-current | emergency-stop |
| 5 (Merge) | proceed | proceed | emergency-stop | emergency-stop |

## Phase Loop

```
Phase 0: Checkpoint Recovery
  └─ Load latest checkpoint, validate issues still open, determine resume phase

Phase 1: Pre-flight & Triage (agent-driven)
  └─ Gate check → checkpoint → agent work

Phase 2: Planning (agent-driven)
  └─ Gate check → checkpoint → agent work

Phase 3: Parallel Dispatch
  └─ Gate check → if Yellow: skip dispatch
  └─ Dispatch up to N Coder agents (N = parallel_coders)

Phase 4: Collect & Evaluate
  └─ Gate check → if Yellow/Orange: finish current only
  └─ Circuit breaker per work unit (max 3 feedback, max 5 total)

Phase 5: Merge & Loop Decision
  └─ Gate check → merge PRs
  └─ If issues_completed >= N or Orange+: shutdown with checkpoint
  └─ Otherwise: loop to Phase 1
```

## Circuit Breaker

Per-work-unit limits prevent infinite evaluation loops:

- **Max 3 Tester FEEDBACK cycles** per work unit — after 3 rounds of Tester feedback, the unit is blocked
- **Max 5 total evaluation cycles** per work unit — including reassignments
- Blocked units are skipped in subsequent dispatch rounds
- Configurable via `max_feedback_cycles` and `max_total_eval_cycles` in config

## Audit Trail

Every orchestrator event is logged as append-only JSONL:

- `session_start` — with resume phase
- `checkpoint_recovery` — with found/not-found and details
- `gate_check` — phase, tier, action on every transition
- `dispatch` — agent count and correlation IDs
- `evaluation` — per work unit
- `circuit_breaker_blocked` — when a unit hits limits
- `merge_start` — with PR list
- `shutdown` — tier and action that triggered it

## Backward Compatibility

The orchestrator is additive. The existing prompt-chained loop (`startup.md`) continues to work unchanged. The orchestrator can be adopted incrementally:

1. **Phase 1:** Use `capacity.py` + `state_machine.py` as a validation layer — startup.md calls the orchestrator to check gates
2. **Phase 2:** Use `runner.py` as the loop driver — replaces the self-navigating prompt chain
3. **Phase 3:** Use `dispatcher.py` for real agent dispatch via Claude Code `Task` tool

## Testing

165 tests across 6 test files with 93% coverage:

- `test_capacity.py` — Tier classification, gate actions, boundary conditions, edge cases
- `test_state_machine.py` — Transitions, gate enforcement, signal recording, history
- `test_circuit_breaker.py` — Feedback limits, total limits, isolation, custom config
- `test_audit.py` — Event logging, JSONL format, directory creation
- `test_checkpoint_orchestrator.py` — Write/load, resume phase, issue validation, cleanup
- `test_runner.py` — Full lifecycle, Phase 0 recovery, gate enforcement, dispatch, Phase 5 decisions, audit

Run tests:
```bash
PYTHONPATH=/path/to/repo .venv/bin/python -m pytest governance/engine/tests/ -v
```
