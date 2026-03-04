# CLAUDE.md

Guidance for Claude Code working in this repository.

## What This Is

**Dark Forge** — AI governance framework for autonomous software delivery, distributed as a git submodule (`.ai/`) to consuming repos. No application source code; entirely configuration, policy, schemas, and documentation. Phase 4b maturity.

## Commands

### Unified CLI (`dark-governance`)

```bash
# Consumer repo setup
dark-governance install                         # Extract content to home cache
dark-governance init                            # Scaffold governance in current repo
dark-governance init --language go              # With language-specific project.yaml
dark-governance verify                          # Check lockfile integrity

# Governance engine
dark-governance engine run                      # Evaluate emissions against policy
dark-governance engine run --profile fin_pii_high  # Specific policy profile
dark-governance engine status                   # Show engine info + embedded content

# Environment verification
dark-governance verify-environment              # Check repo state against delivery intent
dark-governance verify-environment --output json # JSON output for CI
dark-governance verify-environment --fix        # Auto-fix missing directories

# Maintenance
dark-governance update                          # Check for updates
dark-governance version                         # Show binary version
```

See `docs/guides/unified-cli-reference.md` for the full CLI reference.

> **Migrating from submodule?** See [Migration Guide](docs/guides/migration-submodule-to-binary.md) for step-by-step instructions.

### Legacy tools (submodule-based)

```bash
# Bootstrap (consuming repos)
bash .ai/bin/init.sh                            # Shell bootstrap
bash .ai/bin/init.sh --refresh                  # Re-apply after submodule update
bash .ai/bin/init.sh --check-branch-protection  # Query branch protection
bash .ai/bin/init.sh --verify                   # Verify installation

# Policy engine (Python)
python -m governance.engine.policy_engine       # Run policy evaluation
python -m governance.engine.orchestrator status  # Orchestrator status

# Auto-clear wrapper (continuous operation)
bash bin/auto-clear.sh                          # Default: 50 retries
bash bin/auto-clear.sh --max-retries 10         # Custom limit

# MCP server
bash mcp-server/install.sh --governance-root /path/to/repo
```

### Development

```bash
# Tests (policy engine)
python -m pytest governance/engine/ -x --tb=short

# Orchestrator CLI (step-based control plane)
python -m governance.engine.orchestrator init --config project.yaml
python -m governance.engine.orchestrator step --complete 1 --result '{"issues_selected": ["#42"]}'
python -m governance.engine.orchestrator signal --type tool_call --count 5
python -m governance.engine.orchestrator gate --phase 3
python -m governance.engine.orchestrator status

# Or agentic: "Read and execute .ai/governance/prompts/init.md"

# Azure naming
python bin/generate-name.py --resource-type Microsoft.KeyVault/vaults --lob set --stage dev --app-name myapp --app-id a

# Package governance engine for distribution
bash governance/bin/vendor-engine.sh --package   # Creates .artifacts/dist/governance-engine-{ver}.tar.gz

# Go CLI (dark-governance binary)
cd src && make build       # Build dark-governance binary with version injection
cd src && make test        # Run Go tests
cd src && make test-e2e    # Run VHS end-to-end tests
cd src && make vet         # Run go vet
cd src && make lint        # Run golangci-lint (requires golangci-lint installed)
cd src && make all         # Default target (build)
cd src && make clean       # Remove build artifacts
```

**Cross-org CI**: Consuming repos that cannot clone the private submodule can use the reusable governance-check action. See `docs/guides/cross-org-ci-integration.md`.

## Key Conventions

- **Commit style**: Conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`)
- **Branch naming**: `NETWORK_ID/{issue-type}/{issue-number}/{branch-name}`
- **Plans before code**: Every implementation requires a plan in `.artifacts/plans/`
- **Governance pipeline mandatory**: Required panels must execute on every change
- **`jm-compliance.yml` is enterprise-locked**: Never modify
- **Manifests are immutable**: Never edit after creation
- **Slash commands**: `/startup` begins the agentic loop, `/checkpoint` saves state

## Architecture (Summary)

Five governance layers: Intent → Cognitive → Execution → Runtime → Evolution. See `docs/architecture/governance-model.md`.

Nine agentic personas in `governance/personas/agentic/`: Project Manager, DevOps Engineer, Tech Lead, Coder, IaC Engineer, Test Evaluator, Document Writer, Documentation Reviewer. Protocol: `governance/prompts/agent-protocol.md`. See `docs/architecture/agent-architecture.md`.

21 review prompts in `governance/prompts/reviews/`. Five policy profiles and 4 supporting policy configurations in `governance/policy/`, plus 14 future Phase 5 configurations in `governance/policy/future/`. Panel output validated against `governance/schemas/panel-output.schema.json`.

**Tiered evaluation**: Governance runs at Tier 1 (full policy engine) or Tier 2 (lightweight inline fallback) depending on engine availability. Controlled by `governance.evaluation_tier` in `project.yaml` (`auto`/`full`/`lightweight`). See `docs/architecture/governance-model.md` section 15.

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
| `.artifacts/plans/` | Implementation plans (emitted) |
| `.artifacts/panels/` | Panel review reports (emitted) |
| `.artifacts/checkpoints/` | Session checkpoints (emitted) |
| `.artifacts/delivery-intents/` | Delivery intent manifests (emitted by document-writer) |
| `.artifacts/state/sessions/` | Orchestrator session state (persisted) |
| `docs/` | Architecture, compliance, guides, onboarding |
| `mcp-server/` | MCP server + skills |
| `prompts/global/` | 12 developer prompts |
| `src/` | Go CLI binary source (`dark-governance`) |

## Agentic Startup

The Python orchestrator is the sole control plane. The LLM calls `python -m governance.engine.orchestrator` between phases; state survives context resets on disk.

Standard mode phases: Pre-flight → Plan all → Parallel dispatch (N Coders in worktrees) → Collect + Review → Merge. N = `governance.parallel_coders` (default 5, -1 for unlimited). See `governance/prompts/startup.md`.

PM mode (opt-in): Project Manager → DevOps Engineer (background) → M Tech Leads → N Coders each. See `docs/architecture/project-manager-architecture.md`.
