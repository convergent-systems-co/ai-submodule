# IDE Configuration Guide

Configure the Dark Forge governance MCP server for your IDE with a single command.

---

## Quick Start

```bash
bash .ai/bin/install-ide.sh
```

This auto-detects all installed IDEs and configures the governance MCP server for each one.

---

## Supported IDEs

| IDE | Detection Method | Config Location (macOS) |
|-----|-----------------|------------------------|
| VS Code | Settings directory exists | `~/Library/Application Support/Code/User/settings.json` |
| Cursor | `~/.cursor` directory exists | `~/.cursor/mcp.json` |
| Claude Desktop | Application Support directory exists | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Code | `~/.claude.json` exists or `claude` CLI installed | `~/.claude.json` |
| JetBrains | Any JetBrains IDE config directory exists | `~/Library/Application Support/JetBrains/<IDE>/options/mcp.json` |

---

## Commands

### Auto-detect and configure all IDEs

```bash
bash .ai/bin/install-ide.sh
```

### Check which IDEs are detected (without configuring)

```bash
bash .ai/bin/install-ide.sh --check
```

### Configure a specific IDE only

```bash
bash .ai/bin/install-ide.sh --ide vscode
bash .ai/bin/install-ide.sh --ide cursor
bash .ai/bin/install-ide.sh --ide claude-desktop
bash .ai/bin/install-ide.sh --ide claude-code
bash .ai/bin/install-ide.sh --ide jetbrains
```

### Fix stale configurations

If you moved the governance submodule or the MCP server paths changed:

```bash
bash .ai/bin/install-ide.sh --fix
```

### Specify governance root

If your governance root is not the parent of `.ai/`:

```bash
bash .ai/bin/install-ide.sh --governance-root /path/to/project
```

---

## Prerequisites

- **Node.js** — required for MCP server and JSON configuration
- **MCP server built** — the installer will attempt to build automatically if `npm` is available

If the MCP server is not built, the installer will try:
```bash
cd .ai/mcp-server && npm install && npm run build
```

---

## How It Works

The installer:

1. **Detects** installed IDEs by checking standard config directory paths
2. **Builds** the MCP server if not already built (`dist/index.js`)
3. **Writes** MCP server configuration into each IDE's config file
4. **Reports** which IDEs were configured

The MCP server entry added to each IDE config looks like:

```json
{
  "dark-forge-mcp": {
    "command": "/path/to/node",
    "args": ["/path/to/.ai/mcp-server/dist/index.js", "--governance-root", "/path/to/project"]
  }
}
```

---

## Troubleshooting

### IDE not detected

The installer checks standard installation paths. If your IDE is installed in a non-standard location:

1. Run `bash .ai/bin/install-ide.sh --check` to see what was detected
2. Use `--ide <name>` to configure a specific IDE manually
3. Or configure the MCP server manually using the JSON format above

### MCP server not building

Ensure Node.js and npm are installed:
```bash
node --version   # Should be 18+
npm --version
```

Then build manually:
```bash
cd .ai/mcp-server
npm install
npm run build
```

### Config not taking effect

Restart your IDE after running the installer. Most IDEs only read MCP configuration at startup.

### JetBrains detection

JetBrains IDEs store config in versioned directories (e.g., `IntelliJIdea2024.3`). The installer detects the most recent version. If you have multiple versions, run with `--fix` after upgrading.

---

## Integration with init.sh

The IDE installer is also available through `init.sh`:

```bash
bash .ai/bin/init.sh --mcp
```

This runs the same auto-detection and configuration as `install-ide.sh`.

---

## Platform Support

| Platform | VS Code | Cursor | Claude Desktop | Claude Code | JetBrains |
|----------|:-------:|:------:|:--------------:|:-----------:|:---------:|
| macOS    | Yes | Yes | Yes | Yes | Yes |
| Linux    | Yes | Yes | Yes | Yes | Yes |
| Windows (WSL) | Partial | Partial | Partial | Yes | Partial |
