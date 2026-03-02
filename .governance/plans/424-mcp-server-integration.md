# MCP Server for IDE-Agnostic Governance Distribution

**Author:** Code Manager (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** [#424](https://github.com/SET-Apps/ai-submodule/issues/424)
**Branch:** `NETWORK_ID/feat/424/mcp-server-integration`

---

## 1. Objective

Add a TypeScript STDIO MCP server to the ai-submodule that serves governance prompts, review panels, and policy tools to any MCP-compatible IDE (VS Code, Claude Code, Cursor, JetBrains) without requiring the full git submodule setup.

## 2. Rationale

The ai-submodule's governance prompts and tools are currently only accessible via the filesystem after submodule installation. An MCP server provides IDE-agnostic distribution, lowering the adoption barrier and enabling prompt access for repos that don't use the submodule.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| REST API server | Yes | Requires persistent hosting; STDIO is zero-infrastructure |
| VS Code extension only | Yes | Lock-in to single IDE; MCP is multi-IDE by design |
| npm package (no MCP) | Yes | No IDE integration; MCP provides native tool/resource protocol |
| Embed in init.sh only | Yes | No dynamic serving; static copies go stale |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `mcp-server/package.json` | npm package config (`@jm-packages/ai-submodule-mcp`) |
| `mcp-server/tsconfig.json` | TypeScript compilation config |
| `mcp-server/src/index.ts` | Server entry point — STDIO transport, resource/tool/prompt registration |
| `mcp-server/src/resources.ts` | MCP resource handlers — serves review prompts, workflows, personas, perspectives, policy summaries |
| `mcp-server/src/tools.ts` | MCP tool handlers — validate_emission, check_policy, generate_name, list_panels, list_policy_profiles |
| `mcp-server/src/prompts.ts` | MCP prompt handlers — governance_review, plan_create, threat_model |
| `mcp-server/src/manifest.ts` | Content hash manifest generation and integrity validation |
| `mcp-server/src/utils.ts` | Shared utilities (frontmatter parsing, file discovery, path resolution) |
| `mcp-server/install.sh` | macOS/Linux installer — configures Claude Code, VS Code, Cursor |
| `mcp-server/install.ps1` | Windows installer — configures Claude Code, VS Code, Cursor |
| `mcp-server/Dockerfile` | Container image for GHCR distribution |
| `mcp-server/.dockerignore` | Docker build exclusions |
| `mcp-server/tests/index.test.ts` | Integration tests for server startup and resource listing |
| `mcp-server/tests/tools.test.ts` | Unit tests for tool handlers |
| `mcp-server/tests/resources.test.ts` | Unit tests for resource handlers |
| `docs/guides/mcp-server-usage.md` | User-facing documentation |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `config.yaml` | Add `mcp_server` section with package name, version, registry config |
| `bin/init.sh` | Add `--install-mcp` flag to configure MCP server in consuming repos |
| `bin/init.ps1` | Add `--install-mcp` flag (Windows equivalent) |
| `CLAUDE.md` | Add MCP server section to repository commands |
| `README.md` | Add MCP server to distribution options |
| `GOALS.md` | Update with MCP server milestone |

### Files to Delete

None — this is purely additive.

## 4. Approach

### Step 1: Scaffold MCP server package

Create `mcp-server/` directory with TypeScript project structure:
- `package.json` with dependencies: `@modelcontextprotocol/sdk` (^1.26.0), `gray-matter` (^4.0.3), `zod` (^3.22.0)
- Dev dependencies: `typescript`, `@types/node`, `vitest`
- `tsconfig.json` targeting ES2022 with NodeNext module resolution
- `bin` entry point in package.json for `npx` execution

### Step 2: Implement resource serving (`resources.ts`)

Serve governance files as MCP resources:
- Scan `governance/prompts/reviews/*.md` → 20 review panel resources
- Scan `governance/prompts/workflows/*.md` → 10 workflow template resources
- Scan `governance/personas/agentic/*.md` → 5 persona resources
- Serve `governance/prompts/shared-perspectives.md` → 1 shared perspectives resource
- Scan `governance/policy/{default,fin_pii_high,infrastructure_critical,fast-track,reduced_touchpoint}.yaml` → 5 policy summary resources
- Parse frontmatter with `gray-matter` for metadata (name, description, version)
- Each resource has a URI: `governance://reviews/{name}`, `governance://workflows/{name}`, etc.

### Step 3: Implement tool handlers (`tools.ts`)

5 MCP tools:
1. **`validate_emission`** — Accept JSON string, validate against `governance/schemas/panel-output.schema.json` using `ajv` or JSON Schema validation. Return validation result.
2. **`check_policy`** — Accept emissions directory path and profile name. Spawn `python governance/bin/policy-engine.py --dry-run` subprocess. Return decision.
3. **`generate_name`** — Accept resource-type, lob, stage, app-name, app-id. Spawn `python bin/generate-name.py` subprocess. Return name.
4. **`list_panels`** — Return array of panel metadata (name, description, version) from scanned review files.
5. **`list_policy_profiles`** — Return array of policy profile summaries (name, description, risk tolerance, auto-merge settings).

### Step 4: Implement prompt handlers (`prompts.ts`)

3 MCP prompts:
1. **`governance_review`** — Accepts `panel_name` argument. Returns the full review prompt content for the specified panel.
2. **`plan_create`** — Returns the plan template content from `governance/prompts/templates/plan-template.md`.
3. **`threat_model`** — Returns the threat modeling prompt content.

### Step 5: Implement manifest and integrity (`manifest.ts`)

- Generate SHA-256 content hashes for all served resources
- Store in `mcp-server/manifest.json` (generated at build time)
- Validate file integrity on server startup
- Log warnings for hash mismatches (indicates unauthorized modification)

### Step 6: Implement server entry point (`index.ts`)

- Create `McpServer` instance with STDIO transport
- Register all resources, tools, and prompts
- Handle graceful shutdown
- Resolve governance file paths relative to the package install location
- Support `--governance-root` flag to override path (for development/testing)

### Step 7: Installer scripts

- `install.sh` (macOS/Linux): Detect installed IDEs, write MCP config to appropriate locations
  - Claude Code: `~/.claude.json` → add `mcpServers` entry
  - VS Code: `~/.vscode/settings.json` → add MCP config
  - Cursor: `~/.cursor/mcp.json` → add server entry
- `install.ps1` (Windows): Same logic with PowerShell and Windows paths

### Step 8: Docker distribution

- `Dockerfile`: Node.js alpine base, copy built server, expose STDIO
- Publish to `ghcr.io/set-apps/ai-submodule-mcp`

### Step 9: Integration with init.sh

- Add `--install-mcp` flag to `bin/init.sh` and `bin/init.ps1`
- When invoked: run `npx @jm-packages/ai-submodule-mcp install` or fall back to manual config
- Non-blocking — MCP installation is optional

### Step 10: Documentation and tests

- Write `docs/guides/mcp-server-usage.md` covering: installation, configuration, available resources/tools/prompts, development setup
- Write integration tests using vitest: server startup, resource listing, tool execution, prompt retrieval
- Update `CLAUDE.md`, `README.md`, and `GOALS.md`

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `tools.ts`, `resources.ts`, `prompts.ts`, `manifest.ts` | Individual handler correctness, schema validation, file parsing |
| Integration | `index.ts` (full server) | Server startup, STDIO transport, resource/tool/prompt registration and invocation |
| E2E | Install scripts | Installer creates correct config files for each IDE |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MCP SDK API changes | Low | Medium | Pin to specific version, lock file |
| Governance file path resolution | Medium | Low | Use `__dirname` relative paths, `--governance-root` override |
| Python subprocess unavailability | Low | Medium | Tools that require Python gracefully degrade with clear error |
| Large file serving performance | Low | Low | Files are small markdown; lazy loading if needed |
| Security — serving sensitive policy data | Low | Medium | Policy summaries are read-only; no secrets in governance files |

## 7. Dependencies

- [x] `@modelcontextprotocol/sdk` >= 1.26.0 — non-blocking (npm)
- [x] `gray-matter` >= 4.0.0 — non-blocking (npm)
- [x] `zod` >= 3.22.0 — non-blocking (npm)
- [x] Node.js >= 18 — non-blocking (runtime)
- [ ] npm publishing access to `@jm-packages` scope — blocking for distribution (can develop without)
- [ ] GHCR publishing access — blocking for Docker distribution (can develop without)

## 8. Backward Compatibility

Fully backward compatible. This is an additive feature — no existing files, APIs, or behaviors are modified. The MCP server is an optional distribution mechanism alongside the existing submodule installation.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New TypeScript module with 8+ source files |
| security-review | Yes | Always required; subprocess spawning and file serving |
| threat-modeling | Yes | Always required; new distribution surface |
| cost-analysis | Yes | Always required; npm/Docker hosting costs |
| documentation-review | Yes | Always required; new user-facing docs |
| data-governance-review | Yes | Always required; governance data distribution |
| architecture-review | Yes | New distribution layer for the platform |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | STDIO transport over HTTP | Zero infrastructure requirement; standard MCP pattern |
| 2026-02-27 | TypeScript over Python | MCP SDK is TypeScript-native; matches awesome-dach-copilot pattern |
| 2026-02-27 | vitest over jest | Faster, native ESM support, lighter config |
| 2026-02-27 | Subprocess for Python tools | Policy engine and naming CLI remain Python; no port needed |
