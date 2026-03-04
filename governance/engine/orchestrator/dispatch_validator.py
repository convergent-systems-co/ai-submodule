"""Dispatch validation for agent tasks.

Validates task lists against orchestrator configuration before dispatch.
Returns structured results rather than raising exceptions, giving the
orchestrator full control over error handling.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from governance.engine.orchestrator.dispatcher import AgentPersona, AgentTask


@dataclass
class DispatchValidationResult:
    """Result of dispatch validation.

    Attributes:
        valid: True if all validations passed.
        errors: List of human-readable error strings.
        warnings: List of non-blocking warnings.
        tasks: The (possibly modified) task list -- e.g. with isolation flags set.
    """

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    tasks: list[AgentTask] = field(default_factory=list)


def validate_task_count(
    tasks: list[AgentTask],
    coder_min: int,
    coder_max: int,
) -> list[str]:
    """Validate that the task count falls within configured bounds.

    Args:
        tasks: List of tasks to validate.
        coder_min: Minimum required tasks.
        coder_max: Maximum allowed tasks (-1 for unlimited).

    Returns:
        List of error strings (empty if valid).
    """
    errors: list[str] = []
    count = len(tasks)

    if count < coder_min:
        errors.append(
            f"Task count {count} is below minimum {coder_min}."
        )

    if coder_max != -1 and count > coder_max:
        errors.append(
            f"Task count {count} exceeds maximum {coder_max}."
        )

    return errors


def validate_worktree_required(
    tasks: list[AgentTask],
    require_worktree: bool,
) -> list[AgentTask]:
    """Tag tasks with worktree isolation flag in constraints.

    When ``require_worktree`` is True, sets ``constraints["require_worktree"]``
    on each task. Does not remove the flag when False -- only adds it.

    Args:
        tasks: List of tasks to tag.
        require_worktree: Whether worktree isolation is required.

    Returns:
        The same task list with constraints updated.
    """
    if require_worktree:
        for task in tasks:
            task.constraints["require_worktree"] = True
    return tasks


def validate_branch_names(
    tasks: list[AgentTask],
    pattern: str,
) -> list[str]:
    """Check that task branch names match the expected pattern.

    The pattern uses ``{placeholder}`` syntax from project.yaml. It is
    converted to a permissive regex where each placeholder matches one
    or more non-slash word characters (plus hyphens).

    Args:
        tasks: List of tasks to validate.
        pattern: Branch naming pattern (e.g. ``{network_id}/{type}/{number}/{name}``).

    Returns:
        List of error strings (empty if all branches match).
    """
    # Convert {placeholder} pattern to regex
    # Each placeholder matches a segment of word characters plus hyphens
    regex_str = re.sub(r"\{[^}]+\}", r"[\\w.-]+", pattern)
    regex = re.compile(f"^{regex_str}$")

    errors: list[str] = []
    for task in tasks:
        if not regex.match(task.branch):
            errors.append(
                f"Branch '{task.branch}' does not match pattern '{pattern}'."
            )
    return errors


def validate_no_duplicates(tasks: list[AgentTask]) -> list[str]:
    """Prevent duplicate correlation_ids in a single dispatch batch.

    Args:
        tasks: List of tasks to validate.

    Returns:
        List of error strings for any duplicates found.
    """
    seen: dict[str, int] = {}
    errors: list[str] = []

    for task in tasks:
        cid = task.correlation_id
        if cid in seen:
            errors.append(
                f"Duplicate correlation_id '{cid}' at positions {seen[cid]} and {len(seen)}."
            )
        else:
            seen[cid] = len(seen)

    return errors


def validate_dispatch_persona(
    tasks: list[AgentTask],
    use_project_manager: bool,
) -> list[str]:
    """Reject direct Coder dispatch when PM mode is active.

    In PM mode, only Tech Lead tasks should be dispatched directly by the
    orchestrator. Coder tasks must be spawned by Tech Leads, not dispatched
    at the orchestrator level.

    Args:
        tasks: List of tasks to validate.
        use_project_manager: Whether PM mode is active.

    Returns:
        List of error strings (empty if valid or PM mode is off).
    """
    if not use_project_manager:
        return []

    errors: list[str] = []
    for i, task in enumerate(tasks):
        if task.persona == AgentPersona.CODER:
            errors.append(
                f"Task {i} dispatches a Coder directly, but PM mode is active. "
                "In PM mode, dispatch Tech Leads (not Coders). "
                "Coders are spawned by Tech Leads within their worktrees."
            )
    return errors


def validate_tech_lead_count(
    tasks: list[AgentTask],
    parallel_tech_leads: int,
) -> list[str]:
    """Enforce the parallel_tech_leads limit on dispatched tasks.

    Counts tasks with ``persona == AgentPersona.TECH_LEAD`` and returns
    an error if the count exceeds the configured limit.

    Args:
        tasks: List of tasks to validate.
        parallel_tech_leads: Maximum allowed Tech Lead tasks (-1 for unlimited).

    Returns:
        List of error strings (empty if valid).
    """
    if parallel_tech_leads == -1:
        return []

    tl_count = sum(
        1 for t in tasks
        if t.persona == AgentPersona.TECH_LEAD
    )

    errors: list[str] = []
    if tl_count > parallel_tech_leads:
        errors.append(
            f"Tech Lead count {tl_count} exceeds parallel_tech_leads limit "
            f"{parallel_tech_leads}. Reduce the number of Tech Lead tasks."
        )
    return errors


def validate_dispatch(
    tasks: list[AgentTask],
    config: dict,
) -> DispatchValidationResult:
    """Run all dispatch validations.

    This is the main entry point. It composes the individual validators
    and returns a single ``DispatchValidationResult``.

    Args:
        tasks: List of agent tasks to validate.
        config: Dict with keys:
            - ``coder_min`` (int): Minimum task count.
            - ``coder_max`` (int): Maximum task count (-1 for unlimited).
            - ``require_worktree`` (bool): Whether to require worktree isolation.
            - ``branch_pattern`` (str): Branch naming pattern.
            - ``use_project_manager`` (bool): Whether PM mode is active (optional).
            - ``parallel_tech_leads`` (int): Max Tech Lead tasks (optional).

    Returns:
        DispatchValidationResult with aggregated errors and the task list.
    """
    result = DispatchValidationResult(tasks=list(tasks))

    coder_min = config.get("coder_min", 1)
    coder_max = config.get("coder_max", 5)
    require_worktree = config.get("require_worktree", True)
    branch_pattern = config.get("branch_pattern", "")
    use_pm = config.get("use_project_manager", False)
    parallel_tl = config.get("parallel_tech_leads", config.get("parallel_team_leads", -1))

    # Task count
    result.errors.extend(validate_task_count(tasks, coder_min, coder_max))

    # Duplicates
    result.errors.extend(validate_no_duplicates(tasks))

    # Branch naming (only if pattern is provided)
    if branch_pattern:
        result.errors.extend(validate_branch_names(tasks, branch_pattern))

    # PM mode: reject direct Coder dispatch
    result.errors.extend(validate_dispatch_persona(tasks, use_pm))

    # PM mode: enforce Tech Lead count limit
    result.errors.extend(validate_tech_lead_count(tasks, parallel_tl))

    # Worktree tagging (modifies tasks in place)
    validate_worktree_required(tasks, require_worktree)

    result.valid = len(result.errors) == 0
    return result
