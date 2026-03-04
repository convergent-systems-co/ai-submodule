"""Tests for multi_model_integration — policy engine integration layer."""

import pytest

from governance.engine.multi_model_aggregator import (
    AggregatedVerdict,
    ConsensusStrategy,
    MultiModelAggregator,
    MultiModelConfig,
)
from governance.engine.multi_model_integration import (
    MultiModelResult,
    confidence_adjustment,
    get_confidence_multiplier,
    merge_into_emissions,
    process_multi_model_emissions,
)


# ---------------------------------------------------------------------------
# confidence_adjustment
# ---------------------------------------------------------------------------

class TestConfidenceAdjustment:
    def _make_verdict(
        self,
        consensus_reached: bool = True,
        strategy: str = "majority",
        verdict: str = "pass",
        confidence: float = 0.85,
        model_count: int = 3,
        agreeing_count: int = 2,
    ) -> AggregatedVerdict:
        return AggregatedVerdict(
            panel_name="security-review",
            verdict=verdict,
            confidence_score=confidence,
            consensus_reached=consensus_reached,
            consensus_strategy=strategy,
            model_count=model_count,
            agreeing_count=agreeing_count,
        )

    def test_unanimous_no_penalty(self):
        v = self._make_verdict(strategy="unanimous", consensus_reached=True)
        result = confidence_adjustment(0.90, v)
        assert result == 0.90  # 0.90 * 1.0

    def test_supermajority_slight_reduction(self):
        v = self._make_verdict(strategy="supermajority", consensus_reached=True)
        result = confidence_adjustment(0.90, v)
        assert result == 0.855  # 0.90 * 0.95

    def test_majority_moderate_reduction(self):
        v = self._make_verdict(strategy="majority", consensus_reached=True)
        result = confidence_adjustment(0.90, v)
        assert result == 0.81  # 0.90 * 0.90

    def test_no_consensus_caps_at_070(self):
        v = self._make_verdict(consensus_reached=False, confidence=0.90)
        result = confidence_adjustment(0.90, v)
        assert result == 0.70

    def test_no_consensus_low_confidence_unchanged(self):
        v = self._make_verdict(consensus_reached=False, confidence=0.50)
        result = confidence_adjustment(0.50, v)
        assert result == 0.50  # Already below cap

    def test_insufficient_models_caps_at_065(self):
        v = self._make_verdict(verdict="insufficient_models", confidence=0.90)
        result = confidence_adjustment(0.90, v)
        assert result == 0.65

    def test_capped_at_one(self):
        v = self._make_verdict(strategy="unanimous", consensus_reached=True)
        result = confidence_adjustment(1.5, v)
        assert result == 1.0


# ---------------------------------------------------------------------------
# get_confidence_multiplier
# ---------------------------------------------------------------------------

class TestGetConfidenceMultiplier:
    def test_unanimous_multiplier(self):
        v = AggregatedVerdict(
            panel_name="test", verdict="pass", confidence_score=0.9,
            consensus_reached=True, consensus_strategy="unanimous",
            model_count=3, agreeing_count=3,
        )
        assert get_confidence_multiplier(v) == 1.0

    def test_no_consensus_multiplier(self):
        v = AggregatedVerdict(
            panel_name="test", verdict="human_review_required",
            confidence_score=0.9, consensus_reached=False,
            consensus_strategy="majority", model_count=3, agreeing_count=1,
        )
        # 0.70 / 0.9 = ~0.778
        m = get_confidence_multiplier(v)
        assert 0.77 < m < 0.79

    def test_insufficient_models_multiplier(self):
        v = AggregatedVerdict(
            panel_name="test", verdict="insufficient_models",
            confidence_score=0.9, consensus_reached=False,
            consensus_strategy="majority", model_count=1, agreeing_count=1,
        )
        assert get_confidence_multiplier(v) == 0.65


# ---------------------------------------------------------------------------
# process_multi_model_emissions
# ---------------------------------------------------------------------------

class TestProcessMultiModelEmissions:
    def test_disabled_returns_empty(self):
        config = MultiModelConfig(enabled=False)
        result = process_multi_model_emissions([], config)
        assert result == {}

    def test_single_panel_two_models(self):
        config = MultiModelConfig(
            enabled=True,
            models=["opus", "sonnet"],
            consensus=ConsensusStrategy.MAJORITY,
            min_models=2,
        )
        emissions = [
            {
                "panel_name": "security-review",
                "model_id": "opus",
                "verdict": "pass",
                "confidence_score": 0.9,
                "risk_level": "low",
            },
            {
                "panel_name": "security-review",
                "model_id": "sonnet",
                "verdict": "pass",
                "confidence_score": 0.8,
                "risk_level": "low",
            },
        ]
        results = process_multi_model_emissions(emissions, config)
        assert "security-review" in results
        r = results["security-review"]
        assert r.consensus_reached is True
        assert r.verdict == "pass"
        assert r.model_count == 2
        assert r.adjusted_confidence < r.original_confidence  # Majority reduces

    def test_mixed_verdicts_no_consensus(self):
        config = MultiModelConfig(
            enabled=True,
            models=["opus", "sonnet"],
            consensus=ConsensusStrategy.UNANIMOUS,
            min_models=2,
        )
        emissions = [
            {
                "panel_name": "security-review",
                "model_id": "opus",
                "verdict": "pass",
                "confidence_score": 0.9,
            },
            {
                "panel_name": "security-review",
                "model_id": "sonnet",
                "verdict": "fail",
                "confidence_score": 0.3,
            },
        ]
        results = process_multi_model_emissions(emissions, config)
        r = results["security-review"]
        assert r.consensus_reached is False
        assert r.verdict == "human_review_required"

    def test_result_to_dict(self):
        config = MultiModelConfig(
            enabled=True, models=["opus", "sonnet"],
            consensus=ConsensusStrategy.MAJORITY, min_models=2,
        )
        emissions = [
            {"panel_name": "code-review", "model_id": "opus", "verdict": "pass", "confidence_score": 0.85},
            {"panel_name": "code-review", "model_id": "sonnet", "verdict": "pass", "confidence_score": 0.80},
        ]
        results = process_multi_model_emissions(emissions, config)
        d = results["code-review"].to_dict()
        assert "adjusted_confidence" in d
        assert "original_confidence" in d
        assert "consensus_reached" in d


# ---------------------------------------------------------------------------
# merge_into_emissions
# ---------------------------------------------------------------------------

class TestMergeIntoEmissions:
    def test_no_results_returns_original(self):
        emissions = [{"panel_name": "code-review", "verdict": "pass"}]
        result = merge_into_emissions(emissions, {})
        assert result == emissions

    def test_consolidates_multi_model_emissions(self):
        original = [
            {"panel_name": "security-review", "model_id": "opus", "verdict": "pass", "confidence_score": 0.9},
            {"panel_name": "security-review", "model_id": "sonnet", "verdict": "pass", "confidence_score": 0.8},
            {"panel_name": "code-review", "verdict": "pass", "confidence_score": 0.85},
        ]
        mm_result = MultiModelResult(
            panel_name="security-review",
            adjusted_confidence=0.765,
            original_confidence=0.85,
            consensus_reached=True,
            consensus_strategy="majority",
            verdict="pass",
            model_count=2,
            agreeing_count=2,
            confidence_multiplier=0.90,
            model_verdicts=[],
        )
        merged = merge_into_emissions(original, {"security-review": mm_result})
        # Should have 2 entries: consolidated security-review + code-review
        assert len(merged) == 2
        sec = next(e for e in merged if e["panel_name"] == "security-review")
        assert sec["verdict"] == "pass"
        assert sec["confidence_score"] == 0.765
        assert "multi_model" in sec
        assert "model_id" not in sec

    def test_preserves_non_aggregated_emissions(self):
        original = [
            {"panel_name": "code-review", "verdict": "pass", "confidence_score": 0.85},
            {"panel_name": "docs-review", "verdict": "pass", "confidence_score": 0.9},
        ]
        merged = merge_into_emissions(original, {})
        assert len(merged) == 2
