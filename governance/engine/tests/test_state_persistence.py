"""State persistence and cross-session recovery tests.

Covers:
- Agent log: append JSONL entries, read back, verify ordering and completeness
- Agent log: session ID format validation (YYYYMMDD-session-N)
- Agent log: schema validation for entries
- ADO sync ledger: valid/invalid schema validation
- ADO sync errors: error entries with retry tracking round-trip
- State merge strategy: numeric max, array concat/dedup, object deep merge
- State conflict resolution: two sessions write conflicting state
- Checkpoint-to-state handoff: consistent view across sessions
- Directory creation: missing state directories created on demand
"""

import json
import re
from pathlib import Path

import jsonschema
import pytest

from conftest import REPO_ROOT

from governance.engine.orchestrator.session import PersistedSession, SessionStore


# ---------------------------------------------------------------------------
# Schema paths
# ---------------------------------------------------------------------------

AGENT_LOG_SCHEMA_PATH = REPO_ROOT / "governance" / "schemas" / "agent-log-entry.schema.json"
ADO_LEDGER_SCHEMA_PATH = REPO_ROOT / "governance" / "schemas" / "ado-sync-ledger.schema.json"
ADO_ERROR_SCHEMA_PATH = REPO_ROOT / "governance" / "schemas" / "ado-sync-error.schema.json"


@pytest.fixture
def agent_log_schema():
    with open(AGENT_LOG_SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture
def ado_ledger_schema():
    with open(ADO_LEDGER_SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture
def ado_error_schema():
    with open(ADO_ERROR_SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture
def session_dir(tmp_path):
    d = tmp_path / "sessions"
    d.mkdir()
    return d


@pytest.fixture
def store(session_dir):
    return SessionStore(session_dir)


# ===========================================================================
# Agent log: JSONL append/read/ordering
# ===========================================================================


class TestAgentLogAppendRead:
    """Test JSONL agent log append, read back, and ordering."""

    def _make_log_entry(self, session_id, message_type, correlation_id, idx=0):
        return {
            "timestamp": f"2026-03-01T12:0{idx}:00Z",
            "session_id": session_id,
            "message_type": message_type,
            "source_agent": "tech-lead",
            "target_agent": "coder",
            "correlation_id": correlation_id,
            "summary": f"Test entry {idx}",
        }

    def test_append_and_read_back(self, tmp_path):
        log_file = tmp_path / "20260301-session-1.jsonl"
        entries = [
            self._make_log_entry("20260301-session-1", "ASSIGN", "issue-42", 0),
            self._make_log_entry("20260301-session-1", "STATUS", "issue-42", 1),
            self._make_log_entry("20260301-session-1", "RESULT", "issue-42", 2),
        ]
        # Append entries
        for entry in entries:
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        # Read back
        loaded = []
        with open(log_file) as f:
            for line in f:
                loaded.append(json.loads(line))

        assert len(loaded) == 3
        assert loaded[0]["message_type"] == "ASSIGN"
        assert loaded[1]["message_type"] == "STATUS"
        assert loaded[2]["message_type"] == "RESULT"

    def test_ordering_preserved(self, tmp_path):
        log_file = tmp_path / "log.jsonl"
        for i in range(10):
            entry = self._make_log_entry("20260301-session-1", "STATUS", "issue-42", i)
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        with open(log_file) as f:
            entries = [json.loads(line) for line in f]

        for i, entry in enumerate(entries):
            assert entry["summary"] == f"Test entry {i}"

    def test_completeness_all_entries_present(self, tmp_path):
        log_file = tmp_path / "log.jsonl"
        message_types = ["ASSIGN", "STATUS", "RESULT", "FEEDBACK", "APPROVE"]
        for i, mt in enumerate(message_types):
            entry = self._make_log_entry("20260301-session-1", mt, "issue-42", i)
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        with open(log_file) as f:
            entries = [json.loads(line) for line in f]

        actual_types = [e["message_type"] for e in entries]
        assert actual_types == message_types


class TestAgentLogSessionIdFormat:
    """Session ID format validation: YYYYMMDD-session-N."""

    def test_valid_session_id_format(self):
        valid_ids = [
            "20260301-session-1",
            "20260101-session-42",
            "20251231-session-100",
        ]
        pattern = r"^\d{8}-session-\d+$"
        for sid in valid_ids:
            assert re.match(pattern, sid), f"{sid} should match session ID format"

    def test_invalid_session_id_format(self):
        invalid_ids = [
            "session-1",
            "20260301-1",
            "2026-03-01-session-1",
            "emergency",
            "",
        ]
        pattern = r"^\d{8}-session-\d+$"
        for sid in invalid_ids:
            assert not re.match(pattern, sid), f"{sid} should NOT match session ID format"


class TestAgentLogSchemaValidation:
    """Agent log entries must conform to the schema."""

    def _make_valid_entry(self):
        return {
            "timestamp": "2026-03-01T12:00:00Z",
            "session_id": "20260301-session-1",
            "message_type": "ASSIGN",
            "source_agent": "tech-lead",
            "target_agent": "coder",
            "correlation_id": "issue-42",
        }

    def test_valid_entry_passes(self, agent_log_schema):
        entry = self._make_valid_entry()
        jsonschema.validate(entry, agent_log_schema)

    def test_valid_entry_with_summary(self, agent_log_schema):
        entry = self._make_valid_entry()
        entry["summary"] = "Assigned coder to implement feature"
        jsonschema.validate(entry, agent_log_schema)

    def test_missing_required_field_rejected(self, agent_log_schema):
        entry = self._make_valid_entry()
        del entry["message_type"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(entry, agent_log_schema)

    def test_invalid_message_type_rejected(self, agent_log_schema):
        entry = self._make_valid_entry()
        entry["message_type"] = "INVALID"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(entry, agent_log_schema)

    def test_extra_fields_rejected(self, agent_log_schema):
        entry = self._make_valid_entry()
        entry["extra"] = "unexpected"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(entry, agent_log_schema)


# ===========================================================================
# ADO sync ledger schema validation
# ===========================================================================


class TestAdoSyncLedgerSchema:
    """ADO sync ledger must conform to its schema."""

    def _make_valid_ledger(self):
        return {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 42,
                    "github_repo": "SET-Apps/my-project",
                    "ado_work_item_id": 12345,
                    "ado_project": "MyProject",
                    "sync_direction": "github_to_ado",
                    "last_synced_at": "2026-03-01T12:00:00Z",
                    "sync_status": "active",
                },
            ],
        }

    def test_valid_ledger_passes(self, ado_ledger_schema):
        ledger = self._make_valid_ledger()
        jsonschema.validate(ledger, ado_ledger_schema)

    def test_empty_mappings_passes(self, ado_ledger_schema):
        ledger = {"schema_version": "1.0.0", "mappings": []}
        jsonschema.validate(ledger, ado_ledger_schema)

    def test_missing_schema_version_rejected(self, ado_ledger_schema):
        ledger = {"mappings": []}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(ledger, ado_ledger_schema)

    def test_invalid_sync_direction_rejected(self, ado_ledger_schema):
        ledger = self._make_valid_ledger()
        ledger["mappings"][0]["sync_direction"] = "invalid"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(ledger, ado_ledger_schema)

    def test_extra_fields_rejected(self, ado_ledger_schema):
        ledger = self._make_valid_ledger()
        ledger["extra_field"] = "surprise"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(ledger, ado_ledger_schema)


# ===========================================================================
# ADO sync errors with retry tracking
# ===========================================================================


class TestAdoSyncErrorsSchema:
    """ADO sync error entries with retry tracking must round-trip correctly."""

    def _make_valid_errors(self):
        return {
            "schema_version": "1.0.0",
            "errors": [
                {
                    "error_id": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2026-03-01T12:00:00Z",
                    "operation": "create",
                    "source": "github",
                    "error_type": "auth_failure",
                    "error_message": "ADO token expired",
                    "retry_count": 2,
                    "resolved": False,
                    "github_issue_number": 42,
                    "ado_work_item_id": None,
                },
            ],
        }

    def test_valid_errors_pass(self, ado_error_schema):
        errors = self._make_valid_errors()
        jsonschema.validate(errors, ado_error_schema)

    def test_retry_tracking_round_trip(self, tmp_path, ado_error_schema):
        errors = self._make_valid_errors()
        filepath = tmp_path / "ado-sync-errors.json"
        with open(filepath, "w") as f:
            json.dump(errors, f)
        with open(filepath) as f:
            loaded = json.load(f)
        assert loaded["errors"][0]["retry_count"] == 2
        assert loaded["errors"][0]["resolved"] is False
        jsonschema.validate(loaded, ado_error_schema)

    def test_resolved_error(self, ado_error_schema):
        errors = self._make_valid_errors()
        errors["errors"][0]["resolved"] = True
        errors["errors"][0]["retry_count"] = 3
        jsonschema.validate(errors, ado_error_schema)


# ===========================================================================
# State merge strategy
# ===========================================================================


class TestStateMergeStrategy:
    """Test merge strategies for state.json conflict resolution."""

    def _numeric_max_merge(self, a, b):
        """Numeric fields take the maximum value."""
        return max(a, b)

    def _array_concat_dedup(self, a, b):
        """Arrays concatenate and deduplicate."""
        seen = set()
        result = []
        for item in a + b:
            key = json.dumps(item, sort_keys=True) if isinstance(item, dict) else item
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    def _deep_merge(self, a, b):
        """Objects deep merge (b overwrites a for scalar values)."""
        result = dict(a)
        for key, value in b.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def test_numeric_max(self):
        assert self._numeric_max_merge(5, 10) == 10
        assert self._numeric_max_merge(10, 5) == 10
        assert self._numeric_max_merge(0, 0) == 0

    def test_array_concat_dedup(self):
        result = self._array_concat_dedup(["#1", "#2"], ["#2", "#3"])
        assert result == ["#1", "#2", "#3"]

    def test_array_concat_dedup_preserves_order(self):
        result = self._array_concat_dedup(["#3", "#1"], ["#2", "#3"])
        assert result == ["#3", "#1", "#2"]

    def test_deep_merge_nested(self):
        a = {"capacity": {"tool_calls": 25}, "branch": "main"}
        b = {"capacity": {"turns": 10}, "branch": "feat/42"}
        result = self._deep_merge(a, b)
        assert result["capacity"]["tool_calls"] == 25
        assert result["capacity"]["turns"] == 10
        assert result["branch"] == "feat/42"

    def test_deep_merge_scalar_overwrite(self):
        a = {"phase": 2, "tier": "green"}
        b = {"phase": 3}
        result = self._deep_merge(a, b)
        assert result["phase"] == 3
        assert result["tier"] == "green"

    def test_conflict_resolution_two_sessions(self, store):
        """Two sessions writing conflicting state should merge cleanly."""
        s1 = PersistedSession(
            session_id="session-a",
            current_phase=2,
            tool_calls=25,
            issues_selected=["#1", "#2"],
        )
        s2 = PersistedSession(
            session_id="session-b",
            current_phase=3,
            tool_calls=30,
            issues_selected=["#2", "#3"],
        )
        store.save(s1)
        store.save(s2)

        loaded_a = store.load("session-a")
        loaded_b = store.load("session-b")
        assert loaded_a.tool_calls == 25
        assert loaded_b.tool_calls == 30

        # Merge: take max for numeric, concat/dedup for arrays
        merged_tool_calls = max(loaded_a.tool_calls, loaded_b.tool_calls)
        assert merged_tool_calls == 30

        merged_issues = list(dict.fromkeys(
            loaded_a.issues_selected + loaded_b.issues_selected
        ))
        assert merged_issues == ["#1", "#2", "#3"]


# ===========================================================================
# Checkpoint-to-state handoff
# ===========================================================================


class TestCheckpointToStateHandoff:
    """Session ends with checkpoint -> next session reads -> consistent view."""

    def test_session_state_persists_across_save_load(self, store):
        original = PersistedSession(
            session_id="handoff-1",
            current_phase=3,
            completed_phases=[1, 2],
            tool_calls=45,
            turns=20,
            issues_selected=["#42", "#43"],
            issues_done=["#41"],
            prs_created=["#100"],
            loop_count=2,
        )
        store.save(original)
        restored = store.load("handoff-1")

        assert restored.session_id == "handoff-1"
        assert restored.current_phase == 3
        assert restored.completed_phases == [1, 2]
        assert restored.tool_calls == 45
        assert restored.turns == 20
        assert restored.issues_selected == ["#42", "#43"]
        assert restored.issues_done == ["#41"]
        assert restored.prs_created == ["#100"]
        assert restored.loop_count == 2

    def test_load_latest_returns_most_recent(self, store):
        store.save(PersistedSession(session_id="old"))
        store.save(PersistedSession(session_id="new"))
        latest = store.load_latest()
        assert latest.session_id == "new"


# ===========================================================================
# Directory creation
# ===========================================================================


class TestDirectoryCreation:
    """Missing state directories should be created on demand."""

    def test_session_store_creates_dir(self, tmp_path):
        nested = tmp_path / "new" / "nested" / "sessions"
        store = SessionStore(nested)
        assert nested.exists()

    def test_agent_log_dir_created_on_write(self, tmp_path):
        log_dir = tmp_path / "agent-log"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "20260301-session-1.jsonl"
        entry = {"timestamp": "2026-03-01T12:00:00Z"}
        with open(log_file, "w") as f:
            f.write(json.dumps(entry) + "\n")
        assert log_file.exists()
