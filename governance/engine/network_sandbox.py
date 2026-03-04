#!/usr/bin/env python3
"""Network sandboxing for local agent execution.

Generates platform-specific firewall rules (macOS pf, Linux iptables)
to restrict network access for locally running agents. Uses a whitelist
approach — only approved endpoints are reachable.

Default whitelist:
  - GitHub API (api.github.com)
  - GitHub content (*.githubusercontent.com)
  - Anthropic API (api.anthropic.com)
  - OpenAI API (api.openai.com)
  - npm registry (registry.npmjs.org)
  - PyPI (pypi.org, files.pythonhosted.org)
  - DNS (port 53)

Usage:
    from governance.engine.network_sandbox import NetworkSandbox

    sandbox = NetworkSandbox()
    rules = sandbox.generate_rules(platform="darwin")
    print(rules)

    # Or with custom whitelist from project.yaml
    sandbox = NetworkSandbox(config={"extra_hosts": ["custom-api.example.com"]})
"""

from __future__ import annotations

import logging
import platform as _platform
import subprocess
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Default whitelist
# ---------------------------------------------------------------------------

DEFAULT_WHITELIST_HOSTS = [
    # GitHub
    "api.github.com",
    "github.com",
    "*.githubusercontent.com",
    "objects.githubusercontent.com",
    # LLM providers
    "api.anthropic.com",
    "api.openai.com",
    "api.githubcopilot.com",
    # Package registries
    "registry.npmjs.org",
    "pypi.org",
    "files.pythonhosted.org",
    # NuGet
    "api.nuget.org",
]

DEFAULT_WHITELIST_PORTS = [
    443,   # HTTPS
    53,    # DNS
    80,    # HTTP (for redirects)
]


@dataclass
class SandboxConfig:
    """Configuration for network sandboxing."""

    enabled: bool = True
    whitelist_hosts: list[str] = field(default_factory=lambda: list(DEFAULT_WHITELIST_HOSTS))
    whitelist_ports: list[int] = field(default_factory=lambda: list(DEFAULT_WHITELIST_PORTS))
    extra_hosts: list[str] = field(default_factory=list)
    extra_ports: list[int] = field(default_factory=list)
    allow_localhost: bool = True
    dry_run: bool = False

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "SandboxConfig":
        """Create SandboxConfig from a project.yaml configuration dict."""
        return cls(
            enabled=config.get("enabled", True),
            whitelist_hosts=config.get("whitelist_hosts", list(DEFAULT_WHITELIST_HOSTS)),
            whitelist_ports=config.get("whitelist_ports", list(DEFAULT_WHITELIST_PORTS)),
            extra_hosts=config.get("extra_hosts", []),
            extra_ports=config.get("extra_ports", []),
            allow_localhost=config.get("allow_localhost", True),
            dry_run=config.get("dry_run", False),
        )

    @property
    def all_hosts(self) -> list[str]:
        """Combined whitelist and extra hosts."""
        return self.whitelist_hosts + self.extra_hosts

    @property
    def all_ports(self) -> list[int]:
        """Combined whitelist and extra ports."""
        return list(set(self.whitelist_ports + self.extra_ports))


class NetworkSandbox:
    """Network sandboxing rule generator for local agent execution.

    Generates platform-specific firewall rules based on a whitelist
    configuration. Supports macOS (pf/pfctl) and Linux (iptables).
    """

    def __init__(self, config: dict[str, Any] | None = None):
        if config is not None:
            self._config = SandboxConfig.from_dict(config)
        else:
            self._config = SandboxConfig()

    @property
    def config(self) -> SandboxConfig:
        """The sandbox configuration."""
        return self._config

    @property
    def enabled(self) -> bool:
        """Whether sandboxing is enabled."""
        return self._config.enabled

    def detect_platform(self) -> str:
        """Detect the current platform.

        Returns:
            "darwin" for macOS, "linux" for Linux.

        Raises:
            RuntimeError: If the platform is unsupported.
        """
        system = _platform.system().lower()
        if system in ("darwin", "linux"):
            return system
        raise RuntimeError(f"Unsupported platform for network sandboxing: {system}")

    def generate_rules(self, platform: str | None = None) -> str:
        """Generate firewall rules for the given platform.

        Args:
            platform: "darwin" or "linux". Auto-detected if None.

        Returns:
            String containing the firewall rules.
        """
        if not self._config.enabled:
            return "# Network sandboxing disabled\n"

        if platform is None:
            platform = self.detect_platform()

        if platform == "darwin":
            return self._generate_pf_rules()
        elif platform == "linux":
            return self._generate_iptables_rules()
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def _generate_pf_rules(self) -> str:
        """Generate macOS pf rules."""
        lines = [
            "# Dark Forge Network Sandbox — macOS pf rules",
            "# Generated by governance/engine/network_sandbox.py",
            "# Apply: sudo pfctl -f /etc/pf.conf && sudo pfctl -e",
            "",
        ]

        # Allow loopback
        if self._config.allow_localhost:
            lines.append("pass on lo0")
            lines.append("")

        # Allow DNS
        if 53 in self._config.all_ports:
            lines.append("# Allow DNS")
            lines.append("pass out proto { tcp udp } to any port 53")
            lines.append("")

        # Allow whitelisted hosts
        lines.append("# Whitelisted hosts")
        for host in self._config.all_hosts:
            if host.startswith("*"):
                # Wildcard — pf doesn't support wildcards natively,
                # so we add a comment noting this requires DNS resolution
                lines.append(f"# Wildcard: {host} (requires DNS-based resolution)")
            else:
                for port in self._config.all_ports:
                    if port != 53:  # DNS already handled
                        lines.append(f"pass out proto tcp to {host} port {port}")
        lines.append("")

        # Block everything else
        lines.append("# Block all other outbound traffic")
        lines.append("block out all")
        lines.append("")

        return "\n".join(lines)

    def _generate_iptables_rules(self) -> str:
        """Generate Linux iptables rules."""
        lines = [
            "#!/bin/bash",
            "# Dark Forge Network Sandbox — Linux iptables rules",
            "# Generated by governance/engine/network_sandbox.py",
            "# Apply: sudo bash <this-script>",
            "",
            "# Flush existing rules",
            "iptables -F OUTPUT",
            "",
        ]

        # Allow loopback
        if self._config.allow_localhost:
            lines.append("# Allow loopback")
            lines.append("iptables -A OUTPUT -o lo -j ACCEPT")
            lines.append("")

        # Allow established connections
        lines.append("# Allow established connections")
        lines.append("iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT")
        lines.append("")

        # Allow DNS
        if 53 in self._config.all_ports:
            lines.append("# Allow DNS")
            lines.append("iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT")
            lines.append("iptables -A OUTPUT -p udp --dport 53 -j ACCEPT")
            lines.append("")

        # Allow whitelisted hosts
        lines.append("# Whitelisted hosts")
        for host in self._config.all_hosts:
            if host.startswith("*"):
                lines.append(f"# Wildcard: {host} (resolve manually or use domain sets)")
            else:
                for port in self._config.all_ports:
                    if port != 53:
                        lines.append(
                            f"iptables -A OUTPUT -p tcp -d {host} --dport {port} -j ACCEPT"
                        )
        lines.append("")

        # Block everything else
        lines.append("# Block all other outbound traffic")
        lines.append("iptables -A OUTPUT -j DROP")
        lines.append("")

        return "\n".join(lines)

    def is_active(self, platform: str | None = None) -> bool:
        """Check if sandbox rules are currently loaded.

        Parses platform-specific firewall status to detect if Dark Forge
        sandbox rules are active.

        Args:
            platform: "darwin" or "linux". Auto-detected if None.

        Returns:
            True if sandbox rules appear to be active.
        """
        if platform is None:
            platform = self.detect_platform()

        try:
            if platform == "darwin":
                result = subprocess.run(
                    ["sudo", "pfctl", "-sr"],
                    capture_output=True, text=True, timeout=10,
                )
                return "Dark Forge" in result.stdout or "block out all" in result.stdout
            elif platform == "linux":
                result = subprocess.run(
                    ["sudo", "iptables", "-L", "OUTPUT", "-n"],
                    capture_output=True, text=True, timeout=10,
                )
                return "DROP" in result.stdout and "api.github.com" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.debug("Cannot check sandbox status: %s", e)
        return False

    def generate_teardown(self, platform: str | None = None) -> str:
        """Generate teardown commands to remove sandbox rules.

        Args:
            platform: "darwin" or "linux". Auto-detected if None.

        Returns:
            String containing the teardown commands.
        """
        if platform is None:
            platform = self.detect_platform()

        if platform == "darwin":
            return (
                "# Disable pf sandboxing\n"
                "sudo pfctl -d\n"
            )
        elif platform == "linux":
            return (
                "#!/bin/bash\n"
                "# Remove sandbox rules\n"
                "iptables -F OUTPUT\n"
                "iptables -P OUTPUT ACCEPT\n"
            )
        else:
            raise ValueError(f"Unsupported platform: {platform}")
