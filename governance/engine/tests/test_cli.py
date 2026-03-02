"""Tests for governance.engine.orchestrator.__main__ — CLI integration tests."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.engine.orchestrator.__main__ import main
from governance.engine.orchestrator.config import OrchestratorConfig


@pytest.fixture
def work_dir(tmp_path):
    """Create isolated state directories for CLI tests."""
    (tmp_path / "checkpoints").mkdir()
    (tmp_path / "sessions").mkdir()
    (tmp_path / "audit").mkdir()
    return tmp_path


@pytest.fixture
def isolated_config(work_dir):
    """Return an OrchestratorConfig using tmp_path-based directories."""
    return OrchestratorConfig(
        parallel_coders=3,
        checkpoint_dir=str(work_dir / "checkpoints"),
        audit_log_dir=str(work_dir / "audit"),
        session_dir=str(work_dir / "sessions"),
    )


@pytest.fixture
def config_path(work_dir):
    """Write a project.yaml and return its path."""
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
    """Patch load_config to return the isolated config."""
    return patch(
        "governance.engine.orchestrator.__main__.load_config",
        return_value=cfg,
    )


class TestInitCommand:
    def test_init_returns_json(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            exit_code = main(["init", "--config", config_path, "--session-id", "cli-test"])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["session_id"] == "cli-test"
        assert output["action"] in ("execute_phase", "dispatch", "collect", "merge")

    def test_init_auto_session_id(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            exit_code = main(["init", "--config", config_path])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["session_id"].startswith("session-")


class TestStepCommand:
    def test_step_after_init(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "step-test"])
            capsys.readouterr()

            exit_code = main([
                "step", "--complete", "1",
                "--result", '{"issues_selected": ["#42"]}',
                "--session-id", "step-test",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["phase"] == 2

    def test_step_invalid_json(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "json-test"])
            capsys.readouterr()

            exit_code = main([
                "step", "--complete", "1",
                "--result", "not-json",
                "--session-id", "json-test",
                "--config", config_path,
            ])
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out)
        assert "error" in output

    def test_step_no_session(self, isolated_config, config_path, capsys):
        with _patch_config(isolated_config):
            exit_code = main([
                "step", "--complete", "1",
                "--result", "{}",
                "--session-id", "nonexistent",
                "--config", config_path,
            ])
        assert exit_code == 1
        output = json.loads(capsys.readouterr().out)
        assert "error" in output


class TestSignalCommand:
    def test_signal_tool_call(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "sig-test"])
            capsys.readouterr()

            exit_code = main([
                "signal", "--type", "tool_call", "--count", "5",
                "--session-id", "sig-test",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["tool_calls"] == 5

    def test_signal_turn(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "turn-test"])
            capsys.readouterr()

            exit_code = main([
                "signal", "--type", "turn",
                "--session-id", "turn-test",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["turns"] == 1


class TestGateCommand:
    def test_gate_check(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "gate-test"])
            capsys.readouterr()

            exit_code = main([
                "gate", "--phase", "3",
                "--session-id", "gate-test",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert "tier" in output
        assert "action" in output
        assert "would_shutdown" in output


class TestStatusCommand:
    def test_status_active_session(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "status-test"])
            capsys.readouterr()

            exit_code = main([
                "status",
                "--session-id", "status-test",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["session_id"] == "status-test"

    def test_status_no_session(self, isolated_config, config_path, capsys):
        with _patch_config(isolated_config):
            exit_code = main([
                "status",
                "--session-id", "nonexistent",
                "--config", config_path,
            ])
        output = json.loads(capsys.readouterr().out)
        assert "error" in output


class TestShutdownExitCode:
    def test_shutdown_returns_exit_2(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "shutdown-test"])
            capsys.readouterr()

            # Push signals to orange
            main([
                "signal", "--type", "tool_call", "--count", "70",
                "--session-id", "shutdown-test",
                "--config", config_path,
            ])
            capsys.readouterr()

            exit_code = main([
                "step", "--complete", "1",
                "--result", "{}",
                "--session-id", "shutdown-test",
                "--config", config_path,
            ])
        assert exit_code == 2
