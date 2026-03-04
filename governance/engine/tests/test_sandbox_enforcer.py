"""Tests for sandbox_enforcer — operational network sandboxing."""

from unittest.mock import MagicMock, patch

import pytest

from governance.engine.sandbox_enforcer import (
    EnforcementResult,
    EnforcerConfig,
    SandboxEnforcer,
    SelfTestResult,
)
from governance.engine.network_sandbox import SandboxConfig


# ---------------------------------------------------------------------------
# EnforcerConfig
# ---------------------------------------------------------------------------

class TestEnforcerConfig:
    def test_default_config(self):
        config = EnforcerConfig()
        assert config.enabled is True
        assert config.enforce is False
        assert config.self_test is True

    def test_from_dict_none(self):
        config = EnforcerConfig.from_dict(None)
        assert config.enabled is True
        assert config.enforce is False

    def test_from_dict_full(self):
        config = EnforcerConfig.from_dict({
            "enabled": True,
            "enforce": True,
            "self_test": False,
            "whitelist": {
                "extra_hosts": ["custom.example.com"],
                "extra_ports": [8080],
            },
        })
        assert config.enabled is True
        assert config.enforce is True
        assert config.self_test is False
        assert "custom.example.com" in config.sandbox_config.extra_hosts
        assert 8080 in config.sandbox_config.extra_ports

    def test_from_dict_disabled(self):
        config = EnforcerConfig.from_dict({"enabled": False})
        assert config.enabled is False


# ---------------------------------------------------------------------------
# SandboxEnforcer — disabled/generate-only
# ---------------------------------------------------------------------------

class TestSandboxEnforcerDisabled:
    def test_disabled_activation_succeeds(self):
        config = EnforcerConfig(enabled=False)
        enforcer = SandboxEnforcer(config)
        result = enforcer.activate()
        assert result.success is True
        assert "disabled" in result.error

    def test_generate_only_mode(self):
        config = EnforcerConfig(enabled=True, enforce=False)
        enforcer = SandboxEnforcer(config)
        result = enforcer.activate()
        assert result.success is True
        assert result.rules_applied is False
        assert result.dry_run is True

    def test_dry_run_mode(self):
        config = EnforcerConfig(enabled=True, enforce=True)
        enforcer = SandboxEnforcer(config)
        result = enforcer.activate(dry_run=True)
        assert result.success is True
        assert result.rules_applied is False
        assert result.dry_run is True


# ---------------------------------------------------------------------------
# SandboxEnforcer — enforcement
# ---------------------------------------------------------------------------

class TestSandboxEnforcerEnforce:
    @patch("governance.engine.sandbox_enforcer.subprocess.run")
    def test_activate_success_darwin(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        config = EnforcerConfig(enabled=True, enforce=True, self_test=False)
        enforcer = SandboxEnforcer(config)

        with patch.object(enforcer._sandbox, "detect_platform", return_value="darwin"):
            result = enforcer.activate()

        assert result.success is True
        assert result.rules_applied is True
        assert result.platform == "darwin"
        assert enforcer.is_active is True

    @patch("governance.engine.sandbox_enforcer.subprocess.run")
    def test_activate_success_linux(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        config = EnforcerConfig(enabled=True, enforce=True, self_test=False)
        enforcer = SandboxEnforcer(config)

        with patch.object(enforcer._sandbox, "detect_platform", return_value="linux"):
            result = enforcer.activate()

        assert result.success is True
        assert result.rules_applied is True
        assert result.platform == "linux"

    def test_activate_unsupported_platform(self):
        config = EnforcerConfig(enabled=True, enforce=True, self_test=False)
        enforcer = SandboxEnforcer(config)

        with patch.object(enforcer._sandbox, "detect_platform", side_effect=RuntimeError("Unsupported")):
            result = enforcer.activate()

        assert result.success is False
        assert "Unsupported" in result.error

    @patch("governance.engine.sandbox_enforcer.subprocess.run")
    def test_activate_sudo_not_available(self, mock_run):
        mock_run.side_effect = FileNotFoundError("sudo not found")
        config = EnforcerConfig(enabled=True, enforce=True, self_test=False)
        enforcer = SandboxEnforcer(config)

        with patch.object(enforcer._sandbox, "detect_platform", return_value="darwin"):
            result = enforcer.activate()

        assert result.success is False
        assert "sudo not available" in result.error


# ---------------------------------------------------------------------------
# SandboxEnforcer — deactivate
# ---------------------------------------------------------------------------

class TestSandboxEnforcerDeactivate:
    def test_deactivate_when_not_active(self):
        config = EnforcerConfig(enabled=True, enforce=True)
        enforcer = SandboxEnforcer(config)
        result = enforcer.deactivate()
        assert result.success is True
        assert "not active" in result.error

    @patch("governance.engine.sandbox_enforcer.subprocess.run")
    def test_deactivate_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        config = EnforcerConfig(enabled=True, enforce=True, self_test=False)
        enforcer = SandboxEnforcer(config)
        enforcer._active = True

        with patch.object(enforcer._sandbox, "detect_platform", return_value="darwin"):
            result = enforcer.deactivate()

        assert result.success is True
        assert enforcer.is_active is False


# ---------------------------------------------------------------------------
# SelfTestResult
# ---------------------------------------------------------------------------

class TestSelfTestResult:
    def test_to_dict(self):
        result = SelfTestResult(
            success=True,
            blocked_check_passed=True,
            allowed_check_passed=True,
            duration_seconds=0.5,
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["blocked_check_passed"] is True


# ---------------------------------------------------------------------------
# SandboxEnforcer — self-test
# ---------------------------------------------------------------------------

class TestSandboxEnforcerSelfTest:
    @patch.object(SandboxEnforcer, "_can_connect")
    def test_self_test_passes(self, mock_connect):
        # Non-whitelisted blocked (returns False), whitelisted allowed (returns True)
        mock_connect.side_effect = [False, True]
        config = EnforcerConfig(enabled=True, enforce=True, self_test=True)
        enforcer = SandboxEnforcer(config)
        result = enforcer.run_self_test()
        assert result.success is True
        assert result.blocked_check_passed is True
        assert result.allowed_check_passed is True

    @patch.object(SandboxEnforcer, "_can_connect")
    def test_self_test_fails_non_whitelisted_reachable(self, mock_connect):
        # Non-whitelisted reachable (bad), whitelisted reachable (good)
        mock_connect.side_effect = [True, True]
        config = EnforcerConfig(enabled=True, enforce=True, self_test=True)
        enforcer = SandboxEnforcer(config)
        result = enforcer.run_self_test()
        assert result.success is False
        assert result.blocked_check_passed is False

    @patch.object(SandboxEnforcer, "_can_connect")
    def test_self_test_fails_whitelisted_unreachable(self, mock_connect):
        # Non-whitelisted blocked (good), whitelisted unreachable (bad)
        mock_connect.side_effect = [False, False]
        config = EnforcerConfig(enabled=True, enforce=True, self_test=True)
        enforcer = SandboxEnforcer(config)
        result = enforcer.run_self_test()
        assert result.success is False
        assert result.allowed_check_passed is False


# ---------------------------------------------------------------------------
# SandboxEnforcer — status
# ---------------------------------------------------------------------------

class TestSandboxEnforcerStatus:
    def test_status(self):
        config = EnforcerConfig(enabled=True, enforce=False)
        enforcer = SandboxEnforcer(config)
        status = enforcer.status()
        assert status["enabled"] is True
        assert status["enforce"] is False
        assert status["active"] is False
        assert isinstance(status["whitelist_hosts"], list)


# ---------------------------------------------------------------------------
# EnforcementResult
# ---------------------------------------------------------------------------

class TestEnforcementResult:
    def test_to_dict(self):
        result = EnforcementResult(
            success=True,
            action="activate",
            platform="darwin",
            rules_applied=True,
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["action"] == "activate"
        assert d["platform"] == "darwin"

    def test_to_dict_with_self_test(self):
        st = SelfTestResult(success=True, blocked_check_passed=True, allowed_check_passed=True)
        result = EnforcementResult(
            success=True,
            action="activate",
            platform="darwin",
            rules_applied=True,
            self_test=st,
        )
        d = result.to_dict()
        assert "self_test" in d
        assert d["self_test"]["success"] is True
