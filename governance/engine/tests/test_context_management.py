"""Unit tests for context management: tier classification, checkpoint lifecycle, Phase 0 recovery, gate actions.

Covers:
- Tier classification given signal values (tool calls, turns, issues completed)
- Single Red signal escalation
- Unlimited mode (parallel_coders: -1)
- Checkpoint schema validation (valid/invalid/extra fields)
- Checkpoint round-trip (serialize -> write -> read -> deserialize)
- Phase 0 recovery logic (closed issues, all-closed, branch mismatch)
- Malformed checkpoint handling (invalid JSON, missing fields, empty file)
- Context gate action mapping completeness
"""

import json
from pathlib import Path
from unittest.mock import patch

import jsonschema
import pytest

from conftest import REPO_ROOT

from governance.engine.orchestrator.capacity import (
    Action,
    CapacitySignals,
    Tier,
    classify_tier,
    format_gate_block,
    gate_action,
    TOOL_CALLS_GREEN_MAX,
    TOOL_CALLS_YELLOW_MAX,
    TOOL_CALLS_ORANGE_MAX,
    TURNS_GREEN_MAX,
    TURNS_YELLOW_MAX,
    TURNS_ORANGE_MAX,
    VALID_PHASES,
)
from governance.engine.orchestrator.checkpoint import (
    CheckpointManager,
    IssueState,
    _extract_issue_number,
)


# ---------------------------------------------------------------------------
# Schema fixture
# ---------------------------------------------------------------------------

CHECKPOINT_SCHEMA_PATH = REPO_ROOT / "governance" / "schemas" / "checkpoint.schema.json"


@pytest.fixture
def checkpoint_schema():
    with open(CHECKPOINT_SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture
def checkpoint_dir(tmp_path):
    return tmp_path / "checkpoints"


@pytest.fixture
def mgr(checkpoint_dir):
    return CheckpointManager(checkpoint_dir)


@pytest.fixture
def mgr_with_schema(checkpoint_dir):
    return CheckpointManager(checkpoint_dir, schema_path=CHECKPOINT_SCHEMA_PATH)


# ===========================================================================
# Tier classification — boundary and edge-case tests
# ===========================================================================


class TestTierClassificationBoundaries:
    """Verify tier boundaries are correctly enforced at exact threshold values."""

    def test_tool_calls_green_at_zero(self):
        assert classify_tier(CapacitySignals(tool_calls=0)) == Tier.GREEN

    def test_tool_calls_green_at_max(self):
        assert classify_tier(CapacitySignals(tool_calls=TOOL_CALLS_GREEN_MAX)) == Tier.GREEN

    def test_tool_calls_yellow_at_boundary(self):
        assert classify_tier(CapacitySignals(tool_calls=TOOL_CALLS_GREEN_MAX + 1)) == Tier.YELLOW

    def test_tool_calls_yellow_at_max(self):
        assert classify_tier(CapacitySignals(tool_calls=TOOL_CALLS_YELLOW_MAX)) == Tier.YELLOW

    def test_tool_calls_orange_at_boundary(self):
        assert classify_tier(CapacitySignals(tool_calls=TOOL_CALLS_YELLOW_MAX + 1)) == Tier.ORANGE

    def test_tool_calls_orange_at_max(self):
        assert classify_tier(CapacitySignals(tool_calls=TOOL_CALLS_ORANGE_MAX)) == Tier.ORANGE

    def test_tool_calls_red_at_boundary(self):
        assert classify_tier(CapacitySignals(tool_calls=TOOL_CALLS_ORANGE_MAX + 1)) == Tier.RED

    def test_turns_green_at_max(self):
        assert classify_tier(CapacitySignals(turns=TURNS_GREEN_MAX)) == Tier.GREEN

    def test_turns_yellow_at_boundary(self):
        assert classify_tier(CapacitySignals(turns=TURNS_GREEN_MAX + 1)) == Tier.YELLOW

    def test_turns_orange_at_boundary(self):
        assert classify_tier(CapacitySignals(turns=TURNS_YELLOW_MAX + 1)) == Tier.ORANGE

    def test_turns_red_at_boundary(self):
        assert classify_tier(CapacitySignals(turns=TURNS_ORANGE_MAX + 1)) == Tier.RED


class TestTierEscalation:
    """A single Red signal must escalate the entire session to Red."""

    def test_system_warning_overrides_all_green(self):
        signals = CapacitySignals(
            tool_calls=0, turns=0, issues_completed=0,
            parallel_coders=5, system_warning=True,
        )
        assert classify_tier(signals) == Tier.RED

    def test_degraded_recall_overrides_all_green(self):
        signals = CapacitySignals(
            tool_calls=0, turns=0, issues_completed=0,
            parallel_coders=5, degraded_recall=True,
        )
        assert classify_tier(signals) == Tier.RED

    def test_issues_red_overrides_green_tool_calls_and_turns(self):
        signals = CapacitySignals(
            tool_calls=0, turns=0,
            issues_completed=5, parallel_coders=5,
        )
        assert classify_tier(signals) == Tier.RED

    def test_tool_calls_red_overrides_green_others(self):
        signals = CapacitySignals(
            tool_calls=TOOL_CALLS_ORANGE_MAX + 1,
            turns=0, issues_completed=0, parallel_coders=5,
        )
        assert classify_tier(signals) == Tier.RED

    def test_highest_tier_wins_mixed_signals(self):
        signals = CapacitySignals(
            tool_calls=TOOL_CALLS_GREEN_MAX,  # Green
            turns=TURNS_YELLOW_MAX + 1,       # Orange
            issues_completed=0,
        )
        assert classify_tier(signals) == Tier.ORANGE


class TestUnlimitedMode:
    """When parallel_coders == -1, issue count signal is disabled."""

    def test_unlimited_ignores_issue_count(self):
        signals = CapacitySignals(issues_completed=100, parallel_coders=-1)
        assert classify_tier(signals) == Tier.GREEN

    def test_unlimited_tool_calls_still_effective(self):
        signals = CapacitySignals(
            issues_completed=100, parallel_coders=-1,
            tool_calls=TOOL_CALLS_ORANGE_MAX + 1,
        )
        assert classify_tier(signals) == Tier.RED

    def test_unlimited_turns_still_effective(self):
        signals = CapacitySignals(
            issues_completed=100, parallel_coders=-1,
            turns=TURNS_ORANGE_MAX + 1,
        )
        assert classify_tier(signals) == Tier.RED

    def test_unlimited_system_warning_still_red(self):
        signals = CapacitySignals(
            issues_completed=0, parallel_coders=-1, system_warning=True,
        )
        assert classify_tier(signals) == Tier.RED


# ===========================================================================
# Checkpoint schema validation
# ===========================================================================


class TestCheckpointSchemaValidation:
    """Validate checkpoints against the JSON schema."""

    def _make_valid_checkpoint(self):
        return {
            "timestamp": "2026-03-01T12:00:00+00:00",
            "branch": "main",
            "issues_completed": ["#1"],
            "issues_remaining": ["#2"],
            "git_state": "clean",
            "pending_work": "Continue with issue #2",
        }

    def test_valid_checkpoint_passes_schema(self, checkpoint_schema):
        checkpoint = self._make_valid_checkpoint()
        jsonschema.validate(checkpoint, checkpoint_schema)

    def test_missing_required_field_rejected(self, checkpoint_schema):
        checkpoint = self._make_valid_checkpoint()
        del checkpoint["branch"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(checkpoint, checkpoint_schema)

    def test_missing_timestamp_rejected(self, checkpoint_schema):
        checkpoint = self._make_valid_checkpoint()
        del checkpoint["timestamp"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(checkpoint, checkpoint_schema)

    def test_missing_git_state_rejected(self, checkpoint_schema):
        checkpoint = self._make_valid_checkpoint()
        del checkpoint["git_state"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(checkpoint, checkpoint_schema)

    def test_invalid_git_state_rejected(self, checkpoint_schema):
        checkpoint = self._make_valid_checkpoint()
        checkpoint["git_state"] = "unknown"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(checkpoint, checkpoint_schema)

    def test_extra_fields_rejected(self, checkpoint_schema):
        checkpoint = self._make_valid_checkpoint()
        checkpoint["unexpected_field"] = "surprise"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(checkpoint, checkpoint_schema)

    def test_invalid_issue_format_rejected(self, checkpoint_schema):
        checkpoint = self._make_valid_checkpoint()
        checkpoint["issues_completed"] = ["42"]  # Missing # prefix
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(checkpoint, checkpoint_schema)

    def test_full_checkpoint_with_optional_fields(self, checkpoint_schema):
        checkpoint = self._make_valid_checkpoint()
        checkpoint.update({
            "session_id": "20260301-session-1",
            "prs_created": ["#100"],
            "prs_resolved": ["#100"],
            "prs_remaining": [],
            "current_issue": "#3",
            "current_step": "Phase 2 - Planning",
            "context_capacity": {
                "tier": "green",
                "tool_calls": 25,
                "turn_count": 10,
            },
            "context_gates_passed": [
                {"phase": 1, "tier": "green", "action": "proceed"},
            ],
        })
        jsonschema.validate(checkpoint, checkpoint_schema)


class TestCheckpointManagerValidation:
    """Test validation via CheckpointManager.validate()."""

    def test_validate_returns_empty_for_valid(self, mgr_with_schema):
        path = mgr_with_schema.write(
            session_id="s1", branch="main",
            issues_completed=["#1"], issues_remaining=["#2"],
        )
        data = mgr_with_schema.load(path)
        errors = mgr_with_schema.validate(data)
        assert errors == []

    def test_validate_without_schema_always_passes(self, mgr):
        """Manager without schema path should return empty errors."""
        errors = mgr.validate({"garbage": True})
        assert errors == []


# ===========================================================================
# Checkpoint round-trip
# ===========================================================================


class TestCheckpointRoundTrip:
    """Serialize -> write -> read -> deserialize must produce identical data."""

    def test_basic_round_trip(self, mgr):
        path = mgr.write(
            session_id="rt-1",
            branch="feat/42/test",
            issues_completed=["#1", "#2"],
            issues_remaining=["#3", "#4"],
            current_issue="#3",
            current_step="Phase 2 - Planning",
            pending_work="Plan issue #3",
        )
        loaded = mgr.load(path)
        assert loaded["session_id"] == "rt-1"
        assert loaded["branch"] == "feat/42/test"
        assert loaded["issues_completed"] == ["#1", "#2"]
        assert loaded["issues_remaining"] == ["#3", "#4"]
        assert loaded["current_issue"] == "#3"
        assert loaded["pending_work"] == "Plan issue #3"
        assert loaded["git_state"] == "clean"

    def test_round_trip_with_capacity(self, mgr):
        path = mgr.write(
            session_id="rt-2",
            branch="main",
            issues_completed=[],
            issues_remaining=[],
            context_capacity={"tier": "orange", "tool_calls": 72},
            context_gates_passed=[
                {"phase": 1, "tier": "green", "action": "proceed"},
                {"phase": 2, "tier": "yellow", "action": "proceed"},
            ],
        )
        loaded = mgr.load(path)
        assert loaded["context_capacity"]["tier"] == "orange"
        assert loaded["context_capacity"]["tool_calls"] == 72
        assert len(loaded["context_gates_passed"]) == 2

    def test_round_trip_preserves_all_pr_fields(self, mgr):
        path = mgr.write(
            session_id="rt-3",
            branch="main",
            issues_completed=["#1"],
            issues_remaining=["#2"],
            prs_created=["#100", "#101"],
            prs_resolved=["#100"],
            prs_remaining=["#101"],
        )
        loaded = mgr.load(path)
        assert loaded["prs_created"] == ["#100", "#101"]
        assert loaded["prs_resolved"] == ["#100"]
        assert loaded["prs_remaining"] == ["#101"]


# ===========================================================================
# Phase 0 recovery logic
# ===========================================================================


class TestPhase0Recovery:
    """Test Phase 0 checkpoint recovery: issue validation, resume phase."""

    @patch("governance.engine.orchestrator.checkpoint._is_issue_open")
    def test_closed_issues_removed_from_queue(self, mock_open, mgr):
        mock_open.return_value = IssueState.CLOSED
        checkpoint = {
            "current_issue": "#42",
            "issues_remaining": ["#43", "#44"],
        }
        result = mgr.validate_issues(checkpoint)
        assert result["current_issue"] is None
        assert result["issues_remaining"] == []

    @patch("governance.engine.orchestrator.checkpoint._is_issue_open")
    def test_all_closed_discards_entire_queue(self, mock_open, mgr):
        mock_open.return_value = IssueState.CLOSED
        checkpoint = {
            "current_issue": "#42",
            "issues_remaining": ["#43"],
        }
        result = mgr.validate_issues(checkpoint)
        assert result["current_issue"] is None
        assert result["issues_remaining"] == []

    @patch("governance.engine.orchestrator.checkpoint._is_issue_open")
    def test_open_issues_preserved(self, mock_open, mgr):
        mock_open.return_value = IssueState.OPEN
        checkpoint = {
            "current_issue": "#42",
            "issues_remaining": ["#43", "#44"],
        }
        result = mgr.validate_issues(checkpoint)
        assert result["current_issue"] == "#42"
        assert result["issues_remaining"] == ["#43", "#44"]

    @patch("governance.engine.orchestrator.checkpoint._is_issue_open")
    def test_unknown_state_preserves_issues(self, mock_open, mgr):
        """API errors should not silently drop work items."""
        mock_open.return_value = IssueState.UNKNOWN
        checkpoint = {
            "current_issue": "#42",
            "issues_remaining": ["#43"],
        }
        result = mgr.validate_issues(checkpoint)
        assert result["current_issue"] == "#42"
        assert result["issues_remaining"] == ["#43"]

    def test_branch_mismatch_detection(self, mgr):
        """Checkpoint branch vs current branch should be detectable."""
        path = mgr.write(
            session_id="bm-1",
            branch="feat/42/old-branch",
            issues_completed=[],
            issues_remaining=["#42"],
        )
        loaded = mgr.load(path)
        current_branch = "feat/43/new-branch"
        assert loaded["branch"] != current_branch

    def test_resume_no_work_returns_phase1(self, mgr):
        checkpoint = {
            "prs_created": [],
            "prs_remaining": [],
            "issues_remaining": [],
            "current_issue": None,
        }
        assert mgr.determine_resume_phase(checkpoint) == 1

    def test_resume_issues_no_prs_returns_phase2(self, mgr):
        checkpoint = {
            "prs_created": [],
            "prs_remaining": [],
            "issues_remaining": ["#42"],
            "current_issue": None,
        }
        assert mgr.determine_resume_phase(checkpoint) == 2

    def test_resume_prs_and_issues_returns_phase3(self, mgr):
        checkpoint = {
            "prs_created": ["#100"],
            "prs_remaining": [],
            "issues_remaining": ["#43"],
            "current_issue": None,
        }
        assert mgr.determine_resume_phase(checkpoint) == 3

    def test_resume_open_prs_returns_phase4(self, mgr):
        checkpoint = {
            "prs_created": ["#100"],
            "prs_remaining": ["#100"],
            "issues_remaining": [],
            "current_issue": None,
        }
        assert mgr.determine_resume_phase(checkpoint) == 4

    def test_resume_all_prs_resolved_returns_phase5(self, mgr):
        checkpoint = {
            "prs_created": ["#100"],
            "prs_remaining": [],
            "issues_remaining": [],
            "current_issue": None,
        }
        assert mgr.determine_resume_phase(checkpoint) == 5


# ===========================================================================
# Malformed checkpoint handling
# ===========================================================================


class TestMalformedCheckpoints:
    """Test handling of invalid/corrupted checkpoint files."""

    def test_empty_directory_returns_none(self, mgr):
        assert mgr.load_latest() is None

    def test_invalid_json_raises(self, mgr, checkpoint_dir):
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        bad_file = checkpoint_dir / "bad.json"
        bad_file.write_text("not json at all {{{")
        with pytest.raises(json.JSONDecodeError):
            mgr.load(bad_file)

    def test_empty_file_raises(self, mgr, checkpoint_dir):
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        empty_file = checkpoint_dir / "empty.json"
        empty_file.write_text("")
        with pytest.raises(json.JSONDecodeError):
            mgr.load(empty_file)

    def test_missing_fields_in_loaded_checkpoint(self, mgr, checkpoint_dir):
        """A checkpoint missing required fields should be loadable but fail validation."""
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        minimal = checkpoint_dir / "minimal.json"
        minimal.write_text(json.dumps({"branch": "main"}))
        data = mgr.load(minimal)
        assert data["branch"] == "main"
        assert "timestamp" not in data

    def test_schema_validation_catches_missing_fields(self, mgr_with_schema, checkpoint_dir):
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        bad = checkpoint_dir / "incomplete.json"
        bad.write_text(json.dumps({"branch": "main"}))
        data = mgr_with_schema.load(bad)
        errors = mgr_with_schema.validate(data)
        assert len(errors) > 0

    def test_null_values_in_checkpoint(self, mgr, checkpoint_dir):
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        f = checkpoint_dir / "null_vals.json"
        f.write_text(json.dumps({
            "timestamp": "2026-03-01T12:00:00+00:00",
            "branch": "main",
            "issues_completed": [],
            "issues_remaining": [],
            "git_state": "clean",
            "pending_work": "",
            "current_issue": None,
        }))
        data = mgr.load(f)
        assert data["current_issue"] is None


# ===========================================================================
# Context gate action mapping completeness
# ===========================================================================


class TestGateActionMappingCompleteness:
    """Verify every (phase, tier) combination maps to a defined action."""

    def test_all_phase_tier_combinations_defined(self):
        for phase in VALID_PHASES:
            for tier in Tier:
                action = gate_action(phase, tier)
                assert isinstance(action, Action), (
                    f"No action for (phase={phase}, tier={tier})"
                )

    def test_green_always_proceeds(self):
        for phase in VALID_PHASES:
            assert gate_action(phase, Tier.GREEN) == Action.PROCEED

    def test_red_always_emergency_stops(self):
        for phase in VALID_PHASES:
            assert gate_action(phase, Tier.RED) == Action.EMERGENCY_STOP

    def test_invalid_phase_raises(self):
        with pytest.raises(ValueError, match="Invalid phase"):
            gate_action(8, Tier.GREEN)
        with pytest.raises(ValueError, match="Invalid phase"):
            gate_action(-1, Tier.GREEN)

    def test_format_gate_block_contains_required_info(self):
        signals = CapacitySignals(tool_calls=25, turns=30)
        block = format_gate_block(0, signals)
        assert "Phase: 0" in block
        assert "Tool calls this session: 25" in block
        assert "Tier:" in block
        assert "Action:" in block

    def test_format_gate_block_red_emergency(self):
        signals = CapacitySignals(tool_calls=100, turns=200)
        block = format_gate_block(3, signals)
        assert "Tier: Red" in block
        assert "Action: emergency-stop" in block
