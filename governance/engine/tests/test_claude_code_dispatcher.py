"""Tests for governance.engine.orchestrator.claude_code_dispatcher — instruction generation."""

import pytest

from governance.engine.orchestrator.claude_code_dispatcher import (
    ClaudeCodeDispatcher,
    _PERSONA_PATHS,
)
from governance.engine.orchestrator.dispatcher import (
    AgentPersona,
    AgentResult,
    AgentTask,
)


@pytest.fixture
def dispatcher():
    return ClaudeCodeDispatcher(session_id="test-session")


def _make_task(persona=AgentPersona.CODER, correlation_id="issue-42", branch="feat/42"):
    return AgentTask(
        persona=persona,
        correlation_id=correlation_id,
        plan_content="Plan for issue",
        issue_body="Fix the bug",
        branch=branch,
        session_id="test-session",
    )


class TestDispatch:
    def test_dispatch_returns_task_ids(self, dispatcher):
        tasks = [_make_task(), _make_task(correlation_id="issue-43")]
        task_ids = dispatcher.dispatch(tasks)
        assert len(task_ids) == 2
        assert all(tid.startswith("cc-") for tid in task_ids)

    def test_dispatch_unique_ids(self, dispatcher):
        tasks = [_make_task() for _ in range(5)]
        task_ids = dispatcher.dispatch(tasks)
        assert len(set(task_ids)) == 5

    def test_dispatch_stores_instructions(self, dispatcher):
        tasks = [_make_task()]
        task_ids = dispatcher.dispatch(tasks)
        assert len(dispatcher.all_instructions) == 1
        inst = dispatcher.all_instructions[task_ids[0]]
        assert inst.correlation_id == "issue-42"
        assert inst.persona == "coder"

    def test_dispatch_sets_persona_path(self, dispatcher):
        tasks = [_make_task(persona=AgentPersona.TESTER)]
        task_ids = dispatcher.dispatch(tasks)
        inst = dispatcher.all_instructions[task_ids[0]]
        assert inst.persona_path == _PERSONA_PATHS[AgentPersona.TESTER]

    def test_dispatch_sets_plan_path(self, dispatcher):
        tasks = [_make_task()]
        task_ids = dispatcher.dispatch(tasks)
        inst = dispatcher.all_instructions[task_ids[0]]
        assert inst.plan_path == ".governance/plans/issue-42.md"


class TestGetInstructions:
    def test_get_instructions_as_dicts(self, dispatcher):
        tasks = [_make_task(), _make_task(correlation_id="issue-43")]
        dispatcher.dispatch(tasks)
        instructions = dispatcher.get_instructions()
        assert len(instructions) == 2
        assert all(isinstance(i, dict) for i in instructions)
        assert instructions[0]["persona"] == "coder"

    def test_get_pending_instructions_all_pending(self, dispatcher):
        tasks = [_make_task()]
        dispatcher.dispatch(tasks)
        pending = dispatcher.get_pending_instructions()
        assert len(pending) == 1

    def test_get_pending_instructions_excludes_completed(self, dispatcher):
        tasks = [_make_task(), _make_task(correlation_id="issue-43")]
        task_ids = dispatcher.dispatch(tasks)
        # Record result for first task
        dispatcher.record_result(task_ids[0], AgentResult(
            correlation_id="issue-42", success=True
        ))
        pending = dispatcher.get_pending_instructions()
        assert len(pending) == 1
        assert pending[0]["correlation_id"] == "issue-43"


class TestCollect:
    def test_collect_returns_pending_for_unfinished(self, dispatcher):
        tasks = [_make_task()]
        task_ids = dispatcher.dispatch(tasks)
        results = dispatcher.collect(task_ids)
        assert len(results) == 1
        assert results[0].success is False
        assert results[0].error == "pending"

    def test_collect_returns_recorded_results(self, dispatcher):
        tasks = [_make_task()]
        task_ids = dispatcher.dispatch(tasks)
        dispatcher.record_result(task_ids[0], AgentResult(
            correlation_id="issue-42",
            success=True,
            branch="feat/42",
            summary="Done",
        ))
        results = dispatcher.collect(task_ids)
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].branch == "feat/42"


class TestRecordResult:
    def test_record_result(self, dispatcher):
        tasks = [_make_task()]
        task_ids = dispatcher.dispatch(tasks)
        dispatcher.record_result(task_ids[0], AgentResult(
            correlation_id="issue-42", success=True
        ))
        assert len(dispatcher.all_results) == 1


class TestCancel:
    def test_cancel_is_noop(self, dispatcher):
        tasks = [_make_task()]
        task_ids = dispatcher.dispatch(tasks)
        dispatcher.cancel(task_ids)  # Should not raise


class TestPersonaPaths:
    def test_all_personas_have_paths(self):
        for persona in AgentPersona:
            assert persona in _PERSONA_PATHS
