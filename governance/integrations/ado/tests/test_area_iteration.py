"""Tests for area path and iteration path mapping."""

from __future__ import annotations

import pytest

from governance.integrations.ado.area_iteration import (
    map_area_path_to_label,
    map_iteration_to_milestone,
    map_label_to_area_path,
    map_milestone_to_iteration,
)


# ── map_label_to_area_path ─────────────────────────────────────────────────


class TestMapLabelToAreaPath:
    def _config(self, mapping=None):
        return {"area_path_mapping": mapping or {}}

    def test_matches_area_label(self):
        config = self._config({"Team A": "Project\\Team A", "Team B": "Project\\Team B"})
        result = map_label_to_area_path(["area:Team A"], config)
        assert result == "Project\\Team A"

    def test_matches_first_area_label(self):
        config = self._config({"Team A": "Project\\Team A", "Team B": "Project\\Team B"})
        result = map_label_to_area_path(["area:Team A", "area:Team B"], config)
        assert result == "Project\\Team A"

    def test_no_area_labels(self):
        config = self._config({"Team A": "Project\\Team A"})
        result = map_label_to_area_path(["bug", "P1"], config)
        assert result is None

    def test_unmatched_area_label(self):
        config = self._config({"Team A": "Project\\Team A"})
        result = map_label_to_area_path(["area:Team Z"], config)
        assert result is None

    def test_empty_mapping(self):
        result = map_label_to_area_path(["area:Team A"], self._config({}))
        assert result is None

    def test_no_mapping_key(self):
        result = map_label_to_area_path(["area:Team A"], {})
        assert result is None

    def test_case_insensitive_lookup(self):
        config = self._config({"Team A": "Project\\Team A"})
        result = map_label_to_area_path(["area:team a"], config)
        assert result == "Project\\Team A"

    def test_label_prefix_case_insensitive(self):
        config = self._config({"Team A": "Project\\Team A"})
        result = map_label_to_area_path(["Area:Team A"], config)
        assert result == "Project\\Team A"

    def test_empty_labels(self):
        config = self._config({"Team A": "Project\\Team A"})
        result = map_label_to_area_path([], config)
        assert result is None


# ── map_area_path_to_label ─────────────────────────────────────────────────


class TestMapAreaPathToLabel:
    def _config(self, mapping=None):
        return {"area_path_mapping": mapping or {}}

    def test_reverse_maps_area_path(self):
        config = self._config({"Team A": "Project\\Team A"})
        result = map_area_path_to_label("Project\\Team A", config)
        assert result == "area:Team A"

    def test_no_match(self):
        config = self._config({"Team A": "Project\\Team A"})
        result = map_area_path_to_label("Project\\Team Z", config)
        assert result is None

    def test_empty_mapping(self):
        result = map_area_path_to_label("Project\\Team A", self._config({}))
        assert result is None

    def test_no_mapping_key(self):
        result = map_area_path_to_label("Project\\Team A", {})
        assert result is None


# ── map_milestone_to_iteration ─────────────────────────────────────────────


class TestMapMilestoneToIteration:
    def _config(self, mapping=None):
        return {"iteration_mapping": mapping or {}}

    def test_matches_milestone(self):
        config = self._config({"Sprint 1": "Project\\Sprint 1"})
        result = map_milestone_to_iteration("Sprint 1", config)
        assert result == "Project\\Sprint 1"

    def test_no_match(self):
        config = self._config({"Sprint 1": "Project\\Sprint 1"})
        result = map_milestone_to_iteration("Sprint 99", config)
        assert result is None

    def test_empty_milestone(self):
        config = self._config({"Sprint 1": "Project\\Sprint 1"})
        result = map_milestone_to_iteration("", config)
        assert result is None

    def test_none_milestone(self):
        config = self._config({"Sprint 1": "Project\\Sprint 1"})
        result = map_milestone_to_iteration(None, config)
        assert result is None

    def test_current_iteration_macro(self):
        config = self._config({"Current": "@CurrentIteration"})
        result = map_milestone_to_iteration("Current", config)
        assert result == "@CurrentIteration"

    def test_case_insensitive_lookup(self):
        config = self._config({"Sprint 1": "Project\\Sprint 1"})
        result = map_milestone_to_iteration("sprint 1", config)
        assert result == "Project\\Sprint 1"

    def test_empty_mapping(self):
        result = map_milestone_to_iteration("Sprint 1", self._config({}))
        assert result is None

    def test_no_mapping_key(self):
        result = map_milestone_to_iteration("Sprint 1", {})
        assert result is None


# ── map_iteration_to_milestone ─────────────────────────────────────────────


class TestMapIterationToMilestone:
    def _config(self, mapping=None):
        return {"iteration_mapping": mapping or {}}

    def test_reverse_maps_iteration(self):
        config = self._config({"Sprint 1": "Project\\Sprint 1"})
        result = map_iteration_to_milestone("Project\\Sprint 1", config)
        assert result == "Sprint 1"

    def test_no_match(self):
        config = self._config({"Sprint 1": "Project\\Sprint 1"})
        result = map_iteration_to_milestone("Project\\Sprint 99", config)
        assert result is None

    def test_empty_iteration_path(self):
        config = self._config({"Sprint 1": "Project\\Sprint 1"})
        result = map_iteration_to_milestone("", config)
        assert result is None

    def test_none_iteration_path(self):
        config = self._config({"Sprint 1": "Project\\Sprint 1"})
        result = map_iteration_to_milestone(None, config)
        assert result is None

    def test_current_iteration_not_reverse_mapped(self):
        """@CurrentIteration should never be reverse-mapped."""
        config = self._config({"Current": "@CurrentIteration"})
        result = map_iteration_to_milestone("@CurrentIteration", config)
        assert result is None

    def test_skips_current_iteration_in_reverse(self):
        """If a mapping points to @CurrentIteration, it shouldn't be used in reverse."""
        config = self._config({
            "Sprint 1": "Project\\Sprint 1",
            "Current": "@CurrentIteration",
        })
        result = map_iteration_to_milestone("Project\\Sprint 1", config)
        assert result == "Sprint 1"

    def test_empty_mapping(self):
        result = map_iteration_to_milestone("Project\\Sprint 1", self._config({}))
        assert result is None

    def test_no_mapping_key(self):
        result = map_iteration_to_milestone("Project\\Sprint 1", {})
        assert result is None
