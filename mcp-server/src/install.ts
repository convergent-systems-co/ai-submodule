/**
 * install.ts — Multi-IDE auto-installer for ai-submodule-mcp.
 *
 * Detects installed IDEs, generates MCP server configuration entries,
 * and writes them with backup/rollback safety.
 *
 * Supported IDEs:
 *   - VS Code
 *   - Cursor
 *   - Claude Desktop
 *   - Claude Code
 *   - Copilot CLI (manual instructions)
 *   - JetBrains (manual instructions)
 */

import { existsSync, readFileSync, writeFileSync, mkdirSync, copyFileSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { execSync } from "node:child_process";
import { homedir, platform } from "node:os";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type IdeName =
  | "vscode"
  | "cursor"
  | "claude-desktop"
  | "claude-code"
  | "copilot"
  | "jetbrains";

export interface IdeDetectionResult {
  ide: IdeName;
  label: string;
  detected: boolean;
  method: string; // how it was detected
}

export interface InstallResult {
  ide: IdeName;
  label: string;
  action: "configured" | "skipped" | "manual" | "dry-run";
  configPath?: string;
  message: string;
  backedUp?: string;
}

export interface InstallerOptions {
  dryRun: boolean;
  ide?: IdeName;
  skipVerify: boolean;
  local: boolean;
  help: boolean;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SERVER_NAME = "ai-submodule-mcp";
const PACKAGE_NAME = "@jm-packages/ai-submodule-mcp";

// ---------------------------------------------------------------------------
// Argument parsing
// ---------------------------------------------------------------------------

export function parseInstallerArgs(argv: string[]): InstallerOptions {
  const opts: InstallerOptions = {
    dryRun: false,
    skipVerify: false,
    local: false,
    help: false,
  };

  // argv[0] = node, argv[1] = script, argv[2] = "install", rest = flags
  const args = argv.slice(3);

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case "--dry-run":
        opts.dryRun = true;
        break;
      case "--ide":
        if (args[i + 1]) {
          opts.ide = args[i + 1] as IdeName;
          i++;
        }
        break;
      case "--skip-verify":
        opts.skipVerify = true;
        break;
      case "--local":
        opts.local = true;
        break;
      case "--help":
      case "-h":
        opts.help = true;
        break;
      default:
        console.error(`Unknown installer option: ${args[i]}`);
        break;
    }
  }

  return opts;
}

// ---------------------------------------------------------------------------
// Help text
// ---------------------------------------------------------------------------

export function printHelp(): void {
  const help = `
ai-submodule-mcp install — Multi-IDE MCP server auto-installer

Usage:
  ai-submodule-mcp install [options]

Options:
  --dry-run        Show what would be done without modifying files
  --ide <name>     Install for a specific IDE only
                   Values: vscode, cursor, claude-desktop, claude-code, copilot, jetbrains
  --skip-verify    Skip post-install config verification
  --local          Use local path instead of npx (for development)
  --help, -h       Show this help message

Supported IDEs:
  vscode           VS Code (.vscode/mcp.json)
  cursor           Cursor (~/.cursor/mcp.json)
  claude-desktop   Claude Desktop (claude_desktop_config.json)
  claude-code      Claude Code (.claude/settings.json)
  copilot          GitHub Copilot CLI (manual instructions)
  jetbrains        JetBrains IDEs (manual instructions)

Examples:
  ai-submodule-mcp install                    # Auto-detect and configure all IDEs
  ai-submodule-mcp install --dry-run          # Preview changes
  ai-submodule-mcp install --ide vscode       # Configure VS Code only
  ai-submodule-mcp install --local            # Use local path instead of npx
`.trim();
  console.log(help);
}

// ---------------------------------------------------------------------------
// IDE detection helpers
// ---------------------------------------------------------------------------

/**
 * Check if a command is available by running it and checking exit code.
 */
export function commandExists(cmd: string): boolean {
  try {
    execSync(cmd, { stdio: "pipe", timeout: 5000 });
    return true;
  } catch {
    return false;
  }
}

/**
 * Determine the Claude Desktop config directory based on platform.
 */
export function getClaudeDesktopConfigDir(): string | null {
  const p = platform();
  if (p === "darwin") {
    return join(homedir(), "Library", "Application Support", "Claude");
  }
  if (p === "win32") {
    const appData = process.env.APPDATA;
    if (appData) {
      return join(appData, "Claude");
    }
    return join(homedir(), "AppData", "Roaming", "Claude");
  }
  // Linux — Claude Desktop does not officially support Linux yet
  return null;
}

/**
 * Get JetBrains config base directory.
 */
export function getJetBrainsConfigDir(): string | null {
  const p = platform();
  if (p === "darwin") {
    return join(homedir(), "Library", "Application Support", "JetBrains");
  }
  if (p === "win32") {
    const appData = process.env.APPDATA;
    if (appData) {
      return join(appData, "JetBrains");
    }
    return null;
  }
  // Linux
  return join(homedir(), ".config", "JetBrains");
}

// ---------------------------------------------------------------------------
// IDE detection
// ---------------------------------------------------------------------------

export function detectIdes(): IdeDetectionResult[] {
  const results: IdeDetectionResult[] = [];
  const home = homedir();

  // VS Code
  const vscodeDir = join(home, ".vscode");
  if (existsSync(vscodeDir)) {
    results.push({ ide: "vscode", label: "VS Code", detected: true, method: "~/.vscode/ directory found" });
  } else if (commandExists("code --version")) {
    results.push({ ide: "vscode", label: "VS Code", detected: true, method: "code --version command available" });
  } else {
    results.push({ ide: "vscode", label: "VS Code", detected: false, method: "not found" });
  }

  // Cursor
  const cursorDir = join(home, ".cursor");
  if (existsSync(cursorDir)) {
    results.push({ ide: "cursor", label: "Cursor", detected: true, method: "~/.cursor/ directory found" });
  } else if (commandExists("cursor --version")) {
    results.push({ ide: "cursor", label: "Cursor", detected: true, method: "cursor --version command available" });
  } else {
    results.push({ ide: "cursor", label: "Cursor", detected: false, method: "not found" });
  }

  // Claude Desktop
  const claudeDesktopDir = getClaudeDesktopConfigDir();
  if (claudeDesktopDir && existsSync(claudeDesktopDir)) {
    results.push({ ide: "claude-desktop", label: "Claude Desktop", detected: true, method: `${claudeDesktopDir} directory found` });
  } else {
    results.push({ ide: "claude-desktop", label: "Claude Desktop", detected: false, method: "not found" });
  }

  // Claude Code
  if (commandExists("claude --version")) {
    results.push({ ide: "claude-code", label: "Claude Code", detected: true, method: "claude --version command available" });
  } else {
    results.push({ ide: "claude-code", label: "Claude Code", detected: false, method: "not found" });
  }

  // Copilot CLI
  if (commandExists("gh copilot --version")) {
    results.push({ ide: "copilot", label: "GitHub Copilot CLI", detected: true, method: "gh copilot --version command available" });
  } else if (commandExists("github-copilot-cli --version")) {
    results.push({ ide: "copilot", label: "GitHub Copilot CLI", detected: true, method: "github-copilot-cli --version command available" });
  } else {
    results.push({ ide: "copilot", label: "GitHub Copilot CLI", detected: false, method: "not found" });
  }

  // JetBrains
  const jetbrainsDir = getJetBrainsConfigDir();
  if (jetbrainsDir && existsSync(jetbrainsDir)) {
    results.push({ ide: "jetbrains", label: "JetBrains", detected: true, method: `${jetbrainsDir} directory found` });
  } else {
    results.push({ ide: "jetbrains", label: "JetBrains", detected: false, method: "not found" });
  }

  return results;
}

// ---------------------------------------------------------------------------
// MCP server config payload
// ---------------------------------------------------------------------------

export interface McpServerEntry {
  command: string;
  args: string[];
}

export function buildServerEntry(local: boolean): McpServerEntry {
  if (local) {
    // Resolve the local dist/index.js relative to this file
    const distIndex = resolve(dirname(new URL(import.meta.url).pathname), "..", "dist", "index.js");
    return {
      command: "node",
      args: [distIndex],
    };
  }
  return {
    command: "npx",
    args: ["-y", `${PACKAGE_NAME}@latest`],
  };
}

// ---------------------------------------------------------------------------
// File manipulation with backup and rollback
// ---------------------------------------------------------------------------

/**
 * Create a timestamped backup of a file. Returns the backup path.
 */
export function createBackup(filePath: string): string {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const backupPath = `${filePath}.backup-${timestamp}`;
  copyFileSync(filePath, backupPath);
  return backupPath;
}

/**
 * Safely read and parse a JSON file. Returns null on failure.
 */
export function readJsonFile(filePath: string): Record<string, unknown> | null {
  try {
    const raw = readFileSync(filePath, "utf-8");
    return JSON.parse(raw) as Record<string, unknown>;
  } catch {
    return null;
  }
}

/**
 * Write a JSON object to a file, validating that it round-trips correctly.
 * Returns true on success.
 */
export function writeJsonFile(filePath: string, data: Record<string, unknown>): boolean {
  const serialized = JSON.stringify(data, null, 2) + "\n";

  // Validate round-trip before writing
  try {
    JSON.parse(serialized);
  } catch {
    return false;
  }

  const dir = dirname(filePath);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }

  writeFileSync(filePath, serialized, "utf-8");
  return true;
}

/**
 * Merge an MCP server entry into a JSON config file at the given key path.
 * Creates the file if it does not exist.
 * Returns { success, backupPath?, error? }.
 */
export function mergeServerConfig(
  filePath: string,
  serversKey: string,
  entry: McpServerEntry,
  dryRun: boolean
): { success: boolean; backupPath?: string; error?: string } {
  // Read or create the config
  let config: Record<string, unknown>;
  let backupPath: string | undefined;

  if (existsSync(filePath)) {
    const parsed = readJsonFile(filePath);
    if (parsed === null) {
      return { success: false, error: `Failed to parse existing config at ${filePath}` };
    }
    config = parsed;

    if (!dryRun) {
      backupPath = createBackup(filePath);
    }
  } else {
    config = {};
  }

  // Navigate/create the servers key (supports dot-separated keys like "mcp.servers")
  const keyParts = serversKey.split(".");
  let current: Record<string, unknown> = config;
  for (let i = 0; i < keyParts.length - 1; i++) {
    const part = keyParts[i];
    if (typeof current[part] !== "object" || current[part] === null) {
      current[part] = {};
    }
    current = current[part] as Record<string, unknown>;
  }

  const lastKey = keyParts[keyParts.length - 1];
  if (typeof current[lastKey] !== "object" || current[lastKey] === null) {
    current[lastKey] = {};
  }

  const servers = current[lastKey] as Record<string, unknown>;
  servers[SERVER_NAME] = entry;

  if (dryRun) {
    return { success: true };
  }

  // Write with validation
  const written = writeJsonFile(filePath, config);
  if (!written) {
    // Rollback if backup exists
    if (backupPath && existsSync(backupPath)) {
      copyFileSync(backupPath, filePath);
    }
    return { success: false, error: `Failed to write valid JSON to ${filePath}` };
  }

  return { success: true, backupPath };
}

// ---------------------------------------------------------------------------
// Post-install verification
// ---------------------------------------------------------------------------

export function verifyConfig(filePath: string, serversKey: string): boolean {
  const config = readJsonFile(filePath);
  if (!config) return false;

  // Navigate to the servers key
  const keyParts = serversKey.split(".");
  let current: unknown = config;
  for (const part of keyParts) {
    if (typeof current !== "object" || current === null) return false;
    current = (current as Record<string, unknown>)[part];
  }

  if (typeof current !== "object" || current === null) return false;
  const servers = current as Record<string, unknown>;

  return SERVER_NAME in servers;
}

// ---------------------------------------------------------------------------
// Per-IDE installation
// ---------------------------------------------------------------------------

function installVscode(entry: McpServerEntry, opts: InstallerOptions): InstallResult {
  const configPath = join(process.cwd(), ".vscode", "mcp.json");

  if (opts.dryRun) {
    return {
      ide: "vscode",
      label: "VS Code",
      action: "dry-run",
      configPath,
      message: `Would write MCP server config to ${configPath}`,
    };
  }

  const result = mergeServerConfig(configPath, "servers", entry, opts.dryRun);
  if (!result.success) {
    return {
      ide: "vscode",
      label: "VS Code",
      action: "skipped",
      configPath,
      message: result.error ?? "Failed to merge config",
    };
  }

  if (!opts.skipVerify && !verifyConfig(configPath, "servers")) {
    return {
      ide: "vscode",
      label: "VS Code",
      action: "skipped",
      configPath,
      message: "Post-install verification failed",
    };
  }

  return {
    ide: "vscode",
    label: "VS Code",
    action: "configured",
    configPath,
    message: `Configured MCP server in ${configPath}`,
    backedUp: result.backupPath,
  };
}

function installCursor(entry: McpServerEntry, opts: InstallerOptions): InstallResult {
  const configPath = join(homedir(), ".cursor", "mcp.json");

  if (opts.dryRun) {
    return {
      ide: "cursor",
      label: "Cursor",
      action: "dry-run",
      configPath,
      message: `Would write MCP server config to ${configPath}`,
    };
  }

  const result = mergeServerConfig(configPath, "mcpServers", entry, opts.dryRun);
  if (!result.success) {
    return {
      ide: "cursor",
      label: "Cursor",
      action: "skipped",
      configPath,
      message: result.error ?? "Failed to merge config",
    };
  }

  if (!opts.skipVerify && !verifyConfig(configPath, "mcpServers")) {
    return {
      ide: "cursor",
      label: "Cursor",
      action: "skipped",
      configPath,
      message: "Post-install verification failed",
    };
  }

  return {
    ide: "cursor",
    label: "Cursor",
    action: "configured",
    configPath,
    message: `Configured MCP server in ${configPath}`,
    backedUp: result.backupPath,
  };
}

function installClaudeDesktop(entry: McpServerEntry, opts: InstallerOptions): InstallResult {
  const configDir = getClaudeDesktopConfigDir();
  if (!configDir) {
    return {
      ide: "claude-desktop",
      label: "Claude Desktop",
      action: "skipped",
      message: "Claude Desktop config directory not found for this platform",
    };
  }

  const configPath = join(configDir, "claude_desktop_config.json");

  if (opts.dryRun) {
    return {
      ide: "claude-desktop",
      label: "Claude Desktop",
      action: "dry-run",
      configPath,
      message: `Would write MCP server config to ${configPath}`,
    };
  }

  const result = mergeServerConfig(configPath, "mcpServers", entry, opts.dryRun);
  if (!result.success) {
    return {
      ide: "claude-desktop",
      label: "Claude Desktop",
      action: "skipped",
      configPath,
      message: result.error ?? "Failed to merge config",
    };
  }

  if (!opts.skipVerify && !verifyConfig(configPath, "mcpServers")) {
    return {
      ide: "claude-desktop",
      label: "Claude Desktop",
      action: "skipped",
      configPath,
      message: "Post-install verification failed",
    };
  }

  return {
    ide: "claude-desktop",
    label: "Claude Desktop",
    action: "configured",
    configPath,
    message: `Configured MCP server in ${configPath}`,
    backedUp: result.backupPath,
  };
}

function installClaudeCode(_entry: McpServerEntry, opts: InstallerOptions): InstallResult {
  // Claude Code supports `claude mcp add` — recommend that approach
  const configPath = join(process.cwd(), ".claude", "settings.json");

  if (opts.dryRun) {
    return {
      ide: "claude-code",
      label: "Claude Code",
      action: "dry-run",
      configPath,
      message: `Would write MCP server config to ${configPath}`,
    };
  }

  // Try to use `claude mcp add` if available
  if (commandExists("claude --version")) {
    console.log("\n  Claude Code detected. You can also configure via CLI:");
    console.log(`  claude mcp add ${SERVER_NAME} -- npx -y ${PACKAGE_NAME}@latest\n`);
  }

  const result = mergeServerConfig(configPath, "mcpServers", _entry, opts.dryRun);
  if (!result.success) {
    return {
      ide: "claude-code",
      label: "Claude Code",
      action: "skipped",
      configPath,
      message: result.error ?? "Failed to merge config",
    };
  }

  if (!opts.skipVerify && !verifyConfig(configPath, "mcpServers")) {
    return {
      ide: "claude-code",
      label: "Claude Code",
      action: "skipped",
      configPath,
      message: "Post-install verification failed",
    };
  }

  return {
    ide: "claude-code",
    label: "Claude Code",
    action: "configured",
    configPath,
    message: `Configured MCP server in ${configPath}`,
    backedUp: result.backupPath,
  };
}

function installCopilot(_entry: McpServerEntry, opts: InstallerOptions): InstallResult {
  const message = [
    "GitHub Copilot CLI does not support MCP server configuration files.",
    "MCP integration with Copilot is managed through the GitHub Copilot extension settings.",
    "See: https://docs.github.com/en/copilot for current MCP support status.",
  ].join("\n  ");

  return {
    ide: "copilot",
    label: "GitHub Copilot CLI",
    action: opts.dryRun ? "dry-run" : "manual",
    message,
  };
}

function installJetbrains(_entry: McpServerEntry, opts: InstallerOptions): InstallResult {
  const message = [
    "JetBrains IDE MCP configuration requires manual setup:",
    "1. Open Settings > Tools > AI Assistant > MCP Servers",
    `2. Add a new server with name: ${SERVER_NAME}`,
    `3. Command: npx`,
    `4. Args: -y ${PACKAGE_NAME}@latest`,
    "5. Apply and restart the IDE",
    "",
    "See JetBrains documentation for your specific IDE (IntelliJ, WebStorm, etc.).",
  ].join("\n  ");

  return {
    ide: "jetbrains",
    label: "JetBrains",
    action: opts.dryRun ? "dry-run" : "manual",
    message,
  };
}

// ---------------------------------------------------------------------------
// Installer dispatch
// ---------------------------------------------------------------------------

const IDE_INSTALLERS: Record<IdeName, (entry: McpServerEntry, opts: InstallerOptions) => InstallResult> = {
  vscode: installVscode,
  cursor: installCursor,
  "claude-desktop": installClaudeDesktop,
  "claude-code": installClaudeCode,
  copilot: installCopilot,
  jetbrains: installJetbrains,
};

const VALID_IDE_NAMES: IdeName[] = ["vscode", "cursor", "claude-desktop", "claude-code", "copilot", "jetbrains"];

// ---------------------------------------------------------------------------
// Main installer entry point
// ---------------------------------------------------------------------------

export async function runInstaller(argv: string[]): Promise<void> {
  const opts = parseInstallerArgs(argv);

  if (opts.help) {
    printHelp();
    return;
  }

  // Validate --ide if provided
  if (opts.ide && !VALID_IDE_NAMES.includes(opts.ide)) {
    console.error(`Error: Unknown IDE "${opts.ide}". Valid values: ${VALID_IDE_NAMES.join(", ")}`);
    process.exit(1);
  }

  console.log("=== ai-submodule-mcp installer ===\n");

  if (opts.dryRun) {
    console.log("[DRY RUN] No files will be modified.\n");
  }

  // Detect IDEs
  console.log("Detecting installed IDEs...\n");
  const detected = detectIdes();

  for (const d of detected) {
    const status = d.detected ? "[FOUND]" : "[  --  ]";
    console.log(`  ${status} ${d.label} (${d.method})`);
  }
  console.log("");

  // Build the MCP server entry
  const entry = buildServerEntry(opts.local);

  if (opts.local) {
    console.log(`[LOCAL MODE] Using local path: ${entry.args.join(" ")}\n`);
  }

  // Install for each detected (or specified) IDE
  const results: InstallResult[] = [];

  for (const d of detected) {
    // Skip non-detected IDEs unless specifically requested
    if (!d.detected && opts.ide !== d.ide) {
      continue;
    }

    // If --ide is specified, skip non-matching IDEs
    if (opts.ide && opts.ide !== d.ide) {
      continue;
    }

    const installer = IDE_INSTALLERS[d.ide];
    const result = installer(entry, opts);
    results.push(result);
  }

  // Print results
  console.log("--- Results ---\n");

  for (const r of results) {
    const prefix = r.action === "configured" ? "[OK]"
      : r.action === "dry-run" ? "[DRY]"
      : r.action === "manual" ? "[INFO]"
      : "[SKIP]";

    console.log(`  ${prefix} ${r.label}: ${r.message}`);

    if (r.backedUp) {
      console.log(`        Backup: ${r.backedUp}`);
    }
  }

  console.log("\nDone. Restart affected IDEs to pick up the new MCP server configuration.");

  // Summary
  const configured = results.filter(r => r.action === "configured").length;
  const manual = results.filter(r => r.action === "manual").length;
  const skipped = results.filter(r => r.action === "skipped").length;

  if (configured > 0 || manual > 0) {
    console.log(`\nSummary: ${configured} configured, ${manual} manual, ${skipped} skipped`);
  }
}
