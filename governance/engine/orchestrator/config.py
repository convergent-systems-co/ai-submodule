"""Orchestrator configuration loader.

Reads project.yaml for governance settings and provides typed configuration
for the orchestrator. Thresholds are defined as constants (from startup.md)
rather than parsed from markdown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class OrchestratorConfig:
    """Typed configuration for the orchestrator."""

    # From project.yaml governance section
    parallel_coders: int = 5
    parallel_code_managers: int = 3
    use_project_manager: bool = False
    policy_profile: str = "default"

    # Paths
    checkpoint_dir: str = ".governance/checkpoints"
    audit_log_dir: str = ".governance/state/agent-log"
    session_dir: str = ".governance/state/sessions"
    plans_dir: str = ".governance/plans"
    panels_dir: str = ".governance/panels"

    # Circuit breaker limits (from agent-protocol.md)
    max_feedback_cycles: int = 2
    max_total_eval_cycles: int = 5

    # Issue size limits (from startup.md)
    max_issue_body_chars: int = 15000
    max_issue_comments: int = 50

    # APPROVE verification thresholds
    min_coverage: float = 80.0

    # Git conventions (from project.yaml)
    branch_pattern: str = "{network_id}/{type}/{number}/{name}"
    commit_style: str = "conventional"


def load_config(project_yaml_path: str | Path) -> OrchestratorConfig:
    """Load orchestrator config from project.yaml.

    Falls back to defaults for any missing fields.
    """
    path = Path(project_yaml_path)
    if not path.exists():
        return OrchestratorConfig()

    with open(path) as f:
        data = yaml.safe_load(f) or {}

    gov = data.get("governance", {}) or {}
    conv = data.get("conventions", {}) or {}
    git_conv = conv.get("git", {}) or {}

    return OrchestratorConfig(
        parallel_coders=gov.get("parallel_coders", 5),
        parallel_code_managers=gov.get("parallel_code_managers", 3),
        use_project_manager=gov.get("use_project_manager", False),
        policy_profile=gov.get("policy_profile", "default"),
        branch_pattern=git_conv.get("branch_pattern", "{network_id}/{type}/{number}/{name}"),
        commit_style=git_conv.get("commit_style", "conventional"),
    )
