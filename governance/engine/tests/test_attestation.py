"""Tests for governance.engine.attestation — cryptographic merge attestation."""

import json

import pytest

from governance.engine.attestation import (
    AttestationManifest,
    InvalidManifestError,
    MergeAttestation,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def attestation():
    return MergeAttestation(signing_secret="test-signing-secret-2026")


@pytest.fixture
def sample_emissions():
    return {
        "code-review": {
            "panel_name": "code-review",
            "confidence_score": 0.92,
            "risk_level": "low",
            "aggregate_verdict": "approve",
        },
        "security-review": {
            "panel_name": "security-review",
            "confidence_score": 0.88,
            "risk_level": "low",
            "aggregate_verdict": "approve",
        },
        "threat-modeling": {
            "panel_name": "threat-modeling",
            "confidence_score": 0.85,
            "risk_level": "low",
            "aggregate_verdict": "approve",
        },
    }


# ---------------------------------------------------------------------------
# Manifest creation
# ---------------------------------------------------------------------------

class TestManifestCreation:
    def test_creates_manifest(self, attestation, sample_emissions):
        manifest = attestation.create_manifest(
            emissions=sample_emissions,
            decision="auto_merge",
            policy_profile="default",
            rationale="All panels approve with low risk",
        )
        assert manifest.decision == "auto_merge"
        assert manifest.policy_profile == "default"
        assert len(manifest.emission_hashes) == 3
        assert manifest.aggregate_hash
        assert manifest.signature
        assert manifest.manifest_id

    def test_custom_manifest_id(self, attestation, sample_emissions):
        manifest = attestation.create_manifest(
            emissions=sample_emissions,
            decision="auto_merge",
            policy_profile="default",
            manifest_id="custom-id-123",
        )
        assert manifest.manifest_id == "custom-id-123"

    def test_emission_hashes_are_sha256(self, attestation, sample_emissions):
        manifest = attestation.create_manifest(
            emissions=sample_emissions,
            decision="auto_merge",
            policy_profile="default",
        )
        for _name, hash_val in manifest.emission_hashes.items():
            assert len(hash_val) == 64
            assert all(c in "0123456789abcdef" for c in hash_val)

    def test_different_emissions_different_hashes(self, attestation):
        em1 = {"code-review": {"confidence_score": 0.92}}
        em2 = {"code-review": {"confidence_score": 0.50}}
        m1 = attestation.create_manifest(em1, "auto_merge", "default")
        m2 = attestation.create_manifest(em2, "block", "default")
        assert m1.emission_hashes["code-review"] != m2.emission_hashes["code-review"]

    def test_deterministic_hashing(self, attestation, sample_emissions):
        m1 = attestation.create_manifest(
            sample_emissions, "auto_merge", "default", manifest_id="fixed"
        )
        m2 = attestation.create_manifest(
            sample_emissions, "auto_merge", "default", manifest_id="fixed"
        )
        assert m1.emission_hashes == m2.emission_hashes
        assert m1.aggregate_hash == m2.aggregate_hash


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

class TestVerification:
    def test_verify_valid_manifest(self, attestation, sample_emissions):
        manifest = attestation.create_manifest(
            sample_emissions, "auto_merge", "default"
        )
        assert attestation.verify_manifest(manifest) is True

    def test_verify_tampered_decision(self, attestation, sample_emissions):
        manifest = attestation.create_manifest(
            sample_emissions, "auto_merge", "default"
        )
        # Tamper with decision
        tampered = AttestationManifest(
            manifest_id=manifest.manifest_id,
            timestamp=manifest.timestamp,
            policy_profile=manifest.policy_profile,
            decision="block",  # Changed!
            rationale=manifest.rationale,
            emission_hashes=manifest.emission_hashes,
            aggregate_hash=manifest.aggregate_hash,
            signature=manifest.signature,
        )
        with pytest.raises(InvalidManifestError, match="signature"):
            attestation.verify_manifest(tampered)

    def test_verify_tampered_emission_hash(self, attestation, sample_emissions):
        manifest = attestation.create_manifest(
            sample_emissions, "auto_merge", "default"
        )
        # Tamper with an emission hash
        tampered_hashes = dict(manifest.emission_hashes)
        tampered_hashes["code-review"] = "0" * 64
        tampered = AttestationManifest(
            manifest_id=manifest.manifest_id,
            timestamp=manifest.timestamp,
            policy_profile=manifest.policy_profile,
            decision=manifest.decision,
            rationale=manifest.rationale,
            emission_hashes=tampered_hashes,
            aggregate_hash=manifest.aggregate_hash,
            signature=manifest.signature,
        )
        with pytest.raises(InvalidManifestError):
            attestation.verify_manifest(tampered)

    def test_different_secrets_fail_verification(self, sample_emissions):
        att1 = MergeAttestation(signing_secret="secret-1")
        att2 = MergeAttestation(signing_secret="secret-2")
        manifest = att1.create_manifest(
            sample_emissions, "auto_merge", "default"
        )
        with pytest.raises(InvalidManifestError):
            att2.verify_manifest(manifest)


# ---------------------------------------------------------------------------
# Emission verification
# ---------------------------------------------------------------------------

class TestEmissionVerification:
    def test_verify_matching_emissions(self, attestation, sample_emissions):
        manifest = attestation.create_manifest(
            sample_emissions, "auto_merge", "default"
        )
        mismatches = attestation.verify_emissions(manifest, sample_emissions)
        assert mismatches == []

    def test_detect_modified_emission(self, attestation, sample_emissions):
        manifest = attestation.create_manifest(
            sample_emissions, "auto_merge", "default"
        )
        # Modify an emission after manifest creation
        modified = dict(sample_emissions)
        modified["code-review"] = {"panel_name": "code-review", "confidence_score": 0.10}
        mismatches = attestation.verify_emissions(manifest, modified)
        assert "code-review" in mismatches

    def test_detect_extra_emission(self, attestation, sample_emissions):
        manifest = attestation.create_manifest(
            sample_emissions, "auto_merge", "default"
        )
        # Add an emission not in manifest
        extra = dict(sample_emissions)
        extra["new-panel"] = {"panel_name": "new-panel"}
        mismatches = attestation.verify_emissions(manifest, extra)
        assert "new-panel" in mismatches


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_to_dict_and_from_dict(self, attestation, sample_emissions):
        manifest = attestation.create_manifest(
            sample_emissions, "auto_merge", "default"
        )
        d = manifest.to_dict()
        restored = AttestationManifest.from_dict(d)
        assert restored.manifest_id == manifest.manifest_id
        assert restored.signature == manifest.signature
        assert attestation.verify_manifest(restored) is True

    def test_write_and_read(self, attestation, sample_emissions, tmp_path):
        manifest = attestation.create_manifest(
            sample_emissions, "auto_merge", "default"
        )
        path = attestation.write_manifest(manifest, tmp_path / "manifest.json")
        with open(path) as f:
            data = json.load(f)
        restored = AttestationManifest.from_dict(data)
        assert attestation.verify_manifest(restored) is True

    def test_commit_message_hash(self, attestation, sample_emissions):
        manifest = attestation.create_manifest(
            sample_emissions, "auto_merge", "default"
        )
        msg = attestation.get_commit_message_hash(manifest)
        assert msg.startswith("governance-attestation: ")
        assert len(msg.split(": ")[1]) == 64


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_secret_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            MergeAttestation(signing_secret="")

    def test_empty_emissions(self, attestation):
        manifest = attestation.create_manifest(
            emissions={},
            decision="block",
            policy_profile="default",
        )
        assert manifest.emission_hashes == {}
        assert attestation.verify_manifest(manifest) is True

    def test_single_emission(self, attestation):
        manifest = attestation.create_manifest(
            emissions={"code-review": {"verdict": "approve"}},
            decision="auto_merge",
            policy_profile="default",
        )
        assert len(manifest.emission_hashes) == 1
        assert attestation.verify_manifest(manifest) is True
