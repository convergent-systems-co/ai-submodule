"""Structural integrity tests for review prompts, agentic personas, and profiles."""

import json
import re
from pathlib import Path

import pytest
import yaml

from conftest import REPO_ROOT


GOVERNANCE_DIR = REPO_ROOT / "governance"
PERSONAS_DIR = GOVERNANCE_DIR / "personas"
REVIEWS_DIR = GOVERNANCE_DIR / "prompts" / "reviews"
SCHEMAS_DIR = GOVERNANCE_DIR / "schemas"
PROMPTS_DIR = GOVERNANCE_DIR / "prompts"
POLICY_DIR = GOVERNANCE_DIR / "policy"
EMISSIONS_DIR = GOVERNANCE_DIR / "emissions"


# ===========================================================================
# Agentic persona files
# ===========================================================================


class TestAgenticPersonaFiles:
    EXPECTED_AGENTIC = [
        "tech-lead.md",
        "coder.md",
        "devops-engineer.md",
        "iac-engineer.md",
        "test-evaluator.md",
        "test-writer.md",
        "document-writer.md",
        "documentation-reviewer.md",
        "project-manager.md",
    ]

    def test_agentic_personas_exist(self):
        """All 9 agentic persona files must exist."""
        agentic_dir = PERSONAS_DIR / "agentic"
        assert agentic_dir.exists(), "governance/personas/agentic/ directory missing"
        for name in self.EXPECTED_AGENTIC:
            path = agentic_dir / name
            assert path.exists(), f"Missing agentic persona: {name}"

    def test_no_deprecated_persona_dirs(self):
        """Only agentic/ should remain under governance/personas/."""
        subdirs = sorted([d.name for d in PERSONAS_DIR.iterdir() if d.is_dir()])
        assert subdirs == ["agentic"], f"Unexpected persona directories: {subdirs}"


# ===========================================================================
# Consolidated review prompts
# ===========================================================================


class TestReviewPrompts:
    def test_review_prompts_exist(self):
        """Every file in governance/prompts/reviews/ must be a valid markdown file."""
        review_files = sorted(REVIEWS_DIR.glob("*.md"))
        assert len(review_files) > 0, "No review prompts found"
        for fpath in review_files:
            content = fpath.read_text()
            assert len(content) > 50, f"{fpath.name} is too short to be a valid review prompt"

    def test_required_panels_have_review_prompts(self):
        """Every panel name in each profile's required_panels has a review prompt."""
        evaluation_profiles = ["default.yaml", "fin_pii_high.yaml", "infrastructure_critical.yaml", "reduced_touchpoint.yaml"]
        review_files = {p.stem for p in REVIEWS_DIR.glob("*.md")}

        missing = []
        for profile_name in evaluation_profiles:
            path = POLICY_DIR / profile_name
            with open(path) as f:
                profile = yaml.safe_load(f)
            for panel in profile.get("required_panels", []):
                if panel not in review_files:
                    missing.append(f"{profile_name}: {panel}")

        assert not missing, f"Missing review prompts for required panels: {missing}"

    def test_review_prompts_have_baseline_emissions(self):
        """Every review prompt must have a corresponding baseline emission JSON file."""
        review_names = {p.stem for p in REVIEWS_DIR.glob("*.md")}
        emission_names = {p.stem for p in EMISSIONS_DIR.glob("*.json")}
        missing = sorted(review_names - emission_names)
        assert not missing, (
            f"Review prompt(s) missing baseline emission in governance/emissions/: {missing}"
        )

    def test_baseline_emission_panel_name_matches_filename(self):
        """Each baseline emission's panel_name field must match its filename."""
        mismatches = []
        for fpath in sorted(EMISSIONS_DIR.glob("*.json")):
            with open(fpath) as f:
                data = json.load(f)
            expected = fpath.stem
            actual = data.get("panel_name", "")
            if actual != expected:
                mismatches.append(f"{fpath.name}: panel_name={actual!r}, expected={expected!r}")
        assert not mismatches, "Baseline emission panel_name mismatches:\n" + "\n".join(mismatches)


# ===========================================================================
# Schema files
# ===========================================================================


class TestSchemaIntegrity:
    def test_panel_schema_exists(self):
        path = SCHEMAS_DIR / "panel-output.schema.json"
        assert path.exists()
        with open(path) as f:
            schema = json.load(f)
        assert "$schema" in schema

    def test_run_manifest_schema_exists(self):
        path = SCHEMAS_DIR / "run-manifest.schema.json"
        assert path.exists()
        with open(path) as f:
            schema = json.load(f)
        assert "$schema" in schema


# ===========================================================================
# Prompt files
# ===========================================================================


class TestPromptFiles:
    def test_startup_prompt_exists(self):
        assert (PROMPTS_DIR / "startup.md").exists()

    def test_plan_template_exists(self):
        templates_dir = GOVERNANCE_DIR / "templates" / "prompts"
        assert (templates_dir / "plan-template.md").exists()


# ===========================================================================
# Policy profile structure
# ===========================================================================


class TestPolicyProfileStructure:
    EVALUATION_PROFILES = ["default.yaml", "fin_pii_high.yaml", "infrastructure_critical.yaml", "reduced_touchpoint.yaml"]
    REQUIRED_FIELDS = {"profile_name", "profile_version", "weighting", "required_panels", "escalation", "auto_merge"}

    def test_profiles_have_required_fields(self):
        failures = []
        for name in self.EVALUATION_PROFILES:
            path = POLICY_DIR / name
            with open(path) as f:
                profile = yaml.safe_load(f)
            missing = self.REQUIRED_FIELDS - set(profile.keys())
            if missing:
                failures.append(f"{name}: missing {missing}")
        assert not failures, "\n".join(failures)

    def test_profiles_have_weighting_weights(self):
        """Each profile's weighting section must have a weights dict."""
        for name in self.EVALUATION_PROFILES:
            path = POLICY_DIR / name
            with open(path) as f:
                profile = yaml.safe_load(f)
            weights = profile.get("weighting", {}).get("weights", {})
            assert isinstance(weights, dict), f"{name} has no weighting.weights"
            assert len(weights) > 0, f"{name} has empty weighting.weights"

    def test_profiles_required_panels_not_empty(self):
        for name in self.EVALUATION_PROFILES:
            path = POLICY_DIR / name
            with open(path) as f:
                profile = yaml.safe_load(f)
            panels = profile.get("required_panels", [])
            assert len(panels) > 0, f"{name} has no required_panels"
