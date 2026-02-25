"""Shared pytest fixtures for Dark Factory Governance tests."""

import io
import json
import sys
from pathlib import Path

import pytest
import yaml

# Ensure the policy engine module is importable
REPO_ROOT = Path(__file__).resolve().parent.parent
GOVERNANCE_DIR = REPO_ROOT / "governance" / "bin"
sys.path.insert(0, str(GOVERNANCE_DIR))

# Re-export after path setup so tests can import the engine
from importlib import import_module

_engine_path = GOVERNANCE_DIR / "policy-engine.py"
# Python can't import filenames with hyphens directly; use importlib
import importlib.util

_spec = importlib.util.spec_from_file_location("policy_engine", _engine_path)
policy_engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(policy_engine)


# ---------------------------------------------------------------------------
# Path fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def governance_root():
    return REPO_ROOT / "governance"


@pytest.fixture
def schemas_dir(governance_root):
    return governance_root / "schemas"


@pytest.fixture
def emissions_dir(governance_root):
    return governance_root / "emissions"


@pytest.fixture
def policy_dir(governance_root):
    return governance_root / "policy"


@pytest.fixture
def personas_dir(governance_root):
    return governance_root / "personas"


# ---------------------------------------------------------------------------
# Schema fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def panel_schema(schemas_dir):
    with open(schemas_dir / "panel-output.schema.json") as f:
        return json.load(f)


@pytest.fixture
def manifest_schema(schemas_dir):
    with open(schemas_dir / "run-manifest.schema.json") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Profile fixtures
# ---------------------------------------------------------------------------

def _load_profile(name):
    path = REPO_ROOT / "governance" / "policy" / f"{name}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def default_profile():
    return _load_profile("default")


@pytest.fixture
def fin_pii_high_profile():
    return _load_profile("fin_pii_high")


@pytest.fixture
def infrastructure_profile():
    return _load_profile("infrastructure_critical")


@pytest.fixture
def reduced_touchpoint_profile():
    return _load_profile("reduced_touchpoint")


# ---------------------------------------------------------------------------
# Emission builder
# ---------------------------------------------------------------------------

def make_emission(
    panel_name="code-review",
    confidence_score=0.90,
    risk_level="low",
    compliance_score=1.0,
    policy_flags=None,
    requires_human_review=False,
    aggregate_verdict="approve",
    findings=None,
    **overrides,
):
    """Factory that builds a valid panel emission dict with sensible defaults."""
    emission = {
        "panel_name": panel_name,
        "panel_version": "1.0.0",
        "confidence_score": confidence_score,
        "risk_level": risk_level,
        "compliance_score": compliance_score,
        "policy_flags": policy_flags if policy_flags is not None else [],
        "requires_human_review": requires_human_review,
        "timestamp": "2026-02-25T12:00:00Z",
        "findings": findings or [
            {
                "persona": "quality/code-reviewer",
                "verdict": "approve",
                "confidence": confidence_score,
                "rationale": f"Test finding for {panel_name}.",
            }
        ],
        "aggregate_verdict": aggregate_verdict,
    }
    emission.update(overrides)
    return emission


# ---------------------------------------------------------------------------
# Required emissions builder
# ---------------------------------------------------------------------------

DEFAULT_REQUIRED_PANELS = [
    "code-review",
    "security-review",
    "threat-modeling",
    "cost-analysis",
    "documentation-review",
    "data-governance-review",
]


def all_required_emissions(
    confidence=0.90,
    risk_level="low",
    panels=None,
    **overrides,
):
    """Generate emissions for all 6 default required panels."""
    panel_list = panels or DEFAULT_REQUIRED_PANELS
    return [
        make_emission(
            panel_name=p,
            confidence_score=confidence,
            risk_level=risk_level,
            **overrides,
        )
        for p in panel_list
    ]


# ---------------------------------------------------------------------------
# Profile builder
# ---------------------------------------------------------------------------

def make_profile(
    profile_name="test-profile",
    weights=None,
    required_panels=None,
    auto_merge_enabled=True,
    auto_merge_conditions=None,
    auto_remediate_enabled=True,
    auto_remediate_conditions=None,
    escalation_rules=None,
    block_conditions=None,
    risk_rules=None,
    missing_panel_behavior="redistribute",
):
    """Build a minimal valid policy profile dict."""
    return {
        "profile_name": profile_name,
        "profile_version": "1.0.0",
        "weighting": {
            "model": "weighted_average",
            "weights": weights or {
                "code-review": 0.20,
                "security-review": 0.20,
                "threat-modeling": 0.15,
                "cost-analysis": 0.15,
                "documentation-review": 0.15,
                "data-governance-review": 0.15,
            },
            "missing_panel_behavior": missing_panel_behavior,
        },
        "risk_aggregation": {
            "model": "highest_severity",
            "rules": risk_rules or [
                {
                    "description": "Any critical → critical",
                    "condition": 'any_panel_risk == "critical"',
                    "result": "critical",
                },
                {
                    "description": "2+ high → high",
                    "condition": 'count(panel_risk == "high") >= 2',
                    "result": "high",
                },
                {
                    "description": "1 high → medium",
                    "condition": 'count(panel_risk == "high") == 1',
                    "result": "medium",
                },
                {
                    "description": "All low/negligible → low",
                    "condition": 'all_panels_risk in ["low", "negligible"]',
                    "result": "low",
                },
            ],
        },
        "escalation": {
            "rules": escalation_rules or [],
        },
        "auto_merge": {
            "enabled": auto_merge_enabled,
            "conditions": auto_merge_conditions or [
                'aggregate_confidence >= 0.85',
                'risk_level in ["low", "negligible"]',
                'no_policy_flags_severity in ["critical", "high"]',
                'all_panel_verdicts in ["approve"]',
                'requires_human_review == false',
                'ci_checks_passed == true',
            ],
        },
        "auto_remediate": {
            "enabled": auto_remediate_enabled,
            "conditions": auto_remediate_conditions or [
                'risk_level in ["low", "medium"]',
                'all_policy_flags.auto_remediable == true',
                'aggregate_confidence >= 0.60',
            ],
        },
        "block": {
            "conditions": block_conditions or [],
        },
        "required_panels": required_panels or DEFAULT_REQUIRED_PANELS,
    }


# ---------------------------------------------------------------------------
# EvaluationLog fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def evaluation_log():
    """Create an EvaluationLog writing to StringIO for capture."""
    return policy_engine.EvaluationLog(stream=io.StringIO())
