"""Configurable storage backend for governance state and artifacts.

Provides a ``StorageAdapter`` protocol with ``put``/``get``/``list``/``delete``
operations, and concrete implementations for local file storage (XDG-compliant)
and in-repo storage (backward compatibility).

Usage:
    from governance.engine.storage import create_adapter

    adapter = create_adapter({"state": "local"})
    adapter.put("sessions/s1.json", data, metadata={"session_id": "s1"})
    data, meta = adapter.get("sessions/s1.json")
    keys = adapter.list("sessions/")
    adapter.delete("sessions/s1.json")

The default ``LocalAdapter`` stores files under the XDG state directory:
    - Linux: ``~/.local/state/dark-governance/``
    - macOS: ``~/Library/Application Support/dark-governance/``
    - Windows: ``%LOCALAPPDATA%/dark-governance/``

Set ``state: repo`` in ``project.yaml`` for backward compatibility with
the current ``.artifacts/`` in-repo layout.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class KeyNotFoundError(StorageError):
    """Raised when a requested key does not exist."""
    pass


@runtime_checkable
class StorageAdapter(Protocol):
    """Protocol for governance state storage backends.

    All keys are forward-slash-separated paths (e.g., ``sessions/s1.json``).
    Data is bytes; metadata is a dict of string key-value pairs stored alongside.
    """

    def put(self, key: str, data: bytes, metadata: dict[str, Any] | None = None) -> str:
        """Store data under the given key.

        Args:
            key: Storage key (forward-slash path, e.g., ``sessions/s1.json``).
            data: Raw bytes to store.
            metadata: Optional metadata dict stored as a sidecar.

        Returns:
            The canonical key under which the data was stored.

        Raises:
            StorageError: If the write fails.
        """
        ...

    def get(self, key: str) -> tuple[bytes, dict[str, Any]]:
        """Retrieve data and metadata for a key.

        Args:
            key: Storage key to retrieve.

        Returns:
            Tuple of (data_bytes, metadata_dict). Metadata is empty dict
            if no sidecar exists.

        Raises:
            KeyNotFoundError: If the key does not exist.
            StorageError: If the read fails.
        """
        ...

    def list(self, prefix: str = "") -> list[str]:
        """List all keys matching a prefix.

        Args:
            prefix: Key prefix to filter by (e.g., ``sessions/``).
                    Empty string returns all keys.

        Returns:
            Sorted list of matching keys.
        """
        ...

    def delete(self, key: str) -> bool:
        """Delete a key and its metadata sidecar.

        Args:
            key: Storage key to delete.

        Returns:
            True if the key was deleted, False if it didn't exist.

        Raises:
            StorageError: If the deletion fails for reasons other than
                         the key not existing.
        """
        ...


def _get_xdg_state_dir() -> Path:
    """Resolve the XDG state directory for governance data.

    Follows the XDG Base Directory Specification on Linux, and uses
    platform-appropriate equivalents on macOS and Windows.

    Returns:
        Path to the ``dark-governance`` state directory.
    """
    # Check explicit XDG override first (works on all platforms)
    xdg_state = os.environ.get("XDG_STATE_HOME")
    if xdg_state:
        return Path(xdg_state) / "dark-governance"

    system = platform.system()

    if system == "Darwin":
        # macOS: ~/Library/Application Support/
        return Path.home() / "Library" / "Application Support" / "dark-governance"
    elif system == "Windows":
        # Windows: %LOCALAPPDATA%
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "dark-governance"
        return Path.home() / "AppData" / "Local" / "dark-governance"
    else:
        # Linux / other Unix: ~/.local/state/
        return Path.home() / ".local" / "state" / "dark-governance"


class LocalAdapter:
    """Store governance state on the local filesystem.

    Uses XDG-compliant paths by default. Metadata is stored as JSON
    sidecar files (``{key}.meta.json``).

    Args:
        base_dir: Override the base storage directory.
                  If None, uses the XDG state directory.
    """

    def __init__(self, base_dir: str | Path | None = None):
        if base_dir is not None:
            self._base = Path(base_dir)
        else:
            self._base = _get_xdg_state_dir()
        self._base.mkdir(parents=True, exist_ok=True)

    @property
    def base_dir(self) -> Path:
        """The resolved base storage directory."""
        return self._base

    def _resolve(self, key: str) -> Path:
        """Resolve a key to an absolute file path."""
        # Normalize separators and prevent path traversal
        clean_key = key.replace("\\", "/").strip("/")
        if ".." in clean_key.split("/"):
            raise StorageError(f"Path traversal not allowed: {key}")
        return self._base / clean_key

    def _meta_path(self, key: str) -> Path:
        """Resolve the metadata sidecar path for a key."""
        return self._resolve(key).with_suffix(
            self._resolve(key).suffix + ".meta.json"
        )

    def put(self, key: str, data: bytes, metadata: dict[str, Any] | None = None) -> str:
        """Store data under the given key."""
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            path.write_bytes(data)
        except OSError as e:
            raise StorageError(f"Failed to write {key}: {e}") from e

        if metadata:
            meta_path = self._meta_path(key)
            try:
                meta_path.write_text(json.dumps(metadata, indent=2))
            except OSError as e:
                raise StorageError(f"Failed to write metadata for {key}: {e}") from e

        return key

    def get(self, key: str) -> tuple[bytes, dict[str, Any]]:
        """Retrieve data and metadata for a key."""
        path = self._resolve(key)
        if not path.exists():
            raise KeyNotFoundError(f"Key not found: {key}")

        try:
            data = path.read_bytes()
        except OSError as e:
            raise StorageError(f"Failed to read {key}: {e}") from e

        meta: dict[str, Any] = {}
        meta_path = self._meta_path(key)
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
            except (OSError, json.JSONDecodeError):
                pass  # Metadata is best-effort

        return data, meta

    def list(self, prefix: str = "") -> list[str]:
        """List all keys matching a prefix."""
        if prefix:
            search_dir = self._resolve(prefix)
            if search_dir.is_file():
                # Prefix is a file, return just that key
                return [prefix]
            if not search_dir.exists():
                return []
            base_for_rel = self._base
        else:
            search_dir = self._base
            base_for_rel = self._base

        keys = []
        for path in search_dir.rglob("*"):
            if path.is_file() and not path.name.endswith(".meta.json"):
                rel = path.relative_to(base_for_rel)
                keys.append(str(rel).replace("\\", "/"))

        return sorted(keys)

    def delete(self, key: str) -> bool:
        """Delete a key and its metadata sidecar."""
        path = self._resolve(key)
        if not path.exists():
            return False

        try:
            path.unlink()
        except OSError as e:
            raise StorageError(f"Failed to delete {key}: {e}") from e

        # Clean up metadata sidecar
        meta_path = self._meta_path(key)
        if meta_path.exists():
            try:
                meta_path.unlink()
            except OSError:
                pass  # Best-effort metadata cleanup

        return True


class RepoAdapter:
    """Store governance state in the repository's ``.artifacts/`` directory.

    Provides backward compatibility with the current in-repo layout.
    Files are written directly to ``{repo_root}/.artifacts/{key}``.

    Args:
        repo_root: Path to the repository root.
    """

    def __init__(self, repo_root: str | Path):
        self._base = Path(repo_root) / ".artifacts"
        self._base.mkdir(parents=True, exist_ok=True)

    @property
    def base_dir(self) -> Path:
        """The resolved base storage directory."""
        return self._base

    def _resolve(self, key: str) -> Path:
        clean_key = key.replace("\\", "/").strip("/")
        if ".." in clean_key.split("/"):
            raise StorageError(f"Path traversal not allowed: {key}")
        return self._base / clean_key

    def _meta_path(self, key: str) -> Path:
        return self._resolve(key).with_suffix(
            self._resolve(key).suffix + ".meta.json"
        )

    def put(self, key: str, data: bytes, metadata: dict[str, Any] | None = None) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            path.write_bytes(data)
        except OSError as e:
            raise StorageError(f"Failed to write {key}: {e}") from e

        if metadata:
            meta_path = self._meta_path(key)
            try:
                meta_path.write_text(json.dumps(metadata, indent=2))
            except OSError as e:
                raise StorageError(f"Failed to write metadata for {key}: {e}") from e

        return key

    def get(self, key: str) -> tuple[bytes, dict[str, Any]]:
        path = self._resolve(key)
        if not path.exists():
            raise KeyNotFoundError(f"Key not found: {key}")

        try:
            data = path.read_bytes()
        except OSError as e:
            raise StorageError(f"Failed to read {key}: {e}") from e

        meta: dict[str, Any] = {}
        meta_path = self._meta_path(key)
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
            except (OSError, json.JSONDecodeError):
                pass

        return data, meta

    def list(self, prefix: str = "") -> list[str]:
        if prefix:
            search_dir = self._resolve(prefix)
            if search_dir.is_file():
                return [prefix]
            if not search_dir.exists():
                return []
            base_for_rel = self._base
        else:
            search_dir = self._base
            base_for_rel = self._base

        keys = []
        for path in search_dir.rglob("*"):
            if path.is_file() and not path.name.endswith(".meta.json"):
                rel = path.relative_to(base_for_rel)
                keys.append(str(rel).replace("\\", "/"))

        return sorted(keys)

    def delete(self, key: str) -> bool:
        path = self._resolve(key)
        if not path.exists():
            return False

        try:
            path.unlink()
        except OSError as e:
            raise StorageError(f"Failed to delete {key}: {e}") from e

        meta_path = self._meta_path(key)
        if meta_path.exists():
            try:
                meta_path.unlink()
            except OSError:
                pass

        return True


def create_adapter(config: dict[str, Any] | None = None) -> StorageAdapter:
    """Create a storage adapter from configuration.

    Reads the ``state`` key from the config dict to determine which
    adapter to instantiate.

    Args:
        config: Storage configuration dict. Expected keys:
            - ``state``: ``"local"`` (default) or ``"repo"``
            - ``config.base_dir``: Override for local adapter base dir
            - ``config.repo_root``: Repo root for repo adapter

    Returns:
        A configured StorageAdapter instance.

    Raises:
        ValueError: If the backend type is not recognized.
    """
    if config is None:
        config = {}

    backend = config.get("state", "local")
    backend_config = config.get("config") or {}

    if backend == "local":
        base_dir = backend_config.get("base_dir")
        return LocalAdapter(base_dir=base_dir)
    elif backend == "repo":
        repo_root = backend_config.get("repo_root", ".")
        return RepoAdapter(repo_root=repo_root)
    else:
        raise ValueError(
            f"Unknown storage backend: '{backend}'. "
            "Supported backends: 'local', 'repo'"
        )
