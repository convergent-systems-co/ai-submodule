"""Workload tree builder for the orchestrator.

Generates a structured tree showing agent topology, issue assignments,
PR status, and config-driven scaling info. Used by the ``tree`` CLI command.
Includes registered agents from the agent registry when available.
"""

from __future__ import annotations

from governance.engine.orchestrator.agent_registry import AgentRegistry
from governance.engine.orchestrator.config import OrchestratorConfig
from governance.engine.orchestrator.session import PersistedSession

# Phase number -> human-readable name
_PHASE_NAMES: dict[int, str] = {
    0: "Checkpoint Recovery",
    1: "Pre-flight & Triage",
    2: "Parallel Planning",
    3: "Parallel Dispatch",
    4: "Collect & Review",
    5: "Merge & Loop Decision",
}


def build_tree(
    session: PersistedSession,
    config: OrchestratorConfig,
    dispatcher=None,
    registry: AgentRegistry | None = None,
) -> dict:
    """Build structured workload tree from session and dispatcher state.

    Args:
        session: Current persisted session state.
        config: Orchestrator configuration (scaling params, paths).
        dispatcher: Optional ClaudeCodeDispatcher with live task state.
        registry: Optional AgentRegistry with registered agent topology.

    Returns:
        Dict containing tree structure, agent nodes, issue/PR status,
        summary counts, registered agents, and a rendered ASCII tree string.
    """
    # Restore registry from session if not provided directly
    if registry is None and session.agent_registry:
        registry = AgentRegistry.from_dict(session.agent_registry)

    agents = _build_agent_nodes(session, dispatcher)
    registered_agents = _build_registered_agents(registry)
    issues = _build_issue_summary(session)
    prs = _build_pr_summary(session)
    summary = _build_summary(agents, issues, prs)

    tree = {
        "session_id": session.session_id,
        "phase": session.current_phase,
        "phase_name": _PHASE_NAMES.get(session.current_phase, f"Phase {session.current_phase}"),
        "loop_count": session.loop_count,
        "config": {
            "use_project_manager": config.use_project_manager,
            "parallel_coders": config.parallel_coders,
            "parallel_tech_leads": config.parallel_tech_leads,
            "coder_min": config.coder_min,
            "coder_max": config.coder_max,
        },
        "agents": agents,
        "registered_agents": registered_agents,
        "issues": issues,
        "prs": prs,
        "summary": summary,
        "ascii_tree": render_ascii_tree(
            session, config, agents, issues, prs, registered_agents,
        ),
    }
    return tree


def _build_agent_nodes(session: PersistedSession, dispatcher=None) -> list[dict]:
    """Extract agent nodes from dispatcher instructions and results."""
    agents: list[dict] = []

    if dispatcher is None:
        # No live dispatcher -- reconstruct from session dispatch_results
        for result in session.dispatch_results:
            agents.append({
                "persona": result.get("persona", "coder"),
                "issue_ref": result.get("correlation_id", ""),
                "branch": result.get("branch", ""),
                "status": "completed" if result.get("success") else "failed",
                "task_id": result.get("task_id", ""),
            })
        return agents

    # Live dispatcher available -- merge instructions with results
    all_instructions = dispatcher.all_instructions  # dict[str, DispatchInstruction]
    all_results = dispatcher.all_results  # dict[str, AgentResult]

    for task_id, inst in all_instructions.items():
        result = all_results.get(task_id)
        if result is not None:
            status = "completed" if result.success else "failed"
            if result.error == "pending":
                status = "pending"
        else:
            status = "pending"

        agents.append({
            "persona": inst.persona,
            "issue_ref": inst.issue_ref,
            "branch": inst.branch_name,
            "status": status,
            "task_id": task_id,
        })

    return agents


def _build_registered_agents(registry: AgentRegistry | None) -> list[dict]:
    """Extract registered agent nodes from the agent registry."""
    if registry is None:
        return []

    agents: list[dict] = []
    for task_id, agent in registry.all_agents.items():
        agents.append({
            "persona": agent.persona,
            "task_id": agent.task_id,
            "correlation_id": agent.correlation_id,
            "status": agent.status,
            "parent_task_id": agent.parent_task_id,
        })
    return agents


def _build_issue_summary(session: PersistedSession) -> dict:
    """Build issue status summary from session state."""
    return {
        "selected": list(session.issues_selected),
        "done": list(session.issues_done),
        "plans": dict(session.plans),
    }


def _build_pr_summary(session: PersistedSession) -> dict:
    """Build PR status summary from session state."""
    return {
        "created": list(session.prs_created),
        "resolved": list(session.prs_resolved),
        "remaining": list(session.prs_remaining),
    }


def _build_summary(agents: list[dict], issues: dict, prs: dict) -> dict:
    """Build aggregate counts."""
    persona_counts: dict[str, int] = {}
    completed = 0
    pending = 0
    failed = 0

    for agent in agents:
        persona = agent.get("persona", "unknown")
        persona_counts[persona] = persona_counts.get(persona, 0) + 1
        status = agent.get("status", "pending")
        if status == "completed":
            completed += 1
        elif status == "failed":
            failed += 1
        else:
            pending += 1

    return {
        "by_persona": persona_counts,
        "total_agents": len(agents),
        "completed": completed,
        "pending": pending,
        "failed": failed,
        "issues_selected": len(issues.get("selected", [])),
        "issues_done": len(issues.get("done", [])),
        "prs_created": len(prs.get("created", [])),
        "prs_resolved": len(prs.get("resolved", [])),
        "prs_remaining": len(prs.get("remaining", [])),
    }


def render_ascii_tree(
    session: PersistedSession,
    config: OrchestratorConfig,
    agents: list[dict],
    issues: dict,
    prs: dict,
    registered_agents: list[dict] | None = None,
) -> str:
    """Render a human-readable ASCII tree for terminal display.

    Example output::

        Session: session-abc123 | Phase: 3 (Parallel Dispatch) | Loop: 0
        Config: parallel_coders=5, coder_min=1, coder_max=5
        Registered agents: 3 (devops_engineer=1, code_manager=1, coder=1)
        +-- Coder [issue-42] -> branch: itsfwcp/fix/42/... (completed)
        +-- Coder [issue-43] -> branch: itsfwcp/feat/43/... (pending)
        \\-- Tester [pr-108] -> (pending)
        Issues: 2 selected, 1 done | PRs: 1 created, 0 resolved
    """
    phase_name = _PHASE_NAMES.get(session.current_phase, f"Phase {session.current_phase}")
    lines: list[str] = []

    # Header
    lines.append(
        f"Session: {session.session_id} | Phase: {session.current_phase} "
        f"({phase_name}) | Loop: {session.loop_count}"
    )

    # Config line
    lines.append(
        f"Config: parallel_coders={config.parallel_coders}, "
        f"coder_min={config.coder_min}, coder_max={config.coder_max}"
    )

    # Registered agents line (from agent registry)
    if registered_agents:
        persona_counts: dict[str, int] = {}
        for ra in registered_agents:
            p = ra.get("persona", "unknown")
            persona_counts[p] = persona_counts.get(p, 0) + 1
        counts_str = ", ".join(f"{k}={v}" for k, v in sorted(persona_counts.items()))
        lines.append(f"Registered agents: {len(registered_agents)} ({counts_str})")

    # Agent nodes (from dispatcher)
    if agents:
        for i, agent in enumerate(agents):
            is_last = i == len(agents) - 1
            connector = "\\--" if is_last else "+--"
            persona = agent.get("persona", "unknown").capitalize()
            issue_ref = agent.get("issue_ref", "")
            branch = agent.get("branch", "")
            status = agent.get("status", "pending")

            ref_part = f" [{issue_ref}]" if issue_ref else ""
            branch_part = f" -> branch: {branch}" if branch else ""
            lines.append(f"{connector} {persona}{ref_part}{branch_part} ({status})")
    else:
        lines.append("(no agents dispatched)")

    # Footer
    n_selected = len(issues.get("selected", []))
    n_done = len(issues.get("done", []))
    n_prs_created = len(prs.get("created", []))
    n_prs_resolved = len(prs.get("resolved", []))
    lines.append(
        f"Issues: {n_selected} selected, {n_done} done | "
        f"PRs: {n_prs_created} created, {n_prs_resolved} resolved"
    )

    return "\n".join(lines)
