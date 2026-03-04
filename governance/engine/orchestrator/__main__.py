"""CLI entry point for the step-based orchestrator.

Usage:
    python -m governance.engine.orchestrator init [--config PATH] [--session-id ID]
    python -m governance.engine.orchestrator step --complete PHASE --result JSON [--session-id ID] [--agent TASK_ID]
    python -m governance.engine.orchestrator signal --type TYPE [--count N] [--session-id ID]
    python -m governance.engine.orchestrator gate --phase PHASE [--session-id ID]
    python -m governance.engine.orchestrator status [--session-id ID]
    python -m governance.engine.orchestrator tree [--session-id ID]
    python -m governance.engine.orchestrator register --persona PERSONA --task-id ID [--session-id ID]
    python -m governance.engine.orchestrator heartbeat --agent TASK_ID [--session-id ID]
    python -m governance.engine.orchestrator dispatch --persona PERSONA --parent TASK_ID [--session-id ID]
    python -m governance.engine.orchestrator preflight [--config PATH]
    python -m governance.engine.orchestrator locks [--session-id ID] [--cleanup] [--force-release ISSUE]

All output is JSON to stdout. Exit code 2 on shutdown.
"""

from __future__ import annotations

import argparse
import json
import sys

from governance.engine.orchestrator.config import OrchestratorConfig, load_config
from governance.engine.preflight import validate_project_yaml
from governance.engine.orchestrator.step_runner import StepRunner


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m governance.engine.orchestrator",
        description="Step-based orchestrator CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    init_p = sub.add_parser("init", help="Initialize or resume a session")
    init_p.add_argument("--config", default="project.yaml", help="Path to project.yaml")
    init_p.add_argument("--session-id", default=None, help="Session ID (auto-generated if omitted)")

    # step
    step_p = sub.add_parser("step", help="Complete a phase and get next instruction")
    step_p.add_argument("--complete", type=int, required=True, help="Phase number just completed")
    step_p.add_argument("--result", default="{}", help="JSON result from completed phase")
    step_p.add_argument("--agent", default=None, help="Task ID of the agent completing this phase (for persona binding validation)")
    step_p.add_argument("--session-id", default=None, help="Session ID")
    step_p.add_argument("--config", default="project.yaml", help="Path to project.yaml")

    # signal
    sig_p = sub.add_parser("signal", help="Record a capacity signal")
    sig_p.add_argument("--type", required=True, choices=["tool_call", "turn", "issue_completed"])
    sig_p.add_argument("--count", type=int, default=1, help="Number of signals")
    sig_p.add_argument("--session-id", default=None, help="Session ID")
    sig_p.add_argument("--config", default="project.yaml", help="Path to project.yaml")

    # gate
    gate_p = sub.add_parser("gate", help="Read-only gate check")
    gate_p.add_argument("--phase", type=int, required=True, help="Phase to check")
    gate_p.add_argument("--session-id", default=None, help="Session ID")
    gate_p.add_argument("--config", default="project.yaml", help="Path to project.yaml")

    # status
    stat_p = sub.add_parser("status", help="Dump current session state")
    stat_p.add_argument("--session-id", default=None, help="Session ID")
    stat_p.add_argument("--config", default="project.yaml", help="Path to project.yaml")

    # tree
    tree_p = sub.add_parser("tree", help="Show workload tree with agent topology")
    tree_p.add_argument("--session-id", default=None, help="Session ID")
    tree_p.add_argument("--config", default="project.yaml", help="Path to project.yaml")

    # preflight
    pre_p = sub.add_parser("preflight", help="Validate project.yaml (YAML syntax, schema, template coverage)")
    pre_p.add_argument("--config", default="project.yaml", help="Path to project.yaml")

    # register
    reg_p = sub.add_parser("register", help="Register an agent in the agent registry")
    reg_p.add_argument("--persona", required=True, help="Agent persona (e.g. devops_engineer, code_manager, coder)")
    reg_p.add_argument("--task-id", required=True, help="Unique task identifier for the agent")
    reg_p.add_argument("--correlation-id", default="", help="Correlation ID (issue ref, PR ref)")
    reg_p.add_argument("--parent-task-id", default="", help="Parent task ID for hierarchy tracking")
    reg_p.add_argument("--session-id", default=None, help="Session ID")
    reg_p.add_argument("--config", default="project.yaml", help="Path to project.yaml")

    # heartbeat
    hb_p = sub.add_parser("heartbeat", help="Record agent heartbeat (liveness signal)")
    hb_p.add_argument("--agent", required=True, help="Task ID of the agent sending heartbeat")
    hb_p.add_argument("--status", default="alive", choices=["alive"], help="Heartbeat status")
    hb_p.add_argument("--session-id", default=None, help="Session ID")
    hb_p.add_argument("--config", default="project.yaml", help="Path to project.yaml")

    # dispatch
    disp_p = sub.add_parser("dispatch", help="Validate and create a dispatch descriptor for agent spawning")
    disp_p.add_argument("--persona", required=True, help="Target persona to spawn (e.g. tech_lead, coder)")
    disp_p.add_argument("--parent", required=True, help="Task ID of the parent agent requesting the spawn")
    disp_p.add_argument("--assign", default="{}", help="JSON ASSIGN message payload")
    disp_p.add_argument("--topology-path", default=None, help="Path to agent-topology.yaml (default: auto-detect)")
    disp_p.add_argument("--session-id", default=None, help="Session ID")
    disp_p.add_argument("--config", default="project.yaml", help="Path to project.yaml")

    # locks
    locks_p = sub.add_parser("locks", help="Inspect cross-session work locks")
    locks_p.add_argument("--session-id", default=None, help="Session ID (for ownership display)")
    locks_p.add_argument("--config", default="project.yaml", help="Path to project.yaml")
    locks_p.add_argument("--cleanup", action="store_true", help="Remove stale locks")
    locks_p.add_argument("--force-release", type=int, default=None, metavar="ISSUE", help="Force-release a lock for a specific issue number")

    return parser


def _load_config(args: argparse.Namespace) -> OrchestratorConfig:
    config_path = getattr(args, "config", "project.yaml")
    return load_config(config_path)


def _resolve_session_id(args: argparse.Namespace, config: OrchestratorConfig) -> str | None:
    """Resolve session ID from args or find the latest."""
    sid = getattr(args, "session_id", None)
    if sid:
        return sid
    # For non-init commands, try to find the latest session
    if args.command != "init":
        from governance.engine.orchestrator.session import SessionStore
        store = SessionStore(config.session_dir)
        sessions = store.list_sessions()
        if sessions:
            return sessions[0]
    return None


def _cmd_init(args: argparse.Namespace) -> int:
    config = _load_config(args)
    config_path = getattr(args, "config", "project.yaml")
    runner = StepRunner(config, session_id=args.session_id, project_yaml_path=config_path)
    result = runner.init_session()
    print(json.dumps(result.to_dict(), indent=2))
    return 2 if result.action == "shutdown" else 0


def _cmd_preflight(args: argparse.Namespace) -> int:
    config_path = getattr(args, "config", "project.yaml")
    result = validate_project_yaml(config_path)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.valid else 1


def _cmd_step(args: argparse.Namespace) -> int:
    config = _load_config(args)
    session_id = _resolve_session_id(args, config)
    if not session_id:
        print(json.dumps({"error": "No session found. Run init first."}))
        return 1

    try:
        phase_result = json.loads(args.result)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON in --result: {e}"}))
        return 1

    runner = StepRunner(config, session_id=session_id)
    try:
        result = runner.step(
            args.complete,
            phase_result,
            agent_task_id=getattr(args, "agent", None),
        )
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}))
        return 1
    print(json.dumps(result.to_dict(), indent=2))
    return 2 if result.action == "shutdown" else 0


def _cmd_signal(args: argparse.Namespace) -> int:
    config = _load_config(args)
    session_id = _resolve_session_id(args, config)
    if not session_id:
        print(json.dumps({"error": "No session found. Run init first."}))
        return 1

    runner = StepRunner(config, session_id=session_id)
    try:
        result = runner.record_signal(args.type, args.count)
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


def _cmd_gate(args: argparse.Namespace) -> int:
    config = _load_config(args)
    session_id = _resolve_session_id(args, config)
    if not session_id:
        print(json.dumps({"error": "No session found. Run init first."}))
        return 1

    runner = StepRunner(config, session_id=session_id)
    try:
        result = runner.query_gate(args.phase)
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    config = _load_config(args)
    session_id = _resolve_session_id(args, config)
    if not session_id:
        print(json.dumps({"error": "No active sessions found."}))
        return 1

    runner = StepRunner(config, session_id=session_id)
    result = runner.get_status()
    print(json.dumps(result, indent=2))
    return 0


def _cmd_tree(args: argparse.Namespace) -> int:
    config = _load_config(args)
    session_id = _resolve_session_id(args, config)
    if not session_id:
        print(json.dumps({"error": "No active sessions found."}))
        return 1

    runner = StepRunner(config, session_id=session_id)
    result = runner.get_workload_tree()
    print(json.dumps(result, indent=2))
    return 0


def _cmd_register(args: argparse.Namespace) -> int:
    config = _load_config(args)
    session_id = _resolve_session_id(args, config)
    if not session_id:
        print(json.dumps({"error": "No session found. Run init first."}))
        return 1

    runner = StepRunner(config, session_id=session_id)
    try:
        result = runner.register_agent(
            persona=args.persona,
            task_id=args.task_id,
            correlation_id=args.correlation_id,
            parent_task_id=args.parent_task_id,
        )
    except (RuntimeError, ValueError) as e:
        print(json.dumps({"error": str(e)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


def _cmd_heartbeat(args: argparse.Namespace) -> int:
    config = _load_config(args)
    session_id = _resolve_session_id(args, config)
    if not session_id:
        print(json.dumps({"error": "No session found. Run init first."}))
        return 1

    runner = StepRunner(config, session_id=session_id)
    try:
        result = runner.record_heartbeat(agent_task_id=args.agent)
    except (RuntimeError, KeyError) as e:
        print(json.dumps({"error": str(e)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


def _cmd_dispatch(args: argparse.Namespace) -> int:
    config = _load_config(args)
    session_id = _resolve_session_id(args, config)
    if not session_id:
        print(json.dumps({"error": "No session found. Run init first."}))
        return 1

    try:
        assign_payload = json.loads(args.assign)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON in --assign: {e}"}))
        return 1

    runner = StepRunner(config, session_id=session_id)
    try:
        result = runner.dispatch_agent(
            target_persona=args.persona,
            parent_task_id=args.parent,
            assign=assign_payload,
            topology_path=args.topology_path,
        )
    except (RuntimeError, ValueError) as e:
        print(json.dumps({"error": str(e)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


def _cmd_locks(args: argparse.Namespace) -> int:
    from governance.engine.orchestrator.lock_manager import LockManager

    config = _load_config(args)
    session_id = _resolve_session_id(args, config) or "unknown"

    mgr = LockManager(session_id=session_id)

    # --force-release: remove a specific lock regardless of owner
    if args.force_release is not None:
        removed = mgr.force_release(args.force_release)
        print(json.dumps({
            "action": "force_release",
            "issue_number": args.force_release,
            "removed": removed,
        }, indent=2))
        return 0

    # --cleanup: remove stale locks
    if args.cleanup:
        removed = mgr.cleanup_stale()
        print(json.dumps({
            "action": "cleanup_stale",
            "removed_issues": removed,
            "removed_count": len(removed),
        }, indent=2))
        return 0

    # Default: show lock status
    result = mgr.to_status_dict()
    print(json.dumps(result, indent=2))
    return 0


_COMMANDS = {
    "init": _cmd_init,
    "step": _cmd_step,
    "signal": _cmd_signal,
    "gate": _cmd_gate,
    "status": _cmd_status,
    "tree": _cmd_tree,
    "register": _cmd_register,
    "heartbeat": _cmd_heartbeat,
    "dispatch": _cmd_dispatch,
    "preflight": _cmd_preflight,
    "locks": _cmd_locks,
}


def main(argv: list[str] | None = None) -> int:
    parser = _make_parser()
    args = parser.parse_args(argv)
    handler = _COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
