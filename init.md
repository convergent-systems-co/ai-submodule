# Initialize Dark Forge

> **Two installation paths:**
> - **Primary (AI-assisted):** Tell your assistant: "Read and execute `.ai/governance/prompts/init.md`"
> - **Fallback (script):** `bash .ai/bin/init.sh` (this guide)

This guide covers setting up the Dark Forge as a git submodule in your project.

## Quick Start (One Command)

```bash
# Add submodule + run full init (uses HTTPS — works across orgs)
bash .ai/bin/init.sh --quick

# With Python dependencies and MCP server
bash .ai/bin/init.sh --quick --install-deps --mcp
```

## Standard Setup

### 1. Add the Submodule

```bash
git submodule add https://github.com/convergent-systems-co/dark-forge.git .ai
```

### 2. Run the Bootstrap Script

```bash
bash .ai/bin/init.sh
```

This creates symlinks in your project root:
- `CLAUDE.md` -> `.ai/instructions.md` (Claude Code instructions)
- `.github/copilot-instructions.md` -> `.ai/instructions.md` (GitHub Copilot instructions)

### 3. Optional: Install Dependencies

```bash
bash .ai/bin/init.sh --install-deps    # Python venv + governance dependencies
bash .ai/bin/init.sh --mcp             # MCP server for IDE integration
```

### 4. Commit the Submodule

```bash
git add .ai .gitmodules CLAUDE.md .github/copilot-instructions.md
git commit -m "chore: add Dark Forge governance submodule"
```

## Updating the Submodule

```bash
git submodule update --remote .ai
bash .ai/bin/init.sh --refresh
```

The `--refresh` flag re-applies structural setup (symlinks, workflows, directories, CODEOWNERS, repo settings) while skipping the submodule freshness check. It is idempotent — a no-op when nothing has changed. The agentic startup loop runs this automatically.

## Uninstalling

```bash
bash .ai/bin/init.sh --uninstall
```

This removes symlinks, the virtual environment, and provides instructions for full submodule removal.

## Available Flags

| Flag | Purpose |
|------|---------|
| `--quick` | Add submodule (HTTPS) + full init |
| `--install-deps` | Install Python venv and dependencies |
| `--mcp` | Install MCP server for IDE integration |
| `--refresh` | Re-apply setup after submodule update |
| `--uninstall` | Clean removal of governance artifacts |
| `--verify` | Verify installation is complete |
| `--check-branch-protection` | Query branch protection status |
| `--dry-run` | Preview changes without applying |
| `--debug` | Verbose output for troubleshooting |

## What's Included

| Directory | Contents |
|-----------|----------|
| `governance/prompts/reviews/` | 21 consolidated review prompts (canonical location for all reviews) |
| `governance/personas/agentic/` | 7 agentic personas (Project Manager, DevOps Engineer, Team Lead, Coder, IaC Engineer, Tester, Document Writer) |
| `governance/policy/` | 5 deterministic policy profiles (default, fin_pii_high, infrastructure_critical, fast-track, reduced_touchpoint) |
| `governance/schemas/` | JSON schemas for structured emissions and panel configuration |
| `governance/prompts/` | Workflow prompts, templates (plan, runtime DI), startup loop |
| `docs/` | Architecture docs, context management, governance model |
| `mcp-server/` | MCP server for IDE prompt distribution |

## Configuration

- **`config.yaml`** — Defines symlinks created by `init.sh`
- **`panels.local.json`** — Optional per-project panel overrides (place in your project root). See `governance/schemas/panels.schema.json` for the format.
- **`instructions.md`** — Base instructions distributed to all AI tools via symlinks

## Next Steps

- Read [`governance/prompts/startup.md`](governance/prompts/startup.md) for the agentic improvement loop
- Review [`GOALS.md`](GOALS.md) for project roadmap
- See [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) for architecture overview
