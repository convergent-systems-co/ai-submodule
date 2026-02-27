import { readFile, writeFile, mkdir, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { homedir } from "node:os";
import { createHash } from "node:crypto";

/**
 * Environment variable names for hybrid fetch configuration.
 */
export const ENV = {
  CATALOG_URL: "AI_MCP_CATALOG_URL",
  CACHE_DIR: "AI_MCP_CACHE_DIR",
  CACHE_TTL: "AI_MCP_CACHE_TTL",
  OFFLINE: "AI_MCP_OFFLINE",
} as const;

/**
 * Default configuration values.
 */
export const DEFAULTS = {
  CACHE_DIR: join(homedir(), ".ai-submodule-mcp", "cache"),
  CACHE_TTL: 14400, // 4 hours in seconds
  FETCH_TIMEOUT: 3000, // 3 seconds
} as const;

/**
 * A cached content entry stored on disk.
 */
export interface CacheEntry {
  data: string;
  version: string;
  timestamp: number;
  contentHash?: string;
}

/**
 * Options for the fetchContent function.
 */
export interface FetchContentOptions {
  validateHash?: string;
}

/**
 * Result of a 3-tier catalog load operation.
 */
export interface CatalogResult {
  data: string;
  source: "remote" | "cache" | "bundled";
}

/**
 * Resolve the cache directory from env or use the default.
 */
export function getCacheDir(): string {
  return process.env[ENV.CACHE_DIR] || DEFAULTS.CACHE_DIR;
}

/**
 * Resolve the cache TTL in seconds from env or use the default.
 */
export function getCacheTTL(): number {
  const envVal = process.env[ENV.CACHE_TTL];
  if (envVal) {
    const parsed = parseInt(envVal, 10);
    if (!isNaN(parsed) && parsed >= 0) {
      return parsed;
    }
  }
  return DEFAULTS.CACHE_TTL;
}

/**
 * Check whether offline mode is enabled via env var.
 */
export function isOfflineMode(): boolean {
  return process.env[ENV.OFFLINE] === "1";
}

/**
 * Compute a SHA-256 hex digest of the given content string.
 */
export function computeContentHash(content: string): string {
  return createHash("sha256").update(content, "utf-8").digest("hex");
}

/**
 * HTTP fetch with an AbortController timeout.
 *
 * Uses the native `fetch` available in Node 18+.
 * Returns the response body as a string, or throws on timeout/network error.
 */
export async function fetchWithTimeout(
  url: string,
  timeoutMs: number = DEFAULTS.FETCH_TIMEOUT
): Promise<string> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.text();
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Read a cache entry from disk. Returns null if the cache file does not
 * exist, is malformed, or has expired based on the current TTL.
 *
 * When `version` is provided, the cached entry must match that version
 * or it will be treated as stale.
 */
export async function getCachedData(
  key: string,
  options?: { version?: string }
): Promise<CacheEntry | null> {
  const cacheDir = getCacheDir();
  const filePath = join(cacheDir, `${key}.json`);

  try {
    const raw = await readFile(filePath, "utf-8");
    const entry: CacheEntry = JSON.parse(raw);

    // Validate required fields
    if (
      typeof entry.data !== "string" ||
      typeof entry.version !== "string" ||
      typeof entry.timestamp !== "number"
    ) {
      return null;
    }

    // Check TTL
    const ttl = getCacheTTL();
    const ageSeconds = (Date.now() - entry.timestamp) / 1000;
    if (ageSeconds > ttl) {
      return null;
    }

    // Check version match
    if (options?.version && entry.version !== options.version) {
      return null;
    }

    return entry;
  } catch {
    return null;
  }
}

/**
 * Write a cache entry to disk. Creates the cache directory if it does
 * not already exist.
 */
export async function setCachedData(
  key: string,
  entry: CacheEntry
): Promise<void> {
  const cacheDir = getCacheDir();
  const filePath = join(cacheDir, `${key}.json`);

  try {
    await mkdir(dirname(filePath), { recursive: true });
    await writeFile(filePath, JSON.stringify(entry, null, 2), "utf-8");
  } catch {
    // Cache write failures are non-fatal — log to stderr and continue
    console.error(`[ai-submodule-mcp] Warning: failed to write cache for key "${key}"`);
  }
}

/**
 * Load a catalog using the 3-tier fallback strategy:
 *
 * 1. **Remote** — Fetch from `catalogUrl` (skipped in offline mode)
 * 2. **Cache** — Read from disk cache at the configured cache directory
 * 3. **Bundled** — Fall back to local filesystem content at `governanceRoot`
 *
 * @param catalogUrl  Remote catalog URL (or reads from AI_MCP_CATALOG_URL env var)
 * @param version     Expected version string; cached entries must match
 * @param governanceRoot  Local filesystem root for bundled fallback
 */
export async function loadCatalog(
  options?: {
    catalogUrl?: string;
    version?: string;
    governanceRoot?: string;
  }
): Promise<CatalogResult> {
  const catalogUrl = options?.catalogUrl || process.env[ENV.CATALOG_URL];
  const version = options?.version || "latest";
  const cacheKey = "catalog";

  // Tier 1: Remote fetch (skip in offline mode)
  if (catalogUrl && !isOfflineMode()) {
    try {
      const data = await fetchWithTimeout(catalogUrl);
      const entry: CacheEntry = {
        data,
        version,
        timestamp: Date.now(),
        contentHash: computeContentHash(data),
      };
      // Cache the remote response for subsequent offline use
      await setCachedData(cacheKey, entry);
      return { data, source: "remote" };
    } catch {
      // Remote fetch failed — fall through to cache
      console.error("[ai-submodule-mcp] Remote catalog fetch failed, trying cache...");
    }
  }

  // Tier 2: Disk cache
  const cached = await getCachedData(cacheKey, { version });
  if (cached) {
    return { data: cached.data, source: "cache" };
  }

  // Tier 3: Bundled local fallback
  if (options?.governanceRoot) {
    const bundledPath = join(options.governanceRoot, "governance", "catalog.json");
    try {
      const data = await readFile(bundledPath, "utf-8");
      return { data, source: "bundled" };
    } catch {
      // Bundled catalog not found — try a minimal manifest
    }
  }

  // Final fallback: return an empty catalog
  return { data: JSON.stringify({ resources: [], version }), source: "bundled" };
}

/**
 * Fetch content from a URL with caching and optional hash validation.
 *
 * - In offline mode, only the cache is checked.
 * - When `validateHash` is provided, the fetched/cached content's SHA-256
 *   must match or the fetch is treated as failed.
 * - Results are cached to disk for subsequent offline access.
 */
export async function fetchContent(
  url: string,
  cacheKey: string,
  options?: FetchContentOptions
): Promise<string> {
  // Try cache first
  const cached = await getCachedData(cacheKey);
  if (cached) {
    // Validate hash if requested
    if (options?.validateHash) {
      const hash = computeContentHash(cached.data);
      if (hash !== options.validateHash) {
        // Hash mismatch — treat cache as stale and re-fetch
        console.error(`[ai-submodule-mcp] Cache hash mismatch for "${cacheKey}", re-fetching...`);
      } else {
        return cached.data;
      }
    } else {
      return cached.data;
    }
  }

  // If offline, we cannot fetch remotely
  if (isOfflineMode()) {
    throw new Error(
      `Content not available offline: no valid cache for "${cacheKey}"`
    );
  }

  // Fetch remotely
  const data = await fetchWithTimeout(url);

  // Validate hash if requested
  if (options?.validateHash) {
    const hash = computeContentHash(data);
    if (hash !== options.validateHash) {
      throw new Error(
        `Content hash mismatch for "${cacheKey}": expected ${options.validateHash}, got ${hash}`
      );
    }
  }

  // Cache the result
  const entry: CacheEntry = {
    data,
    version: "fetched",
    timestamp: Date.now(),
    contentHash: computeContentHash(data),
  };
  await setCachedData(cacheKey, entry);

  return data;
}
