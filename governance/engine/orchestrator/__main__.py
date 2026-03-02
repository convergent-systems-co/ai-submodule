"""CLI entry point for the step-based orchestrator.

Usage:
    python -m governance.engine.orchestrator init [--config PATH] [--session-id ID]
    python -m governance.engine.orchestrator step --complete PHASE --result JSON [--session-id ID]
    python -m governance.engine.orchestrator signal --type TYPE [--count N] [--session-id ID]
    python -m governance.engine.orchestrator gate --phase PHASE [--session-id ID]
    python -m governance.engine.orchestrator status [--session-id ID]

All output is JSON to stdout. Exit code 2 on shutdown.
"""

from __future__ import annotations

import argparse
import json
import sys

from governance.engine.orchestrator.config import OrchestratorConfig, load_config
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
    runner = StepRunner(config, session_id=args.session_id)
    result = runner.init_session()
    print(json.dumps(result.to_dict(), indent=2))
    return 2 if result.action == "shutdown" else 0


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
        result = runner.step(args.complete, phase_result)
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


_COMMANDS = {
    "init": _cmd_init,
    "step": _cmd_step,
    "signal": _cmd_signal,
    "gate": _cmd_gate,
    "status": _cmd_status,
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
