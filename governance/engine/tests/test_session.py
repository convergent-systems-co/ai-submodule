"""Tests for governance.engine.orchestrator.session — SessionStore save/load/list."""

import json

import pytest

from governance.engine.orchestrator.session import PersistedSession, SessionStore


@pytest.fixture
def session_dir(tmp_path):
    d = tmp_path / "sessions"
    d.mkdir()
    return d


@pytest.fixture
def store(session_dir):
    return SessionStore(session_dir)


class TestPersistedSession:
    def test_defaults(self):
        s = PersistedSession(session_id="test-1")
        assert s.session_id == "test-1"
        assert s.current_phase == 0
        assert s.completed_phases == []
        assert s.tool_calls == 0
        assert s.loop_count == 0
        assert s.created_at != ""
        assert s.updated_at != ""

    def test_timestamps_auto_set(self):
        s = PersistedSession(session_id="test-1")
        assert s.created_at == s.updated_at
        assert "T" in s.created_at  # ISO format

    def test_custom_timestamps_preserved(self):
        s = PersistedSession(
            session_id="test-1",
            created_at="2026-01-01T00:00:00",
            updated_at="2026-01-01T01:00:00",
        )
        assert s.created_at == "2026-01-01T00:00:00"
        assert s.updated_at == "2026-01-01T01:00:00"


class TestSessionStoreSaveLoad:
    def test_save_creates_file(self, store, session_dir):
        session = PersistedSession(session_id="test-1")
        path = store.save(session)
        assert path.exists()
        assert path.suffix == ".json"

    def test_round_trip(self, store):
        original = PersistedSession(
            session_id="test-1",
            current_phase=3,
            completed_phases=[1, 2],
            tool_calls=25,
            turns=10,
            issues_selected=["#42", "#43"],
            issues_done=["#41"],
            prs_created=["#100"],
            loop_count=2,
            state_machine={"phase": 3, "signals": {"tool_calls": 25}},
            circuit_breaker_state={"#42": {"feedback_cycles": 1, "total_eval_cycles": 1}},
        )
        store.save(original)
        loaded = store.load("test-1")

        assert loaded is not None
        assert loaded.session_id == "test-1"
        assert loaded.current_phase == 3
        assert loaded.completed_phases == [1, 2]
        assert loaded.tool_calls == 25
        assert loaded.issues_selected == ["#42", "#43"]
        assert loaded.loop_count == 2
        assert loaded.state_machine["phase"] == 3

    def test_load_nonexistent_returns_none(self, store):
        assert store.load("nonexistent") is None

    def test_save_updates_timestamp(self, store):
        session = PersistedSession(session_id="test-1")
        original_updated = session.updated_at
        store.save(session)
        # updated_at should have been refreshed
        loaded = store.load("test-1")
        assert loaded.updated_at >= original_updated

    def test_overwrite_on_save(self, store):
        session = PersistedSession(session_id="test-1", current_phase=1)
        store.save(session)
        session.current_phase = 3
        store.save(session)
        loaded = store.load("test-1")
        assert loaded.current_phase == 3


class TestSessionStoreLoadLatest:
    def test_load_latest_empty(self, store):
        assert store.load_latest() is None

    def test_load_latest_returns_most_recent(self, store):
        s1 = PersistedSession(session_id="old")
        store.save(s1)
        s2 = PersistedSession(session_id="new")
        store.save(s2)
        latest = store.load_latest()
        assert latest is not None
        assert latest.session_id == "new"


class TestSessionStoreListSessions:
    def test_list_empty(self, store):
        assert store.list_sessions() == []

    def test_list_sessions(self, store):
        for sid in ["alpha", "beta", "gamma"]:
            store.save(PersistedSession(session_id=sid))
        sessions = store.list_sessions()
        assert len(sessions) == 3
        # Most recent first
        assert sessions[0] == "gamma"

    def test_safe_id_with_slashes(self, store):
        session = PersistedSession(session_id="feat/issue/42")
        path = store.save(session)
        assert "feat-issue-42" in path.name
        loaded = store.load("feat/issue/42")
        assert loaded is not None
        assert loaded.session_id == "feat/issue/42"


class TestSessionStoreCreatesDir:
    def test_creates_dir_on_init(self, tmp_path):
        d = tmp_path / "new" / "nested" / "sessions"
        store = SessionStore(d)
        assert d.exists()
