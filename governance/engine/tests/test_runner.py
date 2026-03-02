"""Integration tests for governance.engine.orchestrator.runner — the orchestrator entry point."""

from unittest.mock import patch

import pytest

from governance.engine.orchestrator.config import OrchestratorConfig
from governance.engine.orchestrator.dispatcher import DryRunDispatcher
from governance.engine.orchestrator.runner import OrchestratorRunner, SessionState
from governance.engine.orchestrator.state_machine import ShutdownRequired


@pytest.fixture
def config(tmp_path):
    return OrchestratorConfig(
        parallel_coders=3,
        checkpoint_dir=str(tmp_path / "checkpoints"),
        audit_log_dir=str(tmp_path / "audit"),
    )


@pytest.fixture
def dispatcher():
    return DryRunDispatcher()


@pytest.fixture
def runner(config, dispatcher):
    return OrchestratorRunner(
        config=config,
        session_id="test-session-1",
        dispatcher=dispatcher,
    )


# ---------------------------------------------------------------------------
# Basic lifecycle
# ---------------------------------------------------------------------------


class TestRunnerLifecycle:
    def test_runner_creates_audit_log(self, runner):
        """Runner should create audit log on first event."""
        try:
            runner.run()
        except ShutdownRequired:
            pass  # Expected — Phase 5 checks issue cap
        assert runner.audit.count() > 0

    def test_runner_writes_checkpoints(self, runner, config):
        """Runner writes checkpoint on every phase transition."""
        try:
            runner.run()
        except ShutdownRequired:
            pass
        from pathlib import Path
        checkpoints = list(Path(config.checkpoint_dir).glob("*.json"))
        assert len(checkpoints) > 0

    def test_runner_returns_session_state(self, runner):
        """Runner returns structured session state."""
        # With 0 issues and parallel_coders=3, Phase 5 loop check
        # won't trip the issue cap (0 < 3), so it completes
        result = runner.run()
        assert isinstance(result, SessionState)
        assert result.session_id == "test-session-1"


# ---------------------------------------------------------------------------
# Checkpoint recovery (Phase 0)
# ---------------------------------------------------------------------------


class TestPhase0Recovery:
    def test_no_checkpoint_starts_at_phase1(self, runner):
        """With no checkpoint, Phase 0 returns resume_phase=1."""
        resume = runner._phase_0()
        assert resume == 1

    @patch("governance.engine.orchestrator.checkpoint._is_issue_open", return_value="open")
    def test_checkpoint_restores_state(self, _mock_open, runner):
        """Phase 0 restores work state from checkpoint."""
        runner.checkpoints.write(
            session_id="prev-session",
            branch="main",
            issues_completed=["#1"],
            issues_remaining=["#2", "#3"],
            prs_created=["#10"],
        )
        resume = runner._phase_0()
        assert runner.work.issues_completed == ["#1"]
        assert runner.work.issues_selected == ["#2", "#3"]
        assert runner.work.prs_created == ["#10"]
        assert resume == 3  # PRs created + issues remaining → Phase 3


# ---------------------------------------------------------------------------
# Gate enforcement through runner
# ---------------------------------------------------------------------------


class TestRunnerGateEnforcement:
    def test_orange_triggers_shutdown(self, config, dispatcher):
        """Orange tier at any phase triggers ShutdownRequired."""
        runner = OrchestratorRunner(
            config=config, session_id="s1", dispatcher=dispatcher,
        )
        runner.machine.signals.tool_calls = 70  # Orange
        with pytest.raises(ShutdownRequired) as exc_info:
            runner.run()
        assert exc_info.value.tier.value == "orange"

    def test_red_triggers_shutdown(self, config, dispatcher):
        runner = OrchestratorRunner(
            config=config, session_id="s1", dispatcher=dispatcher,
        )
        runner.machine.signals.system_warning = True  # Red
        with pytest.raises(ShutdownRequired):
            runner.run()

    def test_shutdown_writes_final_checkpoint(self, config, dispatcher):
        runner = OrchestratorRunner(
            config=config, session_id="s1", dispatcher=dispatcher,
        )
        runner.machine.signals.tool_calls = 70  # Orange
        with pytest.raises(ShutdownRequired):
            runner.run()
        # Shutdown handler writes a checkpoint
        from pathlib import Path
        checkpoints = list(Path(config.checkpoint_dir).glob("*.json"))
        assert len(checkpoints) > 0


# ---------------------------------------------------------------------------
# Dispatch control
# ---------------------------------------------------------------------------


class TestRunnerDispatch:
    def test_dispatch_respects_parallel_coders(self, config, dispatcher):
        """Dispatch should not exceed parallel_coders limit."""
        runner = OrchestratorRunner(
            config=config, session_id="s1", dispatcher=dispatcher,
        )
        runner.work.issues_selected = ["#1", "#2", "#3", "#4", "#5"]
        runner.machine._started = True
        runner.machine.state.phase = 2  # Pretend we're coming from Phase 2
        runner.machine.transition(3)
        task_ids = runner._phase_3_dispatch()
        # config.parallel_coders = 3
        assert len(task_ids) == 3
        assert len(dispatcher.dispatched) == 3

    def test_dispatch_with_unlimited_coders(self, tmp_path, dispatcher):
        config = OrchestratorConfig(
            parallel_coders=-1,
            checkpoint_dir=str(tmp_path / "cp"),
            audit_log_dir=str(tmp_path / "audit"),
        )
        runner = OrchestratorRunner(
            config=config, session_id="s1", dispatcher=dispatcher,
        )
        runner.work.issues_selected = ["#1", "#2", "#3", "#4", "#5"]
        runner.machine._started = True
        runner.machine.state.phase = 2
        runner.machine.transition(3)
        task_ids = runner._phase_3_dispatch()
        assert len(task_ids) == 5  # All dispatched

    def test_empty_dispatch(self, runner):
        runner.work.issues_selected = []
        runner.machine._started = True
        runner.machine.state.phase = 2
        runner.machine.transition(3)
        task_ids = runner._phase_3_dispatch()
        assert task_ids == []


# ---------------------------------------------------------------------------
# Phase 5 loop decision
# ---------------------------------------------------------------------------


class TestPhase5LoopDecision:
    def test_issue_cap_triggers_shutdown(self, config, dispatcher):
        """Reaching parallel_coders issues triggers shutdown in _phase_5_merge."""
        runner = OrchestratorRunner(
            config=config, session_id="s1", dispatcher=dispatcher,
        )
        # Set issues_completed to 1 below cap so gate passes (Yellow, not Red)
        runner.machine.signals.issues_completed = 1  # Yellow (N-2 = 1)
        runner.machine._started = True
        runner.machine.state.phase = 4
        runner.machine.transition(5)  # Phase 5 Yellow → PROCEED
        # Now bump to cap inside merge
        runner.machine.signals.issues_completed = 3  # == parallel_coders
        with pytest.raises(ShutdownRequired):
            runner._phase_5_merge()

    def test_unlimited_no_issue_cap(self, tmp_path, dispatcher):
        """With parallel_coders=-1, issue count doesn't trigger shutdown."""
        config = OrchestratorConfig(
            parallel_coders=-1,
            checkpoint_dir=str(tmp_path / "cp"),
            audit_log_dir=str(tmp_path / "audit"),
        )
        runner = OrchestratorRunner(
            config=config, session_id="s1", dispatcher=dispatcher,
        )
        runner.machine.signals.issues_completed = 100
        runner.machine._started = True
        runner.machine.state.phase = 4
        runner.machine.transition(5)
        # Should not raise — unlimited mode, Green tier for issues
        runner._phase_5_merge()

    def test_orange_during_merge_triggers_shutdown(self, config, dispatcher):
        """Orange tier detected inside _phase_5_merge triggers shutdown."""
        runner = OrchestratorRunner(
            config=config, session_id="s1", dispatcher=dispatcher,
        )
        # Enter Phase 5 at Green
        runner.machine._started = True
        runner.machine.state.phase = 4
        runner.machine.transition(5)
        # Now simulate Orange happening during merge
        runner.machine.signals.tool_calls = 70  # Orange
        with pytest.raises(ShutdownRequired):
            runner._phase_5_merge()


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------


class TestRunnerAudit:
    def test_audit_records_session_start(self, runner):
        try:
            runner.run()
        except ShutdownRequired:
            pass
        events = runner.audit.read_all()
        session_starts = [e for e in events if e["event_type"] == "session_start"]
        assert len(session_starts) == 1

    def test_audit_records_gate_checks(self, runner):
        try:
            runner.run()
        except ShutdownRequired:
            pass
        events = runner.audit.read_all()
        gate_checks = [e for e in events if e["event_type"] == "gate_check"]
        assert len(gate_checks) > 0

    def test_audit_records_shutdown(self, config, dispatcher):
        runner = OrchestratorRunner(
            config=config, session_id="s1", dispatcher=dispatcher,
        )
        runner.machine.signals.tool_calls = 100  # Red
        with pytest.raises(ShutdownRequired):
            runner.run()
        events = runner.audit.read_all()
        shutdowns = [e for e in events if e["event_type"] == "shutdown"]
        assert len(shutdowns) == 1
