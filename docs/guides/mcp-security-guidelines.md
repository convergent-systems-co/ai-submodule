# MCP Security Guidelines

This guide defines security controls for the `@jm-packages/dark-forge-mcp` server. The MCP server exposes governance prompts, review panels, policy profiles, and tools via the Model Context Protocol. Because these capabilities influence merge decisions and policy evaluation, securing the MCP surface is critical to maintaining governance integrity.

## Overview

The MCP server bridges AI assistants and the governance pipeline. An improperly secured MCP server can:

- **Leak governance configuration** — policy profiles, review panel logic, and schema details could inform adversarial bypass strategies.
- **Enable policy oracle attacks** — repeated `check_policy` invocations could be used to reverse-engineer passing emission patterns.
- **Serve as a confused deputy** — an untrusted caller could invoke governance tools with the server's filesystem and Python execution privileges.

These risks make tool-level classification, access controls, and audit logging essential.

## Tool Classification

Every MCP tool is classified by its risk profile. Classification determines what access controls, rate limits, and audit requirements apply.

### Read-Only Tools (Low Risk)

These tools return static or computed data without modifying state or invoking external processes.

| Tool | Description | Risk Notes |
|------|-------------|------------|
| `list_panels` | Lists available governance review panels | Exposes panel names and descriptions. Low sensitivity. |
| `list_policy_profiles` | Lists policy profiles with key settings | Exposes profile names, risk tolerance, and auto-merge flags. Useful for reconnaissance but not directly exploitable. |
| `validate_emission` | Validates emission JSON against schema | Parses untrusted JSON input. No subprocess execution. Schema content is returned indirectly via validation errors. |

### Action Tools (Elevated Risk)

These tools invoke subprocesses, accept filesystem paths, or produce decisions that influence the governance pipeline.

| Tool | Description | Risk Notes |
|------|-------------|------------|
| `check_policy` | Runs the policy engine against an emissions directory | **Highest risk.** Spawns a Python subprocess. Accepts a filesystem path (`emissions_dir`). Output reveals merge decisions. Repeated invocations can be used to brute-force passing emission patterns. |
| `generate_name` | Generates compliant Azure resource names | Spawns a Python subprocess. Inputs are constrained strings. Lower risk than `check_policy` but still executes external code. |

### MCP Prompts (Context Injection Surface)

MCP prompts (`governance_review`, `plan_create`, `threat_model`) load governance markdown and inject it into the AI assistant's context. While not "tools" in the execution sense, they are a context injection surface:

- A compromised governance root could serve prompt content containing adversarial instructions.
- Prompt content should be treated as trusted only when served from a verified governance root (see Content Integrity in the [usage guide](mcp-server-usage.md#content-integrity)).

### MCP Resources (Read-Only Content)

Resources served via `governance://` URIs are read-only content (review prompts, personas, schemas, policy profiles, workflow templates). They share the same context injection risks as MCP prompts. Validate governance root integrity before trusting resource content.

## Token Scoping and Authorization

The MCP protocol does not natively enforce per-tool authorization. Deployments must layer access controls at the transport or integration level.

### Recommendations

1. **Separate read-only and action tool servers.** Deploy two MCP server instances:
   - A read-only instance exposing only `list_panels`, `list_policy_profiles`, `validate_emission`, resources, and prompts.
   - A privileged instance exposing `check_policy` and `generate_name`, accessible only from trusted orchestration contexts.

2. **Use transport-level authentication.** When deploying over HTTP/SSE (rather than stdio), require bearer tokens or mTLS. Reject unauthenticated connections.

3. **Restrict `emissions_dir` paths.** The `check_policy` tool accepts an arbitrary filesystem path. Deployments should:
   - Validate that `emissions_dir` resolves to a path within the expected project directory.
   - Reject paths containing `..` traversal segments.
   - Consider sandboxing the Python subprocess (e.g., via containers or filesystem namespaces).

4. **Pin the governance root.** Always pass `--governance-root` explicitly rather than relying on auto-detection. Auto-detection walks up the directory tree and could resolve to an unintended location in shared or containerized environments.

## Confused Deputy Mitigations

A confused deputy attack occurs when a trusted component (the MCP server) is tricked into performing actions on behalf of an untrusted caller using its own elevated privileges.

### Attack Scenarios

| Scenario | Description | Mitigation |
|----------|-------------|------------|
| **Path traversal via `emissions_dir`** | Attacker passes `../../etc/sensitive` as `emissions_dir` to `check_policy`, causing the Python subprocess to read files outside the project. | Validate that `emissions_dir` resolves within the project root. Reject paths with `..` segments. Run Python in a sandboxed environment. |
| **Policy oracle** | Attacker iterates `check_policy` calls with crafted emissions to learn exactly which emission patterns produce `approve` decisions, then generates fake emissions to bypass governance. | Rate limit `check_policy`. Log all invocations with caller identity. Require emissions to be cryptographically signed or hash-linked to actual panel execution. |
| **Prompt injection via resource content** | Compromised governance files contain adversarial instructions that the AI assistant follows when loading resources or prompts. | Validate governance root integrity using the manifest system (`generateManifest` / `validateManifest`). Only serve content from verified governance roots. |
| **Subprocess command injection** | Attacker crafts tool inputs that escape into shell commands when passed to Python subprocesses. | The server uses `spawn` (not `exec`), which avoids shell interpretation. Inputs are passed as array arguments, not interpolated into a command string. This is already mitigated in the current implementation. |

### Defense-in-Depth Checklist

- [ ] `emissions_dir` path validation (project root boundary check)
- [ ] Governance root pinned via `--governance-root` (not auto-detected in production)
- [ ] Manifest validation before serving resources/prompts
- [ ] Python subprocess sandboxed (container or namespace isolation)
- [ ] MCP transport authenticated (bearer token or mTLS for HTTP/SSE)
- [ ] All tool invocations logged with caller identity and timestamp

## Rate Limiting

Rate limiting prevents abuse of action tools and limits the effectiveness of oracle attacks against the policy engine.

### Recommended Limits

| Tool | Limit | Rationale |
|------|-------|-----------|
| `list_panels` | 60 requests/minute | Low risk, but excessive calls may indicate enumeration. |
| `list_policy_profiles` | 60 requests/minute | Low risk. Same rationale as `list_panels`. |
| `validate_emission` | 30 requests/minute | Parses untrusted JSON. Moderate CPU cost per call. |
| `check_policy` | 10 requests/minute | Spawns a Python subprocess. Highest risk for oracle attacks. Strict limit. |
| `generate_name` | 20 requests/minute | Spawns a Python subprocess. Lower risk but still resource-intensive. |

### Implementation Notes

- The MCP protocol does not define a standard rate limiting mechanism. Rate limiting must be implemented at the transport layer (e.g., reverse proxy, API gateway) or within the server application itself.
- For stdio transport (the default), rate limiting is less critical because the caller is the local IDE process. Focus rate limiting efforts on HTTP/SSE deployments.
- Return a descriptive error when rate limits are exceeded. Include a `Retry-After` hint if possible.

## Logging and Audit

Every MCP tool invocation should be logged to support incident investigation and governance compliance auditing.

### What to Log

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 timestamp of the invocation |
| `tool_name` | Name of the tool invoked (e.g., `check_policy`) |
| `parameters` | Tool input parameters (redact sensitive values if applicable) |
| `caller_identity` | Transport-level identity of the caller (token subject, client certificate DN, or local process) |
| `result_summary` | Success/error status and decision outcome (for `check_policy`) |
| `duration_ms` | Execution duration in milliseconds |

### Log Destination

- For local (stdio) deployments: log to stderr (consistent with the server's existing behavior).
- For production (HTTP/SSE) deployments: log to a structured logging pipeline (e.g., JSON lines to stdout, forwarded to a SIEM or log aggregator).
- Audit logs for `check_policy` invocations should be retained according to the organization's governance record retention policy, as they constitute policy evaluation evidence.

### Anomaly Detection

Monitor for patterns that suggest abuse:

- Sustained high-frequency `check_policy` calls from a single caller (oracle attack).
- `emissions_dir` values pointing outside the expected project directory (path traversal attempt).
- Bursts of `validate_emission` calls with incrementally modified payloads (schema probing).

## References

- [MCP Specification — Security Considerations](https://spec.modelcontextprotocol.io/specification/2025-03-26/security/) — Official MCP security guidance covering transport security, consent, and trust boundaries.
- [OWASP MCP Security Cheat Sheet](https://owasp.org/www-project-machine-learning-security-top-10/) — OWASP guidance on securing machine learning and AI tool integrations.
- [MCP Server Usage Guide](mcp-server-usage.md) — Installation, configuration, and content integrity validation for this MCP server.
- [Dark Forge Architecture](../../CLAUDE.md#architecture) — Five governance layers and the policy engine that `check_policy` invokes.
