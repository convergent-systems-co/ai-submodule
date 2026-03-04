"""Deterministic APPROVE payload verification.

Validates Tester APPROVE payloads against independent data sources,
replacing the prompt-based verification in the Team Lead persona.
This is the sole decision authority for whether an APPROVE is structurally
valid before merge proceeds.

Security context: In single-context sessions where Coder and Tester share
the same LLM context, prompt injection is a viable self-approval vector.
Deterministic code verification eliminates this risk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class VerificationStatus(str, Enum):
    """Result of APPROVE verification."""

    VALID = "valid"
    INVALID = "invalid"


@dataclass
class VerificationFailure:
    """A single verification check failure."""

    check: str
    description: str
    expected: str
    actual: str


@dataclass
class VerificationResult:
    """Complete verification result for an APPROVE payload."""

    status: VerificationStatus
    failures: list[VerificationFailure] = field(default_factory=list)
    checks_passed: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.status == VerificationStatus.VALID

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "is_valid": self.is_valid,
            "checks_passed": self.checks_passed,
            "failures": [
                {
                    "check": f.check,
                    "description": f.description,
                    "expected": f.expected,
                    "actual": f.actual,
                }
                for f in self.failures
            ],
        }


# Required fields in an APPROVE payload per agent-protocol.md
_REQUIRED_FIELDS = [
    "test_gate_passed",
    "files_reviewed",
    "acceptance_criteria_met",
    "coverage_percentage",
]


def verify_approve_payload(
    payload: dict,
    diff_files: list[str],
    issue_acceptance_criteria: list[str] | None = None,
    ci_test_passed: bool | None = None,
    min_coverage: float = 80.0,
) -> VerificationResult:
    """Verify an APPROVE payload against independent data sources.

    Args:
        payload: The APPROVE message payload dict from the Tester.
        diff_files: File paths from ``git diff --name-only`` for the PR.
        issue_acceptance_criteria: List of acceptance criterion descriptions
            from the issue body. If None, the acceptance_criteria_met check
            is skipped (but still required to be present).
        ci_test_passed: Whether CI tests passed. If None, the cross-check
            against test_gate_passed is skipped.
        min_coverage: Minimum acceptable coverage percentage (default 80).

    Returns:
        VerificationResult with status and any failures.
    """
    failures: list[VerificationFailure] = []
    checks_passed: list[str] = []

    # 1. Required fields check
    _check_required_fields(payload, failures, checks_passed)

    # If required fields are missing, downstream checks may fail on KeyError.
    # Still run what we can.

    # 2. files_reviewed vs git diff
    if "files_reviewed" in payload:
        _check_files_reviewed(payload["files_reviewed"], diff_files, failures, checks_passed)

    # 3. test_gate_passed consistency
    if "test_gate_passed" in payload:
        _check_test_gate(payload["test_gate_passed"], ci_test_passed, failures, checks_passed)

    # 4. acceptance_criteria_met completeness
    if "acceptance_criteria_met" in payload and issue_acceptance_criteria is not None:
        _check_acceptance_criteria(
            payload["acceptance_criteria_met"],
            issue_acceptance_criteria,
            failures,
            checks_passed,
        )

    # 5. coverage_percentage threshold
    if "coverage_percentage" in payload:
        _check_coverage(payload["coverage_percentage"], min_coverage, failures, checks_passed)

    status = VerificationStatus.VALID if not failures else VerificationStatus.INVALID

    return VerificationResult(
        status=status,
        failures=failures,
        checks_passed=checks_passed,
    )


def _check_required_fields(
    payload: dict,
    failures: list[VerificationFailure],
    checks_passed: list[str],
) -> None:
    """Check that all required fields are present in the payload."""
    missing = [f for f in _REQUIRED_FIELDS if f not in payload]
    if missing:
        failures.append(
            VerificationFailure(
                check="required_fields",
                description=f"Missing required APPROVE fields: {', '.join(missing)}",
                expected=str(_REQUIRED_FIELDS),
                actual=str(list(payload.keys())),
            )
        )
    else:
        checks_passed.append("required_fields")


def _check_files_reviewed(
    files_reviewed: list[str],
    diff_files: list[str],
    failures: list[VerificationFailure],
    checks_passed: list[str],
) -> None:
    """Cross-reference files_reviewed against git diff output."""
    reviewed_set = set(files_reviewed)
    diff_set = set(diff_files)

    # Files in diff but not reviewed
    unreviewed = diff_set - reviewed_set
    if unreviewed:
        failures.append(
            VerificationFailure(
                check="files_reviewed_coverage",
                description=(
                    f"Files in PR diff not listed in files_reviewed: "
                    f"{', '.join(sorted(unreviewed))}"
                ),
                expected=str(sorted(diff_set)),
                actual=str(sorted(reviewed_set)),
            )
        )
    else:
        checks_passed.append("files_reviewed_coverage")


def _check_test_gate(
    test_gate_passed: bool,
    ci_test_passed: bool | None,
    failures: list[VerificationFailure],
    checks_passed: list[str],
) -> None:
    """Validate test_gate_passed against CI status."""
    if not isinstance(test_gate_passed, bool):
        failures.append(
            VerificationFailure(
                check="test_gate_type",
                description="test_gate_passed must be a boolean",
                expected="bool",
                actual=str(type(test_gate_passed).__name__),
            )
        )
        return

    if ci_test_passed is not None and test_gate_passed != ci_test_passed:
        failures.append(
            VerificationFailure(
                check="test_gate_consistency",
                description=(
                    f"test_gate_passed ({test_gate_passed}) does not match "
                    f"CI test status ({ci_test_passed})"
                ),
                expected=str(ci_test_passed),
                actual=str(test_gate_passed),
            )
        )
    else:
        checks_passed.append("test_gate_consistency")


def _check_acceptance_criteria(
    criteria_met: list[dict],
    issue_criteria: list[str],
    failures: list[VerificationFailure],
    checks_passed: list[str],
) -> None:
    """Verify all issue acceptance criteria appear in acceptance_criteria_met."""
    if not isinstance(criteria_met, list):
        failures.append(
            VerificationFailure(
                check="acceptance_criteria_type",
                description="acceptance_criteria_met must be a list",
                expected="list",
                actual=str(type(criteria_met).__name__),
            )
        )
        return

    # Extract criterion descriptions from the payload
    reported_criteria = set()
    for item in criteria_met:
        if isinstance(item, dict) and "criterion" in item:
            reported_criteria.add(item["criterion"].strip().lower())

    # Check each issue criterion is represented
    missing_criteria = []
    for criterion in issue_criteria:
        normalized = criterion.strip().lower()
        if normalized not in reported_criteria:
            missing_criteria.append(criterion)

    if missing_criteria:
        failures.append(
            VerificationFailure(
                check="acceptance_criteria_completeness",
                description=(
                    f"Issue acceptance criteria not present in APPROVE: "
                    f"{', '.join(missing_criteria)}"
                ),
                expected=str(issue_criteria),
                actual=str([c.get("criterion", "") for c in criteria_met if isinstance(c, dict)]),
            )
        )
    else:
        checks_passed.append("acceptance_criteria_completeness")

    # Check for unmet criteria (met: false)
    unmet = [
        item.get("criterion", "unknown")
        for item in criteria_met
        if isinstance(item, dict) and item.get("met") is False
    ]
    if unmet:
        failures.append(
            VerificationFailure(
                check="acceptance_criteria_met_status",
                description=f"Criteria reported as not met: {', '.join(unmet)}",
                expected="all criteria met=true",
                actual=f"{len(unmet)} criteria with met=false",
            )
        )
    else:
        checks_passed.append("acceptance_criteria_met_status")


def _check_coverage(
    coverage_percentage: float | int,
    min_coverage: float,
    failures: list[VerificationFailure],
    checks_passed: list[str],
) -> None:
    """Validate coverage percentage meets minimum threshold."""
    if not isinstance(coverage_percentage, (int, float)):
        failures.append(
            VerificationFailure(
                check="coverage_type",
                description="coverage_percentage must be a number",
                expected="int or float",
                actual=str(type(coverage_percentage).__name__),
            )
        )
        return

    if coverage_percentage < min_coverage:
        failures.append(
            VerificationFailure(
                check="coverage_threshold",
                description=(
                    f"Coverage {coverage_percentage}% is below "
                    f"minimum threshold {min_coverage}%"
                ),
                expected=f">= {min_coverage}%",
                actual=f"{coverage_percentage}%",
            )
        )
    else:
        checks_passed.append("coverage_threshold")

    if coverage_percentage < 0 or coverage_percentage > 100:
        failures.append(
            VerificationFailure(
                check="coverage_range",
                description=f"Coverage {coverage_percentage}% is outside valid range [0, 100]",
                expected="0-100",
                actual=str(coverage_percentage),
            )
        )
    else:
        checks_passed.append("coverage_range")
