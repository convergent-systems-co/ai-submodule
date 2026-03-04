"""Tests for model_router — deterministic model selection per panel and persona."""

import pytest

from governance.engine.orchestrator.model_router import (
    CriticalityTier,
    KNOWN_MODELS,
    ModelConfig,
    ModelRouter,
    ModelValidationWarning,
    parse_panel_models_config,
    validate_model_names,
)


class TestModelConfig:
    """Tests for ModelConfig parsing."""

    def test_default_config(self):
        config = ModelConfig()
        assert config.default == "auto"
        assert config.tier_models["high"] == "opus"
        assert config.tier_models["standard"] == "sonnet"
        assert config.tier_models["low"] == "haiku"
        assert config.panel_overrides == {}
        assert config.persona_overrides == {}

    def test_from_dict_none(self):
        config = ModelConfig.from_dict(None)
        assert config.default == "auto"

    def test_from_dict_empty(self):
        config = ModelConfig.from_dict({})
        assert config.default == "auto"

    def test_from_dict_with_default(self):
        config = ModelConfig.from_dict({"default": "sonnet"})
        assert config.default == "sonnet"

    def test_from_dict_with_tiers(self):
        config = ModelConfig.from_dict({
            "tiers": {"high": "gpt-4", "standard": "gpt-3.5", "low": "gpt-3.5"}
        })
        assert config.tier_models["high"] == "gpt-4"
        assert config.tier_models["standard"] == "gpt-3.5"

    def test_from_dict_with_overrides(self):
        config = ModelConfig.from_dict({
            "panels": {"security-review": "opus"},
            "personas": {"test-evaluator": "opus"},
        })
        assert config.panel_overrides["security-review"] == "opus"
        assert config.persona_overrides["test-evaluator"] == "opus"

    def test_from_dict_full(self):
        config = ModelConfig.from_dict({
            "default": "auto",
            "tiers": {"high": "opus", "standard": "sonnet", "low": "haiku"},
            "panels": {"security-review": "opus", "documentation-review": "haiku"},
            "personas": {"test-evaluator": "opus", "coder": "sonnet"},
        })
        assert config.default == "auto"
        assert config.tier_models["high"] == "opus"
        assert config.panel_overrides["security-review"] == "opus"
        assert config.persona_overrides["test-evaluator"] == "opus"


class TestModelRouterAutoMode:
    """Tests for auto-routing by criticality tier."""

    def test_high_criticality_panel(self):
        router = ModelRouter()
        assert router.resolve_panel_model("security-review") == "opus"
        assert router.resolve_panel_model("threat-modeling") == "opus"

    def test_standard_criticality_panel(self):
        router = ModelRouter()
        assert router.resolve_panel_model("code-review") == "sonnet"
        assert router.resolve_panel_model("data-governance-review") == "sonnet"

    def test_low_criticality_panel(self):
        router = ModelRouter()
        assert router.resolve_panel_model("documentation-review") == "haiku"
        assert router.resolve_panel_model("cost-analysis") == "haiku"

    def test_unknown_panel_gets_standard(self):
        router = ModelRouter()
        assert router.resolve_panel_model("unknown-panel") == "sonnet"

    def test_high_criticality_persona(self):
        router = ModelRouter()
        assert router.resolve_persona_model("test-evaluator") == "opus"

    def test_standard_criticality_persona(self):
        router = ModelRouter()
        assert router.resolve_persona_model("coder") == "sonnet"
        assert router.resolve_persona_model("tech-lead") == "sonnet"
        assert router.resolve_persona_model("devops-engineer") == "sonnet"

    def test_unknown_persona_gets_standard(self):
        router = ModelRouter()
        assert router.resolve_persona_model("unknown-persona") == "sonnet"


class TestModelRouterExplicitDefault:
    """Tests for explicit default model (not auto)."""

    def test_explicit_default_overrides_auto_routing(self):
        config = ModelConfig(default="gpt-4o")
        router = ModelRouter(config)
        assert router.resolve_panel_model("security-review") == "gpt-4o"
        assert router.resolve_panel_model("documentation-review") == "gpt-4o"
        assert router.resolve_persona_model("test-evaluator") == "gpt-4o"

    def test_explicit_override_beats_default(self):
        config = ModelConfig(
            default="gpt-4o",
            panel_overrides={"security-review": "opus"},
        )
        router = ModelRouter(config)
        assert router.resolve_panel_model("security-review") == "opus"
        assert router.resolve_panel_model("code-review") == "gpt-4o"


class TestModelRouterOverrides:
    """Tests for per-panel and per-persona overrides."""

    def test_panel_override(self):
        config = ModelConfig(
            panel_overrides={"security-review": "gpt-4"},
        )
        router = ModelRouter(config)
        assert router.resolve_panel_model("security-review") == "gpt-4"
        # Non-overridden panel still auto-routes
        assert router.resolve_panel_model("code-review") == "sonnet"

    def test_persona_override(self):
        config = ModelConfig(
            persona_overrides={"coder": "opus"},
        )
        router = ModelRouter(config)
        assert router.resolve_persona_model("coder") == "opus"
        # Non-overridden persona still auto-routes
        assert router.resolve_persona_model("test-evaluator") == "opus"

    def test_custom_tier_models(self):
        config = ModelConfig(
            tier_models={"high": "claude-4", "standard": "claude-3.5", "low": "claude-3"},
        )
        router = ModelRouter(config)
        assert router.resolve_panel_model("security-review") == "claude-4"
        assert router.resolve_panel_model("code-review") == "claude-3.5"
        assert router.resolve_panel_model("documentation-review") == "claude-3"


class TestModelRouterTaskModel:
    """Tests for resolve_task_model with combined context."""

    def test_panel_takes_priority(self):
        router = ModelRouter()
        model = router.resolve_task_model(panel_name="security-review", persona_name="coder")
        assert model == "opus"

    def test_persona_when_no_panel(self):
        router = ModelRouter()
        model = router.resolve_task_model(persona_name="test-evaluator")
        assert model == "opus"

    def test_fallback_when_neither(self):
        router = ModelRouter()
        model = router.resolve_task_model()
        assert model == "sonnet"

    def test_fallback_with_explicit_default(self):
        config = ModelConfig(default="gpt-4o")
        router = ModelRouter(config)
        model = router.resolve_task_model()
        assert model == "gpt-4o"


class TestModelRouterSummary:
    """Tests for routing summary."""

    def test_summary_structure(self):
        router = ModelRouter()
        summary = router.get_routing_summary()
        assert "default" in summary
        assert "tier_models" in summary
        assert "panels" in summary
        assert "personas" in summary
        assert "security-review" in summary["panels"]
        assert "test-evaluator" in summary["personas"]

    def test_summary_shows_overrides(self):
        config = ModelConfig(panel_overrides={"security-review": "gpt-4"})
        router = ModelRouter(config)
        summary = router.get_routing_summary()
        assert summary["panels"]["security-review"]["override"] is True
        assert summary["panels"]["code-review"]["override"] is False


# ---------------------------------------------------------------------------
# Model name validation
# ---------------------------------------------------------------------------


class TestValidateModelNames:
    """Tests for validate_model_names."""

    def test_all_known_models_pass(self):
        config = ModelConfig(
            default="sonnet",
            panel_overrides={"security-review": "opus"},
            persona_overrides={"test-evaluator": "haiku"},
        )
        warnings = validate_model_names(config)
        assert len(warnings) == 0

    def test_unknown_default_model(self):
        config = ModelConfig(default="my-custom-model")
        warnings = validate_model_names(config)
        assert len(warnings) == 1
        assert warnings[0].context == "governance.models.default"
        assert "my-custom-model" in warnings[0].message

    def test_unknown_panel_model(self):
        config = ModelConfig(panel_overrides={"security-review": "unknown-model-x"})
        warnings = validate_model_names(config)
        assert len(warnings) == 1
        assert "security-review" in warnings[0].context

    def test_unknown_persona_model(self):
        config = ModelConfig(persona_overrides={"test-evaluator": "unknown-model-y"})
        warnings = validate_model_names(config)
        assert len(warnings) == 1
        assert "test-evaluator" in warnings[0].context

    def test_unknown_tier_model(self):
        config = ModelConfig(tier_models={"high": "custom-tier-model", "standard": "sonnet", "low": "haiku"})
        warnings = validate_model_names(config)
        assert len(warnings) == 1
        assert "high" in warnings[0].context

    def test_auto_default_no_warning(self):
        config = ModelConfig(default="auto")
        warnings = validate_model_names(config)
        assert len(warnings) == 0

    def test_claude_model_ids_recognized(self):
        config = ModelConfig(
            panel_overrides={
                "security-review": "claude-opus-4-6",
                "code-review": "claude-sonnet-4-6",
                "documentation-review": "claude-haiku-4-5",
            }
        )
        warnings = validate_model_names(config)
        assert len(warnings) == 0

    def test_known_models_set_contains_expected(self):
        assert "opus" in KNOWN_MODELS
        assert "sonnet" in KNOWN_MODELS
        assert "haiku" in KNOWN_MODELS
        assert "gpt-4o" in KNOWN_MODELS
        assert "claude-opus-4-6" in KNOWN_MODELS


# ---------------------------------------------------------------------------
# parse_panel_models_config
# ---------------------------------------------------------------------------


class TestParsePanelModelsConfig:
    """Tests for the alternative panel_models syntax."""

    def test_none_input(self):
        default, overrides = parse_panel_models_config(None)
        assert default is None
        assert overrides == {}

    def test_empty_input(self):
        default, overrides = parse_panel_models_config({})
        assert default is None
        assert overrides == {}

    def test_defaults_only(self):
        data = {"defaults": {"model": "claude-sonnet-4-6"}}
        default, overrides = parse_panel_models_config(data)
        assert default == "claude-sonnet-4-6"
        assert overrides == {}

    def test_overrides_dict_syntax(self):
        data = {
            "overrides": {
                "security-review": {"model": "claude-opus-4-6"},
                "documentation-review": {"model": "claude-haiku-4-5"},
            }
        }
        default, overrides = parse_panel_models_config(data)
        assert default is None
        assert overrides["security-review"] == "claude-opus-4-6"
        assert overrides["documentation-review"] == "claude-haiku-4-5"

    def test_overrides_shorthand_syntax(self):
        data = {
            "overrides": {
                "security-review": "opus",
                "documentation-review": "haiku",
            }
        }
        default, overrides = parse_panel_models_config(data)
        assert overrides["security-review"] == "opus"
        assert overrides["documentation-review"] == "haiku"

    def test_full_config(self):
        data = {
            "defaults": {"model": "sonnet"},
            "overrides": {
                "security-review": {"model": "opus"},
                "cost-analysis": "haiku",
            }
        }
        default, overrides = parse_panel_models_config(data)
        assert default == "sonnet"
        assert overrides["security-review"] == "opus"
        assert overrides["cost-analysis"] == "haiku"

    def test_missing_model_key_in_override(self):
        data = {
            "overrides": {
                "security-review": {"other_key": "value"},
            }
        }
        default, overrides = parse_panel_models_config(data)
        assert overrides == {}  # No model key, so not parsed
