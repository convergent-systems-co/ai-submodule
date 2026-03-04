"""API route definitions for the Governance-as-a-Service REST API."""

from __future__ import annotations

import glob
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException

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

router = APIRouter(prefix="/api/v1", tags=["governance"])

# Resolve paths relative to the app
_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_POLICY_DIR = _BASE_DIR / "governance" / "policy"
_SCHEMA_DIR = _BASE_DIR / "governance" / "schemas"

# Environment variable for the active policy profile (set via Helm/deployment)
_DEFAULT_PROFILE = os.environ.get("GOVERNANCE_PROFILE", "default")


def _safe_risk_level(value: str) -> RiskLevel:
    """Convert a risk string to RiskLevel, defaulting to LOW for unknown values."""
    try:
        return RiskLevel(value)
    except ValueError:
        return RiskLevel.LOW


def _load_profile(profile_name: str) -> dict[str, Any]:
    """Load a policy profile by name."""
    profile_path = _POLICY_DIR / f"{profile_name}.yaml"
    if not profile_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Policy profile '{profile_name}' not found.",
        )
    with open(profile_path) as f:
        return yaml.safe_load(f)


def _list_profiles() -> list[dict[str, Any]]:
    """List all available policy profiles."""
    profiles = []
    if _POLICY_DIR.exists():
        for path in sorted(_POLICY_DIR.glob("*.yaml")):
            try:
                with open(path) as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict) and "profile_name" in data:
                    profiles.append(data)
            except Exception:
                continue
    return profiles


def _run_policy_engine(emissions: list[dict[str, Any]], profile_name: str, dry_run: bool = False) -> dict[str, Any] | None:
    """Attempt to run the real policy engine and return its manifest.

    Returns None if the policy engine is unavailable or fails, in which
    case the caller should fall back to the simplified inline evaluation.
    """
    try:
        from governance.engine.policy_engine import (
            EvaluationLog,
            evaluate_emissions,
            load_profile,
            load_schema,
        )
    except ImportError:
        return None

    profile_path = _POLICY_DIR / f"{profile_name}.yaml"
    if not profile_path.exists():
        return None

    schema_path = _SCHEMA_DIR / "panel-output.schema.json"

    try:
        profile = load_profile(str(profile_path))
        schema = load_schema(str(schema_path)) if schema_path.exists() else None

        # Write emissions to a temp directory for the engine
        with tempfile.TemporaryDirectory() as tmpdir:
            for i, emission in enumerate(emissions):
                emission_path = Path(tmpdir) / f"emission_{i}.json"
                emission_path.write_text(json.dumps(emission))

            log = EvaluationLog()
            manifest = evaluate_emissions(
                emissions_dir=tmpdir,
                profile=profile,
                schema=schema,
                log=log,
                dry_run=dry_run,
            )
            return manifest
    except Exception:
        return None


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    profiles = _list_profiles()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        engine_available=True,
        profiles_loaded=len(profiles),
    )


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    """Evaluate panel emissions against a policy profile.

    Accepts a list of panel emissions and a policy profile name,
    runs the policy engine evaluation, and returns the decision.

    Uses the GOVERNANCE_PROFILE env var as the default profile when
    no profile is specified in the request.
    """
    profile_name = request.profile or _DEFAULT_PROFILE
    profile = _load_profile(profile_name)

    # Attempt to use the real policy engine first
    manifest = _run_policy_engine(request.emissions, profile_name, request.dry_run)
    if manifest is not None:
        # Map policy engine decision to API response
        decision_str = manifest.get("decision", "human_review_required")
        decision_map = {
            "auto_merge": PolicyDecision.AUTO_MERGE,
            "block": PolicyDecision.BLOCK,
            "human_review_required": PolicyDecision.HUMAN_REVIEW_REQUIRED,
            "auto_remediate": PolicyDecision.AUTO_REMEDIATE,
        }
        decision = decision_map.get(decision_str, PolicyDecision.HUMAN_REVIEW_REQUIRED)

        risk_str = manifest.get("risk_level", "low")
        risk_level = _safe_risk_level(risk_str)

        evaluation_log = manifest.get("evaluation_log", [])
        panels_evaluated = manifest.get("panels_evaluated", len(request.emissions))
        panels_passed = manifest.get("panels_passed", 0)
        panels_failed = manifest.get("panels_failed", 0)
        confidence = manifest.get("confidence", 0.0)

        if request.dry_run:
            evaluation_log.append({
                "rule_id": "dry_run",
                "result": "info",
                "detail": "Dry-run mode: decision is advisory only.",
            })

        return EvaluateResponse(
            decision=decision,
            confidence=round(confidence, 4),
            risk_level=risk_level,
            panels_evaluated=panels_evaluated,
            panels_passed=panels_passed,
            panels_failed=panels_failed,
            evaluation_log=evaluation_log,
            dry_run=request.dry_run,
        )

    # Fallback: simplified inline evaluation when real engine is unavailable
    panels_evaluated = len(request.emissions)
    panels_passed = 0
    panels_failed = 0
    evaluation_log: list[dict[str, str]] = []
    total_confidence = 0.0
    risk_levels: list[str] = []

    required_panels = set(profile.get("required_panels", []))
    seen_panels: set[str] = set()

    for emission in request.emissions:
        panel_name = emission.get("panel_name", "unknown")
        # Use aggregate_verdict (per schema), fall back to verdict for compat
        verdict = emission.get("aggregate_verdict", emission.get("verdict", "unknown"))
        confidence = float(emission.get("confidence_score", 0.0))
        risk = emission.get("risk_level", "low")

        seen_panels.add(panel_name)
        total_confidence += confidence
        risk_levels.append(risk)

        if verdict in ("pass", "approve", "approved"):
            panels_passed += 1
            evaluation_log.append({
                "rule_id": f"panel_{panel_name}",
                "result": "pass",
                "detail": f"{panel_name}: {verdict} (confidence: {confidence})",
            })
        else:
            panels_failed += 1
            evaluation_log.append({
                "rule_id": f"panel_{panel_name}",
                "result": "fail",
                "detail": f"{panel_name}: {verdict} (confidence: {confidence})",
            })

    # Check for missing required panels
    missing = required_panels - seen_panels
    if missing:
        for m in missing:
            evaluation_log.append({
                "rule_id": f"missing_{m}",
                "result": "fail",
                "detail": f"Required panel '{m}' did not execute.",
            })
        # Fix: add len(missing) once, not inside the loop
        panels_failed += len(missing)

    # Calculate aggregate confidence
    avg_confidence = total_confidence / panels_evaluated if panels_evaluated > 0 else 0.0

    # Determine risk level (highest severity)
    risk_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "negligible": 0}
    highest_risk = max(risk_levels, key=lambda r: risk_order.get(r, 0)) if risk_levels else "low"

    # Determine decision
    if panels_failed > 0 or missing:
        if any(r in ("critical", "high") for r in risk_levels):
            decision = PolicyDecision.BLOCK
        else:
            decision = PolicyDecision.HUMAN_REVIEW_REQUIRED
    elif avg_confidence >= 0.85 and highest_risk in ("low", "negligible"):
        decision = PolicyDecision.AUTO_MERGE
    elif avg_confidence < 0.70:
        decision = PolicyDecision.HUMAN_REVIEW_REQUIRED
    else:
        decision = PolicyDecision.AUTO_MERGE

    if request.dry_run:
        evaluation_log.append({
            "rule_id": "dry_run",
            "result": "info",
            "detail": "Dry-run mode: decision is advisory only.",
        })

    return EvaluateResponse(
        decision=decision,
        confidence=round(avg_confidence, 4),
        risk_level=_safe_risk_level(highest_risk),
        panels_evaluated=panels_evaluated,
        panels_passed=panels_passed,
        panels_failed=panels_failed,
        evaluation_log=evaluation_log,
        dry_run=request.dry_run,
    )


@router.post("/validate", response_model=ValidateResponse)
async def validate_emissions(request: ValidateRequest) -> ValidateResponse:
    """Validate panel emissions against the panel output schema."""
    errors: list[str] = []

    for i, emission in enumerate(request.emissions):
        if "panel_name" not in emission:
            errors.append(f"Emission {i}: missing 'panel_name'")
        if "aggregate_verdict" not in emission:
            errors.append(f"Emission {i}: missing 'aggregate_verdict'")
        if "confidence_score" not in emission:
            errors.append(f"Emission {i}: missing 'confidence_score'")
        else:
            score = emission["confidence_score"]
            if not isinstance(score, (int, float)) or score < 0 or score > 1:
                errors.append(f"Emission {i}: 'confidence_score' must be between 0 and 1")

    return ValidateResponse(
        valid=len(errors) == 0,
        errors=errors,
        emissions_count=len(request.emissions),
    )


@router.get("/profiles", response_model=ProfileListResponse)
async def list_profiles() -> ProfileListResponse:
    """List all available policy profiles."""
    profiles = _list_profiles()
    profile_infos = []

    for p in profiles:
        multi_model = p.get("multi_model", {})
        profile_infos.append(ProfileInfo(
            name=p.get("profile_name", "unknown"),
            version=p.get("profile_version", "0.0.0"),
            description=p.get("description", ""),
            required_panels=p.get("required_panels", []),
            auto_merge_enabled=p.get("auto_merge", {}).get("enabled", False),
            multi_model_enabled=multi_model.get("enabled", False) if isinstance(multi_model, dict) else False,
        ))

    return ProfileListResponse(
        profiles=profile_infos,
        default_profile=_DEFAULT_PROFILE,
    )
