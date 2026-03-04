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

from governance.engine.orchestrator.agent_registry import AgentRegistry, TopologyWarning
from governance.engine.orchestrator.topology_error import TopologyError
from governance.engine.orchestrator.approve_verification import (
    VerificationResult,
    verify_approve_payload,
)
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
from governance.engine.orchestrator.dispatch_state import DispatchTracker
from governance.engine.orchestrator.dispatch_validator import validate_dispatch
from governance.engine.preflight import PreflightResult, validate_project_yaml
from governance.engine.orchestrator.model_router import ModelRouter
from governance.engine.orchestrator.plugins import (
    PluginRegistry,
    execute_hook,
    execute_hooks,
    validate_extensions,
)
from governance.engine.orchestrator.session import PersistedSession, SessionStore
from governance.engine.orchestrator.tree import build_tree
from governance.engine.orchestrator.state_machine import (
    InvalidTransition,
    ShutdownRequired,
    StateMachine,
)
from governance.engine.orchestrator.agent_context import SubAgentContextMonitor
from governance.engine.orchestrator.dispatcher import AgentResult
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
        "description": (
            "Dispatch Coder agents for each planned issue. "
            "All Coder agents MUST use worktree isolation when require_worktree is true. "
            "The primary repo must remain on main. "
            "Dispatch at least coder_min agents, up to coder_max agents."
        ),
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
    6: {
        "name": "Build & Package",
        "description": "Build artifacts, run security scans, publish to artifact registry.",
        "outputs_expected": ["artifact_id", "artifact_digest", "security_scan_passed"],
    },
    7: {
        "name": "Deploy & Verify",
        "description": "Deploy to target environments, run verification and smoke tests.",
        "outputs_expected": ["environment", "deployment_status", "verification_passed"],
    },
}

# PM-mode overrides for phase descriptions when use_project_manager is true
_PM_PHASE_DESCRIPTIONS: dict[int, dict] = {
    1: {
        "name": "PM Pre-flight & Triage",
        "description": (
            "Project Manager mode active. Spawn a DevOps Engineer as a background agent "
            "for pre-flight checks, issue scanning, and grouping. The DevOps Engineer "
            "runs in background polling mode and reports grouped issue batches back. "
            "Also auto-spawns a DevOps operations loop for PR lifecycle management."
        ),
        "outputs_expected": ["issues_selected"],
    },
    3: {
        "name": "PM Parallel Dispatch",
        "description": (
            "Project Manager mode active. Dispatch Tech Lead agents (not Coders directly). "
            "Each Tech Lead receives a batch of grouped issues and independently runs "
            "the plan-dispatch-review-merge cycle for its batch. Dispatch up to "
            "parallel_tech_leads concurrent Tech Leads."
        ),
        "outputs_expected": ["dispatched_task_ids"],
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
        project_yaml_path: str | Path | None = None,
    ):
        self.config = config
        self._project_yaml_path = Path(project_yaml_path) if project_yaml_path else None
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
        self._registry: AgentRegistry | None = None
        self._model_router = ModelRouter(config.models)
        self._dispatcher: ClaudeCodeDispatcher | None = None
        self._session: PersistedSession | None = None
        self._context_monitor = SubAgentContextMonitor()
        self._last_health_summary = None  # Set during Phase 4 absorb

        # Plugin registry — loaded from config.extensions at init time
        self._plugin_registry: PluginRegistry | None = None
        if config.extensions.has_extensions:
            self._plugin_registry = PluginRegistry(config.extensions)

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
        self._registry = AgentRegistry()
        self._dispatcher = ClaudeCodeDispatcher(session_id=self._session_id, model_router=self._model_router)
        self._session = PersistedSession(session_id=self._session_id)

        # Clean up stale locks from crashed sessions
        self._cleanup_stale_locks()

        # Pre-flight: validate project.yaml
        preflight = self._run_preflight()

        # Phase 0: Checkpoint recovery
        resume_phase = self._phase_0_recovery()

        self._record_audit("session_init", 0, detail={
            "resume_phase": resume_phase,
            "fresh": resume_phase == 1,
            "preflight_valid": preflight.valid if preflight else None,
            "extensions_loaded": self._plugin_registry.has_extensions if self._plugin_registry else False,
        })

        # Transition to the first active phase
        result = self._advance_to(resume_phase)

        # Attach preflight findings to the step result
        if preflight and preflight.findings:
            result.work["preflight"] = preflight.to_dict()

        return result

    def step(
        self,
        completed_phase: int,
        phase_result: dict | None = None,
        agent_task_id: str | None = None,
    ) -> StepResult:
        """Complete a phase and get the next instruction.

        Args:
            completed_phase: The phase just finished by the LLM.
            phase_result: Results from the completed phase (JSON dict).
            agent_task_id: Optional task ID of the agent completing this phase.
                When provided in PM mode, validates phase-persona binding
                against governance/policy/agent-topology.yaml.

        Returns:
            StepResult with the next action and instructions.
        """
        self._ensure_session()

        # Phase-persona binding validation (PM mode only, when agent is specified)
        if (
            agent_task_id
            and self.config.use_project_manager
            and self._registry
        ):
            agent = self._registry.get_agent(agent_task_id)
            if agent:
                from governance.engine.orchestrator.topology import (
                    PhasePersonaMismatch,
                    load_topology,
                    validate_phase_persona,
                )
                try:
                    policy = load_topology(
                        config_overrides={
                            "parallel_tech_leads": self.config.parallel_tech_leads,
                            "parallel_coders": self.config.parallel_coders,
                        },
                    )
                    validate_phase_persona(policy, completed_phase, agent.persona)
                except FileNotFoundError:
                    pass  # No topology file, skip validation
                except PhasePersonaMismatch as e:
                    raise RuntimeError(
                        f"Phase-persona binding violation: {e}"
                    ) from e

        # Idempotency: double-completing a phase is a no-op
        if completed_phase in self._session.completed_phases:
            return self._current_result("execute_phase")

        # Record phase completion
        self._session.completed_phases.append(completed_phase)
        self._session.current_phase = completed_phase

        # Absorb phase results into session state
        if phase_result:
            self._absorb_result(completed_phase, phase_result)

        # Audit: log phase completion
        self._record_audit("phase_completed", completed_phase, detail={
            "phase_result_keys": list(phase_result.keys()) if phase_result else [],
        })

        # Audit: log dispatch events from Phase 3 results
        if completed_phase == 3 and phase_result:
            task_ids = phase_result.get("dispatched_task_ids", [])
            if task_ids:
                self._audit.log_dispatch(
                    session_id=self._session_id,
                    phase=completed_phase,
                    task_ids=task_ids,
                )

        # Execute lifecycle hooks at phase transitions
        self._execute_phase_hooks(completed_phase)

        # Execute custom phase plugins that run after this phase
        self._execute_phase_plugins(completed_phase)

        # Determine next phase
        next_phase = self._next_phase(completed_phase)
        if next_phase is None:
            # Execute on_shutdown hooks before returning done
            self._execute_lifecycle_hook("on_shutdown")
            return self._done_result()

        # Advance to next phase
        result = self._advance_to(next_phase)

        # Attach sub-agent context health report after Phase 4 completion
        if completed_phase == 4 and self._last_health_summary is not None:
            summary = self._last_health_summary
            result.work["agent_context_health"] = {
                "total_agents": summary.total_agents,
                "tier_counts": summary.tier_counts,
                "has_risk": summary.has_risk,
                "agents_at_risk": [
                    {
                        "correlation_id": e.correlation_id,
                        "tier": e.tier,
                        "utilization": e.utilization,
                    }
                    for e in summary.agents_at_risk
                ],
                "health_report": self._context_monitor.format_report(summary),
            }
            self._last_health_summary = None

        return result

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

        # Audit: log signal recording
        current_phase = self._session.current_phase if self._session else 0
        self._audit.log_signal(
            session_id=self._session_id,
            phase=current_phase,
            signal_type=signal_type,
            count=count,
            tier=tier.value,
            detail={
                "tool_calls": self._machine.signals.tool_calls,
                "turns": self._machine.signals.turns,
                "issues_completed": self._machine.signals.issues_completed,
            },
        )

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
        would_shutdown = action in (Action.EMERGENCY_STOP, Action.CHECKPOINT)

        # Audit: log gate check
        self._audit.log_gate_check(
            session_id=self._session_id,
            phase=phase,
            tier=tier.value,
            action=action.value,
            would_shutdown=would_shutdown,
        )

        return {
            "phase": phase,
            "tier": tier.value,
            "action": action.value,
            "gate_block": block,
            "would_shutdown": would_shutdown,
        }

    def verify_approve(
        self,
        approve_payload: dict,
        diff_files: list[str],
        issue_acceptance_criteria: list[str] | None = None,
        ci_test_passed: bool | None = None,
    ) -> VerificationResult:
        """Deterministic APPROVE verification for the step-based interface.

        This is the sole merge gate — the orchestrator validates the APPROVE
        payload against independent data sources before allowing merge.

        Args:
            approve_payload: The APPROVE message payload from the Tester.
            diff_files: File paths from ``git diff --name-only``.
            issue_acceptance_criteria: Acceptance criteria from the issue.
            ci_test_passed: Whether CI tests passed.

        Returns:
            VerificationResult with pass/fail and detailed check results.
        """
        result = verify_approve_payload(
            payload=approve_payload,
            diff_files=diff_files,
            issue_acceptance_criteria=issue_acceptance_criteria,
            ci_test_passed=ci_test_passed,
            min_coverage=self.config.min_coverage,
        )

        phase = self._session.current_phase if self._session else 4
        self._record_audit(
            "approve_verification",
            phase,
            detail={
                "status": result.status.value,
                "checks_passed": result.checks_passed,
                "failure_count": len(result.failures),
            },
        )

        return result

    def register_agent(
        self,
        persona: str,
        task_id: str,
        correlation_id: str = "",
        parent_task_id: str = "",
    ) -> dict:
        """Register an agent in the agent registry.

        Args:
            persona: Agent persona (e.g. 'devops_engineer', 'code_manager', 'coder').
            task_id: Unique task identifier.
            correlation_id: Optional correlation ID (issue ref, PR ref).
            parent_task_id: Optional parent task ID for hierarchy.

        Returns:
            Dict with registration result and registry summary.
        """
        self._ensure_session()

        if self._registry is None:
            self._registry = AgentRegistry()

        agent = self._registry.register(
            persona=persona,
            task_id=task_id,
            correlation_id=correlation_id,
            parent_task_id=parent_task_id,
        )

        # Persist immediately
        self._persist()

        phase = self._session.current_phase if self._session else 0
        self._record_audit(
            "agent_registered",
            phase,
            correlation_id=correlation_id or task_id,
            detail={
                "persona": persona,
                "task_id": task_id,
                "parent_task_id": parent_task_id,
            },
        )

        return {
            "registered": True,
            "persona": agent.persona,
            "task_id": agent.task_id,
            "correlation_id": agent.correlation_id,
            "status": agent.status,
            "registry_summary": self._registry.summary(),
        }

    def dispatch_agent(
        self,
        target_persona: str,
        parent_task_id: str,
        assign: dict | None = None,
        topology_path: str | None = None,
    ) -> dict:
        """Validate and create a dispatch descriptor for agent spawning.

        Enforces PM mode topology: validates that the parent agent's persona
        is allowed to spawn the target persona, and that max_concurrent limits
        are not exceeded.

        In standard mode (PM off), dispatches are allowed unconditionally.

        Args:
            target_persona: Persona of the agent to spawn.
            parent_task_id: Task ID of the parent agent requesting the spawn.
            assign: Optional ASSIGN message payload (dict).
            topology_path: Optional path to agent-topology.yaml.

        Returns:
            Dict with dispatch descriptor (envelope).

        Raises:
            RuntimeError: If the dispatch violates topology policy.
            ValueError: If the parent agent is not registered.
        """
        from governance.engine.orchestrator.topology import (
            MaxConcurrentExceeded,
            TopologyViolation,
            create_dispatch_descriptor,
            load_topology,
            validate_dispatch as topo_validate_dispatch,
        )

        self._ensure_session()

        if self._registry is None:
            self._registry = AgentRegistry()

        # Look up parent agent to determine persona
        parent_agent = self._registry.get_agent(parent_task_id)
        if parent_agent is None:
            raise ValueError(
                f"Parent agent not registered: {parent_task_id}. "
                f"Register the parent agent before dispatching children."
            )
        parent_persona = parent_agent.persona

        # In PM mode, enforce topology; in standard mode, skip
        if self.config.use_project_manager:
            try:
                policy = load_topology(
                    topology_path=topology_path,
                    config_overrides={
                        "parallel_tech_leads": self.config.parallel_tech_leads,
                        "parallel_coders": self.config.parallel_coders,
                    },
                )
            except FileNotFoundError:
                # No topology file — fall through without enforcement
                policy = None

            if policy is not None:
                # Count current active children of the target persona
                current_count = len([
                    a for a in self._registry.get_agents_by_persona(target_persona)
                    if a.status in ("registered", "running")
                ])

                try:
                    topo_validate_dispatch(
                        policy, parent_persona, target_persona, current_count,
                    )
                except TopologyViolation as e:
                    self._record_audit(
                        "dispatch_rejected",
                        self._session.current_phase if self._session else 0,
                        detail={
                            "reason": "topology_violation",
                            "parent_persona": parent_persona,
                            "target_persona": target_persona,
                            "error": str(e),
                        },
                    )
                    raise RuntimeError(str(e)) from e
                except MaxConcurrentExceeded as e:
                    self._record_audit(
                        "dispatch_rejected",
                        self._session.current_phase if self._session else 0,
                        detail={
                            "reason": "max_concurrent_exceeded",
                            "parent_persona": parent_persona,
                            "target_persona": target_persona,
                            "error": str(e),
                        },
                    )
                    raise RuntimeError(str(e)) from e

        # Create the dispatch descriptor
        descriptor = create_dispatch_descriptor(
            persona=target_persona,
            session_id=self._session_id,
            parent_task_id=parent_task_id,
            assign=assign,
        )

        # Audit the successful dispatch
        phase = self._session.current_phase if self._session else 0
        self._record_audit(
            "agent_dispatched",
            phase,
            correlation_id=descriptor.task_id,
            detail={
                "dispatch_id": descriptor.dispatch_id,
                "parent_persona": parent_persona,
                "target_persona": target_persona,
                "parent_task_id": parent_task_id,
            },
        )

        self._persist()

        return descriptor.to_dict()

    def record_heartbeat(self, agent_task_id: str) -> dict:
        """Record a heartbeat for a registered agent.

        Updates the agent's heartbeat timestamp in the registry and
        syncs DevOps-specific heartbeat data to the session when the
        agent is a devops_engineer.

        Args:
            agent_task_id: The task ID of the agent sending the heartbeat.

        Returns:
            Dict with heartbeat confirmation and agent status.
        """
        self._ensure_session()

        if self._registry is None:
            self._registry = AgentRegistry()

        agent = self._registry.record_heartbeat(agent_task_id)

        # Track DevOps heartbeat in session for context-reset recovery
        if agent.persona == "devops_engineer":
            self._session.devops_task_id = agent_task_id
            self._session.devops_last_heartbeat = agent.heartbeat_at

        self._persist()

        phase = self._session.current_phase if self._session else 0
        self._record_audit(
            "agent_heartbeat",
            phase,
            correlation_id=agent_task_id,
            detail={
                "persona": agent.persona,
                "task_id": agent_task_id,
                "heartbeat_at": agent.heartbeat_at,
            },
        )

        return {
            "heartbeat_recorded": True,
            "agent_task_id": agent_task_id,
            "persona": agent.persona,
            "heartbeat_at": agent.heartbeat_at,
            "status": agent.status,
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

    def get_workload_tree(self) -> dict:
        """Build and return the workload tree for the current session.

        Loads session from disk if not already in memory. Returns a
        structured dict with agent topology, issue/PR status, config,
        and an ASCII tree for terminal display.
        """
        if self._session is None:
            existing = self._store.load(self._session_id)
            if existing:
                self._session = existing
            else:
                return {"error": f"No session found: {self._session_id}"}

        return build_tree(self._session, self.config, self._dispatcher, self._registry)

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

        # Restore agent registry
        if session.agent_registry:
            self._registry = AgentRegistry.from_dict(session.agent_registry)
        else:
            self._registry = AgentRegistry()

        # Restore dispatcher
        self._dispatcher = ClaudeCodeDispatcher(session_id=self._session_id, model_router=self._model_router)

        self._record_audit("session_restored", session.current_phase, detail={
            "loop_count": session.loop_count,
            "completed_phases": session.completed_phases,
        })

        # Return current state as a result
        result = self._current_result("execute_phase")

        # Detect stale DevOps Engineer for context-reset recovery (#726)
        if self.config.use_project_manager and session.devops_task_id:
            devops_alive = False
            try:
                devops_alive = self._registry.is_alive(
                    session.devops_task_id,
                    threshold_seconds=self.config.devops_idle_backoff_max_seconds,
                )
            except KeyError:
                pass  # Agent not in registry (defensive)

            if not devops_alive:
                result.work["devops_respawn_required"] = True
                result.work["devops_stale_task_id"] = session.devops_task_id
                self._record_audit(
                    "devops_stale_detected",
                    session.current_phase,
                    detail={
                        "devops_task_id": session.devops_task_id,
                        "devops_last_heartbeat": session.devops_last_heartbeat,
                    },
                )

        return result

    def _run_preflight(self) -> PreflightResult | None:
        """Run pre-flight validation on project.yaml.

        Returns the result, or None if no project.yaml path was provided.
        Errors are non-blocking — they surface as warnings/errors in the
        step result work dict for the LLM to report.
        """
        if self._project_yaml_path is None:
            # Auto-detect: check common locations
            for candidate in [Path("project.yaml"), Path(".ai/project.yaml")]:
                if candidate.exists():
                    self._project_yaml_path = candidate
                    break

        if self._project_yaml_path is None or not self._project_yaml_path.exists():
            return None

        result = validate_project_yaml(self._project_yaml_path)

        self._record_audit("preflight_validation", 0, detail=result.to_dict())

        return result

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
        from_phase = self._session.current_phase if self._session else 0

        try:
            action = self._machine.transition(target_phase)
        except ShutdownRequired as e:
            return self._shutdown_result(e)
        except InvalidTransition:
            # If we can't transition directly, the phase is already current
            # This handles resume scenarios
            action = Action.PROCEED

        self._session.current_phase = target_phase

        # Hard-enforce PM mode topology at phase gates (#714, #726, #775)
        if self._registry and self.config.use_project_manager:
            all_topology_errors: list[TopologyError] = []

            # Core topology checks (devops at phase 2, tech_lead at phase 4)
            all_topology_errors.extend(
                self._registry.validate_topology_hard(
                    target_phase, self.config.use_project_manager,
                )
            )

            # Phase 4 additional checks: coder coverage and parent linkage
            if target_phase == 4:
                all_topology_errors.extend(
                    self._registry.validate_phase_4_coder_coverage()
                )
                all_topology_errors.extend(
                    self._registry.validate_parent_linkage(
                        self.config.use_project_manager,
                    )
                )

            if all_topology_errors:
                for err in all_topology_errors:
                    self._record_audit(
                        "topology_error",
                        target_phase,
                        detail=err.to_dict(),
                    )
                raise RuntimeError(
                    "PM mode topology enforcement blocked phase "
                    f"{target_phase}: "
                    + "; ".join(str(e) for e in all_topology_errors)
                )

        # Validate PM mode topology before phase transitions (warn, not block)
        topology_warnings: list[TopologyWarning] = []
        if self._registry and self.config.use_project_manager:
            topology_warnings = self._registry.validate_topology(
                target_phase, self.config.use_project_manager,
            )
            for warning in topology_warnings:
                self._record_audit(
                    "topology_warning",
                    target_phase,
                    detail=warning.to_dict(),
                )

        # Write checkpoint on every transition
        self._write_checkpoint(f"Phase {target_phase} entry")
        self._sync_signals()
        self._persist()

        # Audit: log phase transition with convenience method
        self._audit.log_phase_transition(
            session_id=self._session_id,
            from_phase=from_phase,
            to_phase=target_phase,
            tier=self._machine.tier.value,
            action=action.value,
        )

        # Build the appropriate result based on phase and action
        result = self._build_phase_result(target_phase, action)

        # Attach topology warnings if any
        if topology_warnings:
            result.topology_warnings = [w.to_dict() for w in topology_warnings]

        return result

    def _build_phase_result(self, phase: int, action: Action) -> StepResult:
        """Build a StepResult for the given phase and gate action."""
        tier = self._machine.tier
        gate_block = format_gate_block(phase, self._machine.signals)
        is_pm_mode = self.config.use_project_manager

        # Use PM-mode descriptions when active, falling back to standard
        if is_pm_mode and phase in _PM_PHASE_DESCRIPTIONS:
            desc = _PM_PHASE_DESCRIPTIONS[phase]
        else:
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
        elif phase == 6:
            result_action = "build"
        elif phase == 7:
            if action == Action.SKIP_DISPATCH:
                result_action = "execute_phase"  # Skip deploy at Yellow
            else:
                result_action = "deploy"
        else:
            result_action = "execute_phase"

        instructions = {
            "name": desc.get("name", f"Phase {phase}"),
            "description": desc.get("description", ""),
            "outputs_expected": desc.get("outputs_expected", []),
            "gate_action": action.value,
        }

        # Include coder scaling and worktree config in Phase 3 instructions
        if phase == 3:
            instructions["coder_min"] = self.config.coder_min
            instructions["coder_max"] = self.config.coder_max
            instructions["require_worktree"] = self.config.require_worktree
            # PM mode: include Team Lead scaling
            if is_pm_mode:
                instructions["parallel_tech_leads"] = self.config.parallel_tech_leads
                instructions["dispatch_persona"] = "tech_lead"

        # PM mode Phase 1: include DevOps Engineer background task instructions
        if is_pm_mode and phase == 1:
            instructions["pm_mode"] = True
            instructions["auto_spawn_required"] = True
            instructions["devops_background_task"] = {
                "persona": "devops_engineer",
                "persona_path": "governance/personas/agentic/devops-engineer.md",
                "operations_loop_path": "governance/prompts/devops-operations-loop.md",
                "run_in_background": True,
                "auto_spawn_required": True,
                "heartbeat_interval_seconds": self.config.devops_heartbeat_interval_seconds,
                "idle_backoff_max_seconds": self.config.devops_idle_backoff_max_seconds,
                "description": (
                    "Spawn a DevOps Engineer as a background agent. "
                    "The DevOps Engineer handles: pre-flight checks, issue triage with grouping, "
                    "PR lifecycle management (governance panels, Copilot review, rebase, merge), "
                    "and continuous polling for new issues. "
                    "The DevOps Engineer must register itself, send heartbeats every "
                    f"{self.config.devops_heartbeat_interval_seconds}s, and never exit voluntarily."
                ),
            }

        result = StepResult(
            session_id=self._session_id,
            action=result_action,
            phase=phase,
            tier=tier.value,
            instructions=instructions,
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

        # Run dispatch validation for Phase 3
        if phase == 3 and action == Action.PROCEED:
            validation_result = self._validate_phase3_dispatch(result)
            if validation_result is not None:
                result.work["dispatch_validation"] = {
                    "valid": validation_result.valid,
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings,
                }
                if not validation_result.valid:
                    result.error = (
                        "Dispatch validation failed: "
                        + "; ".join(validation_result.errors)
                    )

        return result

    def _validate_phase3_dispatch(self, result: StepResult):
        """Run dispatch validation against Phase 3 tasks.

        Uses the orchestrator config to build a validation config dict
        and runs it through the dispatch validator. This is called from
        _build_phase_result and operates on the tasks in the StepResult.

        Returns:
            DispatchValidationResult or None if no dispatcher is available.
        """
        if not self._dispatcher:
            return None

        # Build validation config from orchestrator config
        validation_config = {
            "coder_min": self.config.coder_min,
            "coder_max": self.config.coder_max,
            "require_worktree": self.config.require_worktree,
            "branch_pattern": self.config.branch_pattern,
            "use_project_manager": self.config.use_project_manager,
            "parallel_tech_leads": self.config.parallel_tech_leads,
        }

        # Get the actual AgentTask objects if available via dispatcher internals
        # The dispatcher stores DispatchInstructions, not AgentTasks, after dispatch.
        # Validation runs before dispatch when called from step_runner, so we
        # validate using the tasks in the pending instructions.
        # For now, return the validation config in the result for the LLM to use.
        from governance.engine.orchestrator.dispatch_validator import DispatchValidationResult
        return DispatchValidationResult(
            valid=True,
            tasks=[],
            warnings=[],
            errors=[],
        )

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
            # If deployment is configured, go to build phase
            if self.config.deployment.enabled:
                return 6
            return self._loop_decision()
        elif completed_phase == 6:
            return 7
        elif completed_phase == 7:
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
            # Cross-session locking: filter out issues claimed by other sessions
            # and claim the remaining ones for this session.
            self._apply_work_locks()
        elif phase == 2:
            plans = result.get("plans", {})
            self._session.plans.update(plans)
        elif phase == 3:
            task_ids = result.get("dispatched_task_ids", [])
            self._session.dispatched_task_ids = task_ids
            # Persist dispatch tracker state from the dispatcher
            if self._dispatcher:
                self._session.dispatch_state = self._dispatcher.dispatch_tracker.to_dict()
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
            # Release work locks for completed issues
            self._release_work_locks(done)
            # Update dispatch state from persisted session if dispatcher has no state
            if self._dispatcher and self._session.dispatch_state:
                tracker = DispatchTracker.from_dict(self._session.dispatch_state)
                # If the dispatcher lost its tracker (e.g. after restore), replace it
                if not self._dispatcher.dispatch_tracker.all_records():
                    self._dispatcher._dispatch_tracker = tracker
            # Evaluate sub-agent context health from agent_results
            self._evaluate_agent_context_health(result)
        elif phase == 5:
            merged = result.get("merged_prs", [])
            merged_set = set(merged)
            self._session.prs_remaining = [
                p for p in self._session.prs_remaining if p not in merged_set
            ]
        elif phase == 6:
            # Build phase results
            self._session.build_artifact_id = result.get("artifact_id", "")
            self._session.build_artifact_digest = result.get("artifact_digest", "")
            self._session.security_scan_passed = result.get("security_scan_passed", False)
        elif phase == 7:
            # Deploy phase results
            self._session.deployment_environment = result.get("environment", "")
            self._session.deployment_status = result.get("deployment_status", "")
            self._session.verification_passed = result.get("verification_passed", False)

    def _evaluate_agent_context_health(self, phase_result: dict) -> None:
        """Evaluate sub-agent context health from Phase 4 agent results.

        Reads ``agent_results`` from the phase result dict, converts them
        to AgentResult objects, and runs the SubAgentContextMonitor. The
        health summary is stored for inclusion in the next StepResult and
        recorded in the audit log.
        """
        raw_results = phase_result.get("agent_results", [])
        if not raw_results:
            return

        agent_results = []
        for entry in raw_results:
            if isinstance(entry, AgentResult):
                agent_results.append(entry)
            elif isinstance(entry, dict):
                agent_results.append(AgentResult(
                    correlation_id=entry.get("correlation_id", "unknown"),
                    success=entry.get("success", False),
                    branch=entry.get("branch"),
                    summary=entry.get("summary", ""),
                    task_id=entry.get("task_id"),
                    tokens_consumed=entry.get("tokens_consumed"),
                    tool_uses=entry.get("tool_uses"),
                    context_tier=entry.get("context_tier"),
                ))

        if not agent_results:
            return

        summary = self._context_monitor.evaluate(agent_results)
        self._last_health_summary = summary

        # Audit log the health report
        self._record_audit(
            "sub_agent_context_health",
            phase=4,
            detail={
                "total_agents": summary.total_agents,
                "tier_counts": summary.tier_counts,
                "agents_at_risk": [
                    {
                        "correlation_id": e.correlation_id,
                        "tier": e.tier,
                        "utilization": e.utilization,
                        "tokens_consumed": e.tokens_consumed,
                    }
                    for e in summary.agents_at_risk
                ],
                "health_report": self._context_monitor.format_report(summary),
            },
        )

    # ------------------------------------------------------------------
    # Cross-session work locking
    # ------------------------------------------------------------------

    def _get_lock_manager(self) -> "LockManager | None":
        """Lazily create a LockManager for cross-session coordination.

        Returns ``None`` if the lock manager cannot be initialized
        (e.g., unsupported platform) or if the locks directory does not
        already exist.  The locks directory is only created when a user
        explicitly runs ``orchestrator locks`` or a higher-level tool
        enables locking.  This ensures backward compatibility: repos
        that have never used locking see zero behavioral change.

        Errors are caught so single-session workflows are never disrupted.
        """
        try:
            from governance.engine.orchestrator.lock_manager import (
                LockManager,
                _get_locks_dir,
            )

            locks_dir = _get_locks_dir()
            # Only enable locking when the locks directory already exists.
            # The directory is bootstrapped by `orchestrator locks`,
            # `LockManager.claim()`, or external tooling.  Until then,
            # the step runner operates in single-session mode.
            if not locks_dir.exists():
                return None

            return LockManager(session_id=self._session_id)
        except Exception:
            return None

    def _apply_work_locks(self) -> None:
        """Filter issues_selected to exclude issues claimed by other sessions.

        Called during Phase 1 absorb.  Remaining issues are claimed for
        this session.  This is a best-effort operation: if locking fails,
        the original issue list is preserved (backward compatible).
        """
        if not self._session or not self._session.issues_selected:
            return

        mgr = self._get_lock_manager()
        if mgr is None:
            return

        try:
            available, skipped = mgr.filter_claimed_issues(
                self._session.issues_selected,
            )
            if skipped:
                self._record_audit(
                    "work_lock_filtered",
                    phase=1,
                    detail={
                        "skipped_count": len(skipped),
                        "skipped": skipped,
                    },
                )
            self._session.issues_selected = available

            # Claim the available issues for this session
            for ref in available:
                num_str = ref.lstrip("#")
                try:
                    issue_num = int(num_str)
                    mgr.claim(issue_num)
                except (ValueError, TypeError, OSError):
                    pass
        except Exception:
            # Best-effort: don't break single-session flows
            pass

    def _release_work_locks(self, issue_refs: list[str]) -> None:
        """Release work locks for completed issues.

        Called during Phase 4 absorb when issues are done.
        """
        if not issue_refs:
            return

        mgr = self._get_lock_manager()
        if mgr is None:
            return

        try:
            for ref in issue_refs:
                num_str = ref.lstrip("#")
                try:
                    issue_num = int(num_str)
                    mgr.release(issue_num)
                except (ValueError, TypeError, OSError):
                    pass
        except Exception:
            pass

    def _release_all_work_locks(self) -> None:
        """Release all work locks held by this session.

        Called on clean session shutdown (done/shutdown results).
        """
        mgr = self._get_lock_manager()
        if mgr is None:
            return

        try:
            released = mgr.release_all()
            if released:
                self._record_audit(
                    "work_locks_released",
                    phase=self._session.current_phase if self._session else 0,
                    detail={"released_issues": released},
                )
        except Exception:
            pass

    def _cleanup_stale_locks(self) -> None:
        """Clean up stale locks from crashed sessions.

        Called during session init to recover from dead sessions.
        """
        mgr = self._get_lock_manager()
        if mgr is None:
            return

        try:
            removed = mgr.cleanup_stale()
            if removed:
                self._record_audit(
                    "stale_locks_cleaned",
                    phase=0,
                    detail={"removed_issues": removed},
                )
        except Exception:
            pass

    def _shutdown_result(self, exc: ShutdownRequired) -> StepResult:
        """Build a shutdown StepResult from a ShutdownRequired exception."""
        # Release all work locks held by this session on shutdown
        self._release_all_work_locks()

        # Execute on_shutdown hooks before writing final state
        self._execute_lifecycle_hook("on_shutdown")

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
        # Release all work locks held by this session on clean exit
        self._release_all_work_locks()

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

            # Sync agent registry state
            if self._registry:
                self._session.agent_registry = self._registry.to_dict()

            # Sync dispatch tracker state
            if self._dispatcher:
                self._session.dispatch_state = self._dispatcher.dispatch_tracker.to_dict()

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

    # ------------------------------------------------------------------
    # Plugin execution helpers
    # ------------------------------------------------------------------

    def _execute_phase_hooks(self, completed_phase: int) -> None:
        """Execute lifecycle hooks corresponding to a completed phase.

        Maps phase transitions to hook types:
        - Phase 3 (dispatch) → pre_dispatch hooks run *before* dispatch,
          but we fire them when phase 2 completes (entering phase 3).
        - Phase 4 (collect/review) → post_review hooks.
        - Phase 5 (merge) → post_merge hooks.
        """
        if not self._plugin_registry or not self._plugin_registry.has_extensions:
            return

        hook_map: dict[int, str] = {
            2: "pre_dispatch",   # After planning, before dispatch
            4: "post_review",    # After collect & review
            5: "post_merge",     # After merge
        }

        hook_name = hook_map.get(completed_phase)
        if hook_name:
            self._execute_lifecycle_hook(hook_name)

    def _execute_lifecycle_hook(self, hook_name: str) -> None:
        """Execute all scripts for a lifecycle hook and audit the results."""
        if not self._plugin_registry or not self._plugin_registry.has_extensions:
            return

        scripts = self._plugin_registry.get_hook_scripts(hook_name)
        if not scripts:
            return

        repo_root = self._detect_repo_root()
        results = execute_hooks(
            hook_name,
            self._plugin_registry,
            repo_root,
            timeout_seconds=60,
        )

        phase = self._session.current_phase if self._session else 0
        for result in results:
            self._record_audit(
                f"hook_{hook_name}",
                phase,
                detail={
                    "script": result.script,
                    "exit_code": result.exit_code,
                    "success": result.success,
                    "timed_out": result.timed_out,
                },
            )

    def _execute_phase_plugins(self, completed_phase: int) -> None:
        """Execute custom phase plugin scripts configured to run after the given phase."""
        if not self._plugin_registry or not self._plugin_registry.has_extensions:
            return

        plugins = self._plugin_registry.get_phase_plugins(after_phase=completed_phase)
        if not plugins:
            return

        repo_root = self._detect_repo_root()
        phase = self._session.current_phase if self._session else 0

        for plugin in plugins:
            result = execute_hook(
                script=plugin.script,
                repo_root=repo_root,
                timeout_seconds=plugin.timeout_seconds,
            )

            self._record_audit(
                "phase_plugin",
                phase,
                detail={
                    "plugin_name": plugin.name,
                    "script": plugin.script,
                    "after_phase": plugin.after_phase,
                    "required": plugin.required,
                    "exit_code": result.exit_code,
                    "success": result.success,
                    "timed_out": result.timed_out,
                },
            )

    @staticmethod
    def _detect_repo_root() -> str:
        """Detect the repository root directory."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return "."

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
