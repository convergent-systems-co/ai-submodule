"""Platform-agnostic agent dispatch interface.

The dispatcher abstracts how agents are invoked. The orchestrator builds
AgentTask objects; the dispatcher handles platform-specific transport.

Implementations:
- ClaudeCodeDispatcher: Produces Task tool invocations with worktree isolation
- (Future) CopilotDispatcher, APIDispatcher, CIDispatcher
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from governance.engine.orchestrator.dispatch_state import DispatchState
    from governance.engine.orchestrator.dispatch_validator import DispatchValidationResult


class AgentPersona(Enum):
    """Available agent personas."""

    DEVOPS_ENGINEER = "devops-engineer"
    TECH_LEAD = "tech-lead"
    CODER = "coder"
    IAC_ENGINEER = "iac-engineer"
    TEST_WRITER = "test-writer"
    TEST_EVALUATOR = "test-evaluator"
    DOCUMENT_WRITER = "document-writer"
    DOCUMENTATION_REVIEWER = "documentation-reviewer"
    PROJECT_MANAGER = "project-manager"


@dataclass
class AgentTask:
    """A bounded task to dispatch to an agent.

    The agent receives this task, executes it, and returns an AgentResult.
    The agent never sees the full loop — only its bounded assignment.
    """

    persona: AgentPersona
    correlation_id: str  # "issue-42" or "pr-108"
    plan_content: str  # Full plan text
    issue_body: str  # Issue body + comments
    branch: str  # Target branch name
    session_id: str  # For audit log correlation
    constraints: dict = field(default_factory=dict)  # timeout, resource limits
    persona_prompt: str = ""  # Full persona .md content (loaded by runner)
    additional_context: dict = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result returned by a dispatched agent."""

    correlation_id: str
    success: bool
    branch: str | None = None  # Worktree branch with commits
    summary: str = ""
    test_results: dict | None = None
    files_changed: list[str] = field(default_factory=list)
    error: str | None = None
    task_id: str | None = None  # Platform-specific task identifier
    # Context capacity fields (populated from agent SDK metadata when available)
    tokens_consumed: int | None = None  # Total tokens used by the sub-agent
    tool_uses: int | None = None  # Number of tool invocations by the sub-agent
    context_tier: str | None = None  # green/yellow/orange/red/unknown


class Dispatcher(ABC):
    """Abstract base for agent dispatch.

    Subclasses implement platform-specific transport (Claude Code Task tool,
    Copilot, API calls, etc.). The orchestrator uses only this interface.
    """

    @abstractmethod
    def dispatch(self, tasks: list[AgentTask]) -> list[str]:
        """Dispatch agents for the given tasks.

        All tasks in a single call are independent and should be dispatched
        concurrently where possible.

        Args:
            tasks: List of bounded agent tasks.

        Returns:
            List of task IDs for tracking. Order matches input tasks.
        """

    @abstractmethod
    def collect(self, task_ids: list[str], timeout_seconds: int = 600) -> list[AgentResult]:
        """Collect results from dispatched agents.

        Blocks until all tasks complete or timeout is reached.

        Args:
            task_ids: Task IDs from dispatch().
            timeout_seconds: Maximum wait time.

        Returns:
            List of results. Order matches input task_ids.
            Timed-out tasks return AgentResult(success=False, error="timeout").
        """

    @abstractmethod
    def cancel(self, task_ids: list[str]) -> None:
        """Cancel running tasks. Best-effort — some may have already completed."""

    def validate_dispatch(
        self, tasks: list[AgentTask], config: dict,
    ) -> DispatchValidationResult:
        """Validate tasks before dispatch.

        Default implementation passes all tasks through without validation.
        Subclasses may override to enforce dispatch rules.

        Args:
            tasks: List of agent tasks to validate.
            config: Dispatch configuration dict.

        Returns:
            DispatchValidationResult (default: all valid).
        """
        from governance.engine.orchestrator.dispatch_validator import (
            DispatchValidationResult,
        )
        return DispatchValidationResult(valid=True, tasks=list(tasks))

    def get_dispatch_state(self) -> dict[str, DispatchState]:
        """Return current dispatch state for all tracked tasks.

        Default implementation returns an empty dict. Subclasses that
        track dispatch state should override this.

        Returns:
            Dict mapping task_id to DispatchState.
        """
        return {}


class DryRunDispatcher(Dispatcher):
    """Dispatcher that records tasks without executing them.

    Useful for testing the orchestrator without actually spawning agents.
    """

    def __init__(self):
        self.dispatched: list[AgentTask] = []
        self._results: dict[str, AgentResult] = {}
        self._counter = 0

    def dispatch(self, tasks: list[AgentTask]) -> list[str]:
        task_ids = []
        for task in tasks:
            self._counter += 1
            task_id = f"dry-run-{self._counter}"
            task_ids.append(task_id)
            self.dispatched.append(task)
            # Pre-populate a success result
            self._results[task_id] = AgentResult(
                correlation_id=task.correlation_id,
                success=True,
                branch=task.branch,
                summary=f"Dry run: {task.persona.value} for {task.correlation_id}",
                task_id=task_id,
            )
        return task_ids

    def collect(self, task_ids: list[str], timeout_seconds: int = 600) -> list[AgentResult]:
        return [self._results[tid] for tid in task_ids]

    def cancel(self, task_ids: list[str]) -> None:
        pass  # No-op for dry run

    def set_result(self, task_id: str, result: AgentResult) -> None:
        """Override the result for a specific task (for testing)."""
        self._results[task_id] = result
