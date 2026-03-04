"""Tests for governance.engine.orchestrator.agent_registry — agent topology tracking."""

import json
from unittest.mock import patch

import pytest

from governance.engine.orchestrator.__main__ import main
from governance.engine.orchestrator.agent_registry import (
    AgentRegistry,
    AgentStatus,
    RegisteredAgent,
    TopologyWarning,
)
from governance.engine.orchestrator.config import OrchestratorConfig


# ---------------------------------------------------------------
# Unit tests — AgentRegistry basics
# ---------------------------------------------------------------


class TestAgentRegistryBasics:
    def test_empty_registry(self):
        reg = AgentRegistry()
        assert reg.agent_count == 0
        assert reg.all_agents == {}

    def test_register_agent(self):
        reg = AgentRegistry()
        agent = reg.register("devops_engineer", "task-1")
        assert agent.persona == "devops_engineer"
        assert agent.task_id == "task-1"
        assert agent.status == "registered"
        assert reg.agent_count == 1

    def test_register_with_correlation_id(self):
        reg = AgentRegistry()
        agent = reg.register("coder", "task-2", correlation_id="issue-42")
        assert agent.correlation_id == "issue-42"

    def test_register_with_parent_task_id(self):
        reg = AgentRegistry()
        agent = reg.register("coder", "task-2", parent_task_id="task-1")
        assert agent.parent_task_id == "task-1"

    def test_register_duplicate_raises(self):
        reg = AgentRegistry()
        reg.register("devops_engineer", "task-1")
        with pytest.raises(ValueError, match="already registered"):
            reg.register("devops_engineer", "task-1")

    def test_get_agent(self):
        reg = AgentRegistry()
        reg.register("coder", "task-1")
        agent = reg.get_agent("task-1")
        assert agent is not None
        assert agent.persona == "coder"

    def test_get_agent_not_found(self):
        reg = AgentRegistry()
        assert reg.get_agent("nonexistent") is None


class TestAgentRegistryQueries:
    def test_get_agents_by_persona(self):
        reg = AgentRegistry()
        reg.register("coder", "task-1")
        reg.register("coder", "task-2")
        reg.register("devops_engineer", "task-3")
        coders = reg.get_agents_by_persona("coder")
        assert len(coders) == 2

    def test_get_agents_by_persona_empty(self):
        reg = AgentRegistry()
        reg.register("coder", "task-1")
        devops = reg.get_agents_by_persona("devops_engineer")
        assert devops == []

    def test_get_agents_by_status(self):
        reg = AgentRegistry()
        reg.register("coder", "task-1")
        reg.register("coder", "task-2")
        reg.update_status("task-1", "running")
        registered = reg.get_agents_by_status("registered")
        running = reg.get_agents_by_status("running")
        assert len(registered) == 1
        assert len(running) == 1

    def test_all_agents_is_copy(self):
        reg = AgentRegistry()
        reg.register("coder", "task-1")
        all_agents = reg.all_agents
        all_agents["task-1"] = None  # Modify copy
        assert reg.get_agent("task-1") is not None  # Original intact


class TestAgentStatusUpdates:
    def test_update_status_to_running(self):
        reg = AgentRegistry()
        reg.register("coder", "task-1")
        agent = reg.update_status("task-1", "running")
        assert agent.status == "running"

    def test_update_status_to_completed(self):
        reg = AgentRegistry()
        reg.register("coder", "task-1")
        agent = reg.update_status("task-1", "completed")
        assert agent.status == "completed"

    def test_update_status_to_failed(self):
        reg = AgentRegistry()
        reg.register("coder", "task-1")
        agent = reg.update_status("task-1", "failed")
        assert agent.status == "failed"

    def test_update_status_invalid(self):
        reg = AgentRegistry()
        reg.register("coder", "task-1")
        with pytest.raises(ValueError, match="Invalid status"):
            reg.update_status("task-1", "bogus")

    def test_update_status_unknown_task(self):
        reg = AgentRegistry()
        with pytest.raises(KeyError, match="not registered"):
            reg.update_status("nonexistent", "running")


# ---------------------------------------------------------------
# Unit tests — Topology validation
# ---------------------------------------------------------------


class TestTopologyValidationStandardMode:
    """When use_project_manager=False, validation always passes."""

    def test_no_warnings_standard_mode(self):
        reg = AgentRegistry()
        warnings = reg.validate_topology(2, use_project_manager=False)
        assert warnings == []

    def test_no_warnings_standard_mode_phase_4(self):
        reg = AgentRegistry()
        warnings = reg.validate_topology(4, use_project_manager=False)
        assert warnings == []


class TestTopologyValidationPMMode:
    """When use_project_manager=True, validate PM agent topology."""

    def test_phase_2_warns_missing_devops(self):
        reg = AgentRegistry()
        warnings = reg.validate_topology(2, use_project_manager=True)
        assert len(warnings) == 1
        assert "devops_engineer" in warnings[0].missing

    def test_phase_2_no_warning_with_devops(self):
        reg = AgentRegistry()
        reg.register("devops_engineer", "devops-1")
        warnings = reg.validate_topology(2, use_project_manager=True)
        assert warnings == []

    def test_phase_4_warns_missing_tech_lead_and_coder(self):
        reg = AgentRegistry()
        warnings = reg.validate_topology(4, use_project_manager=True)
        assert len(warnings) == 1
        assert "tech_lead" in warnings[0].missing
        assert "coder" in warnings[0].missing

    def test_phase_4_warns_missing_coder_only(self):
        reg = AgentRegistry()
        reg.register("tech_lead", "cm-1")
        warnings = reg.validate_topology(4, use_project_manager=True)
        assert len(warnings) == 1
        assert "coder" in warnings[0].missing
        assert "tech_lead" not in warnings[0].missing

    def test_phase_4_warns_missing_tech_lead_only(self):
        reg = AgentRegistry()
        reg.register("coder", "coder-1")
        warnings = reg.validate_topology(4, use_project_manager=True)
        assert len(warnings) == 1
        assert "tech_lead" in warnings[0].missing
        assert "coder" not in warnings[0].missing

    def test_phase_4_no_warning_with_full_topology(self):
        reg = AgentRegistry()
        reg.register("devops_engineer", "devops-1")
        reg.register("tech_lead", "cm-1")
        reg.register("coder", "coder-1", parent_task_id="cm-1")
        warnings = reg.validate_topology(4, use_project_manager=True)
        assert warnings == []

    def test_other_phases_no_warnings(self):
        """Phases 1, 3, 5 do not have topology checks."""
        reg = AgentRegistry()
        for phase in [1, 3, 5]:
            warnings = reg.validate_topology(phase, use_project_manager=True)
            assert warnings == [], f"Unexpected warning at phase {phase}"


# ---------------------------------------------------------------
# Unit tests — TopologyWarning
# ---------------------------------------------------------------


class TestTopologyWarning:
    def test_to_dict(self):
        w = TopologyWarning(phase=4, missing=["tech_lead"], detail="test")
        d = w.to_dict()
        assert d["phase"] == 4
        assert d["missing"] == ["tech_lead"]
        assert d["detail"] == "test"

    def test_repr(self):
        w = TopologyWarning(phase=2, missing=["devops_engineer"], detail="oops")
        assert "phase=2" in repr(w)
        assert "devops_engineer" in repr(w)


# ---------------------------------------------------------------
# Unit tests — Serialization (persistence round-trip)
# ---------------------------------------------------------------


class TestAgentRegistrySerialization:
    def test_to_dict_empty(self):
        reg = AgentRegistry()
        assert reg.to_dict() == {}

    def test_to_dict_with_agents(self):
        reg = AgentRegistry()
        reg.register("devops_engineer", "devops-1", correlation_id="bg")
        reg.register("tech_lead", "cm-1")
        d = reg.to_dict()
        assert "devops-1" in d
        assert "cm-1" in d
        assert d["devops-1"]["persona"] == "devops_engineer"
        assert d["devops-1"]["correlation_id"] == "bg"

    def test_from_dict_restores_agents(self):
        reg = AgentRegistry()
        reg.register("coder", "task-1", correlation_id="issue-42")
        reg.update_status("task-1", "running")
        reg.register("devops_engineer", "task-2")

        d = reg.to_dict()
        restored = AgentRegistry.from_dict(d)

        assert restored.agent_count == 2
        agent1 = restored.get_agent("task-1")
        assert agent1.persona == "coder"
        assert agent1.status == "running"
        assert agent1.correlation_id == "issue-42"

    def test_round_trip_json(self):
        """Full round-trip through JSON (simulates session persistence)."""
        reg = AgentRegistry()
        reg.register("devops_engineer", "devops-1")
        reg.register("tech_lead", "cm-1")
        reg.register("coder", "coder-1", parent_task_id="cm-1")
        reg.update_status("devops-1", "completed")

        json_str = json.dumps(reg.to_dict())
        data = json.loads(json_str)
        restored = AgentRegistry.from_dict(data)

        assert restored.agent_count == 3
        assert restored.get_agent("devops-1").status == "completed"
        assert restored.get_agent("coder-1").parent_task_id == "cm-1"

    def test_from_dict_ignores_unknown_fields(self):
        """Unknown fields in serialized data should not cause errors."""
        data = {
            "task-1": {
                "persona": "coder",
                "task_id": "task-1",
                "correlation_id": "",
                "status": "registered",
                "parent_task_id": "",
                "registered_at": "2024-01-01T00:00:00+00:00",
                "unknown_field": "should_be_ignored",
            }
        }
        reg = AgentRegistry.from_dict(data)
        assert reg.agent_count == 1
        assert reg.get_agent("task-1").persona == "coder"


# ---------------------------------------------------------------
# Unit tests — Summary
# ---------------------------------------------------------------


class TestAgentRegistrySummary:
    def test_summary_empty(self):
        reg = AgentRegistry()
        s = reg.summary()
        assert s["total"] == 0
        assert s["by_persona"] == {}
        assert s["by_status"] == {}

    def test_summary_with_agents(self):
        reg = AgentRegistry()
        reg.register("devops_engineer", "devops-1")
        reg.register("tech_lead", "cm-1")
        reg.register("coder", "coder-1")
        reg.register("coder", "coder-2")
        reg.update_status("devops-1", "running")
        reg.update_status("coder-1", "completed")

        s = reg.summary()
        assert s["total"] == 4
        assert s["by_persona"]["coder"] == 2
        assert s["by_persona"]["tech_lead"] == 1
        assert s["by_persona"]["devops_engineer"] == 1
        assert s["by_status"]["registered"] == 2
        assert s["by_status"]["running"] == 1
        assert s["by_status"]["completed"] == 1


# ---------------------------------------------------------------
# Unit tests — RegisteredAgent
# ---------------------------------------------------------------


class TestRegisteredAgent:
    def test_default_values(self):
        agent = RegisteredAgent(persona="coder", task_id="t-1")
        assert agent.status == "registered"
        assert agent.correlation_id == ""
        assert agent.parent_task_id == ""
        assert agent.registered_at != ""

    def test_custom_values(self):
        agent = RegisteredAgent(
            persona="tech_lead",
            task_id="cm-1",
            correlation_id="batch-1",
            status="running",
            parent_task_id="pm-1",
        )
        assert agent.persona == "tech_lead"
        assert agent.correlation_id == "batch-1"
        assert agent.status == "running"


# ---------------------------------------------------------------
# Unit tests — AgentStatus enum
# ---------------------------------------------------------------


class TestAgentStatus:
    def test_all_values(self):
        assert AgentStatus.REGISTERED.value == "registered"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.FAILED.value == "failed"


# ---------------------------------------------------------------
# CLI integration — register command
# ---------------------------------------------------------------


@pytest.fixture
def work_dir(tmp_path):
    (tmp_path / "checkpoints").mkdir()
    (tmp_path / "sessions").mkdir()
    (tmp_path / "audit").mkdir()
    return tmp_path


@pytest.fixture
def isolated_config(work_dir):
    return OrchestratorConfig(
        parallel_coders=3,
        checkpoint_dir=str(work_dir / "checkpoints"),
        audit_log_dir=str(work_dir / "audit"),
        session_dir=str(work_dir / "sessions"),
    )


@pytest.fixture
def pm_config(work_dir):
    return OrchestratorConfig(
        parallel_coders=3,
        use_project_manager=True,
        parallel_tech_leads=2,
        checkpoint_dir=str(work_dir / "checkpoints"),
        audit_log_dir=str(work_dir / "audit"),
        session_dir=str(work_dir / "sessions"),
    )


@pytest.fixture
def config_path(work_dir):
    p = work_dir / "project.yaml"
    p.write_text(
        "governance:\n"
        "  parallel_coders: 3\n"
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


class TestRegisterCommand:
    def test_register_returns_json(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "reg-test"])
            capsys.readouterr()

            exit_code = main([
                "register",
                "--persona", "devops_engineer",
                "--task-id", "devops-1",
                "--session-id", "reg-test",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["registered"] is True
        assert output["persona"] == "devops_engineer"
        assert output["task_id"] == "devops-1"
        assert output["status"] == "registered"

    def test_register_with_correlation_id(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "corr-test"])
            capsys.readouterr()

            exit_code = main([
                "register",
                "--persona", "coder",
                "--task-id", "coder-1",
                "--correlation-id", "issue-42",
                "--session-id", "corr-test",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["correlation_id"] == "issue-42"

    def test_register_duplicate_fails(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "dup-test"])
            capsys.readouterr()

            main([
                "register",
                "--persona", "devops_engineer",
                "--task-id", "devops-1",
                "--session-id", "dup-test",
                "--config", config_path,
            ])
            capsys.readouterr()

            exit_code = main([
                "register",
                "--persona", "devops_engineer",
                "--task-id", "devops-1",
                "--session-id", "dup-test",
                "--config", config_path,
            ])
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out)
        assert "error" in output

    def test_register_no_session_fails(self, isolated_config, config_path, capsys):
        with _patch_config(isolated_config):
            exit_code = main([
                "register",
                "--persona", "coder",
                "--task-id", "coder-1",
                "--session-id", "nonexistent",
                "--config", config_path,
            ])
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out)
        assert "error" in output

    def test_register_persists_across_calls(self, isolated_config, config_path, capsys):
        """Registry state persists in session and survives reload."""
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "persist-test"])
            capsys.readouterr()

            # Register an agent
            main([
                "register",
                "--persona", "devops_engineer",
                "--task-id", "devops-1",
                "--session-id", "persist-test",
                "--config", config_path,
            ])
            capsys.readouterr()

            # Register another (fresh StepRunner load)
            exit_code = main([
                "register",
                "--persona", "tech_lead",
                "--task-id", "cm-1",
                "--session-id", "persist-test",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        # Summary should show both agents
        assert output["registry_summary"]["total"] == 2

    def test_register_shows_in_tree(self, isolated_config, config_path, capsys):
        """Registered agents appear in the tree command output."""
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "tree-reg"])
            capsys.readouterr()

            main([
                "register",
                "--persona", "devops_engineer",
                "--task-id", "devops-1",
                "--session-id", "tree-reg",
                "--config", config_path,
            ])
            capsys.readouterr()

            main([
                "tree",
                "--session-id", "tree-reg",
                "--config", config_path,
            ])
        output = json.loads(capsys.readouterr().out)
        assert len(output["registered_agents"]) == 1
        assert output["registered_agents"][0]["persona"] == "devops_engineer"
        assert "Registered agents: 1" in output["ascii_tree"]


# ---------------------------------------------------------------
# Integration — PM mode topology warnings on phase transitions
# ---------------------------------------------------------------


class TestPMModeTopologyWarnings:
    def test_pm_mode_blocks_phase_2_without_devops(self, pm_config, config_path, capsys):
        """Phase 1->2 transition without DevOps Engineer is hard-blocked (#714)."""
        with _patch_git(), _patch_checkpoint(), _patch_config(pm_config):
            main(["init", "--config", config_path, "--session-id", "pm-warn-1"])
            capsys.readouterr()

            # Complete phase 1 without registering DevOps Engineer
            exit_code = main([
                "step", "--complete", "1",
                "--result", '{"issues_selected": ["#42"]}',
                "--session-id", "pm-warn-1",
                "--config", config_path,
            ])
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out)
        # Should be a hard error, not a warning
        assert "error" in output
        assert "topology enforcement" in output["error"]

    def test_pm_mode_no_warning_with_devops_registered(self, pm_config, config_path, capsys):
        """Phase 1->2 with DevOps Engineer registered produces no warning."""
        with _patch_git(), _patch_checkpoint(), _patch_config(pm_config):
            main(["init", "--config", config_path, "--session-id", "pm-ok-1"])
            capsys.readouterr()

            # Register DevOps Engineer
            main([
                "register",
                "--persona", "devops_engineer",
                "--task-id", "devops-1",
                "--session-id", "pm-ok-1",
                "--config", config_path,
            ])
            capsys.readouterr()

            # Complete phase 1
            exit_code = main([
                "step", "--complete", "1",
                "--result", '{"issues_selected": ["#42"]}',
                "--session-id", "pm-ok-1",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["phase"] == 2
        # No topology warnings when devops is registered
        assert "topology_warnings" not in output or output.get("topology_warnings") == []

    def test_standard_mode_no_topology_warnings(self, isolated_config, config_path, capsys):
        """Standard mode (PM off) never produces topology warnings."""
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "std-test"])
            capsys.readouterr()

            exit_code = main([
                "step", "--complete", "1",
                "--result", '{"issues_selected": ["#42"]}',
                "--session-id", "std-test",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        # Standard mode: no topology warnings at all
        assert "topology_warnings" not in output

    def test_pm_mode_phase_3_to_4_blocks_without_tech_lead(self, pm_config, config_path, capsys):
        """Phase 3->4 in PM mode without tech_leads is hard-blocked (#714)."""
        with _patch_git(), _patch_checkpoint(), _patch_config(pm_config):
            main(["init", "--config", config_path, "--session-id", "pm-p4"])
            capsys.readouterr()

            # Register devops for phase 1->2
            main([
                "register",
                "--persona", "devops_engineer",
                "--task-id", "devops-1",
                "--session-id", "pm-p4",
                "--config", config_path,
            ])
            capsys.readouterr()

            # Walk phases 1->2->3->4
            main([
                "step", "--complete", "1",
                "--result", '{"issues_selected": ["#42"]}',
                "--session-id", "pm-p4",
                "--config", config_path,
            ])
            capsys.readouterr()

            main([
                "step", "--complete", "2",
                "--result", '{"plans": {"#42": ".artifacts/plans/42.md"}}',
                "--session-id", "pm-p4",
                "--config", config_path,
            ])
            capsys.readouterr()

            # Complete phase 3 without registering tech_leads or coders
            exit_code = main([
                "step", "--complete", "3",
                "--result", '{"dispatched_task_ids": []}',
                "--session-id", "pm-p4",
                "--config", config_path,
            ])
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out)
        assert "error" in output
        assert "topology enforcement" in output["error"]
        assert "tech_lead" in output["error"].lower() or "Tech Lead" in output["error"]

    def test_pm_mode_phase_4_no_warning_with_full_topology(self, pm_config, config_path, capsys):
        """Phase 3->4 in PM mode with full topology produces no warnings."""
        with _patch_git(), _patch_checkpoint(), _patch_config(pm_config):
            main(["init", "--config", config_path, "--session-id", "pm-full"])
            capsys.readouterr()

            # Register full topology
            for args in [
                ["register", "--persona", "devops_engineer", "--task-id", "devops-1",
                 "--session-id", "pm-full", "--config", config_path],
                ["register", "--persona", "tech_lead", "--task-id", "cm-1",
                 "--session-id", "pm-full", "--config", config_path],
                ["register", "--persona", "coder", "--task-id", "coder-1",
                 "--parent-task-id", "cm-1",
                 "--session-id", "pm-full", "--config", config_path],
            ]:
                main(args)
                capsys.readouterr()

            # Walk phases 1->2->3->4
            main([
                "step", "--complete", "1",
                "--result", '{"issues_selected": ["#42"]}',
                "--session-id", "pm-full",
                "--config", config_path,
            ])
            capsys.readouterr()

            main([
                "step", "--complete", "2",
                "--result", '{"plans": {"#42": ".artifacts/plans/42.md"}}',
                "--session-id", "pm-full",
                "--config", config_path,
            ])
            capsys.readouterr()

            exit_code = main([
                "step", "--complete", "3",
                "--result", '{"dispatched_task_ids": ["coder-1"]}',
                "--session-id", "pm-full",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["phase"] == 4
        # No topology warnings
        assert "topology_warnings" not in output or output.get("topology_warnings") == []
