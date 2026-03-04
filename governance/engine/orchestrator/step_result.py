"""Structured contract between the orchestrator CLI and the LLM.

StepResult is the JSON response the CLI emits after every command.
The LLM parses it, follows the action field, and calls back when done.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class DispatchInstruction:
    """One agent task the LLM should translate into a Task tool call."""

    task_id: str
    correlation_id: str
    persona: str
    persona_path: str
    plan_path: str
    branch_name: str
    issue_ref: str
    issue_body: str
    constraints: dict = field(default_factory=dict)
    model: str = ""  # Model directive — which model to use for this task
    require_worktree: bool = True  # Whether this task requires worktree isolation


@dataclass
class StepResult:
    """The structured JSON response from every CLI invocation.

    Fields:
        session_id: Current session identifier.
        action: What the LLM should do next. One of:
            - execute_phase: Run the phase described in instructions.
            - dispatch: Spawn agents per the tasks list.
            - collect: Wait for dispatched agents and feed results back.
            - merge: Execute merge operations per instructions.
            - loop: Loop back — call step to advance.
            - shutdown: Write checkpoint and exit cleanly.
            - done: All work complete — session finished.
        phase: Current pipeline phase (0-5).
        tier: Current capacity tier (green/yellow/orange/red).
        instructions: Phase-specific guidance for the LLM.
        tasks: Dispatch instructions for Phase 3 (empty otherwise).
        gate_block: Formatted context gate text for observability.
        signals: Current signal counters.
        work: Work state summary.
        shutdown_info: Present only when action is shutdown.
        error: Present only on errors.
    """

    session_id: str = ""
    action: str = ""  # execute_phase|dispatch|collect|merge|loop|shutdown|done
    phase: int = 0
    tier: str = "green"
    instructions: dict = field(default_factory=dict)
    tasks: list[dict] = field(default_factory=list)
    gate_block: str = ""
    signals: dict = field(default_factory=dict)
    work: dict = field(default_factory=dict)
    shutdown_info: dict = field(default_factory=dict)
    error: str = ""
    loop_count: int = 0
    topology_warnings: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict, omitting empty optional fields."""
        d = asdict(self)
        # Strip empty optional fields for cleaner JSON output
        for key in ("instructions", "tasks", "gate_block", "shutdown_info", "error", "topology_warnings"):
            if not d.get(key):
                del d[key]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> StepResult:
        """Deserialize from a dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
