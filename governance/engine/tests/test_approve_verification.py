"""Tests for deterministic APPROVE payload verification."""

from __future__ import annotations

import pytest

from governance.engine.orchestrator.approve_verification import (
    VerificationFailure,
    VerificationResult,
    VerificationStatus,
    verify_approve_payload,
)


def _valid_payload(**overrides) -> dict:
    """Build a valid APPROVE payload with optional overrides."""
    base = {
        "test_gate_passed": True,
        "files_reviewed": ["src/main.py", "tests/test_main.py"],
        "acceptance_criteria_met": [
            {"criterion": "Feature X works", "met": True},
            {"criterion": "Tests pass", "met": True},
        ],
        "coverage_percentage": 92,
    }
    base.update(overrides)
    return base


class TestRequiredFields:
    """Tests for required field validation."""

    def test_all_fields_present(self):
        result = verify_approve_payload(
            _valid_payload(),
            diff_files=["src/main.py", "tests/test_main.py"],
        )
        assert "required_fields" in result.checks_passed

    def test_missing_test_gate_passed(self):
        payload = _valid_payload()
        del payload["test_gate_passed"]
        result = verify_approve_payload(payload, diff_files=[])
        assert not result.is_valid
        assert any(f.check == "required_fields" for f in result.failures)

    def test_missing_files_reviewed(self):
        payload = _valid_payload()
        del payload["files_reviewed"]
        result = verify_approve_payload(payload, diff_files=[])
        assert not result.is_valid

    def test_missing_acceptance_criteria(self):
        payload = _valid_payload()
        del payload["acceptance_criteria_met"]
        result = verify_approve_payload(payload, diff_files=[])
        assert not result.is_valid

    def test_missing_coverage(self):
        payload = _valid_payload()
        del payload["coverage_percentage"]
        result = verify_approve_payload(payload, diff_files=[])
        assert not result.is_valid

    def test_missing_multiple_fields(self):
        result = verify_approve_payload({}, diff_files=[])
        assert not result.is_valid
        failures = [f for f in result.failures if f.check == "required_fields"]
        assert len(failures) == 1
        assert "test_gate_passed" in failures[0].description


class TestFilesReviewed:
    """Tests for files_reviewed cross-reference."""

    def test_exact_match(self):
        payload = _valid_payload(files_reviewed=["a.py", "b.py"])
        result = verify_approve_payload(payload, diff_files=["a.py", "b.py"])
        assert "files_reviewed_coverage" in result.checks_passed

    def test_superset_is_valid(self):
        """Reviewing more files than in diff is acceptable."""
        payload = _valid_payload(files_reviewed=["a.py", "b.py", "c.py"])
        result = verify_approve_payload(payload, diff_files=["a.py", "b.py"])
        assert "files_reviewed_coverage" in result.checks_passed

    def test_missing_file_fails(self):
        payload = _valid_payload(files_reviewed=["a.py"])
        result = verify_approve_payload(payload, diff_files=["a.py", "b.py"])
        assert not result.is_valid
        failures = [f for f in result.failures if f.check == "files_reviewed_coverage"]
        assert len(failures) == 1
        assert "b.py" in failures[0].description

    def test_empty_diff_passes(self):
        payload = _valid_payload(files_reviewed=[])
        result = verify_approve_payload(payload, diff_files=[])
        assert "files_reviewed_coverage" in result.checks_passed


class TestTestGate:
    """Tests for test_gate_passed validation."""

    def test_matching_ci_status(self):
        payload = _valid_payload(test_gate_passed=True)
        result = verify_approve_payload(
            payload, diff_files=[], ci_test_passed=True
        )
        assert "test_gate_consistency" in result.checks_passed

    def test_mismatch_fails(self):
        payload = _valid_payload(test_gate_passed=True)
        result = verify_approve_payload(
            payload, diff_files=[], ci_test_passed=False
        )
        failures = [f for f in result.failures if f.check == "test_gate_consistency"]
        assert len(failures) == 1

    def test_no_ci_data_passes(self):
        """When CI status is unknown, skip the cross-check."""
        payload = _valid_payload(test_gate_passed=True)
        result = verify_approve_payload(payload, diff_files=[], ci_test_passed=None)
        assert "test_gate_consistency" in result.checks_passed

    def test_non_bool_fails(self):
        payload = _valid_payload(test_gate_passed="yes")
        result = verify_approve_payload(payload, diff_files=[])
        failures = [f for f in result.failures if f.check == "test_gate_type"]
        assert len(failures) == 1


class TestAcceptanceCriteria:
    """Tests for acceptance_criteria_met validation."""

    def test_all_criteria_present(self):
        payload = _valid_payload(
            acceptance_criteria_met=[
                {"criterion": "Feature X works", "met": True},
                {"criterion": "Tests pass", "met": True},
            ]
        )
        result = verify_approve_payload(
            payload,
            diff_files=[],
            issue_acceptance_criteria=["Feature X works", "Tests pass"],
        )
        assert "acceptance_criteria_completeness" in result.checks_passed

    def test_missing_criterion_fails(self):
        payload = _valid_payload(
            acceptance_criteria_met=[
                {"criterion": "Feature X works", "met": True},
            ]
        )
        result = verify_approve_payload(
            payload,
            diff_files=[],
            issue_acceptance_criteria=["Feature X works", "Tests pass"],
        )
        failures = [f for f in result.failures if f.check == "acceptance_criteria_completeness"]
        assert len(failures) == 1

    def test_unmet_criterion_fails(self):
        payload = _valid_payload(
            acceptance_criteria_met=[
                {"criterion": "Feature X works", "met": False},
                {"criterion": "Tests pass", "met": True},
            ]
        )
        result = verify_approve_payload(
            payload,
            diff_files=[],
            issue_acceptance_criteria=["Feature X works", "Tests pass"],
        )
        failures = [f for f in result.failures if f.check == "acceptance_criteria_met_status"]
        assert len(failures) == 1

    def test_no_issue_criteria_skips_check(self):
        """When issue criteria are not provided, skip the completeness check."""
        payload = _valid_payload()
        result = verify_approve_payload(
            payload, diff_files=[], issue_acceptance_criteria=None
        )
        # Should not have acceptance_criteria_completeness in either list
        assert "acceptance_criteria_completeness" not in result.checks_passed
        assert not any(f.check == "acceptance_criteria_completeness" for f in result.failures)

    def test_case_insensitive_matching(self):
        payload = _valid_payload(
            acceptance_criteria_met=[
                {"criterion": "FEATURE X WORKS", "met": True},
            ]
        )
        result = verify_approve_payload(
            payload,
            diff_files=[],
            issue_acceptance_criteria=["Feature X works"],
        )
        assert "acceptance_criteria_completeness" in result.checks_passed

    def test_non_list_type_fails(self):
        payload = _valid_payload(acceptance_criteria_met="not a list")
        result = verify_approve_payload(
            payload,
            diff_files=[],
            issue_acceptance_criteria=["Feature X works"],
        )
        failures = [f for f in result.failures if f.check == "acceptance_criteria_type"]
        assert len(failures) == 1


class TestCoverage:
    """Tests for coverage_percentage validation."""

    def test_above_threshold(self):
        payload = _valid_payload(coverage_percentage=92)
        result = verify_approve_payload(payload, diff_files=[])
        assert "coverage_threshold" in result.checks_passed

    def test_at_threshold(self):
        payload = _valid_payload(coverage_percentage=80)
        result = verify_approve_payload(payload, diff_files=[])
        assert "coverage_threshold" in result.checks_passed

    def test_below_threshold(self):
        payload = _valid_payload(coverage_percentage=75)
        result = verify_approve_payload(payload, diff_files=[])
        failures = [f for f in result.failures if f.check == "coverage_threshold"]
        assert len(failures) == 1

    def test_custom_threshold(self):
        payload = _valid_payload(coverage_percentage=90)
        result = verify_approve_payload(payload, diff_files=[], min_coverage=95.0)
        failures = [f for f in result.failures if f.check == "coverage_threshold"]
        assert len(failures) == 1

    def test_out_of_range_negative(self):
        payload = _valid_payload(coverage_percentage=-5)
        result = verify_approve_payload(payload, diff_files=[])
        failures = [f for f in result.failures if f.check == "coverage_range"]
        assert len(failures) == 1

    def test_out_of_range_over_100(self):
        payload = _valid_payload(coverage_percentage=105)
        result = verify_approve_payload(payload, diff_files=[])
        failures = [f for f in result.failures if f.check == "coverage_range"]
        assert len(failures) == 1

    def test_non_numeric_fails(self):
        payload = _valid_payload(coverage_percentage="high")
        result = verify_approve_payload(payload, diff_files=[])
        failures = [f for f in result.failures if f.check == "coverage_type"]
        assert len(failures) == 1


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_valid_result(self):
        result = verify_approve_payload(
            _valid_payload(),
            diff_files=["src/main.py", "tests/test_main.py"],
        )
        assert result.is_valid
        assert result.status == VerificationStatus.VALID
        assert len(result.failures) == 0

    def test_to_dict(self):
        result = verify_approve_payload(
            _valid_payload(),
            diff_files=["src/main.py", "tests/test_main.py"],
        )
        d = result.to_dict()
        assert d["status"] == "valid"
        assert d["is_valid"] is True
        assert isinstance(d["checks_passed"], list)
        assert isinstance(d["failures"], list)

    def test_invalid_result_to_dict(self):
        result = verify_approve_payload({}, diff_files=[])
        d = result.to_dict()
        assert d["status"] == "invalid"
        assert d["is_valid"] is False
        assert len(d["failures"]) > 0


class TestFullPayloadValidation:
    """End-to-end tests for complete payload validation."""

    def test_fully_valid_payload(self):
        payload = {
            "test_gate_passed": True,
            "files_reviewed": ["src/app.py", "tests/test_app.py", "README.md"],
            "acceptance_criteria_met": [
                {"criterion": "App starts correctly", "met": True},
                {"criterion": "All tests pass", "met": True},
                {"criterion": "Documentation updated", "met": True},
            ],
            "coverage_percentage": 87,
        }
        result = verify_approve_payload(
            payload,
            diff_files=["src/app.py", "tests/test_app.py", "README.md"],
            issue_acceptance_criteria=[
                "App starts correctly",
                "All tests pass",
                "Documentation updated",
            ],
            ci_test_passed=True,
        )
        assert result.is_valid
        assert len(result.failures) == 0
        assert len(result.checks_passed) >= 5

    def test_multiple_failures(self):
        payload = {
            "test_gate_passed": "yes",  # Wrong type
            "files_reviewed": [],  # Missing files
            "acceptance_criteria_met": [],  # Missing criteria
            "coverage_percentage": 50,  # Below threshold
        }
        result = verify_approve_payload(
            payload,
            diff_files=["a.py", "b.py"],
            issue_acceptance_criteria=["Feature works"],
            ci_test_passed=True,
        )
        assert not result.is_valid
        assert len(result.failures) >= 3
