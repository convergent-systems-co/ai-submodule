import { describe, it, expect } from "vitest";
import { join } from "node:path";
import { generateManifest, validateManifest } from "../src/manifest.js";

const GOVERNANCE_ROOT = join(__dirname, "..", "..");

describe("generateManifest", () => {
  it("generates a manifest with file entries", async () => {
    const manifest = await generateManifest(GOVERNANCE_ROOT);

    expect(manifest.files.length).toBeGreaterThan(0);
    expect(manifest.generated_at).toBeTruthy();
    // Should be a valid ISO 8601 timestamp
    expect(() => new Date(manifest.generated_at)).not.toThrow();
  });

  it("includes review prompts in manifest", async () => {
    const manifest = await generateManifest(GOVERNANCE_ROOT);

    const reviewFiles = manifest.files.filter((f) =>
      f.path.startsWith("governance/prompts/reviews/")
    );
    expect(reviewFiles.length).toBe(20);
  });

  it("includes policy profiles in manifest", async () => {
    const manifest = await generateManifest(GOVERNANCE_ROOT);

    const policyFiles = manifest.files.filter((f) =>
      f.path.startsWith("governance/policy/")
    );
    expect(policyFiles.length).toBe(4);
  });

  it("includes SHA-256 hashes", async () => {
    const manifest = await generateManifest(GOVERNANCE_ROOT);

    for (const entry of manifest.files) {
      // SHA-256 hashes are 64 hex chars
      expect(entry.hash).toMatch(/^[a-f0-9]{64}$/);
      expect(entry.size).toBeGreaterThan(0);
    }
  });

  it("files are sorted by path", async () => {
    const manifest = await generateManifest(GOVERNANCE_ROOT);

    const paths = manifest.files.map((f) => f.path);
    const sorted = [...paths].sort();
    expect(paths).toEqual(sorted);
  });
});

describe("validateManifest", () => {
  it("validates a freshly generated manifest as valid", async () => {
    const manifest = await generateManifest(GOVERNANCE_ROOT);
    const result = await validateManifest(GOVERNANCE_ROOT, manifest);

    expect(result.valid).toBe(true);
    expect(result.mismatches).toHaveLength(0);
  });

  it("detects missing files", async () => {
    const manifest = await generateManifest(GOVERNANCE_ROOT);

    // Add a fake entry
    manifest.files.push({
      path: "governance/prompts/reviews/nonexistent-review.md",
      hash: "0000000000000000000000000000000000000000000000000000000000000000",
      size: 100,
    });

    const result = await validateManifest(GOVERNANCE_ROOT, manifest);

    expect(result.valid).toBe(false);
    expect(result.mismatches.length).toBe(1);
    expect(result.mismatches[0].reason).toBe("file_missing");
  });

  it("detects content changes", async () => {
    const manifest = await generateManifest(GOVERNANCE_ROOT);

    // Corrupt a hash
    if (manifest.files.length > 0) {
      manifest.files[0].hash = "a".repeat(64);

      const result = await validateManifest(GOVERNANCE_ROOT, manifest);

      expect(result.valid).toBe(false);
      expect(
        result.mismatches.some((m) => m.reason === "content_changed")
      ).toBe(true);
    }
  });
});
