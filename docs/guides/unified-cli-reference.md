# Unified CLI Reference

The `dark-governance` binary is a self-contained CLI that replaces the collection of shell scripts, Python modules, and Node tools previously required to run the governance platform.

---

## Installation

```bash
# macOS (Homebrew)
brew install SET-Apps/tap/dark-governance

# Go install
go install github.com/convergent-systems-co/dark-forge/src@latest

# curl script
curl -sSfL https://raw.githubusercontent.com/convergent-systems-co/dark-forge/main/src/scripts/install.sh | sh

# Specific version
curl -sSfL https://raw.githubusercontent.com/convergent-systems-co/dark-forge/main/src/scripts/install.sh | VERSION=0.1.0 sh
```

## Migration from Fragmented Tools

| Legacy Tool | Unified CLI Command | Notes |
|-------------|-------------------|-------|
| `git submodule add ... .ai && bash .ai/bin/init.sh` | `dark-governance install && dark-governance init` | No submodule required |
| `bash .ai/bin/init.sh --quick` | `dark-governance init` | Single command replaces submodule + init |
| `bash .ai/bin/init.sh --verify` | `dark-governance verify` | Lockfile integrity check |
| `bash .ai/bin/init.sh --refresh` | `dark-governance init --force` | Re-apply governance content |
| `python -m governance.engine.policy_engine` | `dark-governance engine run` | No Python required |
| `python -m governance.engine.orchestrator status` | `dark-governance engine status` | Embedded in binary |
| `bash .ai/bin/governance-status.sh` | `dark-governance engine status` | Richer output |
| `bash .ai/bin/update.sh` | `dark-governance update` | Version management |
| `bash .ai/bin/install-ide.sh` | `dark-governance ide setup` (planned) | Auto-detect + configure |
| `bash mcp-server/install.sh` | `dark-governance mcp install` (planned) | MCP server setup |
| `git submodule update --remote .ai` | `dark-governance update` | Binary self-update |

## Commands

### `dark-governance version`

Display the binary version, commit hash, and build date.

```bash
dark-governance version
dark-governance version --json
```

### `dark-governance install`

Extract embedded governance content to the home directory cache (`~/.ai/versions/<version>/`). This is the first step after downloading the binary.

```bash
dark-governance install                         # Install to ~/.ai/
dark-governance install --ci                    # CI mode ($RUNNER_TEMP/.ai/)
dark-governance install --force                 # Reinstall even if version exists
dark-governance install --json                  # JSON output
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--ci` | Use CI-appropriate home directory (`$RUNNER_TEMP/.ai/` or `$HOME/.ai/`) |
| `--force` | Reinstall even if the version already exists |

**Environment variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `DARK_GOVERNANCE_HOME` | Override the home directory location | `~/.ai` |
| `XDG_DATA_HOME` | XDG data directory (used as `$XDG_DATA_HOME/dark-governance`) | - |

### `dark-governance init`

Initialize governance in the current repository. Extracts CI workflows, CLAUDE.md, slash commands, directory structure, and writes a `.dark-governance.lock` lockfile.

```bash
dark-governance init                            # Initialize with defaults
dark-governance init --dry-run                  # Preview extraction plan
dark-governance init --force                    # Overwrite existing files
dark-governance init --language go              # Use Go project.yaml template
dark-governance init --json                     # JSON output
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would be extracted without writing files |
| `--force` | Overwrite existing files |
| `--language <lang>` | Language hint for project.yaml template (go, python, node, rust, terraform, bicep, csharp) |

**What gets created:**

| File/Directory | Description |
|----------------|-------------|
| `.github/workflows/dark-factory-governance.yml` | CI governance workflow (always updated) |
| `CLAUDE.md` | AI instructions (skip if exists) |
| `.claude/commands/*.md` | Slash commands (always updated) |
| `.artifacts/plans/` | Plan output directory |
| `.artifacts/panels/` | Panel review output directory |
| `.artifacts/checkpoints/` | Session checkpoint directory |
| `.artifacts/emissions/` | Panel emission directory |
| `project.yaml` | Project configuration (if `--language` specified, skip if exists) |
| `.dark-governance.lock` | Version pinning lockfile |

### `dark-governance verify`

Verify that the `.dark-governance.lock` file matches the running binary's content hash. Use this in CI to detect version drift.

```bash
dark-governance verify                          # Check default lockfile
dark-governance verify --lockfile path/to/lock  # Custom lockfile path
dark-governance verify --json                   # JSON output
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--lockfile <path>` | Path to lockfile (default: `.dark-governance.lock`) |

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Lockfile matches binary |
| 1 | Mismatch or lockfile not found |

### `dark-governance update`

Check for available governance updates and display installed versions.

```bash
dark-governance update                          # Check for updates
dark-governance update --json                   # JSON output
```

Currently reports installed versions and indicates whether the running binary is installed to the home cache. Automatic download will be added in a future release.

### `dark-governance engine run`

Evaluate panel emissions against an embedded policy profile.

```bash
dark-governance engine run                                              # Default: .artifacts/emissions/, default profile
dark-governance engine run --emissions-dir .governance/panels/ --profile fin_pii_high
dark-governance engine run --output manifest.json                       # Write manifest to file
dark-governance engine run --json                                       # JSON output
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--emissions-dir <path>` | Path to emissions directory (default: `.artifacts/emissions`) |
| `--profile <name>` | Policy profile to evaluate against (default: `default`) |
| `--output <path>` | Write manifest to file (default: stdout) |

**Available profiles:** `default`, `fast-track`, `fin_pii_high`, `infrastructure_critical`, `reduced_touchpoint`, `multi-model`

### `dark-governance engine status`

Display information about the embedded governance engine, including content counts and available policy profiles.

```bash
dark-governance engine status                   # Human-readable output
dark-governance engine status --json            # JSON output with full content listing
```

### `dark-governance docs`

Browse governance documentation online or offline.

```bash
dark-governance docs                                  # Open docs site in browser
dark-governance docs --offline                        # List available offline topics
dark-governance docs --offline guides/installation    # Read a topic in terminal pager
dark-governance docs --offline --json                 # JSON topic list
dark-governance --docs                                # Alias: open docs site from any command
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--offline` | Browse embedded docs in the terminal (no network required) |

**Offline mode** renders embedded documentation topics directly in the terminal using a pager (`$PAGER` -> `less` -> `more` -> stdout). A curated subset of ~18 high-value documentation topics is embedded in the binary.

**Online mode** (default, no flags) opens the documentation website at `https://set-apps.github.io/dark-forge` in your default browser.

The `--docs` flag is available as a persistent flag on the root command, so `dark-governance --docs` works as a quick shortcut from anywhere.

## Global Flags

These flags are available on all commands:

| Flag | Description |
|------|-------------|
| `--json` | Output in JSON format (machine-readable) |
| `--config <path>` | Path to project.yaml config file |
| `--docs` | Open governance documentation site in browser |
| `--help` | Show help for any command |

## JSON Output Mode

All commands support `--json` for machine-readable output. JSON output is sent to stdout; errors go to stderr. This makes the CLI suitable for scripting and CI pipelines.

```bash
# Parse with jq
dark-governance verify --json | jq '.status'
dark-governance engine status --json | jq '.content_counts'
dark-governance init --json | jq '.extracted'
```

## Typical Workflows

### New project setup

```bash
# 1. Install the binary (one-time)
brew install SET-Apps/tap/dark-governance

# 2. Initialize your repo
cd my-project
dark-governance init --language python

# 3. Verify
dark-governance verify
```

### CI pipeline

```bash
# In your CI workflow
dark-governance install --ci
dark-governance verify
dark-governance engine run --profile default --output manifest.json
```

### CLI-only developer (no IDE, no MCP)

```bash
# Initialize
cd my-project
dark-governance init --detect-language

# Check status
dark-governance engine status

# Run policy evaluation
dark-governance engine run

# Update governance
dark-governance update
```

### Updating governance

```bash
# Download new binary version, then:
dark-governance install --force
dark-governance init --force
dark-governance verify
```

## Architecture

The `dark-governance` binary embeds all governance content via Go's `go:embed` directive:

- Policy profiles (YAML)
- JSON Schemas (validation)
- Review panel prompts (Markdown)
- Agent personas (Markdown)
- Slash commands (Markdown)
- Workflow templates (YAML)
- Language-specific project.yaml templates
- Instructions (CLAUDE.md, instructions.md)
- Curated documentation (~18 high-value topics for offline browsing)

Content is extracted at install/init time and version-pinned via the lockfile. This eliminates the need for git submodules, Python venvs, or Node.js installations.

---

**See also:** [Developer Quickstart](developer-quickstart.md) | [E2E Testing](e2e-testing.md) | [Updating Guide](updating.md)
