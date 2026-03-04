"""Tests for governance.engine.supply_chain — integrity verification."""

import json

import pytest

from governance.engine.supply_chain import IntegrityVerifier, VerificationResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repo_with_files(tmp_path):
    """Create a minimal repo structure with governance files."""
    # Policy
    policy_dir = tmp_path / "governance" / "policy"
    policy_dir.mkdir(parents=True)
    (policy_dir / "default.yaml").write_text("profile_name: default\n")
    (policy_dir / "fast-track.yaml").write_text("profile_name: fast-track\n")

    # Schemas
    schemas_dir = tmp_path / "governance" / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / "panel-output.schema.json").write_text('{"type": "object"}\n')

    # Personas
    personas_dir = tmp_path / "governance" / "personas" / "agentic"
    personas_dir.mkdir(parents=True)
    (personas_dir / "coder.md").write_text("# Coder\n")
    (personas_dir / "tester.md").write_text("# Tester\n")

    # Review prompts
    reviews_dir = tmp_path / "governance" / "prompts" / "reviews"
    reviews_dir.mkdir(parents=True)
    (reviews_dir / "code-review.md").write_text("# Code Review\n")

    return tmp_path


@pytest.fixture
def verifier(repo_with_files):
    return IntegrityVerifier(repo_with_files)


# ---------------------------------------------------------------------------
# Manifest generation
# ---------------------------------------------------------------------------

class TestManifestGeneration:
    def test_generates_manifest(self, verifier):
        manifest = verifier.generate_manifest()
        assert manifest["manifest_version"] == "1.0.0"
        assert manifest["algorithm"] == "sha256"
        assert manifest["file_count"] > 0
        assert len(manifest["files"]) == manifest["file_count"]

    def test_manifest_contains_all_categories(self, verifier):
        manifest = verifier.generate_manifest()
        files = manifest["files"]
        # Should contain policy, schema, persona, and review files
        categories_found = set()
        for path in files:
            if "policy/" in path:
                categories_found.add("policy")
            elif "schemas/" in path:
                categories_found.add("schemas")
            elif "personas/" in path:
                categories_found.add("personas")
            elif "reviews/" in path:
                categories_found.add("reviews")
        assert categories_found == {"policy", "schemas", "personas", "reviews"}

    def test_manifest_has_sha256_hashes(self, verifier):
        manifest = verifier.generate_manifest()
        for _path, hash_val in manifest["files"].items():
            assert len(hash_val) == 64  # SHA-256 hex
            assert all(c in "0123456789abcdef" for c in hash_val)

    def test_manifest_has_timestamp(self, verifier):
        manifest = verifier.generate_manifest()
        assert "generated_at" in manifest
        assert "T" in manifest["generated_at"]

    def test_manifest_deterministic(self, verifier):
        m1 = verifier.generate_manifest()
        m2 = verifier.generate_manifest()
        assert m1["files"] == m2["files"]


# ---------------------------------------------------------------------------
# Manifest write/load
# ---------------------------------------------------------------------------

class TestManifestIO:
    def test_write_and_load(self, verifier, repo_with_files):
        manifest = verifier.generate_manifest()
        path = verifier.write_manifest(manifest)
        assert path.exists()
        loaded = verifier.load_manifest()
        assert loaded["files"] == manifest["files"]

    def test_write_to_custom_path(self, verifier, tmp_path):
        manifest = verifier.generate_manifest()
        custom_path = tmp_path / "custom" / "manifest.json"
        path = verifier.write_manifest(manifest, output_path=custom_path)
        assert path == custom_path
        assert path.exists()

    def test_load_missing_manifest_raises(self, verifier, tmp_path):
        with pytest.raises(FileNotFoundError):
            verifier.load_manifest(tmp_path / "nonexistent.json")


# ---------------------------------------------------------------------------
# Verification — passing
# ---------------------------------------------------------------------------

class TestVerificationPass:
    def test_verify_clean_repo(self, verifier):
        manifest = verifier.generate_manifest()
        verifier.write_manifest(manifest)
        result = verifier.verify()
        assert result.valid is True
        assert result.total_files > 0
        assert result.verified_files == result.total_files
        assert result.failures == []
        assert result.missing_files == []

    def test_verify_result_to_dict(self, verifier):
        manifest = verifier.generate_manifest()
        verifier.write_manifest(manifest)
        result = verifier.verify()
        d = result.to_dict()
        assert d["valid"] is True
        assert "total_files" in d
        assert "failures" in d


# ---------------------------------------------------------------------------
# Verification — tamper detection
# ---------------------------------------------------------------------------

class TestTamperDetection:
    def test_detects_modified_file(self, verifier, repo_with_files):
        manifest = verifier.generate_manifest()
        verifier.write_manifest(manifest)
        # Tamper with a file
        policy_file = repo_with_files / "governance" / "policy" / "default.yaml"
        policy_file.write_text("profile_name: TAMPERED\n")
        result = verifier.verify()
        assert result.valid is False
        assert "governance/policy/default.yaml" in result.failures

    def test_detects_deleted_file(self, verifier, repo_with_files):
        manifest = verifier.generate_manifest()
        verifier.write_manifest(manifest)
        # Delete a file
        (repo_with_files / "governance" / "policy" / "default.yaml").unlink()
        result = verifier.verify()
        assert result.valid is False
        assert "governance/policy/default.yaml" in result.missing_files

    def test_detects_new_file(self, verifier, repo_with_files):
        manifest = verifier.generate_manifest()
        verifier.write_manifest(manifest)
        # Add a new file
        (repo_with_files / "governance" / "policy" / "new-profile.yaml").write_text("new\n")
        result = verifier.verify()
        # New files don't make the verification invalid (additive)
        assert "governance/policy/new-profile.yaml" in result.new_files

    def test_multiple_tampered_files(self, verifier, repo_with_files):
        manifest = verifier.generate_manifest()
        verifier.write_manifest(manifest)
        # Tamper with multiple files
        (repo_with_files / "governance" / "policy" / "default.yaml").write_text("tampered\n")
        (repo_with_files / "governance" / "schemas" / "panel-output.schema.json").write_text("tampered\n")
        result = verifier.verify()
        assert result.valid is False
        assert len(result.failures) == 2


# ---------------------------------------------------------------------------
# Real repo verification
# ---------------------------------------------------------------------------

class TestRealRepo:
    def test_can_generate_manifest_for_real_repo(self):
        """Verify the manifest generator works on the actual repo."""
        from pathlib import Path
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        verifier = IntegrityVerifier(repo_root)
        manifest = verifier.generate_manifest()
        assert manifest["file_count"] > 0
        # Should have files in all critical categories
        assert any("policy/" in p for p in manifest["files"])
        assert any("schemas/" in p for p in manifest["files"])
        assert any("personas/" in p for p in manifest["files"])
