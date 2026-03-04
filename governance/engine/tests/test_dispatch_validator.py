"""Tests for governance.engine.orchestrator.dispatch_validator."""

import pytest

from governance.engine.orchestrator.dispatcher import AgentPersona, AgentTask
from governance.engine.orchestrator.dispatch_validator import (
    DispatchValidationResult,
    validate_branch_names,
    validate_dispatch,
    validate_no_duplicates,
    validate_task_count,
    validate_worktree_required,
)


def _make_task(
    correlation_id="issue-42",
    branch="itsfwcp/feat/42/fix-bug",
    persona=AgentPersona.CODER,
):
    return AgentTask(
        persona=persona,
        correlation_id=correlation_id,
        plan_content="Plan",
        issue_body="Body",
        branch=branch,
        session_id="test-session",
    )


class TestValidateTaskCount:
    def test_valid_count(self):
        tasks = [_make_task() for _ in range(3)]
        errors = validate_task_count(tasks, coder_min=1, coder_max=5)
        assert errors == []

    def test_below_minimum(self):
        tasks = [_make_task()]
        errors = validate_task_count(tasks, coder_min=3, coder_max=5)
        assert len(errors) == 1
        assert "below minimum" in errors[0]

    def test_above_maximum(self):
        tasks = [_make_task() for _ in range(6)]
        errors = validate_task_count(tasks, coder_min=1, coder_max=5)
        assert len(errors) == 1
        assert "exceeds maximum" in errors[0]

    def test_unlimited_max(self):
        tasks = [_make_task() for _ in range(100)]
        errors = validate_task_count(tasks, coder_min=1, coder_max=-1)
        assert errors == []

    def test_exact_min(self):
        tasks = [_make_task() for _ in range(3)]
        errors = validate_task_count(tasks, coder_min=3, coder_max=5)
        assert errors == []

    def test_exact_max(self):
        tasks = [_make_task() for _ in range(5)]
        errors = validate_task_count(tasks, coder_min=1, coder_max=5)
        assert errors == []

    def test_empty_below_minimum(self):
        errors = validate_task_count([], coder_min=1, coder_max=5)
        assert len(errors) == 1


class TestValidateWorktreeRequired:
    def test_sets_flag_when_required(self):
        tasks = [_make_task()]
        result = validate_worktree_required(tasks, require_worktree=True)
        assert result[0].constraints["require_worktree"] is True

    def test_does_not_set_flag_when_not_required(self):
        tasks = [_make_task()]
        result = validate_worktree_required(tasks, require_worktree=False)
        assert "require_worktree" not in result[0].constraints

    def test_preserves_existing_constraints(self):
        task = _make_task()
        task.constraints["timeout"] = 300
        result = validate_worktree_required([task], require_worktree=True)
        assert result[0].constraints["timeout"] == 300
        assert result[0].constraints["require_worktree"] is True


class TestValidateBranchNames:
    def test_valid_branch(self):
        tasks = [_make_task(branch="itsfwcp/feat/42/fix-bug")]
        errors = validate_branch_names(tasks, "{network_id}/{type}/{number}/{name}")
        assert errors == []

    def test_invalid_branch(self):
        tasks = [_make_task(branch="bad-branch")]
        errors = validate_branch_names(tasks, "{network_id}/{type}/{number}/{name}")
        assert len(errors) == 1
        assert "does not match pattern" in errors[0]

    def test_multiple_tasks_mixed(self):
        tasks = [
            _make_task(branch="itsfwcp/feat/42/fix-bug"),
            _make_task(branch="bad-branch"),
            _make_task(branch="itsfwcp/fix/43/another"),
        ]
        errors = validate_branch_names(tasks, "{network_id}/{type}/{number}/{name}")
        assert len(errors) == 1

    def test_branch_with_dots(self):
        tasks = [_make_task(branch="itsfwcp/feat/42/v1.2.3")]
        errors = validate_branch_names(tasks, "{network_id}/{type}/{number}/{name}")
        assert errors == []


class TestValidateNoDuplicates:
    def test_no_duplicates(self):
        tasks = [
            _make_task(correlation_id="issue-42"),
            _make_task(correlation_id="issue-43"),
        ]
        errors = validate_no_duplicates(tasks)
        assert errors == []

    def test_with_duplicates(self):
        tasks = [
            _make_task(correlation_id="issue-42"),
            _make_task(correlation_id="issue-42"),
        ]
        errors = validate_no_duplicates(tasks)
        assert len(errors) == 1
        assert "Duplicate correlation_id 'issue-42'" in errors[0]

    def test_empty_list(self):
        errors = validate_no_duplicates([])
        assert errors == []


class TestValidateDispatch:
    def test_all_valid(self):
        tasks = [
            _make_task(correlation_id="issue-42", branch="itsfwcp/feat/42/fix"),
            _make_task(correlation_id="issue-43", branch="itsfwcp/feat/43/fix"),
        ]
        config = {
            "coder_min": 1,
            "coder_max": 5,
            "require_worktree": True,
            "branch_pattern": "{network_id}/{type}/{number}/{name}",
        }
        result = validate_dispatch(tasks, config)
        assert result.valid is True
        assert result.errors == []
        assert tasks[0].constraints["require_worktree"] is True

    def test_multiple_errors(self):
        tasks = [
            _make_task(correlation_id="issue-42", branch="bad-branch"),
            _make_task(correlation_id="issue-42", branch="also-bad"),
        ]
        config = {
            "coder_min": 1,
            "coder_max": 5,
            "require_worktree": False,
            "branch_pattern": "{network_id}/{type}/{number}/{name}",
        }
        result = validate_dispatch(tasks, config)
        assert result.valid is False
        assert len(result.errors) >= 2  # duplicate + branch errors

    def test_no_branch_pattern(self):
        tasks = [_make_task(branch="anything")]
        config = {
            "coder_min": 1,
            "coder_max": 5,
            "require_worktree": False,
            "branch_pattern": "",
        }
        result = validate_dispatch(tasks, config)
        assert result.valid is True

    def test_defaults_when_missing_config_keys(self):
        tasks = [_make_task()]
        result = validate_dispatch(tasks, {})
        assert result.valid is True

    def test_result_contains_tasks(self):
        tasks = [_make_task()]
        result = validate_dispatch(tasks, {})
        assert len(result.tasks) == 1
