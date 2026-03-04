# Plan: Ship dark-governance One-Binary Installer

**Issue:** #738
**Branch:** `itsfwcp/feat/738/one-binary-installer`
**Type:** feat

## Problem

The dark-governance CLI has its core subcommands (install, init, update, verify, engine) but is missing several utility commands needed for a complete one-binary installer experience: dependency management (Python venv for engine bridge), MCP server installation, interactive configuration, and clean uninstallation.

The install.sh script also lacks checksum verification and Cosign verification stubs.

## Solution

### 1. New Go Commands

#### `deps_cmd.go` -- `deps setup`

Manages the Python virtual environment needed to bridge to the Python policy engine:

```
dark-governance deps setup [--python PATH] [--force]
dark-governance deps status
```

- Creates a venv at `~/.ai/venv/` (or `DARK_GOVERNANCE_HOME/venv/`)
- Installs `pyyaml` (minimum dependency for engine bridge)
- Reports venv path, Python version, installed packages
- `--force` recreates even if exists
- `status` subcommand shows current venv state

#### `mcp_cmd.go` -- `mcp install`

Installs the MCP server for IDE integration:

```
dark-governance mcp install [--target claude|cursor|all] [--governance-root PATH]
dark-governance mcp status
```

- Writes MCP server config to the appropriate IDE config location
- `claude`: `~/.claude/claude_desktop_config.json`
- `cursor`: `~/.cursor/mcp.json`
- Shows installed MCP server status

#### `configure_cmd.go` -- `configure`

Interactive configuration wizard stub:

```
dark-governance configure [--non-interactive] [--output PATH]
```

- In non-interactive mode: generates a default `project.yaml`
- Interactive mode: prints guidance message (full wizard is future work)
- Validates existing `project.yaml` if present

#### `uninstall_cmd.go` -- `uninstall`

Removes home cache and optionally all governance artifacts:

```
dark-governance uninstall [--all] [--yes]
```

- Default: removes `~/.ai/versions/` and `~/.ai/venv/`
- `--all`: removes the entire governance home directory (all contents of `DARK_GOVERNANCE_HOME`, typically `~/.ai/`)
- `--yes`: skip confirmation prompt
- Always shows what will be removed before acting

### 2. Update `install.sh`

Enhance the curl installer script:

- Add checksum verification: download `checksums.txt` alongside archive, verify SHA-256
- Add Cosign verification stub: check for `cosign` binary, verify signature if available, warn if not
- Improve error messages and logging
- Add `CHECKSUM_VERIFY=1` env var (default on) to control checksum behavior

### 3. Installation Guide

Create `docs/guides/installation.md` covering:

- Local install (curl, brew, manual)
- CI install (GitHub Actions snippet with pinned version)
- Offline/airgapped install
- Verification steps
- Uninstallation

### 4. Implementation Files

| File | Change |
|------|--------|
| `src/cmd/dark-governance/deps_cmd.go` | New: `deps setup`, `deps status` |
| `src/cmd/dark-governance/mcp_cmd.go` | New: `mcp install`, `mcp status` |
| `src/cmd/dark-governance/configure_cmd.go` | New: `configure` |
| `src/cmd/dark-governance/uninstall_cmd.go` | New: `uninstall` |
| `src/cmd/dark-governance/root.go` | Register new commands |
| `src/scripts/install.sh` | Add checksum + Cosign verification |
| `docs/guides/installation.md` | New: comprehensive install guide |

### 5. Test Plan

- Build: `cd src && make prepare-embed && make build`
- Unit: `cd src && make test`
- Manual: `./bin/dark-governance deps setup`, `./bin/dark-governance mcp status`, `./bin/dark-governance configure --non-interactive`, `./bin/dark-governance uninstall --yes` (dry-run)
- Script: verify install.sh checksum logic with mock checksums file

### 6. Out of Scope

- Full interactive wizard (future iteration)
- Brew tap formula creation
- Winget manifest
- NPM shim package
- Cosign signing infrastructure (we add the verification stub only)
- Go engine migration (parallel track)
