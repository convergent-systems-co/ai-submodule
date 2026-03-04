"""Validate all persona .md files have required structural sections.

Every agentic persona must contain:
- ## Role
- ## Responsibilities
- ## Constraints OR ## Containment Policy (the actual section name in the codebase)

Additional structural checks:
- Non-empty content
- H1 heading matches expected format
- Persona count matches expected
"""

import re
from pathlib import Path

import pytest

from conftest import REPO_ROOT


PERSONAS_DIR = REPO_ROOT / "governance" / "personas" / "agentic"

EXPECTED_PERSONAS = [
    "coder.md",
    "devops-engineer.md",
    "document-writer.md",
    "documentation-reviewer.md",
    "iac-engineer.md",
    "project-manager.md",
    "tech-lead.md",
    "test-evaluator.md",
    "test-writer.md",
]

# Required sections — every persona must have these
# Note: the codebase uses "Containment Policy" rather than "Constraints"
REQUIRED_SECTIONS = {"Role", "Responsibilities"}
CONSTRAINT_SECTIONS = {"Constraints", "Containment Policy"}


class TestPersonaFilesExist:
    """All 9 agentic persona files must exist."""

    def test_agentic_directory_exists(self):
        assert PERSONAS_DIR.exists(), "governance/personas/agentic/ directory missing"

    @pytest.mark.parametrize("filename", EXPECTED_PERSONAS)
    def test_persona_file_exists(self, filename):
        path = PERSONAS_DIR / filename
        assert path.exists(), f"Missing agentic persona: {filename}"

    def test_persona_count(self):
        actual = sorted(f.name for f in PERSONAS_DIR.glob("*.md"))
        assert actual == sorted(EXPECTED_PERSONAS), (
            f"Expected {len(EXPECTED_PERSONAS)} personas, found {len(actual)}: {actual}"
        )


class TestPersonaRequiredSections:
    """Each persona file must contain the required ## sections."""

    @pytest.fixture(params=EXPECTED_PERSONAS)
    def persona_content(self, request):
        path = PERSONAS_DIR / request.param
        return request.param, path.read_text()

    def _extract_h2_sections(self, content: str) -> set[str]:
        return {m.group(1) for m in re.finditer(r"^## (.+)$", content, re.MULTILINE)}

    def test_has_role_section(self, persona_content):
        filename, content = persona_content
        sections = self._extract_h2_sections(content)
        assert "Role" in sections, f"{filename} missing ## Role section"

    def test_has_responsibilities_section(self, persona_content):
        filename, content = persona_content
        sections = self._extract_h2_sections(content)
        assert "Responsibilities" in sections, f"{filename} missing ## Responsibilities section"

    def test_has_containment_or_constraints_section(self, persona_content):
        filename, content = persona_content
        sections = self._extract_h2_sections(content)
        has_constraint = bool(sections & CONSTRAINT_SECTIONS)
        assert has_constraint, (
            f"{filename} missing ## Constraints or ## Containment Policy section. "
            f"Found sections: {sorted(sections)}"
        )

    def test_has_h1_heading(self, persona_content):
        filename, content = persona_content
        lines = content.strip().split("\n")
        assert lines[0].startswith("# "), f"{filename} must start with an H1 heading"

    def test_content_not_trivially_short(self, persona_content):
        filename, content = persona_content
        assert len(content) > 200, f"{filename} is too short ({len(content)} chars)"

    def test_has_evaluate_for_section(self, persona_content):
        """Most personas define what they evaluate for."""
        filename, content = persona_content
        sections = self._extract_h2_sections(content)
        assert "Evaluate For" in sections, (
            f"{filename} missing ## Evaluate For section"
        )


class TestPersonaDirectoryStructure:
    """Only the agentic/ subdirectory should exist under personas/."""

    def test_no_deprecated_persona_dirs(self):
        personas_root = REPO_ROOT / "governance" / "personas"
        subdirs = sorted(d.name for d in personas_root.iterdir() if d.is_dir())
        assert subdirs == ["agentic"], f"Unexpected persona directories: {subdirs}"
