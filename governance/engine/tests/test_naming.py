"""Unit tests for the Azure resource naming module."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Repo root is four levels up: tests/ -> engine/ -> governance/ -> repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from governance.engine.naming import (
    NamingError,
    NamingInput,
    generate_name,
    list_resource_types,
    validate_name,
)
from governance.engine.naming_data import RESOURCE_TYPES, VALID_LOBS, VALID_STAGES


# ===========================================================================
# NamingInput validation
# ===========================================================================


class TestNamingInputValidation:
    """Verify that NamingInput rejects bad inputs early."""

    def test_invalid_resource_type(self):
        with pytest.raises(NamingError, match="Unsupported resource type"):
            NamingInput(
                resource_type="Microsoft.Fake/stuff",
                lob="set",
                stage="dev",
                app_name="myapp",
                app_id="a",
                role="web",
            )

    def test_invalid_lob(self):
        with pytest.raises(NamingError, match="Invalid LOB"):
            NamingInput(
                resource_type="Microsoft.Sql/servers",
                lob="badlob",
                stage="dev",
                app_name="myapp",
                app_id="a",
                role="web",
            )

    def test_invalid_stage(self):
        with pytest.raises(NamingError, match="Invalid stage"):
            NamingInput(
                resource_type="Microsoft.Sql/servers",
                lob="set",
                stage="badstage",
                app_name="myapp",
                app_id="a",
                role="web",
            )

    def test_invalid_app_id_too_long(self):
        with pytest.raises(NamingError, match="Invalid app_id"):
            NamingInput(
                resource_type="Microsoft.Sql/servers",
                lob="set",
                stage="dev",
                app_name="myapp",
                app_id="ab",
                role="web",
            )

    def test_invalid_app_id_number(self):
        with pytest.raises(NamingError, match="Invalid app_id"):
            NamingInput(
                resource_type="Microsoft.Sql/servers",
                lob="set",
                stage="dev",
                app_name="myapp",
                app_id="1",
                role="web",
            )

    def test_empty_app_name(self):
        with pytest.raises(NamingError, match="app_name is required"):
            NamingInput(
                resource_type="Microsoft.Sql/servers",
                lob="set",
                stage="dev",
                app_name="",
                app_id="a",
                role="web",
            )

    def test_role_required_for_standard(self):
        with pytest.raises(NamingError, match="role is required"):
            NamingInput(
                resource_type="Microsoft.Sql/servers",
                lob="set",
                stage="dev",
                app_name="myapp",
                app_id="a",
                role="",
            )

    def test_role_not_required_for_mini(self):
        """Mini pattern should not require role."""
        inp = NamingInput(
            resource_type="Microsoft.KeyVault/vaults",
            lob="set",
            stage="dev",
            app_name="myapp",
            app_id="a",
            role="",
        )
        assert inp.resource_type == "Microsoft.KeyVault/vaults"

    def test_role_not_required_for_small(self):
        """Small pattern should not require role."""
        inp = NamingInput(
            resource_type="Microsoft.AppConfiguration/configurationStores",
            lob="set",
            stage="dev",
            app_name="myapp",
            app_id="a",
            role="",
        )
        assert inp.resource_type == "Microsoft.AppConfiguration/configurationStores"

    def test_valid_app_id_with_si(self):
        """app_id 'a-si' (shared infrastructure) should be valid."""
        inp = NamingInput(
            resource_type="Microsoft.Sql/servers",
            lob="set",
            stage="dev",
            app_name="myapp",
            app_id="a-si",
            role="web",
        )
        assert inp.app_id == "a-si"

    def test_multiple_errors_reported(self):
        """All validation errors should be combined."""
        with pytest.raises(NamingError) as exc_info:
            NamingInput(
                resource_type="Microsoft.Fake/stuff",
                lob="badlob",
                stage="badstage",
                app_name="",
                app_id="99",
            )
        msg = str(exc_info.value)
        assert "Unsupported resource type" in msg
        assert "Invalid LOB" in msg
        assert "Invalid stage" in msg
        assert "Invalid app_id" in msg
        assert "app_name is required" in msg


# ===========================================================================
# Standard pattern generation
# ===========================================================================


class TestStandardPattern:
    def test_basic_sql_server(self):
        inp = NamingInput(
            resource_type="Microsoft.Sql/servers",
            lob="set",
            stage="dev",
            app_name="payments",
            app_id="a",
            role="db",
        )
        name = generate_name(inp)
        assert name == "sql-set-dev-payments-db-a"

    def test_with_location(self):
        inp = NamingInput(
            resource_type="Microsoft.Sql/servers",
            lob="jma",
            stage="prod",
            app_name="billing",
            app_id="b",
            role="api",
            location="eastus",
        )
        name = generate_name(inp)
        assert name == "sql-jma-prod-billing-api-eastus-b"

    def test_with_si_suffix(self):
        inp = NamingInput(
            resource_type="Microsoft.Sql/servers",
            lob="set",
            stage="dev",
            app_name="shared",
            app_id="a-si",
            role="db",
        )
        name = generate_name(inp)
        assert name == "sql-set-dev-shared-db-a-si"

    def test_case_normalized(self):
        """All inputs should be lowercased in the output."""
        inp = NamingInput(
            resource_type="Microsoft.Sql/servers",
            lob="SET",
            stage="DEV",
            app_name="MyApp",
            app_id="A",
            role="Web",
        )
        name = generate_name(inp)
        assert name == "sql-set-dev-myapp-web-a"
        assert name == name.lower()

    def test_all_standard_resources_generate(self):
        """Every standard-pattern resource type should produce a valid name."""
        for rt, info in RESOURCE_TYPES.items():
            if info.pattern != "standard":
                continue
            inp = NamingInput(
                resource_type=rt,
                lob="set",
                stage="dev",
                app_name="testapp",
                app_id="a",
                role="web",
            )
            name = generate_name(inp)
            assert name.startswith(f"{info.prefix}-")
            assert len(name) <= info.max_length, (
                f"{rt}: name '{name}' ({len(name)} chars) exceeds max {info.max_length}"
            )


# ===========================================================================
# Mini pattern generation
# ===========================================================================


class TestMiniPattern:
    def test_keyvault(self):
        inp = NamingInput(
            resource_type="Microsoft.KeyVault/vaults",
            lob="set",
            stage="dev",
            app_name="myapp",
            app_id="a",
        )
        name = generate_name(inp)
        assert name == "kvsetdevmyapp"
        assert "-" not in name
        assert len(name) <= 24

    def test_storage_account(self):
        inp = NamingInput(
            resource_type="Microsoft.Storage/storageAccounts",
            lob="jma",
            stage="prod",
            app_name="datalake",
            app_id="b",
        )
        name = generate_name(inp)
        assert name == "stjmaproddatalake"
        assert "-" not in name
        assert len(name) <= 24

    def test_container_registry(self):
        inp = NamingInput(
            resource_type="Microsoft.ContainerRegistry/registries",
            lob="set",
            stage="dev",
            app_name="platform",
            app_id="a",
        )
        name = generate_name(inp)
        assert name == "crsetdevplatform"
        assert "-" not in name
        assert len(name) <= 50

    def test_mini_truncation_for_long_name(self):
        """Long app names should be truncated for mini pattern."""
        inp = NamingInput(
            resource_type="Microsoft.KeyVault/vaults",
            lob="set",
            stage="dev",
            app_name="verylongapplicationname",
            app_id="a",
        )
        name = generate_name(inp)
        # kv(2) + set(3) + dev(3) = 8 fixed; budget = 24 - 8 = 16
        assert len(name) <= 24
        assert name.startswith("kvsetdev")

    def test_mini_strips_hyphens_from_app_name(self):
        """Hyphens in app_name should be removed for mini pattern."""
        inp = NamingInput(
            resource_type="Microsoft.KeyVault/vaults",
            lob="set",
            stage="dev",
            app_name="my-cool-app",
            app_id="a",
        )
        name = generate_name(inp)
        assert "-" not in name
        assert "mycoolapp" in name

    def test_all_mini_resources_generate(self):
        """Every mini-pattern resource type should produce a valid name."""
        for rt, info in RESOURCE_TYPES.items():
            if info.pattern != "mini":
                continue
            inp = NamingInput(
                resource_type=rt,
                lob="set",
                stage="dev",
                app_name="testapp",
                app_id="a",
            )
            name = generate_name(inp)
            assert "-" not in name
            assert len(name) <= info.max_length, (
                f"{rt}: name '{name}' ({len(name)} chars) exceeds max {info.max_length}"
            )


# ===========================================================================
# Small pattern generation
# ===========================================================================


class TestSmallPattern:
    def test_app_configuration(self):
        inp = NamingInput(
            resource_type="Microsoft.AppConfiguration/configurationStores",
            lob="set",
            stage="dev",
            app_name="platform",
            app_id="a",
        )
        name = generate_name(inp)
        assert name == "appcs-set-dev-platform"

    def test_app_insights(self):
        inp = NamingInput(
            resource_type="Microsoft.Insights/components",
            lob="jma",
            stage="prod",
            app_name="analytics",
            app_id="b",
        )
        name = generate_name(inp)
        assert name == "appi-jma-prod-analytics"

    def test_small_truncation(self):
        """Long names should be truncated for small pattern."""
        inp = NamingInput(
            resource_type="Microsoft.AppConfiguration/configurationStores",
            lob="set",
            stage="dev",
            app_name="a" * 100,
            app_id="a",
        )
        name = generate_name(inp)
        assert len(name) <= 50

    def test_all_small_resources_generate(self):
        """Every small-pattern resource type should produce a valid name."""
        for rt, info in RESOURCE_TYPES.items():
            if info.pattern != "small":
                continue
            inp = NamingInput(
                resource_type=rt,
                lob="set",
                stage="dev",
                app_name="testapp",
                app_id="a",
            )
            name = generate_name(inp)
            assert len(name) <= info.max_length


# ===========================================================================
# Deterministic shortening
# ===========================================================================


class TestDeterministicShortening:
    def test_app_name_truncated_before_role(self):
        """When name is too long, appName truncates first, role stays intact."""
        inp = NamingInput(
            resource_type="Microsoft.Web/serverfarms",  # max 40
            lob="set",
            stage="dev",
            app_name="averylongapplicationname",
            app_id="a",
            role="web",
        )
        name = generate_name(inp)
        assert len(name) <= 40
        # Role should be intact
        assert "-web-" in name
        # prefix, lob, stage, appId all present
        assert name.startswith("plan-set-dev-")
        assert name.endswith("-a")

    def test_role_truncated_after_app_name(self):
        """If appName at min (1 char) and still too long, role gets truncated."""
        inp = NamingInput(
            resource_type="Microsoft.Web/serverfarms",  # max 40
            lob="setf",
            stage="nonprod",
            app_name="app",
            app_id="a-si",
            role="a" * 40,  # very long role
        )
        name = generate_name(inp)
        assert len(name) <= 40
        assert name.startswith("plan-setf-nonprod-")

    def test_shortening_preserves_fixed_parts(self):
        """prefix, lob, stage, appId are never truncated."""
        inp = NamingInput(
            resource_type="Microsoft.DocumentDB/databaseAccounts",  # cosmos, max 44
            lob="lexus",
            stage="nonprod",
            app_name="superlongapplicationname",
            app_id="a-si",
            role="database",
        )
        name = generate_name(inp)
        assert len(name) <= 44
        assert name.startswith("cosmos-lexus-nonprod-")
        assert name.endswith("-a-si")

    def test_shortening_is_deterministic(self):
        """Same inputs always produce the same output."""
        inp = NamingInput(
            resource_type="Microsoft.Web/serverfarms",
            lob="set",
            stage="dev",
            app_name="longname",
            app_id="a",
            role="web",
        )
        name1 = generate_name(inp)
        name2 = generate_name(inp)
        assert name1 == name2


# ===========================================================================
# Name validation
# ===========================================================================


class TestValidateName:
    def test_valid_name(self):
        result = validate_name("sql-set-dev-payments-db-a", "Microsoft.Sql/servers")
        assert result["valid"] is True
        assert result["errors"] == []

    def test_exceeds_max_length(self):
        long_name = "sql-" + "a" * 100
        result = validate_name(long_name, "Microsoft.Sql/servers")
        assert result["valid"] is False
        assert any("exceeds maximum" in e for e in result["errors"])

    def test_hyphens_rejected_for_mini(self):
        result = validate_name("kv-set-dev-app", "Microsoft.KeyVault/vaults")
        assert result["valid"] is False
        assert any("Hyphens are not allowed" in e for e in result["errors"])

    def test_wrong_prefix(self):
        result = validate_name("wrongprefix-set-dev-app-web-a", "Microsoft.Sql/servers")
        assert result["valid"] is False
        assert any("should start with" in e for e in result["errors"])

    def test_unsupported_resource_type(self):
        result = validate_name("anything", "Microsoft.Fake/stuff")
        assert result["valid"] is False
        assert any("Unsupported" in e for e in result["errors"])

    def test_empty_name(self):
        result = validate_name("", "Microsoft.Sql/servers")
        assert result["valid"] is False

    def test_leading_hyphen(self):
        result = validate_name("-sql-set-dev-app-web-a", "Microsoft.Sql/servers")
        assert result["valid"] is False
        assert any("start or end with a hyphen" in e for e in result["errors"])

    def test_trailing_hyphen(self):
        result = validate_name("sql-set-dev-app-web-a-", "Microsoft.Sql/servers")
        assert result["valid"] is False

    def test_includes_length_info(self):
        result = validate_name("sql-set-dev-app-web-a", "Microsoft.Sql/servers")
        assert result["max_length"] == 63
        assert result["actual_length"] == len("sql-set-dev-app-web-a")


# ===========================================================================
# list_resource_types
# ===========================================================================


class TestListResourceTypes:
    def test_returns_all_types(self):
        types = list_resource_types()
        assert len(types) == len(RESOURCE_TYPES)

    def test_sorted_by_resource_type(self):
        types = list_resource_types()
        names = [t["resource_type"] for t in types]
        assert names == sorted(names)

    def test_entry_shape(self):
        types = list_resource_types()
        for t in types:
            assert "resource_type" in t
            assert "prefix" in t
            assert "max_length" in t
            assert "pattern" in t
            assert "allows_hyphens" in t


# ===========================================================================
# Resource data integrity
# ===========================================================================


class TestResourceDataIntegrity:
    def test_all_lobs_are_lowercase(self):
        for lob in VALID_LOBS:
            assert lob == lob.lower()

    def test_all_stages_are_lowercase(self):
        for stage in VALID_STAGES:
            assert stage == stage.lower()

    def test_all_prefixes_are_lowercase(self):
        for info in RESOURCE_TYPES.values():
            assert info.prefix == info.prefix.lower()

    def test_max_lengths_are_positive(self):
        for info in RESOURCE_TYPES.values():
            assert info.max_length > 0

    def test_patterns_are_valid(self):
        valid_patterns = {"standard", "mini", "small"}
        for info in RESOURCE_TYPES.values():
            assert info.pattern in valid_patterns, (
                f"{info.resource_type} has invalid pattern '{info.pattern}'"
            )

    def test_mini_pattern_disallows_hyphens(self):
        """All mini-pattern resources should not allow hyphens."""
        for info in RESOURCE_TYPES.values():
            if info.pattern == "mini":
                assert info.allows_hyphens is False, (
                    f"{info.resource_type} is mini but allows hyphens"
                )

    def test_expected_resource_count(self):
        """We should have at least 22 resource types defined."""
        assert len(RESOURCE_TYPES) >= 22


# ===========================================================================
# CLI integration tests
# ===========================================================================


class TestCLI:
    """Test the CLI entry point via subprocess."""

    CLI_PATH = str(REPO_ROOT / "bin" / "generate-name.py")

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, self.CLI_PATH, *args],
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_list_types(self):
        result = self._run("--list-types")
        assert result.returncode == 0
        assert "Microsoft.Sql/servers" in result.stdout

    def test_list_types_json(self):
        result = self._run("--list-types", "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_generate_standard(self):
        result = self._run(
            "--resource-type", "Microsoft.Sql/servers",
            "--lob", "set",
            "--stage", "dev",
            "--app-name", "payments",
            "--app-id", "a",
            "--role", "db",
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "sql-set-dev-payments-db-a"

    def test_generate_json(self):
        result = self._run(
            "--resource-type", "Microsoft.Sql/servers",
            "--lob", "set",
            "--stage", "dev",
            "--app-name", "payments",
            "--app-id", "a",
            "--role", "db",
            "--json",
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["name"] == "sql-set-dev-payments-db-a"
        assert data["resource_type"] == "Microsoft.Sql/servers"
        assert data["length"] == len("sql-set-dev-payments-db-a")

    def test_generate_mini(self):
        result = self._run(
            "--resource-type", "Microsoft.KeyVault/vaults",
            "--lob", "set",
            "--stage", "dev",
            "--app-name", "myapp",
            "--app-id", "a",
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "kvsetdevmyapp"

    def test_validate_valid(self):
        result = self._run(
            "--validate-only", "sql-set-dev-payments-db-a",
            "--resource-type", "Microsoft.Sql/servers",
        )
        assert result.returncode == 0
        assert "VALID" in result.stdout

    def test_validate_invalid(self):
        result = self._run(
            "--validate-only", "kv-bad-name",
            "--resource-type", "Microsoft.KeyVault/vaults",
        )
        assert result.returncode == 1
        assert "INVALID" in result.stdout

    def test_missing_required_args(self):
        result = self._run(
            "--resource-type", "Microsoft.Sql/servers",
            "--lob", "set",
        )
        assert result.returncode == 1
        assert "required" in result.stderr.lower()

    def test_invalid_lob_error(self):
        result = self._run(
            "--resource-type", "Microsoft.Sql/servers",
            "--lob", "invalid",
            "--stage", "dev",
            "--app-name", "myapp",
            "--app-id", "a",
            "--role", "web",
        )
        assert result.returncode == 1

    def test_validate_without_resource_type(self):
        result = self._run("--validate-only", "some-name")
        assert result.returncode == 1
        assert "--resource-type" in result.stderr

    def test_generate_with_location(self):
        result = self._run(
            "--resource-type", "Microsoft.Sql/servers",
            "--lob", "set",
            "--stage", "dev",
            "--app-name", "payments",
            "--app-id", "a",
            "--role", "db",
            "--location", "eastus",
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "sql-set-dev-payments-db-eastus-a"
