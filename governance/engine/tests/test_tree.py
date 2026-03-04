"""Tests for governance.engine.orchestrator.tree — workload tree builder."""

import json
from unittest.mock import patch

import pytest

from governance.engine.orchestrator.__main__ import main
from governance.engine.orchestrator.config import OrchestratorConfig
from governance.engine.orchestrator.session import PersistedSession
from governance.engine.orchestrator.tree import build_tree, render_ascii_tree


# ---------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------

@pytest.fixture
def default_config():
    return OrchestratorConfig()


@pytest.fixture
def custom_config():
    return OrchestratorConfig(
        parallel_coders=6,
        parallel_tech_leads=4,
        use_project_manager=True,
        coder_min=2,
        coder_max=8,
    )


@pytest.fixture
def empty_session():
    return PersistedSession(session_id="test-empty")


@pytest.fixture
def session_with_issues():
    return PersistedSession(
        session_id="test-issues",
        current_phase=3,
        loop_count=1,
        issues_selected=["#42", "#43"],
        issues_done=["#41"],
        plans={"#42": ".artifacts/plans/42.md", "#43": ".artifacts/plans/43.md"},
    )


@pytest.fixture
def session_with_prs():
    return PersistedSession(
        session_id="test-prs",
        current_phase=4,
        prs_created=["pr-100", "pr-101"],
        prs_resolved=["pr-99"],
        prs_remaining=["pr-100"],
    )


@pytest.fixture
def session_with_dispatch_results():
    return PersistedSession(
        session_id="test-dispatch",
        current_phase=4,
        issues_selected=["#42"],
        dispatch_results=[
            {
                "persona": "coder",
                "correlation_id": "issue-42",
                "branch": "itsfwcp/fix/42/fix-bug",
                "success": True,
                "task_id": "cc-abc123",
            },
            {
                "persona": "test-evaluator",
                "correlation_id": "pr-108",
                "branch": "",
                "success": False,
                "task_id": "cc-def456",
            },
        ],
    )


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
        coder_min=1,
        coder_max=5,
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


# ---------------------------------------------------------------
# Unit tests — build_tree
# ---------------------------------------------------------------

class TestBuildTreeEmpty:
    def test_empty_session_produces_valid_tree(self, empty_session, default_config):
        tree = build_tree(empty_session, default_config)
        assert tree["session_id"] == "test-empty"
        assert tree["phase"] == 0
        assert tree["loop_count"] == 0
        assert tree["agents"] == []
        assert tree["issues"]["selected"] == []
        assert tree["issues"]["done"] == []
        assert tree["prs"]["created"] == []
        assert tree["summary"]["total_agents"] == 0

    def test_empty_session_has_config(self, empty_session, default_config):
        tree = build_tree(empty_session, default_config)
        assert tree["config"]["parallel_coders"] == 5
        assert tree["config"]["coder_min"] == 1
        assert tree["config"]["coder_max"] == 5
        assert tree["config"]["use_project_manager"] is False

    def test_empty_session_has_ascii_tree(self, empty_session, default_config):
        tree = build_tree(empty_session, default_config)
        assert isinstance(tree["ascii_tree"], str)
        assert "Session: test-empty" in tree["ascii_tree"]


class TestBuildTreeWithIssues:
    def test_issues_appear_in_tree(self, session_with_issues, default_config):
        tree = build_tree(session_with_issues, default_config)
        assert tree["issues"]["selected"] == ["#42", "#43"]
        assert tree["issues"]["done"] == ["#41"]
        assert "#42" in tree["issues"]["plans"]

    def test_phase_name_resolved(self, session_with_issues, default_config):
        tree = build_tree(session_with_issues, default_config)
        assert tree["phase"] == 3
        assert tree["phase_name"] == "Parallel Dispatch"

    def test_summary_issue_counts(self, session_with_issues, default_config):
        tree = build_tree(session_with_issues, default_config)
        assert tree["summary"]["issues_selected"] == 2
        assert tree["summary"]["issues_done"] == 1


class TestBuildTreeWithPRs:
    def test_prs_appear_in_tree(self, session_with_prs, default_config):
        tree = build_tree(session_with_prs, default_config)
        assert tree["prs"]["created"] == ["pr-100", "pr-101"]
        assert tree["prs"]["resolved"] == ["pr-99"]
        assert tree["prs"]["remaining"] == ["pr-100"]

    def test_summary_pr_counts(self, session_with_prs, default_config):
        tree = build_tree(session_with_prs, default_config)
        assert tree["summary"]["prs_created"] == 2
        assert tree["summary"]["prs_resolved"] == 1
        assert tree["summary"]["prs_remaining"] == 1


class TestBuildTreeWithDispatchResults:
    def test_agents_from_dispatch_results(self, session_with_dispatch_results, default_config):
        tree = build_tree(session_with_dispatch_results, default_config)
        assert len(tree["agents"]) == 2
        assert tree["agents"][0]["persona"] == "coder"
        assert tree["agents"][0]["status"] == "completed"
        assert tree["agents"][1]["persona"] == "test-evaluator"
        assert tree["agents"][1]["status"] == "failed"

    def test_summary_agent_counts(self, session_with_dispatch_results, default_config):
        tree = build_tree(session_with_dispatch_results, default_config)
        assert tree["summary"]["total_agents"] == 2
        assert tree["summary"]["completed"] == 1
        assert tree["summary"]["failed"] == 1
        assert tree["summary"]["pending"] == 0
        assert tree["summary"]["by_persona"] == {"coder": 1, "test-evaluator": 1}


class TestBuildTreeWithCustomConfig:
    def test_custom_config_values(self, empty_session, custom_config):
        tree = build_tree(empty_session, custom_config)
        assert tree["config"]["parallel_coders"] == 6
        assert tree["config"]["parallel_tech_leads"] == 4
        assert tree["config"]["use_project_manager"] is True
        assert tree["config"]["coder_min"] == 2
        assert tree["config"]["coder_max"] == 8


# ---------------------------------------------------------------
# Unit tests — render_ascii_tree
# ---------------------------------------------------------------

class TestRenderAsciiTree:
    def test_renders_without_errors(self, empty_session, default_config):
        result = render_ascii_tree(empty_session, default_config, [], {}, {})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_agents_shows_placeholder(self, empty_session, default_config):
        result = render_ascii_tree(empty_session, default_config, [], {}, {})
        assert "(no agents dispatched)" in result

    def test_agents_rendered_with_connectors(self, empty_session, default_config):
        agents = [
            {"persona": "coder", "issue_ref": "issue-42", "branch": "fix/42", "status": "completed"},
            {"persona": "test-evaluator", "issue_ref": "pr-108", "branch": "", "status": "pending"},
        ]
        result = render_ascii_tree(empty_session, default_config, agents, {}, {})
        assert "+-- Coder [issue-42]" in result
        assert "\\-- Test-evaluator [pr-108]" in result
        assert "(completed)" in result
        assert "(pending)" in result

    def test_single_agent_uses_last_connector(self, empty_session, default_config):
        agents = [
            {"persona": "coder", "issue_ref": "issue-1", "branch": "b", "status": "pending"},
        ]
        result = render_ascii_tree(empty_session, default_config, agents, {}, {})
        assert "\\-- Coder [issue-1]" in result

    def test_header_contains_session_and_phase(self, session_with_issues, default_config):
        result = render_ascii_tree(session_with_issues, default_config, [], {"selected": ["#42"], "done": []}, {})
        assert "Session: test-issues" in result
        assert "Phase: 3" in result
        assert "Parallel Dispatch" in result
        assert "Loop: 1" in result

    def test_footer_shows_issue_and_pr_counts(self, empty_session, default_config):
        issues = {"selected": ["#1", "#2"], "done": ["#0"]}
        prs = {"created": ["pr-10"], "resolved": []}
        result = render_ascii_tree(empty_session, default_config, [], issues, prs)
        assert "Issues: 2 selected, 1 done" in result
        assert "PRs: 1 created, 0 resolved" in result

    def test_config_line_present(self, empty_session, default_config):
        result = render_ascii_tree(empty_session, default_config, [], {}, {})
        assert "Config: parallel_coders=5" in result
        assert "coder_min=1" in result
        assert "coder_max=5" in result


# ---------------------------------------------------------------
# CLI integration — tree command
# ---------------------------------------------------------------

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


class TestTreeCommand:
    def test_tree_active_session(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "tree-test"])
            capsys.readouterr()

            exit_code = main([
                "tree",
                "--session-id", "tree-test",
                "--config", config_path,
            ])
        assert exit_code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["session_id"] == "tree-test"
        assert "ascii_tree" in output
        assert "agents" in output
        assert "config" in output
        assert "summary" in output

    def test_tree_no_session(self, isolated_config, config_path, capsys):
        with _patch_config(isolated_config):
            exit_code = main([
                "tree",
                "--session-id", "nonexistent",
                "--config", config_path,
            ])
        assert exit_code == 0  # returns JSON with error field
        output = json.loads(capsys.readouterr().out)
        assert "error" in output

    def test_tree_json_serializable(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "serial-test"])
            capsys.readouterr()

            main([
                "tree",
                "--session-id", "serial-test",
                "--config", config_path,
            ])
        raw = capsys.readouterr().out
        parsed = json.loads(raw)
        # Round-trip: re-serialize should work
        assert json.dumps(parsed, indent=2)

    def test_tree_after_step_shows_issues(self, isolated_config, config_path, capsys):
        with _patch_git(), _patch_checkpoint(), _patch_config(isolated_config):
            main(["init", "--config", config_path, "--session-id", "step-tree"])
            capsys.readouterr()

            main([
                "step", "--complete", "1",
                "--result", '{"issues_selected": ["#42", "#43"]}',
                "--session-id", "step-tree",
                "--config", config_path,
            ])
            capsys.readouterr()

            main([
                "tree",
                "--session-id", "step-tree",
                "--config", config_path,
            ])
        output = json.loads(capsys.readouterr().out)
        assert "#42" in output["issues"]["selected"]
        assert "#43" in output["issues"]["selected"]
