# Activate Operational Network Sandboxing for Agent Execution

**Author:** Team Lead (batch-scoped PM mode)
**Date:** 2026-03-02
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/707
**Branch:** itsfwcp/feat/707/network-sandboxing-enforcement

---

## 1. Objective

Transform the existing network sandbox from a rule-generator-only module into an operational enforcement system with self-testing verification, orchestrator integration, and configurable whitelist support via project.yaml.

## 2. Rationale

The existing `network_sandbox.py` generates firewall rules but never applies them. DACH's Smelter actively enforces network isolation with self-testing. We need to close this gap.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Use Docker-based network isolation | Yes | Not all developers run Docker locally; pf/iptables is more universal |
| Mandatory enforcement for all repos | Yes | Breaking change; sudo required; opt-in is safer |
| Delegate to external tool (e.g., Little Snitch) | Yes | Non-portable, paid software, can't automate |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/engine/sandbox_enforcer.py` | Enforcement module: applies rules, runs self-test, handles teardown |
| `governance/engine/tests/test_sandbox_enforcer.py` | Tests for enforcer (mocked subprocess calls) |
| `docs/configuration/network-sandboxing.md` | Configuration guide |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/engine/network_sandbox.py` | Add `self_test()` method that verifies rules are active; add `apply_rules()` and `remove_rules()` methods that invoke platform commands; add project.yaml whitelist parsing |
| `governance/engine/orchestrator/dispatcher.py` | Add sandbox activation before Phase 3 agent dispatch and deactivation after Phase 5 |
| `project.yaml` | Add `governance.network_sandbox` configuration section (documented, disabled) |

### Files to Delete

None.

## 4. Approach

1. **Extend `network_sandbox.py`** with enforcement methods:
   - `apply_rules(dry_run=False)` — writes rules to temp file and applies via `pfctl` (macOS) or `iptables-restore` (Linux). Requires sudo. In dry_run mode, only prints commands.
   - `remove_rules()` — teardown (already exists as `generate_teardown`, wire it to subprocess)
   - `self_test()` — after applying rules, attempt to connect to a non-whitelisted host (e.g., `example.com:443`) and verify it is blocked. Then verify a whitelisted host (e.g., `api.github.com:443`) is reachable. Returns `SelfTestResult` dataclass.
   - `is_active()` — check if sandbox rules are currently loaded (parse `pfctl -sr` or `iptables -L OUTPUT`)

2. **Create `sandbox_enforcer.py`** — high-level orchestration:
   - `SandboxEnforcer.activate(config)` — generates rules, applies, runs self-test
   - `SandboxEnforcer.deactivate()` — removes rules
   - `SandboxEnforcer.status()` — returns current enforcement status
   - Handles errors gracefully: if sudo not available, log warning and continue (no hard failure)

3. **Integrate with orchestrator dispatcher** — Add pre-dispatch hook in `dispatcher.py` that calls `SandboxEnforcer.activate()` when `governance.network_sandbox.enforce: true` in project.yaml. Add post-completion hook for `deactivate()`.

4. **Add project.yaml configuration**:
   ```yaml
   governance:
     network_sandbox:
       enabled: true
       enforce: false          # true = actually apply rules (requires sudo)
       self_test: true         # verify rules after activation
       whitelist:
         extra_hosts: []
         extra_ports: []
   ```

5. **Write tests** — Mock subprocess calls for rule application and self-test network connections

6. **Write documentation** — Setup guide, whitelist customization, troubleshooting

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `network_sandbox.py` | Test new `apply_rules`, `self_test`, `is_active` methods (mocked subprocess) |
| Unit | `sandbox_enforcer.py` | Test activate/deactivate lifecycle, error handling |
| Unit | `dispatcher.py` | Test sandbox hooks are called at correct lifecycle points |
| Integration | Full sandbox lifecycle | Test generate -> apply -> self-test -> teardown (dry_run mode) |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| sudo not available | High | Low | Graceful degradation: log warning, skip enforcement |
| Rules block legitimate traffic | Medium | High | Self-test verifies whitelist connectivity; dry_run default |
| Rules persist after crash | Low | Medium | Teardown in finally block; document manual cleanup |
| macOS System Integrity Protection blocks pf | Low | Medium | Detect SIP status, warn if enforcement unavailable |

## 7. Dependencies

- [x] `governance/engine/network_sandbox.py` exists (non-blocking)
- [ ] sudo access for enforcement (optional; graceful degradation)

## 8. Backward Compatibility

Fully backward compatible. Enforcement is opt-in (`enforce: false` by default). Existing rule generation behavior unchanged. The `enabled: true` default only means rules are *generated*, not applied.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Core engine changes |
| security-review | Yes | Network security enforcement |
| threat-modeling | Yes | Firewall rule changes, privilege escalation (sudo) |
| cost-analysis | Yes | No cost impact |

**Policy Profile:** default
**Expected Risk Level:** high (security-sensitive, requires sudo)

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Enforce off by default | Sudo requirement is a barrier; generate-only is safe default |
| 2026-03-02 | Self-test is mandatory when enforce=true | Prevents silent misconfiguration |
| 2026-03-02 | Graceful degradation on sudo failure | Developer experience over strict enforcement |
