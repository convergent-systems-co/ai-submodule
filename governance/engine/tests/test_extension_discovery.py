"""Tests for governance.engine.orchestrator.extension_discovery."""

import json

import pytest

from governance.engine.orchestrator.extension_discovery import (
    DiscoveredExtensions,
    HookExtension,
    PanelExtension,
    PhaseExtension,
    VALID_HOOK_POINTS,
    discover_extensions,
    discover_hooks,
    discover_panels,
    discover_phases,
    generate_catalog,
    write_catalog,
)


# ---------------------------------------------------------------------------
# PanelExtension
# ---------------------------------------------------------------------------


class TestPanelExtension:
    def test_to_dict(self):
        p = PanelExtension(
            name="custom-review",
            path="/ext/panels/custom-review.md",
            description="My custom review",
        )
        d = p.to_dict()
        assert d["name"] == "custom-review"
        assert d["type"] == "panel"
        assert d["path"] == "/ext/panels/custom-review.md"
        assert d["description"] == "My custom review"


# ---------------------------------------------------------------------------
# PhaseExtension
# ---------------------------------------------------------------------------


class TestPhaseExtension:
    def test_to_dict(self):
        p = PhaseExtension(
            name="03-lint",
            path="/ext/phases/03-lint.sh",
            description="Run linter",
            after_phase=3,
        )
        d = p.to_dict()
        assert d["name"] == "03-lint"
        assert d["type"] == "phase"
        assert d["after_phase"] == 3


# ---------------------------------------------------------------------------
# HookExtension
# ---------------------------------------------------------------------------


class TestHookExtension:
    def test_to_dict(self):
        h = HookExtension(
            name="notify",
            path="/ext/hooks/post_merge/notify.sh",
            hook_point="post_merge",
        )
        d = h.to_dict()
        assert d["name"] == "notify"
        assert d["type"] == "hook"
        assert d["hook_point"] == "post_merge"


# ---------------------------------------------------------------------------
# DiscoveredExtensions
# ---------------------------------------------------------------------------


class TestDiscoveredExtensions:
    def test_empty(self):
        ext = DiscoveredExtensions()
        assert ext.total_count == 0
        assert ext.is_empty is True

    def test_total_count(self):
        ext = DiscoveredExtensions(
            panels=[PanelExtension(name="p1", path="/p1")],
            phases=[PhaseExtension(name="ph1", path="/ph1")],
            hooks=[HookExtension(name="h1", path="/h1", hook_point="post_merge")],
        )
        assert ext.total_count == 3
        assert ext.is_empty is False

    def test_panel_names(self):
        ext = DiscoveredExtensions(
            panels=[
                PanelExtension(name="a", path="/a"),
                PanelExtension(name="b", path="/b"),
            ],
        )
        assert ext.panel_names() == ["a", "b"]

    def test_hook_names_for(self):
        ext = DiscoveredExtensions(
            hooks=[
                HookExtension(name="h1", path="/h1", hook_point="pre_dispatch"),
                HookExtension(name="h2", path="/h2", hook_point="post_merge"),
                HookExtension(name="h3", path="/h3", hook_point="pre_dispatch"),
            ],
        )
        assert ext.hook_names_for("pre_dispatch") == ["h1", "h3"]
        assert ext.hook_names_for("post_merge") == ["h2"]
        assert ext.hook_names_for("post_review") == []


# ---------------------------------------------------------------------------
# discover_panels
# ---------------------------------------------------------------------------


class TestDiscoverPanels:
    def test_empty_dir(self, tmp_path):
        panels_dir = tmp_path / "panels"
        panels_dir.mkdir()
        result = discover_panels(panels_dir)
        assert result == []

    def test_missing_dir(self, tmp_path):
        result = discover_panels(tmp_path / "nonexistent")
        assert result == []

    def test_discovers_md_files(self, tmp_path):
        panels_dir = tmp_path / "panels"
        panels_dir.mkdir()
        (panels_dir / "my-review.md").write_text(
            "---\nname: my-review\ndescription: My custom review\n---\n# Review\n"
        )
        result = discover_panels(panels_dir)
        assert len(result) == 1
        assert result[0].name == "my-review"
        assert result[0].description == "My custom review"

    def test_falls_back_to_stem_name(self, tmp_path):
        panels_dir = tmp_path / "panels"
        panels_dir.mkdir()
        (panels_dir / "business-logic.md").write_text("# Business Logic Review\n")
        result = discover_panels(panels_dir)
        assert len(result) == 1
        assert result[0].name == "business-logic"

    def test_ignores_non_md(self, tmp_path):
        panels_dir = tmp_path / "panels"
        panels_dir.mkdir()
        (panels_dir / "not-a-panel.txt").write_text("hello")
        result = discover_panels(panels_dir)
        assert result == []

    def test_multiple_panels_sorted(self, tmp_path):
        panels_dir = tmp_path / "panels"
        panels_dir.mkdir()
        (panels_dir / "z-review.md").write_text("# Z\n")
        (panels_dir / "a-review.md").write_text("# A\n")
        result = discover_panels(panels_dir)
        assert len(result) == 2
        assert result[0].name == "a-review"
        assert result[1].name == "z-review"

    def test_frontmatter_with_version_and_author(self, tmp_path):
        panels_dir = tmp_path / "panels"
        panels_dir.mkdir()
        (panels_dir / "test.md").write_text(
            "---\nname: test-panel\nversion: 2.0.0\nauthor: team-x\n---\n"
        )
        result = discover_panels(panels_dir)
        assert result[0].version == "2.0.0"
        assert result[0].author == "team-x"


# ---------------------------------------------------------------------------
# discover_phases
# ---------------------------------------------------------------------------


class TestDiscoverPhases:
    def test_empty_dir(self, tmp_path):
        phases_dir = tmp_path / "phases"
        phases_dir.mkdir()
        result = discover_phases(phases_dir)
        assert result == []

    def test_missing_dir(self, tmp_path):
        result = discover_phases(tmp_path / "nonexistent")
        assert result == []

    def test_discovers_sh_script(self, tmp_path):
        phases_dir = tmp_path / "phases"
        phases_dir.mkdir()
        (phases_dir / "lint.sh").write_text("#!/bin/bash\n# Run linting\necho lint")
        result = discover_phases(phases_dir)
        assert len(result) == 1
        assert result[0].name == "lint"
        assert result[0].interpreter == "bash"

    def test_discovers_py_script(self, tmp_path):
        phases_dir = tmp_path / "phases"
        phases_dir.mkdir()
        (phases_dir / "validate.py").write_text("#!/usr/bin/env python3\n# Validate config")
        result = discover_phases(phases_dir)
        assert len(result) == 1
        assert result[0].name == "validate"
        assert result[0].interpreter == "python3"

    def test_extracts_after_phase_from_name(self, tmp_path):
        phases_dir = tmp_path / "phases"
        phases_dir.mkdir()
        (phases_dir / "03-lint.sh").write_text("#!/bin/bash\n# After phase 3")
        result = discover_phases(phases_dir)
        assert result[0].after_phase == 3
        assert result[0].name == "03-lint"

    def test_no_phase_number_in_name(self, tmp_path):
        phases_dir = tmp_path / "phases"
        phases_dir.mkdir()
        (phases_dir / "lint.sh").write_text("#!/bin/bash\n")
        result = discover_phases(phases_dir)
        assert result[0].after_phase is None

    def test_extracts_description(self, tmp_path):
        phases_dir = tmp_path / "phases"
        phases_dir.mkdir()
        (phases_dir / "check.sh").write_text("#!/bin/bash\n# My custom check phase\necho done")
        result = discover_phases(phases_dir)
        assert "custom check" in result[0].description


# ---------------------------------------------------------------------------
# discover_hooks
# ---------------------------------------------------------------------------


class TestDiscoverHooks:
    def test_empty_dir(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        result = discover_hooks(hooks_dir)
        assert result == []

    def test_missing_dir(self, tmp_path):
        result = discover_hooks(tmp_path / "nonexistent")
        assert result == []

    def test_discovers_pre_dispatch_hook(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        (hooks_dir / "pre_dispatch").mkdir(parents=True)
        (hooks_dir / "pre_dispatch" / "setup.sh").write_text("#!/bin/bash\n# Setup")
        result = discover_hooks(hooks_dir)
        assert len(result) == 1
        assert result[0].hook_point == "pre_dispatch"
        assert result[0].name == "setup"

    def test_discovers_post_merge_hook(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        (hooks_dir / "post_merge").mkdir(parents=True)
        (hooks_dir / "post_merge" / "cleanup.py").write_text("#!/usr/bin/env python3\n# Cleanup")
        result = discover_hooks(hooks_dir)
        assert len(result) == 1
        assert result[0].hook_point == "post_merge"

    def test_discovers_post_review_hook(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        (hooks_dir / "post_review").mkdir(parents=True)
        (hooks_dir / "post_review" / "notify.sh").write_text("#!/bin/bash\n# Notify")
        result = discover_hooks(hooks_dir)
        assert len(result) == 1
        assert result[0].hook_point == "post_review"

    def test_ignores_unknown_hook_points(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        (hooks_dir / "unknown_point").mkdir(parents=True)
        (hooks_dir / "unknown_point" / "skip.sh").write_text("#!/bin/bash")
        result = discover_hooks(hooks_dir)
        assert result == []

    def test_multiple_hooks_in_same_point(self, tmp_path):
        hooks_dir = tmp_path / "hooks"
        (hooks_dir / "pre_dispatch").mkdir(parents=True)
        (hooks_dir / "pre_dispatch" / "a.sh").write_text("#!/bin/bash")
        (hooks_dir / "pre_dispatch" / "b.sh").write_text("#!/bin/bash")
        result = discover_hooks(hooks_dir)
        assert len(result) == 2

    def test_valid_hook_points_constant(self):
        assert VALID_HOOK_POINTS == {"pre_dispatch", "post_merge", "post_review"}


# ---------------------------------------------------------------------------
# discover_extensions (integration)
# ---------------------------------------------------------------------------


class TestDiscoverExtensions:
    def test_empty_base_dir(self, tmp_path):
        result = discover_extensions(tmp_path)
        assert result.is_empty is True

    def test_full_extension_tree(self, tmp_path):
        ext_dir = tmp_path

        # Panels
        (ext_dir / "panels").mkdir()
        (ext_dir / "panels" / "custom.md").write_text("---\nname: custom\n---\n")

        # Phases
        (ext_dir / "phases").mkdir()
        (ext_dir / "phases" / "lint.sh").write_text("#!/bin/bash\n")

        # Hooks
        (ext_dir / "hooks" / "post_merge").mkdir(parents=True)
        (ext_dir / "hooks" / "post_merge" / "clean.sh").write_text("#!/bin/bash\n")

        result = discover_extensions(ext_dir)
        assert result.total_count == 3
        assert len(result.panels) == 1
        assert len(result.phases) == 1
        assert len(result.hooks) == 1

    def test_partial_extension_tree(self, tmp_path):
        ext_dir = tmp_path
        (ext_dir / "panels").mkdir()
        (ext_dir / "panels" / "review.md").write_text("# Review\n")
        result = discover_extensions(ext_dir)
        assert len(result.panels) == 1
        assert len(result.phases) == 0
        assert len(result.hooks) == 0


# ---------------------------------------------------------------------------
# generate_catalog
# ---------------------------------------------------------------------------


class TestGenerateCatalog:
    def test_empty_catalog(self):
        ext = DiscoveredExtensions()
        catalog = generate_catalog(ext)
        assert catalog["total_extensions"] == 0
        assert catalog["panels"] == []
        assert catalog["phases"] == []
        assert catalog["hooks"] == []
        assert "generated_at" in catalog

    def test_catalog_with_extensions(self):
        ext = DiscoveredExtensions(
            panels=[PanelExtension(name="p1", path="/p1", description="Panel 1")],
            phases=[PhaseExtension(name="ph1", path="/ph1")],
        )
        catalog = generate_catalog(ext)
        assert catalog["total_extensions"] == 2
        assert len(catalog["panels"]) == 1
        assert catalog["panels"][0]["name"] == "p1"
        assert catalog["panels"][0]["type"] == "panel"


# ---------------------------------------------------------------------------
# write_catalog
# ---------------------------------------------------------------------------


class TestWriteCatalog:
    def test_writes_json_file(self, tmp_path):
        ext = DiscoveredExtensions(
            panels=[PanelExtension(name="test", path="/test")],
        )
        output = tmp_path / "catalog.json"
        result_path = write_catalog(ext, output)
        assert result_path == output
        assert output.exists()

        data = json.loads(output.read_text())
        assert data["total_extensions"] == 1

    def test_creates_parent_dirs(self, tmp_path):
        output = tmp_path / "nested" / "dir" / "catalog.json"
        write_catalog(DiscoveredExtensions(), output)
        assert output.exists()
