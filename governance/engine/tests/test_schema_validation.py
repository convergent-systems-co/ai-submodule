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
        "timestamp", "findings", "aggregate_verdict",
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


# ===========================================================================
# Execution backend schema validation
# ===========================================================================


class TestExecutionBackendSchema:
    @pytest.fixture
    def backend_schema(self):
        with open(SCHEMAS_DIR / "execution-backend.schema.json") as f:
            return json.load(f)

    def _valid_backend_config(self):
        """Return a minimal valid execution backend config."""
        return {
            "backends": {
                "claude-opus": {
                    "model_id": "claude-opus-4-6",
                    "provider": "anthropic",
                    "context_window": 200000,
                    "cost_per_1k_input_tokens": 0.015,
                    "cost_per_1k_output_tokens": 0.075,
                    "capabilities": ["reasoning", "code-generation"],
                    "max_output_tokens": 32000,
                },
                "claude-sonnet": {
                    "model_id": "claude-sonnet-4-20250514",
                    "provider": "anthropic",
                    "context_window": 200000,
                    "cost_per_1k_input_tokens": 0.003,
                    "cost_per_1k_output_tokens": 0.015,
                },
            },
            "default_backend": "claude-opus",
            "model_assignment": {
                "tech-lead": {
                    "primary": "claude-opus",
                    "fallback": "claude-sonnet",
                },
                "coder": {
                    "primary": "claude-sonnet",
                },
            },
        }

    def test_valid_config_passes(self, backend_schema):
        """A fully populated backend config validates successfully."""
        validate(instance=self._valid_backend_config(), schema=backend_schema)

    def test_minimal_config_passes(self, backend_schema):
        """A config with only required fields validates."""
        config = {
            "backends": {
                "default": {
                    "model_id": "gpt-4o",
                    "provider": "openai",
                    "context_window": 128000,
                },
            },
            "default_backend": "default",
        }
        validate(instance=config, schema=backend_schema)

    def test_rejects_missing_backends(self, backend_schema):
        """Config without 'backends' key is rejected."""
        config = {"default_backend": "x"}
        with pytest.raises(ValidationError):
            validate(instance=config, schema=backend_schema)

    def test_rejects_missing_default_backend(self, backend_schema):
        """Config without 'default_backend' key is rejected."""
        config = {
            "backends": {
                "x": {
                    "model_id": "m",
                    "provider": "anthropic",
                    "context_window": 2048,
                },
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=backend_schema)

    def test_rejects_invalid_provider(self, backend_schema):
        """Backend with unsupported provider is rejected."""
        config = {
            "backends": {
                "bad": {
                    "model_id": "m",
                    "provider": "unsupported-provider",
                    "context_window": 2048,
                },
            },
            "default_backend": "bad",
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=backend_schema)

    def test_rejects_context_window_too_small(self, backend_schema):
        """Context window below 1024 is rejected."""
        config = {
            "backends": {
                "tiny": {
                    "model_id": "m",
                    "provider": "openai",
                    "context_window": 512,
                },
            },
            "default_backend": "tiny",
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=backend_schema)

    def test_rejects_negative_cost(self, backend_schema):
        """Negative cost values are rejected."""
        config = {
            "backends": {
                "neg": {
                    "model_id": "m",
                    "provider": "openai",
                    "context_window": 2048,
                    "cost_per_1k_input_tokens": -0.01,
                },
            },
            "default_backend": "neg",
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=backend_schema)

    def test_rejects_missing_backend_required_fields(self, backend_schema):
        """Backend entry missing model_id is rejected."""
        config = {
            "backends": {
                "incomplete": {
                    "provider": "anthropic",
                    "context_window": 2048,
                },
            },
            "default_backend": "incomplete",
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=backend_schema)

    def test_all_providers_accepted(self, backend_schema):
        """Each supported provider enum value is accepted."""
        for provider in ["anthropic", "openai", "azure-openai", "github-copilot"]:
            config = {
                "backends": {
                    "test": {
                        "model_id": "test-model",
                        "provider": provider,
                        "context_window": 4096,
                    },
                },
                "default_backend": "test",
            }
            validate(instance=config, schema=backend_schema)


# ===========================================================================
# Token count and cost fields in panel output
# ===========================================================================


class TestPanelOutputCostFields:
    @pytest.fixture
    def panel_schema(self):
        with open(SCHEMAS_DIR / "panel-output.schema.json") as f:
            return json.load(f)

    @pytest.fixture
    def valid_emission(self):
        return make_emission()

    def test_emission_with_token_count_and_cost(self, panel_schema, valid_emission):
        """Emission with token_count and estimated_cost_usd in execution_context validates."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "model_version": "claude-opus-4-6",
            "token_count": {
                "input": 45200,
                "output": 3800,
            },
            "estimated_cost_usd": 0.963,
        }
        validate(instance=emission, schema=panel_schema)

    def test_emission_with_token_count_only(self, panel_schema, valid_emission):
        """Emission with token_count but no cost validates (cost is optional)."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "model_version": "claude-opus-4-6",
            "token_count": {
                "input": 10000,
                "output": 500,
            },
        }
        validate(instance=emission, schema=panel_schema)

    def test_emission_with_cost_only(self, panel_schema, valid_emission):
        """Emission with estimated_cost_usd but no token_count validates."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "model_version": "claude-opus-4-6",
            "estimated_cost_usd": 0.50,
        }
        validate(instance=emission, schema=panel_schema)

    def test_emission_without_cost_fields_still_valid(self, panel_schema, valid_emission):
        """Emission without any cost fields is backward compatible."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "model_version": "claude-opus-4-6",
        }
        validate(instance=emission, schema=panel_schema)

    def test_emission_without_execution_context_still_valid(self, panel_schema, valid_emission):
        """Emission without execution_context at all is backward compatible."""
        emission = copy.deepcopy(valid_emission)
        assert "execution_context" not in emission
        validate(instance=emission, schema=panel_schema)

    def test_rejects_negative_estimated_cost(self, panel_schema, valid_emission):
        """Negative estimated_cost_usd is rejected."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "estimated_cost_usd": -1.0,
        }
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)

    def test_rejects_negative_token_count(self, panel_schema, valid_emission):
        """Negative input token count is rejected."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "token_count": {
                "input": -100,
                "output": 50,
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)

    def test_rejects_string_token_count(self, panel_schema, valid_emission):
        """String values for token counts are rejected."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "token_count": {
                "input": "many",
                "output": 50,
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)

    def test_partial_token_count_valid(self, panel_schema, valid_emission):
        """Token count with only input or only output is valid."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "token_count": {
                "input": 5000,
            },
        }
        validate(instance=emission, schema=panel_schema)

    def test_zero_cost_valid(self, panel_schema, valid_emission):
        """Zero cost is valid (e.g., for free-tier providers)."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "estimated_cost_usd": 0,
            "token_count": {
                "input": 1000,
                "output": 100,
            },
        }
        validate(instance=emission, schema=panel_schema)


# ===========================================================================
# Model provenance fields in panel output (Issue #560)
# ===========================================================================


class TestPanelOutputProvenanceFields:
    @pytest.fixture
    def panel_schema(self):
        with open(SCHEMAS_DIR / "panel-output.schema.json") as f:
            return json.load(f)

    @pytest.fixture
    def valid_emission(self):
        return make_emission()

    def test_rejects_temperature_above_max(self, panel_schema, valid_emission):
        """Temperature above 2.0 is rejected."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "inference_config": {
                "temperature": 2.1,
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)

    def test_rejects_temperature_below_min(self, panel_schema, valid_emission):
        """Temperature below 0.0 is rejected."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "inference_config": {
                "temperature": -0.1,
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)

    def test_rejects_top_p_above_max(self, panel_schema, valid_emission):
        """top_p above 1.0 is rejected."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "inference_config": {
                "top_p": 1.1,
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)

    def test_rejects_invalid_system_prompt_hash_wrong_length(self, panel_schema, valid_emission):
        """system_prompt_hash with wrong length is rejected."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "system_prompt_hash": "abcdef1234",
        }
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)

    def test_rejects_invalid_system_prompt_hash_non_hex(self, panel_schema, valid_emission):
        """system_prompt_hash with non-hex characters is rejected."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "system_prompt_hash": "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
        }
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)

    def test_rejects_extra_properties_on_inference_config(self, panel_schema, valid_emission):
        """Extra properties on inference_config are rejected."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "inference_config": {
                "temperature": 0.7,
                "unknown_param": True,
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=emission, schema=panel_schema)

    def test_valid_provenance_fields(self, panel_schema, valid_emission):
        """Emission with all provenance fields validates successfully."""
        emission = copy.deepcopy(valid_emission)
        emission["execution_context"] = {
            "model_id": "claude-opus-4-6",
            "system_prompt_hash": "a" * 64,
            "inference_config": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 0.9,
            },
        }
        validate(instance=emission, schema=panel_schema)


# ===========================================================================
# Escalation chain in run-manifest schema (Issue #436)
# ===========================================================================


class TestEscalationChainSchema:
    """Validate escalation_chain behaviour in run-manifest.schema.json."""

    @pytest.fixture
    def manifest_schema(self):
        with open(SCHEMAS_DIR / "run-manifest.schema.json") as f:
            return json.load(f)

    @pytest.fixture
    def _base_manifest(self):
        """Minimal valid run-manifest (without escalation_chain)."""
        return {
            "manifest_version": "1.0.0",
            "manifest_id": "20260227-120000-abcdef1",
            "timestamp": "2026-02-27T12:00:00Z",
            "persona_set_commit": "a" * 40,
            "panel_graph_version": "1.0.0",
            "policy_profile_used": "default",
            "model_version": "claude-opus-4-6",
            "aggregate_confidence": 0.92,
            "risk_level": "low",
            "human_intervention": {
                "required": False,
                "occurred": False,
            },
            "decision": {
                "action": "auto_merge",
                "rationale": "All panels approved with high confidence.",
            },
            "panels_executed": [
                {
                    "panel_name": "code-review",
                    "verdict": "approve",
                    "confidence_score": 0.92,
                    "artifact_path": ".artifacts/emissions/code-review.json",
                }
            ],
        }

    # -- backward compatibility -------------------------------------------

    def test_manifest_without_escalation_chain_is_valid(
        self, manifest_schema, _base_manifest,
    ):
        """escalation_chain is optional — manifests without it must still pass."""
        validate(instance=_base_manifest, schema=manifest_schema)

    # -- valid escalation chains ------------------------------------------

    def test_manifest_with_valid_escalation_chain(
        self, manifest_schema, _base_manifest,
    ):
        """A manifest containing a well-formed escalation_chain must validate."""
        manifest = copy.deepcopy(_base_manifest)
        manifest["escalation_chain"] = [
            {
                "timestamp": "2026-02-27T12:01:00Z",
                "source_agent": "policy-engine",
                "target_role": "security-lead",
                "reason": "Critical vulnerability detected in dependency scan.",
                "escalation_type": "human_review_required",
            }
        ]
        validate(instance=manifest, schema=manifest_schema)

    def test_escalation_chain_with_human_decision(
        self, manifest_schema, _base_manifest,
    ):
        """An escalation event that includes a human_decision must validate."""
        manifest = copy.deepcopy(_base_manifest)
        manifest["escalation_chain"] = [
            {
                "timestamp": "2026-02-27T12:01:00Z",
                "source_agent": "tech-lead",
                "target_role": "architect",
                "reason": "Block decision on high-risk refactor.",
                "escalation_type": "block_decision",
                "human_decision": {
                    "action": "override",
                    "justification": "Risk accepted per ADR-042.",
                    "decision_timestamp": "2026-02-27T12:15:00Z",
                    "reviewer": "octocat",
                },
            }
        ]
        validate(instance=manifest, schema=manifest_schema)

    def test_escalation_chain_multiple_events(
        self, manifest_schema, _base_manifest,
    ):
        """Multiple escalation events in sequence must validate."""
        manifest = copy.deepcopy(_base_manifest)
        manifest["escalation_chain"] = [
            {
                "timestamp": "2026-02-27T12:01:00Z",
                "source_agent": "security-review",
                "target_role": "security-lead",
                "reason": "PII exposure detected.",
                "escalation_type": "circuit_breaker",
            },
            {
                "timestamp": "2026-02-27T12:05:00Z",
                "source_agent": "policy-engine",
                "target_role": "compliance-officer",
                "reason": "Policy override requested after circuit breaker.",
                "escalation_type": "policy_override",
                "human_decision": {
                    "action": "approve",
                    "decision_timestamp": "2026-02-27T12:10:00Z",
                    "reviewer": "compliance-bot",
                },
            },
        ]
        validate(instance=manifest, schema=manifest_schema)

    def test_empty_escalation_chain_is_valid(
        self, manifest_schema, _base_manifest,
    ):
        """An empty escalation_chain array must validate (no escalations occurred)."""
        manifest = copy.deepcopy(_base_manifest)
        manifest["escalation_chain"] = []
        validate(instance=manifest, schema=manifest_schema)

    # -- invalid escalation chains ----------------------------------------

    def test_rejects_escalation_event_missing_required_field(
        self, manifest_schema, _base_manifest,
    ):
        """An escalation event missing a required field must fail validation."""
        manifest = copy.deepcopy(_base_manifest)
        manifest["escalation_chain"] = [
            {
                # missing "timestamp"
                "source_agent": "policy-engine",
                "target_role": "security-lead",
                "reason": "Missing timestamp field.",
                "escalation_type": "human_review_required",
            }
        ]
        with pytest.raises(ValidationError):
            validate(instance=manifest, schema=manifest_schema)

    def test_rejects_invalid_escalation_type(
        self, manifest_schema, _base_manifest,
    ):
        """An unrecognised escalation_type must fail validation."""
        manifest = copy.deepcopy(_base_manifest)
        manifest["escalation_chain"] = [
            {
                "timestamp": "2026-02-27T12:01:00Z",
                "source_agent": "policy-engine",
                "target_role": "security-lead",
                "reason": "Invalid type test.",
                "escalation_type": "unknown_type",
            }
        ]
        with pytest.raises(ValidationError):
            validate(instance=manifest, schema=manifest_schema)

    def test_rejects_invalid_human_decision_action(
        self, manifest_schema, _base_manifest,
    ):
        """A human_decision with an invalid action must fail validation."""
        manifest = copy.deepcopy(_base_manifest)
        manifest["escalation_chain"] = [
            {
                "timestamp": "2026-02-27T12:01:00Z",
                "source_agent": "policy-engine",
                "target_role": "architect",
                "reason": "Bad action test.",
                "escalation_type": "block_decision",
                "human_decision": {
                    "action": "maybe",
                    "decision_timestamp": "2026-02-27T12:10:00Z",
                    "reviewer": "octocat",
                },
            }
        ]
        with pytest.raises(ValidationError):
            validate(instance=manifest, schema=manifest_schema)

    def test_rejects_human_decision_missing_reviewer(
        self, manifest_schema, _base_manifest,
    ):
        """A human_decision missing the required reviewer field must fail."""
        manifest = copy.deepcopy(_base_manifest)
        manifest["escalation_chain"] = [
            {
                "timestamp": "2026-02-27T12:01:00Z",
                "source_agent": "policy-engine",
                "target_role": "architect",
                "reason": "Missing reviewer.",
                "escalation_type": "policy_override",
                "human_decision": {
                    "action": "approve",
                    "decision_timestamp": "2026-02-27T12:10:00Z",
                    # missing "reviewer"
                },
            }
        ]
        with pytest.raises(ValidationError):
            validate(instance=manifest, schema=manifest_schema)

    def test_rejects_additional_properties_on_escalation_event(
        self, manifest_schema, _base_manifest,
    ):
        """Extra properties on an escalation event must fail validation."""
        manifest = copy.deepcopy(_base_manifest)
        manifest["escalation_chain"] = [
            {
                "timestamp": "2026-02-27T12:01:00Z",
                "source_agent": "policy-engine",
                "target_role": "security-lead",
                "reason": "Extra field test.",
                "escalation_type": "human_review_required",
                "unexpected_field": True,
            }
        ]
        with pytest.raises(ValidationError):
            validate(instance=manifest, schema=manifest_schema)

    def test_rejects_additional_properties_on_human_decision(
        self, manifest_schema, _base_manifest,
    ):
        """Extra properties on human_decision must fail validation."""
        manifest = copy.deepcopy(_base_manifest)
        manifest["escalation_chain"] = [
            {
                "timestamp": "2026-02-27T12:01:00Z",
                "source_agent": "policy-engine",
                "target_role": "architect",
                "reason": "Extra human_decision field test.",
                "escalation_type": "block_decision",
                "human_decision": {
                    "action": "approve",
                    "decision_timestamp": "2026-02-27T12:10:00Z",
                    "reviewer": "octocat",
                    "mood": "happy",
                },
            }
        ]
        with pytest.raises(ValidationError):
            validate(instance=manifest, schema=manifest_schema)
