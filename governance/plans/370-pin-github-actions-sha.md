# Pin GitHub Actions to Full SHA Hashes

**Author:** Team Lead (agent)
**Date:** 2026-02-26
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/370
**Branch:** NETWORK_ID/fix/370/pin-actions-sha

---

## 1. Objective

Pin all GitHub Actions in `deploy-docs.yml` to immutable commit SHA hashes instead of mutable major version tags, improving supply chain integrity.

## 2. Rationale

Mutable version tags (e.g., `@v4`) can be force-pushed by the action maintainer. Pinning to SHA hashes ensures reproducible builds.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| SHA pinning (chosen) | Yes | — |
| Keep version tags | Yes | Does not defend against supply chain attacks |
| Dependabot for updates | Yes | Complementary, not a replacement — can be added later |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | — |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `.github/workflows/deploy-docs.yml` | Replace `@v4`/`@v5`/`@v3` tags with full SHA hashes and version comments |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | — |

## 4. Approach

1. Replace the 4 action references with their SHA-pinned equivalents:
   - `actions/checkout@v4` → `actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4`
   - `actions/setup-python@v5` → `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5`
   - `actions/upload-pages-artifact@v3` → `actions/upload-pages-artifact@56afc609e74202658d3ffba0e8f6dda462b719fa # v3`
   - `actions/deploy-pages@v4` → `actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e # v4`

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| CI validation | deploy-docs workflow | Workflow runs with SHA-pinned actions |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SHA becomes outdated | Low | Low | Version comment makes it easy to find updates; Dependabot can be added |

## 7. Dependencies

- None

## 8. Backward Compatibility

N/A — CI-only change.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Supply chain security change |
| threat-modeling | Yes | Default policy requirement |
| cost-analysis | Yes | Default policy requirement |
| documentation-review | Yes | Default policy requirement |
| data-governance-review | Yes | Default policy requirement |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Pin to current latest SHA for each major version | Verified via GitHub API |
