import { readFile, readdir, stat } from "node:fs/promises";
import { existsSync, statSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";
import matter from "gray-matter";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Walk up from the package directory to find the governance root.
 * In the dark-forge itself, governance/ is at the repo root.
 * In a consuming repo, it would be under .ai/governance/.
 */
export function resolveGovernanceRoot(explicitRoot?: string): string {
  if (explicitRoot) {
    return resolve(explicitRoot);
  }

  // Walk up from the package's dist/ directory
  let current = resolve(__dirname);
  for (let i = 0; i < 10; i++) {
    // Check for governance/ directory directly
    const candidate = join(current, "governance");
    if (existsSync(candidate) && statSync(candidate).isDirectory()) {
      return current;
    }

    // Also check .ai/governance/ for consuming repos
    const submoduleCandidate = join(current, ".ai", "governance");
    if (
      existsSync(submoduleCandidate) &&
      statSync(submoduleCandidate).isDirectory()
    ) {
      return join(current, ".ai");
    }

    const parent = dirname(current);
    if (parent === current) break;
    current = parent;
  }

  throw new Error(
    "Could not find governance/ directory. Use --governance-root to specify it explicitly."
  );
}

/**
 * Recursively scan a directory for Markdown files.
 */
export async function scanMarkdownFiles(dir: string): Promise<string[]> {
  const results: string[] = [];

  async function walk(d: string): Promise<void> {
    let entries;
    try {
      entries = await readdir(d, { withFileTypes: true });
    } catch {
      return;
    }

    for (const entry of entries) {
      const fullPath = join(d, entry.name);
      if (entry.isDirectory()) {
        await walk(fullPath);
      } else if (entry.isFile() && entry.name.endsWith(".md")) {
        results.push(fullPath);
      }
    }
  }

  await walk(dir);
  return results.sort();
}

/**
 * Scan a directory for YAML files.
 */
export async function scanYamlFiles(dir: string): Promise<string[]> {
  const results: string[] = [];

  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch {
    return results;
  }

  for (const entry of entries) {
    if (entry.isFile() && (entry.name.endsWith(".yaml") || entry.name.endsWith(".yml"))) {
      results.push(join(dir, entry.name));
    }
  }

  return results.sort();
}

/**
 * Parse a Markdown file extracting frontmatter and content.
 */
export function parseMarkdownWithFrontmatter(content: string): {
  data: Record<string, unknown>;
  content: string;
} {
  const parsed = matter(content);
  return {
    data: parsed.data as Record<string, unknown>,
    content: parsed.content,
  };
}

/**
 * Read a file as UTF-8 text.
 */
export async function readTextFile(filePath: string): Promise<string> {
  return readFile(filePath, "utf-8");
}

/**
 * Get file metadata (size, mtime).
 */
export async function getFileInfo(
  filePath: string
): Promise<{ size: number; mtime: Date }> {
  const s = await stat(filePath);
  return { size: s.size, mtime: s.mtimeMs ? new Date(s.mtimeMs) : s.mtime };
}

/**
 * Spawn a Python subprocess and capture output.
 * Returns { stdout, stderr, exitCode, ok }.
 *
 * Design: This function always resolves (never rejects) because MCP tool
 * handlers need to return structured error responses rather than throwing.
 * The `ok` field provides a clear boolean for callers to check success
 * without inspecting exitCode. When Python is not installed, exitCode
 * will be 1 and ok will be false with a descriptive stderr message.
 */
export function spawnPython(
  args: string[],
  cwd?: string
): Promise<{ stdout: string; stderr: string; exitCode: number; ok: boolean }> {
  return new Promise((resolve) => {
    // Try python3 first, fall back to python
    const pythonCmd = process.platform === "win32" ? "python" : "python3";

    const child = spawn(pythonCmd, args, {
      cwd,
      stdio: ["pipe", "pipe", "pipe"],
      timeout: 30000,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (data: Buffer) => {
      stdout += data.toString();
    });

    child.stderr.on("data", (data: Buffer) => {
      stderr += data.toString();
    });

    child.on("error", (err: Error) => {
      resolve({
        stdout: "",
        stderr: `Failed to spawn Python: ${err.message}. Ensure python3 is installed and available on PATH.`,
        exitCode: 1,
        ok: false,
      });
    });

    child.on("close", (code: number | null) => {
      const exitCode = code ?? 1;
      resolve({
        stdout,
        stderr,
        exitCode,
        ok: exitCode === 0,
      });
    });
  });
}

/**
 * Extract a descriptive name from a Markdown file's first heading or filename.
 */
export function extractTitle(content: string, filename: string): string {
  // Try to find the first # heading
  const match = content.match(/^#\s+(?:Review:\s+)?(.+)$/m);
  if (match) {
    return match[1].trim();
  }
  // Fall back to filename without extension
  return filename.replace(/\.md$/, "").replace(/[-_]/g, " ");
}

/**
 * Convert a filesystem path to a URI-safe slug.
 */
export function pathToSlug(filename: string): string {
  return filename.replace(/\.md$/, "").replace(/\.yaml$/, "").replace(/\.yml$/, "");
}
