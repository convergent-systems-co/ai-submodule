import { createHash } from "node:crypto";
import { readFile, stat } from "node:fs/promises";
import { join, relative } from "node:path";
import { scanMarkdownFiles, scanYamlFiles } from "./utils.js";

export interface ManifestEntry {
  path: string;
  hash: string;
  size: number;
}

export interface Manifest {
  files: ManifestEntry[];
  generated_at: string;
}

/**
 * Compute SHA-256 hash of a file's contents.
 */
async function hashFile(filePath: string): Promise<string> {
  const content = await readFile(filePath);
  return createHash("sha256").update(content).digest("hex");
}

/**
 * Generate a manifest of all served governance files with content hashes.
 */
export async function generateManifest(
  governanceRoot: string
): Promise<Manifest> {
  const entries: ManifestEntry[] = [];
  const governanceDir = join(governanceRoot, "governance");

  // Collect all files that are served as resources
  const dirs = [
    join(governanceDir, "prompts", "reviews"),
    join(governanceDir, "prompts", "workflows"),
    join(governanceDir, "personas", "agentic"),
  ];

  for (const dir of dirs) {
    const files = await scanMarkdownFiles(dir);
    for (const filePath of files) {
      const hash = await hashFile(filePath);
      const s = await stat(filePath);
      entries.push({
        path: relative(governanceRoot, filePath),
        hash,
        size: s.size,
      });
    }
  }

  // Shared perspectives
  const sharedPath = join(
    governanceDir,
    "prompts",
    "shared-perspectives.md"
  );
  try {
    const hash = await hashFile(sharedPath);
    const s = await stat(sharedPath);
    entries.push({
      path: relative(governanceRoot, sharedPath),
      hash,
      size: s.size,
    });
  } catch {
    // File may not exist
  }

  // Primary policy profiles
  const primaryPolicies = [
    "default.yaml",
    "fin_pii_high.yaml",
    "infrastructure_critical.yaml",
    "reduced_touchpoint.yaml",
  ];
  for (const policyFile of primaryPolicies) {
    const filePath = join(governanceDir, "policy", policyFile);
    try {
      const hash = await hashFile(filePath);
      const s = await stat(filePath);
      entries.push({
        path: relative(governanceRoot, filePath),
        hash,
        size: s.size,
      });
    } catch {
      // Policy file may not exist
    }
  }

  // Panel output schema
  const schemaPath = join(
    governanceDir,
    "schemas",
    "panel-output.schema.json"
  );
  try {
    const hash = await hashFile(schemaPath);
    const s = await stat(schemaPath);
    entries.push({
      path: relative(governanceRoot, schemaPath),
      hash,
      size: s.size,
    });
  } catch {
    // Schema may not exist
  }

  return {
    files: entries.sort((a, b) => a.path.localeCompare(b.path)),
    generated_at: new Date().toISOString(),
  };
}

/**
 * Validate current files against a stored manifest.
 * Returns a list of mismatches.
 */
export async function validateManifest(
  governanceRoot: string,
  manifest: Manifest
): Promise<{
  valid: boolean;
  mismatches: Array<{
    path: string;
    expected: string;
    actual: string | null;
    reason: string;
  }>;
}> {
  const mismatches: Array<{
    path: string;
    expected: string;
    actual: string | null;
    reason: string;
  }> = [];

  for (const entry of manifest.files) {
    const fullPath = join(governanceRoot, entry.path);
    try {
      const currentHash = await hashFile(fullPath);
      if (currentHash !== entry.hash) {
        mismatches.push({
          path: entry.path,
          expected: entry.hash,
          actual: currentHash,
          reason: "content_changed",
        });
      }
    } catch {
      mismatches.push({
        path: entry.path,
        expected: entry.hash,
        actual: null,
        reason: "file_missing",
      });
    }
  }

  return {
    valid: mismatches.length === 0,
    mismatches,
  };
}
