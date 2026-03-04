# MCP Server Hybrid Fetch Architecture with 3-Tier Loading

**Author:** Coder (AI Agent)
**Date:** 2026-02-27
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/466
**Branch:** NETWORK_ID/feat/466/mcp-hybrid-fetch

---

## 1. Objective

Add a hybrid fetch system to the MCP server that supports 3-tier content loading: remote fetch, disk cache, and local filesystem fallback. This enables the MCP server to serve governance content from remote catalogs while maintaining offline resilience through caching and bundled fallback data.

## 2. Rationale

The current MCP server reads all content directly from the local filesystem. Adding a hybrid fetch layer enables remote catalog support (for centralized governance content distribution) while maintaining offline reliability through tiered fallback.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Remote-only fetch | Yes | No offline support; fragile in disconnected environments |
| Local-only (current) | Yes | No remote catalog support; cannot centralize governance content |
| Hybrid 3-tier with cache | Yes (chosen) | N/A — provides remote capability with offline resilience |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `mcp-server/src/fetch.ts` | Core hybrid fetch module with cache, remote fetch, and fallback logic |
| `mcp-server/tests/fetch.test.ts` | Unit tests for all fetch module functionality |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `mcp-server/src/index.ts` | Add CLI flags: `--no-cache`, `--refresh`, `--validate-hash`, `--offline` |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. Create `mcp-server/src/fetch.ts` with all exported functions
2. Update `parseArgs()` in `index.ts` to support new CLI flags
3. Create comprehensive unit tests in `mcp-server/tests/fetch.test.ts`
4. Verify build passes with `npm run build`

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | fetch.ts — all functions | Cache read/write/TTL expiry, 3-tier fallback, content hash validation, offline mode, timeout |
| Unit | index.ts — parseArgs | New CLI flag parsing |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Native fetch not available on Node < 18 | Low | High | `engines` in package.json already requires Node >= 18 |
| Cache directory permissions | Low | Medium | Graceful fallback when cache is unwritable |
| Network timeout in CI | Low | Low | Default 3s timeout with configurable override |

## 7. Dependencies

- [x] Node.js >= 18 (for native `fetch`) — non-blocking, already required
- [x] Node.js `crypto` module — built-in, non-blocking

## 8. Backward Compatibility

Fully backward compatible. All new functionality is additive. Existing MCP server behavior is unchanged when no env vars or CLI flags are set. The fetch module is opt-in — nothing in the existing codebase depends on it.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New module with network and filesystem operations |
| security-review | Yes | Network fetch, cache filesystem operations, hash validation |
| threat-modeling | Yes | Remote content fetching introduces new attack surface |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Use native fetch instead of node-fetch | Node 18+ is already required; avoids extra dependency |
| 2026-02-27 | Use vitest for tests | Already configured in package.json |
| 2026-02-27 | SHA-256 for content hashing | Standard, built into Node crypto |
