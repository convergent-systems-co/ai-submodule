"""Tests for deployment phases 6-7 in the orchestrator.

Tests cover:
- DeploymentConfig parsing and defaults
- Deployment validation
- Gate actions for phases 6 and 7
- State machine transitions with deployment phases
- Phase routing with/without deployment configured
- Build and deploy result serialization
- Session deployment state fields
"""

from __future__ import annotations

import pytest

from governance.engine.orchestrator.capacity import (
    Action,
    CapacitySignals,
    Tier,
    gate_action,
)
from governance.engine.orchestrator.config import OrchestratorConfig, load_config
from governance.engine.orchestrator.deployment import (
    BuildOutcome,
    BuildResult,
    DeploymentConfig,
    DeploymentPhaseResult,
    DeploymentStage,
    DeploymentTarget,
    DeployOutcome,
    DeployResult,
    build_phase_instructions,
    deploy_phase_instructions,
    should_run_deployment,
    should_skip_build,
    should_skip_deploy,
    validate_deployment_config,
)
from governance.engine.orchestrator.session import PersistedSession
from governance.engine.orchestrator.state_machine import (
    InvalidTransition,
    ShutdownRequired,
    StateMachine,
)


# ---------------------------------------------------------------------------
# DeploymentConfig
# ---------------------------------------------------------------------------


class TestDeploymentConfig:
    """Tests for DeploymentConfig parsing and defaults."""

    def test_default_disabled(self) -> None:
        config = DeploymentConfig()
        assert config.enabled is False
        assert config.target == "custom"
        assert config.environments == ["dev"]

    def test_from_dict_none(self) -> None:
        config = DeploymentConfig.from_dict(None)
        assert config.enabled is False

    def test_from_dict_empty(self) -> None:
        config = DeploymentConfig.from_dict({})
        assert config.enabled is False

    def test_from_dict_enabled(self) -> None:
        config = DeploymentConfig.from_dict({
            "enabled": True,
            "target": "aks",
            "environments": ["dev", "staging", "production"],
            "rollback_on_failure": True,
            "artifact_registry": "myregistry.azurecr.io",
            "helm_chart": "charts/myapp",
        })
        assert config.enabled is True
        assert config.target == "aks"
        assert config.environments == ["dev", "staging", "production"]
        assert config.rollback_on_failure is True
        assert config.artifact_registry == "myregistry.azurecr.io"
        assert config.helm_chart == "charts/myapp"

    def test_from_dict_skip_flags(self) -> None:
        config = DeploymentConfig.from_dict({
            "enabled": True,
            "skip_build": True,
            "skip_deploy": False,
        })
        assert config.skip_build is True
        assert config.skip_deploy is False

    def test_to_dict_round_trip(self) -> None:
        config = DeploymentConfig(
            enabled=True,
            target="ecs",
            environments=["dev", "staging"],
        )
        d = config.to_dict()
        restored = DeploymentConfig.from_dict(d)
        assert restored.enabled == config.enabled
        assert restored.target == config.target
        assert restored.environments == config.environments


# ---------------------------------------------------------------------------
# Deployment validation
# ---------------------------------------------------------------------------


class TestValidateDeploymentConfig:
    """Tests for validate_deployment_config()."""

    def test_disabled_always_valid(self) -> None:
        config = DeploymentConfig(enabled=False)
        assert validate_deployment_config(config) == []

    def test_valid_aks_config(self) -> None:
        config = DeploymentConfig(
            enabled=True,
            target="aks",
            environments=["dev", "staging", "production"],
        )
        assert validate_deployment_config(config) == []

    def test_invalid_target(self) -> None:
        config = DeploymentConfig(enabled=True, target="invalid")
        errors = validate_deployment_config(config)
        assert len(errors) == 1
        assert "Invalid deployment target" in errors[0]

    def test_invalid_environment(self) -> None:
        config = DeploymentConfig(
            enabled=True,
            target="aks",
            environments=["dev", "qa"],
        )
        errors = validate_deployment_config(config)
        assert any("Invalid environment" in e for e in errors)

    def test_wrong_promotion_order(self) -> None:
        config = DeploymentConfig(
            enabled=True,
            target="aks",
            environments=["production", "dev"],
        )
        errors = validate_deployment_config(config)
        assert any("cannot come before" in e for e in errors)

    def test_negative_timeout(self) -> None:
        config = DeploymentConfig(
            enabled=True,
            target="aks",
            environments=["dev"],
            verify_timeout_seconds=-1,
        )
        errors = validate_deployment_config(config)
        assert any("non-negative" in e for e in errors)

    def test_valid_all_targets(self) -> None:
        for target in DeploymentTarget:
            config = DeploymentConfig(
                enabled=True,
                target=target.value,
                environments=["dev"],
            )
            assert validate_deployment_config(config) == []


# ---------------------------------------------------------------------------
# Should run / skip
# ---------------------------------------------------------------------------


class TestShouldRunDeployment:
    """Tests for should_run_deployment, should_skip_build, should_skip_deploy."""

    def test_disabled(self) -> None:
        config = DeploymentConfig(enabled=False)
        assert should_run_deployment(config) is False
        assert should_skip_build(config) is True
        assert should_skip_deploy(config) is True

    def test_enabled(self) -> None:
        config = DeploymentConfig(enabled=True)
        assert should_run_deployment(config) is True
        assert should_skip_build(config) is False
        assert should_skip_deploy(config) is False

    def test_skip_build_flag(self) -> None:
        config = DeploymentConfig(enabled=True, skip_build=True)
        assert should_skip_build(config) is True
        assert should_skip_deploy(config) is False

    def test_skip_deploy_flag(self) -> None:
        config = DeploymentConfig(enabled=True, skip_deploy=True)
        assert should_skip_build(config) is False
        assert should_skip_deploy(config) is True


# ---------------------------------------------------------------------------
# Gate actions for phases 6-7
# ---------------------------------------------------------------------------


class TestDeploymentGateActions:
    """Tests for gate actions on deployment phases."""

    def test_phase_6_green_proceeds(self) -> None:
        assert gate_action(6, Tier.GREEN) == Action.PROCEED

    def test_phase_6_yellow_proceeds(self) -> None:
        assert gate_action(6, Tier.YELLOW) == Action.PROCEED

    def test_phase_6_orange_checkpoints(self) -> None:
        assert gate_action(6, Tier.ORANGE) == Action.CHECKPOINT

    def test_phase_6_red_stops(self) -> None:
        assert gate_action(6, Tier.RED) == Action.EMERGENCY_STOP

    def test_phase_7_green_proceeds(self) -> None:
        assert gate_action(7, Tier.GREEN) == Action.PROCEED

    def test_phase_7_yellow_skips(self) -> None:
        assert gate_action(7, Tier.YELLOW) == Action.SKIP_DISPATCH

    def test_phase_7_orange_checkpoints(self) -> None:
        assert gate_action(7, Tier.ORANGE) == Action.CHECKPOINT

    def test_phase_7_red_stops(self) -> None:
        assert gate_action(7, Tier.RED) == Action.EMERGENCY_STOP

    def test_phase_8_invalid(self) -> None:
        with pytest.raises(ValueError, match="Must be 0-7"):
            gate_action(8, Tier.GREEN)


# ---------------------------------------------------------------------------
# State machine transitions
# ---------------------------------------------------------------------------


class TestDeploymentTransitions:
    """Tests for state machine transitions with deployment phases."""

    def test_phase_5_to_6(self) -> None:
        sm = StateMachine()
        sm.transition(1)  # Start
        sm.transition(2)
        sm.transition(3)
        sm.transition(4)
        sm.transition(5)
        action = sm.transition(6)  # Merge -> Build
        assert action == Action.PROCEED
        assert sm.phase == 6

    def test_phase_6_to_7(self) -> None:
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        sm.transition(3)
        sm.transition(4)
        sm.transition(5)
        sm.transition(6)
        action = sm.transition(7)  # Build -> Deploy
        assert action == Action.PROCEED
        assert sm.phase == 7

    def test_phase_7_to_1_loop(self) -> None:
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        sm.transition(3)
        sm.transition(4)
        sm.transition(5)
        sm.transition(6)
        sm.transition(7)
        action = sm.transition(1)  # Deploy -> Pre-flight (loop)
        assert action == Action.PROCEED
        assert sm.phase == 1

    def test_phase_0_can_resume_to_6(self) -> None:
        sm = StateMachine()
        action = sm.transition(6)  # Recovery -> Build
        assert action == Action.PROCEED

    def test_phase_0_can_resume_to_7(self) -> None:
        sm = StateMachine()
        action = sm.transition(7)  # Recovery -> Deploy
        assert action == Action.PROCEED

    def test_phase_6_cannot_skip_to_1(self) -> None:
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        sm.transition(3)
        sm.transition(4)
        sm.transition(5)
        sm.transition(6)
        with pytest.raises(InvalidTransition):
            sm.transition(1)  # Build cannot skip to Pre-flight

    def test_phase_7_cannot_go_to_6(self) -> None:
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        sm.transition(3)
        sm.transition(4)
        sm.transition(5)
        sm.transition(6)
        sm.transition(7)
        with pytest.raises(InvalidTransition):
            sm.transition(6)  # Deploy cannot go back to Build


# ---------------------------------------------------------------------------
# Phase instructions
# ---------------------------------------------------------------------------


class TestPhaseInstructions:
    """Tests for build and deploy phase instructions."""

    def test_build_instructions_enabled(self) -> None:
        config = DeploymentConfig(enabled=True, target="aks", artifact_registry="reg.io")
        inst = build_phase_instructions(config)
        assert inst["name"] == "Build & Package"
        assert "artifact_registry" in inst
        assert "aks" in inst["description"]

    def test_build_instructions_skipped(self) -> None:
        config = DeploymentConfig(enabled=True, skip_build=True)
        inst = build_phase_instructions(config)
        assert "Skipped" in inst["name"]

    def test_deploy_instructions_enabled(self) -> None:
        config = DeploymentConfig(
            enabled=True,
            target="ecs",
            environments=["dev", "staging"],
            smoke_test_command="curl localhost/health",
        )
        inst = deploy_phase_instructions(config)
        assert inst["name"] == "Deploy & Verify"
        assert "smoke_test_command" in inst
        assert "ecs" in inst["description"]

    def test_deploy_instructions_skipped(self) -> None:
        config = DeploymentConfig(enabled=True, skip_deploy=True)
        inst = deploy_phase_instructions(config)
        assert "Skipped" in inst["name"]

    def test_deploy_instructions_disabled(self) -> None:
        config = DeploymentConfig(enabled=False)
        inst = deploy_phase_instructions(config)
        assert "Skipped" in inst["name"]


# ---------------------------------------------------------------------------
# Result serialization
# ---------------------------------------------------------------------------


class TestResultSerialization:
    """Tests for build and deploy result serialization."""

    def test_build_result_default(self) -> None:
        result = BuildResult()
        d = result.to_dict()
        assert d["outcome"] == "skipped"
        assert d["artifact_id"] == ""

    def test_build_result_success(self) -> None:
        result = BuildResult(
            outcome=BuildOutcome.SUCCESS.value,
            artifact_id="sha256:abc123",
            security_scan_passed=True,
        )
        d = result.to_dict()
        assert d["outcome"] == "success"
        assert d["artifact_id"] == "sha256:abc123"

    def test_deploy_result_default(self) -> None:
        result = DeployResult()
        d = result.to_dict()
        assert d["outcome"] == "skipped"
        assert d["rollback_performed"] is False

    def test_deploy_result_rolled_back(self) -> None:
        result = DeployResult(
            outcome=DeployOutcome.ROLLED_BACK.value,
            environment="staging",
            rollback_performed=True,
        )
        d = result.to_dict()
        assert d["outcome"] == "rolled_back"
        assert d["rollback_performed"] is True

    def test_deployment_phase_result(self) -> None:
        result = DeploymentPhaseResult(
            build=BuildResult(outcome="success"),
            deployments=[
                DeployResult(outcome="success", environment="dev"),
                DeployResult(outcome="success", environment="staging"),
            ],
            overall_success=True,
        )
        d = result.to_dict()
        assert d["overall_success"] is True
        assert len(d["deployments"]) == 2


# ---------------------------------------------------------------------------
# Config integration
# ---------------------------------------------------------------------------


class TestConfigIntegration:
    """Tests for deployment config in OrchestratorConfig."""

    def test_default_config_has_deployment(self) -> None:
        config = OrchestratorConfig()
        assert config.deployment.enabled is False

    def test_config_with_deployment(self) -> None:
        config = OrchestratorConfig(
            deployment=DeploymentConfig(enabled=True, target="aks"),
        )
        assert config.deployment.enabled is True
        assert config.deployment.target == "aks"

    def test_load_config_without_deployment(self, tmp_path) -> None:
        yaml_file = tmp_path / "project.yaml"
        yaml_file.write_text(
            "governance:\n  parallel_coders: 3\n"
        )
        config = load_config(yaml_file)
        assert config.deployment.enabled is False

    def test_load_config_with_deployment(self, tmp_path) -> None:
        yaml_file = tmp_path / "project.yaml"
        yaml_file.write_text(
            "governance:\n"
            "  parallel_coders: 3\n"
            "  deployment:\n"
            "    enabled: true\n"
            "    target: aks\n"
            "    environments:\n"
            "      - dev\n"
            "      - staging\n"
        )
        config = load_config(yaml_file)
        assert config.deployment.enabled is True
        assert config.deployment.target == "aks"
        assert config.deployment.environments == ["dev", "staging"]


# ---------------------------------------------------------------------------
# Session deployment fields
# ---------------------------------------------------------------------------


class TestSessionDeploymentFields:
    """Tests for deployment state in PersistedSession."""

    def test_session_has_deployment_fields(self) -> None:
        session = PersistedSession(session_id="test")
        assert session.build_artifact_id == ""
        assert session.build_artifact_digest == ""
        assert session.security_scan_passed is False
        assert session.deployment_environment == ""
        assert session.deployment_status == ""
        assert session.verification_passed is False

    def test_session_deployment_fields_set(self) -> None:
        session = PersistedSession(session_id="test")
        session.build_artifact_id = "sha256:abc"
        session.deployment_environment = "staging"
        session.verification_passed = True
        assert session.build_artifact_id == "sha256:abc"
        assert session.deployment_environment == "staging"
        assert session.verification_passed is True
