"""Tests for governance.engine.orchestrator.config — configuration loader."""

import pytest
import yaml

from governance.engine.orchestrator.config import OrchestratorConfig, load_config


# ---------------------------------------------------------------------------
# OrchestratorConfig dataclass defaults
# ---------------------------------------------------------------------------


class TestOrchestratorConfigDefaults:
    def test_default_parallel_coders(self):
        config = OrchestratorConfig()
        assert config.parallel_coders == 5

    def test_default_parallel_tech_leads(self):
        config = OrchestratorConfig()
        assert config.parallel_tech_leads == 3

    def test_default_use_project_manager(self):
        config = OrchestratorConfig()
        assert config.use_project_manager is False

    def test_default_policy_profile(self):
        config = OrchestratorConfig()
        assert config.policy_profile == "default"

    def test_default_paths(self):
        config = OrchestratorConfig()
        assert config.checkpoint_dir == ".artifacts/checkpoints"
        assert config.audit_log_dir == ".artifacts/logs"
        assert config.session_dir == ".artifacts/state/sessions"
        assert config.plans_dir == ".artifacts/plans"
        assert config.panels_dir == ".artifacts/panels"

    def test_default_circuit_breaker_limits(self):
        config = OrchestratorConfig()
        assert config.max_feedback_cycles == 2
        assert config.max_total_eval_cycles == 5

    def test_default_issue_size_limits(self):
        config = OrchestratorConfig()
        assert config.max_issue_body_chars == 15000
        assert config.max_issue_comments == 50

    def test_default_git_conventions(self):
        config = OrchestratorConfig()
        assert config.branch_pattern == "{network_id}/{type}/{number}/{name}"
        assert config.commit_style == "conventional"


# ---------------------------------------------------------------------------
# OrchestratorConfig is frozen (immutable)
# ---------------------------------------------------------------------------


class TestOrchestratorConfigFrozen:
    def test_cannot_set_attribute(self):
        config = OrchestratorConfig()
        with pytest.raises(AttributeError):
            config.parallel_coders = 10

    def test_cannot_set_path(self):
        config = OrchestratorConfig()
        with pytest.raises(AttributeError):
            config.checkpoint_dir = "/tmp/override"


# ---------------------------------------------------------------------------
# OrchestratorConfig with explicit values
# ---------------------------------------------------------------------------


class TestOrchestratorConfigExplicit:
    def test_custom_parallel_coders(self):
        config = OrchestratorConfig(parallel_coders=10)
        assert config.parallel_coders == 10

    def test_custom_policy_profile(self):
        config = OrchestratorConfig(policy_profile="fin_pii_high")
        assert config.policy_profile == "fin_pii_high"

    def test_custom_paths(self):
        config = OrchestratorConfig(
            checkpoint_dir="/custom/checkpoints",
            audit_log_dir="/custom/audit",
        )
        assert config.checkpoint_dir == "/custom/checkpoints"
        assert config.audit_log_dir == "/custom/audit"

    def test_unlimited_coders(self):
        config = OrchestratorConfig(parallel_coders=-1)
        assert config.parallel_coders == -1


# ---------------------------------------------------------------------------
# load_config — file not found
# ---------------------------------------------------------------------------


class TestLoadConfigMissingFile:
    def test_missing_file_returns_defaults(self, tmp_path):
        config = load_config(tmp_path / "nonexistent.yaml")
        assert config == OrchestratorConfig()

    def test_missing_file_default_parallel_coders(self, tmp_path):
        config = load_config(tmp_path / "nonexistent.yaml")
        assert config.parallel_coders == 5

    def test_missing_file_default_policy_profile(self, tmp_path):
        config = load_config(tmp_path / "nonexistent.yaml")
        assert config.policy_profile == "default"


# ---------------------------------------------------------------------------
# load_config — empty file / empty document
# ---------------------------------------------------------------------------


class TestLoadConfigEmptyFile:
    def test_empty_file_returns_defaults(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text("")
        config = load_config(path)
        assert config == OrchestratorConfig()

    def test_null_document_returns_defaults(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text("---\n")
        config = load_config(path)
        assert config == OrchestratorConfig()


# ---------------------------------------------------------------------------
# load_config — partial governance section
# ---------------------------------------------------------------------------


class TestLoadConfigPartialGovernance:
    def test_only_parallel_coders(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text(yaml.dump({"governance": {"parallel_coders": 8}}))
        config = load_config(path)
        assert config.parallel_coders == 8
        assert config.parallel_tech_leads == 3  # default

    def test_only_policy_profile(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text(yaml.dump({"governance": {"policy_profile": "fin_pii_high"}}))
        config = load_config(path)
        assert config.policy_profile == "fin_pii_high"
        assert config.parallel_coders == 5  # default

    def test_only_use_project_manager(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text(yaml.dump({"governance": {"use_project_manager": True}}))
        config = load_config(path)
        assert config.use_project_manager is True

    def test_missing_governance_section(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text(yaml.dump({"name": "test-project"}))
        config = load_config(path)
        assert config == OrchestratorConfig()

    def test_backward_compat_parallel_code_managers(self, tmp_path):
        """parallel_code_managers is accepted for backward compatibility."""
        path = tmp_path / "project.yaml"
        path.write_text(yaml.dump({"governance": {"parallel_code_managers": 4}}))
        config = load_config(path)
        assert config.parallel_tech_leads == 4

    def test_parallel_team_leads_takes_precedence(self, tmp_path):
        """parallel_team_leads takes precedence over parallel_code_managers."""
        path = tmp_path / "project.yaml"
        path.write_text(yaml.dump({
            "governance": {
                "parallel_team_leads": 5,
                "parallel_code_managers": 2,
            }
        }))
        config = load_config(path)
        assert config.parallel_tech_leads == 5


# ---------------------------------------------------------------------------
# load_config — full governance section
# ---------------------------------------------------------------------------


class TestLoadConfigFullGovernance:
    def test_all_governance_fields(self, tmp_path):
        path = tmp_path / "project.yaml"
        data = {
            "governance": {
                "parallel_coders": 12,
                "parallel_tech_leads": 6,
                "use_project_manager": True,
                "policy_profile": "infrastructure_critical",
            },
        }
        path.write_text(yaml.dump(data))
        config = load_config(path)
        assert config.parallel_coders == 12
        assert config.parallel_tech_leads == 6
        assert config.use_project_manager is True
        assert config.policy_profile == "infrastructure_critical"


# ---------------------------------------------------------------------------
# load_config — conventions / git section
# ---------------------------------------------------------------------------


class TestLoadConfigConventions:
    def test_git_conventions(self, tmp_path):
        path = tmp_path / "project.yaml"
        data = {
            "conventions": {
                "git": {
                    "branch_pattern": "{org}/{type}/{id}",
                    "commit_style": "angular",
                },
            },
        }
        path.write_text(yaml.dump(data))
        config = load_config(path)
        assert config.branch_pattern == "{org}/{type}/{id}"
        assert config.commit_style == "angular"

    def test_missing_git_section(self, tmp_path):
        path = tmp_path / "project.yaml"
        data = {"conventions": {}}
        path.write_text(yaml.dump(data))
        config = load_config(path)
        assert config.branch_pattern == "{network_id}/{type}/{number}/{name}"
        assert config.commit_style == "conventional"

    def test_missing_conventions_section(self, tmp_path):
        path = tmp_path / "project.yaml"
        data = {"governance": {"parallel_coders": 3}}
        path.write_text(yaml.dump(data))
        config = load_config(path)
        assert config.branch_pattern == "{network_id}/{type}/{number}/{name}"
        assert config.commit_style == "conventional"

    def test_partial_git_conventions(self, tmp_path):
        path = tmp_path / "project.yaml"
        data = {
            "conventions": {
                "git": {
                    "branch_pattern": "custom/{name}",
                },
            },
        }
        path.write_text(yaml.dump(data))
        config = load_config(path)
        assert config.branch_pattern == "custom/{name}"
        assert config.commit_style == "conventional"  # default


# ---------------------------------------------------------------------------
# load_config — combined governance + conventions
# ---------------------------------------------------------------------------


class TestLoadConfigCombined:
    def test_full_project_yaml(self, tmp_path):
        path = tmp_path / "project.yaml"
        data = {
            "name": "my-project",
            "language": "python",
            "governance": {
                "parallel_coders": 4,
                "parallel_tech_leads": 2,
                "use_project_manager": True,
                "policy_profile": "reduced_touchpoint",
            },
            "conventions": {
                "git": {
                    "branch_pattern": "{team}/{type}/{id}",
                    "commit_style": "gitmoji",
                },
            },
        }
        path.write_text(yaml.dump(data))
        config = load_config(path)
        assert config.parallel_coders == 4
        assert config.parallel_tech_leads == 2
        assert config.use_project_manager is True
        assert config.policy_profile == "reduced_touchpoint"
        assert config.branch_pattern == "{team}/{type}/{id}"
        assert config.commit_style == "gitmoji"
        # Paths retain defaults (not set by project.yaml)
        assert config.checkpoint_dir == ".artifacts/checkpoints"
        assert config.audit_log_dir == ".artifacts/logs"


# ---------------------------------------------------------------------------
# load_config — null subsections
# ---------------------------------------------------------------------------


class TestLoadConfigNullSubsections:
    def test_governance_null(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text("governance: null\n")
        config = load_config(path)
        assert config == OrchestratorConfig()

    def test_conventions_null(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text("conventions: null\n")
        config = load_config(path)
        assert config.branch_pattern == "{network_id}/{type}/{number}/{name}"

    def test_git_null(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text("conventions:\n  git: null\n")
        config = load_config(path)
        assert config.branch_pattern == "{network_id}/{type}/{number}/{name}"
        assert config.commit_style == "conventional"


# ---------------------------------------------------------------------------
# load_config — accepts Path and str
# ---------------------------------------------------------------------------


class TestLoadConfigPathTypes:
    def test_accepts_pathlib_path(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text(yaml.dump({"governance": {"parallel_coders": 7}}))
        config = load_config(path)
        assert config.parallel_coders == 7

    def test_accepts_string_path(self, tmp_path):
        path = tmp_path / "project.yaml"
        path.write_text(yaml.dump({"governance": {"parallel_coders": 9}}))
        config = load_config(str(path))
        assert config.parallel_coders == 9


# ---------------------------------------------------------------------------
# load_config — panel_models alternative syntax (#711)
# ---------------------------------------------------------------------------


class TestLoadConfigPanelModels:
    def test_panel_models_defaults(self, tmp_path):
        path = tmp_path / "project.yaml"
        data = {
            "governance": {
                "panel_models": {
                    "defaults": {"model": "claude-sonnet-4-6"},
                }
            }
        }
        path.write_text(yaml.dump(data))
        config = load_config(path)
        assert config.models.default == "claude-sonnet-4-6"

    def test_panel_models_overrides(self, tmp_path):
        path = tmp_path / "project.yaml"
        data = {
            "governance": {
                "panel_models": {
                    "overrides": {
                        "security-review": {"model": "claude-opus-4-6"},
                        "documentation-review": {"model": "claude-haiku-4-5"},
                    }
                }
            }
        }
        path.write_text(yaml.dump(data))
        config = load_config(path)
        assert config.models.panel_overrides["security-review"] == "claude-opus-4-6"
        assert config.models.panel_overrides["documentation-review"] == "claude-haiku-4-5"

    def test_panel_models_overrides_merge_with_models_panels(self, tmp_path):
        """panel_models overrides take precedence over models.panels."""
        path = tmp_path / "project.yaml"
        data = {
            "governance": {
                "models": {
                    "panels": {
                        "security-review": "opus",
                        "code-review": "sonnet",
                    }
                },
                "panel_models": {
                    "overrides": {
                        "security-review": {"model": "gpt-4o"},
                    }
                }
            }
        }
        path.write_text(yaml.dump(data))
        config = load_config(path)
        # panel_models override wins for security-review
        assert config.models.panel_overrides["security-review"] == "gpt-4o"
        # models.panels is preserved for code-review
        assert config.models.panel_overrides["code-review"] == "sonnet"

    def test_panel_models_default_does_not_override_explicit_models_default(self, tmp_path):
        """panel_models.defaults.model only applies when models.default is 'auto'."""
        path = tmp_path / "project.yaml"
        data = {
            "governance": {
                "models": {
                    "default": "sonnet",
                },
                "panel_models": {
                    "defaults": {"model": "haiku"},
                }
            }
        }
        path.write_text(yaml.dump(data))
        config = load_config(path)
        # models.default was explicitly set, so panel_models.defaults.model is not used
        assert config.models.default == "sonnet"

    def test_panel_models_default_applies_when_models_default_is_auto(self, tmp_path):
        """panel_models.defaults.model applies when models.default is 'auto'."""
        path = tmp_path / "project.yaml"
        data = {
            "governance": {
                "panel_models": {
                    "defaults": {"model": "claude-sonnet-4-6"},
                }
            }
        }
        path.write_text(yaml.dump(data))
        config = load_config(path)
        assert config.models.default == "claude-sonnet-4-6"

    def test_no_panel_models_section(self, tmp_path):
        """Without panel_models, config loads normally."""
        path = tmp_path / "project.yaml"
        data = {"governance": {"parallel_coders": 3}}
        path.write_text(yaml.dump(data))
        config = load_config(path)
        assert config.models.panel_overrides == {}
        assert config.models.default == "auto"
