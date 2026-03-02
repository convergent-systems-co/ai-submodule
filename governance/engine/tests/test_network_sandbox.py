"""Tests for governance.engine.network_sandbox — network sandboxing rules."""

import pytest

from governance.engine.network_sandbox import (
    DEFAULT_WHITELIST_HOSTS,
    DEFAULT_WHITELIST_PORTS,
    NetworkSandbox,
    SandboxConfig,
)


# ---------------------------------------------------------------------------
# SandboxConfig
# ---------------------------------------------------------------------------

class TestSandboxConfig:
    def test_default_config(self):
        config = SandboxConfig()
        assert config.enabled is True
        assert config.allow_localhost is True
        assert config.dry_run is False
        assert len(config.whitelist_hosts) > 0
        assert 443 in config.whitelist_ports
        assert 53 in config.whitelist_ports

    def test_from_dict(self):
        config = SandboxConfig.from_dict({
            "enabled": True,
            "extra_hosts": ["custom.example.com"],
            "extra_ports": [8080],
        })
        assert "custom.example.com" in config.extra_hosts
        assert 8080 in config.extra_ports

    def test_from_dict_disabled(self):
        config = SandboxConfig.from_dict({"enabled": False})
        assert config.enabled is False

    def test_all_hosts_includes_extra(self):
        config = SandboxConfig(extra_hosts=["custom.example.com"])
        assert "custom.example.com" in config.all_hosts
        assert "api.github.com" in config.all_hosts

    def test_all_ports_includes_extra(self):
        config = SandboxConfig(extra_ports=[8080])
        assert 8080 in config.all_ports
        assert 443 in config.all_ports

    def test_all_ports_deduplicated(self):
        config = SandboxConfig(extra_ports=[443])
        ports = config.all_ports
        assert ports.count(443) == 1

    def test_default_whitelist_has_github(self):
        assert "api.github.com" in DEFAULT_WHITELIST_HOSTS
        assert "github.com" in DEFAULT_WHITELIST_HOSTS

    def test_default_whitelist_has_llm_providers(self):
        assert "api.anthropic.com" in DEFAULT_WHITELIST_HOSTS
        assert "api.openai.com" in DEFAULT_WHITELIST_HOSTS

    def test_default_whitelist_has_registries(self):
        assert "registry.npmjs.org" in DEFAULT_WHITELIST_HOSTS
        assert "pypi.org" in DEFAULT_WHITELIST_HOSTS


# ---------------------------------------------------------------------------
# NetworkSandbox — basic
# ---------------------------------------------------------------------------

class TestNetworkSandbox:
    def test_default_init(self):
        sandbox = NetworkSandbox()
        assert sandbox.enabled is True

    def test_custom_config(self):
        sandbox = NetworkSandbox(config={"enabled": False})
        assert sandbox.enabled is False

    def test_disabled_returns_comment(self):
        sandbox = NetworkSandbox(config={"enabled": False})
        rules = sandbox.generate_rules(platform="darwin")
        assert "disabled" in rules.lower()


# ---------------------------------------------------------------------------
# macOS pf rules
# ---------------------------------------------------------------------------

class TestPfRules:
    def test_generates_pf_rules(self):
        sandbox = NetworkSandbox()
        rules = sandbox.generate_rules(platform="darwin")
        assert "pf rules" in rules.lower()
        assert "block out all" in rules

    def test_allows_loopback(self):
        sandbox = NetworkSandbox()
        rules = sandbox.generate_rules(platform="darwin")
        assert "pass on lo0" in rules

    def test_no_loopback_when_disabled(self):
        sandbox = NetworkSandbox(config={"allow_localhost": False})
        rules = sandbox.generate_rules(platform="darwin")
        assert "lo0" not in rules

    def test_allows_dns(self):
        sandbox = NetworkSandbox()
        rules = sandbox.generate_rules(platform="darwin")
        assert "port 53" in rules

    def test_whitelisted_hosts_present(self):
        sandbox = NetworkSandbox()
        rules = sandbox.generate_rules(platform="darwin")
        assert "api.github.com" in rules
        assert "api.anthropic.com" in rules

    def test_extra_hosts_present(self):
        sandbox = NetworkSandbox(config={"extra_hosts": ["custom.example.com"]})
        rules = sandbox.generate_rules(platform="darwin")
        assert "custom.example.com" in rules

    def test_blocks_all_other_traffic(self):
        sandbox = NetworkSandbox()
        rules = sandbox.generate_rules(platform="darwin")
        assert "block out all" in rules


# ---------------------------------------------------------------------------
# Linux iptables rules
# ---------------------------------------------------------------------------

class TestIptablesRules:
    def test_generates_iptables_rules(self):
        sandbox = NetworkSandbox()
        rules = sandbox.generate_rules(platform="linux")
        assert "iptables" in rules
        assert "DROP" in rules

    def test_allows_loopback(self):
        sandbox = NetworkSandbox()
        rules = sandbox.generate_rules(platform="linux")
        assert "-o lo -j ACCEPT" in rules

    def test_allows_established(self):
        sandbox = NetworkSandbox()
        rules = sandbox.generate_rules(platform="linux")
        assert "ESTABLISHED,RELATED" in rules

    def test_allows_dns(self):
        sandbox = NetworkSandbox()
        rules = sandbox.generate_rules(platform="linux")
        assert "--dport 53" in rules

    def test_whitelisted_hosts_present(self):
        sandbox = NetworkSandbox()
        rules = sandbox.generate_rules(platform="linux")
        assert "api.github.com" in rules

    def test_blocks_all_other_traffic(self):
        sandbox = NetworkSandbox()
        rules = sandbox.generate_rules(platform="linux")
        assert "-j DROP" in rules

    def test_extra_hosts_present(self):
        sandbox = NetworkSandbox(config={"extra_hosts": ["custom.example.com"]})
        rules = sandbox.generate_rules(platform="linux")
        assert "custom.example.com" in rules


# ---------------------------------------------------------------------------
# Teardown
# ---------------------------------------------------------------------------

class TestTeardown:
    def test_darwin_teardown(self):
        sandbox = NetworkSandbox()
        teardown = sandbox.generate_teardown(platform="darwin")
        assert "pfctl -d" in teardown

    def test_linux_teardown(self):
        sandbox = NetworkSandbox()
        teardown = sandbox.generate_teardown(platform="linux")
        assert "iptables -F OUTPUT" in teardown
        assert "ACCEPT" in teardown


# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------

class TestPlatformDetection:
    def test_unsupported_platform_raises(self):
        sandbox = NetworkSandbox()
        with pytest.raises(ValueError, match="Unsupported"):
            sandbox.generate_rules(platform="windows")

    def test_teardown_unsupported_platform_raises(self):
        sandbox = NetworkSandbox()
        with pytest.raises(ValueError, match="Unsupported"):
            sandbox.generate_teardown(platform="windows")
