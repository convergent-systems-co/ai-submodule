# Submodule Integrity Verification

**Author:** Code Manager (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** #405 — SC-1: Submodule Update Mechanism
**Branch:** itsfwcp/fix/405/submodule-integrity-verification

---

## 1. Objective

Add content integrity verification to the submodule update mechanism in init.sh and startup.md, ensuring that submodule updates are validated against a known-good state before being applied.

## 2. Rationale

Auto-update fetches from origin/main. If upstream is compromised, all consuming repos pull malicious content. Current defenses (pin opt-in, dirty state check) don't verify content integrity. Adding commit signature verification and critical file hash checks provides supply chain defense.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| GPG signature verification on all commits | Yes | Requires all contributors to sign; not enforceable externally |
| Content hash manifest for critical files | Yes | **Selected** — verifiable without GPG infrastructure |
| Staged rollout with canary repos | Yes | Requires multi-repo orchestration beyond this scope |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/integrity/critical-files.sha256` | SHA-256 hashes of critical governance files (policy profiles, schemas) |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `bin/init.sh` | Add integrity verification step after submodule update: verify critical file hashes match manifest |
| `governance/prompts/startup.md` | Add integrity check reference in Phase 1a (submodule update) |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Create `governance/integrity/critical-files.sha256`:
   - SHA-256 hashes for: all policy profiles (`governance/policy/*.yaml`), all schemas (`governance/schemas/*.json`), `bin/init.sh`
   - Format: standard `sha256sum` output
   - Updated as part of any PR that modifies these files
2. Add verification to `bin/init.sh`:
   - After submodule update, run `sha256sum --check governance/integrity/critical-files.sha256`
   - If verification fails: warn loudly, do not apply the update, keep the previous version
   - Verification is non-blocking in the first release (warning only) to allow adoption
3. Add to startup.md Phase 1a:
   - After submodule update step, reference the integrity check
   - If check fails: warn and continue with the previous submodule state

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | init.sh | Verify hash check runs after update |
| Manual | critical-files.sha256 | Verify all listed files exist and hashes are correct |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Hash manifest out of date | Medium | Low | Automated update in PR workflow; warning mode first |
| Legitimate updates blocked by stale hashes | Medium | Medium | Warning-only mode; hash update is part of the PR process |

## 7. Dependencies

- [ ] None — self-contained

## 8. Backward Compatibility

Additive. Hash verification is warning-only by default. Consuming repos without the manifest skip verification.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Supply chain security |
| code-review | Yes | Script changes |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | SHA-256 manifest over GPG | No GPG infrastructure required; simpler adoption |
| 2026-02-26 | Warning-only first release | Allows gradual adoption without blocking existing workflows |
