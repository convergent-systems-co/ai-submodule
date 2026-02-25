"""Structural integrity tests for personas, panels, prompts, and profiles."""

import json
import re
from pathlib import Path

import pytest
import yaml

from conftest import REPO_ROOT


GOVERNANCE_DIR = REPO_ROOT / "governance"
PERSONAS_DIR = GOVERNANCE_DIR / "personas"
PANELS_DIR = PERSONAS_DIR / "panels"
SCHEMAS_DIR = GOVERNANCE_DIR / "schemas"
PROMPTS_DIR = GOVERNANCE_DIR / "prompts"
POLICY_DIR = GOVERNANCE_DIR / "policy"


# ===========================================================================
# Persona files
# ===========================================================================


class TestPersonaFiles:
    # Panel files (panels/) use different sections (Purpose/Participants),
    # so we only check individual persona files (category/persona.md), not panels.
    PANEL_CATEGORIES = {"panels"}

    @pytest.fixture
    def persona_index_entries(self):
        """Parse persona file references from index.md, excluding panel files."""
        index_path = PERSONAS_DIR / "index.md"
        content = index_path.read_text()
        # Match patterns like `quality/style-reviewer.md`
        matches = re.findall(r'`([a-z-]+/[a-z-]+\.md)`', content)
        # Exclude panel entries — they have different structure
        return [m for m in matches if m.split("/")[0] not in self.PANEL_CATEGORIES]

    def test_all_persona_files_exist(self, persona_index_entries):
        """Every persona referenced in index.md must have a corresponding file."""
        missing = []
        for ref in persona_index_entries:
            path = PERSONAS_DIR / ref
            if not path.exists():
                missing.append(ref)
        assert not missing, f"Missing persona files: {missing}"

    def test_persona_files_have_required_sections(self, persona_index_entries):
        """Each persona markdown must contain Role, Evaluate For, Output Format."""
        required_sections = ["## Role", "## Evaluate For", "## Output Format"]
        failures = []
        for ref in persona_index_entries:
            path = PERSONAS_DIR / ref
            if not path.exists():
                continue
            content = path.read_text()
            for section in required_sections:
                if section not in content:
                    failures.append(f"{ref} missing '{section}'")
        assert not failures, f"Section failures:\n" + "\n".join(failures)


# ===========================================================================
# Panel definitions
# ===========================================================================


class TestPanelDefinitions:
    def test_panel_definitions_exist(self):
        """Every file in governance/personas/panels/ must be a valid markdown file."""
        panel_files = sorted(PANELS_DIR.glob("*.md"))
        assert len(panel_files) > 0, "No panel definitions found"
        for fpath in panel_files:
            content = fpath.read_text()
            assert len(content) > 50, f"{fpath.name} is too short to be a valid panel definition"

    def test_required_panels_have_definitions(self):
        """Every panel name in each profile's required_panels has a panel definition."""
        evaluation_profiles = ["default.yaml", "fin_pii_high.yaml", "infrastructure_critical.yaml", "reduced_touchpoint.yaml"]
        panel_files = {p.stem for p in PANELS_DIR.glob("*.md")}

        missing = []
        for profile_name in evaluation_profiles:
            path = POLICY_DIR / profile_name
            with open(path) as f:
                profile = yaml.safe_load(f)
            for panel in profile.get("required_panels", []):
                if panel not in panel_files:
                    missing.append(f"{profile_name}: {panel}")

        assert not missing, f"Missing panel definitions for required panels: {missing}"


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
        assert (PROMPTS_DIR / "templates" / "plan-template.md").exists()


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
