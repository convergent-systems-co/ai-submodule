"""Multi-model validation aggregator for review panels.

Aggregates panel emissions from multiple models into a consensus verdict.
Supports configurable consensus strategies (majority, supermajority, unanimous).

When multi-model validation is enabled, each panel is run across N models.
Each model produces a separate emission file named:
    {panel_name}.{model_id}.json   (e.g., security-review.opus.json)

The aggregator groups these by panel_name, applies the consensus strategy,
and produces a single aggregated verdict per panel for the policy engine.

Configuration in policy profile YAML:

    multi_model:
      enabled: false
      models: ["opus", "sonnet", "haiku"]
      consensus: "majority"          # majority | supermajority | unanimous
      min_models: 2                  # Minimum models required for valid consensus
      panels: []                     # Panels to run multi-model. Empty = all panels.

Default: disabled (backward compatible single-model behavior).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum


class ConsensusStrategy(str, Enum):
    """How to aggregate multi-model verdicts."""
    MAJORITY = "majority"            # > 50% agree
    SUPERMAJORITY = "supermajority"  # >= 75% agree (3/4)
    UNANIMOUS = "unanimous"          # 100% agree


@dataclass(frozen=True)
class MultiModelConfig:
    """Configuration for multi-model validation."""
    enabled: bool = False
    models: list[str] = field(default_factory=list)
    consensus: ConsensusStrategy = ConsensusStrategy.MAJORITY
    min_models: int = 2
    panels: list[str] = field(default_factory=list)  # empty = all panels

    @classmethod
    def from_dict(cls, data: dict | None) -> MultiModelConfig:
        """Parse from a policy profile's multi_model section."""
        if not data:
            return cls()
        if not data.get("enabled", False):
            return cls()

        consensus_str = data.get("consensus", "majority")
        try:
            consensus = ConsensusStrategy(consensus_str)
        except ValueError:
            consensus = ConsensusStrategy.MAJORITY

        return cls(
            enabled=True,
            models=data.get("models", []),
            consensus=consensus,
            min_models=data.get("min_models", 2),
            panels=data.get("panels", []),
        )

    def applies_to_panel(self, panel_name: str) -> bool:
        """Check if multi-model validation applies to a given panel."""
        if not self.enabled:
            return False
        if not self.panels:
            return True  # All panels
        return panel_name in self.panels


@dataclass
class ModelEmission:
    """A single model's emission for a panel."""
    model_id: str
    panel_name: str
    verdict: str
    confidence_score: float
    risk_level: str = "low"
    findings_count: int = 0
    raw_emission: dict = field(default_factory=dict)


@dataclass
class AggregatedVerdict:
    """Consensus result from multi-model validation."""
    panel_name: str
    verdict: str                      # The consensus verdict
    confidence_score: float           # Average confidence across models
    consensus_reached: bool           # Whether consensus threshold was met
    consensus_strategy: str           # Strategy used
    model_count: int                  # Number of models that participated
    agreeing_count: int               # Number of models that agree with verdict
    model_verdicts: list[dict] = field(default_factory=list)  # Per-model detail
    risk_level: str = "low"

    def to_dict(self) -> dict:
        return {
            "panel_name": self.panel_name,
            "verdict": self.verdict,
            "confidence_score": self.confidence_score,
            "consensus_reached": self.consensus_reached,
            "consensus_strategy": self.consensus_strategy,
            "model_count": self.model_count,
            "agreeing_count": self.agreeing_count,
            "model_verdicts": self.model_verdicts,
            "risk_level": self.risk_level,
        }


class MultiModelAggregator:
    """Aggregates emissions from multiple models into consensus verdicts."""

    def __init__(self, config: MultiModelConfig | None = None):
        self._config = config or MultiModelConfig()

    @property
    def config(self) -> MultiModelConfig:
        return self._config

    @property
    def is_enabled(self) -> bool:
        return self._config.enabled

    def group_emissions(self, emissions: list[dict]) -> dict[str, list[ModelEmission]]:
        """Group emissions by panel name, identifying multi-model emissions.

        Multi-model emissions are identified by:
        1. A 'model_id' field in the emission
        2. Multiple emissions for the same panel_name

        Returns:
            Dict mapping panel_name to list of ModelEmission objects.
        """
        groups: dict[str, list[ModelEmission]] = {}

        for emission in emissions:
            panel_name = emission.get("panel_name", "")
            if not panel_name:
                continue

            model_id = emission.get("model_id", emission.get("model", "unknown"))
            me = ModelEmission(
                model_id=model_id,
                panel_name=panel_name,
                verdict=emission.get("verdict", "unknown"),
                confidence_score=float(emission.get("confidence_score", 0.0)),
                risk_level=emission.get("risk_level", "low"),
                findings_count=len(emission.get("findings", [])),
                raw_emission=emission,
            )

            if panel_name not in groups:
                groups[panel_name] = []
            groups[panel_name].append(me)

        return groups

    def aggregate(self, emissions: list[ModelEmission]) -> AggregatedVerdict:
        """Aggregate multiple model emissions for a single panel into a consensus.

        Args:
            emissions: List of emissions from different models for the same panel.

        Returns:
            AggregatedVerdict with the consensus result.
        """
        if not emissions:
            return AggregatedVerdict(
                panel_name="unknown",
                verdict="no_data",
                confidence_score=0.0,
                consensus_reached=False,
                consensus_strategy=self._config.consensus.value,
                model_count=0,
                agreeing_count=0,
            )

        panel_name = emissions[0].panel_name
        model_count = len(emissions)

        # Count verdicts
        verdict_counts: dict[str, int] = {}
        total_confidence = 0.0
        risk_levels: list[str] = []

        model_verdicts = []
        for em in emissions:
            verdict_counts[em.verdict] = verdict_counts.get(em.verdict, 0) + 1
            total_confidence += em.confidence_score
            risk_levels.append(em.risk_level)
            model_verdicts.append({
                "model_id": em.model_id,
                "verdict": em.verdict,
                "confidence_score": em.confidence_score,
                "risk_level": em.risk_level,
                "findings_count": em.findings_count,
            })

        avg_confidence = total_confidence / model_count if model_count > 0 else 0.0

        # Determine majority verdict
        majority_verdict = max(verdict_counts, key=verdict_counts.get)
        majority_count = verdict_counts[majority_verdict]

        # Check consensus threshold
        consensus_reached = self._check_consensus(majority_count, model_count)

        # If consensus not reached, escalate to human review
        if not consensus_reached:
            final_verdict = "human_review_required"
        else:
            final_verdict = majority_verdict

        # Risk level: use the highest risk from any model
        risk_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        highest_risk = max(risk_levels, key=lambda r: risk_order.get(r, 0))

        # Minimum models check
        if model_count < self._config.min_models:
            consensus_reached = False
            final_verdict = "insufficient_models"

        return AggregatedVerdict(
            panel_name=panel_name,
            verdict=final_verdict,
            confidence_score=round(avg_confidence, 4),
            consensus_reached=consensus_reached,
            consensus_strategy=self._config.consensus.value,
            model_count=model_count,
            agreeing_count=majority_count,
            model_verdicts=model_verdicts,
            risk_level=highest_risk,
        )

    def _check_consensus(self, agreeing_count: int, total_count: int) -> bool:
        """Check if the agreeing count meets the consensus threshold."""
        if total_count == 0:
            return False

        ratio = agreeing_count / total_count

        if self._config.consensus == ConsensusStrategy.UNANIMOUS:
            return agreeing_count == total_count
        elif self._config.consensus == ConsensusStrategy.SUPERMAJORITY:
            return ratio >= 0.75
        else:  # MAJORITY
            return ratio > 0.5

    def confidence_adjustment(self, verdict: AggregatedVerdict) -> float:
        """Calculate a confidence multiplier based on consensus strength.

        Returns a value between 0.0 and 1.0 that should be applied to
        the base confidence score:
        - Unanimous: 1.0 (no penalty)
        - Supermajority: 0.95
        - Majority: 0.90
        - No consensus: 0.70
        - Insufficient models: 0.65

        Args:
            verdict: The aggregated verdict to assess.

        Returns:
            Confidence multiplier (0.0 to 1.0).
        """
        if verdict.verdict == "insufficient_models":
            return 0.65
        if not verdict.consensus_reached:
            return 0.70
        strategy_multipliers = {
            "unanimous": 1.0,
            "supermajority": 0.95,
            "majority": 0.90,
        }
        return strategy_multipliers.get(verdict.consensus_strategy, 0.90)

    def process_all_panels(self, all_emissions: list[dict]) -> dict[str, AggregatedVerdict]:
        """Process all emissions and return aggregated verdicts for multi-model panels.

        Single-model panels are not aggregated (returned as-is through the policy engine).

        Returns:
            Dict mapping panel_name to AggregatedVerdict for panels with multi-model emissions.
        """
        groups = self.group_emissions(all_emissions)
        results: dict[str, AggregatedVerdict] = {}

        for panel_name, emissions in groups.items():
            if len(emissions) > 1 and self._config.applies_to_panel(panel_name):
                results[panel_name] = self.aggregate(emissions)

        return results
