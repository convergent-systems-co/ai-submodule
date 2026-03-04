"""Tests for topology enforcement -- hard-blocking TopologyError at phase gates.

Covers:
    - TopologyError exception class
    - AgentRegistry.validate_topology_hard() returning TopologyError objects
    - AgentRegistry.validate_parent_linkage() for Coder->TL hierarchy
    - AgentRegistry.validate_phase_4_coder_coverage() for TL->Coder coverage
    - StepRunner integration: phase transitions blocked by topology violations
    - E2E scenario: full PM mode agent hierarchy with proper topology
"""

import json
from unittest.mock import patch

import pytest

from governance.engine.orchestrator.agent_registry import AgentRegistry
from governance.engine.orchestrator.config import OrchestratorConfig
from governance.engine.orchestrator.step_runner import StepRunner
from governance.engine.orchestrator.topology_error import TopologyError


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


# ---------------------------------------------------------------
# Unit tests -- TopologyError
# ---------------------------------------------------------------


class TestTopologyError:
    def test_construction_and_str(self):
        err = TopologyError(
            phase=2,
            rule="missing_devops_engineer",
            detail="No devops_engineer registered.",
        )
        msg = str(err)
        assert "phase 2" in msg.lower() or "phase 2" in msg
        assert "missing_devops_engineer" in msg
        assert "No devops_engineer registered." in msg

    def test_to_dict(self):
        err = TopologyError(
            phase=4,
            rule="missing_tech_lead",
            detail="No tech_lead registered.",
            missing_personas=["tech_lead"],
        )
        d = err.to_dict()
        assert d["phase"] == 4
        assert d["rule"] == "missing_tech_lead"
        assert d["detail"] == "No tech_lead registered."
        assert d["missing_personas"] == ["tech_lead"]

    def test_repr(self):
        err = TopologyError(
            phase=2,
            rule="missing_devops_engineer",
            detail="test detail",
        )
        r = repr(err)
        assert "TopologyError" in r
        assert "phase=2" in r
        assert "missing_devops_engineer" in r

    def test_missing_personas_default_empty(self):
        err = TopologyError(phase=1, rule="test_rule")
        assert err.missing_personas == []

    def test_inherits_runtime_error(self):
        err = TopologyError(phase=1, rule="test")
        assert isinstance(err, RuntimeError)

    def test_format_message_with_missing_personas(self):
        err = TopologyError(
            phase=2,
            rule="missing_devops_engineer",
            detail="test",
            missing_personas=["devops_engineer"],
        )
        msg = str(err)
        assert "(missing: devops_engineer)" in msg

    def test_format_message_without_detail(self):
        err = TopologyError(phase=3, rule="test_rule")
        msg = str(err)
        assert "phase 3" in msg.lower() or "phase 3" in msg
        assert "test_rule" in msg


# ---------------------------------------------------------------
# Unit tests -- AgentRegistry.validate_topology_hard() with TopologyError
# ---------------------------------------------------------------


class TestValidateTopologyHardTopologyError:
    def test_returns_topology_error_objects(self):
        reg = AgentRegistry()
        errors = reg.validate_topology_hard(2, use_project_manager=True)
        assert len(errors) == 1
        assert isinstance(errors[0], TopologyError)

    def test_phase_2_error_has_correct_rule(self):
        reg = AgentRegistry()
        errors = reg.validate_topology_hard(2, use_project_manager=True)
        assert errors[0].rule == "missing_devops_engineer"
        assert errors[0].phase == 2
        assert "devops_engineer" in errors[0].missing_personas

    def test_phase_4_error_has_correct_rule(self):
        reg = AgentRegistry()
        errors = reg.validate_topology_hard(4, use_project_manager=True)
        assert errors[0].rule == "missing_tech_lead"
        assert errors[0].phase == 4
        assert "tech_lead" in errors[0].missing_personas

    def test_standard_mode_returns_empty(self):
        reg = AgentRegistry()
        errors = reg.validate_topology_hard(2, use_project_manager=False)
        assert errors == []

    def test_phase_2_passes_with_devops(self):
        reg = AgentRegistry()
        reg.register("devops_engineer", "devops-1")
        errors = reg.validate_topology_hard(2, use_project_manager=True)
        assert errors == []

    def test_phase_4_passes_with_tech_lead(self):
        reg = AgentRegistry()
        reg.register("tech_lead", "tl-1")
        errors = reg.validate_topology_hard(4, use_project_manager=True)
        assert errors == []

    def test_error_to_dict_roundtrip(self):
        reg = AgentRegistry()
        errors = reg.validate_topology_hard(2, use_project_manager=True)
        d = errors[0].to_dict()
        assert d["phase"] == 2
        assert d["rule"] == "missing_devops_engineer"
        assert isinstance(d["detail"], str)
        assert isinstance(d["missing_personas"], list)


# ---------------------------------------------------------------
# Unit tests -- AgentRegistry.validate_parent_linkage()
# ---------------------------------------------------------------


class TestValidateParentLinkage:
    def test_standard_mode_returns_empty(self):
        reg = AgentRegistry()
        reg.register("coder", "coder-1")  # No parent_task_id
        errors = reg.validate_parent_linkage(use_project_manager=False)
        assert errors == []

    def test_pm_mode_coder_without_parent(self):
        reg = AgentRegistry()
        reg.register("coder", "coder-1")  # No parent_task_id
        errors = reg.validate_parent_linkage(use_project_manager=True)
        assert len(errors) == 1
        assert errors[0].rule == "missing_parent_linkage"
        assert "coder-1" in errors[0].detail

    def test_pm_mode_coder_with_parent(self):
        reg = AgentRegistry()
        reg.register("tech_lead", "tl-1")
        reg.register("coder", "coder-1", parent_task_id="tl-1")
        errors = reg.validate_parent_linkage(use_project_manager=True)
        assert errors == []

    def test_pm_mode_multiple_coders_mixed(self):
        reg = AgentRegistry()
        reg.register("tech_lead", "tl-1")
        reg.register("coder", "coder-1", parent_task_id="tl-1")
        reg.register("coder", "coder-2")  # Missing parent
        reg.register("coder", "coder-3", parent_task_id="tl-1")
        errors = reg.validate_parent_linkage(use_project_manager=True)
        assert len(errors) == 1
        assert "coder-2" in errors[0].detail

    def test_pm_mode_no_coders_returns_empty(self):
        reg = AgentRegistry()
        reg.register("tech_lead", "tl-1")
        errors = reg.validate_parent_linkage(use_project_manager=True)
        assert errors == []

    def test_pm_mode_all_coders_without_parent(self):
        reg = AgentRegistry()
        reg.register("coder", "coder-1")
        reg.register("coder", "coder-2")
        errors = reg.validate_parent_linkage(use_project_manager=True)
        assert len(errors) == 2


# ---------------------------------------------------------------
# Unit tests -- AgentRegistry.validate_phase_4_coder_coverage()
# ---------------------------------------------------------------


class TestValidatePhase4CoderCoverage:
    def test_no_tech_leads_returns_empty(self):
        reg = AgentRegistry()
        errors = reg.validate_phase_4_coder_coverage()
        assert errors == []

    def test_tech_lead_with_coder(self):
        reg = AgentRegistry()
        reg.register("tech_lead", "tl-1")
        reg.register("coder", "coder-1", parent_task_id="tl-1")
        errors = reg.validate_phase_4_coder_coverage()
        assert errors == []

    def test_tech_lead_without_coder(self):
        reg = AgentRegistry()
        reg.register("tech_lead", "tl-1")
        errors = reg.validate_phase_4_coder_coverage()
        assert len(errors) == 1
        assert errors[0].rule == "tech_lead_no_coders"
        assert "tl-1" in errors[0].detail

    def test_multiple_tech_leads_partial_coverage(self):
        reg = AgentRegistry()
        reg.register("tech_lead", "tl-1")
        reg.register("tech_lead", "tl-2")
        reg.register("coder", "coder-1", parent_task_id="tl-1")
        # tl-2 has no coders
        errors = reg.validate_phase_4_coder_coverage()
        assert len(errors) == 1
        assert "tl-2" in errors[0].detail

    def test_multiple_tech_leads_full_coverage(self):
        reg = AgentRegistry()
        reg.register("tech_lead", "tl-1")
        reg.register("tech_lead", "tl-2")
        reg.register("coder", "coder-1", parent_task_id="tl-1")
        reg.register("coder", "coder-2", parent_task_id="tl-2")
        errors = reg.validate_phase_4_coder_coverage()
        assert errors == []

    def test_multiple_coders_per_tech_lead(self):
        reg = AgentRegistry()
        reg.register("tech_lead", "tl-1")
        reg.register("coder", "coder-1", parent_task_id="tl-1")
        reg.register("coder", "coder-2", parent_task_id="tl-1")
        reg.register("coder", "coder-3", parent_task_id="tl-1")
        errors = reg.validate_phase_4_coder_coverage()
        assert errors == []

    def test_coder_without_parent_does_not_cover(self):
        """A coder with empty parent_task_id does not cover any tech lead."""
        reg = AgentRegistry()
        reg.register("tech_lead", "tl-1")
        reg.register("coder", "coder-1")  # No parent_task_id
        errors = reg.validate_phase_4_coder_coverage()
        assert len(errors) == 1
        assert "tl-1" in errors[0].detail


# ---------------------------------------------------------------
# StepRunner integration tests -- phase transitions blocked
# ---------------------------------------------------------------


class TestStepRunnerTopologyEnforcement:
    def test_phase_2_blocked_without_devops(self, pm_config):
        """step(1, ...) in PM mode fails if no DevOps Engineer registered."""
        runner = StepRunner(pm_config, session_id="topo-test-1")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            with pytest.raises(RuntimeError, match="topology enforcement"):
                runner.step(1, {"issues_selected": ["#42"]})

    def test_phase_2_passes_with_devops(self, pm_config):
        """step(1, ...) in PM mode succeeds when DevOps Engineer is registered."""
        runner = StepRunner(pm_config, session_id="topo-test-2")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")
            result = runner.step(1, {"issues_selected": ["#42"]})
            assert result.phase == 2

    def test_phase_4_blocked_without_tech_lead(self, pm_config):
        """step(3, ...) in PM mode fails if no Tech Lead registered."""
        runner = StepRunner(pm_config, session_id="topo-test-3")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")
            runner.step(1, {"issues_selected": ["#42"]})
            runner.step(2, {"plans": {"#42": "plan"}})
            with pytest.raises(RuntimeError, match="topology enforcement"):
                runner.step(3, {"dispatched_task_ids": ["cc-1"]})

    def test_phase_4_blocked_without_coders(self, pm_config):
        """step(3, ...) in PM mode fails if Tech Lead has no Coders."""
        runner = StepRunner(pm_config, session_id="topo-test-4")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")
            runner.step(1, {"issues_selected": ["#42"]})
            runner.register_agent("tech_lead", "tl-1")
            runner.step(2, {"plans": {"#42": "plan"}})
            with pytest.raises(RuntimeError, match="topology enforcement"):
                runner.step(3, {"dispatched_task_ids": ["cc-1"]})

    def test_phase_4_blocked_coder_without_parent(self, pm_config):
        """step(3, ...) fails if Coder has no parent_task_id in PM mode."""
        runner = StepRunner(pm_config, session_id="topo-test-5")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")
            runner.step(1, {"issues_selected": ["#42"]})
            runner.register_agent("tech_lead", "tl-1")
            runner.register_agent("coder", "coder-1")  # No parent
            runner.step(2, {"plans": {"#42": "plan"}})
            with pytest.raises(RuntimeError, match="topology enforcement"):
                runner.step(3, {"dispatched_task_ids": ["cc-1"]})

    def test_phase_4_passes_with_full_topology(self, pm_config):
        """step(3, ...) succeeds with complete PM topology."""
        runner = StepRunner(pm_config, session_id="topo-test-6")
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
        """Standard mode (PM off) skips all topology enforcement."""
        runner = StepRunner(std_config, session_id="topo-test-7")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            # No agents registered -- should still advance
            runner.step(1, {"issues_selected": ["#42"]})
            runner.step(2, {"plans": {"#42": "plan"}})
            result = runner.step(3, {"dispatched_task_ids": ["cc-1"]})
            assert result.phase == 4

    def test_topology_error_message_contains_rule(self, pm_config):
        """RuntimeError message includes the topology rule name."""
        runner = StepRunner(pm_config, session_id="topo-test-8")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            with pytest.raises(RuntimeError, match="missing_devops_engineer"):
                runner.step(1, {"issues_selected": ["#42"]})


# ---------------------------------------------------------------
# E2E scenario -- full PM mode topology lifecycle
# ---------------------------------------------------------------


class TestTopologyE2EScenario:
    def test_full_pm_lifecycle(self, pm_config):
        """E2E: PM -> DevOps -> TL -> Coder -> Phase 4 succeeds."""
        runner = StepRunner(pm_config, session_id="e2e-topo-1")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()

            # Register DevOps Engineer -> Phase 2 succeeds
            runner.register_agent("devops_engineer", "devops-1")
            r1 = runner.step(1, {"issues_selected": ["#42", "#43"]})
            assert r1.phase == 2

            # Register Tech Lead -> Phase 3 succeeds
            runner.register_agent("tech_lead", "tl-1")
            r2 = runner.step(2, {"plans": {"#42": "plan-42", "#43": "plan-43"}})
            assert r2.phase == 3

            # Register Coder under TL -> Phase 4 succeeds
            runner.register_agent("coder", "coder-1", parent_task_id="tl-1")
            r3 = runner.step(3, {"dispatched_task_ids": ["cc-1"]})
            assert r3.phase == 4

    def test_tl_without_coders_then_add_coders(self, pm_config):
        """E2E: Phase 4 fails without Coders, then succeeds after adding."""
        runner = StepRunner(pm_config, session_id="e2e-topo-2")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")
            runner.step(1, {"issues_selected": ["#42"]})
            runner.register_agent("tech_lead", "tl-1")
            runner.step(2, {"plans": {"#42": "plan"}})

            # Phase 4 fails: TL has no Coders
            with pytest.raises(RuntimeError, match="tech_lead_no_coders"):
                runner.step(3, {"dispatched_task_ids": ["cc-1"]})

            # Register Coder, retry Phase 3->4
            runner.register_agent("coder", "coder-1", parent_task_id="tl-1")
            r = runner.step(3, {"dispatched_task_ids": ["cc-1"]})
            assert r.phase == 4

    def test_multiple_tech_leads_with_coders(self, pm_config):
        """E2E: Multiple Tech Leads, each with Coders, all pass."""
        runner = StepRunner(pm_config, session_id="e2e-topo-3")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")
            runner.step(1, {"issues_selected": ["#42", "#43", "#44"]})

            runner.register_agent("tech_lead", "tl-1")
            runner.register_agent("tech_lead", "tl-2")
            runner.step(2, {"plans": {"#42": "plan"}})

            runner.register_agent("coder", "coder-1", parent_task_id="tl-1")
            runner.register_agent("coder", "coder-2", parent_task_id="tl-2")
            r = runner.step(3, {"dispatched_task_ids": ["cc-1", "cc-2"]})
            assert r.phase == 4

    def test_multiple_tech_leads_partial_coverage_fails(self, pm_config):
        """E2E: One TL has Coders, another does not -- fails."""
        runner = StepRunner(pm_config, session_id="e2e-topo-4")
        with _patch_git(), _patch_checkpoint():
            runner.init_session()
            runner.register_agent("devops_engineer", "devops-1")
            runner.step(1, {"issues_selected": ["#42"]})

            runner.register_agent("tech_lead", "tl-1")
            runner.register_agent("tech_lead", "tl-2")
            runner.step(2, {"plans": {"#42": "plan"}})

            # Only tl-1 has a Coder
            runner.register_agent("coder", "coder-1", parent_task_id="tl-1")
            with pytest.raises(RuntimeError, match="tech_lead_no_coders"):
                runner.step(3, {"dispatched_task_ids": ["cc-1"]})

    def test_session_persistence_preserves_parent_linkage(self, pm_config):
        """Parent linkage survives session save/restore cycle."""
        runner1 = StepRunner(pm_config, session_id="e2e-persist-1")
        with _patch_git(), _patch_checkpoint():
            runner1.init_session()
            runner1.register_agent("devops_engineer", "devops-1")
            runner1.register_agent("tech_lead", "tl-1")
            runner1.register_agent("coder", "coder-1", parent_task_id="tl-1")
            runner1.step(1, {"issues_selected": ["#42"]})

        # Restore session
        runner2 = StepRunner(pm_config, session_id="e2e-persist-1")
        with _patch_git(), _patch_checkpoint():
            runner2.init_session(session_id="e2e-persist-1")
            # The restored registry should have the parent linkage intact
            agent = runner2._registry.get_agent("coder-1")
            assert agent is not None
            assert agent.parent_task_id == "tl-1"


# ---------------------------------------------------------------
# Export verification
# ---------------------------------------------------------------


class TestTopologyErrorExport:
    def test_importable_from_orchestrator_package(self):
        """TopologyError should be importable from the orchestrator package."""
        from governance.engine.orchestrator import TopologyError as TE
        assert TE is TopologyError

    def test_in_all(self):
        """TopologyError should be in __all__."""
        from governance.engine.orchestrator import __all__
        assert "TopologyError" in __all__
