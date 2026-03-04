#!/usr/bin/env python3
"""Cryptographic attestation for governance merge decisions.

Links panel emissions to merge decisions via signed run manifests.
Each manifest includes content hashes of all panel emissions, ensuring
the merge decision was based on specific, unmodified panel outputs.

Usage:
    from governance.engine.attestation import MergeAttestation

    attestation = MergeAttestation(signing_secret="session-secret")
    manifest = attestation.create_manifest(
        emissions={"code-review": {...}, "security-review": {...}},
        decision="auto_merge",
        policy_profile="default",
    )
    # Verify later
    assert attestation.verify_manifest(manifest)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AttestationManifest:
    """A signed manifest linking panel emissions to a merge decision."""

    manifest_id: str
    timestamp: str
    policy_profile: str
    decision: str          # "auto_merge", "block", "human_review_required", "auto_remediate"
    rationale: str
    emission_hashes: dict[str, str]  # panel_name -> SHA-256 of emission content
    aggregate_hash: str    # SHA-256 of all emission hashes combined
    signature: str         # HMAC-SHA256 of the manifest content

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "timestamp": self.timestamp,
            "policy_profile": self.policy_profile,
            "decision": self.decision,
            "rationale": self.rationale,
            "emission_hashes": self.emission_hashes,
            "aggregate_hash": self.aggregate_hash,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttestationManifest":
        return cls(
            manifest_id=data["manifest_id"],
            timestamp=data["timestamp"],
            policy_profile=data["policy_profile"],
            decision=data["decision"],
            rationale=data["rationale"],
            emission_hashes=data["emission_hashes"],
            aggregate_hash=data["aggregate_hash"],
            signature=data["signature"],
        )


class AttestationError(Exception):
    """Base exception for attestation errors."""
    pass


class InvalidManifestError(AttestationError):
    """Raised when a manifest fails verification."""
    pass


class MergeAttestation:
    """Cryptographic attestation engine for governance merge decisions.

    Args:
        signing_secret: Secret used for HMAC signing. Should be unique per
                       session or derived from a deployment key.
    """

    def __init__(self, signing_secret: str):
        if not signing_secret:
            raise ValueError("signing_secret must not be empty")
        self._secret = signing_secret.encode("utf-8")

    def _hash_content(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _hash_emission(self, emission: dict[str, Any]) -> str:
        """Compute SHA-256 hash of a panel emission."""
        canonical = json.dumps(emission, sort_keys=True, separators=(",", ":"))
        return self._hash_content(canonical)

    def _compute_aggregate_hash(self, emission_hashes: dict[str, str]) -> str:
        """Compute aggregate hash from individual emission hashes."""
        # Sort by panel name for determinism, then hash the concatenation
        combined = "".join(
            f"{name}:{hash_val}"
            for name, hash_val in sorted(emission_hashes.items())
        )
        return self._hash_content(combined)

    def _sign_manifest(self, manifest_data: dict[str, Any]) -> str:
        """Sign the manifest content with HMAC-SHA256."""
        # Remove signature field if present
        signable = {k: v for k, v in manifest_data.items() if k != "signature"}
        canonical = json.dumps(signable, sort_keys=True, separators=(",", ":"))
        return hmac.new(self._secret, canonical.encode("utf-8"), hashlib.sha256).hexdigest()

    def create_manifest(
        self,
        emissions: dict[str, dict[str, Any]],
        decision: str,
        policy_profile: str,
        rationale: str = "",
        manifest_id: str | None = None,
    ) -> AttestationManifest:
        """Create a signed attestation manifest.

        Args:
            emissions: Dict mapping panel names to emission dicts.
            decision: The governance decision (auto_merge, block, etc.).
            policy_profile: Name of the policy profile used.
            rationale: Explanation of the decision.
            manifest_id: Optional custom manifest ID. Auto-generated if None.

        Returns:
            A signed AttestationManifest.
        """
        # Hash each emission
        emission_hashes = {
            name: self._hash_emission(emission)
            for name, emission in emissions.items()
        }

        # Compute aggregate hash
        aggregate_hash = self._compute_aggregate_hash(emission_hashes)

        # Build manifest data
        if manifest_id is None:
            now = datetime.now(timezone.utc)
            short_id = uuid.uuid4().hex[:7]
            manifest_id = f"{now.strftime('%Y%m%d-%H%M%S')}-{short_id}"

        manifest_data = {
            "manifest_id": manifest_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "policy_profile": policy_profile,
            "decision": decision,
            "rationale": rationale,
            "emission_hashes": emission_hashes,
            "aggregate_hash": aggregate_hash,
        }

        # Sign
        signature = self._sign_manifest(manifest_data)
        manifest_data["signature"] = signature

        return AttestationManifest.from_dict(manifest_data)

    def verify_manifest(self, manifest: AttestationManifest) -> bool:
        """Verify a manifest's signature and internal consistency.

        Args:
            manifest: The manifest to verify.

        Returns:
            True if valid.

        Raises:
            InvalidManifestError: If verification fails.
        """
        data = manifest.to_dict()

        # Verify signature
        expected_sig = self._sign_manifest(data)
        if not hmac.compare_digest(manifest.signature, expected_sig):
            raise InvalidManifestError("Manifest signature is invalid")

        # Verify aggregate hash consistency
        expected_aggregate = self._compute_aggregate_hash(manifest.emission_hashes)
        if manifest.aggregate_hash != expected_aggregate:
            raise InvalidManifestError("Aggregate hash is inconsistent with emission hashes")

        return True

    def verify_emissions(
        self,
        manifest: AttestationManifest,
        emissions: dict[str, dict[str, Any]],
    ) -> list[str]:
        """Verify that emissions match the hashes in the manifest.

        Args:
            manifest: The manifest with expected hashes.
            emissions: The actual emissions to verify.

        Returns:
            List of panel names with mismatched hashes. Empty means all match.
        """
        mismatches = []
        for name, emission in emissions.items():
            expected_hash = manifest.emission_hashes.get(name)
            if expected_hash is None:
                mismatches.append(name)
                continue
            actual_hash = self._hash_emission(emission)
            if actual_hash != expected_hash:
                mismatches.append(name)
        return mismatches

    def write_manifest(
        self,
        manifest: AttestationManifest,
        output_path: str | Path,
    ) -> Path:
        """Write a manifest to disk as JSON.

        Args:
            manifest: The manifest to write.
            output_path: Where to write it.

        Returns:
            The path where the manifest was written.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(manifest.to_dict(), f, indent=2)
            f.write("\n")
        return path

    def get_commit_message_hash(self, manifest: AttestationManifest) -> str:
        """Get a hash suitable for embedding in a merge commit message.

        Returns:
            A string like "governance-attestation: <sha256>"
        """
        manifest_json = json.dumps(manifest.to_dict(), sort_keys=True, separators=(",", ":"))
        manifest_hash = hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()
        return f"governance-attestation: {manifest_hash}"
