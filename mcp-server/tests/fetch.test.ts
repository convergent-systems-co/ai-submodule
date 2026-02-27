import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { join } from "node:path";
import { mkdtemp, rm, readFile, writeFile, mkdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import {
  computeContentHash,
  fetchWithTimeout,
  getCachedData,
  setCachedData,
  loadCatalog,
  fetchContent,
  getCacheDir,
  getCacheTTL,
  isOfflineMode,
  ENV,
  DEFAULTS,
  type CacheEntry,
} from "../src/fetch.js";

let tempDir: string;

beforeEach(async () => {
  tempDir = await mkdtemp(join(tmpdir(), "mcp-fetch-test-"));
  // Override cache dir to use temp directory
  process.env[ENV.CACHE_DIR] = tempDir;
  // Clear other env vars
  delete process.env[ENV.CATALOG_URL];
  delete process.env[ENV.CACHE_TTL];
  delete process.env[ENV.OFFLINE];
});

afterEach(async () => {
  // Clean up temp directory
  await rm(tempDir, { recursive: true, force: true });
  // Restore env vars
  delete process.env[ENV.CACHE_DIR];
  delete process.env[ENV.CATALOG_URL];
  delete process.env[ENV.CACHE_TTL];
  delete process.env[ENV.OFFLINE];
});

describe("computeContentHash", () => {
  it("returns a SHA-256 hex digest", () => {
    const hash = computeContentHash("hello world");
    // Known SHA-256 of "hello world"
    expect(hash).toBe(
      "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    );
  });

  it("returns different hashes for different content", () => {
    const hash1 = computeContentHash("content-a");
    const hash2 = computeContentHash("content-b");
    expect(hash1).not.toBe(hash2);
  });

  it("returns consistent hashes for same content", () => {
    const hash1 = computeContentHash("same content");
    const hash2 = computeContentHash("same content");
    expect(hash1).toBe(hash2);
  });

  it("returns a 64-character hex string", () => {
    const hash = computeContentHash("test");
    expect(hash).toHaveLength(64);
    expect(hash).toMatch(/^[0-9a-f]{64}$/);
  });
});

describe("getCacheDir", () => {
  it("uses env var when set", () => {
    process.env[ENV.CACHE_DIR] = "/custom/cache";
    expect(getCacheDir()).toBe("/custom/cache");
  });

  it("falls back to default when env var is not set", () => {
    delete process.env[ENV.CACHE_DIR];
    expect(getCacheDir()).toBe(DEFAULTS.CACHE_DIR);
  });
});

describe("getCacheTTL", () => {
  it("uses env var when set to a valid number", () => {
    process.env[ENV.CACHE_TTL] = "3600";
    expect(getCacheTTL()).toBe(3600);
  });

  it("falls back to default for invalid env var", () => {
    process.env[ENV.CACHE_TTL] = "not-a-number";
    expect(getCacheTTL()).toBe(DEFAULTS.CACHE_TTL);
  });

  it("falls back to default when env var is not set", () => {
    delete process.env[ENV.CACHE_TTL];
    expect(getCacheTTL()).toBe(DEFAULTS.CACHE_TTL);
  });

  it("accepts zero as a valid TTL", () => {
    process.env[ENV.CACHE_TTL] = "0";
    expect(getCacheTTL()).toBe(0);
  });
});

describe("isOfflineMode", () => {
  it("returns true when env var is '1'", () => {
    process.env[ENV.OFFLINE] = "1";
    expect(isOfflineMode()).toBe(true);
  });

  it("returns false when env var is not set", () => {
    delete process.env[ENV.OFFLINE];
    expect(isOfflineMode()).toBe(false);
  });

  it("returns false when env var is '0'", () => {
    process.env[ENV.OFFLINE] = "0";
    expect(isOfflineMode()).toBe(false);
  });

  it("returns false when env var is any non-'1' value", () => {
    process.env[ENV.OFFLINE] = "true";
    expect(isOfflineMode()).toBe(false);
  });
});

describe("setCachedData / getCachedData", () => {
  it("writes and reads a cache entry", async () => {
    const entry: CacheEntry = {
      data: "cached content",
      version: "1.0.0",
      timestamp: Date.now(),
      contentHash: computeContentHash("cached content"),
    };

    await setCachedData("test-key", entry);
    const result = await getCachedData("test-key");

    expect(result).not.toBeNull();
    expect(result!.data).toBe("cached content");
    expect(result!.version).toBe("1.0.0");
    expect(result!.contentHash).toBe(entry.contentHash);
  });

  it("returns null for non-existent cache key", async () => {
    const result = await getCachedData("non-existent");
    expect(result).toBeNull();
  });

  it("returns null for expired cache entry (TTL exceeded)", async () => {
    // Set TTL to 1 second
    process.env[ENV.CACHE_TTL] = "1";

    const entry: CacheEntry = {
      data: "old content",
      version: "1.0.0",
      timestamp: Date.now() - 2000, // 2 seconds ago
    };

    await setCachedData("expired-key", entry);
    const result = await getCachedData("expired-key");

    expect(result).toBeNull();
  });

  it("returns entry when TTL has not expired", async () => {
    process.env[ENV.CACHE_TTL] = "3600"; // 1 hour

    const entry: CacheEntry = {
      data: "fresh content",
      version: "1.0.0",
      timestamp: Date.now() - 1000, // 1 second ago
    };

    await setCachedData("fresh-key", entry);
    const result = await getCachedData("fresh-key");

    expect(result).not.toBeNull();
    expect(result!.data).toBe("fresh content");
  });

  it("returns null when version does not match", async () => {
    const entry: CacheEntry = {
      data: "version-1 content",
      version: "1.0.0",
      timestamp: Date.now(),
    };

    await setCachedData("version-key", entry);
    const result = await getCachedData("version-key", { version: "2.0.0" });

    expect(result).toBeNull();
  });

  it("returns entry when version matches", async () => {
    const entry: CacheEntry = {
      data: "matching content",
      version: "1.0.0",
      timestamp: Date.now(),
    };

    await setCachedData("version-match", entry);
    const result = await getCachedData("version-match", { version: "1.0.0" });

    expect(result).not.toBeNull();
    expect(result!.data).toBe("matching content");
  });

  it("returns null for malformed cache file", async () => {
    const filePath = join(tempDir, "bad-cache.json");
    await writeFile(filePath, "this is not json", "utf-8");

    const result = await getCachedData("bad-cache");
    expect(result).toBeNull();
  });

  it("returns null for cache entry with missing required fields", async () => {
    const filePath = join(tempDir, "incomplete.json");
    await writeFile(filePath, JSON.stringify({ data: "content" }), "utf-8");

    const result = await getCachedData("incomplete");
    expect(result).toBeNull();
  });

  it("creates nested cache directories", async () => {
    // Point cache dir to a non-existent nested path
    const nestedDir = join(tempDir, "deep", "nested", "cache");
    process.env[ENV.CACHE_DIR] = nestedDir;

    const entry: CacheEntry = {
      data: "nested content",
      version: "1.0.0",
      timestamp: Date.now(),
    };

    await setCachedData("nested-key", entry);
    const result = await getCachedData("nested-key");

    expect(result).not.toBeNull();
    expect(result!.data).toBe("nested content");
  });
});

describe("fetchWithTimeout", () => {
  it("throws on invalid URL", async () => {
    await expect(fetchWithTimeout("not-a-url")).rejects.toThrow();
  });

  it("throws on timeout with very short timeout", async () => {
    // Use a non-routable IP to force a timeout
    await expect(
      fetchWithTimeout("http://192.0.2.1/timeout-test", 1)
    ).rejects.toThrow();
  });

  it("throws on non-existent host", async () => {
    await expect(
      fetchWithTimeout("http://this-host-does-not-exist.invalid/test", 500)
    ).rejects.toThrow();
  });
});

describe("loadCatalog", () => {
  it("falls back to bundled when no remote URL and no cache", async () => {
    const result = await loadCatalog();
    expect(result.source).toBe("bundled");
    expect(result.data).toBeDefined();
  });

  it("returns bundled data with empty resources when no catalog file exists", async () => {
    const result = await loadCatalog({ governanceRoot: tempDir });
    expect(result.source).toBe("bundled");
    const parsed = JSON.parse(result.data);
    expect(parsed.resources).toEqual([]);
  });

  it("reads from bundled catalog.json when it exists", async () => {
    // Create a bundled catalog
    const governanceDir = join(tempDir, "governance");
    await mkdir(governanceDir, { recursive: true });
    const catalogData = JSON.stringify({ resources: ["test"], version: "bundled" });
    await writeFile(join(governanceDir, "catalog.json"), catalogData, "utf-8");

    const result = await loadCatalog({ governanceRoot: tempDir });
    expect(result.source).toBe("bundled");
    expect(result.data).toBe(catalogData);
  });

  it("uses cache when available and no remote URL", async () => {
    // Pre-populate cache
    const entry: CacheEntry = {
      data: JSON.stringify({ resources: ["cached-resource"], version: "cached" }),
      version: "latest",
      timestamp: Date.now(),
    };
    await setCachedData("catalog", entry);

    const result = await loadCatalog();
    expect(result.source).toBe("cache");
    const parsed = JSON.parse(result.data);
    expect(parsed.resources).toEqual(["cached-resource"]);
  });

  it("skips remote fetch in offline mode", async () => {
    process.env[ENV.OFFLINE] = "1";
    process.env[ENV.CATALOG_URL] = "http://example.com/catalog.json";

    const result = await loadCatalog();
    // Should not attempt remote fetch, falls through to cache or bundled
    expect(result.source).toBe("bundled");
  });

  it("skips remote fetch when no catalog URL is provided", async () => {
    delete process.env[ENV.CATALOG_URL];

    const result = await loadCatalog();
    expect(result.source).toBe("bundled");
  });

  it("respects version filtering on cache", async () => {
    // Pre-populate cache with version "1.0"
    const entry: CacheEntry = {
      data: JSON.stringify({ resources: ["v1"] }),
      version: "1.0",
      timestamp: Date.now(),
    };
    await setCachedData("catalog", entry);

    // Request version "2.0" — cache should miss
    const result = await loadCatalog({ version: "2.0", governanceRoot: tempDir });
    expect(result.source).toBe("bundled");
  });

  it("returns cache when version matches", async () => {
    const entry: CacheEntry = {
      data: JSON.stringify({ resources: ["v2"] }),
      version: "2.0",
      timestamp: Date.now(),
    };
    await setCachedData("catalog", entry);

    const result = await loadCatalog({ version: "2.0" });
    expect(result.source).toBe("cache");
    const parsed = JSON.parse(result.data);
    expect(parsed.resources).toEqual(["v2"]);
  });
});

describe("fetchContent", () => {
  it("returns cached content when available", async () => {
    const entry: CacheEntry = {
      data: "cached response body",
      version: "fetched",
      timestamp: Date.now(),
    };
    await setCachedData("my-content", entry);

    const result = await fetchContent("http://example.com/resource", "my-content");
    expect(result).toBe("cached response body");
  });

  it("validates hash on cached content", async () => {
    const content = "hash-validated content";
    const hash = computeContentHash(content);

    const entry: CacheEntry = {
      data: content,
      version: "fetched",
      timestamp: Date.now(),
      contentHash: hash,
    };
    await setCachedData("hash-key", entry);

    const result = await fetchContent("http://example.com/resource", "hash-key", {
      validateHash: hash,
    });
    expect(result).toBe(content);
  });

  it("rejects cached content with hash mismatch (in offline mode)", async () => {
    process.env[ENV.OFFLINE] = "1";

    const entry: CacheEntry = {
      data: "wrong content",
      version: "fetched",
      timestamp: Date.now(),
    };
    await setCachedData("bad-hash", entry);

    await expect(
      fetchContent("http://example.com/resource", "bad-hash", {
        validateHash: "expected-hash-that-does-not-match",
      })
    ).rejects.toThrow("not available offline");
  });

  it("throws in offline mode when no cache exists", async () => {
    process.env[ENV.OFFLINE] = "1";

    await expect(
      fetchContent("http://example.com/resource", "no-cache-key")
    ).rejects.toThrow("not available offline");
  });

  it("throws when remote fetch fails and no cache (non-existent host)", async () => {
    await expect(
      fetchContent(
        "http://this-host-does-not-exist.invalid/test",
        "fail-key"
      )
    ).rejects.toThrow();
  });
});

describe("parseArgs CLI flags", () => {
  // Test parseArgs directly since it is exported from index.ts
  it("parses --no-cache flag", async () => {
    const { parseArgs } = await import("../src/index.js");

    const args = parseArgs(["node", "index.js", "--no-cache"]);
    expect(args.noCache).toBe(true);
  });

  it("parses --refresh flag", async () => {
    const { parseArgs } = await import("../src/index.js");

    const args = parseArgs(["node", "index.js", "--refresh"]);
    expect(args.refresh).toBe(true);
  });

  it("parses --validate-hash flag", async () => {
    const { parseArgs } = await import("../src/index.js");

    const args = parseArgs(["node", "index.js", "--validate-hash"]);
    expect(args.validateHash).toBe(true);
  });

  it("parses --offline flag", async () => {
    const { parseArgs } = await import("../src/index.js");

    const args = parseArgs(["node", "index.js", "--offline"]);
    expect(args.offline).toBe(true);
  });

  it("parses --governance-root with value", async () => {
    const { parseArgs } = await import("../src/index.js");

    const args = parseArgs(["node", "index.js", "--governance-root", "/my/root"]);
    expect(args.governanceRoot).toBe("/my/root");
  });

  it("parses multiple flags together", async () => {
    const { parseArgs } = await import("../src/index.js");

    const args = parseArgs([
      "node",
      "index.js",
      "--governance-root",
      "/root",
      "--no-cache",
      "--offline",
      "--validate-hash",
      "--refresh",
    ]);
    expect(args.governanceRoot).toBe("/root");
    expect(args.noCache).toBe(true);
    expect(args.offline).toBe(true);
    expect(args.validateHash).toBe(true);
    expect(args.refresh).toBe(true);
  });

  it("returns empty args for no flags", async () => {
    const { parseArgs } = await import("../src/index.js");

    const args = parseArgs(["node", "index.js"]);
    expect(args.governanceRoot).toBeUndefined();
    expect(args.noCache).toBeUndefined();
    expect(args.refresh).toBeUndefined();
    expect(args.validateHash).toBeUndefined();
    expect(args.offline).toBeUndefined();
  });
});
