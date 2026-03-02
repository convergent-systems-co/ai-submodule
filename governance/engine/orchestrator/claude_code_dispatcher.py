"""Claude Code dispatcher — generates structured dispatch instructions.

Unlike platform-specific dispatchers that make actual API calls, this
dispatcher generates instruction dicts that the LLM translates into
Claude Code Task tool calls. Python can't invoke the Task tool directly.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict

from governance.engine.orchestrator.dispatcher import (
    AgentPersona,
    AgentResult,
    AgentTask,
    Dispatcher,
)
from governance.engine.orchestrator.step_result import DispatchInstruction

# Persona → relative path from repo root
_PERSONA_PATHS: dict[AgentPersona, str] = {
    AgentPersona.DEVOPS_ENGINEER: "governance/personas/agentic/devops-engineer.md",
    AgentPersona.CODE_MANAGER: "governance/personas/agentic/code-manager.md",
    AgentPersona.CODER: "governance/personas/agentic/coder.md",
    AgentPersona.IAC_ENGINEER: "governance/personas/agentic/iac-engineer.md",
    AgentPersona.TESTER: "governance/personas/agentic/tester.md",
    AgentPersona.PROJECT_MANAGER: "governance/personas/agentic/project-manager.md",
}


class ClaudeCodeDispatcher(Dispatcher):
    """Generates structured dispatch instructions for the LLM.

    The LLM reads these instructions and translates each into a
    Task tool call with worktree isolation.
    """

    def __init__(self, session_id: str = ""):
        self._session_id = session_id
        self._instructions: dict[str, DispatchInstruction] = {}
        self._results: dict[str, AgentResult] = {}
        self._task_ids: list[str] = []

    def dispatch(self, tasks: list[AgentTask]) -> list[str]:
        """Build dispatch instructions from agent tasks.

        Does not actually spawn agents — stores instructions that
        get_instructions() returns for the LLM to execute.
        """
        task_ids = []
        for task in tasks:
            task_id = f"cc-{uuid.uuid4().hex[:8]}"
            task_ids.append(task_id)

            persona_path = _PERSONA_PATHS.get(task.persona, "")
            instruction = DispatchInstruction(
                task_id=task_id,
                correlation_id=task.correlation_id,
                persona=task.persona.value,
                persona_path=persona_path,
                plan_path=f".governance/plans/{task.correlation_id}.md",
                branch_name=task.branch,
                issue_ref=task.correlation_id,
                issue_body=task.issue_body,
                constraints=task.constraints,
            )
            self._instructions[task_id] = instruction

        self._task_ids.extend(task_ids)
        return task_ids

    def collect(self, task_ids: list[str], timeout_seconds: int = 600) -> list[AgentResult]:
        """Return recorded results for the given task IDs.

        The LLM calls record_result() as agents complete. This method
        returns whatever results have been recorded.
        """
        results = []
        for tid in task_ids:
            if tid in self._results:
                results.append(self._results[tid])
            else:
                # Not yet reported — mark as pending
                instruction = self._instructions.get(tid)
                correlation_id = instruction.correlation_id if instruction else tid
                results.append(AgentResult(
                    correlation_id=correlation_id,
                    success=False,
                    error="pending",
                    task_id=tid,
                ))
        return results

    def cancel(self, task_ids: list[str]) -> None:
        """No-op — the LLM manages agent lifecycle."""

    def get_instructions(self) -> list[dict]:
        """Return dispatch instructions as dicts for StepResult.tasks."""
        return [asdict(inst) for inst in self._instructions.values()]

    def get_pending_instructions(self) -> list[dict]:
        """Return only instructions that don't have results yet."""
        return [
            asdict(inst)
            for tid, inst in self._instructions.items()
            if tid not in self._results
        ]

    def record_result(self, task_id: str, result: AgentResult) -> None:
        """Record a result from the LLM after an agent completes."""
        self._results[task_id] = result

    @property
    def all_instructions(self) -> dict[str, DispatchInstruction]:
        """Read-only view of all dispatch instructions."""
        return dict(self._instructions)

    @property
    def all_results(self) -> dict[str, AgentResult]:
        """Read-only view of all recorded results."""
        return dict(self._results)
