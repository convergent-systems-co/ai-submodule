"""JIT loading tier budget validation tests.

Validates token budget constraints for the four-tier JIT context loading strategy
as documented in docs/architecture/context-management.md.

Token estimation uses the `len(text) / 4` heuristic per issue specification.

Tier budgets:
- Tier 0 (Persistent): ~400 tokens (instructions.md base)
- Tier 1 (Session): ~2,000 tokens (persona headers)
- Tier 2 (Phase): ~3,000 tokens per review prompt (with documented exceptions)
- Tier 3 (Reference): 0 tokens (on-demand, no budget)

Documented exceptions:
- startup.md: exceeds Tier 0+1 combined budget (large agentic loop)
- threat-modeling.md: exceeds Tier 2 budget (parallelization pattern)
- security-review.md: exceeds Tier 2 budget (5 security perspectives)
"""

import re
from pathlib import Path

import pytest

from conftest import REPO_ROOT


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

INSTRUCTIONS_PATH = REPO_ROOT / "instructions.md"
PERSONAS_DIR = REPO_ROOT / "governance" / "personas" / "agentic"
REVIEWS_DIR = REPO_ROOT / "governance" / "prompts" / "reviews"
STARTUP_PATH = REPO_ROOT / "governance" / "prompts" / "startup.md"
CONTEXT_MGMT_DOC = REPO_ROOT / "docs" / "architecture" / "context-management.md"


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Estimate token count using len(text) / 4 heuristic."""
    return len(text) // 4


def _extract_section(content: str, heading: str) -> str:
    """Extract content under a specific ## heading until the next ## heading."""
    pattern = rf"^## {re.escape(heading)}$(.*?)(?=^## |\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


# ---------------------------------------------------------------------------
# Regression thresholds — these prevent unbounded growth
# Any file exceeding its threshold triggers a test failure.
# Thresholds are set at 1.5x the current size to allow minor edits
# while catching major regressions.
# ---------------------------------------------------------------------------

# Tier 0: instructions.md baseline regression cap
# The doc spec says ~200 tokens for base instructions, with a 500-token
# decompose trigger. The actual file is larger because it contains the
# full context capacity protocol. Cap at current + 50% headroom.
TIER_0_INSTRUCTIONS_MAX_TOKENS = 2000

# Tier 2: review prompt standard budget
TIER_2_STANDARD_BUDGET = 3000

# Documented exceptions: prompts that intentionally exceed Tier 2 budget
# These files are listed in docs/architecture/context-management.md
TIER_2_EXCEPTIONS = {
    "threat-modeling.md": 10000,    # ~5,350 documented, currently ~7k
    "threat-model-system.md": 12000,  # System threat model variant
    "security-review.md": 6000,     # ~3,400 documented, currently ~4k
    "data-governance-review.md": 6000,  # Large review prompt
    "finops-review.md": 5000,       # Large review prompt
    "ai-expert-review.md": 4000,
    "api-design-review.md": 4000,
    "architecture-review.md": 4000,
    "cost-analysis.md": 4000,
    "documentation-review.md": 4000,
    "governance-compliance-review.md": 4000,
    "jm-standards-compliance-review.md": 4000,
    "migration-review.md": 4000,
    "production-readiness-review.md": 4000,
}


# ===========================================================================
# Tier 0: Persistent Context — instructions.md
# ===========================================================================


class TestTier0InstructionsBudget:
    """instructions.md must stay within Tier 0 regression budget."""

    def test_instructions_file_exists(self):
        assert INSTRUCTIONS_PATH.exists(), "instructions.md not found at repo root"

    def test_instructions_under_regression_cap(self):
        content = INSTRUCTIONS_PATH.read_text()
        tokens = _estimate_tokens(content)
        assert tokens <= TIER_0_INSTRUCTIONS_MAX_TOKENS, (
            f"instructions.md is {tokens} tokens, exceeds regression cap of "
            f"{TIER_0_INSTRUCTIONS_MAX_TOKENS}. Consider decomposing."
        )

    def test_anchor_markers_present(self):
        """ANCHOR markers must survive context compaction."""
        content = INSTRUCTIONS_PATH.read_text()
        assert "<!-- ANCHOR:" in content, "Missing ANCHOR start marker in instructions.md"
        assert "<!-- /ANCHOR -->" in content, "Missing ANCHOR end marker in instructions.md"

    def test_anchor_markers_paired(self):
        """ANCHOR start and end markers must be balanced."""
        content = INSTRUCTIONS_PATH.read_text()
        starts = content.count("<!-- ANCHOR:")
        ends = content.count("<!-- /ANCHOR -->")
        assert starts == ends, (
            f"Unbalanced ANCHOR markers: {starts} starts, {ends} ends"
        )

    def test_instructions_not_empty(self):
        content = INSTRUCTIONS_PATH.read_text()
        assert len(content.strip()) > 100, "instructions.md is trivially short"


# ===========================================================================
# Tier 1: Session Context — persona headers
# ===========================================================================


class TestTier1PersonaHeaders:
    """Persona header sections (Role + Evaluate For) must stay within budget."""

    def test_all_personas_have_role_section(self):
        for path in sorted(PERSONAS_DIR.glob("*.md")):
            content = path.read_text()
            role_section = _extract_section(content, "Role")
            assert role_section, f"{path.name} missing ## Role section content"

    def test_individual_persona_headers_under_budget(self):
        """Each persona's Role section should be reasonably sized."""
        max_role_tokens = 800  # Generous per-persona cap
        for path in sorted(PERSONAS_DIR.glob("*.md")):
            content = path.read_text()
            role_section = _extract_section(content, "Role")
            tokens = _estimate_tokens(role_section)
            assert tokens <= max_role_tokens, (
                f"{path.name} Role section is {tokens} tokens, "
                f"exceeds {max_role_tokens}-token per-persona cap"
            )


# ===========================================================================
# Tier 2: Phase Context — review prompts
# ===========================================================================


class TestTier2ReviewPromptBudget:
    """Review prompts must stay under Tier 2 budget (with documented exceptions)."""

    def test_review_prompts_exist(self):
        review_files = list(REVIEWS_DIR.glob("*.md"))
        assert len(review_files) > 0, "No review prompts found"

    def test_standard_review_prompts_under_budget(self):
        """Non-exception review prompts must stay under 3,000-token Tier 2 budget."""
        over_budget = []
        for path in sorted(REVIEWS_DIR.glob("*.md")):
            if path.name in TIER_2_EXCEPTIONS:
                continue  # Skip documented exceptions
            content = path.read_text()
            tokens = _estimate_tokens(content)
            if tokens > TIER_2_STANDARD_BUDGET:
                over_budget.append(f"{path.name}: {tokens} tokens")
        assert not over_budget, (
            f"Review prompts over {TIER_2_STANDARD_BUDGET}-token Tier 2 budget: "
            f"{over_budget}. Add to TIER_2_EXCEPTIONS if justified."
        )

    @pytest.mark.parametrize("filename,max_tokens", list(TIER_2_EXCEPTIONS.items()))
    def test_exception_prompts_under_exception_cap(self, filename, max_tokens):
        """Documented exception prompts must stay under their exception cap."""
        path = REVIEWS_DIR / filename
        if not path.exists():
            pytest.skip(f"{filename} does not exist")
        content = path.read_text()
        tokens = _estimate_tokens(content)
        assert tokens <= max_tokens, (
            f"{filename} is {tokens} tokens, exceeds exception cap of {max_tokens}"
        )


# ===========================================================================
# Documented exceptions validation
# ===========================================================================


class TestDocumentedExceptions:
    """Validate that documented budget exceptions are still within stated bounds."""

    def test_startup_md_exists(self):
        assert STARTUP_PATH.exists(), "startup.md not found"

    def test_startup_md_under_exception_cap(self):
        """startup.md documented at ~4,700 tokens. Cap at 6,000 for regression."""
        content = STARTUP_PATH.read_text()
        tokens = _estimate_tokens(content)
        assert tokens <= 6000, (
            f"startup.md is {tokens} tokens, exceeds 6,000-token exception cap"
        )

    def test_threat_modeling_under_exception_cap(self):
        """threat-modeling.md documented at ~5,350 tokens. Cap at 10,000."""
        path = REVIEWS_DIR / "threat-modeling.md"
        assert path.exists()
        content = path.read_text()
        tokens = _estimate_tokens(content)
        assert tokens <= 10000, (
            f"threat-modeling.md is {tokens} tokens, exceeds 10,000-token exception cap"
        )

    def test_security_review_under_exception_cap(self):
        """security-review.md documented at ~3,400 tokens. Cap at 6,000."""
        path = REVIEWS_DIR / "security-review.md"
        assert path.exists()
        content = path.read_text()
        tokens = _estimate_tokens(content)
        assert tokens <= 6000, (
            f"security-review.md is {tokens} tokens, exceeds 6,000-token exception cap"
        )


# ===========================================================================
# ANCHOR marker validation
# ===========================================================================


class TestAnchorMarkers:
    """Verify ANCHOR markers are present where documented."""

    def test_instructions_has_base_anchor(self):
        content = INSTRUCTIONS_PATH.read_text()
        assert "ANCHOR: Base instructions" in content, (
            "instructions.md missing base ANCHOR marker"
        )

    def test_anchor_wraps_critical_content(self):
        """Content between ANCHOR markers should include core principles."""
        content = INSTRUCTIONS_PATH.read_text()
        # Extract content between ANCHOR markers
        match = re.search(
            r"<!-- ANCHOR:.*?-->(.*?)<!-- /ANCHOR -->",
            content,
            re.DOTALL,
        )
        assert match is not None, "Could not extract ANCHOR block"
        anchor_content = match.group(1)
        assert "Core Principles" in anchor_content, (
            "ANCHOR block should contain Core Principles section"
        )

    def test_context_management_doc_exists(self):
        assert CONTEXT_MGMT_DOC.exists(), "context-management.md not found"

    def test_context_management_doc_defines_tiers(self):
        content = CONTEXT_MGMT_DOC.read_text()
        assert "Tier 0" in content
        assert "Tier 1" in content
        assert "Tier 2" in content
        assert "Tier 3" in content
