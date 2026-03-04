#!/usr/bin/env python3
"""Supply chain verification for submodule consumers.

Generates and verifies SHA-256 content hashes for critical governance files
to detect tampering after `git submodule update`. Provides integrity
verification equivalent to npm's `package-lock.json` SHA checks.

Critical file categories:
  - Policy profiles (governance/policy/*.yaml)
  - JSON schemas (governance/schemas/*.json)
  - Persona definitions (governance/personas/agentic/*.md)
  - Review prompts (governance/prompts/reviews/*.md)

Usage:
    from governance.engine.supply_chain import IntegrityVerifier

    verifier = IntegrityVerifier(governance_root)
    manifest = verifier.generate_manifest()
    verifier.write_manifest(manifest)

    # Later, verify integrity
    result = verifier.verify()
    if not result.valid:
        for f in result.failures:
            print(f"TAMPERED: {f}")
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Critical file patterns
# ---------------------------------------------------------------------------

CRITICAL_DIRECTORIES = [
    ("policy", "governance/policy", "*.yaml"),
    ("schemas", "governance/schemas", "*.json"),
    ("personas", "governance/personas/agentic", "*.md"),
    ("review_prompts", "governance/prompts/reviews", "*.md"),
]


@dataclass
class VerificationResult:
    """Result of an integrity verification check."""

    valid: bool
    total_files: int
    verified_files: int
    failures: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    new_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "total_files": self.total_files,
            "verified_files": self.verified_files,
            "failures": self.failures,
            "missing_files": self.missing_files,
            "new_files": self.new_files,
        }


class IntegrityVerifier:
    """Generates and verifies integrity manifests for governance files.

    Args:
        repo_root: Path to the repository root (parent of governance/).
    """

    def __init__(self, repo_root: str | Path):
        self._repo_root = Path(repo_root)

    def _hash_file(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _collect_critical_files(self) -> dict[str, str]:
        """Collect all critical files and their hashes.

        Returns:
            Dict mapping relative file paths to their SHA-256 hashes.
        """
        hashes = {}
        for _category, rel_dir, pattern in CRITICAL_DIRECTORIES:
            dir_path = self._repo_root / rel_dir
            if dir_path.is_dir():
                for file_path in sorted(dir_path.glob(pattern)):
                    if file_path.is_file():
                        rel_path = str(file_path.relative_to(self._repo_root))
                        hashes[rel_path] = self._hash_file(file_path)
        return hashes

    def generate_manifest(self) -> dict[str, Any]:
        """Generate an integrity manifest for all critical governance files.

        Returns:
            Dict containing manifest version, timestamp, and file hashes.
        """
        file_hashes = self._collect_critical_files()
        return {
            "manifest_version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "algorithm": "sha256",
            "files": file_hashes,
            "file_count": len(file_hashes),
        }

    def write_manifest(
        self,
        manifest: dict[str, Any],
        output_path: str | Path | None = None,
    ) -> Path:
        """Write the manifest to disk.

        Args:
            manifest: The manifest dict to write.
            output_path: Where to write. Defaults to governance/integrity-manifest.json.

        Returns:
            The path where the manifest was written.
        """
        if output_path is None:
            output_path = self._repo_root / "governance" / "integrity-manifest.json"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")
        return output_path

    def load_manifest(self, manifest_path: str | Path | None = None) -> dict[str, Any]:
        """Load a manifest from disk.

        Args:
            manifest_path: Path to the manifest. Defaults to governance/integrity-manifest.json.

        Returns:
            The manifest dict.

        Raises:
            FileNotFoundError: If the manifest does not exist.
        """
        if manifest_path is None:
            manifest_path = self._repo_root / "governance" / "integrity-manifest.json"
        else:
            manifest_path = Path(manifest_path)

        with open(manifest_path) as f:
            return json.load(f)

    def verify(self, manifest_path: str | Path | None = None) -> VerificationResult:
        """Verify file integrity against a stored manifest.

        Args:
            manifest_path: Path to the manifest to verify against.

        Returns:
            VerificationResult with pass/fail details.
        """
        manifest = self.load_manifest(manifest_path)
        expected_files = manifest.get("files", {})

        current_hashes = self._collect_critical_files()
        failures = []
        missing_files = []
        new_files = []

        # Check files in manifest
        for path, expected_hash in expected_files.items():
            if path not in current_hashes:
                missing_files.append(path)
            elif current_hashes[path] != expected_hash:
                failures.append(path)

        # Check for new files not in manifest
        for path in current_hashes:
            if path not in expected_files:
                new_files.append(path)

        total = len(expected_files)
        verified = total - len(failures) - len(missing_files)

        return VerificationResult(
            valid=len(failures) == 0 and len(missing_files) == 0,
            total_files=total,
            verified_files=verified,
            failures=failures,
            missing_files=missing_files,
            new_files=new_files,
        )
