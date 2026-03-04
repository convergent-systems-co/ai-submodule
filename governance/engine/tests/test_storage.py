"""Tests for governance.engine.storage — storage adapter protocol and implementations."""

from __future__ import annotations

import json
import os
import platform

import pytest

from governance.engine.storage import (
    KeyNotFoundError,
    LocalAdapter,
    RepoAdapter,
    StorageAdapter,
    StorageError,
    _get_xdg_state_dir,
    create_adapter,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def local_adapter(tmp_path):
    """Create a LocalAdapter using a temporary directory."""
    return LocalAdapter(base_dir=tmp_path / "local-state")


@pytest.fixture
def repo_adapter(tmp_path):
    """Create a RepoAdapter using a temporary repo root."""
    return RepoAdapter(repo_root=tmp_path / "repo")


@pytest.fixture
def sample_data():
    """Sample bytes data for storage tests."""
    return b'{"session_id": "test-1", "phase": 3}'


@pytest.fixture
def sample_metadata():
    """Sample metadata dict."""
    return {"session_id": "test-1", "created_at": "2026-03-03T00:00:00Z"}


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    def test_local_adapter_is_storage_adapter(self, local_adapter):
        assert isinstance(local_adapter, StorageAdapter)

    def test_repo_adapter_is_storage_adapter(self, repo_adapter):
        assert isinstance(repo_adapter, StorageAdapter)


# ---------------------------------------------------------------------------
# LocalAdapter
# ---------------------------------------------------------------------------


class TestLocalAdapterPutGet:
    def test_put_creates_file(self, local_adapter, sample_data):
        key = local_adapter.put("sessions/s1.json", sample_data)
        assert key == "sessions/s1.json"
        assert (local_adapter.base_dir / "sessions" / "s1.json").exists()

    def test_round_trip(self, local_adapter, sample_data):
        local_adapter.put("sessions/s1.json", sample_data)
        data, meta = local_adapter.get("sessions/s1.json")
        assert data == sample_data
        assert meta == {}

    def test_round_trip_with_metadata(self, local_adapter, sample_data, sample_metadata):
        local_adapter.put("sessions/s1.json", sample_data, metadata=sample_metadata)
        data, meta = local_adapter.get("sessions/s1.json")
        assert data == sample_data
        assert meta == sample_metadata

    def test_metadata_sidecar_created(self, local_adapter, sample_data, sample_metadata):
        local_adapter.put("sessions/s1.json", sample_data, metadata=sample_metadata)
        meta_path = local_adapter.base_dir / "sessions" / "s1.json.meta.json"
        assert meta_path.exists()
        loaded = json.loads(meta_path.read_text())
        assert loaded == sample_metadata

    def test_overwrite_existing(self, local_adapter):
        local_adapter.put("test.txt", b"version1")
        local_adapter.put("test.txt", b"version2")
        data, _ = local_adapter.get("test.txt")
        assert data == b"version2"

    def test_get_nonexistent_raises(self, local_adapter):
        with pytest.raises(KeyNotFoundError, match="Key not found"):
            local_adapter.get("nonexistent.json")

    def test_nested_directories(self, local_adapter, sample_data):
        local_adapter.put("deep/nested/path/file.json", sample_data)
        data, _ = local_adapter.get("deep/nested/path/file.json")
        assert data == sample_data

    def test_path_traversal_blocked(self, local_adapter):
        with pytest.raises(StorageError, match="Path traversal"):
            local_adapter.put("../escape/file.txt", b"malicious")


class TestLocalAdapterList:
    def test_list_empty(self, local_adapter):
        assert local_adapter.list() == []

    def test_list_all(self, local_adapter):
        local_adapter.put("a.txt", b"a")
        local_adapter.put("b.txt", b"b")
        local_adapter.put("c.txt", b"c")
        keys = local_adapter.list()
        assert keys == ["a.txt", "b.txt", "c.txt"]

    def test_list_excludes_metadata_sidecars(self, local_adapter):
        local_adapter.put("data.json", b"data", metadata={"key": "value"})
        keys = local_adapter.list()
        assert keys == ["data.json"]
        assert not any(k.endswith(".meta.json") for k in keys)

    def test_list_with_prefix(self, local_adapter):
        local_adapter.put("sessions/s1.json", b"s1")
        local_adapter.put("sessions/s2.json", b"s2")
        local_adapter.put("checkpoints/c1.json", b"c1")
        keys = local_adapter.list("sessions/")
        assert keys == ["sessions/s1.json", "sessions/s2.json"]

    def test_list_nonexistent_prefix(self, local_adapter):
        assert local_adapter.list("nonexistent/") == []

    def test_list_sorted(self, local_adapter):
        for name in ["z.txt", "a.txt", "m.txt"]:
            local_adapter.put(name, b"data")
        keys = local_adapter.list()
        assert keys == sorted(keys)


class TestLocalAdapterDelete:
    def test_delete_existing(self, local_adapter):
        local_adapter.put("test.txt", b"data")
        assert local_adapter.delete("test.txt") is True
        with pytest.raises(KeyNotFoundError):
            local_adapter.get("test.txt")

    def test_delete_nonexistent(self, local_adapter):
        assert local_adapter.delete("nonexistent.txt") is False

    def test_delete_removes_metadata_sidecar(self, local_adapter):
        local_adapter.put("test.json", b"data", metadata={"key": "val"})
        meta_path = local_adapter.base_dir / "test.json.meta.json"
        assert meta_path.exists()
        local_adapter.delete("test.json")
        assert not meta_path.exists()


# ---------------------------------------------------------------------------
# RepoAdapter
# ---------------------------------------------------------------------------


class TestRepoAdapter:
    def test_stores_under_artifacts(self, repo_adapter):
        repo_adapter.put("sessions/s1.json", b"data")
        assert (repo_adapter.base_dir / "sessions" / "s1.json").exists()
        assert ".artifacts" in str(repo_adapter.base_dir)

    def test_round_trip(self, repo_adapter):
        repo_adapter.put("test.json", b'{"key": "value"}')
        data, _ = repo_adapter.get("test.json")
        assert data == b'{"key": "value"}'

    def test_round_trip_with_metadata(self, repo_adapter):
        meta = {"created": "2026-03-03"}
        repo_adapter.put("test.json", b"data", metadata=meta)
        data, loaded_meta = repo_adapter.get("test.json")
        assert loaded_meta == meta

    def test_list_with_prefix(self, repo_adapter):
        repo_adapter.put("sessions/a.json", b"a")
        repo_adapter.put("sessions/b.json", b"b")
        repo_adapter.put("logs/c.json", b"c")
        keys = repo_adapter.list("sessions/")
        assert keys == ["sessions/a.json", "sessions/b.json"]

    def test_delete(self, repo_adapter):
        repo_adapter.put("test.json", b"data")
        assert repo_adapter.delete("test.json") is True
        assert repo_adapter.delete("test.json") is False


# ---------------------------------------------------------------------------
# XDG path resolution
# ---------------------------------------------------------------------------


class TestXDGPathResolution:
    def test_xdg_state_home_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "custom-state"))
        result = _get_xdg_state_dir()
        assert result == tmp_path / "custom-state" / "dark-governance"

    def test_default_path_contains_dark_governance(self, monkeypatch):
        monkeypatch.delenv("XDG_STATE_HOME", raising=False)
        result = _get_xdg_state_dir()
        assert "dark-governance" in str(result)

    def test_local_adapter_uses_xdg_by_default(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg"))
        adapter = LocalAdapter()
        assert adapter.base_dir == tmp_path / "xdg" / "dark-governance"


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------


class TestCreateAdapter:
    def test_default_creates_local(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        adapter = create_adapter()
        assert isinstance(adapter, LocalAdapter)

    def test_local_with_base_dir(self, tmp_path):
        adapter = create_adapter({
            "state": "local",
            "config": {"base_dir": str(tmp_path / "custom")},
        })
        assert isinstance(adapter, LocalAdapter)
        assert adapter.base_dir == tmp_path / "custom"

    def test_repo_backend(self, tmp_path):
        adapter = create_adapter({
            "state": "repo",
            "config": {"repo_root": str(tmp_path)},
        })
        assert isinstance(adapter, RepoAdapter)

    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError, match="Unknown storage backend"):
            create_adapter({"state": "s3"})

    def test_none_config_defaults_to_local(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        adapter = create_adapter(None)
        assert isinstance(adapter, LocalAdapter)
