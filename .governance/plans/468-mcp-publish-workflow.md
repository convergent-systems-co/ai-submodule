# MCP Server Publish Workflow for GitHub Packages

**Author:** Claude (Coder persona)
**Date:** 2026-02-27
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/468
**Branch:** itsfwcp/feat/468/mcp-publish-workflow

---

## 1. Objective

Add a GitHub Actions workflow that publishes the MCP server (`mcp-server/`) to GitHub Packages as both an npm package (`@jm-packages/ai-submodule-mcp`) and a Docker image (`ghcr.io`) on release events, with a manual dry-run option.

## 2. Rationale

The MCP server at `mcp-server/` is configured with `publishConfig.registry: https://npm.pkg.github.com` and has a Dockerfile, but no CI/CD workflow exists to automate publishing. Manual publishing is error-prone and inconsistent. A release-triggered workflow ensures every tagged release is automatically built, tested, and published to both registries.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Manual npm publish | Yes | Error-prone, no audit trail, requires local credentials |
| Publish on push to main | Yes | Too frequent; releases should be intentional via GitHub Releases |
| Single job (build + publish) | Yes | Separating build/test from publish provides a quality gate and allows parallel npm + Docker publishing |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.github/workflows/publish-mcp.yml` | GitHub Actions workflow for building, testing, and publishing the MCP server |
| `.governance/plans/468-mcp-publish-workflow.md` | This governance plan |

### Files to Modify

| File | Change Description |
|------|-------------------|
| N/A | No existing files modified |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files deleted |

## 4. Approach

1. Create `.github/workflows/publish-mcp.yml` with three jobs:
   - `build-and-test`: Checkout, install dependencies, build TypeScript, run tests
   - `publish-npm`: Publish to GitHub Packages npm registry (depends on build-and-test)
   - `publish-docker`: Build and push multi-arch Docker image to ghcr.io (depends on build-and-test)
2. Configure triggers: `release.published` for automated publishing, `workflow_dispatch` with `dry_run` input for manual testing
3. Use `defaults.run.working-directory: mcp-server` to scope npm commands to the MCP server directory
4. Add concurrency control to prevent duplicate publish runs
5. Publish jobs only execute on release events or non-dry-run manual dispatches

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Dry run | workflow_dispatch | Manual trigger with `dry_run: true` validates build-and-test without publishing |
| Release trigger | release event | Creating a GitHub Release triggers the full pipeline |
| YAML lint | workflow syntax | Valid YAML structure verified by GitHub Actions parser on push |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| npm publish fails due to auth | Low | Med | Uses `GITHUB_TOKEN` which is automatically available with `packages: write` permission |
| Docker build fails on multi-arch | Low | Med | Uses `docker/setup-buildx-action` which handles QEMU setup for cross-compilation |
| Accidental publish on dry run | Low | High | Explicit `if` condition gates publish jobs; dry_run=true skips both publish jobs |

## 7. Dependencies

- [x] MCP server package.json with publishConfig — already configured
- [x] MCP server Dockerfile — already exists
- [ ] GitHub Packages enabled on the repository — non-blocking, standard GitHub feature

## 8. Backward Compatibility

No breaking changes. This is a new workflow that does not affect any existing workflows or functionality. The `jm-compliance.yml` enterprise-locked workflow is not modified.

## 9. Governance

Expected panel reviews and policy profile:

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New workflow file needs structural review |
| security-review | Yes | Publishing workflow handles credentials (GITHUB_TOKEN) |
| documentation-review | Yes | Workflow is self-documenting via YAML comments |
| cost-analysis | Yes | GitHub Actions compute costs for build + multi-arch Docker |
| threat-modeling | Yes | Supply chain security for published packages |
| data-governance-review | Yes | No PII involved in build/publish pipeline |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Use node 22 for build | Matches issue specification; package.json requires >=18 so 22 is compatible |
| 2026-02-27 | Use version tags instead of pinned SHAs for actions | Consistent with newer workflows in the repo (prompt-eval.yml, propagate-submodule.yml) |
| 2026-02-27 | Set concurrency cancel-in-progress: false | Publish operations should not be cancelled mid-flight to avoid partial releases |
| 2026-02-27 | Multi-arch Docker build (amd64 + arm64) | Supports both Intel and ARM deployments |
