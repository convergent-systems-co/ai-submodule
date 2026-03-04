import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { join } from "node:path";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import {
  parseInstallerArgs,
  buildServerEntry,
  readJsonFile,
  writeJsonFile,
  mergeServerConfig,
  verifyConfig,
  createBackup,
  detectIdes,
  type InstallerOptions,
} from "../src/install.js";

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

function makeTmpDir(): string {
  const dir = join(tmpdir(), `mcp-install-test-${Date.now()}-${Math.random().toString(36).slice(2)}`);
  mkdirSync(dir, { recursive: true });
  return dir;
}

// ---------------------------------------------------------------------------
// parseInstallerArgs
// ---------------------------------------------------------------------------

describe("parseInstallerArgs", () => {
  it("parses empty args", () => {
    const opts = parseInstallerArgs(["node", "index.js", "install"]);
    expect(opts.dryRun).toBe(false);
    expect(opts.ide).toBeUndefined();
    expect(opts.skipVerify).toBe(false);
    expect(opts.local).toBe(false);
    expect(opts.help).toBe(false);
  });

  it("parses --dry-run", () => {
    const opts = parseInstallerArgs(["node", "index.js", "install", "--dry-run"]);
    expect(opts.dryRun).toBe(true);
  });

  it("parses --ide vscode", () => {
    const opts = parseInstallerArgs(["node", "index.js", "install", "--ide", "vscode"]);
    expect(opts.ide).toBe("vscode");
  });

  it("parses --skip-verify", () => {
    const opts = parseInstallerArgs(["node", "index.js", "install", "--skip-verify"]);
    expect(opts.skipVerify).toBe(true);
  });

  it("parses --local", () => {
    const opts = parseInstallerArgs(["node", "index.js", "install", "--local"]);
    expect(opts.local).toBe(true);
  });

  it("parses --help", () => {
    const opts = parseInstallerArgs(["node", "index.js", "install", "--help"]);
    expect(opts.help).toBe(true);
  });

  it("parses -h as help", () => {
    const opts = parseInstallerArgs(["node", "index.js", "install", "-h"]);
    expect(opts.help).toBe(true);
  });

  it("parses multiple flags", () => {
    const opts = parseInstallerArgs([
      "node", "index.js", "install",
      "--dry-run", "--ide", "cursor", "--skip-verify", "--local",
    ]);
    expect(opts.dryRun).toBe(true);
    expect(opts.ide).toBe("cursor");
    expect(opts.skipVerify).toBe(true);
    expect(opts.local).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// buildServerEntry
// ---------------------------------------------------------------------------

describe("buildServerEntry", () => {
  it("returns npx entry when not local", () => {
    const entry = buildServerEntry(false);
    expect(entry.command).toBe("npx");
    expect(entry.args).toContain("-y");
    expect(entry.args.some(a => a.includes("@jm-packages/dark-forge-mcp"))).toBe(true);
  });

  it("returns node entry when local", () => {
    const entry = buildServerEntry(true);
    expect(entry.command).toBe("node");
    expect(entry.args.length).toBe(1);
    expect(entry.args[0]).toContain("dist");
  });
});

// ---------------------------------------------------------------------------
// readJsonFile / writeJsonFile
// ---------------------------------------------------------------------------

describe("readJsonFile", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = makeTmpDir();
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  it("reads valid JSON", () => {
    const fp = join(tmpDir, "test.json");
    writeFileSync(fp, '{"key": "value"}');
    const result = readJsonFile(fp);
    expect(result).toEqual({ key: "value" });
  });

  it("returns null for invalid JSON", () => {
    const fp = join(tmpDir, "bad.json");
    writeFileSync(fp, "not json");
    const result = readJsonFile(fp);
    expect(result).toBeNull();
  });

  it("returns null for non-existent file", () => {
    const result = readJsonFile(join(tmpDir, "missing.json"));
    expect(result).toBeNull();
  });
});

describe("writeJsonFile", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = makeTmpDir();
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  it("writes valid JSON", () => {
    const fp = join(tmpDir, "out.json");
    const success = writeJsonFile(fp, { key: "value" });
    expect(success).toBe(true);
    const content = readFileSync(fp, "utf-8");
    expect(JSON.parse(content)).toEqual({ key: "value" });
  });

  it("creates parent directories if needed", () => {
    const fp = join(tmpDir, "nested", "dir", "out.json");
    const success = writeJsonFile(fp, { hello: "world" });
    expect(success).toBe(true);
    expect(existsSync(fp)).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// createBackup
// ---------------------------------------------------------------------------

describe("createBackup", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = makeTmpDir();
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  it("creates a backup copy", () => {
    const fp = join(tmpDir, "config.json");
    writeFileSync(fp, '{"original": true}');
    const backupPath = createBackup(fp);
    expect(existsSync(backupPath)).toBe(true);
    expect(backupPath).toContain("backup-");
    const content = readFileSync(backupPath, "utf-8");
    expect(JSON.parse(content)).toEqual({ original: true });
  });
});

// ---------------------------------------------------------------------------
// mergeServerConfig
// ---------------------------------------------------------------------------

describe("mergeServerConfig", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = makeTmpDir();
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  const testEntry = { command: "npx", args: ["-y", "@jm-packages/dark-forge-mcp@latest"] };

  it("creates new config file if missing", () => {
    const fp = join(tmpDir, "new-config.json");
    const result = mergeServerConfig(fp, "mcpServers", testEntry, false);
    expect(result.success).toBe(true);
    expect(existsSync(fp)).toBe(true);

    const config = JSON.parse(readFileSync(fp, "utf-8"));
    expect(config.mcpServers["dark-forge-mcp"]).toEqual(testEntry);
  });

  it("merges into existing config", () => {
    const fp = join(tmpDir, "existing.json");
    writeFileSync(fp, JSON.stringify({ mcpServers: { "other-server": { command: "other" } } }));

    const result = mergeServerConfig(fp, "mcpServers", testEntry, false);
    expect(result.success).toBe(true);

    const config = JSON.parse(readFileSync(fp, "utf-8"));
    expect(config.mcpServers["dark-forge-mcp"]).toEqual(testEntry);
    expect(config.mcpServers["other-server"]).toEqual({ command: "other" });
  });

  it("creates backup of existing files", () => {
    const fp = join(tmpDir, "backup-test.json");
    writeFileSync(fp, '{"existing": true}');

    const result = mergeServerConfig(fp, "servers", testEntry, false);
    expect(result.success).toBe(true);
    expect(result.backupPath).toBeDefined();
    expect(existsSync(result.backupPath!)).toBe(true);
  });

  it("does not write in dry-run mode", () => {
    const fp = join(tmpDir, "dry-run.json");
    const result = mergeServerConfig(fp, "servers", testEntry, true);
    expect(result.success).toBe(true);
    expect(existsSync(fp)).toBe(false);
  });

  it("handles dot-separated keys (mcp.servers)", () => {
    const fp = join(tmpDir, "dotkey.json");
    writeFileSync(fp, "{}");

    const result = mergeServerConfig(fp, "mcp.servers", testEntry, false);
    expect(result.success).toBe(true);

    const config = JSON.parse(readFileSync(fp, "utf-8"));
    expect(config.mcp.servers["dark-forge-mcp"]).toEqual(testEntry);
  });

  it("is idempotent — safe to run multiple times", () => {
    const fp = join(tmpDir, "idempotent.json");
    writeFileSync(fp, "{}");

    mergeServerConfig(fp, "mcpServers", testEntry, false);
    mergeServerConfig(fp, "mcpServers", testEntry, false);

    const config = JSON.parse(readFileSync(fp, "utf-8"));
    expect(config.mcpServers["dark-forge-mcp"]).toEqual(testEntry);
    // Only one entry, not duplicated
    expect(Object.keys(config.mcpServers)).toEqual(["dark-forge-mcp"]);
  });

  it("returns error for invalid JSON in existing file", () => {
    const fp = join(tmpDir, "invalid.json");
    writeFileSync(fp, "not json {{{");

    const result = mergeServerConfig(fp, "servers", testEntry, false);
    expect(result.success).toBe(false);
    expect(result.error).toContain("Failed to parse");
  });
});

// ---------------------------------------------------------------------------
// verifyConfig
// ---------------------------------------------------------------------------

describe("verifyConfig", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = makeTmpDir();
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  it("returns true when server entry exists", () => {
    const fp = join(tmpDir, "verify.json");
    writeFileSync(fp, JSON.stringify({
      mcpServers: { "dark-forge-mcp": { command: "npx", args: [] } },
    }));
    expect(verifyConfig(fp, "mcpServers")).toBe(true);
  });

  it("returns false when server entry is missing", () => {
    const fp = join(tmpDir, "verify.json");
    writeFileSync(fp, JSON.stringify({ mcpServers: {} }));
    expect(verifyConfig(fp, "mcpServers")).toBe(false);
  });

  it("returns false for non-existent file", () => {
    expect(verifyConfig(join(tmpDir, "missing.json"), "mcpServers")).toBe(false);
  });

  it("handles dot-separated keys", () => {
    const fp = join(tmpDir, "verify-dot.json");
    writeFileSync(fp, JSON.stringify({
      mcp: { servers: { "dark-forge-mcp": { command: "npx" } } },
    }));
    expect(verifyConfig(fp, "mcp.servers")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// detectIdes
// ---------------------------------------------------------------------------

describe("detectIdes", () => {
  it("returns results for all 6 IDEs", () => {
    const results = detectIdes();
    const ideNames = results.map(r => r.ide);
    expect(ideNames).toContain("vscode");
    expect(ideNames).toContain("cursor");
    expect(ideNames).toContain("claude-desktop");
    expect(ideNames).toContain("claude-code");
    expect(ideNames).toContain("copilot");
    expect(ideNames).toContain("jetbrains");
  });

  it("each result has required fields", () => {
    const results = detectIdes();
    for (const r of results) {
      expect(r).toHaveProperty("ide");
      expect(r).toHaveProperty("label");
      expect(r).toHaveProperty("detected");
      expect(r).toHaveProperty("method");
      expect(typeof r.detected).toBe("boolean");
    }
  });
});
