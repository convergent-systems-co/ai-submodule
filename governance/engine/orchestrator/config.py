"""Orchestrator configuration loader.

Reads project.yaml for governance settings and provides typed configuration
for the orchestrator. Thresholds are defined as constants (from startup.md)
rather than parsed from markdown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from governance.engine.orchestrator.deployment import DeploymentConfig
from governance.engine.orchestrator.model_router import ModelConfig, parse_panel_models_config
from governance.engine.orchestrator.plugins import ExtensionsConfig


@dataclass(frozen=True)
class OrchestratorConfig:
    """Typed configuration for the orchestrator."""

    # From project.yaml governance section
    parallel_coders: int = 5
    parallel_tech_leads: int = 3
    use_project_manager: bool = False
    policy_profile: str = "default"

    # Model routing configuration (from governance.models in project.yaml)
    models: ModelConfig = field(default_factory=ModelConfig)

    # Coder scaling (from project.yaml governance section)
    coder_min: int = 1
    coder_max: int = 5
    require_worktree: bool = True

    # Paths (see governance/engine/paths.py for constants)
    checkpoint_dir: str = ".artifacts/checkpoints"
    audit_log_dir: str = ".artifacts/logs"
    session_dir: str = ".artifacts/state/sessions"
    plans_dir: str = ".artifacts/plans"
    panels_dir: str = ".artifacts/panels"
    emissions_dir: str = ".artifacts/emissions"

    # DevOps Engineer heartbeat/backoff (PM mode)
    devops_heartbeat_interval_seconds: int = 60
    devops_idle_backoff_max_seconds: int = 300

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

    # Deployment configuration (optional phases 6-7)
    deployment: DeploymentConfig = field(default_factory=DeploymentConfig)

    # Plugin extensions (from project.yaml governance.extensions)
    extensions: ExtensionsConfig = field(default_factory=ExtensionsConfig)

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

    # Parse model configuration from governance.models (primary syntax)
    models_data = gov.get("models", None)
    models_config = ModelConfig.from_dict(models_data)

    # Parse alternative governance.panel_models syntax (defaults/overrides)
    # This merges into the existing ModelConfig — panel_models overrides take
    # precedence over governance.models.panels when both are present.
    panel_models_data = gov.get("panel_models", None)
    if panel_models_data:
        pm_default, pm_overrides = parse_panel_models_config(panel_models_data)
        # Merge: panel_models overrides win over models.panels
        merged_panel_overrides = dict(models_config.panel_overrides)
        merged_panel_overrides.update(pm_overrides)
        # If panel_models.defaults.model is set, use it as default
        # (only if governance.models.default was not explicitly set)
        merged_default = models_config.default
        if pm_default and models_config.default == "auto":
            merged_default = pm_default
        models_config = ModelConfig(
            default=merged_default,
            tier_models=dict(models_config.tier_models),
            panel_overrides=merged_panel_overrides,
            persona_overrides=dict(models_config.persona_overrides),
        )

    deployment_data = gov.get("deployment", None)
    deployment_config = DeploymentConfig.from_dict(deployment_data)

    # Backward compat: accept parallel_tech_leads, parallel_team_leads, parallel_code_managers
    # parallel_tech_leads takes precedence over parallel_team_leads over parallel_code_managers
    parallel_tech_leads = gov.get(
        "parallel_tech_leads",
        gov.get("parallel_team_leads",
                gov.get("parallel_code_managers", 3)),
    )

    extensions = ExtensionsConfig.from_dict(gov.get("extensions", None))

    return OrchestratorConfig(
        parallel_coders=gov.get("parallel_coders", 5),
        parallel_tech_leads=parallel_tech_leads,
        use_project_manager=gov.get("use_project_manager", False),
        policy_profile=gov.get("policy_profile", "default"),
        models=models_config,
        coder_min=gov.get("coder_min", 1),
        coder_max=gov.get("coder_max", 5),
        require_worktree=gov.get("require_worktree", True),
        branch_pattern=git_conv.get("branch_pattern", "{network_id}/{type}/{number}/{name}"),
        commit_style=git_conv.get("commit_style", "conventional"),
        devops_heartbeat_interval_seconds=gov.get("devops_heartbeat_interval_seconds", 60),
        devops_idle_backoff_max_seconds=gov.get("devops_idle_backoff_max_seconds", 300),
        deployment=deployment_config,
        extensions=extensions,
    )
