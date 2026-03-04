"""Agent registry for PM mode topology enforcement.

Tracks spawned agents and validates the PM mode agent topology:
    Project Manager -> DevOps Engineer (background) + N Tech Leads -> M Coders each

When ``use_project_manager`` is enabled, the orchestrator validates that required
agents are registered before allowing phase transitions. In standard mode (PM off),
the registry is a no-op — it accepts registrations but skips topology validation.

Pattern follows circuit_breaker.py: dataclass for per-agent state, class for
registry logic, exception for topology violations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum

from governance.engine.orchestrator.topology_error import TopologyError


class AgentStatus(Enum):
    """Lifecycle status for a registered agent."""

    REGISTERED = "registered"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TopologyWarning:
    """Warning emitted when PM mode topology is incomplete at a phase transition.

    Not an exception — topology issues produce warnings (not hard blocks)
    per the plan requirement: 'Phase 3->4 transition should warn (not block)'.
    """

    def __init__(self, phase: int, missing: list[str], detail: str = ""):
        self.phase = phase
        self.missing = missing
        self.detail = detail

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "missing": self.missing,
            "detail": self.detail,
        }

    def __repr__(self) -> str:
        return (
            f"TopologyWarning(phase={self.phase}, "
            f"missing={self.missing}, detail={self.detail!r})"
        )


# Valid persona names for PM mode topology
PM_TOPOLOGY_PERSONAS = frozenset({
    "project_manager",
    "devops_engineer",
    "tech_lead",
    "coder",
})

# All recognized personas (PM + standard)
ALL_PERSONAS = PM_TOPOLOGY_PERSONAS | frozenset({
    "test_writer",
    "test_evaluator",
    "document_writer",
    "documentation_reviewer",
    "iac_engineer",
})


@dataclass
class RegisteredAgent:
    """State for a single registered agent."""

    persona: str
    task_id: str
    correlation_id: str = ""
    status: str = "registered"  # registered | running | completed | failed
    parent_task_id: str = ""  # For coders: the code_manager task_id
    registered_at: str = ""
    heartbeat_at: str = ""  # ISO-8601 timestamp of last heartbeat

    def __post_init__(self):
        if not self.registered_at:
            self.registered_at = datetime.now(timezone.utc).isoformat()


class AgentRegistry:
    """Tracks spawned agents and validates PM mode topology.

    In PM mode the expected topology is:
        - 1 project_manager (implicit, the main LLM)
        - 1 devops_engineer (background)
        - N tech_leads (parallel dispatch)
        - M coders per tech_lead

    The registry:
        1. Accepts ``register()`` calls to record agent spawns.
        2. Accepts ``update_status()`` calls as agents progress.
        3. Provides ``validate_topology()`` for phase transition checks.
        4. Provides ``validate_topology_hard()`` for hard enforcement.
        5. Provides ``record_heartbeat()`` / ``is_alive()`` for liveness.
        6. Serializes/deserializes for session persistence.

    When PM mode is off, ``validate_topology()`` always returns an empty
    list of warnings — the registry still records agents but imposes no
    constraints.
    """

    def __init__(self) -> None:
        self._agents: dict[str, RegisteredAgent] = {}

    def register(
        self,
        persona: str,
        task_id: str,
        correlation_id: str = "",
        parent_task_id: str = "",
    ) -> RegisteredAgent:
        """Register a new agent.

        Args:
            persona: Agent persona name (e.g. 'devops_engineer', 'tech_lead').
            task_id: Unique task identifier for the agent.
            correlation_id: Optional correlation ID (issue ref, PR ref, etc.).
            parent_task_id: Optional parent task ID for hierarchy tracking.

        Returns:
            The newly created RegisteredAgent.

        Raises:
            ValueError: If task_id is already registered.
        """
        if task_id in self._agents:
            raise ValueError(f"Agent already registered: {task_id}")

        agent = RegisteredAgent(
            persona=persona,
            task_id=task_id,
            correlation_id=correlation_id,
            parent_task_id=parent_task_id,
        )
        self._agents[task_id] = agent
        return agent

    def update_status(self, task_id: str, status: str) -> RegisteredAgent:
        """Update the status of a registered agent.

        Args:
            task_id: The agent's task identifier.
            status: New status (registered/running/completed/failed).

        Returns:
            The updated RegisteredAgent.

        Raises:
            KeyError: If task_id is not registered.
            ValueError: If status is not a valid AgentStatus value.
        """
        if task_id not in self._agents:
            raise KeyError(f"Agent not registered: {task_id}")

        # Validate status value
        valid_statuses = {s.value for s in AgentStatus}
        if status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {sorted(valid_statuses)}"
            )

        self._agents[task_id].status = status
        return self._agents[task_id]

    def get_agent(self, task_id: str) -> RegisteredAgent | None:
        """Get agent by task_id. Returns None if not found."""
        return self._agents.get(task_id)

    def get_agents_by_persona(self, persona: str) -> list[RegisteredAgent]:
        """Get all agents with a given persona."""
        return [a for a in self._agents.values() if a.persona == persona]

    def get_agents_by_status(self, status: str) -> list[RegisteredAgent]:
        """Get all agents with a given status."""
        return [a for a in self._agents.values() if a.status == status]

    @property
    def all_agents(self) -> dict[str, RegisteredAgent]:
        """Read-only view of all registered agents."""
        return dict(self._agents)

    @property
    def agent_count(self) -> int:
        """Total number of registered agents."""
        return len(self._agents)

    def record_heartbeat(self, task_id: str) -> RegisteredAgent:
        """Record a heartbeat for a registered agent.

        Updates the agent's ``heartbeat_at`` timestamp to now (UTC).

        Args:
            task_id: The agent's task identifier.

        Returns:
            The updated RegisteredAgent.

        Raises:
            KeyError: If task_id is not registered.
        """
        if task_id not in self._agents:
            raise KeyError(f"Agent not registered: {task_id}")

        self._agents[task_id].heartbeat_at = datetime.now(timezone.utc).isoformat()
        return self._agents[task_id]

    def is_alive(self, task_id: str, threshold_seconds: int = 300) -> bool:
        """Check whether an agent is alive based on its heartbeat.

        An agent is considered alive if its last heartbeat was within
        ``threshold_seconds`` of now. Agents that have never sent a
        heartbeat (empty ``heartbeat_at``) are considered *not* alive.

        Args:
            task_id: The agent's task identifier.
            threshold_seconds: Maximum age of last heartbeat in seconds
                before the agent is considered stale (default 300 = 5 min).

        Returns:
            True if the agent has a recent heartbeat, False otherwise.

        Raises:
            KeyError: If task_id is not registered.
        """
        if task_id not in self._agents:
            raise KeyError(f"Agent not registered: {task_id}")

        agent = self._agents[task_id]
        if not agent.heartbeat_at:
            return False

        try:
            last = datetime.fromisoformat(agent.heartbeat_at)
            now = datetime.now(timezone.utc)
            elapsed = (now - last).total_seconds()
            return elapsed <= threshold_seconds
        except (ValueError, TypeError):
            return False

    def validate_topology(
        self,
        target_phase: int,
        use_project_manager: bool,
    ) -> list[TopologyWarning]:
        """Validate agent topology for a phase transition.

        Only enforced when ``use_project_manager=True``. In standard mode,
        always returns an empty list.

        PM mode validations by phase transition:
            - Phase 1->2: devops_engineer should be registered
            - Phase 3->4: at least one tech_lead should be registered
            - Phase 3->4: at least one coder should be registered

        Args:
            target_phase: The phase being transitioned to.
            use_project_manager: Whether PM mode is active.

        Returns:
            List of TopologyWarning objects. Empty means topology is valid
            (or PM mode is off).
        """
        if not use_project_manager:
            return []

        warnings: list[TopologyWarning] = []

        if target_phase == 2:
            # Transitioning from phase 1 to 2:
            # DevOps Engineer should have been spawned in phase 1
            devops_agents = self.get_agents_by_persona("devops_engineer")
            if not devops_agents:
                warnings.append(TopologyWarning(
                    phase=target_phase,
                    missing=["devops_engineer"],
                    detail=(
                        "PM mode requires a DevOps Engineer agent for pre-flight. "
                        "No devops_engineer registered before phase 2 entry."
                    ),
                ))

        elif target_phase == 4:
            # Transitioning from phase 3 to 4:
            # Tech Leads and Coders should have been dispatched
            missing: list[str] = []
            detail_parts: list[str] = []

            tl_agents = self.get_agents_by_persona("tech_lead")
            if not tl_agents:
                missing.append("tech_lead")
                detail_parts.append(
                    "PM mode dispatches Tech Leads (not Coders directly). "
                    "No tech_lead registered."
                )

            coder_agents = self.get_agents_by_persona("coder")
            if not coder_agents:
                missing.append("coder")
                detail_parts.append(
                    "No coder agents registered. Tech Leads should spawn Coders."
                )

            if missing:
                warnings.append(TopologyWarning(
                    phase=target_phase,
                    missing=missing,
                    detail=" ".join(detail_parts),
                ))

        return warnings

    def validate_topology_hard(
        self,
        target_phase: int,
        use_project_manager: bool,
    ) -> list[TopologyError]:
        """Hard-enforce PM mode topology -- returns TopologyError list.

        Unlike ``validate_topology()`` which returns advisory warnings,
        this method returns blocking ``TopologyError`` objects. The caller
        should raise or aggregate them to block phase transitions.

        Only enforced when ``use_project_manager=True``. In standard mode,
        always returns an empty list.

        PM mode hard validations:
            - Phase 2 entry: devops_engineer must be registered
            - Phase 4 entry: at least one tech_lead must be registered

        Args:
            target_phase: The phase being transitioned to.
            use_project_manager: Whether PM mode is active.

        Returns:
            List of TopologyError objects. Empty means topology is valid.
        """
        if not use_project_manager:
            return []

        errors: list[TopologyError] = []

        if target_phase == 2:
            devops_agents = self.get_agents_by_persona("devops_engineer")
            if not devops_agents:
                errors.append(TopologyError(
                    phase=target_phase,
                    rule="missing_devops_engineer",
                    detail=(
                        "PM mode requires a DevOps Engineer agent before phase 2 entry. "
                        "Register a devops_engineer agent before advancing to phase 2."
                    ),
                    missing_personas=["devops_engineer"],
                ))

        elif target_phase == 4:
            tl_agents = self.get_agents_by_persona("tech_lead")
            if not tl_agents:
                errors.append(TopologyError(
                    phase=target_phase,
                    rule="missing_tech_lead",
                    detail=(
                        "PM mode requires at least one Tech Lead (tech_lead) "
                        "before phase 4 entry. Register a tech_lead agent "
                        "before advancing to phase 4."
                    ),
                    missing_personas=["tech_lead"],
                ))

        return errors

    def validate_parent_linkage(
        self,
        use_project_manager: bool,
    ) -> list[TopologyError]:
        """Validate that all Coders have ``parent_task_id`` set in PM mode.

        In PM mode, every Coder agent must reference its parent Tech Lead
        via ``parent_task_id``. This ensures the agent hierarchy is auditable.

        In standard mode, returns an empty list (no enforcement).

        Args:
            use_project_manager: Whether PM mode is active.

        Returns:
            List of TopologyError objects, one per Coder with missing linkage.
        """
        if not use_project_manager:
            return []

        errors: list[TopologyError] = []
        coder_agents = self.get_agents_by_persona("coder")
        for coder in coder_agents:
            if not coder.parent_task_id:
                errors.append(TopologyError(
                    phase=0,
                    rule="missing_parent_linkage",
                    detail=(
                        f"Coder agent '{coder.task_id}' has no parent_task_id. "
                        f"In PM mode, every Coder must reference its parent Tech Lead."
                    ),
                    missing_personas=["parent_task_id"],
                ))

        return errors

    def validate_phase_4_coder_coverage(self) -> list[TopologyError]:
        """Validate that every Tech Lead has at least one Coder registered.

        Called at Phase 3->4 transition in PM mode. Ensures no Tech Lead was
        dispatched without spawning any Coders.

        Returns:
            List of TopologyError objects, one per Tech Lead with no Coders.
        """
        errors: list[TopologyError] = []
        tl_agents = self.get_agents_by_persona("tech_lead")
        coder_agents = self.get_agents_by_persona("coder")

        # Build set of parent_task_ids that coders reference
        covered_tls = {c.parent_task_id for c in coder_agents if c.parent_task_id}

        for tl in tl_agents:
            if tl.task_id not in covered_tls:
                errors.append(TopologyError(
                    phase=4,
                    rule="tech_lead_no_coders",
                    detail=(
                        f"Tech Lead '{tl.task_id}' has no Coder agents registered "
                        f"under it. Each Tech Lead must spawn at least one Coder "
                        f"before Phase 4."
                    ),
                    missing_personas=["coder"],
                ))

        return errors

    def to_dict(self) -> dict:
        """Serialize registry state for session persistence."""
        return {
            task_id: asdict(agent)
            for task_id, agent in self._agents.items()
        }

    @classmethod
    def from_dict(cls, data: dict) -> AgentRegistry:
        """Restore registry from persisted session state.

        Args:
            data: Dict of {task_id: agent_dict} from session JSON.

        Returns:
            Restored AgentRegistry instance.
        """
        registry = cls()
        for task_id, agent_data in data.items():
            # Filter to only valid fields for RegisteredAgent
            valid_fields = set(RegisteredAgent.__dataclass_fields__)
            filtered = {k: v for k, v in agent_data.items() if k in valid_fields}
            registry._agents[task_id] = RegisteredAgent(**filtered)
        return registry

    def summary(self) -> dict:
        """Build a summary of registered agents by persona and status."""
        by_persona: dict[str, int] = {}
        by_status: dict[str, int] = {}

        for agent in self._agents.values():
            by_persona[agent.persona] = by_persona.get(agent.persona, 0) + 1
            by_status[agent.status] = by_status.get(agent.status, 0) + 1

        return {
            "total": len(self._agents),
            "by_persona": by_persona,
            "by_status": by_status,
        }
