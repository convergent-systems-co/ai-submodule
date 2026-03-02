# CLAUDE.md

Guidance for Claude Code working in this repository.

## What This Is

**Dark Factory Governance Platform** — AI governance framework for autonomous software delivery, distributed as a git submodule (`.ai/`) to consuming repos. No application source code; entirely configuration, policy, schemas, and documentation. Phase 4b maturity.

## Commands

```bash
# Tests (policy engine)
python -m pytest governance/engine/ -x --tb=short

# Orchestrator CLI (step-based control plane)
python -m governance.engine.orchestrator init --config project.yaml
python -m governance.engine.orchestrator step --complete 1 --result '{"issues_selected": ["#42"]}'
python -m governance.engine.orchestrator signal --type tool_call --count 5
python -m governance.engine.orchestrator gate --phase 3
python -m governance.engine.orchestrator status

# Auto-clear wrapper (continuous operation)
bash bin/auto-clear.sh                          # Default: 50 retries
bash bin/auto-clear.sh --max-retries 10         # Custom limit

# Bootstrap (consuming repos)
bash .ai/bin/init.sh                            # Shell bootstrap
bash .ai/bin/init.sh --refresh                  # Re-apply after submodule update
bash .ai/bin/init.sh --check-branch-protection  # Query branch protection
bash .ai/bin/init.sh --verify                   # Verify installation

# Or agentic: "Read and execute .ai/governance/prompts/init.md"

# Azure naming
python bin/generate-name.py --resource-type Microsoft.KeyVault/vaults --lob set --stage dev --app-name myapp --app-id a

# MCP server
bash mcp-server/install.sh --governance-root /path/to/repo
```

## Key Conventions

- **Commit style**: Conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`)
- **Branch naming**: `NETWORK_ID/{issue-type}/{issue-number}/{branch-name}`
- **Plans before code**: Every implementation requires a plan in `.governance/plans/`
- **Governance pipeline mandatory**: Required panels must execute on every change
- **`jm-compliance.yml` is enterprise-locked**: Never modify
- **Manifests are immutable**: Never edit after creation
- **Slash commands**: `/startup` begins the agentic loop, `/checkpoint` saves state

## Architecture (Summary)

Five governance layers: Intent → Cognitive → Execution → Runtime → Evolution. See `docs/architecture/governance-model.md`.

Six agentic personas in `governance/personas/agentic/`: Project Manager, DevOps Engineer, Code Manager, Coder, IaC Engineer, Tester. Protocol: `governance/prompts/agent-protocol.md`. See `docs/architecture/agent-architecture.md`.

21 review prompts in `governance/prompts/reviews/`. Five policy profiles and 18 supporting policy configurations in `governance/policy/`. Panel output validated against `governance/schemas/panel-output.schema.json`.

**Context management**: Hard stop at 80% capacity. Four-tier model (Green/Yellow/Orange/Red). See `docs/architecture/context-management.md`.

## Key Directories

| Path | Purpose |
|------|---------|
| `governance/personas/agentic/` | Agent persona definitions |
| `governance/prompts/reviews/` | 21 review panel prompts |
| `governance/prompts/` | Operational prompts (startup, init, protocol) |
| `governance/policy/` | Deterministic YAML policy profiles |
| `governance/schemas/` | JSON Schema enforcement artifacts |
| `governance/engine/` | Policy engine + orchestrator (Python) |
| `governance/integrations/ado/` | Azure DevOps client library |
| `.governance/plans/` | Implementation plans (emitted) |
| `.governance/panels/` | Panel review reports (emitted) |
| `.governance/checkpoints/` | Session checkpoints (emitted) |
| `.governance/state/sessions/` | Orchestrator session state (persisted) |
| `docs/` | Architecture, compliance, guides, onboarding |
| `mcp-server/` | MCP server + skills |
| `prompts/global/` | 12 developer prompts |

## Agentic Startup

The Python orchestrator is the sole control plane. The LLM calls `python -m governance.engine.orchestrator` between phases; state survives context resets on disk.

Standard mode phases: Pre-flight → Plan all → Parallel dispatch (N Coders in worktrees) → Collect + Review → Merge. N = `governance.parallel_coders` (default 5, -1 for unlimited). See `governance/prompts/startup.md`.

PM mode (opt-in): Project Manager → DevOps Engineer (background) → M Code Managers → N Coders each. See `docs/architecture/project-manager-architecture.md`.
