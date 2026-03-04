"""Prompt regression testing — validate golden test datasets.

This module validates the structural integrity of golden test cases stored
in governance/evals/golden/. It ensures every test case conforms to the
expected JSON schema and that all required fields are present and correctly
typed. These tests run as part of the standard pytest suite and are
triggered on changes to governance/prompts/reviews/.
"""

import json
from pathlib import Path

import pytest

from conftest import REPO_ROOT


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EVALS_DIR = REPO_ROOT / "governance" / "evals" / "golden"

# Panels that must have golden test cases
REQUIRED_PANELS = ["security-review", "code-review", "documentation-review"]

# Minimum number of test cases per panel
MIN_CASES_PER_PANEL = 3

# Required top-level fields in every golden test case
REQUIRED_FIELDS = {"test_id", "panel", "description", "input", "expected"}

# Required fields inside the "input" object
REQUIRED_INPUT_FIELDS = {"diff", "files_changed", "change_type"}

# Valid change types
VALID_CHANGE_TYPES = {"feat", "fix", "refactor", "docs", "test", "chore", "perf", "ci"}

# Valid expected verdicts
VALID_VERDICTS = {"approve", "request_changes", "block"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def all_golden_cases():
    """Load all golden test case files from governance/evals/golden/."""
    cases = []
    for panel_dir in sorted(EVALS_DIR.iterdir()):
        if not panel_dir.is_dir():
            continue
        for json_file in sorted(panel_dir.glob("*.json")):
            with open(json_file) as f:
                data = json.load(f)
            cases.append((json_file, data))
    return cases


def _collect_test_case_params():
    """Collect parametrize params at module load time."""
    params = []
    if not EVALS_DIR.exists():
        return params
    for panel_dir in sorted(EVALS_DIR.iterdir()):
        if not panel_dir.is_dir():
            continue
        for json_file in sorted(panel_dir.glob("*.json")):
            with open(json_file) as f:
                data = json.load(f)
            test_id = data.get("test_id", json_file.stem)
            params.append(pytest.param(json_file, data, id=test_id))
    return params


# ---------------------------------------------------------------------------
# Test: Golden directory structure
# ---------------------------------------------------------------------------

class TestGoldenDirectoryStructure:
    """Verify the golden test dataset directory structure."""

    def test_evals_directory_exists(self):
        assert EVALS_DIR.exists(), (
            f"Golden test directory does not exist: {EVALS_DIR}"
        )

    @pytest.mark.parametrize("panel", REQUIRED_PANELS)
    def test_panel_directory_exists(self, panel):
        panel_dir = EVALS_DIR / panel
        assert panel_dir.exists(), (
            f"Missing golden test directory for panel: {panel}"
        )
        assert panel_dir.is_dir(), (
            f"Expected directory but found file: {panel_dir}"
        )

    @pytest.mark.parametrize("panel", REQUIRED_PANELS)
    def test_minimum_test_cases_per_panel(self, panel):
        panel_dir = EVALS_DIR / panel
        if not panel_dir.exists():
            pytest.skip(f"Panel directory does not exist: {panel}")
        json_files = list(panel_dir.glob("*.json"))
        assert len(json_files) >= MIN_CASES_PER_PANEL, (
            f"Panel '{panel}' has {len(json_files)} test cases, "
            f"minimum required is {MIN_CASES_PER_PANEL}"
        )


# ---------------------------------------------------------------------------
# Test: JSON structure validation (parametrized across all cases)
# ---------------------------------------------------------------------------

class TestGoldenCaseStructure:
    """Validate the JSON structure of each golden test case."""

    @pytest.mark.parametrize("json_file,case", _collect_test_case_params())
    def test_is_valid_json_object(self, json_file, case):
        assert isinstance(case, dict), (
            f"{json_file.name}: root must be a JSON object"
        )

    @pytest.mark.parametrize("json_file,case", _collect_test_case_params())
    def test_required_top_level_fields(self, json_file, case):
        missing = REQUIRED_FIELDS - set(case.keys())
        assert not missing, (
            f"{json_file.name}: missing required fields: {missing}"
        )

    @pytest.mark.parametrize("json_file,case", _collect_test_case_params())
    def test_test_id_is_string(self, json_file, case):
        assert isinstance(case.get("test_id"), str), (
            f"{json_file.name}: 'test_id' must be a string"
        )
        assert len(case["test_id"]) > 0, (
            f"{json_file.name}: 'test_id' must not be empty"
        )

    @pytest.mark.parametrize("json_file,case", _collect_test_case_params())
    def test_panel_matches_directory(self, json_file, case):
        expected_panel = json_file.parent.name
        assert case.get("panel") == expected_panel, (
            f"{json_file.name}: 'panel' is '{case.get('panel')}' "
            f"but file is in '{expected_panel}/' directory"
        )

    @pytest.mark.parametrize("json_file,case", _collect_test_case_params())
    def test_description_is_nonempty_string(self, json_file, case):
        assert isinstance(case.get("description"), str), (
            f"{json_file.name}: 'description' must be a string"
        )
        assert len(case["description"].strip()) > 0, (
            f"{json_file.name}: 'description' must not be empty"
        )

    @pytest.mark.parametrize("json_file,case", _collect_test_case_params())
    def test_input_has_required_fields(self, json_file, case):
        input_obj = case.get("input", {})
        assert isinstance(input_obj, dict), (
            f"{json_file.name}: 'input' must be a JSON object"
        )
        missing = REQUIRED_INPUT_FIELDS - set(input_obj.keys())
        assert not missing, (
            f"{json_file.name}: 'input' missing required fields: {missing}"
        )

    @pytest.mark.parametrize("json_file,case", _collect_test_case_params())
    def test_input_diff_is_nonempty_string(self, json_file, case):
        diff = case.get("input", {}).get("diff")
        assert isinstance(diff, str) and len(diff.strip()) > 0, (
            f"{json_file.name}: 'input.diff' must be a non-empty string"
        )

    @pytest.mark.parametrize("json_file,case", _collect_test_case_params())
    def test_input_files_changed_is_list(self, json_file, case):
        files = case.get("input", {}).get("files_changed")
        assert isinstance(files, list) and len(files) > 0, (
            f"{json_file.name}: 'input.files_changed' must be a non-empty list"
        )
        for f in files:
            assert isinstance(f, str), (
                f"{json_file.name}: each entry in 'files_changed' must be a string"
            )

    @pytest.mark.parametrize("json_file,case", _collect_test_case_params())
    def test_input_change_type_is_valid(self, json_file, case):
        change_type = case.get("input", {}).get("change_type")
        assert change_type in VALID_CHANGE_TYPES, (
            f"{json_file.name}: 'input.change_type' is '{change_type}', "
            f"must be one of {VALID_CHANGE_TYPES}"
        )

    @pytest.mark.parametrize("json_file,case", _collect_test_case_params())
    def test_expected_is_dict(self, json_file, case):
        expected = case.get("expected")
        assert isinstance(expected, dict), (
            f"{json_file.name}: 'expected' must be a JSON object"
        )

    @pytest.mark.parametrize("json_file,case", _collect_test_case_params())
    def test_expected_verdict_is_valid(self, json_file, case):
        verdict = case.get("expected", {}).get("expected_verdict")
        assert verdict in VALID_VERDICTS, (
            f"{json_file.name}: 'expected.expected_verdict' is '{verdict}', "
            f"must be one of {VALID_VERDICTS}"
        )

    @pytest.mark.parametrize("json_file,case", _collect_test_case_params())
    def test_expected_categories_is_list(self, json_file, case):
        categories = case.get("expected", {}).get("expected_categories")
        assert isinstance(categories, list), (
            f"{json_file.name}: 'expected.expected_categories' must be a list"
        )
        for cat in categories:
            assert isinstance(cat, str), (
                f"{json_file.name}: each category must be a string"
            )

    @pytest.mark.parametrize("json_file,case", _collect_test_case_params())
    def test_expected_findings_counts_are_non_negative(self, json_file, case):
        expected = case.get("expected", {})
        count_fields = [
            "min_findings_critical",
            "min_findings_high",
            "min_findings_medium",
            "min_findings_low",
        ]
        for field in count_fields:
            if field in expected:
                val = expected[field]
                assert isinstance(val, int) and val >= 0, (
                    f"{json_file.name}: 'expected.{field}' must be a "
                    f"non-negative integer, got {val}"
                )


# ---------------------------------------------------------------------------
# Test: Schema compatibility — golden cases with quality metrics
# ---------------------------------------------------------------------------

class TestSchemaCompatibility:
    """Verify that the panel-output schema supports quality metric fields."""

    @pytest.fixture
    def panel_schema(self):
        schema_path = REPO_ROOT / "governance" / "schemas" / "panel-output.schema.json"
        with open(schema_path) as f:
            return json.load(f)

    def test_findings_schema_allows_groundedness_score(self, panel_schema):
        """The findings items schema must include groundedness_score."""
        findings_props = (
            panel_schema["properties"]["findings"]["items"]["properties"]
        )
        assert "groundedness_score" in findings_props, (
            "Schema missing 'groundedness_score' in findings items"
        )
        gs = findings_props["groundedness_score"]
        assert gs["type"] == "number"
        assert gs["minimum"] == 0.0
        assert gs["maximum"] == 1.0

    def test_findings_schema_allows_hallucination_indicators(self, panel_schema):
        """The findings items schema must include hallucination_indicators."""
        findings_props = (
            panel_schema["properties"]["findings"]["items"]["properties"]
        )
        assert "hallucination_indicators" in findings_props, (
            "Schema missing 'hallucination_indicators' in findings items"
        )
        hi = findings_props["hallucination_indicators"]
        assert hi["type"] == "array"
        assert hi["items"]["type"] == "string"

    def test_quality_metrics_are_optional(self, panel_schema):
        """groundedness_score and hallucination_indicators must NOT be required."""
        required = (
            panel_schema["properties"]["findings"]["items"].get("required", [])
        )
        assert "groundedness_score" not in required, (
            "'groundedness_score' must be optional (not in required list)"
        )
        assert "hallucination_indicators" not in required, (
            "'hallucination_indicators' must be optional (not in required list)"
        )
