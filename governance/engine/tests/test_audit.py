"""Tests for governance.engine.orchestrator.audit — structured event logging."""

import json

import pytest

from governance.engine.orchestrator.audit import AuditEvent, AuditLog


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
