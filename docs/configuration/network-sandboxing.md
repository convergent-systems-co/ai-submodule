# Network Sandboxing Configuration

Network sandboxing restricts outbound network access during local agent execution. Only approved endpoints (GitHub API, LLM providers, package registries, DNS) are reachable. All other traffic is blocked.

## Quick Start

Network sandboxing is enabled by default in generate-only mode (rules are produced but not applied). To enable enforcement:

```yaml
# project.yaml
governance:
  network_sandbox:
    enabled: true
    enforce: true       # Actually apply firewall rules (requires sudo)
    self_test: true     # Verify rules after activation
```

## How It Works

1. **Phase 3 (Dispatch):** Before agent execution begins, the orchestrator calls `SandboxEnforcer.activate()`
2. **Rule Generation:** Platform-specific firewall rules are generated (macOS pf or Linux iptables)
3. **Enforcement:** If `enforce: true`, rules are applied via `sudo pfctl` (macOS) or `sudo iptables` (Linux)
4. **Self-Test:** If `self_test: true`, the enforcer verifies a non-whitelisted host is blocked and a whitelisted host is reachable
5. **Phase 5 (Complete):** After agent execution, `SandboxEnforcer.deactivate()` removes all rules

## Configuration

```yaml
governance:
  network_sandbox:
    enabled: true           # Generate rules (default: true)
    enforce: false          # Apply rules via sudo (default: false)
    self_test: true         # Verify after activation (default: true)
    whitelist:
      extra_hosts:          # Additional hosts to allow
        - "custom-api.example.com"
        - "internal-registry.corp.net"
      extra_ports:          # Additional ports to allow
        - 8080
        - 8443
```

## Default Whitelist

The following hosts are always allowed:

| Host | Purpose |
|------|---------|
| `api.github.com` | GitHub API |
| `github.com` | GitHub web |
| `*.githubusercontent.com` | GitHub content |
| `api.anthropic.com` | Anthropic (Claude) API |
| `api.openai.com` | OpenAI API |
| `api.githubcopilot.com` | GitHub Copilot API |
| `registry.npmjs.org` | npm registry |
| `pypi.org` | Python Package Index |
| `files.pythonhosted.org` | PyPI file hosting |
| `api.nuget.org` | NuGet registry |

Default ports: 443 (HTTPS), 53 (DNS), 80 (HTTP redirects).

## Platform Support

| Platform | Backend | Requirements |
|----------|---------|--------------|
| macOS | pf (packet filter) | sudo access; pfctl |
| Linux | iptables | sudo access; iptables installed |

## Modes

| Mode | `enabled` | `enforce` | Behavior |
|------|-----------|-----------|----------|
| Disabled | `false` | any | No rules generated |
| Generate-only | `true` | `false` | Rules logged but not applied (default) |
| Enforced | `true` | `true` | Rules applied via sudo |

## Self-Test

When `self_test: true` and enforcement is active, the enforcer:

1. Attempts to connect to `example.com:443` (should be blocked)
2. Attempts to connect to `api.github.com:443` (should be allowed)
3. If either check fails, enforcement is automatically deactivated

## Graceful Degradation

- **sudo unavailable:** Logs a warning and continues without enforcement
- **macOS SIP restrictions:** Detected and reported; enforcement may not work
- **Self-test failure:** Enforcement is automatically deactivated
- **Crash recovery:** If the process crashes mid-enforcement, manually run:
  - macOS: `sudo pfctl -d`
  - Linux: `sudo iptables -F OUTPUT && sudo iptables -P OUTPUT ACCEPT`

## Troubleshooting

**Rules not taking effect on macOS:**
```bash
sudo pfctl -sr   # Show current rules
sudo pfctl -d    # Disable pf entirely
```

**Rules not taking effect on Linux:**
```bash
sudo iptables -L OUTPUT -n   # Show OUTPUT chain
sudo iptables -F OUTPUT      # Flush OUTPUT chain
sudo iptables -P OUTPUT ACCEPT  # Reset default policy
```
