"""Tests for governance.engine.orchestrator.topology — spawn DAG enforcement."""

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.engine.orchestrator.__main__ import main
from governance.engine.orchestrator.config import OrchestratorConfig
from governance.engine.orchestrator.topology import (
    DispatchDescriptor,
    MaxConcurrentExceeded,
    PhasePersonaMismatch,
    TopologyPolicy,
    TopologyRule,
    TopologyViolation,
    create_dispatch_descriptor,
    load_topology,
    validate_dispatch,
    validate_phase_persona,
)


# ---------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------


@pytest.fixture
def topology_yaml(tmp_path):
    """Write a minimal topology file and return its path."""
    content = textwrap.dedent("""\
        topology:
          project_manager:
            can_spawn:
              - devops_engineer
              - tech_lead
            max_concurrent:
              devops_engineer: 1
              tech_lead: 3
          tech_lead:
            can_spawn:
              - coder
              - iac_engineer
            max_concurrent:
              coder: 5
          devops_engineer:
            can_spawn: []
          coder:
            can_spawn: []

        phase_bindings:
          1: devops_engineer
          2: tech_lead
          3: tech_lead
          4: devops_engineer
          5: devops_engineer
    """)
    p = tmp_path / "agent-topology.yaml"
    p.write_text(content)
    return str(p)


@pytest.fixture
def policy(topology_yaml):
    return load_topology(topology_yaml)


# ---------------------------------------------------------------
# Unit tests — TopologyPolicy
# ---------------------------------------------------------------


class TestTopologyPolicyLoad:
    def test_load_basic(self, policy):
        assert "project_manager" in policy.rules
        assert "tech_lead" in policy.rules
        assert "devops_engineer" in policy.rules
        assert "coder" in policy.rules

    def test_can_spawn(self, policy):
        assert policy.can_spawn("project_manager", "devops_engineer") is True
        assert policy.can_spawn("project_manager", "tech_lead") is True
        assert policy.can_spawn("project_manager", "coder") is False
        assert policy.can_spawn("tech_lead", "coder") is True
        assert policy.can_spawn("tech_lead", "devops_engineer") is False
        assert policy.can_spawn("devops_engineer", "coder") is False
        assert policy.can_spawn("coder", "coder") is False

    def test_get_max_concurrent(self, policy):
        assert policy.get_max_concurrent("project_manager", "devops_engineer") == 1
        assert policy.get_max_concurrent("project_manager", "tech_lead") == 3
        assert policy.get_max_concurrent("tech_lead", "coder") == 5
        # No limit configured
        assert policy.get_max_concurrent("devops_engineer", "coder") is None

    def test_get_allowed_children(self, policy):
        assert set(policy.get_allowed_children("project_manager")) == {"devops_engineer", "tech_lead"}
        assert set(policy.get_allowed_children("tech_lead")) == {"coder", "iac_engineer"}
        assert policy.get_allowed_children("coder") == []
        assert policy.get_allowed_children("devops_engineer") == []

    def test_unknown_persona_cannot_spawn(self, policy):
        assert policy.can_spawn("unknown_persona", "coder") is False
        assert policy.get_allowed_children("unknown_persona") == []

    def test_phase_bindings(self, policy):
        assert policy.get_phase_executor(1) == "devops_engineer"
        assert policy.get_phase_executor(2) == "tech_lead"
        assert policy.get_phase_executor(3) == "tech_lead"
        assert policy.get_phase_executor(4) == "devops_engineer"
        assert policy.get_phase_executor(5) == "devops_engineer"
        assert policy.get_phase_executor(6) is None  # Not bound
        assert policy.get_phase_executor(99) is None

    def test_load_with_config_overrides(self, topology_yaml):
        policy = load_topology(
            topology_yaml,
            config_overrides={"parallel_tech_leads": 10, "parallel_coders": 20},
        )
        assert policy.get_max_concurrent("project_manager", "tech_lead") == 10
        assert policy.get_max_concurrent("tech_lead", "coder") == 20

    def test_load_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_topology(str(tmp_path / "nonexistent.yaml"))

    def test_load_empty_topology_raises(self, tmp_path):
        p = tmp_path / "empty.yaml"
        p.write_text("other_key: true\n")
        with pytest.raises(ValueError, match="No 'topology' section"):
            load_topology(str(p))


# ---------------------------------------------------------------
# Unit tests — validate_dispatch
# ---------------------------------------------------------------


class TestValidateDispatch:
    def test_valid_spawn_pm_to_devops(self, policy):
        # Should not raise
        validate_dispatch(policy, "project_manager", "devops_engineer", 0)

    def test_valid_spawn_pm_to_tech_lead(self, policy):
        validate_dispatch(policy, "project_manager", "tech_lead", 0)

    def test_invalid_spawn_pm_to_coder(self, policy):
        with pytest.raises(TopologyViolation) as exc_info:
            validate_dispatch(policy, "project_manager", "coder", 0)
        assert "project_manager" in str(exc_info.value)
        assert "coder" in str(exc_info.value)

    def test_invalid_spawn_coder_to_anything(self, policy):
        with pytest.raises(TopologyViolation):
            validate_dispatch(policy, "coder", "tech_lead", 0)

    def test_invalid_spawn_devops_to_anything(self, policy):
        with pytest.raises(TopologyViolation):
            validate_dispatch(policy, "devops_engineer", "coder", 0)

    def test_max_concurrent_not_exceeded(self, policy):
        validate_dispatch(policy, "project_manager", "devops_engineer", 0)

    def test_max_concurrent_exceeded(self, policy):
        with pytest.raises(MaxConcurrentExceeded) as exc_info:
            validate_dispatch(policy, "project_manager", "devops_engineer", 1)
        assert exc_info.value.limit == 1
        assert exc_info.value.current == 1

    def test_max_concurrent_tech_leads(self, policy):
        # 3 is the limit
        validate_dispatch(policy, "project_manager", "tech_lead", 2)  # OK
        with pytest.raises(MaxConcurrentExceeded):
            validate_dispatch(policy, "project_manager", "tech_lead", 3)  # Exceeds

    def test_max_concurrent_coders(self, policy):
        validate_dispatch(policy, "tech_lead", "coder", 4)  # OK
        with pytest.raises(MaxConcurrentExceeded):
            validate_dispatch(policy, "tech_lead", "coder", 5)  # Exceeds


# ---------------------------------------------------------------
# Unit tests — validate_phase_persona
# ---------------------------------------------------------------


class TestValidatePhasePersona:
    def test_correct_persona_phase_1(self, policy):
        validate_phase_persona(policy, 1, "devops_engineer")  # Should not raise

    def test_correct_persona_phase_2(self, policy):
        validate_phase_persona(policy, 2, "tech_lead")

    def test_wrong_persona_phase_1(self, policy):
        with pytest.raises(PhasePersonaMismatch) as exc_info:
            validate_phase_persona(policy, 1, "project_manager")
        assert exc_info.value.phase == 1
        assert exc_info.value.expected_persona == "devops_engineer"
        assert exc_info.value.actual_persona == "project_manager"

    def test_wrong_persona_phase_2(self, policy):
        with pytest.raises(PhasePersonaMismatch):
            validate_phase_persona(policy, 2, "coder")

    def test_unbound_phase_allows_any(self, policy):
        validate_phase_persona(policy, 6, "coder")  # Phase 6 unbound
        validate_phase_persona(policy, 99, "project_manager")


# ---------------------------------------------------------------
# Unit tests — DispatchDescriptor
# ---------------------------------------------------------------


class TestDispatchDescriptor:
    def test_create_descriptor(self):
        desc = create_dispatch_descriptor(
            persona="tech_lead",
            session_id="session-abc",
            parent_task_id="pm-001",
            assign={"task": "plan", "issues": ["#42"]},
        )
        assert desc.persona == "tech_lead"
        assert desc.session_id == "session-abc"
        assert desc.parent_task_id == "pm-001"
        assert desc.assign == {"task": "plan", "issues": ["#42"]}
        assert desc.self_register_required is True
        assert desc.dispatch_id.startswith("dispatch-")
        assert desc.task_id.startswith("tech_lead-")

    def test_descriptor_to_dict(self):
        desc = create_dispatch_descriptor(
            persona="coder",
            session_id="session-xyz",
            parent_task_id="tl-001",
        )
        d = desc.to_dict()
        assert d["persona"] == "coder"
        assert d["session_id"] == "session-xyz"
        assert d["parent_task_id"] == "tl-001"
        assert d["self_register_required"] is True
        assert "dispatch_id" in d
        assert "task_id" in d

    def test_descriptor_default_assign(self):
        desc = create_dispatch_descriptor(
            persona="devops_engineer",
            session_id="session-1",
            parent_task_id="pm-1",
        )
        assert desc.assign == {}


# ---------------------------------------------------------------
# Unit tests — TopologyViolation exception
# ---------------------------------------------------------------


class TestExceptions:
    def test_topology_violation_message(self):
        exc = TopologyViolation("project_manager", "coder", "Valid targets: [devops_engineer, tech_lead]")
        assert "project_manager" in str(exc)
        assert "coder" in str(exc)
        assert "Valid targets" in str(exc)

    def test_max_concurrent_exceeded_message(self):
        exc = MaxConcurrentExceeded("project_manager", "devops_engineer", 1, 1)
        assert "limit is 1" in str(exc)
        assert "currently 1" in str(exc)

    def test_phase_persona_mismatch_message(self):
        exc = PhasePersonaMismatch(2, "tech_lead", "project_manager")
        assert "Phase 2" in str(exc)
        assert "tech_lead" in str(exc)
        assert "project_manager" in str(exc)


# ---------------------------------------------------------------
# Integration — CLI dispatch command
# ---------------------------------------------------------------


@pytest.fixture
def work_dir(tmp_path):
    (tmp_path / "checkpoints").mkdir()
    (tmp_path / "sessions").mkdir()
    (tmp_path / "audit").mkdir()
    return tmp_path


@pytest.fixture
def pm_config(work_dir):
    return OrchestratorConfig(
        parallel_coders=5,
        use_project_manager=True,
        parallel_tech_leads=3,
        checkpoint_dir=str(work_dir / "checkpoints"),
        audit_log_dir=str(work_dir / "audit"),
        session_dir=str(work_dir / "sessions"),
    )


@pytest.fixture
def std_config(work_dir):
    return OrchestratorConfig(
        parallel_coders=5,
        use_project_manager=False,
        checkpoint_dir=str(work_dir / "checkpoints"),
        audit_log_dir=str(work_dir / "audit"),
        session_dir=str(work_dir / "sessions"),
    )


@pytest.fixture
def config_path(work_dir):
    p = work_dir / "project.yaml"
    p.write_text(
        "governance:\n"
        "  parallel_coders: 5\n"
        "  use_project_manager: true\n"
    )
    return str(p)


def _patch_git():
    return patch(
        "governance.engine.orchestrator.step_runner.StepRunner._get_current_branch",
        return_value="main",
    )


def _patch_checkpoint():
    return patch(
        "governance.engine.orchestrator.step_runner.CheckpointManager.load_latest",
        return_value=None,
    )


def _patch_config(cfg):
    return patch(
        "governance.engine.orchestrator.__main__.load_config",
        return_value=cfg,
    )


class TestDispatchCommand:
    def test_dispatch_valid_pm_to_devops(self, pm_config, config_path, topology_yaml, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(pm_config):
            main(["init", "--config", config_path, "--session-id", "disp-test"])
            capsys.readouterr()

            # Register PM first
            main([
                "register", "--persona", "project_manager",
                "--task-id", "pm-001",
                "--session-id", "disp-test",
                "--config", config_path,
            ])
            capsys.readouterr()

            # Dispatch devops_engineer from PM — should succeed
            with patch(
                "governance.engine.orchestrator.topology._DEFAULT_TOPOLOGY_PATH",
                topology_yaml,
            ):
                exit_code = main([
                    "dispatch",
                    "--persona", "devops_engineer",
                    "--parent", "pm-001",
                    "--session-id", "disp-test",
                    "--config", config_path,
                    "--topology-path", topology_yaml,
                ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["persona"] == "devops_engineer"
        assert output["parent_task_id"] == "pm-001"
        assert output["self_register_required"] is True
        assert "dispatch_id" in output
        assert "task_id" in output

    def test_dispatch_invalid_pm_to_coder(self, pm_config, config_path, topology_yaml, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(pm_config):
            main(["init", "--config", config_path, "--session-id", "disp-inv"])
            capsys.readouterr()

            main([
                "register", "--persona", "project_manager",
                "--task-id", "pm-001",
                "--session-id", "disp-inv",
                "--config", config_path,
            ])
            capsys.readouterr()

            with patch(
                "governance.engine.orchestrator.topology._DEFAULT_TOPOLOGY_PATH",
                topology_yaml,
            ):
                exit_code = main([
                    "dispatch",
                    "--persona", "coder",
                    "--parent", "pm-001",
                    "--session-id", "disp-inv",
                    "--config", config_path,
                    "--topology-path", topology_yaml,
                ])
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out)
        assert "error" in output
        assert "project_manager" in output["error"]
        assert "coder" in output["error"]

    def test_dispatch_unregistered_parent_fails(self, pm_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(pm_config):
            main(["init", "--config", config_path, "--session-id", "disp-unreg"])
            capsys.readouterr()

            exit_code = main([
                "dispatch",
                "--persona", "devops_engineer",
                "--parent", "nonexistent",
                "--session-id", "disp-unreg",
                "--config", config_path,
            ])
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out)
        assert "error" in output
        assert "not registered" in output["error"]

    def test_dispatch_standard_mode_allows_any(self, std_config, config_path, capsys):
        """Standard mode (PM off) skips topology validation."""
        with _patch_git(), _patch_checkpoint(), _patch_config(std_config):
            main(["init", "--config", config_path, "--session-id", "disp-std"])
            capsys.readouterr()

            main([
                "register", "--persona", "coder",
                "--task-id", "coder-1",
                "--session-id", "disp-std",
                "--config", config_path,
            ])
            capsys.readouterr()

            # In standard mode, even coder spawning tech_lead should work
            exit_code = main([
                "dispatch",
                "--persona", "tech_lead",
                "--parent", "coder-1",
                "--session-id", "disp-std",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["persona"] == "tech_lead"


class TestStepWithAgentBinding:
    def test_step_with_correct_agent(self, pm_config, config_path, topology_yaml, capsys):
        """Phase 1 completed by devops_engineer should succeed."""
        with _patch_git(), _patch_checkpoint(), _patch_config(pm_config):
            main(["init", "--config", config_path, "--session-id", "bind-ok"])
            capsys.readouterr()

            main([
                "register", "--persona", "devops_engineer",
                "--task-id", "devops-1",
                "--session-id", "bind-ok",
                "--config", config_path,
            ])
            capsys.readouterr()

            with patch(
                "governance.engine.orchestrator.topology._DEFAULT_TOPOLOGY_PATH",
                topology_yaml,
            ):
                exit_code = main([
                    "step", "--complete", "1",
                    "--result", '{"issues_selected": ["#42"]}',
                    "--agent", "devops-1",
                    "--session-id", "bind-ok",
                    "--config", config_path,
                ])
        assert exit_code == 0

    def test_step_with_wrong_agent(self, pm_config, config_path, topology_yaml, capsys):
        """Phase 1 completed by project_manager should fail binding check."""
        with _patch_git(), _patch_checkpoint(), _patch_config(pm_config):
            main(["init", "--config", config_path, "--session-id", "bind-fail"])
            capsys.readouterr()

            main([
                "register", "--persona", "devops_engineer",
                "--task-id", "devops-1",
                "--session-id", "bind-fail",
                "--config", config_path,
            ])
            capsys.readouterr()

            main([
                "register", "--persona", "project_manager",
                "--task-id", "pm-1",
                "--session-id", "bind-fail",
                "--config", config_path,
            ])
            capsys.readouterr()

            with patch(
                "governance.engine.orchestrator.topology._DEFAULT_TOPOLOGY_PATH",
                topology_yaml,
            ):
                exit_code = main([
                    "step", "--complete", "1",
                    "--result", '{"issues_selected": ["#42"]}',
                    "--agent", "pm-1",
                    "--session-id", "bind-fail",
                    "--config", config_path,
                ])
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out)
        assert "error" in output
        assert "Phase-persona binding" in output["error"]

    def test_step_without_agent_skips_binding(self, pm_config, config_path, capsys):
        """When --agent is not provided, no binding check occurs."""
        with _patch_git(), _patch_checkpoint(), _patch_config(pm_config):
            main(["init", "--config", config_path, "--session-id", "bind-skip"])
            capsys.readouterr()

            main([
                "register", "--persona", "devops_engineer",
                "--task-id", "devops-1",
                "--session-id", "bind-skip",
                "--config", config_path,
            ])
            capsys.readouterr()

            # No --agent flag: should work without binding validation
            exit_code = main([
                "step", "--complete", "1",
                "--result", '{"issues_selected": ["#42"]}',
                "--session-id", "bind-skip",
                "--config", config_path,
            ])
        assert exit_code == 0
