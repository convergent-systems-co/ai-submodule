"""Agent topology policy loader and validator.

Loads the spawn DAG from governance/policy/agent-topology.yaml and validates
parent->child agent spawn relationships. Used by `orchestrator dispatch` to
enforce PM mode topology at spawn time.

When PM mode is off, all validation passes unconditionally.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Default topology policy path (relative to repo root)
_DEFAULT_TOPOLOGY_PATH = "governance/policy/agent-topology.yaml"


@dataclass(frozen=True)
class TopologyRule:
    """Spawn rules for a single persona."""

    persona: str
    can_spawn: list[str] = field(default_factory=list)
    max_concurrent: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class PhaseBinding:
    """Maps a phase number to the persona that must execute it."""

    phase: int
    persona: str


@dataclass
class TopologyPolicy:
    """Loaded topology policy with spawn rules and phase bindings."""

    rules: dict[str, TopologyRule] = field(default_factory=dict)
    phase_bindings: dict[int, str] = field(default_factory=dict)

    def can_spawn(self, parent_persona: str, child_persona: str) -> bool:
        """Check if parent persona is allowed to spawn child persona.

        Returns True if the spawn is allowed, False otherwise.
        If the parent persona has no rules defined, spawning is denied.
        """
        rule = self.rules.get(parent_persona)
        if rule is None:
            return False
        return child_persona in rule.can_spawn

    def get_max_concurrent(self, parent_persona: str, child_persona: str) -> int | None:
        """Get the max concurrent limit for a parent spawning a child persona.

        Returns None if no limit is configured (unlimited).
        """
        rule = self.rules.get(parent_persona)
        if rule is None:
            return None
        return rule.max_concurrent.get(child_persona)

    def get_allowed_children(self, parent_persona: str) -> list[str]:
        """Return the list of personas that parent_persona can spawn."""
        rule = self.rules.get(parent_persona)
        if rule is None:
            return []
        return list(rule.can_spawn)

    def get_phase_executor(self, phase: int) -> str | None:
        """Return the persona that must execute a given phase, or None if unbound."""
        return self.phase_bindings.get(phase)


def load_topology(
    topology_path: str | Path | None = None,
    config_overrides: dict | None = None,
) -> TopologyPolicy:
    """Load topology policy from YAML file.

    Args:
        topology_path: Path to agent-topology.yaml. If None, uses default.
        config_overrides: Optional dict with runtime overrides for max_concurrent
            values. Keys: 'parallel_tech_leads', 'parallel_coders'.

    Returns:
        Loaded TopologyPolicy.

    Raises:
        FileNotFoundError: If the topology file does not exist.
        ValueError: If the topology file is malformed.
    """
    if topology_path is None:
        topology_path = Path(_DEFAULT_TOPOLOGY_PATH)
    else:
        topology_path = Path(topology_path)

    if not topology_path.exists():
        raise FileNotFoundError(f"Topology policy not found: {topology_path}")

    with open(topology_path) as f:
        data = yaml.safe_load(f) or {}

    topology_data = data.get("topology", {})
    if not topology_data:
        raise ValueError(f"No 'topology' section in {topology_path}")

    rules: dict[str, TopologyRule] = {}
    for persona_name, rule_data in topology_data.items():
        if not isinstance(rule_data, dict):
            continue
        can_spawn = rule_data.get("can_spawn", []) or []
        max_concurrent = rule_data.get("max_concurrent", {}) or {}
        rules[persona_name] = TopologyRule(
            persona=persona_name,
            can_spawn=list(can_spawn),
            max_concurrent=dict(max_concurrent),
        )

    # Apply config overrides for max_concurrent
    if config_overrides:
        parallel_tl = config_overrides.get("parallel_tech_leads")
        parallel_coders = config_overrides.get("parallel_coders")

        if parallel_tl is not None and "project_manager" in rules:
            rule = rules["project_manager"]
            updated_mc = dict(rule.max_concurrent)
            updated_mc["tech_lead"] = parallel_tl
            rules["project_manager"] = TopologyRule(
                persona=rule.persona,
                can_spawn=rule.can_spawn,
                max_concurrent=updated_mc,
            )

        if parallel_coders is not None and "tech_lead" in rules:
            rule = rules["tech_lead"]
            updated_mc = dict(rule.max_concurrent)
            updated_mc["coder"] = parallel_coders
            rules["tech_lead"] = TopologyRule(
                persona=rule.persona,
                can_spawn=rule.can_spawn,
                max_concurrent=updated_mc,
            )

    # Load phase bindings
    bindings_data = data.get("phase_bindings", {}) or {}
    phase_bindings: dict[int, str] = {}
    for phase_str, persona in bindings_data.items():
        try:
            phase_bindings[int(phase_str)] = str(persona)
        except (ValueError, TypeError):
            continue

    return TopologyPolicy(rules=rules, phase_bindings=phase_bindings)


@dataclass
class DispatchDescriptor:
    """Structured envelope returned by `orchestrator dispatch`.

    Contains all information needed to spawn an agent through the transport layer.
    """

    dispatch_id: str
    persona: str
    task_id: str
    session_id: str
    parent_task_id: str
    assign: dict = field(default_factory=dict)
    self_register_required: bool = True

    def to_dict(self) -> dict:
        return {
            "dispatch_id": self.dispatch_id,
            "persona": self.persona,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "parent_task_id": self.parent_task_id,
            "assign": self.assign,
            "self_register_required": self.self_register_required,
        }


class TopologyViolation(Exception):
    """Raised when a dispatch violates the topology policy."""

    def __init__(self, parent_persona: str, child_persona: str, detail: str = ""):
        self.parent_persona = parent_persona
        self.child_persona = child_persona
        self.detail = detail
        allowed = detail or f"Check agent-topology.yaml for allowed spawns."
        super().__init__(
            f"{parent_persona} cannot spawn {child_persona}. {allowed}"
        )


class MaxConcurrentExceeded(Exception):
    """Raised when a dispatch would exceed the max_concurrent limit."""

    def __init__(self, parent_persona: str, child_persona: str, limit: int, current: int):
        self.parent_persona = parent_persona
        self.child_persona = child_persona
        self.limit = limit
        self.current = current
        super().__init__(
            f"{parent_persona} cannot spawn another {child_persona}: "
            f"limit is {limit}, currently {current} active."
        )


class PhasePersonaMismatch(Exception):
    """Raised when the wrong persona tries to complete a phase."""

    def __init__(self, phase: int, expected_persona: str, actual_persona: str):
        self.phase = phase
        self.expected_persona = expected_persona
        self.actual_persona = actual_persona
        super().__init__(
            f"Phase {phase} must be completed by {expected_persona}, "
            f"not {actual_persona}."
        )


def validate_dispatch(
    policy: TopologyPolicy,
    parent_persona: str,
    child_persona: str,
    current_child_count: int = 0,
) -> None:
    """Validate a dispatch against the topology policy.

    Args:
        policy: Loaded topology policy.
        parent_persona: Persona of the parent agent requesting the spawn.
        child_persona: Persona of the child agent to spawn.
        current_child_count: Current number of active agents with child_persona
            spawned by this parent persona.

    Raises:
        TopologyViolation: If the spawn is not allowed.
        MaxConcurrentExceeded: If the max_concurrent limit would be exceeded.
    """
    if not policy.can_spawn(parent_persona, child_persona):
        allowed = policy.get_allowed_children(parent_persona)
        detail = f"Valid targets: {allowed}" if allowed else "This persona cannot spawn any agents."
        raise TopologyViolation(parent_persona, child_persona, detail)

    limit = policy.get_max_concurrent(parent_persona, child_persona)
    if limit is not None and current_child_count >= limit:
        raise MaxConcurrentExceeded(parent_persona, child_persona, limit, current_child_count)


def validate_phase_persona(
    policy: TopologyPolicy,
    phase: int,
    agent_persona: str,
) -> None:
    """Validate that the right persona is completing a phase.

    Args:
        policy: Loaded topology policy.
        phase: Phase number being completed.
        agent_persona: Persona of the agent completing the phase.

    Raises:
        PhasePersonaMismatch: If the persona doesn't match the phase binding.
    """
    expected = policy.get_phase_executor(phase)
    if expected is not None and agent_persona != expected:
        raise PhasePersonaMismatch(phase, expected, agent_persona)


def create_dispatch_descriptor(
    persona: str,
    session_id: str,
    parent_task_id: str,
    assign: dict | None = None,
) -> DispatchDescriptor:
    """Create a new dispatch descriptor (envelope) for agent spawning.

    Args:
        persona: Target persona to spawn.
        session_id: Current orchestrator session ID.
        parent_task_id: Task ID of the parent agent.
        assign: Optional ASSIGN message payload.

    Returns:
        DispatchDescriptor with a generated dispatch_id and task_id.
    """
    dispatch_id = f"dispatch-{uuid.uuid4().hex[:8]}"
    task_id = f"{persona}-{uuid.uuid4().hex[:6]}"

    return DispatchDescriptor(
        dispatch_id=dispatch_id,
        persona=persona,
        task_id=task_id,
        session_id=session_id,
        parent_task_id=parent_task_id,
        assign=assign or {},
        self_register_required=True,
    )
