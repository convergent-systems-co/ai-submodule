"""Tests for the Governance-as-a-Service REST API models.

These tests validate the API model definitions. The full API integration
tests require pydantic and fastapi, which are installed in the Docker
container but may not be available locally.
"""

import pytest

pydantic = pytest.importorskip("pydantic", reason="pydantic required for API tests")

from governance.engine.api.models import (
    EvaluateRequest,
    EvaluateResponse,
    HealthResponse,
    PolicyDecision,
    ProfileInfo,
    ProfileListResponse,
    RiskLevel,
    ValidateRequest,
    ValidateResponse,
)


class TestEvaluateRequest:
    def test_valid_request(self):
        req = EvaluateRequest(
            emissions=[{"panel_name": "code-review", "verdict": "pass", "confidence_score": 0.9}],
            profile="default",
        )
        assert req.profile == "default"
        assert len(req.emissions) == 1

    def test_default_profile(self):
        req = EvaluateRequest(
            emissions=[{"panel_name": "test", "verdict": "pass", "confidence_score": 0.8}],
        )
        assert req.profile == "default"

    def test_dry_run_flag(self):
        req = EvaluateRequest(
            emissions=[{"panel_name": "test", "verdict": "pass", "confidence_score": 0.8}],
            dry_run=True,
        )
        assert req.dry_run is True


class TestEvaluateResponse:
    def test_auto_merge_response(self):
        resp = EvaluateResponse(
            decision=PolicyDecision.AUTO_MERGE,
            confidence=0.92,
            risk_level=RiskLevel.LOW,
            panels_evaluated=3,
            panels_passed=3,
            panels_failed=0,
        )
        assert resp.decision == PolicyDecision.AUTO_MERGE
        assert resp.confidence == 0.92

    def test_block_response(self):
        resp = EvaluateResponse(
            decision=PolicyDecision.BLOCK,
            confidence=0.3,
            risk_level=RiskLevel.CRITICAL,
            panels_evaluated=3,
            panels_passed=1,
            panels_failed=2,
        )
        assert resp.decision == PolicyDecision.BLOCK


class TestValidateRequest:
    def test_valid_request(self):
        req = ValidateRequest(
            emissions=[{"panel_name": "test", "aggregate_verdict": "approve", "confidence_score": 0.8}],
        )
        assert len(req.emissions) == 1


class TestValidateResponse:
    def test_valid_response(self):
        resp = ValidateResponse(valid=True, errors=[], emissions_count=2)
        assert resp.valid is True

    def test_invalid_response(self):
        resp = ValidateResponse(
            valid=False,
            errors=["missing panel_name"],
            emissions_count=1,
        )
        assert resp.valid is False
        assert len(resp.errors) == 1


class TestProfileInfo:
    def test_profile_info(self):
        info = ProfileInfo(
            name="default",
            version="1.5.0",
            description="Default profile",
            required_panels=["code-review", "security-review"],
            auto_merge_enabled=True,
        )
        assert info.name == "default"
        assert info.auto_merge_enabled is True


class TestHealthResponse:
    def test_healthy(self):
        resp = HealthResponse(
            status="healthy",
            version="1.0.0",
            engine_available=True,
            profiles_loaded=5,
        )
        assert resp.status == "healthy"
        assert resp.profiles_loaded == 5


class TestPolicyDecision:
    def test_enum_values(self):
        assert PolicyDecision.AUTO_MERGE == "auto_merge"
        assert PolicyDecision.BLOCK == "block"
        assert PolicyDecision.HUMAN_REVIEW_REQUIRED == "human_review_required"
        assert PolicyDecision.AUTO_REMEDIATE == "auto_remediate"


class TestRiskLevel:
    def test_enum_values(self):
        assert RiskLevel.CRITICAL == "critical"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.NEGLIGIBLE == "negligible"
