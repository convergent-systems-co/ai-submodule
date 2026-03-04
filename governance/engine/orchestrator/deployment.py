"""Deployment phase support for the orchestrator (Phases 6-7).

Extends the orchestrator with optional deployment phases:

- **Phase 6 (Build & Package):** Docker build, artifact publish, security scan.
- **Phase 7 (Deploy & Verify):** IaC apply, Helm/container deploy, rollout
  verification, smoke tests.

These phases are **optional** and only execute when ``governance.deployment``
is configured in ``project.yaml``. When deployment is not configured, the
orchestrator skips directly from Phase 5 to loop/done.

Design:
- Phases are capacity-gated like all other phases.
- Deployment decisions are audited to the run manifest.
- Automatic rollback on verification failure.
- Fall back to human review when rollback fails.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class DeploymentTarget(str, Enum):
    """Supported deployment target platforms."""

    AKS = "aks"
    ECS = "ecs"
    LAMBDA = "lambda"
    STATIC = "static"
    CUSTOM = "custom"


class DeploymentStage(str, Enum):
    """Deployment environment stages."""

    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


class BuildOutcome(str, Enum):
    """Outcome of a build phase."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class DeployOutcome(str, Enum):
    """Outcome of a deploy/verify phase."""

    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


@dataclass
class DeploymentConfig:
    """Configuration for deployment phases.

    Parsed from ``governance.deployment`` in ``project.yaml``.
    When ``enabled`` is False, phases 6-7 are skipped entirely.
    """

    enabled: bool = False
    target: str = "custom"
    environments: list[str] = field(default_factory=lambda: ["dev"])
    rollback_on_failure: bool = True
    skip_build: bool = False
    skip_deploy: bool = False
    verify_timeout_seconds: int = 300
    artifact_registry: str = ""
    helm_chart: str = ""
    iac_path: str = ""
    smoke_test_command: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> DeploymentConfig:
        """Create DeploymentConfig from a dictionary.

        Args:
            data: Dictionary from project.yaml ``governance.deployment``.

        Returns:
            DeploymentConfig instance.
        """
        if not data:
            return cls()

        return cls(
            enabled=data.get("enabled", False),
            target=data.get("target", "custom"),
            environments=data.get("environments", ["dev"]),
            rollback_on_failure=data.get("rollback_on_failure", True),
            skip_build=data.get("skip_build", False),
            skip_deploy=data.get("skip_deploy", False),
            verify_timeout_seconds=data.get("verify_timeout_seconds", 300),
            artifact_registry=data.get("artifact_registry", ""),
            helm_chart=data.get("helm_chart", ""),
            iac_path=data.get("iac_path", ""),
            smoke_test_command=data.get("smoke_test_command", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)


@dataclass
class BuildResult:
    """Result of Phase 6 (Build & Package)."""

    outcome: str = BuildOutcome.SKIPPED.value
    artifact_id: str = ""
    artifact_digest: str = ""
    security_scan_passed: bool = False
    security_findings: list[str] = field(default_factory=list)
    timestamp: str = ""
    duration_seconds: float = 0.0
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeployResult:
    """Result of Phase 7 (Deploy & Verify)."""

    outcome: str = DeployOutcome.SKIPPED.value
    environment: str = ""
    target: str = ""
    rollback_performed: bool = False
    verification_passed: bool = False
    smoke_test_passed: bool = False
    timestamp: str = ""
    duration_seconds: float = 0.0
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeploymentPhaseResult:
    """Aggregated result of deployment phases 6-7."""

    build: BuildResult = field(default_factory=BuildResult)
    deployments: list[DeployResult] = field(default_factory=list)
    overall_success: bool = False
    needs_rollback: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "build": self.build.to_dict(),
            "deployments": [d.to_dict() for d in self.deployments],
            "overall_success": self.overall_success,
            "needs_rollback": self.needs_rollback,
        }


def should_run_deployment(config: DeploymentConfig) -> bool:
    """Determine if deployment phases should execute."""
    return config.enabled


def should_skip_build(config: DeploymentConfig) -> bool:
    """Determine if Phase 6 (build) should be skipped."""
    return not config.enabled or config.skip_build


def should_skip_deploy(config: DeploymentConfig) -> bool:
    """Determine if Phase 7 (deploy) should be skipped."""
    return not config.enabled or config.skip_deploy


def validate_deployment_config(config: DeploymentConfig) -> list[str]:
    """Validate deployment configuration for common issues.

    Returns:
        List of validation error messages. Empty if valid.
    """
    errors: list[str] = []

    if not config.enabled:
        return errors

    valid_targets = {t.value for t in DeploymentTarget}
    if config.target not in valid_targets:
        errors.append(
            f"Invalid deployment target '{config.target}'. "
            f"Must be one of: {', '.join(sorted(valid_targets))}"
        )

    valid_stages = {s.value for s in DeploymentStage}
    for env in config.environments:
        if env not in valid_stages:
            errors.append(
                f"Invalid environment '{env}'. "
                f"Must be one of: {', '.join(sorted(valid_stages))}"
            )

    stage_order = {"dev": 0, "staging": 1, "production": 2}
    envs = config.environments
    for i in range(1, len(envs)):
        prev_order = stage_order.get(envs[i - 1], -1)
        curr_order = stage_order.get(envs[i], -1)
        if curr_order >= 0 and prev_order >= 0 and curr_order < prev_order:
            errors.append(
                f"Environment '{envs[i]}' cannot come before '{envs[i-1]}' "
                "in the promotion order."
            )

    if config.verify_timeout_seconds < 0:
        errors.append("verify_timeout_seconds must be non-negative.")

    return errors


def build_phase_instructions(config: DeploymentConfig) -> dict[str, Any]:
    """Build LLM instructions for Phase 6 (Build & Package)."""
    if should_skip_build(config):
        return {
            "name": "Build & Package (Skipped)",
            "description": "Build phase skipped per configuration.",
            "outputs_expected": [],
            "gate_action": "proceed",
        }

    instructions: dict[str, Any] = {
        "name": "Build & Package",
        "description": (
            "Build artifacts, run security scans, and publish to the artifact registry. "
            f"Target platform: {config.target}."
        ),
        "outputs_expected": [
            "artifact_id",
            "artifact_digest",
            "security_scan_passed",
        ],
    }

    if config.artifact_registry:
        instructions["artifact_registry"] = config.artifact_registry

    return instructions


def deploy_phase_instructions(config: DeploymentConfig) -> dict[str, Any]:
    """Build LLM instructions for Phase 7 (Deploy & Verify)."""
    if should_skip_deploy(config):
        return {
            "name": "Deploy & Verify (Skipped)",
            "description": "Deploy phase skipped per configuration.",
            "outputs_expected": [],
            "gate_action": "proceed",
        }

    instructions: dict[str, Any] = {
        "name": "Deploy & Verify",
        "description": (
            f"Deploy to {', '.join(config.environments)} environments. "
            f"Target: {config.target}. "
            f"Rollback on failure: {config.rollback_on_failure}."
        ),
        "outputs_expected": [
            "environment",
            "deployment_status",
            "verification_passed",
        ],
    }

    if config.smoke_test_command:
        instructions["smoke_test_command"] = config.smoke_test_command
    if config.helm_chart:
        instructions["helm_chart"] = config.helm_chart
    if config.iac_path:
        instructions["iac_path"] = config.iac_path

    return instructions
