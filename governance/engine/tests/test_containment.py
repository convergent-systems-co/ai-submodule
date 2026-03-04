"""Tests for governance.engine.containment — agent containment enforcement."""

import json

import pytest
import yaml

from governance.engine.containment import (
    ContainmentChecker,
    ContainmentResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def containment_policy():
    """Load the real agent-containment.yaml policy."""
    from pathlib import Path
    policy_path = Path(__file__).resolve().parent.parent.parent.parent / "governance" / "policy" / "agent-containment.yaml"
    with open(policy_path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def enforced_checker(containment_policy):
    """Checker with enforced mode (default now)."""
    return ContainmentChecker(containment_policy)


@pytest.fixture
def advisory_checker(containment_policy):
    """Checker with advisory mode for testing."""
    policy = containment_policy.copy()
    policy["enforcement"] = {"mode": "advisory"}
    return ContainmentChecker(policy)


# ---------------------------------------------------------------------------
# Default enforcement mode
# ---------------------------------------------------------------------------

class TestDefaultEnforcementMode:
    def test_default_mode_is_enforced(self, containment_policy):
        assert containment_policy["enforcement"]["mode"] == "enforced"

    def test_checker_reports_enforced(self, enforced_checker):
        assert enforced_checker.mode == "enforced"

    def test_advisory_mode_available(self, advisory_checker):
        assert advisory_checker.mode == "advisory"


# ---------------------------------------------------------------------------
# Enforced mode — path checks
# ---------------------------------------------------------------------------

class TestEnforcedPathChecks:
    def test_coder_blocked_from_policy(self, enforced_checker):
        result = enforced_checker.check_path("coder", "governance/policy/default.yaml")
        assert result.blocked is True
        assert result.allowed is False
        assert result.violation is True

    def test_coder_blocked_from_schemas(self, enforced_checker):
        result = enforced_checker.check_path("coder", "governance/schemas/panel-output.schema.json")
        assert result.blocked is True

    def test_coder_blocked_from_personas(self, enforced_checker):
        result = enforced_checker.check_path("coder", "governance/personas/agentic/coder.md")
        assert result.blocked is True

    def test_coder_blocked_from_jm_compliance(self, enforced_checker):
        result = enforced_checker.check_path("coder", "jm-compliance.yml")
        assert result.blocked is True

    def test_coder_allowed_src(self, enforced_checker):
        result = enforced_checker.check_path("coder", "src/main.py")
        assert result.allowed is True
        assert result.blocked is False
        assert result.violation is False

    def test_iac_blocked_from_policy(self, enforced_checker):
        result = enforced_checker.check_path("iac-engineer", "governance/policy/default.yaml")
        assert result.blocked is True

    def test_iac_allowed_infra(self, enforced_checker):
        result = enforced_checker.check_path("iac-engineer", "infra/main.bicep")
        assert result.allowed is True

    def test_iac_blocked_from_src(self, enforced_checker):
        # Not in allowed_paths
        result = enforced_checker.check_path("iac-engineer", "src/app.py")
        assert result.blocked is True

    def test_test_evaluator_blocked_from_policy(self, enforced_checker):
        result = enforced_checker.check_path("test-evaluator", "governance/policy/default.yaml")
        assert result.blocked is True

    def test_test_writer_allowed_tests(self, enforced_checker):
        result = enforced_checker.check_path("test-writer", "tests/test_main.py")
        assert result.allowed is True

    def test_test_evaluator_blocked_from_src(self, enforced_checker):
        result = enforced_checker.check_path("test-evaluator", "src/main.py")
        assert result.blocked is True

    def test_devops_blocked_from_src(self, enforced_checker):
        result = enforced_checker.check_path("devops-engineer", "src/main.py")
        assert result.blocked is True


# ---------------------------------------------------------------------------
# Advisory mode — path checks
# ---------------------------------------------------------------------------

class TestAdvisoryPathChecks:
    def test_coder_violation_logged_not_blocked(self, advisory_checker):
        result = advisory_checker.check_path("coder", "governance/policy/default.yaml")
        assert result.allowed is True
        assert result.blocked is False
        assert result.violation is True
        assert result.mode == "advisory"

    def test_coder_allowed_src(self, advisory_checker):
        result = advisory_checker.check_path("coder", "src/main.py")
        assert result.allowed is True
        assert result.violation is False


# ---------------------------------------------------------------------------
# Operation checks
# ---------------------------------------------------------------------------

class TestOperationChecks:
    def test_coder_denied_git_push(self, enforced_checker):
        result = enforced_checker.check_operation("coder", "git_push")
        assert result.blocked is True
        assert result.violation is True

    def test_coder_denied_git_merge(self, enforced_checker):
        result = enforced_checker.check_operation("coder", "git_merge")
        assert result.blocked is True

    def test_coder_denied_approve_pr(self, enforced_checker):
        result = enforced_checker.check_operation("coder", "approve_pr")
        assert result.blocked is True

    def test_test_evaluator_denied_modify_source(self, enforced_checker):
        result = enforced_checker.check_operation("test-evaluator", "modify_source_code")
        assert result.blocked is True

    def test_test_evaluator_denied_create_branch(self, enforced_checker):
        result = enforced_checker.check_operation("test-evaluator", "create_branch")
        assert result.blocked is True

    def test_devops_denied_implement_code(self, enforced_checker):
        result = enforced_checker.check_operation("devops-engineer", "implement_code")
        assert result.blocked is True

    def test_tech_lead_denied_approve_own_pr(self, enforced_checker):
        result = enforced_checker.check_operation("tech-lead", "approve_own_pr")
        assert result.blocked is True

    def test_coder_allowed_normal_operation(self, enforced_checker):
        result = enforced_checker.check_operation("coder", "write_code")
        assert result.allowed is True
        assert result.violation is False

    def test_advisory_operation_not_blocked(self, advisory_checker):
        result = advisory_checker.check_operation("coder", "git_push")
        assert result.allowed is True
        assert result.blocked is False
        assert result.violation is True


# ---------------------------------------------------------------------------
# Resource limit checks
# ---------------------------------------------------------------------------

class TestResourceLimits:
    def test_coder_within_file_limit(self, enforced_checker):
        result = enforced_checker.check_resource_limit("coder", "max_files_per_pr", 10)
        assert result.allowed is True
        assert result.violation is False

    def test_coder_exceeds_file_limit(self, enforced_checker):
        result = enforced_checker.check_resource_limit("coder", "max_files_per_pr", 35)
        assert result.blocked is True
        assert result.violation is True

    def test_global_limit_applied(self, enforced_checker):
        # Global max is 50, coder max is 30 — 35 should violate coder limit
        result = enforced_checker.check_resource_limit("coder", "max_files_per_pr", 35)
        assert result.blocked is True

    def test_advisory_limit_not_blocked(self, advisory_checker):
        result = advisory_checker.check_resource_limit("coder", "max_files_per_pr", 35)
        assert result.allowed is True
        assert result.blocked is False
        assert result.violation is True


# ---------------------------------------------------------------------------
# Violation logging
# ---------------------------------------------------------------------------

class TestViolationLogging:
    def test_violations_written_to_file(self, tmp_path, containment_policy):
        log_path = tmp_path / "violations.jsonl"
        checker = ContainmentChecker(containment_policy, violations_log=log_path)
        checker.check_path("coder", "governance/policy/default.yaml")
        assert log_path.exists()
        with open(log_path) as f:
            line = f.readline()
            data = json.loads(line)
        assert data["violation"] is True
        assert data["persona"] == "coder"
        assert "timestamp" in data

    def test_no_log_for_allowed_actions(self, tmp_path, containment_policy):
        log_path = tmp_path / "violations.jsonl"
        checker = ContainmentChecker(containment_policy, violations_log=log_path)
        checker.check_path("coder", "src/main.py")
        assert not log_path.exists()

    def test_multiple_violations_appended(self, tmp_path, containment_policy):
        log_path = tmp_path / "violations.jsonl"
        checker = ContainmentChecker(containment_policy, violations_log=log_path)
        checker.check_path("coder", "governance/policy/default.yaml")
        checker.check_path("coder", "governance/schemas/panel.json")
        with open(log_path) as f:
            lines = [l for l in f if l.strip()]
        assert len(lines) == 2


# ---------------------------------------------------------------------------
# ContainmentResult structure
# ---------------------------------------------------------------------------

class TestContainmentResult:
    def test_to_dict(self):
        result = ContainmentResult(
            allowed=False,
            blocked=True,
            persona="coder",
            action="path_check",
            target="governance/policy/default.yaml",
            reason="Denied",
            mode="enforced",
            violation=True,
        )
        d = result.to_dict()
        assert d["allowed"] is False
        assert d["blocked"] is True
        assert d["persona"] == "coder"
        assert "timestamp" in d
