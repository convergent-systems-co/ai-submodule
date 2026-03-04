"""Sandbox enforcer — operational network sandboxing for agent execution.

High-level orchestration layer for the NetworkSandbox rule generator.
Handles rule application, self-testing, and teardown lifecycle.

When ``governance.network_sandbox.enforce`` is ``true`` in ``project.yaml``,
the enforcer applies generated firewall rules before agent dispatch (Phase 3)
and removes them after completion (Phase 5).

Usage:
    from governance.engine.sandbox_enforcer import SandboxEnforcer

    enforcer = SandboxEnforcer(config)
    result = enforcer.activate()
    if result.success:
        # Agent execution happens here
        ...
    enforcer.deactivate()
"""

from __future__ import annotations

import logging
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any

from governance.engine.network_sandbox import NetworkSandbox, SandboxConfig

logger = logging.getLogger(__name__)


@dataclass
class SelfTestResult:
    """Result of sandbox self-test verification."""

    success: bool
    blocked_check_passed: bool = False   # Non-whitelisted host is blocked
    allowed_check_passed: bool = False   # Whitelisted host is reachable
    error: str = ""
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "blocked_check_passed": self.blocked_check_passed,
            "allowed_check_passed": self.allowed_check_passed,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class EnforcementResult:
    """Result of sandbox activation or deactivation."""

    success: bool
    action: str  # "activate" or "deactivate"
    platform: str = ""
    rules_applied: bool = False
    self_test: SelfTestResult | None = None
    error: str = ""
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "success": self.success,
            "action": self.action,
            "platform": self.platform,
            "rules_applied": self.rules_applied,
            "error": self.error,
            "dry_run": self.dry_run,
        }
        if self.self_test:
            result["self_test"] = self.self_test.to_dict()
        return result


@dataclass
class EnforcerConfig:
    """Configuration for the sandbox enforcer.

    Parsed from governance.network_sandbox in project.yaml:

        governance:
          network_sandbox:
            enabled: true
            enforce: false
            self_test: true
            whitelist:
              extra_hosts: []
              extra_ports: []
    """

    enabled: bool = True
    enforce: bool = False
    self_test: bool = True
    sandbox_config: SandboxConfig = field(default_factory=SandboxConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> EnforcerConfig:
        """Parse from project.yaml governance.network_sandbox section."""
        if not data:
            return cls()

        whitelist = data.get("whitelist", {})
        sandbox_dict = {
            "enabled": data.get("enabled", True),
            "extra_hosts": whitelist.get("extra_hosts", []),
            "extra_ports": whitelist.get("extra_ports", []),
        }

        return cls(
            enabled=data.get("enabled", True),
            enforce=data.get("enforce", False),
            self_test=data.get("self_test", True),
            sandbox_config=SandboxConfig.from_dict(sandbox_dict),
        )


class SandboxEnforcer:
    """Operational network sandboxing for agent execution.

    Manages the full lifecycle: generate rules, apply, self-test, teardown.
    Requires sudo for enforcement. Degrades gracefully when sudo is unavailable.
    """

    # Test targets for self-verification
    BLOCKED_TEST_HOST = "example.com"
    BLOCKED_TEST_PORT = 443
    ALLOWED_TEST_HOST = "api.github.com"
    ALLOWED_TEST_PORT = 443
    SELF_TEST_TIMEOUT = 5  # seconds

    def __init__(self, config: EnforcerConfig | None = None):
        self._config = config or EnforcerConfig()
        self._sandbox = NetworkSandbox(
            config={
                "enabled": self._config.sandbox_config.enabled,
                "extra_hosts": list(self._config.sandbox_config.extra_hosts),
                "extra_ports": list(self._config.sandbox_config.extra_ports),
                "allow_localhost": self._config.sandbox_config.allow_localhost,
                "dry_run": self._config.sandbox_config.dry_run,
            }
        )
        self._active = False

    @property
    def config(self) -> EnforcerConfig:
        """The enforcer configuration."""
        return self._config

    @property
    def is_active(self) -> bool:
        """Whether sandbox enforcement is currently active."""
        return self._active

    def activate(self, dry_run: bool = False) -> EnforcementResult:
        """Activate network sandboxing.

        Generates firewall rules, applies them, and optionally runs
        a self-test to verify enforcement.

        Args:
            dry_run: If True, generate and log rules but do not apply.

        Returns:
            EnforcementResult with activation status.
        """
        if not self._config.enabled:
            return EnforcementResult(
                success=True,
                action="activate",
                error="Network sandboxing is disabled",
                dry_run=dry_run,
            )

        if not self._config.enforce and not dry_run:
            # Generate-only mode: log rules but don't apply
            platform = self._sandbox.detect_platform()
            rules = self._sandbox.generate_rules(platform)
            logger.info("Network sandbox rules generated (not enforced):\n%s", rules)
            return EnforcementResult(
                success=True,
                action="activate",
                platform=platform,
                rules_applied=False,
                dry_run=True,
            )

        try:
            platform = self._sandbox.detect_platform()
        except RuntimeError as e:
            return EnforcementResult(
                success=False,
                action="activate",
                error=str(e),
                dry_run=dry_run,
            )

        rules = self._sandbox.generate_rules(platform)

        if dry_run:
            logger.info("Dry-run: would apply rules:\n%s", rules)
            return EnforcementResult(
                success=True,
                action="activate",
                platform=platform,
                rules_applied=False,
                dry_run=True,
            )

        # Apply rules
        apply_result = self._apply_rules(rules, platform)
        if not apply_result.success:
            return apply_result

        self._active = True

        # Self-test
        if self._config.self_test:
            test_result = self.run_self_test()
            apply_result.self_test = test_result
            if not test_result.success:
                logger.warning(
                    "Self-test failed: %s. Deactivating sandbox.",
                    test_result.error,
                )
                self.deactivate()
                apply_result.success = False
                apply_result.error = f"Self-test failed: {test_result.error}"
                return apply_result

        return apply_result

    def deactivate(self) -> EnforcementResult:
        """Remove network sandbox rules.

        Returns:
            EnforcementResult with deactivation status.
        """
        if not self._active:
            return EnforcementResult(
                success=True,
                action="deactivate",
                error="Sandbox was not active",
            )

        try:
            platform = self._sandbox.detect_platform()
        except RuntimeError as e:
            return EnforcementResult(
                success=False,
                action="deactivate",
                error=str(e),
            )

        teardown = self._sandbox.generate_teardown(platform)

        try:
            subprocess.run(
                ["sudo", "bash", "-c", teardown],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            self._active = False
            return EnforcementResult(
                success=True,
                action="deactivate",
                platform=platform,
                rules_applied=False,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error("Failed to deactivate sandbox: %s", e)
            return EnforcementResult(
                success=False,
                action="deactivate",
                platform=platform,
                error=str(e),
            )

    def run_self_test(self) -> SelfTestResult:
        """Verify that sandbox rules are enforced.

        Tests two conditions:
        1. A non-whitelisted host (example.com) should be unreachable
        2. A whitelisted host (api.github.com) should be reachable

        Returns:
            SelfTestResult with verification details.
        """
        start = time.monotonic()

        # Test 1: Non-whitelisted host should be blocked
        blocked_ok = not self._can_connect(
            self.BLOCKED_TEST_HOST, self.BLOCKED_TEST_PORT
        )

        # Test 2: Whitelisted host should be reachable
        allowed_ok = self._can_connect(
            self.ALLOWED_TEST_HOST, self.ALLOWED_TEST_PORT
        )

        duration = time.monotonic() - start

        success = blocked_ok and allowed_ok
        error = ""
        if not blocked_ok:
            error = f"Non-whitelisted host {self.BLOCKED_TEST_HOST} was reachable (should be blocked)"
        elif not allowed_ok:
            error = f"Whitelisted host {self.ALLOWED_TEST_HOST} was unreachable (should be allowed)"

        return SelfTestResult(
            success=success,
            blocked_check_passed=blocked_ok,
            allowed_check_passed=allowed_ok,
            error=error,
            duration_seconds=round(duration, 3),
        )

    def status(self) -> dict[str, Any]:
        """Return current enforcement status.

        Returns:
            Dict with status information.
        """
        return {
            "enabled": self._config.enabled,
            "enforce": self._config.enforce,
            "active": self._active,
            "self_test_enabled": self._config.self_test,
            "platform": self._detect_platform_safe(),
            "whitelist_hosts": self._config.sandbox_config.all_hosts,
            "whitelist_ports": self._config.sandbox_config.all_ports,
        }

    def _apply_rules(self, rules: str, platform: str) -> EnforcementResult:
        """Apply firewall rules for the given platform."""
        try:
            if platform == "darwin":
                return self._apply_pf_rules(rules)
            elif platform == "linux":
                return self._apply_iptables_rules(rules)
            else:
                return EnforcementResult(
                    success=False,
                    action="activate",
                    platform=platform,
                    error=f"Unsupported platform: {platform}",
                )
        except FileNotFoundError:
            logger.warning(
                "sudo not available. Network sandbox enforcement requires sudo. "
                "Skipping enforcement."
            )
            return EnforcementResult(
                success=False,
                action="activate",
                platform=platform,
                error="sudo not available",
            )

    def _apply_pf_rules(self, rules: str) -> EnforcementResult:
        """Apply macOS pf rules."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".conf", delete=False, prefix="dark-factory-pf-"
        ) as f:
            f.write(rules)
            rules_file = f.name

        try:
            # Load rules
            subprocess.run(
                ["sudo", "pfctl", "-f", rules_file],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            # Enable pf
            subprocess.run(
                ["sudo", "pfctl", "-e"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,  # May already be enabled
            )
            return EnforcementResult(
                success=True,
                action="activate",
                platform="darwin",
                rules_applied=True,
            )
        except subprocess.CalledProcessError as e:
            return EnforcementResult(
                success=False,
                action="activate",
                platform="darwin",
                error=f"pfctl failed: {e.stderr}",
            )
        except subprocess.TimeoutExpired:
            return EnforcementResult(
                success=False,
                action="activate",
                platform="darwin",
                error="pfctl timed out",
            )

    def _apply_iptables_rules(self, rules: str) -> EnforcementResult:
        """Apply Linux iptables rules."""
        try:
            subprocess.run(
                ["sudo", "bash", "-c", rules],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            return EnforcementResult(
                success=True,
                action="activate",
                platform="linux",
                rules_applied=True,
            )
        except subprocess.CalledProcessError as e:
            return EnforcementResult(
                success=False,
                action="activate",
                platform="linux",
                error=f"iptables failed: {e.stderr}",
            )
        except subprocess.TimeoutExpired:
            return EnforcementResult(
                success=False,
                action="activate",
                platform="linux",
                error="iptables timed out",
            )

    def _can_connect(self, host: str, port: int) -> bool:
        """Test if a TCP connection to host:port succeeds."""
        try:
            sock = socket.create_connection(
                (host, port), timeout=self.SELF_TEST_TIMEOUT
            )
            sock.close()
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def _detect_platform_safe(self) -> str:
        """Detect platform without raising on unsupported systems."""
        try:
            return self._sandbox.detect_platform()
        except RuntimeError:
            return "unsupported"
