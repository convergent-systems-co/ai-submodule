"""Multi-model validation integration with the policy engine.

Bridges the MultiModelAggregator with the policy engine's confidence
calculation pipeline. When multi-model validation is enabled, this module:

1. Detects multi-model emissions (multiple emissions per panel with model_id)
2. Aggregates them into consensus verdicts via MultiModelAggregator
3. Adjusts confidence scores based on consensus strength
4. Returns adjusted emissions for the policy engine to evaluate

Configuration in project.yaml:

    governance:
      multi_model_validation:
        enabled: true
        models: ["claude-opus-4-6", "claude-sonnet-4-6"]
        consensus_threshold: 0.75
        consensus_mode: "majority"

Or in policy profile YAML:

    multi_model:
      enabled: true
      models: ["opus", "sonnet"]
      consensus: majority
      min_models: 2
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.engine.multi_model_aggregator import (
    AggregatedVerdict,
    MultiModelAggregator,
    MultiModelConfig,
)


# Consensus strength multipliers for confidence adjustment
_CONSENSUS_MULTIPLIERS = {
    "unanimous": 1.0,       # Full agreement = no penalty
    "supermajority": 0.95,  # Strong agreement = slight reduction
    "majority": 0.90,       # Simple majority = moderate reduction
}

# When consensus is not reached, cap confidence at this value
_NO_CONSENSUS_CONFIDENCE_CAP = 0.70

# When insufficient models respond, cap confidence at this value
_INSUFFICIENT_MODELS_CONFIDENCE_CAP = 0.65


@dataclass
class MultiModelResult:
    """Result of multi-model integration processing."""

    panel_name: str
    adjusted_confidence: float
    original_confidence: float
    consensus_reached: bool
    consensus_strategy: str
    verdict: str
    model_count: int
    agreeing_count: int
    confidence_multiplier: float
    model_verdicts: list[dict]

    def to_dict(self) -> dict[str, Any]:
        return {
            "panel_name": self.panel_name,
            "adjusted_confidence": self.adjusted_confidence,
            "original_confidence": self.original_confidence,
            "consensus_reached": self.consensus_reached,
            "consensus_strategy": self.consensus_strategy,
            "verdict": self.verdict,
            "model_count": self.model_count,
            "agreeing_count": self.agreeing_count,
            "confidence_multiplier": self.confidence_multiplier,
            "model_verdicts": self.model_verdicts,
        }


def confidence_adjustment(
    base_confidence: float,
    verdict: AggregatedVerdict,
) -> float:
    """Calculate adjusted confidence based on multi-model consensus strength.

    When consensus is reached, the base confidence is multiplied by a
    strategy-specific factor. When consensus is not reached, confidence
    is capped at a lower threshold to trigger human review.

    Args:
        base_confidence: The average confidence across all models.
        verdict: The aggregated verdict from the MultiModelAggregator.

    Returns:
        Adjusted confidence score (0.0 to 1.0).
    """
    if verdict.verdict == "insufficient_models":
        return min(base_confidence, _INSUFFICIENT_MODELS_CONFIDENCE_CAP)

    if not verdict.consensus_reached:
        return min(base_confidence, _NO_CONSENSUS_CONFIDENCE_CAP)

    multiplier = _CONSENSUS_MULTIPLIERS.get(
        verdict.consensus_strategy, 0.90
    )
    adjusted = base_confidence * multiplier
    return round(min(adjusted, 1.0), 4)


def get_confidence_multiplier(verdict: AggregatedVerdict) -> float:
    """Get the confidence multiplier for a given verdict.

    Args:
        verdict: The aggregated verdict.

    Returns:
        Multiplier value (0.0 to 1.0).
    """
    if verdict.verdict == "insufficient_models":
        return _INSUFFICIENT_MODELS_CONFIDENCE_CAP
    if not verdict.consensus_reached:
        return _NO_CONSENSUS_CONFIDENCE_CAP / max(verdict.confidence_score, 0.01)
    return _CONSENSUS_MULTIPLIERS.get(verdict.consensus_strategy, 0.90)


def process_multi_model_emissions(
    raw_emissions: list[dict],
    config: MultiModelConfig,
) -> dict[str, MultiModelResult]:
    """Process raw emissions through multi-model aggregation.

    This is the main entry point for the policy engine. It takes raw
    emission dicts (as loaded from JSON files), runs them through the
    aggregator, and returns adjusted results per panel.

    Args:
        raw_emissions: List of emission dicts loaded from files.
        config: Multi-model configuration from policy profile.

    Returns:
        Dict mapping panel_name to MultiModelResult for panels that
        had multi-model emissions. Single-model panels are not included.
    """
    if not config.enabled:
        return {}

    aggregator = MultiModelAggregator(config)
    aggregated = aggregator.process_all_panels(raw_emissions)

    results: dict[str, MultiModelResult] = {}
    for panel_name, verdict in aggregated.items():
        multiplier = _CONSENSUS_MULTIPLIERS.get(
            verdict.consensus_strategy, 0.90
        )
        adjusted = confidence_adjustment(verdict.confidence_score, verdict)

        results[panel_name] = MultiModelResult(
            panel_name=panel_name,
            adjusted_confidence=adjusted,
            original_confidence=verdict.confidence_score,
            consensus_reached=verdict.consensus_reached,
            consensus_strategy=verdict.consensus_strategy,
            verdict=verdict.verdict,
            model_count=verdict.model_count,
            agreeing_count=verdict.agreeing_count,
            confidence_multiplier=multiplier,
            model_verdicts=verdict.model_verdicts,
        )

    return results


def merge_into_emissions(
    original_emissions: list[dict],
    multi_model_results: dict[str, MultiModelResult],
) -> list[dict]:
    """Merge multi-model results back into the emissions list.

    For panels that were aggregated, replaces the individual model
    emissions with a single synthesized emission containing the
    consensus verdict and adjusted confidence.

    Args:
        original_emissions: The original raw emissions list.
        multi_model_results: Results from process_multi_model_emissions.

    Returns:
        Modified emissions list with multi-model panels consolidated.
    """
    if not multi_model_results:
        return original_emissions

    # Collect panel names that were aggregated
    aggregated_panels = set(multi_model_results.keys())

    # Keep non-aggregated emissions as-is
    merged: list[dict] = []
    seen_panels: set[str] = set()

    for emission in original_emissions:
        panel_name = emission.get("panel_name", "")
        if panel_name in aggregated_panels:
            if panel_name not in seen_panels:
                # Replace with synthesized emission
                result = multi_model_results[panel_name]
                synthesized = dict(emission)  # Copy base fields
                synthesized["verdict"] = result.verdict
                synthesized["confidence_score"] = result.adjusted_confidence
                synthesized["multi_model"] = result.to_dict()
                synthesized.pop("model_id", None)
                synthesized.pop("model", None)
                merged.append(synthesized)
                seen_panels.add(panel_name)
            # Skip duplicate model emissions for aggregated panels
        else:
            merged.append(emission)

    return merged
