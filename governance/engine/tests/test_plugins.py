"""Tests for governance.engine.orchestrator.plugins — plugin architecture for extensibility."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.engine.orchestrator.plugins import (
    ExtensionsConfig,
    HookConfig,
    HookResult,
    PanelPlugin,
    PhasePlugin,
    PluginRegistry,
    execute_hook,
    execute_hooks,
    validate_extensions,
)


# ---------------------------------------------------------------------------
# PhasePlugin dataclass
# ---------------------------------------------------------------------------


class TestPhasePlugin:
    def test_defaults(self):
        p = PhasePlugin()
        assert p.name == ""
        assert p.script == ""
        assert p.after_phase == 5
        assert p.timeout_seconds == 300
        assert p.required is True

    def test_custom_values(self):
        p = PhasePlugin(name="deploy", script="scripts/deploy.py", after_phase=3, timeout_seconds=60, required=False)
        assert p.name == "deploy"
        assert p.after_phase == 3
        assert p.required is False

    def test_to_dict(self):
        p = PhasePlugin(name="lint", script="scripts/lint.sh")
        d = p.to_dict()
        assert d["name"] == "lint"
        assert d["script"] == "scripts/lint.sh"
        assert d["after_phase"] == 5
        assert d["timeout_seconds"] == 300
        assert d["required"] is True


# ---------------------------------------------------------------------------
# PanelPlugin dataclass
# ---------------------------------------------------------------------------


class TestPanelPlugin:
    def test_defaults(self):
        p = PanelPlugin()
        assert p.name == ""
        assert p.prompt == ""
        assert p.weight == 0.05
        assert p.required is False

    def test_custom_values(self):
        p = PanelPlugin(name="custom-sec", prompt="prompts/sec.md", weight=0.10, required=True)
        assert p.name == "custom-sec"
        assert p.weight == 0.10
        assert p.required is True

    def test_to_dict(self):
        p = PanelPlugin(name="perf", prompt="prompts/perf.md", weight=0.15)
        d = p.to_dict()
        assert d["name"] == "perf"
        assert d["prompt"] == "prompts/perf.md"
        assert d["weight"] == 0.15
        assert d["required"] is False


# ---------------------------------------------------------------------------
# HookConfig dataclass
# ---------------------------------------------------------------------------


class TestHookConfig:
    def test_defaults(self):
        h = HookConfig()
        assert h.post_merge == []
        assert h.pre_dispatch == []
        assert h.post_review == []
        assert h.on_shutdown == []

    def test_with_scripts(self):
        h = HookConfig(post_merge=["scripts/a.sh"], pre_dispatch=["scripts/b.sh"])
        assert h.post_merge == ["scripts/a.sh"]
        assert h.pre_dispatch == ["scripts/b.sh"]

    def test_to_dict(self):
        h = HookConfig(post_merge=["x.sh"])
        d = h.to_dict()
        assert d["post_merge"] == ["x.sh"]
        assert d["pre_dispatch"] == []
        assert d["post_review"] == []
        assert d["on_shutdown"] == []


# ---------------------------------------------------------------------------
# ExtensionsConfig parsing
# ---------------------------------------------------------------------------


class TestExtensionsConfigFromDict:
    def test_none_returns_empty(self):
        cfg = ExtensionsConfig.from_dict(None)
        assert cfg.phases == []
        assert cfg.panel_types == []
        assert cfg.hooks.post_merge == []

    def test_empty_dict_returns_empty(self):
        cfg = ExtensionsConfig.from_dict({})
        assert cfg.phases == []
        assert cfg.panel_types == []

    def test_parses_phases(self):
        data = {
            "phases": [
                {"name": "deploy", "script": "scripts/deploy.py", "after_phase": 5},
                {"name": "lint", "script": "scripts/lint.sh", "after_phase": 2, "timeout_seconds": 60},
            ]
        }
        cfg = ExtensionsConfig.from_dict(data)
        assert len(cfg.phases) == 2
        assert cfg.phases[0].name == "deploy"
        assert cfg.phases[0].after_phase == 5
        assert cfg.phases[1].name == "lint"
        assert cfg.phases[1].timeout_seconds == 60

    def test_parses_panel_types(self):
        data = {
            "panel_types": [
                {"name": "custom-security", "prompt": "prompts/sec.md", "weight": 0.10},
            ]
        }
        cfg = ExtensionsConfig.from_dict(data)
        assert len(cfg.panel_types) == 1
        assert cfg.panel_types[0].name == "custom-security"
        assert cfg.panel_types[0].weight == 0.10

    def test_parses_hooks(self):
        data = {
            "hooks": {
                "post_merge": ["scripts/post-merge.sh"],
                "pre_dispatch": ["scripts/pre-dispatch.sh"],
                "post_review": ["scripts/post-review.sh"],
                "on_shutdown": ["scripts/shutdown.sh"],
            }
        }
        cfg = ExtensionsConfig.from_dict(data)
        assert cfg.hooks.post_merge == ["scripts/post-merge.sh"]
        assert cfg.hooks.pre_dispatch == ["scripts/pre-dispatch.sh"]
        assert cfg.hooks.post_review == ["scripts/post-review.sh"]
        assert cfg.hooks.on_shutdown == ["scripts/shutdown.sh"]

    def test_null_hooks_becomes_empty(self):
        data = {"hooks": None}
        cfg = ExtensionsConfig.from_dict(data)
        assert cfg.hooks.post_merge == []

    def test_missing_phase_fields_use_defaults(self):
        data = {"phases": [{}]}
        cfg = ExtensionsConfig.from_dict(data)
        assert cfg.phases[0].name == ""
        assert cfg.phases[0].after_phase == 5
        assert cfg.phases[0].required is True

    def test_missing_panel_fields_use_defaults(self):
        data = {"panel_types": [{}]}
        cfg = ExtensionsConfig.from_dict(data)
        assert cfg.panel_types[0].name == ""
        assert cfg.panel_types[0].weight == 0.05
        assert cfg.panel_types[0].required is False


class TestExtensionsConfigHasExtensions:
    def test_empty_has_no_extensions(self):
        cfg = ExtensionsConfig()
        assert cfg.has_extensions is False

    def test_with_phase_has_extensions(self):
        cfg = ExtensionsConfig(phases=[PhasePlugin(name="x")])
        assert cfg.has_extensions is True

    def test_with_panel_has_extensions(self):
        cfg = ExtensionsConfig(panel_types=[PanelPlugin(name="y")])
        assert cfg.has_extensions is True

    def test_with_hook_has_extensions(self):
        cfg = ExtensionsConfig(hooks=HookConfig(post_merge=["a.sh"]))
        assert cfg.has_extensions is True

    def test_empty_hooks_has_no_extensions(self):
        cfg = ExtensionsConfig(hooks=HookConfig())
        assert cfg.has_extensions is False


class TestExtensionsConfigSerialization:
    def test_round_trip(self):
        original = ExtensionsConfig(
            phases=[PhasePlugin(name="deploy", script="s.py", after_phase=5)],
            panel_types=[PanelPlugin(name="sec", prompt="p.md", weight=0.10)],
            hooks=HookConfig(post_merge=["a.sh"], on_shutdown=["b.sh"]),
        )
        d = original.to_dict()

        # Verify structure
        assert len(d["phases"]) == 1
        assert d["phases"][0]["name"] == "deploy"
        assert len(d["panel_types"]) == 1
        assert d["panel_types"][0]["name"] == "sec"
        assert d["hooks"]["post_merge"] == ["a.sh"]
        assert d["hooks"]["on_shutdown"] == ["b.sh"]

        # Re-parse
        restored = ExtensionsConfig.from_dict(d)
        assert restored.phases[0].name == "deploy"
        assert restored.panel_types[0].weight == 0.10
        assert restored.hooks.post_merge == ["a.sh"]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidateExtensions:
    def test_empty_config_is_valid(self, tmp_path):
        cfg = ExtensionsConfig()
        errors = validate_extensions(cfg, tmp_path)
        assert errors == []

    def test_missing_phase_name(self, tmp_path):
        cfg = ExtensionsConfig(phases=[PhasePlugin(script="s.py")])
        errors = validate_extensions(cfg, tmp_path)
        assert any("missing 'name'" in e for e in errors)

    def test_duplicate_phase_name(self, tmp_path):
        (tmp_path / "s1.py").touch()
        (tmp_path / "s2.py").touch()
        cfg = ExtensionsConfig(phases=[
            PhasePlugin(name="deploy", script="s1.py"),
            PhasePlugin(name="deploy", script="s2.py"),
        ])
        errors = validate_extensions(cfg, tmp_path)
        assert any("Duplicate phase plugin name" in e for e in errors)

    def test_missing_phase_script(self, tmp_path):
        cfg = ExtensionsConfig(phases=[PhasePlugin(name="deploy")])
        errors = validate_extensions(cfg, tmp_path)
        assert any("missing 'script'" in e for e in errors)

    def test_phase_script_not_found(self, tmp_path):
        cfg = ExtensionsConfig(phases=[PhasePlugin(name="deploy", script="missing.py")])
        errors = validate_extensions(cfg, tmp_path)
        assert any("script not found" in e for e in errors)

    def test_phase_script_exists(self, tmp_path):
        (tmp_path / "deploy.py").touch()
        cfg = ExtensionsConfig(phases=[PhasePlugin(name="deploy", script="deploy.py")])
        errors = validate_extensions(cfg, tmp_path)
        assert errors == []

    def test_after_phase_out_of_range(self, tmp_path):
        (tmp_path / "s.py").touch()
        cfg = ExtensionsConfig(phases=[PhasePlugin(name="x", script="s.py", after_phase=8)])
        errors = validate_extensions(cfg, tmp_path)
        assert any("after_phase must be 0-7" in e for e in errors)

    def test_after_phase_negative(self, tmp_path):
        (tmp_path / "s.py").touch()
        cfg = ExtensionsConfig(phases=[PhasePlugin(name="x", script="s.py", after_phase=-1)])
        errors = validate_extensions(cfg, tmp_path)
        assert any("after_phase must be 0-7" in e for e in errors)

    def test_negative_timeout(self, tmp_path):
        (tmp_path / "s.py").touch()
        cfg = ExtensionsConfig(phases=[PhasePlugin(name="x", script="s.py", timeout_seconds=-1)])
        errors = validate_extensions(cfg, tmp_path)
        assert any("timeout_seconds must be non-negative" in e for e in errors)

    def test_missing_panel_name(self, tmp_path):
        cfg = ExtensionsConfig(panel_types=[PanelPlugin(prompt="p.md")])
        errors = validate_extensions(cfg, tmp_path)
        assert any("Panel plugin missing 'name'" in e for e in errors)

    def test_duplicate_panel_name(self, tmp_path):
        (tmp_path / "p1.md").touch()
        (tmp_path / "p2.md").touch()
        cfg = ExtensionsConfig(panel_types=[
            PanelPlugin(name="sec", prompt="p1.md"),
            PanelPlugin(name="sec", prompt="p2.md"),
        ])
        errors = validate_extensions(cfg, tmp_path)
        assert any("Duplicate panel plugin name" in e for e in errors)

    def test_missing_panel_prompt(self, tmp_path):
        cfg = ExtensionsConfig(panel_types=[PanelPlugin(name="sec")])
        errors = validate_extensions(cfg, tmp_path)
        assert any("missing 'prompt'" in e for e in errors)

    def test_panel_prompt_not_found(self, tmp_path):
        cfg = ExtensionsConfig(panel_types=[PanelPlugin(name="sec", prompt="missing.md")])
        errors = validate_extensions(cfg, tmp_path)
        assert any("prompt not found" in e for e in errors)

    def test_panel_prompt_exists(self, tmp_path):
        (tmp_path / "sec.md").touch()
        cfg = ExtensionsConfig(panel_types=[PanelPlugin(name="sec", prompt="sec.md")])
        errors = validate_extensions(cfg, tmp_path)
        assert errors == []

    def test_panel_weight_too_low(self, tmp_path):
        (tmp_path / "p.md").touch()
        cfg = ExtensionsConfig(panel_types=[PanelPlugin(name="x", prompt="p.md", weight=-0.1)])
        errors = validate_extensions(cfg, tmp_path)
        assert any("weight must be 0.0-1.0" in e for e in errors)

    def test_panel_weight_too_high(self, tmp_path):
        (tmp_path / "p.md").touch()
        cfg = ExtensionsConfig(panel_types=[PanelPlugin(name="x", prompt="p.md", weight=1.1)])
        errors = validate_extensions(cfg, tmp_path)
        assert any("weight must be 0.0-1.0" in e for e in errors)

    def test_hook_script_not_found(self, tmp_path):
        cfg = ExtensionsConfig(hooks=HookConfig(post_merge=["missing.sh"]))
        errors = validate_extensions(cfg, tmp_path)
        assert any("Hook 'post_merge' script not found" in e for e in errors)

    def test_hook_script_exists(self, tmp_path):
        (tmp_path / "hook.sh").touch()
        cfg = ExtensionsConfig(hooks=HookConfig(post_merge=["hook.sh"]))
        errors = validate_extensions(cfg, tmp_path)
        assert errors == []

    def test_multiple_hook_types_validated(self, tmp_path):
        cfg = ExtensionsConfig(hooks=HookConfig(
            post_merge=["missing1.sh"],
            pre_dispatch=["missing2.sh"],
            post_review=["missing3.sh"],
            on_shutdown=["missing4.sh"],
        ))
        errors = validate_extensions(cfg, tmp_path)
        assert len(errors) == 4

    def test_mixed_valid_and_invalid(self, tmp_path):
        """A config with some valid and some invalid entries."""
        (tmp_path / "good.py").touch()
        cfg = ExtensionsConfig(
            phases=[
                PhasePlugin(name="good", script="good.py"),
                PhasePlugin(name="bad", script="missing.py"),
            ]
        )
        errors = validate_extensions(cfg, tmp_path)
        assert len(errors) == 1
        assert "bad" in errors[0]


# ---------------------------------------------------------------------------
# PluginRegistry
# ---------------------------------------------------------------------------


class TestPluginRegistry:
    def _make_registry(self):
        cfg = ExtensionsConfig(
            phases=[
                PhasePlugin(name="deploy", script="deploy.py", after_phase=5),
                PhasePlugin(name="test-e2e", script="e2e.py", after_phase=4),
                PhasePlugin(name="lint", script="lint.py", after_phase=2),
            ],
            panel_types=[
                PanelPlugin(name="perf-review", prompt="perf.md", weight=0.10),
                PanelPlugin(name="a11y-review", prompt="a11y.md", weight=0.05),
            ],
            hooks=HookConfig(
                post_merge=["pm.sh"],
                pre_dispatch=["pd.sh"],
            ),
        )
        return PluginRegistry(cfg)

    def test_has_extensions(self):
        reg = self._make_registry()
        assert reg.has_extensions is True

    def test_empty_has_no_extensions(self):
        reg = PluginRegistry(ExtensionsConfig())
        assert reg.has_extensions is False

    def test_get_all_phase_plugins(self):
        reg = self._make_registry()
        phases = reg.get_phase_plugins()
        assert len(phases) == 3

    def test_get_phase_plugins_filtered(self):
        reg = self._make_registry()
        phases = reg.get_phase_plugins(after_phase=5)
        assert len(phases) == 1
        assert phases[0].name == "deploy"

    def test_get_phase_plugins_filtered_empty(self):
        reg = self._make_registry()
        phases = reg.get_phase_plugins(after_phase=1)
        assert phases == []

    def test_get_all_panel_plugins(self):
        reg = self._make_registry()
        panels = reg.get_panel_plugins()
        assert len(panels) == 2

    def test_get_panel_by_name(self):
        reg = self._make_registry()
        panel = reg.get_panel_by_name("perf-review")
        assert panel is not None
        assert panel.weight == 0.10

    def test_get_panel_by_name_missing(self):
        reg = self._make_registry()
        assert reg.get_panel_by_name("nonexistent") is None

    def test_get_hook_scripts(self):
        reg = self._make_registry()
        assert reg.get_hook_scripts("post_merge") == ["pm.sh"]
        assert reg.get_hook_scripts("pre_dispatch") == ["pd.sh"]
        assert reg.get_hook_scripts("post_review") == []
        assert reg.get_hook_scripts("on_shutdown") == []

    def test_get_hook_scripts_unknown_name(self):
        reg = self._make_registry()
        assert reg.get_hook_scripts("nonexistent") == []

    def test_to_dict(self):
        reg = self._make_registry()
        d = reg.to_dict()
        assert len(d["phases"]) == 3
        assert len(d["panel_types"]) == 2
        assert d["hooks"]["post_merge"] == ["pm.sh"]

    def test_config_property(self):
        cfg = ExtensionsConfig()
        reg = PluginRegistry(cfg)
        assert reg.config is cfg


# ---------------------------------------------------------------------------
# HookResult
# ---------------------------------------------------------------------------


class TestHookResult:
    def test_success_result(self):
        r = HookResult(script="a.sh", exit_code=0, success=True)
        assert r.success is True
        assert r.timed_out is False

    def test_failure_result(self):
        r = HookResult(script="a.sh", exit_code=1, stderr="error", success=False)
        assert r.success is False
        assert r.stderr == "error"

    def test_to_dict(self):
        r = HookResult(script="a.sh", exit_code=0, stdout="ok", success=True)
        d = r.to_dict()
        assert d["script"] == "a.sh"
        assert d["exit_code"] == 0
        assert d["stdout"] == "ok"
        assert d["success"] is True
        assert d["timed_out"] is False


# ---------------------------------------------------------------------------
# execute_hook
# ---------------------------------------------------------------------------


class TestExecuteHook:
    def test_dry_run(self, tmp_path):
        result = execute_hook("test.sh", tmp_path, dry_run=True)
        assert result.success is True
        assert result.stdout == "dry run"
        assert result.exit_code == 0

    def test_script_not_found(self, tmp_path):
        result = execute_hook("missing.sh", tmp_path)
        assert result.success is False
        assert result.exit_code == 127
        assert "not found" in result.stderr

    def test_successful_execution(self, tmp_path):
        script = tmp_path / "ok.sh"
        script.write_text("#!/bin/bash\necho hello")
        script.chmod(0o755)
        result = execute_hook("ok.sh", tmp_path)
        assert result.success is True
        assert result.exit_code == 0
        assert "hello" in result.stdout

    def test_failed_execution(self, tmp_path):
        script = tmp_path / "fail.sh"
        script.write_text("#!/bin/bash\nexit 1")
        script.chmod(0o755)
        result = execute_hook("fail.sh", tmp_path)
        assert result.success is False
        assert result.exit_code == 1

    def test_timeout(self, tmp_path):
        script = tmp_path / "slow.sh"
        script.write_text("#!/bin/bash\nsleep 60")
        script.chmod(0o755)
        result = execute_hook("slow.sh", tmp_path, timeout_seconds=1)
        assert result.success is False
        assert result.timed_out is True
        assert result.exit_code == -1

    def test_stdout_truncated(self, tmp_path):
        script = tmp_path / "long.sh"
        # Generate more than 2000 chars of output
        script.write_text("#!/bin/bash\npython3 -c \"print('x' * 5000)\"")
        script.chmod(0o755)
        result = execute_hook("long.sh", tmp_path)
        assert result.success is True
        assert len(result.stdout) <= 2000

    def test_custom_env(self, tmp_path):
        script = tmp_path / "env.sh"
        script.write_text("#!/bin/bash\necho $MY_VAR")
        script.chmod(0o755)
        env = {"MY_VAR": "test_value", "PATH": "/usr/bin:/bin"}
        result = execute_hook("env.sh", tmp_path, env=env)
        assert result.success is True
        assert "test_value" in result.stdout

    def test_os_error(self, tmp_path):
        """Test OSError handling (e.g., permission denied)."""
        script = tmp_path / "noperm.sh"
        script.write_text("#!/bin/bash\necho hi")
        script.chmod(0o000)
        result = execute_hook("noperm.sh", tmp_path)
        assert result.success is False
        assert result.exit_code == -1


# ---------------------------------------------------------------------------
# execute_hooks (multiple hooks)
# ---------------------------------------------------------------------------


class TestExecuteHooks:
    def test_no_hooks(self, tmp_path):
        registry = PluginRegistry(ExtensionsConfig())
        results = execute_hooks("post_merge", registry, tmp_path)
        assert results == []

    def test_dry_run_multiple(self, tmp_path):
        cfg = ExtensionsConfig(hooks=HookConfig(post_merge=["a.sh", "b.sh"]))
        registry = PluginRegistry(cfg)
        results = execute_hooks("post_merge", registry, tmp_path, dry_run=True)
        assert len(results) == 2
        assert all(r.success for r in results)
        assert all(r.stdout == "dry run" for r in results)

    def test_executes_in_order(self, tmp_path):
        s1 = tmp_path / "first.sh"
        s1.write_text("#!/bin/bash\necho first")
        s1.chmod(0o755)
        s2 = tmp_path / "second.sh"
        s2.write_text("#!/bin/bash\necho second")
        s2.chmod(0o755)

        cfg = ExtensionsConfig(hooks=HookConfig(post_merge=["first.sh", "second.sh"]))
        registry = PluginRegistry(cfg)
        results = execute_hooks("post_merge", registry, tmp_path)
        assert len(results) == 2
        assert "first" in results[0].stdout
        assert "second" in results[1].stdout

    def test_continues_after_failure(self, tmp_path):
        """All hooks execute even if one fails."""
        bad = tmp_path / "bad.sh"
        bad.write_text("#!/bin/bash\nexit 1")
        bad.chmod(0o755)
        good = tmp_path / "good.sh"
        good.write_text("#!/bin/bash\necho ok")
        good.chmod(0o755)

        cfg = ExtensionsConfig(hooks=HookConfig(pre_dispatch=["bad.sh", "good.sh"]))
        registry = PluginRegistry(cfg)
        results = execute_hooks("pre_dispatch", registry, tmp_path)
        assert len(results) == 2
        assert results[0].success is False
        assert results[1].success is True

    def test_unknown_hook_name_returns_empty(self, tmp_path):
        cfg = ExtensionsConfig(hooks=HookConfig(post_merge=["a.sh"]))
        registry = PluginRegistry(cfg)
        results = execute_hooks("nonexistent", registry, tmp_path)
        assert results == []
