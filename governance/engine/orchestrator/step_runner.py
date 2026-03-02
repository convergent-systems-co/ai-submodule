"""Step-based orchestrator — the sole control plane for the agentic loop.

StepRunner replaces the prompt chain in startup.md. The LLM calls it via
CLI between phases; state is persisted to disk, surviving context resets.

Usage:
    runner = StepRunner(config)
    result = runner.init_session()          # Phase 0 → first phase
    result = runner.step(1, {"issues_selected": [...]})  # Complete phase 1
    ...
    # Until result.action == "shutdown" or "done"
"""

from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

from governance.engine.orchestrator.audit import AuditEvent, AuditLog
from governance.engine.orchestrator.capacity import (
    Action,
    CapacitySignals,
    Tier,
    classify_tier,
    format_gate_block,
    gate_action,
)
from governance.engine.orchestrator.checkpoint import CheckpointManager
from governance.engine.orchestrator.circuit_breaker import CircuitBreaker
from governance.engine.orchestrator.claude_code_dispatcher import ClaudeCodeDispatcher
from governance.engine.orchestrator.config import OrchestratorConfig
from governance.engine.orchestrator.session import PersistedSession, SessionStore
from governance.engine.orchestrator.state_machine import (
    InvalidTransition,
    ShutdownRequired,
    StateMachine,
)
from governance.engine.orchestrator.step_result import StepResult

# Phase descriptions for LLM instructions
_PHASE_DESCRIPTIONS: dict[int, dict] = {
    0: {
        "name": "Checkpoint Recovery",
        "description": "Scan for checkpoints, validate issues, determine resume point.",
    },
    1: {
        "name": "Pre-flight & Triage",
        "description": "Scan for open issues, triage by priority, select work batch.",
        "outputs_expected": ["issues_selected"],
    },
    2: {
        "name": "Parallel Planning",
        "description": "Create implementation plans for each selected issue.",
        "outputs_expected": ["plans"],
    },
    3: {
        "name": "Parallel Dispatch",
        "description": "Dispatch Coder agents for each planned issue.",
        "outputs_expected": ["dispatched_task_ids"],
    },
    4: {
        "name": "Collect & Review",
        "description": "Collect agent results, run Tester evaluation, handle feedback.",
        "outputs_expected": ["prs_created", "prs_resolved"],
    },
    5: {
        "name": "Merge & Loop Decision",
        "description": "Merge approved PRs, decide whether to loop or finish.",
        "outputs_expected": ["merged_prs"],
    },
}


class StepRunner:
    """Step-based orchestrator that persists state between CLI invocations.

    Composes the same primitives as OrchestratorRunner (StateMachine,
    CheckpointManager, CircuitBreaker, AuditLog) but exposes a step
    function instead of a monolithic run() loop.
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        session_id: str | None = None,
        checkpoint_schema_path: str | Path | None = None,
    ):
        self.config = config
        self._session_id = session_id or f"session-{uuid.uuid4().hex[:8]}"
        self._store = SessionStore(config.session_dir)
        self._checkpoints = CheckpointManager(
            config.checkpoint_dir,
            schema_path=checkpoint_schema_path,
        )
        self._audit = AuditLog(
            Path(config.audit_log_dir) / f"{self._session_id}.jsonl"
        )

        # Initialized on init_session() or restored from persisted state
        self._machine: StateMachine | None = None
        self._breaker: CircuitBreaker | None = None
        self._dispatcher: ClaudeCodeDispatcher | None = None
        self._session: PersistedSession | None = None

    @property
    def session_id(self) -> str:
        return self._session_id

    def init_session(self, session_id: str | None = None) -> StepResult:
        """Initialize or resume a session. Returns the first phase instruction.

        Phase 0: checkpoint recovery → determine resume phase → return instruction.
        """
        if session_id:
            self._session_id = session_id

        # Check for existing session
        existing = self._store.load(self._session_id)
        if existing:
            return self._restore_session(existing)

        # Fresh session
        self._machine = StateMachine(parallel_coders=self.config.parallel_coders)
        self._breaker = CircuitBreaker(
            max_feedback_cycles=self.config.max_feedback_cycles,
            max_total_eval_cycles=self.config.max_total_eval_cycles,
        )
        self._dispatcher = ClaudeCodeDispatcher(session_id=self._session_id)
        self._session = PersistedSession(session_id=self._session_id)

        # Phase 0: Checkpoint recovery
        resume_phase = self._phase_0_recovery()

        self._record_audit("session_init", 0, detail={
            "resume_phase": resume_phase,
            "fresh": resume_phase == 1,
        })

        # Transition to the first active phase
        return self._advance_to(resume_phase)

    def step(self, completed_phase: int, phase_result: dict | None = None) -> StepResult:
        """Complete a phase and get the next instruction.

        Args:
            completed_phase: The phase just finished by the LLM.
            phase_result: Results from the completed phase (JSON dict).

        Returns:
            StepResult with the next action and instructions.
        """
        self._ensure_session()

        # Idempotency: double-completing a phase is a no-op
        if completed_phase in self._session.completed_phases:
            return self._current_result("execute_phase")

        # Record phase completion
        self._session.completed_phases.append(completed_phase)
        self._session.current_phase = completed_phase

        # Absorb phase results into session state
        if phase_result:
            self._absorb_result(completed_phase, phase_result)

        # Determine next phase
        next_phase = self._next_phase(completed_phase)
        if next_phase is None:
            return self._done_result()

        # Advance to next phase
        return self._advance_to(next_phase)

    def record_signal(self, signal_type: str, count: int = 1) -> dict:
        """Feed a signal into the state machine.

        Args:
            signal_type: One of "tool_call", "turn", "issue_completed".
            count: Number of signals to record (default 1).

        Returns:
            Dict with current tier and signal counters.
        """
        self._ensure_session()

        tier = Tier.GREEN
        for _ in range(count):
            if signal_type == "tool_call":
                tier = self._machine.record_tool_call()
            elif signal_type == "turn":
                tier = self._machine.record_turn()
            elif signal_type == "issue_completed":
                tier = self._machine.record_issue_completed()

        # Sync signals to session
        self._sync_signals()
        self._persist()

        return {
            "tier": tier.value,
            "tool_calls": self._machine.signals.tool_calls,
            "turns": self._machine.signals.turns,
            "issues_completed": self._machine.signals.issues_completed,
        }

    def query_gate(self, phase: int) -> dict:
        """Read-only gate check without transitioning.

        Returns:
            Dict with tier, action, and gate_block text.
        """
        self._ensure_session()

        tier = classify_tier(self._machine.signals)
        action = gate_action(phase, tier)
        block = format_gate_block(phase, self._machine.signals)

        return {
            "phase": phase,
            "tier": tier.value,
            "action": action.value,
            "gate_block": block,
            "would_shutdown": action in (Action.EMERGENCY_STOP, Action.CHECKPOINT),
        }

    def get_status(self) -> dict:
        """Dump current session state."""
        if self._session is None:
            # Try loading from disk
            existing = self._store.load(self._session_id)
            if existing:
                return {
                    "session_id": existing.session_id,
                    "current_phase": existing.current_phase,
                    "completed_phases": existing.completed_phases,
                    "loop_count": existing.loop_count,
                    "tier": "unknown",
                    "signals": {
                        "tool_calls": existing.tool_calls,
                        "turns": existing.turns,
                        "issues_completed": existing.issues_completed,
                    },
                    "work": {
                        "issues_selected": existing.issues_selected,
                        "issues_done": existing.issues_done,
                        "prs_created": existing.prs_created,
                    },
                }
            return {"error": f"No session found: {self._session_id}"}

        return {
            "session_id": self._session.session_id,
            "current_phase": self._session.current_phase,
            "completed_phases": self._session.completed_phases,
            "loop_count": self._session.loop_count,
            "tier": self._machine.tier.value if self._machine else "unknown",
            "signals": {
                "tool_calls": self._machine.signals.tool_calls if self._machine else 0,
                "turns": self._machine.signals.turns if self._machine else 0,
                "issues_completed": self._machine.signals.issues_completed if self._machine else 0,
            },
            "work": {
                "issues_selected": self._session.issues_selected,
                "issues_done": self._session.issues_done,
                "prs_created": self._session.prs_created,
                "prs_resolved": self._session.prs_resolved,
                "prs_remaining": self._session.prs_remaining,
            },
            "gate_history": self._machine.get_gate_history() if self._machine else [],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_session(self) -> None:
        """Load session from disk if not in memory."""
        if self._session is not None and self._machine is not None:
            return

        existing = self._store.load(self._session_id)
        if existing is None:
            raise RuntimeError(
                f"No active session '{self._session_id}'. Call init first."
            )
        self._restore_session(existing)

    def _restore_session(self, session: PersistedSession) -> StepResult:
        """Restore in-memory state from a persisted session."""
        self._session = session
        self._session_id = session.session_id

        # Restore state machine
        if session.state_machine:
            self._machine = StateMachine.from_dict(session.state_machine)
        else:
            self._machine = StateMachine(parallel_coders=self.config.parallel_coders)

        # Restore circuit breaker
        self._breaker = CircuitBreaker(
            max_feedback_cycles=self.config.max_feedback_cycles,
            max_total_eval_cycles=self.config.max_total_eval_cycles,
        )
        for cid, state in session.circuit_breaker_state.items():
            for _ in range(state.get("feedback_cycles", 0)):
                try:
                    self._breaker.record_feedback(cid)
                except Exception:
                    break
            extra = state.get("total_eval_cycles", 0) - state.get("feedback_cycles", 0)
            for _ in range(extra):
                try:
                    self._breaker.record_reassign(cid)
                except Exception:
                    break

        # Restore dispatcher
        self._dispatcher = ClaudeCodeDispatcher(session_id=self._session_id)

        self._record_audit("session_restored", session.current_phase, detail={
            "loop_count": session.loop_count,
            "completed_phases": session.completed_phases,
        })

        # Return current state as a result
        return self._current_result("execute_phase")

    def _phase_0_recovery(self) -> int:
        """Phase 0: scan checkpoints, validate issues, determine resume phase."""
        checkpoint = self._checkpoints.load_latest()
        if checkpoint is None:
            return 1  # Fresh start

        checkpoint = self._checkpoints.validate_issues(checkpoint)
        resume_phase = self._checkpoints.determine_resume_phase(checkpoint)

        # Restore work state from checkpoint
        self._session.issues_done = checkpoint.get("issues_completed", [])
        self._session.prs_created = checkpoint.get("prs_created", [])
        self._session.prs_resolved = checkpoint.get("prs_resolved", [])
        self._session.prs_remaining = checkpoint.get("prs_remaining", [])
        self._session.issues_selected = checkpoint.get("issues_remaining", [])

        return resume_phase

    def _advance_to(self, target_phase: int) -> StepResult:
        """Transition to target phase and return instruction StepResult."""
        try:
            action = self._machine.transition(target_phase)
        except ShutdownRequired as e:
            return self._shutdown_result(e)
        except InvalidTransition:
            # If we can't transition directly, the phase is already current
            # This handles resume scenarios
            action = Action.PROCEED

        self._session.current_phase = target_phase

        # Write checkpoint on every transition
        self._write_checkpoint(f"Phase {target_phase} entry")
        self._sync_signals()
        self._persist()

        self._record_audit("gate_check", target_phase,
                           tier=self._machine.tier.value,
                           action=action.value)

        # Build the appropriate result based on phase and action
        return self._build_phase_result(target_phase, action)

    def _build_phase_result(self, phase: int, action: Action) -> StepResult:
        """Build a StepResult for the given phase and gate action."""
        tier = self._machine.tier
        gate_block = format_gate_block(phase, self._machine.signals)
        desc = _PHASE_DESCRIPTIONS.get(phase, {})

        # Determine the action string
        if phase == 3 and action == Action.SKIP_DISPATCH:
            result_action = "execute_phase"
        elif phase == 3 and action == Action.PROCEED:
            result_action = "dispatch"
        elif phase == 4:
            result_action = "collect"
        elif phase == 5:
            result_action = "merge"
        else:
            result_action = "execute_phase"

        result = StepResult(
            session_id=self._session_id,
            action=result_action,
            phase=phase,
            tier=tier.value,
            instructions={
                "name": desc.get("name", f"Phase {phase}"),
                "description": desc.get("description", ""),
                "outputs_expected": desc.get("outputs_expected", []),
                "gate_action": action.value,
            },
            gate_block=gate_block,
            signals={
                "tool_calls": self._machine.signals.tool_calls,
                "turns": self._machine.signals.turns,
                "issues_completed": self._machine.signals.issues_completed,
            },
            work={
                "issues_selected": self._session.issues_selected,
                "issues_done": self._session.issues_done,
                "prs_created": self._session.prs_created,
            },
            loop_count=self._session.loop_count,
        )

        # Add dispatch instructions for Phase 3
        if phase == 3 and action == Action.PROCEED and self._dispatcher:
            result.tasks = self._dispatcher.get_pending_instructions()

        return result

    def _next_phase(self, completed_phase: int) -> int | None:
        """Determine the next phase after completing one."""
        if completed_phase == 1:
            return 2
        elif completed_phase == 2:
            return 3
        elif completed_phase == 3:
            return 4
        elif completed_phase == 4:
            # Check if there are feedback items that need re-dispatch
            # For now, advance to merge
            return 5
        elif completed_phase == 5:
            return self._loop_decision()
        return None

    def _loop_decision(self) -> int | None:
        """Phase 5 loop decision: continue or finish?"""
        tier = self._machine.tier
        self._session.loop_count += 1

        # Orange+ → shutdown
        if tier >= Tier.ORANGE:
            return None

        # Check if there's remaining work
        has_work = bool(self._session.issues_selected) or bool(self._session.prs_remaining)
        if not has_work:
            return None  # All done

        # Green/Yellow with work remaining → loop to Phase 1
        return 1

    def _absorb_result(self, phase: int, result: dict) -> None:
        """Merge phase results into session state."""
        if phase == 1:
            self._session.issues_selected = result.get(
                "issues_selected", self._session.issues_selected
            )
        elif phase == 2:
            plans = result.get("plans", {})
            self._session.plans.update(plans)
        elif phase == 3:
            task_ids = result.get("dispatched_task_ids", [])
            self._session.dispatched_task_ids = task_ids
        elif phase == 4:
            prs = result.get("prs_created", [])
            self._session.prs_created.extend(prs)
            resolved = result.get("prs_resolved", [])
            self._session.prs_resolved.extend(resolved)
            remaining = result.get("prs_remaining", [])
            self._session.prs_remaining = remaining
            done = result.get("issues_completed", [])
            self._session.issues_done.extend(done)
            # Remove completed issues from selected
            done_set = set(done)
            self._session.issues_selected = [
                i for i in self._session.issues_selected if i not in done_set
            ]
        elif phase == 5:
            merged = result.get("merged_prs", [])
            merged_set = set(merged)
            self._session.prs_remaining = [
                p for p in self._session.prs_remaining if p not in merged_set
            ]

    def _shutdown_result(self, exc: ShutdownRequired) -> StepResult:
        """Build a shutdown StepResult from a ShutdownRequired exception."""
        self._write_checkpoint(
            f"Shutdown: tier={exc.tier.value}, action={exc.action.value}",
            context_capacity={
                "tier": exc.tier.value,
                "tool_calls": self._machine.signals.tool_calls,
                "turn_count": self._machine.signals.turns,
                "issues_completed_count": self._machine.signals.issues_completed,
            },
        )
        self._record_audit("shutdown", self._machine.phase,
                           tier=exc.tier.value, action=exc.action.value)
        self._persist()

        return StepResult(
            session_id=self._session_id,
            action="shutdown",
            phase=self._machine.phase,
            tier=exc.tier.value,
            signals={
                "tool_calls": self._machine.signals.tool_calls,
                "turns": self._machine.signals.turns,
                "issues_completed": self._machine.signals.issues_completed,
            },
            work={
                "issues_selected": self._session.issues_selected,
                "issues_done": self._session.issues_done,
            },
            shutdown_info={
                "reason": str(exc),
                "tier": exc.tier.value,
                "action": exc.action.value,
                "gates_passed": exc.gates_passed,
            },
            loop_count=self._session.loop_count,
        )

    def _done_result(self) -> StepResult:
        """Build a done StepResult — all work complete."""
        self._record_audit("session_done", self._session.current_phase, detail={
            "loop_count": self._session.loop_count,
            "issues_done": len(self._session.issues_done),
        })
        self._persist()

        return StepResult(
            session_id=self._session_id,
            action="done",
            phase=self._session.current_phase,
            tier=self._machine.tier.value if self._machine else "green",
            signals={
                "tool_calls": self._machine.signals.tool_calls if self._machine else 0,
                "turns": self._machine.signals.turns if self._machine else 0,
                "issues_completed": self._machine.signals.issues_completed if self._machine else 0,
            },
            work={
                "issues_selected": self._session.issues_selected,
                "issues_done": self._session.issues_done,
                "prs_created": self._session.prs_created,
            },
            loop_count=self._session.loop_count,
        )

    def _current_result(self, action: str) -> StepResult:
        """Build a StepResult reflecting current state."""
        phase = self._session.current_phase if self._session else 0
        tier = self._machine.tier if self._machine else Tier.GREEN
        gate_block = format_gate_block(phase, self._machine.signals) if self._machine else ""
        desc = _PHASE_DESCRIPTIONS.get(phase, {})

        return StepResult(
            session_id=self._session_id,
            action=action,
            phase=phase,
            tier=tier.value,
            instructions={
                "name": desc.get("name", f"Phase {phase}"),
                "description": desc.get("description", ""),
                "outputs_expected": desc.get("outputs_expected", []),
            },
            gate_block=gate_block,
            signals={
                "tool_calls": self._machine.signals.tool_calls if self._machine else 0,
                "turns": self._machine.signals.turns if self._machine else 0,
                "issues_completed": self._machine.signals.issues_completed if self._machine else 0,
            },
            work={
                "issues_selected": self._session.issues_selected if self._session else [],
                "issues_done": self._session.issues_done if self._session else [],
                "prs_created": self._session.prs_created if self._session else [],
            },
            loop_count=self._session.loop_count if self._session else 0,
        )

    def _sync_signals(self) -> None:
        """Sync state machine signals to session for persistence."""
        if self._machine and self._session:
            self._session.tool_calls = self._machine.signals.tool_calls
            self._session.turns = self._machine.signals.turns
            self._session.issues_completed = self._machine.signals.issues_completed
            self._session.state_machine = self._machine.to_dict()
            self._session.gate_history = self._machine.get_gate_history()

            # Sync circuit breaker state
            if self._breaker:
                self._session.circuit_breaker_state = {
                    cid: {
                        "feedback_cycles": unit.feedback_cycles,
                        "total_eval_cycles": unit.total_eval_cycles,
                        "blocked": unit.blocked,
                    }
                    for cid, unit in self._breaker.all_units.items()
                }

    def _persist(self) -> None:
        """Save session state to disk."""
        if self._session:
            self._sync_signals()
            self._store.save(self._session)

    def _write_checkpoint(
        self,
        current_step: str,
        context_capacity: dict | None = None,
    ) -> Path:
        """Write a checkpoint with current state."""
        branch = self._get_current_branch()
        return self._checkpoints.write(
            session_id=self._session_id,
            branch=branch,
            issues_completed=self._session.issues_done if self._session else [],
            issues_remaining=self._session.issues_selected if self._session else [],
            prs_created=self._session.prs_created if self._session else [],
            prs_resolved=self._session.prs_resolved if self._session else [],
            prs_remaining=self._session.prs_remaining if self._session else [],
            current_step=current_step,
            pending_work=(
                f"{len(self._session.issues_selected)} issues remaining"
                if self._session else ""
            ),
            context_capacity=context_capacity or (
                {
                    "tier": self._machine.tier.value,
                    "tool_calls": self._machine.signals.tool_calls,
                    "turn_count": self._machine.signals.turns,
                    "issues_completed_count": self._machine.signals.issues_completed,
                }
                if self._machine else {}
            ),
            context_gates_passed=(
                self._machine.get_gate_history() if self._machine else []
            ),
        )

    def _record_audit(
        self,
        event_type: str,
        phase: int,
        tier: str | None = None,
        action: str | None = None,
        correlation_id: str | None = None,
        detail: dict | None = None,
    ) -> None:
        """Record an audit event."""
        self._audit.record(AuditEvent(
            event_type=event_type,
            phase=phase,
            session_id=self._session_id,
            tier=tier,
            action=action,
            correlation_id=correlation_id,
            detail=detail or {},
        ))

    @staticmethod
    def _get_current_branch() -> str:
        """Get current git branch name."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True, timeout=5,
            )
            return result.stdout.strip() or "unknown"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return "unknown"
