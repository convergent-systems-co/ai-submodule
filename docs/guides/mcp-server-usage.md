# MCP Server Usage Guide

The `@jm-packages/dark-forge-mcp` server exposes governance prompts, review panels, policy profiles, and tools via the [Model Context Protocol](https://modelcontextprotocol.io/) (MCP). This allows any MCP-compatible IDE or AI assistant to access governance resources without directly reading the Dark Forge filesystem.

## Installation

### npx (recommended)

```bash
npx @jm-packages/dark-forge-mcp --governance-root /path/to/dark-forge
```

### From source

```bash
cd mcp-server
npm install
npm run build
node dist/index.js --governance-root /path/to/dark-forge
```

### Docker

```bash
cd mcp-server
npm run build
docker build -t dark-forge-mcp --build-arg GOVERNANCE_SRC=../governance .
docker run -i dark-forge-mcp
```

### Installer scripts

The installer scripts automatically configure Claude Code, VS Code, and Cursor:

**macOS / Linux:**
```bash
bash mcp-server/install.sh --governance-root /path/to/dark-forge
```

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File mcp-server\install.ps1 -GovernanceRoot C:\path\to\dark-forge
```

## CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--governance-root` | Auto-detected | Path to the repository root containing `governance/` |
| `--no-cache` | `false` | Disable resource caching (reload from disk on every request) |
| `--refresh` | `false` | Clear cached resources on startup |
| `--validate-hash` | `false` | Validate content integrity against stored SHA-256 hashes |
| `--offline` | `false` | Disable network requests (use only local resources) |

If `--governance-root` is not specified, the server walks up from its install location to find the `governance/` directory (works for both the Dark Forge repository itself and consuming repos with `.ai/governance/`).

## IDE Configuration

### Claude Code

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "dark-forge-mcp": {
      "command": "node",
      "args": ["/path/to/mcp-server/dist/index.js", "--governance-root", "/path/to/repo"]
    }
  }
}
```

### VS Code

Add to VS Code settings (`settings.json`):

```json
{
  "mcp.servers": {
    "dark-forge-mcp": {
      "command": "node",
      "args": ["/path/to/mcp-server/dist/index.js", "--governance-root", "/path/to/repo"]
    }
  }
}
```

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "dark-forge-mcp": {
      "command": "node",
      "args": ["/path/to/mcp-server/dist/index.js", "--governance-root", "/path/to/repo"]
    }
  }
}
```

## Available Resources

Resources are served as read-only content via `governance://` URIs.

### Review Prompts (20)

URI pattern: `governance://reviews/{panel-name}`

| URI | Description |
|-----|-------------|
| `governance://reviews/code-review` | Comprehensive code evaluation |
| `governance://reviews/security-review` | Security vulnerability analysis |
| `governance://reviews/threat-modeling` | STRIDE/MITRE ATT&CK threat analysis |
| `governance://reviews/cost-analysis` | Cost impact assessment |
| `governance://reviews/documentation-review` | Documentation completeness check |
| `governance://reviews/data-governance-review` | Data classification and handling |
| `governance://reviews/architecture-review` | Architecture pattern evaluation |
| `governance://reviews/performance-review` | Performance impact analysis |
| `governance://reviews/testing-review` | Test coverage evaluation |
| `governance://reviews/ai-expert-review` | AI/ML governance assessment |
| `governance://reviews/api-design-review` | API design quality |
| `governance://reviews/copilot-review` | AI assistant output review |
| `governance://reviews/data-design-review` | Data model evaluation |
| `governance://reviews/governance-compliance-review` | Governance pipeline compliance |
| `governance://reviews/incident-post-mortem` | Incident analysis |
| `governance://reviews/migration-review` | Migration safety review |
| `governance://reviews/production-readiness-review` | Production readiness gate |
| `governance://reviews/technical-debt-review` | Technical debt assessment |
| `governance://reviews/test-generation-review` | Test generation evaluation |
| `governance://reviews/threat-model-system` | System-level threat model |

### Workflow Templates (10)

URI pattern: `governance://workflows/{workflow-name}`

Includes: feature-implementation, bug-fix, refactoring, documentation, migration, api-design, architecture-decision, incident-response, acceptance-verification, and index.

### Personas (6)

URI pattern: `governance://personas/{persona-name}`

| URI | Description |
|-----|-------------|
| `governance://personas/project-manager` | Portfolio-level orchestrator (opt-in) |
| `governance://personas/tech-lead` | Pipeline orchestrator |
| `governance://personas/coder` | Implementation agent |
| `governance://personas/devops-engineer` | Session entry point and routing |
| `governance://personas/iac-engineer` | Infrastructure execution agent |
| `governance://personas/tester` | Independent evaluator |

### Shared Resources

| URI | Description |
|-----|-------------|
| `governance://shared/perspectives` | Shared perspective definitions |
| `governance://schemas/panel-output` | Panel output JSON schema |

### Policy Profiles (5)

URI pattern: `governance://policy/{profile-name}`

| URI | Description |
|-----|-------------|
| `governance://policy/default` | Standard risk tolerance, auto-merge enabled |
| `governance://policy/fin_pii_high` | SOC2/PCI-DSS/HIPAA/GDPR compliance |
| `governance://policy/infrastructure_critical` | Mandatory architecture and SRE review |
| `governance://policy/fast-track` | Lightweight profile for trivial changes |
| `governance://policy/reduced_touchpoint` | Near-full autonomy |

## Available Tools

### validate_emission

Validate a panel emission JSON against the `panel-output.schema.json` schema.

**Parameters:**
- `emission_json` (string, required): The JSON string to validate

**Returns:** `{valid: boolean, errors?: string[]}`

### check_policy

Run the policy engine against a directory of panel emissions.

**Parameters:**
- `emissions_dir` (string, required): Path to the emissions directory
- `profile` (string, default: "default"): Policy profile name

**Returns:** `{decision: string, details: string}`

**Note:** Requires Python 3 to be available on PATH.

### generate_name

Generate a compliant Azure resource name.

**Parameters:**
- `resource_type` (string, required): Azure resource type (e.g., `Microsoft.KeyVault/vaults`)
- `lob` (string, required): Line of business code
- `stage` (string, required): Deployment stage (dev, staging, prod)
- `app_name` (string, required): Application name
- `app_id` (string, required): Application identifier

**Returns:** `{name: string}` or `{error: string}`

**Note:** Requires Python 3 to be available on PATH.

### list_panels

List all available governance review panels.

**Returns:** Array of `{name, description, uri}`

### list_policy_profiles

List available policy profiles dynamically discovered from `governance/policy/`.

**Returns:** Array of `{name, description, version, path}`

### create_plan

Create an implementation plan in `.artifacts/plans/`.

**Parameters:**
- `plan_name` (string, required): Plan filename without extension (e.g., `42-fix-auth-flow`)
- `content` (string, required): Markdown content for the plan

**Returns:** `{success: boolean, path?: string, error?: string}`

### write_emission

Write a validated panel emission to `.artifacts/panels/`. Validates against the panel-output schema before writing.

**Parameters:**
- `panel_name` (string, required): Panel name (e.g., `code-review`, `security-review`)
- `emission_json` (string, required): The emission JSON string to validate and write

**Returns:** `{success: boolean, valid: boolean, path?: string, errors?: string[]}`

### read_checkpoint

Read the latest governance checkpoint from `.artifacts/checkpoints/`.

**Returns:** `{found: boolean, file?: string, checkpoint?: object}`

### get_governance_status

Get an aggregate view of the project's governance posture.

**Returns:** `{governance_root, emissions_count, plans_count, checkpoints_count, project_yaml_found, available_profiles}`

### validate_project_yaml

Validate `project.yaml` against the project schema.

**Parameters:**
- `yaml_path` (string, optional): Path to project.yaml (defaults to project root)

**Returns:** `{valid: boolean, error?: string, path?: string[]}`

**Note:** Requires Python 3 with `jsonschema` and `pyyaml` installed.

### health_check

Verify the MCP server's health: governance root, Python availability, required directories, and schema files.

**Returns:** `{server, governance_root, governance_root_exists, directories, python_available, python_version, policy_engine_available, panel_schema_available}`

### list_personas

List all available agentic personas with their descriptions and prompt references.

**Returns:** Array of `{name, description, uri, prompt}`

### search_catalog

Search the governance prompt and resource catalog by keyword.

**Parameters:**
- `query` (string, required): Search keyword(s)
- `category` (string, optional): Filter by category: reviews, personas, policies, workflows, prompts

**Returns:** `{query, count, results: [{name, description, uri, category}]}`

## Azure DevOps Integration

The MCP server can expose Azure DevOps work item operations through both the `ado` skill and a Python client library at `governance/integrations/ado/`.

### Configuration

Add `ado_integration` to your `project.yaml`:

```yaml
ado_integration:
  organization: my-org              # Required — ADO org name
  default_project: My Project       # Default project for API calls
  auth_method: pat                  # pat | service_principal | managed_identity
  api_version: "7.1"               # ADO REST API version
  max_retries: 5                   # Retry attempts for transient failures
  timeout: 30.0                    # HTTP timeout in seconds
```

### Authentication

Set credentials via environment variables:

| Auth Method | Environment Variables |
|-------------|----------------------|
| `pat` | `ADO_PAT` |
| `service_principal` | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |
| `managed_identity` | `AZURE_CLIENT_ID` (optional) |

PAT auth uses only `requests`. Service Principal and Managed Identity lazily import `azure-identity` — it is not required for PAT-only usage.

### Client Library

The Python client library (`governance/integrations/ado/`) provides:

| Category | Methods |
|----------|---------|
| **Work Items** | `create_work_item()`, `get_work_item()`, `update_work_item()`, `delete_work_item()`, `get_work_items_batch()` |
| **WIQL** | `query_wiql()`, `query_wiql_with_details()` |
| **Comments** | `get_comments()`, `add_comment()` — HTML only, not Markdown |
| **Classification** | `list_area_paths()`, `list_iteration_paths()` |
| **Fields & Types** | `list_fields()`, `create_field()`, `list_work_item_types()` |
| **Project Inspection** | `get_work_item_type_states()`, `get_project_properties()` |
| **Patch Builder** | `add_field()`, `replace_field()`, `add_tag()`, `add_github_pr_link()`, `add_github_commit_link()`, `add_hyperlink()`, `remove_relation()` |

Usage:

```python
from governance.integrations.ado import AdoClient, AdoConfig, create_auth_provider

config = AdoConfig(organization="myorg", default_project="myproject")
auth = create_auth_provider("pat", pat="my-token")

with AdoClient(config, auth) as client:
    wi = client.get_work_item(42)
    states = client.get_work_item_type_states("Bug")
    client.add_comment(42, "<p>Status update from governance pipeline</p>")
```

### Project Inspection

ADO projects can have custom processes with different states, fields, and work item types. Always inspect the project before making assumptions:

```python
# Discover the process template (Agile, Scrum, CMMI, or custom)
props = client.get_project_properties()
template = props["capabilities"]["processTemplate"]["templateName"]

# Get valid states for a work item type in this project
states = client.get_work_item_type_states("User Story")
# May return custom states like "Ready", "In Development" instead of defaults
```

### Dependencies

Install the ADO client:

```bash
# Standalone (from governance/integrations/ado/)
pip install -e .

# With azure-identity for Service Principal / Managed Identity
pip install -e ".[azure]"

# Or via the engine's optional group
pip install -e ".[ado]"    # from governance/engine/
```

### MCP Skill

The `ado` skill (`mcp-server/skills/ado.skill.md`) exposes ADO operations as an MCP tool. It provides guided instructions for work item CRUD, WIQL queries, comment posting, GitHub linking, and project inspection using the client library.

### GitHub Artifact Links

Link GitHub resources to ADO work items:

| Link Type | ADO Section | Helper |
|-----------|-------------|--------|
| Pull Request | Development | `add_github_pr_link(connection_id, pr_number)` |
| Commit (full SHA) | Development | `add_github_commit_link(connection_id, commit_sha)` |
| Branch / Issue | Links tab | `add_hyperlink(url, comment)` |

The `connection_id` is the GitHub service connection GUID configured in your ADO organization. Discover it by inspecting an existing artifact link on any work item.

## Available Prompts

### governance_review

Run a governance review panel. Loads the full review prompt content for the specified panel.

**Arguments:**
- `panel_name` (string, required): Name of the review panel (e.g., `code-review`, `security-review`)

### plan_create

Create an implementation plan using the governance plan template.

**Arguments:** None

### threat_model

Perform threat modeling analysis using the threat modeling prompt.

**Arguments:** None

## Hybrid Fetch System

The MCP server uses a hybrid fetch strategy for loading governance resources:

1. **Local filesystem** (primary) — Reads directly from the governance root directory
2. **Cached content** — Stores parsed resources in memory for fast repeated access
3. **Hash validation** — Optional integrity checking via `--validate-hash` using SHA-256 digests from the prompt catalog

The `--offline` flag restricts the server to local resources only, useful for air-gapped environments.

## Install Subcommand

The `install.sh` script automatically configures MCP server entries for supported IDEs:

```bash
bash mcp-server/install.sh --governance-root /path/to/repo
```

**What it configures:**

| IDE | Configuration File | Server Key |
|-----|-------------------|------------|
| Claude Code | `~/.claude.json` (workspace) | `dark-forge-mcp` |
| VS Code | `.vscode/settings.json` | `mcp.servers.dark-forge-mcp` |
| Cursor | `~/.cursor/mcp.json` | `dark-forge-mcp` |

The installer validates Node.js availability and the built server (`dist/index.js`) before configuring. It generates the correct args array with the governance root path and merges it into existing IDE settings without overwriting other configuration.

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File mcp-server\install.ps1 -GovernanceRoot C:\path\to\repo
```

## Skills

Skills are self-contained capabilities exposed as MCP tools. Each skill is a `.skill.md` file in `mcp-server/skills/` with YAML frontmatter defining its name, description, and allowed tools.

**Available skills:**

| Skill | Description | Allowed Tools |
|-------|-------------|---------------|
| `governance-review` | Run governance panel reviews against code changes | Read, Glob, Grep, Bash |
| `ado` | Azure DevOps work item operations (query, create, update, comment, link) | Read, Bash, Grep |

**Skill tool input schema:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task` | string | Yes | The specific task to perform |
| `context` | string | No | Additional context |
| `output_format` | string | No | Desired output format |

See [Skills Development Guide](skills-development.md) for creating new skills.

## Content Integrity

The server provides manifest generation for integrity validation:

```typescript
import { generateManifest, validateManifest } from "./manifest.js";

const manifest = await generateManifest("/path/to/governance-root");
// manifest.files: [{path, hash (SHA-256), size}]
// manifest.generated_at: ISO 8601 timestamp

const result = await validateManifest("/path/to/governance-root", storedManifest);
// result.valid: boolean
// result.mismatches: [{path, expected, actual, reason}]
```

## Development

```bash
cd mcp-server
npm install
npm run build         # Compile TypeScript
npm test              # Run test suite
npm run test:watch    # Run tests in watch mode
```

## Troubleshooting

### "Could not find governance/ directory"

The server could not auto-detect the governance root. Pass `--governance-root` explicitly:

```bash
node dist/index.js --governance-root /path/to/dark-forge
```

### Python tools return errors

The `check_policy` and `generate_name` tools require Python 3 on PATH. Install Python 3 and ensure it is accessible as `python3` (Unix) or `python` (Windows).

### Server starts but no resources appear

Verify the governance root contains the expected directory structure:

```
governance/
  prompts/reviews/     (20 .md files)
  prompts/workflows/   (10 .md files)
  personas/agentic/    (6 .md files)
  policy/              (4 primary .yaml files)
  schemas/             (panel-output.schema.json)
```

## Security

The MCP server exposes governance tools that influence merge decisions and policy evaluation. Securing this surface is essential to maintaining governance integrity. Key concerns include:

- **Tool classification** — Tools are classified as read-only (`list_panels`, `list_policy_profiles`, `validate_emission`) or action (`check_policy`, `generate_name`). Action tools spawn subprocesses and accept filesystem paths, requiring stricter controls.
- **Confused deputy attacks** — The `check_policy` tool accepts an `emissions_dir` filesystem path and invokes a Python subprocess. Without path validation, a caller could read files outside the project boundary.
- **Policy oracle attacks** — Repeated `check_policy` invocations with crafted emissions could reverse-engineer passing patterns.
- **Rate limiting** — Action tools should be rate-limited, especially `check_policy` (recommended: 10 requests/minute).
- **Audit logging** — All tool invocations should be logged with caller identity, parameters, and outcomes.

For comprehensive guidance including token scoping, confused deputy mitigations, rate limit recommendations, and audit requirements, see the [MCP Security Guidelines](mcp-security-guidelines.md).
