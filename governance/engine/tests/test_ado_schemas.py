"""Tests for ADO integration schemas (ado-integration, ado-sync-ledger, ado-sync-error).

Validates that:
- All three schemas load as valid JSON
- Valid example data passes validation
- Invalid data (missing required fields, wrong types) is rejected
- The policy engine validate_ado_config() function works correctly
"""

import copy
import io
import json
import sys
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError

from conftest import REPO_ROOT

SCHEMAS_DIR = REPO_ROOT / "governance" / "schemas"

# Ensure governance package is importable
sys.path.insert(0, str(REPO_ROOT))

from governance.engine.policy_engine import EvaluationLog, validate_ado_config


# ===========================================================================
# Schema loading
# ===========================================================================


class TestAdoSchemaFiles:
    """Verify all three ADO schemas are valid JSON and well-formed."""

    @pytest.mark.parametrize("schema_name", [
        "ado-integration.schema.json",
        "ado-sync-ledger.schema.json",
        "ado-sync-error.schema.json",
    ])
    def test_schema_loads_as_valid_json(self, schema_name):
        path = SCHEMAS_DIR / schema_name
        assert path.exists(), f"Schema {schema_name} not found"
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert "$schema" in data
        assert data["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    @pytest.mark.parametrize("schema_name", [
        "ado-integration.schema.json",
        "ado-sync-ledger.schema.json",
        "ado-sync-error.schema.json",
    ])
    def test_schema_has_required_metadata(self, schema_name):
        with open(SCHEMAS_DIR / schema_name) as f:
            data = json.load(f)
        assert "title" in data
        assert "description" in data
        assert "$id" in data


# ===========================================================================
# ADO Integration Config schema
# ===========================================================================


class TestAdoIntegrationSchema:
    @pytest.fixture
    def schema(self):
        with open(SCHEMAS_DIR / "ado-integration.schema.json") as f:
            return json.load(f)

    @pytest.fixture
    def valid_config(self):
        return {
            "schema_version": "1.0.0",
            "enabled": True,
            "organization": "https://dev.azure.com/contoso",
            "project": "MyProject",
            "auth_method": "pat",
            "auth_secret_name": "ADO_PAT",
            "sync": {
                "direction": "github_to_ado",
                "auto_create": True,
                "auto_close": True,
                "grace_period_seconds": 5,
                "conflict_strategy": "last_write",
                "sync_comments": False,
                "sync_attachments": False,
            },
            "state_mapping": {
                "open": "New",
                "closed": "Closed",
            },
            "type_mapping": {
                "default": "User Story",
                "bug": "Bug",
            },
            "field_mapping": {
                "area_path": "MyProject\\Team",
                "iteration_path": "@CurrentIteration",
                "priority_labels": {
                    "critical": 1,
                    "high": 2,
                    "medium": 3,
                    "low": 4,
                },
            },
            "user_mapping": {
                "octocat": "octocat@contoso.com",
            },
            "filters": {
                "include_labels": [],
                "exclude_labels": ["internal", "governance"],
                "ado_area_path_filter": "",
            },
        }

    def test_valid_full_config(self, schema, valid_config):
        validate(instance=valid_config, schema=schema)

    def test_minimal_config(self, schema):
        config = {
            "schema_version": "1.0.0",
            "enabled": True,
            "organization": "https://dev.azure.com/contoso",
            "project": "MyProject",
        }
        validate(instance=config, schema=schema)

    @pytest.mark.parametrize("field", [
        "schema_version", "enabled", "organization", "project",
    ])
    def test_rejects_missing_required_field(self, schema, valid_config, field):
        config = copy.deepcopy(valid_config)
        del config[field]
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_rejects_invalid_organization_url(self, schema, valid_config):
        config = copy.deepcopy(valid_config)
        config["organization"] = "contoso"
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_rejects_invalid_auth_method(self, schema, valid_config):
        config = copy.deepcopy(valid_config)
        config["auth_method"] = "api_key"
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_rejects_invalid_sync_direction(self, schema, valid_config):
        config = copy.deepcopy(valid_config)
        config["sync"]["direction"] = "both"
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_rejects_invalid_conflict_strategy(self, schema, valid_config):
        config = copy.deepcopy(valid_config)
        config["sync"]["conflict_strategy"] = "merge"
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_rejects_negative_grace_period(self, schema, valid_config):
        config = copy.deepcopy(valid_config)
        config["sync"]["grace_period_seconds"] = -1
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_rejects_invalid_priority_value(self, schema, valid_config):
        config = copy.deepcopy(valid_config)
        config["field_mapping"]["priority_labels"]["urgent"] = 5
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_rejects_priority_zero(self, schema, valid_config):
        config = copy.deepcopy(valid_config)
        config["field_mapping"]["priority_labels"]["low"] = 0
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_rejects_additional_properties(self, schema, valid_config):
        config = copy.deepcopy(valid_config)
        config["extra_field"] = "not allowed"
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_rejects_additional_sync_properties(self, schema, valid_config):
        config = copy.deepcopy(valid_config)
        config["sync"]["unknown"] = True
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_rejects_wrong_schema_version(self, schema, valid_config):
        config = copy.deepcopy(valid_config)
        config["schema_version"] = "2.0.0"
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_all_auth_methods_accepted(self, schema, valid_config):
        for method in ["pat", "service_principal", "managed_identity"]:
            config = copy.deepcopy(valid_config)
            config["auth_method"] = method
            validate(instance=config, schema=schema)

    def test_all_sync_directions_accepted(self, schema, valid_config):
        for direction in ["bidirectional", "github_to_ado", "ado_to_github", "disabled"]:
            config = copy.deepcopy(valid_config)
            config["sync"]["direction"] = direction
            validate(instance=config, schema=schema)


# ===========================================================================
# ADO Sync Ledger schema
# ===========================================================================


class TestAdoSyncLedgerSchema:
    @pytest.fixture
    def schema(self):
        with open(SCHEMAS_DIR / "ado-sync-ledger.schema.json") as f:
            return json.load(f)

    @pytest.fixture
    def valid_ledger(self):
        return {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 42,
                    "github_repo": "SET-Apps/my-project",
                    "ado_work_item_id": 1001,
                    "ado_project": "MyProject",
                    "ado_work_item_type": "User Story",
                    "ado_work_item_url": "https://dev.azure.com/contoso/MyProject/_workitems/edit/1001",
                    "sync_direction": "github_to_ado",
                    "last_synced_at": "2026-02-27T12:00:00Z",
                    "last_sync_source": "github",
                    "last_sync_fields": ["title", "state"],
                    "created_at": "2026-02-27T10:00:00Z",
                    "sync_status": "active",
                }
            ],
        }

    def test_valid_full_ledger(self, schema, valid_ledger):
        validate(instance=valid_ledger, schema=schema)

    def test_minimal_ledger(self, schema):
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 1,
                    "github_repo": "org/repo",
                    "ado_work_item_id": 100,
                    "ado_project": "Proj",
                    "sync_direction": "github_to_ado",
                    "last_synced_at": "2026-02-27T12:00:00Z",
                    "sync_status": "active",
                }
            ],
        }
        validate(instance=ledger, schema=schema)

    def test_empty_mappings_valid(self, schema):
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [],
        }
        validate(instance=ledger, schema=schema)

    @pytest.mark.parametrize("field", [
        "github_issue_number", "github_repo", "ado_work_item_id",
        "ado_project", "sync_direction", "last_synced_at", "sync_status",
    ])
    def test_rejects_missing_required_mapping_field(self, schema, valid_ledger, field):
        ledger = copy.deepcopy(valid_ledger)
        del ledger["mappings"][0][field]
        with pytest.raises(ValidationError):
            validate(instance=ledger, schema=schema)

    def test_rejects_invalid_github_repo_format(self, schema, valid_ledger):
        ledger = copy.deepcopy(valid_ledger)
        ledger["mappings"][0]["github_repo"] = "not-a-valid-repo"
        with pytest.raises(ValidationError):
            validate(instance=ledger, schema=schema)

    def test_rejects_zero_issue_number(self, schema, valid_ledger):
        ledger = copy.deepcopy(valid_ledger)
        ledger["mappings"][0]["github_issue_number"] = 0
        with pytest.raises(ValidationError):
            validate(instance=ledger, schema=schema)

    def test_rejects_invalid_sync_direction(self, schema, valid_ledger):
        ledger = copy.deepcopy(valid_ledger)
        ledger["mappings"][0]["sync_direction"] = "bidirectional"
        with pytest.raises(ValidationError):
            validate(instance=ledger, schema=schema)

    def test_rejects_invalid_sync_status(self, schema, valid_ledger):
        ledger = copy.deepcopy(valid_ledger)
        ledger["mappings"][0]["sync_status"] = "unknown"
        with pytest.raises(ValidationError):
            validate(instance=ledger, schema=schema)

    def test_rejects_additional_mapping_properties(self, schema, valid_ledger):
        ledger = copy.deepcopy(valid_ledger)
        ledger["mappings"][0]["extra"] = "not allowed"
        with pytest.raises(ValidationError):
            validate(instance=ledger, schema=schema)

    def test_rejects_missing_schema_version(self, schema, valid_ledger):
        ledger = copy.deepcopy(valid_ledger)
        del ledger["schema_version"]
        with pytest.raises(ValidationError):
            validate(instance=ledger, schema=schema)


# ===========================================================================
# ADO Sync Error schema
# ===========================================================================


class TestAdoSyncErrorSchema:
    @pytest.fixture
    def schema(self):
        with open(SCHEMAS_DIR / "ado-sync-error.schema.json") as f:
            return json.load(f)

    @pytest.fixture
    def valid_error_log(self):
        return {
            "schema_version": "1.0.0",
            "errors": [
                {
                    "error_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "timestamp": "2026-02-27T12:00:00Z",
                    "operation": "create",
                    "source": "github",
                    "github_issue_number": 42,
                    "ado_work_item_id": None,
                    "error_type": "auth_failure",
                    "error_message": "PAT expired or revoked.",
                    "retry_count": 3,
                    "resolved": False,
                }
            ],
        }

    def test_valid_full_error_log(self, schema, valid_error_log):
        validate(instance=valid_error_log, schema=schema)

    def test_minimal_error_entry(self, schema):
        error_log = {
            "schema_version": "1.0.0",
            "errors": [
                {
                    "error_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "timestamp": "2026-02-27T12:00:00Z",
                    "operation": "update",
                    "source": "ado",
                    "error_type": "network_timeout",
                    "error_message": "Connection timed out after 30s.",
                }
            ],
        }
        validate(instance=error_log, schema=schema)

    def test_empty_errors_valid(self, schema):
        error_log = {
            "schema_version": "1.0.0",
            "errors": [],
        }
        validate(instance=error_log, schema=schema)

    @pytest.mark.parametrize("field", [
        "error_id", "timestamp", "operation", "source",
        "error_type", "error_message",
    ])
    def test_rejects_missing_required_error_field(self, schema, valid_error_log, field):
        log = copy.deepcopy(valid_error_log)
        del log["errors"][0][field]
        with pytest.raises(ValidationError):
            validate(instance=log, schema=schema)

    def test_rejects_invalid_operation(self, schema, valid_error_log):
        log = copy.deepcopy(valid_error_log)
        log["errors"][0]["operation"] = "sync"
        with pytest.raises(ValidationError):
            validate(instance=log, schema=schema)

    def test_rejects_invalid_source(self, schema, valid_error_log):
        log = copy.deepcopy(valid_error_log)
        log["errors"][0]["source"] = "jira"
        with pytest.raises(ValidationError):
            validate(instance=log, schema=schema)

    def test_null_github_issue_number_valid(self, schema, valid_error_log):
        """Null is allowed for github_issue_number (e.g., ADO-originated errors)."""
        log = copy.deepcopy(valid_error_log)
        log["errors"][0]["github_issue_number"] = None
        validate(instance=log, schema=schema)

    def test_null_ado_work_item_id_valid(self, schema, valid_error_log):
        """Null is allowed for ado_work_item_id (e.g., create failures)."""
        log = copy.deepcopy(valid_error_log)
        log["errors"][0]["ado_work_item_id"] = None
        validate(instance=log, schema=schema)

    def test_rejects_additional_error_properties(self, schema, valid_error_log):
        log = copy.deepcopy(valid_error_log)
        log["errors"][0]["stack_trace"] = "not allowed"
        with pytest.raises(ValidationError):
            validate(instance=log, schema=schema)

    def test_rejects_negative_retry_count(self, schema, valid_error_log):
        log = copy.deepcopy(valid_error_log)
        log["errors"][0]["retry_count"] = -1
        with pytest.raises(ValidationError):
            validate(instance=log, schema=schema)


# ===========================================================================
# Policy engine validate_ado_config()
# ===========================================================================


class TestPolicyEngineAdoValidation:
    @pytest.fixture
    def log(self):
        return EvaluationLog(stream=io.StringIO())

    @pytest.fixture
    def valid_ado_config(self):
        return {
            "schema_version": "1.0.0",
            "enabled": True,
            "organization": "https://dev.azure.com/contoso",
            "project": "MyProject",
        }

    def test_valid_config_passes(self, log, valid_ado_config):
        result = validate_ado_config(valid_ado_config, log)
        assert result["valid"] is True
        assert result["warnings"] == []

    def test_valid_config_in_project_wrapper(self, log, valid_ado_config):
        """Accepts full project.yaml dict with ado_integration key."""
        project = {"ado_integration": valid_ado_config}
        result = validate_ado_config(project, log)
        assert result["valid"] is True

    def test_invalid_config_returns_warnings(self, log):
        bad_config = {
            "schema_version": "1.0.0",
            "enabled": True,
            # missing organization and project
        }
        result = validate_ado_config(bad_config, log)
        assert result["valid"] is False
        assert len(result["warnings"]) > 0

    def test_empty_config_returns_skip(self, log):
        result = validate_ado_config({"ado_integration": {}}, log)
        assert "No ado_integration configuration found" in result["warnings"][0]

    def test_none_ado_section_returns_skip(self, log):
        result = validate_ado_config({"ado_integration": None}, log)
        assert len(result["warnings"]) > 0

    def test_wrong_schema_version_fails(self, log):
        config = {
            "schema_version": "99.0.0",
            "enabled": True,
            "organization": "https://dev.azure.com/contoso",
            "project": "MyProject",
        }
        result = validate_ado_config(config, log)
        assert result["valid"] is False
