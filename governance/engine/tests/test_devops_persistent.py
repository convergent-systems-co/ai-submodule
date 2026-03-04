"""Tests for #726 DevOps Engineer persistent framework and #714 PM topology enforcement.

Covers:
- heartbeat_at field on RegisteredAgent
- record_heartbeat() and is_alive() on AgentRegistry
- validate_topology_hard() on AgentRegistry
- heartbeat CLI subcommand
- devops_task_id / devops_last_heartbeat on PersistedSession
- devops_heartbeat_interval_seconds / devops_idle_backoff_max_seconds on OrchestratorConfig
- auto_spawn_required in Phase 1 PM mode result
- devops_respawn_required on stale session restore
- validate_dispatch_persona() and validate_tech_lead_count() in dispatch_validator
- PM mode params wired into validate_dispatch()
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from governance.engine.orchestrator.__main__ import main
from governance.engine.orchestrator.agent_registry import AgentRegistry, RegisteredAgent
from governance.engine.orchestrator.config import OrchestratorConfig
from governance.engine.orchestrator.dispatch_validator import (
    validate_dispatch,
    validate_dispatch_persona,
    validate_tech_lead_count,
)
from governance.engine.orchestrator.dispatcher import AgentPersona, AgentTask
from governance.engine.orchestrator.session import PersistedSession
from governance.engine.orchestrator.step_runner import StepRunner


# ---------------------------------------------------------------
# Fixtures
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
        parallel_coders=3,
        use_project_manager=True,
        parallel_tech_leads=2,
        checkpoint_dir=str(work_dir / "checkpoints"),
        audit_log_dir=str(work_dir / "audit"),
        session_dir=str(work_dir / "sessions"),
    )


@pytest.fixture
def std_config(work_dir):
    return OrchestratorConfig(
        parallel_coders=3,
        use_project_manager=False,
        checkpoint_dir=str(work_dir / "checkpoints"),
        audit_log_dir=str(work_dir / "audit"),
        session_dir=str(work_dir / "sessions"),
    )


@pytest.fixture
def config_path(work_dir):
    p = work_dir / "project.yaml"
    p.write_text("governance:\n  parallel_coders: 3\n")
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


# ---------------------------------------------------------------
# RegisteredAgent.heartbeat_at
# ---------------------------------------------------------------


class TestRegisteredAgentHeartbeat:
    def test_heartbeat_at_default_empty(self):
        agent = RegisteredAgent(persona="devops_engineer", task_id="t-1")
        assert agent.heartbeat_at == ""

    def test_heartbeat_at_can_be_set(self):
        agent = RegisteredAgent(persona="devops_engineer", task_id="t-1")
        agent.heartbeat_at = "2026-01-01T00:00:00+00:00"
        assert agent.heartbeat_at == "2026-01-01T00:00:00+00:00"

    def test_heartbeat_at_serializes(self):
        reg = AgentRegistry()
        agent = reg.register("devops_engineer", "devops-1")
        agent.heartbeat_at = "2026-01-01T12:00:00+00:00"
        d = reg.to_dict()
        assert d["devops-1"]["heartbeat_at"] == "2026-01-01T12:00:00+00:00"

    def test_heartbeat_at_round_trips(self):
        reg = AgentRegistry()
        agent = reg.register("devops_engineer", "devops-1")
        agent.heartbeat_at = "2026-03-01T08:00:00+00:00"
        restored = AgentRegistry.from_dict(reg.to_dict())
        assert restored.get_agent("devops-1").heartbeat_at == "2026-03-01T08:00:00+00:00"


# ---------------------------------------------------------------
# AgentRegistry.record_heartbeat() and is_alive()
# ---------------------------------------------------------------


class TestAgentRegistryHeartbeat:
    def test_record_heartbeat_updates_timestamp(self):
        reg = AgentRegistry()
        reg.register("devops_engineer", "devops-1")
        agent = reg.record_heartbeat("devops-1")
        assert agent.heartbeat_at != ""
        # Timestamp should be recent
        ts = datetime.fromisoformat(agent.heartbeat_at)
        assert (datetime.now(timezone.utc) - ts).total_seconds() < 5

    def test_record_heartbeat_unknown_agent(self):
        reg = AgentRegistry()
        with pytest.raises(KeyError, match="not registered"):
            reg.record_heartbeat("nonexistent")

    def test_is_alive_after_heartbeat(self):
        reg = AgentRegistry()
        reg.register("devops_engineer", "devops-1")
        reg.record_heartbeat("devops-1")
        assert reg.is_alive("devops-1", threshold_seconds=300) is True

    def test_is_alive_no_heartbeat(self):
        reg = AgentRegistry()
        reg.register("devops_engineer", "devops-1")
        # Never sent a heartbeat
        assert reg.is_alive("devops-1") is False

    def test_is_alive_stale_heartbeat(self):
        reg = AgentRegistry()
        reg.register("devops_engineer", "devops-1")
        # Set heartbeat to 10 minutes ago
        old_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        reg._agents["devops-1"].heartbeat_at = old_time
        assert reg.is_alive("devops-1", threshold_seconds=300) is False

    def test_is_alive_unknown_agent(self):
        reg = AgentRegistry()
        with pytest.raises(KeyError, match="not registered"):
            reg.is_alive("nonexistent")

    def test_is_alive_custom_threshold(self):
        reg = AgentRegistry()
        reg.register("devops_engineer", "devops-1")
        # Set heartbeat to 30 seconds ago
        recent_time = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
        reg._agents["devops-1"].heartbeat_at = recent_time
        assert reg.is_alive("devops-1", threshold_seconds=60) is True
        assert reg.is_alive("devops-1", threshold_seconds=10) is False


# ---------------------------------------------------------------
# AgentRegistry.validate_topology_hard()
# ---------------------------------------------------------------


class TestValidateTopologyHard:
    def test_standard_mode_always_empty(self):
        reg = AgentRegistry()
        errors = reg.validate_topology_hard(2, use_project_manager=False)
        assert errors == []

    def test_phase_2_without_devops(self):
        reg = AgentRegistry()
        errors = reg.validate_topology_hard(2, use_project_manager=True)
        assert len(errors) == 1
        assert errors[0].rule == "missing_devops_engineer"
        assert "devops_engineer" in errors[0].missing_personas

    def test_phase_2_with_devops(self):
        reg = AgentRegistry()
        reg.register("devops_engineer", "devops-1")
        errors = reg.validate_topology_hard(2, use_project_manager=True)
        assert errors == []

    def test_phase_4_without_tech_lead(self):
        reg = AgentRegistry()
        errors = reg.validate_topology_hard(4, use_project_manager=True)
        assert len(errors) == 1
        assert errors[0].rule == "missing_tech_lead"
        assert "tech_lead" in errors[0].missing_personas

    def test_phase_4_with_tech_lead(self):
        reg = AgentRegistry()
        reg.register("tech_lead", "tl-1")
        errors = reg.validate_topology_hard(4, use_project_manager=True)
        assert errors == []

    def test_other_phases_no_errors(self):
        reg = AgentRegistry()
        for phase in [1, 3, 5, 6, 7]:
            errors = reg.validate_topology_hard(phase, use_project_manager=True)
            assert errors == [], f"Unexpected error at phase {phase}"


# ---------------------------------------------------------------
# PersistedSession fields
# ---------------------------------------------------------------


class TestPersistedSessionDevOpsFields:
    def test_default_devops_fields(self):
        session = PersistedSession()
        assert session.devops_task_id == ""
        assert session.devops_last_heartbeat == ""

    def test_set_devops_fields(self):
        session = PersistedSession()
        session.devops_task_id = "devops-1"
        session.devops_last_heartbeat = "2026-01-01T00:00:00+00:00"
        assert session.devops_task_id == "devops-1"
        assert session.devops_last_heartbeat == "2026-01-01T00:00:00+00:00"


# ---------------------------------------------------------------
# OrchestratorConfig fields
# ---------------------------------------------------------------


class TestOrchestratorConfigDevOpsFields:
    def test_default_heartbeat_interval(self):
        config = OrchestratorConfig()
        assert config.devops_heartbeat_interval_seconds == 60

    def test_default_idle_backoff_max(self):
        config = OrchestratorConfig()
        assert config.devops_idle_backoff_max_seconds == 300

    def test_custom_heartbeat_interval(self):
        config = OrchestratorConfig(devops_heartbeat_interval_seconds=120)
        assert config.devops_heartbeat_interval_seconds == 120


# ---------------------------------------------------------------
# validate_dispatch_persona()
# ---------------------------------------------------------------


def _make_task(persona=AgentPersona.CODER, branch="net/feat/1/fix", cid="issue-1"):
    return AgentTask(
        persona=persona,
        correlation_id=cid,
        plan_content="test plan",
        issue_body="test body",
        branch=branch,
        session_id="test-session",
    )


class TestValidateDispatchPersona:
    def test_standard_mode_allows_coder(self):
        tasks = [_make_task(persona=AgentPersona.CODER)]
        errors = validate_dispatch_persona(tasks, use_project_manager=False)
        assert errors == []

    def test_pm_mode_rejects_coder(self):
        tasks = [_make_task(persona=AgentPersona.CODER)]
        errors = validate_dispatch_persona(tasks, use_project_manager=True)
        assert len(errors) == 1
        assert "Coder directly" in errors[0]

    def test_pm_mode_allows_tech_lead(self):
        tasks = [_make_task(persona=AgentPersona.TECH_LEAD)]
        errors = validate_dispatch_persona(tasks, use_project_manager=True)
        assert errors == []

    def test_pm_mode_rejects_multiple_coders(self):
        tasks = [
            _make_task(persona=AgentPersona.CODER, cid="issue-1"),
            _make_task(persona=AgentPersona.CODER, cid="issue-2"),
        ]
        errors = validate_dispatch_persona(tasks, use_project_manager=True)
        assert len(errors) == 2


# ---------------------------------------------------------------
# validate_tech_lead_count()
# ---------------------------------------------------------------


class TestValidateTechLeadCount:
    def test_unlimited(self):
        tasks = [_make_task(persona=AgentPersona.TECH_LEAD, cid=f"issue-{i}") for i in range(10)]
        errors = validate_tech_lead_count(tasks, parallel_tech_leads=-1)
        assert errors == []

    def test_within_limit(self):
        tasks = [_make_task(persona=AgentPersona.TECH_LEAD)]
        errors = validate_tech_lead_count(tasks, parallel_tech_leads=3)
        assert errors == []

    def test_exceeds_limit(self):
        tasks = [_make_task(persona=AgentPersona.TECH_LEAD, cid=f"issue-{i}") for i in range(4)]
        errors = validate_tech_lead_count(tasks, parallel_tech_leads=3)
        assert len(errors) == 1
        assert "exceeds" in errors[0]

    def test_coders_not_counted(self):
        tasks = [_make_task(persona=AgentPersona.CODER, cid=f"issue-{i}") for i in range(5)]
        errors = validate_tech_lead_count(tasks, parallel_tech_leads=1)
        assert errors == []


# ---------------------------------------------------------------
# validate_dispatch() with PM mode params
# ---------------------------------------------------------------


class TestValidateDispatchPMMode:
    def test_pm_mode_rejects_coder_via_validate_dispatch(self):
        tasks = [_make_task(persona=AgentPersona.CODER)]
        config = {
            "coder_min": 1,
            "coder_max": 5,
            "require_worktree": True,
            "use_project_manager": True,
            "parallel_tech_leads": 3,
        }
        result = validate_dispatch(tasks, config)
        assert not result.valid
        assert any("Coder directly" in e for e in result.errors)

    def test_pm_mode_tech_lead_limit_via_validate_dispatch(self):
        tasks = [_make_task(persona=AgentPersona.TECH_LEAD, cid=f"issue-{i}") for i in range(4)]
        config = {
            "coder_min": 1,
            "coder_max": 10,
            "require_worktree": True,
            "use_project_manager": True,
            "parallel_tech_leads": 3,
        }
        result = validate_dispatch(tasks, config)
        assert not result.valid
        assert any("exceeds" in e for e in result.errors)


# ---------------------------------------------------------------
# StepRunner.record_heartbeat() and heartbeat CLI
# ---------------------------------------------------------------


class TestStepRunnerHeartbeat:
    def test_record_heartbeat_via_runner(self, pm_config):
        runner = StepRunner(pm_config, session_id="hb-test")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")
            result = runner.record_heartbeat("devops-1")
        assert result["heartbeat_recorded"] is True
        assert result["persona"] == "devops_engineer"
        assert result["heartbeat_at"] != ""

    def test_heartbeat_updates_session_devops_fields(self, pm_config):
        runner = StepRunner(pm_config, session_id="hb-persist")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")
            runner.record_heartbeat("devops-1")
        assert runner._session.devops_task_id == "devops-1"
        assert runner._session.devops_last_heartbeat != ""


class TestHeartbeatCLI:
    def test_heartbeat_command(self, pm_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(pm_config):
            main(["init", "--config", config_path, "--session-id", "hb-cli"])
            capsys.readouterr()

            main([
                "register",
                "--persona", "devops_engineer",
                "--task-id", "devops-1",
                "--session-id", "hb-cli",
                "--config", config_path,
            ])
            capsys.readouterr()

            exit_code = main([
                "heartbeat",
                "--agent", "devops-1",
                "--session-id", "hb-cli",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["heartbeat_recorded"] is True
        assert output["persona"] == "devops_engineer"

    def test_heartbeat_unknown_agent(self, pm_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(pm_config):
            main(["init", "--config", config_path, "--session-id", "hb-unknown"])
            capsys.readouterr()

            exit_code = main([
                "heartbeat",
                "--agent", "nonexistent",
                "--session-id", "hb-unknown",
                "--config", config_path,
            ])
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out)
        assert "error" in output


# ---------------------------------------------------------------
# Phase 1 auto_spawn_required in PM mode
# ---------------------------------------------------------------


class TestAutoSpawnRequired:
    def test_pm_phase1_has_auto_spawn_required(self, pm_config):
        runner = StepRunner(pm_config, session_id="spawn-test")
        with _patch_git(), _patch_checkpoint():
            result = runner.init_session()
        inst = result.instructions
        assert inst.get("auto_spawn_required") is True
        devops = inst["devops_background_task"]
        assert devops["auto_spawn_required"] is True
        assert devops["heartbeat_interval_seconds"] == 60
        assert devops["idle_backoff_max_seconds"] == 300

    def test_standard_mode_no_auto_spawn(self, std_config):
        runner = StepRunner(std_config, session_id="no-spawn")
        with _patch_git(), _patch_checkpoint():
            result = runner.init_session()
        assert result.instructions.get("auto_spawn_required") is None


# ---------------------------------------------------------------
# Stale DevOps detection on session restore
# ---------------------------------------------------------------


class TestStaleDevOpsDetection:
    def test_stale_devops_flagged_on_restore(self, pm_config):
        """When DevOps heartbeat is stale, restore flags devops_respawn_required."""
        runner = StepRunner(pm_config, session_id="stale-test")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")

        # Manually set a stale heartbeat
        runner._session.devops_task_id = "devops-1"
        old_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        runner._session.devops_last_heartbeat = old_time
        runner._registry._agents["devops-1"].heartbeat_at = old_time
        runner._persist()

        # Restore session (simulates context reset)
        runner2 = StepRunner(pm_config, session_id="stale-test")
        with _patch_git(), _patch_checkpoint():
            result = runner2.init_session()

        assert result.work.get("devops_respawn_required") is True
        assert result.work.get("devops_stale_task_id") == "devops-1"

    def test_fresh_devops_not_flagged(self, pm_config):
        """When DevOps heartbeat is fresh, no respawn flag."""
        runner = StepRunner(pm_config, session_id="fresh-test")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")
            runner.record_heartbeat("devops-1")

        # Set session devops fields
        runner._session.devops_task_id = "devops-1"
        runner._persist()

        # Restore
        runner2 = StepRunner(pm_config, session_id="fresh-test")
        with _patch_git(), _patch_checkpoint():
            result = runner2.init_session()

        assert result.work.get("devops_respawn_required") is not True


# ---------------------------------------------------------------
# Hard topology enforcement in step_runner._advance_to()
# ---------------------------------------------------------------


class TestHardTopologyEnforcement:
    def test_phase_2_blocked_without_devops(self, pm_config):
        """Stepping from phase 1 to 2 without DevOps raises RuntimeError."""
        runner = StepRunner(pm_config, session_id="hard-p2")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            with pytest.raises(RuntimeError, match="topology enforcement"):
                runner.step(1, {"issues_selected": ["#42"]})

    def test_phase_2_allowed_with_devops(self, pm_config):
        """Stepping from phase 1 to 2 with DevOps succeeds."""
        runner = StepRunner(pm_config, session_id="hard-p2-ok")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")
            result = runner.step(1, {"issues_selected": ["#42"]})
        assert result.phase == 2

    def test_phase_4_blocked_without_tech_lead(self, pm_config):
        """Stepping from phase 3 to 4 without Tech Lead raises RuntimeError."""
        runner = StepRunner(pm_config, session_id="hard-p4")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")
            runner.step(1, {"issues_selected": ["#42"]})
            runner.step(2, {"plans": {"#42": "plan"}})
            with pytest.raises(RuntimeError, match="topology enforcement"):
                runner.step(3, {"dispatched_task_ids": []})

    def test_phase_4_allowed_with_tech_lead_and_coder(self, pm_config):
        """Stepping from phase 3 to 4 with Tech Lead + Coder succeeds."""
        runner = StepRunner(pm_config, session_id="hard-p4-ok")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")
            runner.step(1, {"issues_selected": ["#42"]})
            runner.register_agent("tech_lead", "tl-1")
            runner.register_agent("coder", "coder-1", parent_task_id="tl-1")
            runner.step(2, {"plans": {"#42": "plan"}})
            result = runner.step(3, {"dispatched_task_ids": ["cc-1"]})
        assert result.phase == 4

    def test_standard_mode_no_enforcement(self, std_config):
        """Standard mode allows all transitions without topology checks."""
        runner = StepRunner(std_config, session_id="std-no-enforce")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            result = runner.step(1, {"issues_selected": ["#42"]})
        assert result.phase == 2  # No error
