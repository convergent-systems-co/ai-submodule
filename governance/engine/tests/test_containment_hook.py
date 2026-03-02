"""Tests for governance.engine.containment_hook — mechanical containment enforcement."""

import pytest

from governance.engine.containment_hook import ContainmentHook, Violation


@pytest.fixture
def hook():
    return ContainmentHook()


# ---------------------------------------------------------------------------
# Persona detection
# ---------------------------------------------------------------------------

class TestPersonaDetection:
    def test_coder_branch(self, hook):
        assert hook.detect_persona("itsfwcp/coder/42/fix-bug") == "coder"

    def test_iac_engineer_branch(self, hook):
        assert hook.detect_persona("itsfwcp/iac-engineer/42/add-infra") == "iac-engineer"

    def test_tester_branch(self, hook):
        assert hook.detect_persona("itsfwcp/tester/42/add-tests") == "tester"

    def test_code_manager_branch(self, hook):
        # Code managers are not restricted by the mechanical hook
        assert hook.detect_persona("itsfwcp/feat/42/some-feature") is None

    def test_main_branch(self, hook):
        assert hook.detect_persona("main") is None

    def test_arbitrary_branch(self, hook):
        assert hook.detect_persona("feature/some-thing") is None


# ---------------------------------------------------------------------------
# Coder restrictions
# ---------------------------------------------------------------------------

class TestCoderRestrictions:
    def test_coder_blocked_from_policy(self, hook):
        violations = hook.check(
            branch="itsfwcp/coder/42/fix-bug",
            changed_files=["governance/policy/default.yaml"],
        )
        assert len(violations) >= 1
        assert violations[0].persona == "coder"

    def test_coder_blocked_from_schemas(self, hook):
        violations = hook.check(
            branch="itsfwcp/coder/42/fix-bug",
            changed_files=["governance/schemas/panel-output.schema.json"],
        )
        assert len(violations) >= 1

    def test_coder_blocked_from_personas(self, hook):
        violations = hook.check(
            branch="itsfwcp/coder/42/fix-bug",
            changed_files=["governance/personas/agentic/coder.md"],
        )
        assert len(violations) >= 1

    def test_coder_blocked_from_review_prompts(self, hook):
        violations = hook.check(
            branch="itsfwcp/coder/42/fix-bug",
            changed_files=["governance/prompts/reviews/code-review.md"],
        )
        assert len(violations) >= 1

    def test_coder_allowed_src(self, hook):
        violations = hook.check(
            branch="itsfwcp/coder/42/fix-bug",
            changed_files=["src/main.py"],
        )
        assert len(violations) == 0

    def test_coder_allowed_tests(self, hook):
        violations = hook.check(
            branch="itsfwcp/coder/42/fix-bug",
            changed_files=["tests/test_main.py"],
        )
        assert len(violations) == 0


# ---------------------------------------------------------------------------
# IaC Engineer restrictions
# ---------------------------------------------------------------------------

class TestIaCEngineerRestrictions:
    def test_iac_blocked_from_policy(self, hook):
        violations = hook.check(
            branch="itsfwcp/iac-engineer/42/add-infra",
            changed_files=["governance/policy/default.yaml"],
        )
        assert len(violations) >= 1

    def test_iac_allowed_infra(self, hook):
        violations = hook.check(
            branch="itsfwcp/iac-engineer/42/add-infra",
            changed_files=["infra/main.bicep"],
        )
        assert len(violations) == 0


# ---------------------------------------------------------------------------
# Universal restrictions
# ---------------------------------------------------------------------------

class TestUniversalRestrictions:
    def test_jm_compliance_blocked_all_branches(self, hook):
        violations = hook.check(
            branch="itsfwcp/feat/42/feature",
            changed_files=["jm-compliance.yml"],
        )
        assert len(violations) >= 1
        assert violations[0].persona == "any"

    def test_jm_compliance_blocked_coder(self, hook):
        violations = hook.check(
            branch="itsfwcp/coder/42/fix-bug",
            changed_files=["jm-compliance.yml"],
        )
        assert len(violations) >= 1


# ---------------------------------------------------------------------------
# Non-restricted branches
# ---------------------------------------------------------------------------

class TestNonRestrictedBranches:
    def test_feature_branch_allowed_policy(self, hook):
        violations = hook.check(
            branch="itsfwcp/feat/42/feature",
            changed_files=["governance/policy/default.yaml"],
        )
        # Only jm-compliance is universally restricted
        assert len(violations) == 0

    def test_main_allowed_policy(self, hook):
        violations = hook.check(
            branch="main",
            changed_files=["governance/policy/default.yaml"],
        )
        assert len(violations) == 0


# ---------------------------------------------------------------------------
# Multiple files
# ---------------------------------------------------------------------------

class TestMultipleFiles:
    def test_mixed_allowed_and_denied(self, hook):
        violations = hook.check(
            branch="itsfwcp/coder/42/fix-bug",
            changed_files=[
                "src/main.py",
                "governance/policy/default.yaml",
                "tests/test_main.py",
            ],
        )
        assert len(violations) == 1
        assert violations[0].file_path == "governance/policy/default.yaml"

    def test_multiple_violations(self, hook):
        violations = hook.check(
            branch="itsfwcp/coder/42/fix-bug",
            changed_files=[
                "governance/policy/default.yaml",
                "governance/schemas/panel-output.schema.json",
            ],
        )
        assert len(violations) == 2


# ---------------------------------------------------------------------------
# Violation structure
# ---------------------------------------------------------------------------

class TestViolationStructure:
    def test_violation_to_dict(self):
        v = Violation(
            file_path="governance/policy/default.yaml",
            persona="coder",
            restricted_pattern="governance/policy/**",
            message="Denied",
        )
        d = v.to_dict()
        assert d["file_path"] == "governance/policy/default.yaml"
        assert d["persona"] == "coder"

    def test_format_violations(self, hook):
        violations = hook.check(
            branch="itsfwcp/coder/42/fix-bug",
            changed_files=["governance/policy/default.yaml"],
        )
        report = hook.format_violations(violations)
        assert "CONTAINMENT VIOLATION" in report
        assert "governance/policy/default.yaml" in report

    def test_format_no_violations(self, hook):
        report = hook.format_violations([])
        assert "No containment violations" in report
