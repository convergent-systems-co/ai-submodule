"""Tests for the emission migration CLI and migration logic."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

from conftest import REPO_ROOT

# Ensure governance.bin.migrate-emissions is importable
sys.path.insert(0, str(REPO_ROOT))

# Import from the migration module using importlib since filename has hyphens
import importlib.util

_MIGRATE_SCRIPT = REPO_ROOT / "governance" / "bin" / "migrate-emissions.py"
_spec = importlib.util.spec_from_file_location("migrate_emissions", _MIGRATE_SCRIPT)
migrate_emissions = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migrate_emissions)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_emission():
    """A minimal valid emission without schema_version."""
    return {
        "panel_name": "code-review",
        "panel_version": "1.0.0",
        "confidence_score": 0.90,
        "risk_level": "low",
        "compliance_score": 1.0,
        "policy_flags": [],
        "requires_human_review": False,
        "timestamp": "2026-02-27T00:00:00Z",
        "findings": [
            {
                "persona": "quality/code-reviewer",
                "verdict": "approve",
                "confidence": 0.90,
                "rationale": "Test finding.",
            }
        ],
        "aggregate_verdict": "approve",
    }


@pytest.fixture
def sample_emission_with_version(sample_emission):
    """An emission that already has schema_version."""
    sample_emission["schema_version"] = "1.0.0"
    return sample_emission


@pytest.fixture
def migrations_dir(tmp_path):
    """Create a temporary migrations directory with test rules."""
    mdir = tmp_path / "migrations"
    mdir.mkdir()
    return mdir


@pytest.fixture
def emissions_dir(tmp_path):
    """Create a temporary emissions directory."""
    edir = tmp_path / "emissions"
    edir.mkdir()
    return edir


def write_migration(mdir: Path, from_ver: str, to_ver: str, transforms: list) -> Path:
    """Helper to write a migration rule file."""
    rule = {
        "from_version": from_ver,
        "to_version": to_ver,
        "description": f"Migrate {from_ver} to {to_ver}",
        "transforms": transforms,
    }
    fpath = mdir / f"v{from_ver}_to_v{to_ver}.json"
    with open(fpath, "w") as f:
        json.dump(rule, f, indent=2)
    return fpath


def write_emission(edir: Path, name: str, data: dict) -> Path:
    """Helper to write an emission file."""
    fpath = edir / f"{name}.json"
    with open(fpath, "w") as f:
        json.dump(data, f, indent=2)
    return fpath


# ===========================================================================
# Test: detect_schema_version
# ===========================================================================


class TestDetectSchemaVersion:
    def test_detect_schema_version_present(self, sample_emission_with_version):
        """Detects version from emission that has schema_version field."""
        assert migrate_emissions.detect_schema_version(sample_emission_with_version) == "1.0.0"

    def test_detect_schema_version_missing(self, sample_emission):
        """Defaults to 1.0.0 when schema_version is absent."""
        assert migrate_emissions.detect_schema_version(sample_emission) == "1.0.0"

    def test_detect_schema_version_custom(self):
        """Detects a non-default version."""
        emission = {"schema_version": "2.3.1"}
        assert migrate_emissions.detect_schema_version(emission) == "2.3.1"


# ===========================================================================
# Test: add_field transform
# ===========================================================================


class TestAddFieldTransform:
    def test_add_field_transform(self, sample_emission):
        """Applies add_field transform correctly when field is missing."""
        transform = {
            "type": "add_field",
            "field": "schema_version",
            "default_value": "1.1.0",
            "condition": "field_missing",
        }
        updated, changes = migrate_emissions.apply_transform(sample_emission, transform)
        assert updated["schema_version"] == "1.1.0"
        assert len(changes) == 1
        assert "added" in changes[0]

    def test_add_field_skips_when_present(self, sample_emission_with_version):
        """Does not overwrite when field already exists and condition is field_missing."""
        transform = {
            "type": "add_field",
            "field": "schema_version",
            "default_value": "1.1.0",
            "condition": "field_missing",
        }
        updated, changes = migrate_emissions.apply_transform(
            sample_emission_with_version, transform
        )
        assert updated["schema_version"] == "1.0.0"  # unchanged
        assert len(changes) == 0

    def test_add_field_no_condition(self, sample_emission):
        """Adds field unconditionally when no condition specified."""
        transform = {
            "type": "add_field",
            "field": "new_field",
            "default_value": "hello",
        }
        updated, changes = migrate_emissions.apply_transform(sample_emission, transform)
        assert updated["new_field"] == "hello"
        assert len(changes) == 1


# ===========================================================================
# Test: rename_field transform
# ===========================================================================


class TestRenameFieldTransform:
    def test_rename_field(self, sample_emission):
        """Renames an existing field."""
        sample_emission["old_name"] = "value"
        transform = {
            "type": "rename_field",
            "old_field": "old_name",
            "new_field": "new_name",
            "condition": "field_exists",
        }
        updated, changes = migrate_emissions.apply_transform(sample_emission, transform)
        assert "old_name" not in updated
        assert updated["new_name"] == "value"
        assert len(changes) == 1

    def test_rename_field_missing(self, sample_emission):
        """Does nothing when old field does not exist."""
        transform = {
            "type": "rename_field",
            "old_field": "nonexistent",
            "new_field": "new_name",
        }
        updated, changes = migrate_emissions.apply_transform(sample_emission, transform)
        assert "new_name" not in updated


# ===========================================================================
# Test: set_default transform
# ===========================================================================


class TestSetDefaultTransform:
    def test_set_default_when_missing(self, sample_emission):
        """Sets default value for a missing field."""
        transform = {
            "type": "set_default",
            "field": "execution_status",
            "default_value": "success",
        }
        updated, changes = migrate_emissions.apply_transform(sample_emission, transform)
        assert updated["execution_status"] == "success"
        assert len(changes) == 1

    def test_set_default_when_null(self, sample_emission):
        """Sets default value when field is null."""
        sample_emission["execution_status"] = None
        transform = {
            "type": "set_default",
            "field": "execution_status",
            "default_value": "success",
        }
        updated, changes = migrate_emissions.apply_transform(sample_emission, transform)
        assert updated["execution_status"] == "success"

    def test_set_default_preserves_existing(self, sample_emission):
        """Does not overwrite an existing non-null value."""
        sample_emission["execution_status"] = "error"
        transform = {
            "type": "set_default",
            "field": "execution_status",
            "default_value": "success",
        }
        updated, changes = migrate_emissions.apply_transform(sample_emission, transform)
        assert updated["execution_status"] == "error"
        assert len(changes) == 0


# ===========================================================================
# Test: remove_field transform
# ===========================================================================


class TestRemoveFieldTransform:
    def test_remove_field(self, sample_emission):
        """Removes an existing field."""
        sample_emission["deprecated_field"] = "old_value"
        transform = {
            "type": "remove_field",
            "field": "deprecated_field",
            "condition": "field_exists",
        }
        updated, changes = migrate_emissions.apply_transform(sample_emission, transform)
        assert "deprecated_field" not in updated
        assert len(changes) == 1

    def test_remove_field_missing(self, sample_emission):
        """Does nothing when field does not exist (condition: field_exists)."""
        transform = {
            "type": "remove_field",
            "field": "nonexistent",
            "condition": "field_exists",
        }
        updated, changes = migrate_emissions.apply_transform(sample_emission, transform)
        assert len(changes) == 0


# ===========================================================================
# Test: dry run
# ===========================================================================


class TestDryRun:
    def test_dry_run_no_changes(self, sample_emission, emissions_dir, migrations_dir):
        """Dry run prints changes but does not modify files."""
        write_emission(emissions_dir, "code-review", sample_emission)
        write_migration(migrations_dir, "1.0.0", "1.1.0", [
            {
                "type": "add_field",
                "field": "schema_version",
                "default_value": "1.1.0",
                "condition": "field_missing",
            }
        ])

        # Run in dry-run mode
        result = migrate_emissions.main([
            "--from-version", "1.0.0",
            "--to-version", "1.1.0",
            "--path", str(emissions_dir),
            "--migrations-dir", str(migrations_dir),
            "--dry-run",
        ])
        assert result == 0

        # Verify file was NOT modified
        with open(emissions_dir / "code-review.json") as f:
            data = json.load(f)
        assert "schema_version" not in data


# ===========================================================================
# Test: missing migration path
# ===========================================================================


class TestMissingMigrationPath:
    def test_missing_migration_path(self, migrations_dir, emissions_dir):
        """Error when no migration chain exists between versions."""
        # Only have 1.0.0 -> 1.1.0 migration
        write_migration(migrations_dir, "1.0.0", "1.1.0", [])

        result = migrate_emissions.main([
            "--from-version", "1.0.0",
            "--to-version", "2.0.0",
            "--path", str(emissions_dir),
            "--migrations-dir", str(migrations_dir),
        ])
        assert result == 1

    def test_no_migrations_at_all(self, tmp_path, emissions_dir):
        """Error when migrations directory has no rules."""
        empty_mdir = tmp_path / "empty_migrations"
        empty_mdir.mkdir()

        result = migrate_emissions.main([
            "--from-version", "1.0.0",
            "--to-version", "1.1.0",
            "--path", str(emissions_dir),
            "--migrations-dir", str(empty_mdir),
        ])
        assert result == 1

    def test_no_starting_migration(self, migrations_dir, emissions_dir):
        """Error when starting version has no migration rule."""
        write_migration(migrations_dir, "2.0.0", "2.1.0", [])

        result = migrate_emissions.main([
            "--from-version", "1.0.0",
            "--to-version", "2.1.0",
            "--path", str(emissions_dir),
            "--migrations-dir", str(migrations_dir),
        ])
        assert result == 1


# ===========================================================================
# Test: chain migrations
# ===========================================================================


class TestChainMigrations:
    def test_chain_migrations(self, sample_emission, emissions_dir, migrations_dir):
        """Chains multiple migrations sequentially (1.0.0 -> 1.1.0 -> 1.2.0)."""
        write_emission(emissions_dir, "code-review", sample_emission)

        # Create two migration steps
        write_migration(migrations_dir, "1.0.0", "1.1.0", [
            {
                "type": "add_field",
                "field": "schema_version",
                "default_value": "1.1.0",
                "condition": "field_missing",
            }
        ])
        write_migration(migrations_dir, "1.1.0", "1.2.0", [
            {
                "type": "add_field",
                "field": "migration_note",
                "default_value": "migrated-to-1.2.0",
                "condition": "field_missing",
            }
        ])

        result = migrate_emissions.main([
            "--from-version", "1.0.0",
            "--to-version", "1.2.0",
            "--path", str(emissions_dir),
            "--migrations-dir", str(migrations_dir),
        ])
        assert result == 0

        # Verify file was updated with both migrations
        with open(emissions_dir / "code-review.json") as f:
            data = json.load(f)
        assert data["schema_version"] == "1.2.0"
        assert data["migration_note"] == "migrated-to-1.2.0"

    def test_chain_three_migrations(self, sample_emission, emissions_dir, migrations_dir):
        """Chains three migrations (1.0.0 -> 1.1.0 -> 1.2.0 -> 2.0.0)."""
        write_emission(emissions_dir, "test-emission", sample_emission)

        write_migration(migrations_dir, "1.0.0", "1.1.0", [
            {"type": "add_field", "field": "schema_version", "default_value": "1.1.0",
             "condition": "field_missing"}
        ])
        write_migration(migrations_dir, "1.1.0", "1.2.0", [
            {"type": "add_field", "field": "field_a", "default_value": "a",
             "condition": "field_missing"}
        ])
        write_migration(migrations_dir, "1.2.0", "2.0.0", [
            {"type": "add_field", "field": "field_b", "default_value": "b",
             "condition": "field_missing"}
        ])

        result = migrate_emissions.main([
            "--from-version", "1.0.0",
            "--to-version", "2.0.0",
            "--path", str(emissions_dir),
            "--migrations-dir", str(migrations_dir),
        ])
        assert result == 0

        with open(emissions_dir / "test-emission.json") as f:
            data = json.load(f)
        assert data["schema_version"] == "2.0.0"
        assert data["field_a"] == "a"
        assert data["field_b"] == "b"


# ===========================================================================
# Test: build_migration_chain
# ===========================================================================


class TestBuildMigrationChain:
    def test_single_step(self, migrations_dir):
        """Builds a single-step chain."""
        write_migration(migrations_dir, "1.0.0", "1.1.0", [])
        migrations = migrate_emissions.discover_migrations(migrations_dir)
        chain = migrate_emissions.build_migration_chain(migrations, "1.0.0", "1.1.0")
        assert len(chain) == 1
        assert chain[0]["from_version"] == "1.0.0"
        assert chain[0]["to_version"] == "1.1.0"

    def test_multi_step(self, migrations_dir):
        """Builds a multi-step chain."""
        write_migration(migrations_dir, "1.0.0", "1.1.0", [])
        write_migration(migrations_dir, "1.1.0", "1.2.0", [])
        migrations = migrate_emissions.discover_migrations(migrations_dir)
        chain = migrate_emissions.build_migration_chain(migrations, "1.0.0", "1.2.0")
        assert len(chain) == 2

    def test_raises_on_missing_path(self, migrations_dir):
        """Raises ValueError when no chain connects the versions."""
        write_migration(migrations_dir, "1.0.0", "1.1.0", [])
        migrations = migrate_emissions.discover_migrations(migrations_dir)
        with pytest.raises(ValueError, match="chain broken"):
            migrate_emissions.build_migration_chain(migrations, "1.0.0", "2.0.0")

    def test_raises_on_no_starting_rule(self, migrations_dir):
        """Raises ValueError when from_version has no rule."""
        write_migration(migrations_dir, "2.0.0", "2.1.0", [])
        migrations = migrate_emissions.discover_migrations(migrations_dir)
        with pytest.raises(ValueError, match="No migration found"):
            migrate_emissions.build_migration_chain(migrations, "1.0.0", "2.1.0")


# ===========================================================================
# Test: full migration with actual emissions
# ===========================================================================


class TestFullMigration:
    def test_migrate_actual_emissions_path(self):
        """Verify migration rules in the repo can be discovered."""
        migrations = migrate_emissions.discover_migrations(_MIGRATE_SCRIPT.parent.parent / "migrations")
        assert "1.0.0" in migrations
        assert migrations["1.0.0"]["to_version"] == "1.1.0"

    def test_multiple_emissions(self, emissions_dir, migrations_dir):
        """Migrates multiple emission files in one run."""
        for name in ["code-review", "security-review", "cost-analysis"]:
            write_emission(emissions_dir, name, {
                "panel_name": name,
                "panel_version": "1.0.0",
            })

        write_migration(migrations_dir, "1.0.0", "1.1.0", [
            {"type": "add_field", "field": "schema_version", "default_value": "1.1.0",
             "condition": "field_missing"}
        ])

        result = migrate_emissions.main([
            "--from-version", "1.0.0",
            "--to-version", "1.1.0",
            "--path", str(emissions_dir),
            "--migrations-dir", str(migrations_dir),
        ])
        assert result == 0

        for name in ["code-review", "security-review", "cost-analysis"]:
            with open(emissions_dir / f"{name}.json") as f:
                data = json.load(f)
            assert data["schema_version"] == "1.1.0"
