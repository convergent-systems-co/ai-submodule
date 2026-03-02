"""Orchestrator runner — entry point for the deterministic agentic loop.

This replaces startup.md as the loop driver. The runner:
1. Manages the state machine (phase transitions with gate enforcement)
2. Writes checkpoints on every state transition
3. Dispatches agents for bounded cognitive tasks
4. Tracks circuit breakers per work unit
5. Produces a deterministic audit trail

The runner does NOT perform cognitive work (planning, coding, reviewing).
That stays with the agents. The runner holds the program counter.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from governance.engine.orchestrator.audit import AuditEvent, AuditLog
from governance.engine.orchestrator.capacity import (
    Action,
    Tier,
    classify_tier,
    format_gate_block,
)
from governance.engine.orchestrator.checkpoint import CheckpointManager
from governance.engine.orchestrator.circuit_breaker import CircuitBreaker, CircuitBreakerTripped
from governance.engine.orchestrator.config import OrchestratorConfig
from governance.engine.orchestrator.dispatcher import (
    AgentPersona,
    AgentResult,
    AgentTask,
    Dispatcher,
    DryRunDispatcher,
)
from governance.engine.orchestrator.state_machine import (
    ShutdownRequired,
    StateMachine,
)


@dataclass
class SessionState:
    """Tracks work items across the session."""

    session_id: str
    issues_selected: list[str] = field(default_factory=list)
    issues_completed: list[str] = field(default_factory=list)
    prs_created: list[str] = field(default_factory=list)
    prs_resolved: list[str] = field(default_factory=list)
    prs_remaining: list[str] = field(default_factory=list)
    plans: dict[str, str] = field(default_factory=dict)  # correlation_id → plan content


class OrchestratorRunner:
    """Deterministic orchestrator for the agentic governance loop.

    Usage:
        config = load_config("project.yaml")
        runner = OrchestratorRunner(config, session_id="20260301-session-1")
        runner.run()
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        session_id: str,
        dispatcher: Dispatcher | None = None,
        checkpoint_schema_path: str | Path | None = None,
    ):
        self.config = config
        self.session_id = session_id
        self.machine = StateMachine(parallel_coders=config.parallel_coders)
        self.checkpoints = CheckpointManager(
            config.checkpoint_dir,
            schema_path=checkpoint_schema_path,
        )
        self.breaker = CircuitBreaker(
            max_feedback_cycles=config.max_feedback_cycles,
            max_total_eval_cycles=config.max_total_eval_cycles,
        )
        self.audit = AuditLog(
            Path(config.audit_log_dir) / f"{session_id}.jsonl"
        )
        self.dispatcher = dispatcher or DryRunDispatcher()
        self.work = SessionState(session_id=session_id)

    def run(self) -> SessionState:
        """Execute the Phase 0→5 loop.

        Returns the final session state. Raises ShutdownRequired if
        context capacity triggers shutdown (this is expected behavior —
        the caller writes the checkpoint).
        """
        try:
            resume_phase = self._phase_0()
            self._audit("session_start", 0, detail={"resume_phase": resume_phase})

            if resume_phase <= 1:
                self._enter_phase(1)
                # Phase 1: Pre-flight & Triage (agent-driven)
                self._audit("phase_complete", 1)

            if resume_phase <= 2:
                self._enter_phase(2)
                # Phase 2: Planning (agent-driven)
                self._audit("phase_complete", 2)

            if resume_phase <= 3:
                action = self._enter_phase(3)
                if action != Action.SKIP_DISPATCH:
                    self._phase_3_dispatch()
                self._audit("phase_complete", 3)

            if resume_phase <= 4:
                action = self._enter_phase(4)
                self._phase_4_collect(action)
                self._audit("phase_complete", 4)

            self._enter_phase(5)
            self._phase_5_merge()
            self._audit("phase_complete", 5)

            return self.work

        except ShutdownRequired as e:
            self._handle_shutdown(e)
            raise

    def _phase_0(self) -> int:
        """Checkpoint recovery. Returns the phase to resume from."""
        checkpoint = self.checkpoints.load_latest()
        if checkpoint is None:
            self._audit("checkpoint_recovery", 0, detail={"found": False})
            return 1

        # Validate issues are still open
        checkpoint = self.checkpoints.validate_issues(checkpoint)

        # Determine resume phase
        resume_phase = self.checkpoints.determine_resume_phase(checkpoint)

        # Restore work state from checkpoint
        self.work.issues_completed = checkpoint.get("issues_completed", [])
        self.work.prs_created = checkpoint.get("prs_created", [])
        self.work.prs_resolved = checkpoint.get("prs_resolved", [])
        self.work.prs_remaining = checkpoint.get("prs_remaining", [])
        self.work.issues_selected = checkpoint.get("issues_remaining", [])

        self._audit("checkpoint_recovery", 0, detail={
            "found": True,
            "resume_phase": resume_phase,
            "issues_remaining": len(self.work.issues_selected),
        })

        return resume_phase

    def _enter_phase(self, phase: int) -> Action:
        """Transition to a phase with gate enforcement.

        Writes a checkpoint on every transition and logs the gate decision.
        Returns the gate action (PROCEED, SKIP_DISPATCH, or FINISH_CURRENT).

        If transition() raises ShutdownRequired, a gate_check audit event
        is recorded before the exception propagates.
        """
        try:
            action = self.machine.transition(phase)
        except ShutdownRequired as e:
            # Record the gate_check that led to shutdown before propagating
            self._audit("gate_check", phase,
                        tier=e.tier.value, action=e.action.value)
            raise

        # Checkpoint on every transition
        self._write_checkpoint(f"Phase {phase} entry")

        # Audit the gate decision
        tier = self.machine.tier
        self._audit("gate_check", phase, tier=tier.value, action=action.value)

        return action

    def _phase_3_dispatch(self) -> list[str]:
        """Dispatch worker agents with orchestrator-controlled concurrency."""
        tasks = []
        limit = self.config.parallel_coders
        issues = self.work.issues_selected

        if limit != -1:
            issues = issues[:limit]

        for issue_ref in issues:
            task = AgentTask(
                persona=AgentPersona.CODER,
                correlation_id=issue_ref,
                plan_content=self.work.plans.get(issue_ref, ""),
                issue_body="",  # Loaded by caller before run()
                branch="",     # Set by caller
                session_id=self.session_id,
            )
            tasks.append(task)

        if not tasks:
            return []

        task_ids = self.dispatcher.dispatch(tasks)

        self._audit("dispatch", 3, detail={
            "agents_dispatched": len(task_ids),
            "correlation_ids": [t.correlation_id for t in tasks],
        })

        return task_ids

    def _phase_4_collect(self, action: Action) -> list[AgentResult]:
        """Collect results and evaluate with circuit breaker tracking.

        Wires up circuit breaker record_feedback/record_reassign so that
        evaluation cycle limits are enforced per work unit.
        """
        # In a real implementation, this would collect from dispatcher
        # and route through Tester evaluation. For now, we track the
        # circuit breaker and audit trail.
        results = []

        for issue_ref in self.work.issues_selected:
            if not self.breaker.can_dispatch(issue_ref):
                self._audit("circuit_breaker_blocked", 4,
                            correlation_id=issue_ref)
                continue

            # Record a feedback cycle for this evaluation pass.
            # In a full implementation, the Tester result type (FEEDBACK
            # vs BLOCK/ESCALATE) determines which method to call.
            try:
                self.breaker.record_feedback(issue_ref)
            except CircuitBreakerTripped:
                self._audit("circuit_breaker_tripped", 4,
                            correlation_id=issue_ref,
                            detail={"reason": "feedback_cycle_limit"})
                continue

            self._audit("evaluation", 4, correlation_id=issue_ref)

            if action == Action.FINISH_CURRENT:
                break  # Yellow/Orange — only process current

        return results

    def _phase_5_merge(self) -> None:
        """Merge PRs and decide whether to loop."""
        self._audit("merge_start", 5, detail={
            "prs_to_merge": list(self.work.prs_remaining),
        })

        # Loop decision is deterministic
        tier = self.machine.tier
        if tier >= Tier.ORANGE:
            # Consistent with gate_action(5, Orange/Red) → EMERGENCY_STOP
            raise ShutdownRequired(
                tier=tier,
                action=Action.EMERGENCY_STOP,
                gates_passed=self.machine.get_gate_history(),
                signals=self.machine.signals,
            )

        n = self.config.parallel_coders
        if n != -1 and self.machine.signals.issues_completed >= n:
            # Issue cap reached — orderly shutdown via checkpoint
            raise ShutdownRequired(
                tier=tier,
                action=Action.CHECKPOINT,
                gates_passed=self.machine.get_gate_history(),
                signals=self.machine.signals,
            )

    def _handle_shutdown(self, exc: ShutdownRequired) -> None:
        """Write final checkpoint and audit the shutdown."""
        # Determine the target phase from the gate history — the last
        # gate record is the transition that triggered shutdown
        target_phase = (
            exc.gates_passed[-1]["phase"]
            if exc.gates_passed
            else self.machine.phase
        )
        self._write_checkpoint(
            f"Shutdown: tier={exc.tier.value}, action={exc.action.value}",
            context_capacity={
                "tier": exc.tier.value,
                "tool_calls": self.machine.signals.tool_calls,
                "turn_count": self.machine.signals.turns,
                "issues_completed_count": self.machine.signals.issues_completed,
                "trigger": str(exc),
            },
        )
        self._audit("shutdown", self.machine.phase,
                     tier=exc.tier.value, action=exc.action.value,
                     detail={"target_phase": target_phase})

    def _write_checkpoint(
        self,
        current_step: str,
        context_capacity: dict | None = None,
    ) -> Path:
        """Write a checkpoint with current state."""
        branch = self._get_current_branch()
        return self.checkpoints.write(
            session_id=self.session_id,
            branch=branch,
            issues_completed=self.work.issues_completed,
            issues_remaining=self.work.issues_selected,
            prs_created=self.work.prs_created,
            prs_resolved=self.work.prs_resolved,
            prs_remaining=self.work.prs_remaining,
            current_step=current_step,
            pending_work=f"{len(self.work.issues_selected)} issues remaining",
            context_capacity=context_capacity or {
                "tier": self.machine.tier.value,
                "tool_calls": self.machine.signals.tool_calls,
                "turn_count": self.machine.signals.turns,
                "issues_completed_count": self.machine.signals.issues_completed,
            },
            context_gates_passed=self.machine.get_gate_history(),
        )

    def _audit(
        self,
        event_type: str,
        phase: int,
        tier: str | None = None,
        action: str | None = None,
        correlation_id: str | None = None,
        detail: dict | None = None,
    ) -> None:
        """Record an audit event."""
        self.audit.record(AuditEvent(
            event_type=event_type,
            phase=phase,
            session_id=self.session_id,
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
