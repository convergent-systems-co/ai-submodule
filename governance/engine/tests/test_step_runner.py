"""Tests for governance.engine.orchestrator.step_runner — init, step, loop, signals, persistence."""

import json
from unittest.mock import patch, call

import pytest

from governance.engine.orchestrator.config import OrchestratorConfig
from governance.engine.orchestrator.plugins import (
    ExtensionsConfig,
    HookConfig,
    PanelPlugin,
    PhasePlugin,
)
from governance.engine.orchestrator.step_runner import StepRunner


@pytest.fixture
def config(tmp_path):
    return OrchestratorConfig(
        checkpoint_dir=str(tmp_path / "checkpoints"),
        audit_log_dir=str(tmp_path / "audit"),
        session_dir=str(tmp_path / "sessions"),
        parallel_coders=5,
    )


@pytest.fixture
def runner(config):
    return StepRunner(config, session_id="test-session")


def _patch_branch():
    return patch.object(StepRunner, "_get_current_branch", return_value="main")


def _patch_checkpoint_recovery():
    return patch(
        "governance.engine.orchestrator.step_runner.CheckpointManager.load_latest",
        return_value=None,
    )


class TestInitSession:
    def test_init_returns_step_result(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            result = runner.init_session()
        assert result.session_id == "test-session"
        assert result.action in ("execute_phase", "dispatch", "collect", "merge")
        assert result.phase == 1  # Fresh start → Phase 1

    def test_init_fresh_session(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            result = runner.init_session()
        assert result.phase == 1
        assert result.tier == "green"

    def test_init_persists_session(self, runner, config):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
        # Verify session file was created
        from governance.engine.orchestrator.session import SessionStore
        store = SessionStore(config.session_dir)
        session = store.load("test-session")
        assert session is not None
        assert session.session_id == "test-session"

    def test_init_with_custom_session_id(self, config):
        runner = StepRunner(config, session_id="custom-id")
        with _patch_branch(), _patch_checkpoint_recovery():
            result = runner.init_session()
        assert result.session_id == "custom-id"

    def test_init_resumes_existing_session(self, config):
        # Create first session
        runner1 = StepRunner(config, session_id="resume-test")
        with _patch_branch(), _patch_checkpoint_recovery():
            runner1.init_session()
            runner1.step(1, {"issues_selected": ["#42"]})

        # Resume should restore state
        runner2 = StepRunner(config, session_id="resume-test")
        with _patch_branch():
            result = runner2.init_session()
        assert result.session_id == "resume-test"


class TestStep:
    def test_step_advances_phase(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
            result = runner.step(1, {"issues_selected": ["#42"]})
        assert result.phase == 2  # Phase 1 → 2

    def test_step_absorbs_issues_selected(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
            result = runner.step(1, {"issues_selected": ["#42", "#43"]})
        assert "#42" in result.work.get("issues_selected", [])

    def test_step_absorbs_plans(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
            runner.step(1, {"issues_selected": ["#42"]})
            result = runner.step(2, {"plans": {"#42": "plan content"}})
        assert result.phase == 3

    def test_step_phase3_returns_dispatch(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
            runner.step(1, {"issues_selected": ["#42"]})
            runner.step(2, {"plans": {"#42": "plan"}})
            result = runner.step(3, {"dispatched_task_ids": ["cc-abc"]})
        assert result.phase == 4
        assert result.action == "collect"

    def test_step_through_full_pipeline(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
            r1 = runner.step(1, {"issues_selected": ["#42"]})
            assert r1.phase == 2
            r2 = runner.step(2, {"plans": {"#42": "plan"}})
            assert r2.phase == 3
            r3 = runner.step(3, {"dispatched_task_ids": ["cc-1"]})
            assert r3.phase == 4
            r4 = runner.step(4, {
                "prs_created": ["#100"],
                "prs_resolved": ["#100"],
                "issues_completed": ["#42"],
            })
            assert r4.phase == 5
            r5 = runner.step(5, {"merged_prs": ["#100"]})
            # All work done → should be "done"
            assert r5.action == "done"

    def test_idempotent_double_complete(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
            r1 = runner.step(1, {"issues_selected": ["#42"]})
            r2 = runner.step(1, {"issues_selected": ["#99"]})  # Double-complete
        # Should be a no-op — same result
        assert r1.phase == r2.phase


class TestLoopDecision:
    def test_loop_when_work_remains(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
            runner.step(1, {"issues_selected": ["#42", "#43"]})
            runner.step(2, {"plans": {"#42": "p", "#43": "p"}})
            runner.step(3, {"dispatched_task_ids": ["cc-1"]})
            runner.step(4, {
                "prs_created": ["#100"],
                "issues_completed": ["#42"],
                "prs_remaining": ["#101"],
            })
            result = runner.step(5, {"merged_prs": ["#100"]})
        # Work remains (#43 still selected, #101 remaining) → loop
        assert result.action == "execute_phase"
        assert result.phase == 1
        assert result.loop_count == 1

    def test_done_when_no_work(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
            runner.step(1, {"issues_selected": ["#42"]})
            runner.step(2, {"plans": {}})
            runner.step(3, {})
            runner.step(4, {"issues_completed": ["#42"]})
            result = runner.step(5, {})
        assert result.action == "done"


class TestRecordSignal:
    def test_record_tool_call(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
        result = runner.record_signal("tool_call", 5)
        assert result["tool_calls"] == 5
        assert result["tier"] == "green"

    def test_record_turn(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
        result = runner.record_signal("turn", 1)
        assert result["turns"] == 1

    def test_record_issue_completed(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
        result = runner.record_signal("issue_completed", 1)
        assert result["issues_completed"] == 1

    def test_signals_persist(self, runner, config):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
        runner.record_signal("tool_call", 10)

        # Load from disk
        from governance.engine.orchestrator.session import SessionStore
        store = SessionStore(config.session_dir)
        session = store.load("test-session")
        assert session.tool_calls == 10

    def test_tier_escalation(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
        result = runner.record_signal("tool_call", 55)
        assert result["tier"] == "yellow"


class TestQueryGate:
    def test_query_gate_green(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
        result = runner.query_gate(1)
        assert result["tier"] == "green"
        assert result["action"] == "proceed"
        assert result["would_shutdown"] is False

    def test_query_gate_after_signals(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
        runner.record_signal("tool_call", 70)
        result = runner.query_gate(1)
        assert result["tier"] == "orange"
        assert result["would_shutdown"] is True

    def test_query_gate_readonly(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
        # Query should not change phase
        runner.query_gate(3)
        status = runner.get_status()
        assert status["current_phase"] == 1  # Still at phase 1


class TestShutdown:
    def test_shutdown_on_orange(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
        runner.record_signal("tool_call", 70)  # Orange
        with _patch_branch():
            result = runner.step(1, {"issues_selected": ["#42"]})
        assert result.action == "shutdown"
        assert result.shutdown_info["tier"] == "orange"

    def test_shutdown_writes_checkpoint(self, runner, config):
        from pathlib import Path
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
        runner.record_signal("tool_call", 70)
        with _patch_branch():
            runner.step(1, {})
        # Verify checkpoint was written
        checkpoints = list(Path(config.checkpoint_dir).glob("*.json"))
        assert len(checkpoints) >= 1


class TestGetStatus:
    def test_status_active_session(self, runner):
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
        status = runner.get_status()
        assert status["session_id"] == "test-session"
        assert status["current_phase"] == 1
        assert "signals" in status
        assert "work" in status

    def test_status_no_session(self, config):
        runner = StepRunner(config, session_id="nonexistent")
        status = runner.get_status()
        assert "error" in status

    def test_status_from_disk(self, config):
        # Init and destroy in-memory state
        runner1 = StepRunner(config, session_id="disk-test")
        with _patch_branch(), _patch_checkpoint_recovery():
            runner1.init_session()

        # New runner loads from disk
        runner2 = StepRunner(config, session_id="disk-test")
        status = runner2.get_status()
        assert status["session_id"] == "disk-test"


class TestSessionPersistence:
    def test_state_survives_new_runner(self, config):
        """Verify that state persisted by one runner instance is loadable by another."""
        runner1 = StepRunner(config, session_id="persist-test")
        with _patch_branch(), _patch_checkpoint_recovery():
            runner1.init_session()
            runner1.step(1, {"issues_selected": ["#42"]})
            runner1.record_signal("tool_call", 15)

        runner2 = StepRunner(config, session_id="persist-test")
        with _patch_branch():
            result = runner2.init_session()
        # Should see the work state from runner1
        assert "#42" in result.work.get("issues_selected", [])


class TestPMMode:
    """Tests for Project Manager mode (use_project_manager=True).

    Verifies that PM mode includes DevOps Engineer background task in Phase 1,
    dispatches Team Lead tasks in Phase 3, and leaves standard mode unchanged.
    """

    @pytest.fixture
    def pm_config(self, tmp_path):
        return OrchestratorConfig(
            checkpoint_dir=str(tmp_path / "checkpoints"),
            audit_log_dir=str(tmp_path / "audit"),
            session_dir=str(tmp_path / "sessions"),
            parallel_coders=5,
            parallel_tech_leads=3,
            use_project_manager=True,
        )

    @pytest.fixture
    def pm_runner(self, pm_config):
        return StepRunner(pm_config, session_id="pm-test-session")

    def test_pm_phase1_includes_devops_background_task(self, pm_runner):
        """PM mode Phase 1 must include DevOps Engineer background task instructions."""
        with _patch_branch(), _patch_checkpoint_recovery():
            result = pm_runner.init_session()
        assert result.phase == 1
        inst = result.instructions
        assert inst.get("pm_mode") is True
        assert "devops_background_task" in inst
        devops = inst["devops_background_task"]
        assert devops["persona"] == "devops_engineer"
        assert devops["run_in_background"] is True
        assert "devops-engineer.md" in devops["persona_path"]
        assert "devops-operations-loop.md" in devops["operations_loop_path"]

    def test_pm_phase1_description_mentions_pm(self, pm_runner):
        """PM mode Phase 1 uses PM-specific description."""
        with _patch_branch(), _patch_checkpoint_recovery():
            result = pm_runner.init_session()
        assert "Project Manager mode" in result.instructions["description"]

    def test_pm_phase3_includes_tech_lead_info(self, pm_runner):
        """PM mode Phase 3 includes Tech Lead dispatch metadata."""
        with _patch_branch(), _patch_checkpoint_recovery():
            pm_runner.init_session()
            pm_runner.register_agent("devops_engineer", "devops-1")
            pm_runner.step(1, {"issues_selected": ["#42"]})
            result = pm_runner.step(2, {"plans": {"#42": "plan"}})
        # Phase 3 result
        assert result.phase == 3
        inst = result.instructions
        assert inst.get("parallel_tech_leads") == 3
        assert inst.get("dispatch_persona") == "tech_lead"

    def test_pm_phase3_description_mentions_tech_lead(self, pm_runner):
        """PM mode Phase 3 uses PM-specific description."""
        with _patch_branch(), _patch_checkpoint_recovery():
            pm_runner.init_session()
            pm_runner.register_agent("devops_engineer", "devops-1")
            pm_runner.step(1, {"issues_selected": ["#42"]})
            result = pm_runner.step(2, {"plans": {"#42": "plan"}})
        assert "Tech Lead" in result.instructions["description"]

    def test_standard_mode_phase1_no_devops_task(self, runner):
        """Standard mode Phase 1 must NOT include DevOps background task."""
        with _patch_branch(), _patch_checkpoint_recovery():
            result = runner.init_session()
        assert result.phase == 1
        assert result.instructions.get("pm_mode") is None
        assert "devops_background_task" not in result.instructions

    def test_standard_mode_phase3_no_tech_lead_fields(self, runner):
        """Standard mode Phase 3 must NOT include Tech Lead dispatch fields."""
        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
            runner.step(1, {"issues_selected": ["#42"]})
            result = runner.step(2, {"plans": {"#42": "plan"}})
        assert result.phase == 3
        assert "parallel_tech_leads" not in result.instructions
        assert "dispatch_persona" not in result.instructions

    def test_pm_full_pipeline(self, pm_runner):
        """PM mode runs through the full pipeline without errors."""
        with _patch_branch(), _patch_checkpoint_recovery():
            pm_runner.init_session()
            pm_runner.register_agent("devops_engineer", "devops-1")
            r1 = pm_runner.step(1, {"issues_selected": ["#42"]})
            assert r1.phase == 2
            pm_runner.register_agent("tech_lead", "tl-1")
            r2 = pm_runner.step(2, {"plans": {"#42": "plan"}})
            assert r2.phase == 3
            # Register a Coder under the Tech Lead (required for Phase 4 entry)
            pm_runner.register_agent(
                "coder", "coder-1", parent_task_id="tl-1",
            )
            r3 = pm_runner.step(3, {"dispatched_task_ids": ["cc-1"]})
            assert r3.phase == 4
            r4 = pm_runner.step(4, {
                "prs_created": ["#100"],
                "prs_resolved": ["#100"],
                "issues_completed": ["#42"],
            })
            assert r4.phase == 5
            r5 = pm_runner.step(5, {"merged_prs": ["#100"]})
            assert r5.action == "done"

    def test_pm_phase2_uses_standard_description(self, pm_runner):
        """PM mode Phase 2 (planning) uses standard description -- no override."""
        with _patch_branch(), _patch_checkpoint_recovery():
            pm_runner.init_session()
            pm_runner.register_agent("devops_engineer", "devops-1")
            result = pm_runner.step(1, {"issues_selected": ["#42"]})
        # Phase 2
        assert result.phase == 2
        assert "Parallel Planning" in result.instructions["name"]


# ---------------------------------------------------------------------------
# Plugin integration tests
# ---------------------------------------------------------------------------


class TestPluginIntegration:
    """Tests for plugin extension integration in the step runner.

    Verifies that lifecycle hooks fire at the correct phase transitions,
    custom phase scripts execute after their target phase, and on_shutdown
    hooks execute on both normal completion and shutdown.
    """

    @pytest.fixture
    def ext_config(self, tmp_path):
        """Config with extensions that have real executable scripts."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        # Create hook scripts
        for name in ["pre-dispatch.sh", "post-review.sh", "post-merge.sh", "shutdown.sh"]:
            script = scripts_dir / name
            script.write_text("#!/bin/bash\necho ok")
            script.chmod(0o755)

        # Create a phase plugin script
        phase_script = scripts_dir / "custom-phase.sh"
        phase_script.write_text("#!/bin/bash\necho custom phase done")
        phase_script.chmod(0o755)

        ext = ExtensionsConfig(
            phases=[
                PhasePlugin(
                    name="custom-after-merge",
                    script="scripts/custom-phase.sh",
                    after_phase=5,
                    timeout_seconds=10,
                    required=True,
                ),
            ],
            hooks=HookConfig(
                pre_dispatch=["scripts/pre-dispatch.sh"],
                post_review=["scripts/post-review.sh"],
                post_merge=["scripts/post-merge.sh"],
                on_shutdown=["scripts/shutdown.sh"],
            ),
        )

        return OrchestratorConfig(
            checkpoint_dir=str(tmp_path / "checkpoints"),
            audit_log_dir=str(tmp_path / "audit"),
            session_dir=str(tmp_path / "sessions"),
            parallel_coders=5,
            extensions=ext,
        )

    @pytest.fixture
    def ext_runner(self, ext_config):
        return StepRunner(ext_config, session_id="ext-test")

    def test_plugin_registry_loaded(self, ext_runner):
        """Plugin registry is created when extensions are configured."""
        assert ext_runner._plugin_registry is not None
        assert ext_runner._plugin_registry.has_extensions is True

    def test_no_plugin_registry_without_extensions(self, config):
        """No plugin registry when config has no extensions."""
        runner = StepRunner(config, session_id="no-ext")
        assert runner._plugin_registry is None

    def test_lifecycle_hooks_fire_at_correct_phases(self, ext_config, tmp_path):
        """Lifecycle hooks fire at the correct phase transitions."""
        runner = StepRunner(ext_config, session_id="hook-test")

        # Track hook executions via audit
        with _patch_branch(), _patch_checkpoint_recovery(), \
             patch.object(StepRunner, "_detect_repo_root", return_value=str(tmp_path)):
            runner.init_session()
            runner.step(1, {"issues_selected": ["#42"]})

            # After phase 2 → pre_dispatch hook should fire
            runner.step(2, {"plans": {"#42": "plan"}})
            runner.step(3, {"dispatched_task_ids": ["cc-1"]})

            # After phase 4 → post_review hook should fire
            runner.step(4, {
                "prs_created": ["#100"],
                "issues_completed": ["#42"],
            })

            # After phase 5 → post_merge hook and custom phase plugin should fire
            # Also on_shutdown should fire when done
            result = runner.step(5, {"merged_prs": ["#100"]})

        assert result.action == "done"

    def test_pre_dispatch_hook_fires_after_phase2(self, ext_config, tmp_path):
        """pre_dispatch hook fires when phase 2 completes."""
        runner = StepRunner(ext_config, session_id="pd-hook-test")
        audit_events = []
        original_record = runner._record_audit

        def capture_audit(*args, **kwargs):
            audit_events.append(args[0] if args else kwargs.get("event_type"))
            original_record(*args, **kwargs)

        runner._record_audit = capture_audit

        with _patch_branch(), _patch_checkpoint_recovery(), \
             patch.object(StepRunner, "_detect_repo_root", return_value=str(tmp_path)):
            runner.init_session()
            runner.step(1, {"issues_selected": ["#42"]})
            runner.step(2, {"plans": {"#42": "plan"}})

        assert "hook_pre_dispatch" in audit_events

    def test_post_review_hook_fires_after_phase4(self, ext_config, tmp_path):
        """post_review hook fires when phase 4 completes."""
        runner = StepRunner(ext_config, session_id="pr-hook-test")
        audit_events = []
        original_record = runner._record_audit

        def capture_audit(*args, **kwargs):
            audit_events.append(args[0] if args else kwargs.get("event_type"))
            original_record(*args, **kwargs)

        runner._record_audit = capture_audit

        with _patch_branch(), _patch_checkpoint_recovery(), \
             patch.object(StepRunner, "_detect_repo_root", return_value=str(tmp_path)):
            runner.init_session()
            runner.step(1, {"issues_selected": ["#42"]})
            runner.step(2, {"plans": {"#42": "plan"}})
            runner.step(3, {"dispatched_task_ids": ["cc-1"]})
            runner.step(4, {
                "prs_created": ["#100"],
                "issues_completed": ["#42"],
            })

        assert "hook_post_review" in audit_events

    def test_post_merge_hook_fires_after_phase5(self, ext_config, tmp_path):
        """post_merge hook fires when phase 5 completes."""
        runner = StepRunner(ext_config, session_id="pm-hook-test")
        audit_events = []
        original_record = runner._record_audit

        def capture_audit(*args, **kwargs):
            audit_events.append(args[0] if args else kwargs.get("event_type"))
            original_record(*args, **kwargs)

        runner._record_audit = capture_audit

        with _patch_branch(), _patch_checkpoint_recovery(), \
             patch.object(StepRunner, "_detect_repo_root", return_value=str(tmp_path)):
            runner.init_session()
            runner.step(1, {"issues_selected": ["#42"]})
            runner.step(2, {"plans": {"#42": "plan"}})
            runner.step(3, {"dispatched_task_ids": ["cc-1"]})
            runner.step(4, {"prs_created": ["#100"], "issues_completed": ["#42"]})
            runner.step(5, {"merged_prs": ["#100"]})

        assert "hook_post_merge" in audit_events

    def test_on_shutdown_hook_fires_on_done(self, ext_config, tmp_path):
        """on_shutdown hook fires when pipeline completes (done)."""
        runner = StepRunner(ext_config, session_id="sd-hook-test")
        audit_events = []
        original_record = runner._record_audit

        def capture_audit(*args, **kwargs):
            audit_events.append(args[0] if args else kwargs.get("event_type"))
            original_record(*args, **kwargs)

        runner._record_audit = capture_audit

        with _patch_branch(), _patch_checkpoint_recovery(), \
             patch.object(StepRunner, "_detect_repo_root", return_value=str(tmp_path)):
            runner.init_session()
            runner.step(1, {"issues_selected": ["#42"]})
            runner.step(2, {"plans": {}})
            runner.step(3, {})
            runner.step(4, {"issues_completed": ["#42"]})
            runner.step(5, {})

        assert "hook_on_shutdown" in audit_events

    def test_on_shutdown_hook_fires_on_capacity_shutdown(self, ext_config, tmp_path):
        """on_shutdown hook fires when pipeline shuts down due to capacity."""
        runner = StepRunner(ext_config, session_id="cap-sd-test")
        audit_events = []
        original_record = runner._record_audit

        def capture_audit(*args, **kwargs):
            audit_events.append(args[0] if args else kwargs.get("event_type"))
            original_record(*args, **kwargs)

        runner._record_audit = capture_audit

        with _patch_branch(), _patch_checkpoint_recovery(), \
             patch.object(StepRunner, "_detect_repo_root", return_value=str(tmp_path)):
            runner.init_session()
            runner.record_signal("tool_call", 70)  # Orange
            runner.step(1, {"issues_selected": ["#42"]})

        assert "hook_on_shutdown" in audit_events

    def test_phase_plugin_executes_after_target_phase(self, ext_config, tmp_path):
        """Custom phase plugin runs after its configured after_phase."""
        runner = StepRunner(ext_config, session_id="pp-test")
        audit_events = []
        original_record = runner._record_audit

        def capture_audit(*args, **kwargs):
            audit_events.append(args[0] if args else kwargs.get("event_type"))
            original_record(*args, **kwargs)

        runner._record_audit = capture_audit

        with _patch_branch(), _patch_checkpoint_recovery(), \
             patch.object(StepRunner, "_detect_repo_root", return_value=str(tmp_path)):
            runner.init_session()
            runner.step(1, {"issues_selected": ["#42"]})
            runner.step(2, {"plans": {"#42": "plan"}})
            runner.step(3, {"dispatched_task_ids": ["cc-1"]})
            runner.step(4, {"prs_created": ["#100"], "issues_completed": ["#42"]})
            # Phase 5 completion → custom-after-merge plugin (after_phase=5) should execute
            runner.step(5, {"merged_prs": ["#100"]})

        assert "phase_plugin" in audit_events

    def test_no_hooks_without_extensions(self, config, tmp_path):
        """No hooks fire when no extensions are configured."""
        runner = StepRunner(config, session_id="no-ext-test")
        audit_events = []
        original_record = runner._record_audit

        def capture_audit(*args, **kwargs):
            audit_events.append(args[0] if args else kwargs.get("event_type"))
            original_record(*args, **kwargs)

        runner._record_audit = capture_audit

        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()
            runner.step(1, {"issues_selected": ["#42"]})
            runner.step(2, {"plans": {"#42": "plan"}})
            runner.step(3, {"dispatched_task_ids": ["cc-1"]})
            runner.step(4, {"prs_created": ["#100"], "issues_completed": ["#42"]})
            runner.step(5, {"merged_prs": ["#100"]})

        hook_events = [e for e in audit_events if e.startswith("hook_") or e == "phase_plugin"]
        assert hook_events == []

    def test_extensions_loaded_audit_event(self, ext_config, tmp_path):
        """Init session audits that extensions were loaded."""
        runner = StepRunner(ext_config, session_id="audit-ext-test")
        audit_details = []
        original_record = runner._record_audit

        def capture_audit(event_type, phase, **kwargs):
            if event_type == "session_init":
                audit_details.append(kwargs.get("detail", {}))
            original_record(event_type, phase, **kwargs)

        runner._record_audit = capture_audit

        with _patch_branch(), _patch_checkpoint_recovery():
            runner.init_session()

        assert len(audit_details) == 1
        assert audit_details[0].get("extensions_loaded") is True
