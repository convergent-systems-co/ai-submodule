# Plan: Network Sandboxing for Local Agent Execution (#592)

## Summary
Add an optional network containment layer for local agent execution with
platform-specific firewall rules (macOS pf, Linux iptables/nftables).

## Changes

### 1. New file: `governance/engine/network_sandbox.py`
- Whitelist-based network sandboxing configuration
- Generate platform-specific firewall rules (macOS pf, Linux iptables)
- Default whitelist: GitHub API, LLM endpoints, package registries, DNS
- Configurable via project.yaml
- Dry-run mode for preview

### 2. New file: `governance/engine/tests/test_network_sandbox.py`
- Tests for whitelist configuration
- Tests for rule generation (both platforms)
- Tests for opt-out flag

### 3. Update: Reference in project.yaml documentation

## Test Plan
- `python -m pytest governance/engine/ -x --tb=short`
