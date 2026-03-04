"""Tests for multi_model_aggregator — multi-model consensus validation."""

import pytest

from governance.engine.multi_model_aggregator import (
    AggregatedVerdict,
    ConsensusStrategy,
    ModelEmission,
    MultiModelAggregator,
    MultiModelConfig,
)


class TestMultiModelConfig:
    """Tests for MultiModelConfig parsing."""

    def test_default_config_disabled(self):
        config = MultiModelConfig()
        assert config.enabled is False
        assert config.consensus == ConsensusStrategy.MAJORITY

    def test_from_dict_none(self):
        config = MultiModelConfig.from_dict(None)
        assert config.enabled is False

    def test_from_dict_disabled(self):
        config = MultiModelConfig.from_dict({"enabled": False})
        assert config.enabled is False

    def test_from_dict_enabled(self):
        config = MultiModelConfig.from_dict({
            "enabled": True,
            "models": ["opus", "sonnet", "haiku"],
            "consensus": "supermajority",
            "min_models": 3,
            "panels": ["security-review"],
        })
        assert config.enabled is True
        assert config.models == ["opus", "sonnet", "haiku"]
        assert config.consensus == ConsensusStrategy.SUPERMAJORITY
        assert config.min_models == 3
        assert config.panels == ["security-review"]

    def test_from_dict_invalid_consensus(self):
        config = MultiModelConfig.from_dict({
            "enabled": True,
            "consensus": "invalid_strategy",
        })
        assert config.consensus == ConsensusStrategy.MAJORITY

    def test_applies_to_panel_all(self):
        config = MultiModelConfig(enabled=True, panels=[])
        assert config.applies_to_panel("any-panel") is True

    def test_applies_to_panel_specific(self):
        config = MultiModelConfig(enabled=True, panels=["security-review"])
        assert config.applies_to_panel("security-review") is True
        assert config.applies_to_panel("code-review") is False

    def test_applies_to_panel_disabled(self):
        config = MultiModelConfig(enabled=False)
        assert config.applies_to_panel("security-review") is False


class TestMultiModelAggregator:
    """Tests for consensus aggregation."""

    def _make_emission(self, model_id: str, verdict: str, confidence: float = 0.8) -> ModelEmission:
        return ModelEmission(
            model_id=model_id,
            panel_name="security-review",
            verdict=verdict,
            confidence_score=confidence,
            risk_level="low",
        )

    def test_empty_emissions(self):
        agg = MultiModelAggregator()
        result = agg.aggregate([])
        assert result.verdict == "no_data"
        assert result.consensus_reached is False

    def test_unanimous_pass(self):
        config = MultiModelConfig(enabled=True, consensus=ConsensusStrategy.UNANIMOUS, min_models=2)
        agg = MultiModelAggregator(config)
        emissions = [
            self._make_emission("opus", "pass", 0.9),
            self._make_emission("sonnet", "pass", 0.85),
            self._make_emission("haiku", "pass", 0.8),
        ]
        result = agg.aggregate(emissions)
        assert result.verdict == "pass"
        assert result.consensus_reached is True
        assert result.model_count == 3
        assert result.agreeing_count == 3

    def test_unanimous_fails_with_dissent(self):
        config = MultiModelConfig(enabled=True, consensus=ConsensusStrategy.UNANIMOUS, min_models=2)
        agg = MultiModelAggregator(config)
        emissions = [
            self._make_emission("opus", "pass", 0.9),
            self._make_emission("sonnet", "pass", 0.85),
            self._make_emission("haiku", "fail", 0.3),
        ]
        result = agg.aggregate(emissions)
        assert result.verdict == "human_review_required"
        assert result.consensus_reached is False

    def test_majority_consensus(self):
        config = MultiModelConfig(enabled=True, consensus=ConsensusStrategy.MAJORITY, min_models=2)
        agg = MultiModelAggregator(config)
        emissions = [
            self._make_emission("opus", "pass", 0.9),
            self._make_emission("sonnet", "pass", 0.85),
            self._make_emission("haiku", "fail", 0.3),
        ]
        result = agg.aggregate(emissions)
        assert result.verdict == "pass"
        assert result.consensus_reached is True
        assert result.agreeing_count == 2

    def test_supermajority_three_of_four(self):
        config = MultiModelConfig(enabled=True, consensus=ConsensusStrategy.SUPERMAJORITY, min_models=2)
        agg = MultiModelAggregator(config)
        emissions = [
            self._make_emission("opus", "pass", 0.9),
            self._make_emission("sonnet", "pass", 0.85),
            self._make_emission("haiku", "pass", 0.8),
            self._make_emission("gpt4", "fail", 0.3),
        ]
        result = agg.aggregate(emissions)
        assert result.verdict == "pass"
        assert result.consensus_reached is True

    def test_supermajority_fails_two_of_four(self):
        config = MultiModelConfig(enabled=True, consensus=ConsensusStrategy.SUPERMAJORITY, min_models=2)
        agg = MultiModelAggregator(config)
        emissions = [
            self._make_emission("opus", "pass", 0.9),
            self._make_emission("sonnet", "pass", 0.85),
            self._make_emission("haiku", "fail", 0.3),
            self._make_emission("gpt4", "fail", 0.4),
        ]
        result = agg.aggregate(emissions)
        assert result.verdict == "human_review_required"
        assert result.consensus_reached is False

    def test_insufficient_models(self):
        config = MultiModelConfig(enabled=True, min_models=3)
        agg = MultiModelAggregator(config)
        emissions = [
            self._make_emission("opus", "pass", 0.9),
            self._make_emission("sonnet", "pass", 0.85),
        ]
        result = agg.aggregate(emissions)
        assert result.verdict == "insufficient_models"
        assert result.consensus_reached is False

    def test_average_confidence(self):
        config = MultiModelConfig(enabled=True, min_models=2)
        agg = MultiModelAggregator(config)
        emissions = [
            self._make_emission("opus", "pass", 0.9),
            self._make_emission("sonnet", "pass", 0.8),
        ]
        result = agg.aggregate(emissions)
        assert result.confidence_score == 0.85

    def test_highest_risk_used(self):
        config = MultiModelConfig(enabled=True, min_models=2)
        agg = MultiModelAggregator(config)
        emissions = [
            ModelEmission("opus", "security-review", "pass", 0.9, "low"),
            ModelEmission("sonnet", "security-review", "pass", 0.8, "high"),
        ]
        result = agg.aggregate(emissions)
        assert result.risk_level == "high"

    def test_model_verdicts_in_output(self):
        config = MultiModelConfig(enabled=True, min_models=2)
        agg = MultiModelAggregator(config)
        emissions = [
            self._make_emission("opus", "pass", 0.9),
            self._make_emission("sonnet", "pass", 0.8),
        ]
        result = agg.aggregate(emissions)
        assert len(result.model_verdicts) == 2
        assert result.model_verdicts[0]["model_id"] == "opus"


class TestGroupEmissions:
    """Tests for emission grouping."""

    def test_group_by_panel(self):
        agg = MultiModelAggregator()
        emissions = [
            {"panel_name": "security-review", "model_id": "opus", "verdict": "pass", "confidence_score": 0.9},
            {"panel_name": "security-review", "model_id": "sonnet", "verdict": "pass", "confidence_score": 0.8},
            {"panel_name": "code-review", "model_id": "opus", "verdict": "pass", "confidence_score": 0.85},
        ]
        groups = agg.group_emissions(emissions)
        assert "security-review" in groups
        assert len(groups["security-review"]) == 2
        assert "code-review" in groups
        assert len(groups["code-review"]) == 1

    def test_skip_empty_panel_name(self):
        agg = MultiModelAggregator()
        emissions = [{"verdict": "pass", "confidence_score": 0.9}]
        groups = agg.group_emissions(emissions)
        assert len(groups) == 0


class TestProcessAllPanels:
    """Tests for full pipeline processing."""

    def test_only_multi_model_panels_aggregated(self):
        config = MultiModelConfig(enabled=True, min_models=2)
        agg = MultiModelAggregator(config)
        emissions = [
            {"panel_name": "security-review", "model_id": "opus", "verdict": "pass", "confidence_score": 0.9},
            {"panel_name": "security-review", "model_id": "sonnet", "verdict": "pass", "confidence_score": 0.8},
            {"panel_name": "code-review", "model_id": "opus", "verdict": "pass", "confidence_score": 0.85},
        ]
        results = agg.process_all_panels(emissions)
        assert "security-review" in results
        assert "code-review" not in results  # Only one emission, not aggregated

    def test_respects_panel_filter(self):
        config = MultiModelConfig(enabled=True, min_models=2, panels=["security-review"])
        agg = MultiModelAggregator(config)
        emissions = [
            {"panel_name": "security-review", "model_id": "opus", "verdict": "pass", "confidence_score": 0.9},
            {"panel_name": "security-review", "model_id": "sonnet", "verdict": "pass", "confidence_score": 0.8},
            {"panel_name": "code-review", "model_id": "opus", "verdict": "pass", "confidence_score": 0.85},
            {"panel_name": "code-review", "model_id": "sonnet", "verdict": "pass", "confidence_score": 0.8},
        ]
        results = agg.process_all_panels(emissions)
        assert "security-review" in results
        assert "code-review" not in results  # Filtered out

    def test_to_dict(self):
        config = MultiModelConfig(enabled=True, min_models=2)
        agg = MultiModelAggregator(config)
        emissions = [
            {"panel_name": "security-review", "model_id": "opus", "verdict": "pass", "confidence_score": 0.9},
            {"panel_name": "security-review", "model_id": "sonnet", "verdict": "pass", "confidence_score": 0.8},
        ]
        results = agg.process_all_panels(emissions)
        d = results["security-review"].to_dict()
        assert d["panel_name"] == "security-review"
        assert d["consensus_reached"] is True
