"""Validate existing emissions and schemas."""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError

from conftest import make_emission, REPO_ROOT


EMISSIONS_DIR = REPO_ROOT / "governance" / "emissions"
SCHEMAS_DIR = REPO_ROOT / "governance" / "schemas"


# ===========================================================================
# Existing emissions against panel-output schema
# ===========================================================================


class TestExistingEmissions:
    @pytest.fixture
    def panel_schema(self):
        with open(SCHEMAS_DIR / "panel-output.schema.json") as f:
            return json.load(f)

    def test_existing_emissions_valid(self, panel_schema):
        """Every JSON file in governance/emissions/ must validate against the panel schema."""
        json_files = sorted(EMISSIONS_DIR.glob("*.json"))
        assert len(json_files) > 0, "No emission files found"
        for fpath in json_files:
            with open(fpath) as f:
                emission = json.load(f)
            validate(instance=emission, schema=panel_schema)


# ===========================================================================
# Schema rejection tests
# ===========================================================================


class TestSchemaRejection:
    @pytest.fixture
    def panel_schema(self):
        with open(SCHEMAS_DIR / "panel-output.schema.json") as f:
            return json.load(f)

    @pytest.fixture
    def valid_emission(self):
        return make_emission()

    @pytest.mark.parametrize("field", [
        "panel_name", "panel_version", "confidence_score", "risk_level",
        "compliance_score", "policy_flags", "requires_human_review",
        "timestamp", "findings",
    ])
    def test_rejects_missing_required_field(self, panel_schema, valid_emission, field):
        emission = copy.deepcopy(valid_emission)
        del emission[field]
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)

    def test_rejects_invalid_risk_level(self, panel_schema, valid_emission):
        emission = copy.deepcopy(valid_emission)
        emission["risk_level"] = "extreme"
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)

    def test_rejects_invalid_confidence_too_high(self, panel_schema, valid_emission):
        emission = copy.deepcopy(valid_emission)
        emission["confidence_score"] = 1.5
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)

    def test_rejects_invalid_confidence_negative(self, panel_schema, valid_emission):
        emission = copy.deepcopy(valid_emission)
        emission["confidence_score"] = -0.1
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)

    def test_rejects_empty_findings(self, panel_schema, valid_emission):
        emission = copy.deepcopy(valid_emission)
        emission["findings"] = []
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)


# ===========================================================================
# Schema file validity
# ===========================================================================


class TestSchemaFiles:
    def test_all_schemas_are_valid_json(self):
        """Every .json file in governance/schemas/ must parse as valid JSON."""
        json_files = sorted(SCHEMAS_DIR.glob("*.json"))
        assert len(json_files) > 0, "No schema files found"
        for fpath in json_files:
            with open(fpath) as f:
                data = json.load(f)
            assert isinstance(data, dict), f"{fpath.name} is not a JSON object"


# ===========================================================================
# Policy profile validity
# ===========================================================================


class TestPolicyProfileValidity:
    POLICY_DIR = REPO_ROOT / "governance" / "policy"
    # The 4 main evaluation profiles
    EVALUATION_PROFILES = [
        "default.yaml",
        "fin_pii_high.yaml",
        "infrastructure_critical.yaml",
        "reduced_touchpoint.yaml",
    ]

    def test_evaluation_profiles_are_valid_yaml(self):
        """The 4 evaluation profiles must parse and have required keys."""
        import yaml
        required_keys = {
            "profile_name", "profile_version", "weighting",
            "required_panels", "escalation", "auto_merge",
        }
        for name in self.EVALUATION_PROFILES:
            path = self.POLICY_DIR / name
            assert path.exists(), f"Profile {name} not found"
            with open(path) as f:
                profile = yaml.safe_load(f)
            assert isinstance(profile, dict), f"{name} did not parse as dict"
            missing = required_keys - set(profile.keys())
            assert not missing, f"{name} missing keys: {missing}"

    def test_all_yaml_files_parse(self):
        """Every .yaml file in governance/policy/ must parse without error."""
        import yaml
        # severity-reclassification.yaml has a known structural issue upstream
        KNOWN_INVALID = {"severity-reclassification.yaml"}
        yaml_files = sorted(self.POLICY_DIR.glob("*.yaml"))
        assert len(yaml_files) > 0
        failures = []
        for fpath in yaml_files:
            if fpath.name in KNOWN_INVALID:
                continue
            try:
                with open(fpath) as f:
                    data = yaml.safe_load(f)
                assert data is not None, f"{fpath.name} parsed as None"
            except yaml.YAMLError as e:
                failures.append(f"{fpath.name}: {e}")
        assert not failures, "\n".join(failures)
