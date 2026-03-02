"""Orchestrator configuration loader.

Reads project.yaml for governance settings and provides typed configuration
for the orchestrator. Thresholds are defined as constants (from startup.md)
rather than parsed from markdown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from governance.engine.orchestrator.model_router import ModelConfig


@dataclass(frozen=True)
class OrchestratorConfig:
    """Typed configuration for the orchestrator."""

    # From project.yaml governance section
    parallel_coders: int = 5
    parallel_code_managers: int = 3
    use_project_manager: bool = False
    policy_profile: str = "default"

    # Model routing configuration (from governance.models in project.yaml)
    models: ModelConfig = field(default_factory=ModelConfig)

    # Coder scaling (from project.yaml governance section)
    coder_min: int = 1
    coder_max: int = 5
    require_worktree: bool = True

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

    def __post_init__(self) -> None:
        """Validate coder_min <= coder_max (unless coder_max is -1 for unlimited)."""
        if self.coder_max != -1 and self.coder_min > self.coder_max:
            raise ValueError(
                f"coder_min ({self.coder_min}) must be <= coder_max ({self.coder_max})"
            )


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

    # Parse model configuration
    models_data = gov.get("models", None)
    models_config = ModelConfig.from_dict(models_data)

    return OrchestratorConfig(
        parallel_coders=gov.get("parallel_coders", 5),
        parallel_code_managers=gov.get("parallel_code_managers", 3),
        use_project_manager=gov.get("use_project_manager", False),
        policy_profile=gov.get("policy_profile", "default"),
        models=models_config,
        branch_pattern=git_conv.get("branch_pattern", "{network_id}/{type}/{number}/{name}"),
        commit_style=git_conv.get("commit_style", "conventional"),
    )
