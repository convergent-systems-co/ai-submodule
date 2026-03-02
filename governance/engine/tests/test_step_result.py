"""Tests for governance.engine.orchestrator.step_result — serialization round-trips."""

import pytest

from governance.engine.orchestrator.step_result import DispatchInstruction, StepResult


class TestStepResultSerialization:
    def test_to_dict_minimal(self):
        result = StepResult(session_id="s1", action="execute_phase", phase=1, tier="green")
        d = result.to_dict()
        assert d["session_id"] == "s1"
        assert d["action"] == "execute_phase"
        assert d["phase"] == 1
        assert d["tier"] == "green"

    def test_to_dict_strips_empty_optional_fields(self):
        result = StepResult(session_id="s1", action="done")
        d = result.to_dict()
        assert "instructions" not in d
        assert "tasks" not in d
        assert "gate_block" not in d
        assert "shutdown_info" not in d
        assert "error" not in d

    def test_to_dict_preserves_nonempty_fields(self):
        result = StepResult(
            session_id="s1",
            action="execute_phase",
            instructions={"name": "Pre-flight"},
            gate_block="--- CONTEXT GATE ---",
            error="something went wrong",
        )
        d = result.to_dict()
        assert d["instructions"] == {"name": "Pre-flight"}
        assert d["gate_block"] == "--- CONTEXT GATE ---"
        assert d["error"] == "something went wrong"

    def test_round_trip(self):
        original = StepResult(
            session_id="s1",
            action="dispatch",
            phase=3,
            tier="yellow",
            instructions={"name": "Parallel Dispatch", "outputs_expected": ["task_ids"]},
            tasks=[{"task_id": "cc-abc", "persona": "coder"}],
            gate_block="--- GATE ---",
            signals={"tool_calls": 25, "turns": 10},
            work={"issues_selected": ["#42"]},
            loop_count=2,
        )
        d = original.to_dict()
        restored = StepResult.from_dict(d)
        assert restored.session_id == original.session_id
        assert restored.action == original.action
        assert restored.phase == original.phase
        assert restored.tier == original.tier
        assert restored.instructions == original.instructions
        assert restored.tasks == original.tasks
        assert restored.loop_count == original.loop_count

    def test_from_dict_ignores_unknown_keys(self):
        d = {"session_id": "s1", "action": "done", "unknown_field": "xyz"}
        result = StepResult.from_dict(d)
        assert result.session_id == "s1"
        assert result.action == "done"

    def test_from_dict_defaults(self):
        result = StepResult.from_dict({})
        assert result.session_id == ""
        assert result.action == ""
        assert result.phase == 0
        assert result.tier == "green"

    def test_shutdown_result(self):
        result = StepResult(
            session_id="s1",
            action="shutdown",
            shutdown_info={"reason": "Orange tier", "tier": "orange"},
        )
        d = result.to_dict()
        assert d["action"] == "shutdown"
        assert d["shutdown_info"]["tier"] == "orange"

    def test_tasks_list_serialization(self):
        result = StepResult(
            session_id="s1",
            action="dispatch",
            tasks=[
                {"task_id": "cc-1", "persona": "coder", "branch_name": "feat/1"},
                {"task_id": "cc-2", "persona": "coder", "branch_name": "feat/2"},
            ],
        )
        d = result.to_dict()
        assert len(d["tasks"]) == 2
        assert d["tasks"][0]["task_id"] == "cc-1"


class TestDispatchInstruction:
    def test_defaults(self):
        inst = DispatchInstruction(
            task_id="cc-1",
            correlation_id="issue-42",
            persona="coder",
            persona_path="governance/personas/agentic/coder.md",
            plan_path=".governance/plans/issue-42.md",
            branch_name="feat/42",
            issue_ref="#42",
            issue_body="Fix the bug",
        )
        assert inst.task_id == "cc-1"
        assert inst.constraints == {}

    def test_with_constraints(self):
        inst = DispatchInstruction(
            task_id="cc-1",
            correlation_id="issue-42",
            persona="coder",
            persona_path="",
            plan_path="",
            branch_name="",
            issue_ref="",
            issue_body="",
            constraints={"timeout": 300},
        )
        assert inst.constraints["timeout"] == 300
