"""Tests for governance.engine.orchestrator.lock_manager — cross-session work locking."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.engine.orchestrator.lock_manager import (
    DEFAULT_TTL_SECONDS,
    HEARTBEAT_INTERVAL_SECONDS,
    LockEntry,
    LockManager,
    _get_locks_dir,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def locks_dir(tmp_path):
    d = tmp_path / "locks" / "issues"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def mgr(locks_dir):
    return LockManager(session_id="session-aaa", locks_dir=locks_dir)


@pytest.fixture
def mgr_other(locks_dir):
    """A second lock manager representing a different session."""
    return LockManager(session_id="session-bbb", locks_dir=locks_dir)


# ---------------------------------------------------------------------------
# LockEntry
# ---------------------------------------------------------------------------


class TestLockEntry:
    def test_defaults(self):
        entry = LockEntry(issue_number=42, session_id="s1")
        assert entry.issue_number == 42
        assert entry.session_id == "s1"
        assert entry.claimed_at != ""
        assert entry.heartbeat != ""
        assert entry.ttl_seconds == DEFAULT_TTL_SECONDS
        assert entry.hostname != ""
        assert entry.pid > 0

    def test_custom_values_preserved(self):
        entry = LockEntry(
            issue_number=100,
            session_id="s2",
            claimed_at="2026-01-01T00:00:00+00:00",
            heartbeat="2026-01-01T01:00:00+00:00",
            hostname="test-host",
            pid=9999,
            ttl_seconds=1800,
        )
        assert entry.claimed_at == "2026-01-01T00:00:00+00:00"
        assert entry.heartbeat == "2026-01-01T01:00:00+00:00"
        assert entry.hostname == "test-host"
        assert entry.pid == 9999
        assert entry.ttl_seconds == 1800

    def test_round_trip_dict(self):
        entry = LockEntry(issue_number=42, session_id="s1")
        d = entry.to_dict()
        restored = LockEntry.from_dict(d)
        assert restored.issue_number == entry.issue_number
        assert restored.session_id == entry.session_id
        assert restored.claimed_at == entry.claimed_at

    def test_from_dict_ignores_extra_keys(self):
        data = {
            "issue_number": 42,
            "session_id": "s1",
            "extra_field": "ignored",
        }
        entry = LockEntry.from_dict(data)
        assert entry.issue_number == 42
        assert not hasattr(entry, "extra_field")

    def test_is_stale_fresh_lock(self):
        entry = LockEntry(issue_number=1, session_id="s1", ttl_seconds=3600)
        assert entry.is_stale() is False

    def test_is_stale_expired_lock(self):
        old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        entry = LockEntry(
            issue_number=1,
            session_id="s1",
            heartbeat=old_time,
            ttl_seconds=3600,
        )
        assert entry.is_stale() is True

    def test_is_stale_with_explicit_now(self):
        entry = LockEntry(
            issue_number=1,
            session_id="s1",
            heartbeat="2026-01-01T00:00:00+00:00",
            ttl_seconds=60,
        )
        # 30 seconds after heartbeat — not stale
        now_30s = datetime(2026, 1, 1, 0, 0, 30, tzinfo=timezone.utc).timestamp()
        assert entry.is_stale(now=now_30s) is False

        # 120 seconds after heartbeat — stale
        now_120s = datetime(2026, 1, 1, 0, 2, 0, tzinfo=timezone.utc).timestamp()
        assert entry.is_stale(now=now_120s) is True

    def test_is_stale_unparseable_heartbeat(self):
        entry = LockEntry(issue_number=1, session_id="s1")
        entry.heartbeat = "not-a-timestamp"
        assert entry.is_stale() is True


# ---------------------------------------------------------------------------
# LockManager — claim and release
# ---------------------------------------------------------------------------


class TestLockManagerClaim:
    def test_claim_new_issue(self, mgr):
        assert mgr.claim(42) is True
        assert mgr.is_claimed(42) is True

    def test_claim_creates_lock_file(self, mgr, locks_dir):
        mgr.claim(42)
        lock_file = locks_dir / "issue-42.lock.json"
        assert lock_file.exists()
        data = json.loads(lock_file.read_text())
        assert data["issue_number"] == 42
        assert data["session_id"] == "session-aaa"

    def test_claim_same_session_succeeds(self, mgr):
        assert mgr.claim(42) is True
        # Claiming the same issue from the same session is a refresh
        assert mgr.claim(42) is True

    def test_claim_different_session_denied(self, mgr, mgr_other):
        assert mgr.claim(42) is True
        assert mgr_other.claim(42) is False

    def test_claim_stale_lock_takeover(self, mgr, mgr_other, locks_dir):
        # Session A claims the issue
        mgr.claim(42)

        # Manually make the lock stale
        lock_file = locks_dir / "issue-42.lock.json"
        data = json.loads(lock_file.read_text())
        old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        data["heartbeat"] = old_time
        lock_file.write_text(json.dumps(data))

        # Session B should now be able to take over
        assert mgr_other.claim(42) is True
        entry = mgr_other.get_lock(42)
        assert entry.session_id == "session-bbb"

    def test_claim_multiple_issues(self, mgr):
        for i in [100, 101, 102]:
            assert mgr.claim(i) is True
        claimed = mgr.list_claimed()
        issue_nums = {e.issue_number for e in claimed}
        assert issue_nums == {100, 101, 102}


class TestLockManagerRelease:
    def test_release_own_lock(self, mgr, locks_dir):
        mgr.claim(42)
        assert mgr.release(42) is True
        assert not (locks_dir / "issue-42.lock.json").exists()

    def test_release_nonexistent(self, mgr):
        assert mgr.release(999) is False

    def test_release_other_session_denied(self, mgr, mgr_other):
        mgr.claim(42)
        # Session B cannot release Session A's lock
        assert mgr_other.release(42) is False
        # Session A can still release it
        assert mgr.release(42) is True

    def test_release_all(self, mgr):
        mgr.claim(100)
        mgr.claim(101)
        mgr.claim(102)
        released = mgr.release_all()
        assert sorted(released) == [100, 101, 102]
        assert mgr.list_claimed() == []

    def test_release_all_only_own(self, mgr, mgr_other):
        mgr.claim(100)
        mgr_other.claim(200)
        released = mgr.release_all()
        assert released == [100]
        # Other session's lock remains
        assert mgr_other.is_claimed(200) is True


# ---------------------------------------------------------------------------
# LockManager — heartbeat
# ---------------------------------------------------------------------------


class TestLockManagerHeartbeat:
    def test_heartbeat_updates_timestamp(self, mgr, locks_dir):
        mgr.claim(42)
        lock_file = locks_dir / "issue-42.lock.json"
        data1 = json.loads(lock_file.read_text())
        hb1 = data1["heartbeat"]

        # Small delay to ensure different timestamp
        time.sleep(0.01)

        assert mgr.heartbeat(42) is True
        data2 = json.loads(lock_file.read_text())
        hb2 = data2["heartbeat"]
        assert hb2 >= hb1

    def test_heartbeat_own_lock_only(self, mgr, mgr_other):
        mgr.claim(42)
        assert mgr.heartbeat(42) is True
        assert mgr_other.heartbeat(42) is False

    def test_heartbeat_nonexistent(self, mgr):
        assert mgr.heartbeat(999) is False

    def test_heartbeat_all(self, mgr):
        mgr.claim(100)
        mgr.claim(101)
        count = mgr.heartbeat_all()
        assert count == 2


# ---------------------------------------------------------------------------
# LockManager — query methods
# ---------------------------------------------------------------------------


class TestLockManagerQuery:
    def test_is_claimed_unclaimed(self, mgr):
        assert mgr.is_claimed(999) is False

    def test_is_claimed_active(self, mgr):
        mgr.claim(42)
        assert mgr.is_claimed(42) is True

    def test_is_claimed_stale_returns_false(self, mgr, locks_dir):
        mgr.claim(42)
        # Make stale
        lock_file = locks_dir / "issue-42.lock.json"
        data = json.loads(lock_file.read_text())
        data["heartbeat"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        lock_file.write_text(json.dumps(data))
        assert mgr.is_claimed(42) is False

    def test_is_claimed_by_other(self, mgr, mgr_other):
        mgr.claim(42)
        # Session B sees it as claimed by other
        assert mgr_other.is_claimed_by_other(42) is True
        # Session A does not see it as claimed by other
        assert mgr.is_claimed_by_other(42) is False

    def test_is_claimed_by_other_unclaimed(self, mgr):
        assert mgr.is_claimed_by_other(999) is False

    def test_get_lock_returns_entry(self, mgr):
        mgr.claim(42)
        entry = mgr.get_lock(42)
        assert entry is not None
        assert entry.issue_number == 42
        assert entry.session_id == "session-aaa"

    def test_get_lock_nonexistent(self, mgr):
        assert mgr.get_lock(999) is None

    def test_list_claimed_excludes_stale(self, mgr, locks_dir):
        mgr.claim(100)
        mgr.claim(101)

        # Make issue 100 stale
        lock_file = locks_dir / "issue-100.lock.json"
        data = json.loads(lock_file.read_text())
        data["heartbeat"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        lock_file.write_text(json.dumps(data))

        claimed = mgr.list_claimed()
        assert len(claimed) == 1
        assert claimed[0].issue_number == 101

    def test_list_stale(self, mgr, locks_dir):
        mgr.claim(100)
        # Make stale
        lock_file = locks_dir / "issue-100.lock.json"
        data = json.loads(lock_file.read_text())
        data["heartbeat"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        lock_file.write_text(json.dumps(data))

        stale = mgr.list_stale()
        assert len(stale) == 1
        assert stale[0].issue_number == 100


# ---------------------------------------------------------------------------
# LockManager — cleanup and force release
# ---------------------------------------------------------------------------


class TestLockManagerCleanup:
    def test_cleanup_stale(self, mgr, locks_dir):
        mgr.claim(100)
        mgr.claim(101)

        # Make both stale
        for num in [100, 101]:
            lock_file = locks_dir / f"issue-{num}.lock.json"
            data = json.loads(lock_file.read_text())
            data["heartbeat"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
            lock_file.write_text(json.dumps(data))

        removed = mgr.cleanup_stale()
        assert sorted(removed) == [100, 101]
        assert mgr.list_claimed() == []
        assert mgr.list_stale() == []

    def test_cleanup_stale_preserves_active(self, mgr, locks_dir):
        mgr.claim(100)  # Active
        mgr.claim(101)  # Will be made stale

        lock_file = locks_dir / "issue-101.lock.json"
        data = json.loads(lock_file.read_text())
        data["heartbeat"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        lock_file.write_text(json.dumps(data))

        removed = mgr.cleanup_stale()
        assert removed == [101]
        assert len(mgr.list_claimed()) == 1

    def test_force_release(self, mgr, mgr_other):
        mgr.claim(42)
        # Force-release doesn't care about ownership
        assert mgr_other.force_release(42) is True
        assert mgr.is_claimed(42) is False

    def test_force_release_nonexistent(self, mgr):
        assert mgr.force_release(999) is False


# ---------------------------------------------------------------------------
# LockManager — filter_claimed_issues
# ---------------------------------------------------------------------------


class TestFilterClaimedIssues:
    def test_no_locks_all_available(self, mgr):
        available, skipped = mgr.filter_claimed_issues(["#42", "#43", "#44"])
        assert available == ["#42", "#43", "#44"]
        assert skipped == []

    def test_filters_other_session_claims(self, mgr, mgr_other):
        mgr_other.claim(42)
        available, skipped = mgr.filter_claimed_issues(["#42", "#43"])
        assert available == ["#43"]
        assert len(skipped) == 1
        assert skipped[0]["issue"] == "#42"
        assert skipped[0]["claimed_by_session"] == "session-bbb"

    def test_preserves_own_session_claims(self, mgr):
        mgr.claim(42)
        available, skipped = mgr.filter_claimed_issues(["#42", "#43"])
        assert available == ["#42", "#43"]
        assert skipped == []

    def test_handles_bare_numbers(self, mgr, mgr_other):
        mgr_other.claim(42)
        available, skipped = mgr.filter_claimed_issues(["42", "43"])
        assert available == ["43"]
        assert len(skipped) == 1

    def test_handles_unparseable_refs(self, mgr):
        available, skipped = mgr.filter_claimed_issues(["#42", "not-a-number"])
        assert available == ["#42", "not-a-number"]
        assert skipped == []

    def test_empty_list(self, mgr):
        available, skipped = mgr.filter_claimed_issues([])
        assert available == []
        assert skipped == []


# ---------------------------------------------------------------------------
# LockManager — status dict
# ---------------------------------------------------------------------------


class TestStatusDict:
    def test_empty_status(self, mgr):
        status = mgr.to_status_dict()
        assert status["session_id"] == "session-aaa"
        assert status["active_count"] == 0
        assert status["stale_count"] == 0
        assert status["active_locks"] == []
        assert status["stale_locks"] == []

    def test_status_with_locks(self, mgr, mgr_other):
        mgr.claim(42)
        mgr_other.claim(43)

        status = mgr.to_status_dict()
        assert status["active_count"] == 2

        # Check ownership flag
        own_locks = [l for l in status["active_locks"] if l["owned_by_this_session"]]
        other_locks = [l for l in status["active_locks"] if not l["owned_by_this_session"]]
        assert len(own_locks) == 1
        assert own_locks[0]["issue_number"] == 42
        assert len(other_locks) == 1
        assert other_locks[0]["issue_number"] == 43


# ---------------------------------------------------------------------------
# LockManager — directory creation
# ---------------------------------------------------------------------------


class TestLockManagerInit:
    def test_creates_directory(self, tmp_path):
        d = tmp_path / "new" / "locks" / "issues"
        mgr = LockManager(session_id="s1", locks_dir=d)
        assert d.exists()

    def test_locks_dir_property(self, locks_dir):
        mgr = LockManager(session_id="s1", locks_dir=locks_dir)
        assert mgr.locks_dir == locks_dir

    def test_custom_ttl(self, locks_dir):
        mgr = LockManager(session_id="s1", locks_dir=locks_dir, ttl_seconds=120)
        mgr.claim(42)
        entry = mgr.get_lock(42)
        assert entry.ttl_seconds == 120


# ---------------------------------------------------------------------------
# _get_locks_dir
# ---------------------------------------------------------------------------


class TestGetLocksDir:
    def test_xdg_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg"))
        result = _get_locks_dir()
        assert result == tmp_path / "xdg" / "dark-governance" / "locks" / "issues"

    def test_base_dir_override(self, tmp_path):
        result = _get_locks_dir(base_dir=tmp_path / "custom")
        assert result == tmp_path / "custom" / "locks" / "issues"

    def test_default_contains_dark_governance(self, monkeypatch):
        monkeypatch.delenv("XDG_STATE_HOME", raising=False)
        result = _get_locks_dir()
        assert "dark-governance" in str(result)
        assert str(result).endswith(os.path.join("locks", "issues"))


# ---------------------------------------------------------------------------
# Concurrent claim simulation
# ---------------------------------------------------------------------------


class TestConcurrentClaims:
    """Test that two managers cannot both claim the same issue."""

    def test_only_one_wins(self, locks_dir):
        """When two sessions race to claim, only one succeeds."""
        mgr_a = LockManager(session_id="session-aaa", locks_dir=locks_dir)
        mgr_b = LockManager(session_id="session-bbb", locks_dir=locks_dir)

        result_a = mgr_a.claim(42)
        result_b = mgr_b.claim(42)

        assert result_a is True
        assert result_b is False

        entry = mgr_a.get_lock(42)
        assert entry.session_id == "session-aaa"

    def test_different_issues_no_conflict(self, locks_dir):
        """Different issues can be claimed by different sessions."""
        mgr_a = LockManager(session_id="session-aaa", locks_dir=locks_dir)
        mgr_b = LockManager(session_id="session-bbb", locks_dir=locks_dir)

        assert mgr_a.claim(42) is True
        assert mgr_b.claim(43) is True

        assert mgr_a.is_claimed_by_other(43) is True
        assert mgr_b.is_claimed_by_other(42) is True
        assert mgr_a.is_claimed_by_other(42) is False
        assert mgr_b.is_claimed_by_other(43) is False


# ---------------------------------------------------------------------------
# Corrupt lock file handling
# ---------------------------------------------------------------------------


class TestCorruptLockFiles:
    def test_corrupt_json_treated_as_available(self, locks_dir, mgr):
        lock_file = locks_dir / "issue-42.lock.json"
        lock_file.write_text("not valid json!!!")
        # Should be treated as no lock
        assert mgr.is_claimed(42) is False
        # Should be able to claim over corrupt file
        assert mgr.claim(42) is True

    def test_empty_file_treated_as_available(self, locks_dir, mgr):
        lock_file = locks_dir / "issue-42.lock.json"
        lock_file.write_text("")
        assert mgr.is_claimed(42) is False
        assert mgr.claim(42) is True


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


class TestCLILocks:
    """Test the locks CLI command via the main() function."""

    def test_locks_command_default(self, locks_dir, monkeypatch):
        from governance.engine.orchestrator.__main__ import main

        # Patch _get_locks_dir to use our temp dir
        monkeypatch.setattr(
            "governance.engine.orchestrator.lock_manager._get_locks_dir",
            lambda base_dir=None: locks_dir,
        )

        # Create a lock first
        mgr = LockManager(session_id="test-session", locks_dir=locks_dir)
        mgr.claim(42)

        # Run the locks command (it will use "unknown" session since no session store)
        import io
        import sys
        captured = io.StringIO()
        monkeypatch.setattr(sys, "stdout", captured)

        exit_code = main(["locks", "--session-id", "test-session"])
        assert exit_code == 0

        output = json.loads(captured.getvalue())
        assert "active_locks" in output
        assert output["active_count"] >= 1

    def test_locks_cleanup_command(self, locks_dir, monkeypatch):
        from governance.engine.orchestrator.__main__ import main

        monkeypatch.setattr(
            "governance.engine.orchestrator.lock_manager._get_locks_dir",
            lambda base_dir=None: locks_dir,
        )

        # Create a stale lock
        mgr = LockManager(session_id="old-session", locks_dir=locks_dir)
        mgr.claim(42)
        lock_file = locks_dir / "issue-42.lock.json"
        data = json.loads(lock_file.read_text())
        data["heartbeat"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        lock_file.write_text(json.dumps(data))

        import io
        import sys
        captured = io.StringIO()
        monkeypatch.setattr(sys, "stdout", captured)

        exit_code = main(["locks", "--cleanup", "--session-id", "test-session"])
        assert exit_code == 0

        output = json.loads(captured.getvalue())
        assert output["action"] == "cleanup_stale"
        assert 42 in output["removed_issues"]

    def test_locks_force_release_command(self, locks_dir, monkeypatch):
        from governance.engine.orchestrator.__main__ import main

        monkeypatch.setattr(
            "governance.engine.orchestrator.lock_manager._get_locks_dir",
            lambda base_dir=None: locks_dir,
        )

        mgr = LockManager(session_id="session-aaa", locks_dir=locks_dir)
        mgr.claim(42)

        import io
        import sys
        captured = io.StringIO()
        monkeypatch.setattr(sys, "stdout", captured)

        exit_code = main(["locks", "--force-release", "42", "--session-id", "test-session"])
        assert exit_code == 0

        output = json.loads(captured.getvalue())
        assert output["action"] == "force_release"
        assert output["removed"] is True
