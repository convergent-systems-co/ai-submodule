"""Pydantic models for the Governance-as-a-Service REST API."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PolicyDecision(str, Enum):
    """Policy engine decision outcomes."""

    AUTO_MERGE = "auto_merge"
    BLOCK = "block"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    AUTO_REMEDIATE = "auto_remediate"


class RiskLevel(str, Enum):
    """Risk level classifications."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


# --- Request Models ---


class EvaluateRequest(BaseModel):
    """Request body for policy evaluation."""

    emissions: list[dict[str, Any]] = Field(
        ...,
        description="List of panel emission objects to evaluate.",
        min_length=1,
    )
    profile: str = Field(
        default="default",
        description="Policy profile name to evaluate against.",
    )
    pr_number: int | None = Field(
        default=None,
        description="Optional PR number for context.",
    )
    files_changed: int | None = Field(
        default=None,
        description="Number of files changed in the PR.",
    )
    dry_run: bool = Field(
        default=False,
        description="If true, evaluate but always return success exit code.",
    )


class ValidateRequest(BaseModel):
    """Request body for emission schema validation."""

    emissions: list[dict[str, Any]] = Field(
        ...,
        description="List of panel emission objects to validate.",
        min_length=1,
    )


# --- Response Models ---


class EvaluateResponse(BaseModel):
    """Response body for policy evaluation."""

    decision: PolicyDecision
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    panels_evaluated: int
    panels_passed: int
    panels_failed: int
    evaluation_log: list[dict[str, str]] = Field(default_factory=list)
    dry_run: bool = False


class ValidateResponse(BaseModel):
    """Response body for emission validation."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    emissions_count: int


class ProfileInfo(BaseModel):
    """Information about a policy profile."""

    name: str
    version: str
    description: str
    required_panels: list[str] = Field(default_factory=list)
    auto_merge_enabled: bool = False
    multi_model_enabled: bool = False


class ProfileListResponse(BaseModel):
    """Response body for listing policy profiles."""

    profiles: list[ProfileInfo]
    default_profile: str = "default"


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    engine_available: bool = True
    profiles_loaded: int = 0
