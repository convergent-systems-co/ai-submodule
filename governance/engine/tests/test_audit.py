"""Tests for governance.engine.orchestrator.audit — structured event logging with hash chaining."""

import json

import pytest

from governance.engine.orchestrator.audit import (
    AuditEvent,
    AuditLog,
    ChainVerificationResult,
    _compute_seed,
    _hash_entry,
)


@pytest.fixture
def audit_log(tmp_path):
    return AuditLog(tmp_path / "test-session.jsonl")


class TestAuditEvent:
    def test_auto_timestamp(self):
        event = AuditEvent(event_type="test", phase=0, session_id="s1")
        assert event.timestamp != ""
        assert "T" in event.timestamp  # ISO format

    def test_explicit_timestamp(self):
        event = AuditEvent(
            event_type="test", phase=0, session_id="s1",
            timestamp="2026-03-01T00:00:00Z",
        )
        assert event.timestamp == "2026-03-01T00:00:00Z"


class TestAuditLogWrite:
    def test_record_creates_file(self, audit_log):
        event = AuditEvent(event_type="gate_check", phase=1, session_id="s1")
        audit_log.record(event)
        assert audit_log.log_path.exists()

    def test_record_appends(self, audit_log):
        for i in range(3):
            event = AuditEvent(event_type=f"event-{i}", phase=i, session_id="s1")
            audit_log.record(event)
        assert audit_log.count() == 3

    def test_record_is_valid_json(self, audit_log):
        event = AuditEvent(
            event_type="gate_check", phase=1, session_id="s1",
            tier="green", action="proceed", correlation_id="issue-42",
            detail={"tool_calls": 25},
        )
        audit_log.record(event)
        with open(audit_log.log_path) as f:
            line = f.readline()
            data = json.loads(line)
        assert data["event_type"] == "gate_check"
        assert data["phase"] == 1
        assert data["tier"] == "green"
        assert data["detail"]["tool_calls"] == 25


class TestAuditLogRead:
    def test_read_all_empty(self, audit_log):
        events = audit_log.read_all()
        assert events == []

    def test_read_all_returns_events(self, audit_log):
        for i in range(3):
            audit_log.record(
                AuditEvent(event_type=f"event-{i}", phase=i, session_id="s1")
            )
        events = audit_log.read_all()
        assert len(events) == 3
        assert events[0]["event_type"] == "event-0"
        assert events[2]["event_type"] == "event-2"

    def test_count_matches_events(self, audit_log):
        for i in range(5):
            audit_log.record(
                AuditEvent(event_type="test", phase=0, session_id="s1")
            )
        assert audit_log.count() == 5

    def test_count_empty_file(self, audit_log):
        assert audit_log.count() == 0


class TestAuditLogDirectory:
    def test_creates_parent_directory(self, tmp_path):
        log = AuditLog(tmp_path / "nested" / "deep" / "log.jsonl")
        event = AuditEvent(event_type="test", phase=0, session_id="s1")
        log.record(event)
        assert log.log_path.exists()


# ---------------------------------------------------------------------------
# Hash chaining tests
# ---------------------------------------------------------------------------

class TestHashChainSeed:
    def test_seed_is_deterministic(self):
        seed1 = _compute_seed("session-1")
        seed2 = _compute_seed("session-1")
        assert seed1 == seed2

    def test_different_sessions_different_seeds(self):
        seed1 = _compute_seed("session-1")
        seed2 = _compute_seed("session-2")
        assert seed1 != seed2

    def test_seed_is_sha256(self):
        seed = _compute_seed("test-session")
        assert len(seed) == 64
        assert all(c in "0123456789abcdef" for c in seed)


class TestHashChainLinks:
    def test_first_entry_has_seed_hash(self, audit_log):
        event = AuditEvent(event_type="test", phase=0, session_id="s1")
        audit_log.record(event)
        events = audit_log.read_all()
        assert "previous_hash" in events[0]
        assert events[0]["previous_hash"] == _compute_seed("s1")

    def test_second_entry_links_to_first(self, audit_log):
        event1 = AuditEvent(event_type="event-1", phase=0, session_id="s1")
        event2 = AuditEvent(event_type="event-2", phase=1, session_id="s1")
        audit_log.record(event1)
        audit_log.record(event2)

        # Read raw lines to compute expected hash
        with open(audit_log.log_path) as f:
            lines = [l.strip() for l in f if l.strip()]
        expected_hash = _hash_entry(lines[0])

        events = audit_log.read_all()
        assert events[1]["previous_hash"] == expected_hash

    def test_chain_of_five_entries(self, audit_log):
        for i in range(5):
            audit_log.record(
                AuditEvent(event_type=f"event-{i}", phase=i, session_id="s1")
            )

        with open(audit_log.log_path) as f:
            lines = [l.strip() for l in f if l.strip()]

        # Verify first entry has seed
        first_entry = json.loads(lines[0])
        assert first_entry["previous_hash"] == _compute_seed("s1")

        # Verify each subsequent entry links to the previous
        for i in range(1, 5):
            entry = json.loads(lines[i])
            expected_hash = _hash_entry(lines[i - 1])
            assert entry["previous_hash"] == expected_hash


class TestChainVerification:
    def test_verify_empty_log(self, audit_log):
        result = audit_log.verify_chain()
        assert result.valid is True
        assert result.total_entries == 0

    def test_verify_single_entry(self, audit_log):
        audit_log.record(
            AuditEvent(event_type="test", phase=0, session_id="s1")
        )
        result = audit_log.verify_chain()
        assert result.valid is True
        assert result.total_entries == 1
        assert result.verified_entries == 1

    def test_verify_multiple_entries(self, audit_log):
        for i in range(10):
            audit_log.record(
                AuditEvent(event_type=f"event-{i}", phase=i, session_id="s1")
            )
        result = audit_log.verify_chain()
        assert result.valid is True
        assert result.total_entries == 10
        assert result.verified_entries == 10

    def test_detect_tampered_entry(self, audit_log):
        for i in range(5):
            audit_log.record(
                AuditEvent(event_type=f"event-{i}", phase=i, session_id="s1")
            )

        # Tamper with the third entry (index 2)
        with open(audit_log.log_path) as f:
            lines = f.readlines()

        entry = json.loads(lines[2])
        entry["event_type"] = "TAMPERED"
        lines[2] = json.dumps(entry, separators=(",", ":")) + "\n"

        with open(audit_log.log_path, "w") as f:
            f.writelines(lines)

        result = audit_log.verify_chain()
        assert result.valid is False
        assert result.broken_at_index == 3  # The entry AFTER the tampered one detects it
        assert "broken" in result.reason.lower()

    def test_detect_tampered_first_entry(self, audit_log):
        for i in range(3):
            audit_log.record(
                AuditEvent(event_type=f"event-{i}", phase=i, session_id="s1")
            )

        # Tamper with the first entry's previous_hash
        with open(audit_log.log_path) as f:
            lines = f.readlines()

        entry = json.loads(lines[0])
        entry["previous_hash"] = "0" * 64
        lines[0] = json.dumps(entry, separators=(",", ":")) + "\n"

        with open(audit_log.log_path, "w") as f:
            f.writelines(lines)

        result = audit_log.verify_chain()
        assert result.valid is False
        assert result.broken_at_index == 0

    def test_detect_deleted_entry(self, audit_log):
        for i in range(5):
            audit_log.record(
                AuditEvent(event_type=f"event-{i}", phase=i, session_id="s1")
            )

        # Delete the third entry
        with open(audit_log.log_path) as f:
            lines = f.readlines()

        del lines[2]

        with open(audit_log.log_path, "w") as f:
            f.writelines(lines)

        result = audit_log.verify_chain()
        assert result.valid is False


class TestChainVerificationResult:
    def test_to_dict(self):
        result = ChainVerificationResult(
            valid=False,
            total_entries=10,
            verified_entries=5,
            broken_at_index=5,
            reason="Chain broken",
        )
        d = result.to_dict()
        assert d["valid"] is False
        assert d["total_entries"] == 10
        assert d["broken_at_index"] == 5


class TestHashChainResume:
    """Test that hash chaining works correctly when resuming an existing log."""

    def test_resume_from_existing_log(self, tmp_path):
        log_path = tmp_path / "resume.jsonl"

        # Write initial entries
        log1 = AuditLog(log_path)
        for i in range(3):
            log1.record(
                AuditEvent(event_type=f"event-{i}", phase=i, session_id="s1")
            )

        # Create a new AuditLog instance (simulates restart)
        log2 = AuditLog(log_path)
        log2.record(
            AuditEvent(event_type="resumed-event", phase=3, session_id="s1")
        )

        # Verify the full chain is valid
        result = log2.verify_chain()
        assert result.valid is True
        assert result.total_entries == 4
