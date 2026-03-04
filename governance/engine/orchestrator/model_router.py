"""Model router — deterministic model selection per panel and persona.

Routes panels and personas to appropriate models based on task criticality
tiers or explicit per-panel/persona overrides in project.yaml.

Configuration in project.yaml (primary syntax):

    governance:
      models:
        default: "auto"          # or a specific model ID
        tiers:
          high: "opus"           # High-stakes tasks
          standard: "sonnet"     # Balanced cost/quality
          low: "haiku"           # Cost-effective
        panels:
          security-review: "opus"
          documentation-review: "haiku"
        personas:
          tester: "opus"
          coder: "sonnet"

Alternative syntax (per-panel defaults/overrides):

    governance:
      panel_models:
        defaults:
          model: "claude-sonnet-4-6"
        overrides:
          security-review:
            model: "claude-opus-4-6"
          documentation-review:
            model: "claude-haiku-4-5"

When models.default is "auto" or the models section is omitted, the
router uses criticality tiers to select models deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from governance.engine.multi_model_aggregator import MultiModelConfig


class CriticalityTier(str, Enum):
    """Task criticality tiers for model routing."""
    HIGH = "high"
    STANDARD = "standard"
    LOW = "low"


# Default criticality mappings
_PANEL_CRITICALITY: dict[str, CriticalityTier] = {
    "security-review": CriticalityTier.HIGH,
    "threat-modeling": CriticalityTier.HIGH,
    "code-review": CriticalityTier.STANDARD,
    "data-governance-review": CriticalityTier.STANDARD,
    "documentation-review": CriticalityTier.LOW,
    "cost-analysis": CriticalityTier.LOW,
}

_PERSONA_CRITICALITY: dict[str, CriticalityTier] = {
    "test-evaluator": CriticalityTier.HIGH,
    "coder": CriticalityTier.STANDARD,
    "tech-lead": CriticalityTier.STANDARD,
    "devops-engineer": CriticalityTier.STANDARD,
    "iac-engineer": CriticalityTier.STANDARD,
    "project-manager": CriticalityTier.STANDARD,
    "test-writer": CriticalityTier.STANDARD,
    "document-writer": CriticalityTier.STANDARD,
    "documentation-reviewer": CriticalityTier.STANDARD,
}

# Default tier-to-model mapping
_DEFAULT_TIER_MODELS: dict[CriticalityTier, str] = {
    CriticalityTier.HIGH: "opus",
    CriticalityTier.STANDARD: "sonnet",
    CriticalityTier.LOW: "haiku",
}


@dataclass(frozen=True)
class ModelConfig:
    """Parsed model configuration from project.yaml."""

    default: str = "auto"
    tier_models: dict[str, str] = field(default_factory=lambda: {
        "high": "opus",
        "standard": "sonnet",
        "low": "haiku",
    })
    panel_overrides: dict[str, str] = field(default_factory=dict)
    persona_overrides: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict | None) -> ModelConfig:
        """Parse from the governance.models section of project.yaml."""
        if not data:
            return cls()

        return cls(
            default=data.get("default", "auto"),
            tier_models={
                "high": data.get("tiers", {}).get("high", "opus"),
                "standard": data.get("tiers", {}).get("standard", "sonnet"),
                "low": data.get("tiers", {}).get("low", "haiku"),
            },
            panel_overrides=data.get("panels", {}),
            persona_overrides=data.get("personas", {}),
        )


# ---------------------------------------------------------------------------
# Known model names (for validation)
# ---------------------------------------------------------------------------

KNOWN_MODELS: frozenset[str] = frozenset({
    # Short names (used in tier config)
    "auto", "opus", "sonnet", "haiku",
    # Claude model IDs
    "claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5",
    "claude-opus-4-5", "claude-sonnet-4-5", "claude-haiku-3-5",
    "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
    "claude-3-5-sonnet", "claude-3-5-haiku",
    # OpenAI model IDs (for cross-provider setups)
    "gpt-4", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o-mini",
    "o1", "o1-mini", "o1-pro", "o3", "o3-mini",
})


@dataclass
class ModelValidationWarning:
    """A warning about an unrecognized model name."""

    model_name: str
    context: str  # e.g., "governance.models.panels.security-review"
    message: str


def validate_model_names(config: ModelConfig) -> list[ModelValidationWarning]:
    """Validate all model names in a ModelConfig against known models.

    Returns warnings for unrecognized names. These are advisory — custom
    model names are allowed but flagged.
    """
    warnings: list[ModelValidationWarning] = []

    # Check default
    if config.default != "auto" and config.default not in KNOWN_MODELS:
        warnings.append(ModelValidationWarning(
            model_name=config.default,
            context="governance.models.default",
            message=f"Unrecognized model: '{config.default}'",
        ))

    # Check tier models
    for tier, model in config.tier_models.items():
        if model not in KNOWN_MODELS:
            warnings.append(ModelValidationWarning(
                model_name=model,
                context=f"governance.models.tiers.{tier}",
                message=f"Unrecognized model: '{model}'",
            ))

    # Check panel overrides
    for panel, model in config.panel_overrides.items():
        if model not in KNOWN_MODELS:
            warnings.append(ModelValidationWarning(
                model_name=model,
                context=f"governance.models.panels.{panel}",
                message=f"Unrecognized model: '{model}'",
            ))

    # Check persona overrides
    for persona, model in config.persona_overrides.items():
        if model not in KNOWN_MODELS:
            warnings.append(ModelValidationWarning(
                model_name=model,
                context=f"governance.models.personas.{persona}",
                message=f"Unrecognized model: '{model}'",
            ))

    return warnings


def parse_panel_models_config(panel_models_data: dict | None) -> tuple[str | None, dict[str, str]]:
    """Parse the alternative governance.panel_models syntax.

    Args:
        panel_models_data: The governance.panel_models dict from project.yaml.

    Returns:
        Tuple of (default_model_or_None, panel_overrides_dict).

    Example input:
        {
            "defaults": {"model": "claude-sonnet-4-6"},
            "overrides": {
                "security-review": {"model": "claude-opus-4-6"},
                "documentation-review": {"model": "claude-haiku-4-5"},
            }
        }
    """
    if not panel_models_data:
        return None, {}

    default_model = None
    defaults = panel_models_data.get("defaults", {})
    if isinstance(defaults, dict):
        default_model = defaults.get("model")

    overrides: dict[str, str] = {}
    raw_overrides = panel_models_data.get("overrides", {})
    if isinstance(raw_overrides, dict):
        for panel_name, panel_config in raw_overrides.items():
            if isinstance(panel_config, dict) and "model" in panel_config:
                overrides[panel_name] = panel_config["model"]
            elif isinstance(panel_config, str):
                # Allow shorthand: "security-review": "opus"
                overrides[panel_name] = panel_config

    return default_model, overrides


class ModelRouter:
    """Deterministic model router for panels and personas.

    The engine makes the routing decision. The LLM receives an instruction
    to use a specific model — it does not choose its own.
    """

    def __init__(self, config: ModelConfig | None = None):
        self._config = config or ModelConfig()

    @property
    def config(self) -> ModelConfig:
        return self._config

    def resolve_panel_model(self, panel_name: str) -> str:
        """Resolve the model to use for a given panel.

        Priority:
        1. Explicit panel override in config
        2. Explicit default model (if not "auto")
        3. Auto-route by criticality tier
        """
        # Check explicit panel override
        if panel_name in self._config.panel_overrides:
            return self._config.panel_overrides[panel_name]

        # Check explicit default
        if self._config.default != "auto":
            return self._config.default

        # Auto-route by criticality
        tier = _PANEL_CRITICALITY.get(panel_name, CriticalityTier.STANDARD)
        return self._resolve_tier_model(tier)

    def resolve_persona_model(self, persona_name: str) -> str:
        """Resolve the model to use for a given persona.

        Priority:
        1. Explicit persona override in config
        2. Explicit default model (if not "auto")
        3. Auto-route by criticality tier
        """
        # Check explicit persona override
        if persona_name in self._config.persona_overrides:
            return self._config.persona_overrides[persona_name]

        # Check explicit default
        if self._config.default != "auto":
            return self._config.default

        # Auto-route by criticality
        tier = _PERSONA_CRITICALITY.get(persona_name, CriticalityTier.STANDARD)
        return self._resolve_tier_model(tier)

    def resolve_task_model(self, panel_name: str | None = None, persona_name: str | None = None) -> str:
        """Resolve model for a task that may have both panel and persona context.

        If both are provided, panel takes priority (the panel drives the work).
        """
        if panel_name:
            return self.resolve_panel_model(panel_name)
        if persona_name:
            return self.resolve_persona_model(persona_name)
        # Fallback
        if self._config.default != "auto":
            return self._config.default
        return self._resolve_tier_model(CriticalityTier.STANDARD)

    def get_routing_summary(self) -> dict:
        """Return a summary of model routing for all known panels and personas."""
        panels = {}
        for panel in _PANEL_CRITICALITY:
            panels[panel] = {
                "model": self.resolve_panel_model(panel),
                "criticality": _PANEL_CRITICALITY[panel].value,
                "override": panel in self._config.panel_overrides,
            }

        personas = {}
        for persona in _PERSONA_CRITICALITY:
            personas[persona] = {
                "model": self.resolve_persona_model(persona),
                "criticality": _PERSONA_CRITICALITY[persona].value,
                "override": persona in self._config.persona_overrides,
            }

        return {
            "default": self._config.default,
            "tier_models": dict(self._config.tier_models),
            "panels": panels,
            "personas": personas,
        }

    def resolve_multi_model_panel(
        self,
        panel_name: str,
        multi_model_config: MultiModelConfig,
    ) -> list[str]:
        """Resolve the list of models for a multi-model panel evaluation.

        When multi-model validation is enabled and applies to this panel,
        returns the configured model list. Otherwise returns a single-element
        list with the standard panel model.

        Args:
            panel_name: The panel to resolve models for.
            multi_model_config: The multi-model configuration.

        Returns:
            List of model IDs to run the panel against.
        """
        if multi_model_config.enabled and multi_model_config.applies_to_panel(panel_name):
            if multi_model_config.models:
                return list(multi_model_config.models)
        # Fallback to single model
        return [self.resolve_panel_model(panel_name)]

    def _resolve_tier_model(self, tier: CriticalityTier) -> str:
        """Resolve a tier to a model using config or defaults."""
        return self._config.tier_models.get(
            tier.value,
            _DEFAULT_TIER_MODELS.get(tier, "sonnet"),
        )
