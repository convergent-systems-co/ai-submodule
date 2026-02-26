# Submodule Integrity Verification

**Author:** Code Manager (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** #405 — SC-1: Submodule Update Mechanism

**Author:** Coder Agent
**Date:** 2026-02-26
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/405
**Branch:** itsfwcp/fix/405/submodule-integrity-verification

---

## 1. Objective

Add content integrity verification to the submodule update mechanism in init.sh and startup.md, ensuring that submodule updates are validated against a known-good state before being applied.

Add SHA-256 integrity verification for critical governance files (policy profiles, JSON schemas, and `bin/init.sh`) to detect unauthorized modifications after a submodule update. This is the first mitigation for the supply chain risk identified in Issue #405 (SC-1: Submodule Update Mechanism).

## 2. Rationale

Auto-update fetches from origin/main. If upstream is compromised, all consuming repos pull malicious content. Current defenses (pin opt-in, dirty state check) don't verify content integrity. Adding commit signature verification and critical file hash checks provides supply chain defense.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| GPG signature verification on all commits | Yes | Requires all contributors to sign; not enforceable externally |
| Content hash manifest for critical files | Yes | **Selected** — verifiable without GPG infrastructure |
| Staged rollout with canary repos | Yes | Requires multi-repo orchestration beyond this scope |

The `.ai` submodule auto-update mechanism fetches from `origin/main` without verifying content integrity. If the upstream repository is compromised, all consuming repos would silently pull malicious governance files. A SHA-256 manifest provides a lightweight, portable integrity check.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| GPG signature verification | Yes | Requires key management infrastructure; deferred to future phase |
| Git commit signature checks | Yes | Not all contributors sign commits; enforcement gap |
| SHA-256 manifest (chosen) | Yes | Simple, portable, no external dependencies |
| Staged rollout with canary | Yes | Higher complexity; planned for future phase |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/integrity/critical-files.sha256` | SHA-256 hashes of critical governance files (policy profiles, schemas) |
| `governance/integrity/critical-files.sha256` | SHA-256 manifest of all critical governance files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `bin/init.sh` | Add integrity verification step after submodule update: verify critical file hashes match manifest |
| `governance/prompts/startup.md` | Add integrity check reference in Phase 1a (submodule update) |

| File | Change Description |
|------|-------------------|
| `bin/init.sh` | Add integrity verification step after submodule update |
| `governance/prompts/startup.md` | Add integrity check reference in Phase 1a |

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

### Implementation Details

1. Generate SHA-256 hashes for all critical files: `governance/policy/*.yaml`, `governance/schemas/*.json`, `bin/init.sh`
2. Create `governance/integrity/critical-files.sha256` with hashes in standard `sha256sum` format
3. Add integrity verification to `bin/init.sh`:
   - Runs after submodule update, before symlinks
   - Portable: uses `sha256sum` (Linux) or `shasum -a 256` (macOS)
   - Advisory: warns on mismatch but does not block execution
   - Backward compatible: skips silently if manifest does not exist
4. Add step 6 to Phase 1a of `startup.md` documenting the integrity check
5. Update manifest hash for `bin/init.sh` after modification

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | init.sh | Verify hash check runs after update |
| Manual | critical-files.sha256 | Verify all listed files exist and hashes are correct |
| Manual | Manifest verification | Run `shasum -a 256 --check governance/integrity/critical-files.sha256` to confirm all hashes pass |
| Manual | init.sh execution | Run `bash bin/init.sh` to verify integrity check runs without errors |
| Manual | Failure case | Temporarily modify a policy file and verify the warning output |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Hash manifest out of date | Medium | Low | Automated update in PR workflow; warning mode first |
| Legitimate updates blocked by stale hashes | Medium | Medium | Warning-only mode; hash update is part of the PR process |
| Manifest becomes stale after policy/schema changes | Medium | Low | Document that manifest must be updated when critical files change |
| SHA-256 tool not available on target platform | Low | Low | Graceful skip with informative message |
| False positives from line ending differences | Low | Low | Files are committed with consistent line endings via .gitattributes |

## 7. Dependencies

- [ ] None — self-contained
- [x] No external dependencies — uses only standard system tools (`sha256sum`/`shasum`)

## 8. Backward Compatibility

Additive. Hash verification is warning-only by default. Consuming repos without the manifest skip verification.

Fully backward compatible. The integrity check:
- Skips silently if the manifest file does not exist
- Is advisory-only (warning, not error)
- Does not change init.sh exit behavior

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Supply chain security |
| code-review | Yes | Script changes |
| security-review | Yes | Security-focused change to supply chain verification |
| threat-modeling | Yes | Addresses identified supply chain threat SC-1 |
| code-review | Yes | New shell code in init.sh |
| documentation-review | Yes | startup.md updated |
| cost-analysis | Yes | Standard requirement |
| data-governance-review | Yes | Standard requirement |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | SHA-256 manifest over GPG | No GPG infrastructure required; simpler adoption |
| 2026-02-26 | Warning-only first release | Allows gradual adoption without blocking existing workflows |
| 2026-02-26 | Warning-only, not blocking | First release should be advisory to avoid disrupting existing workflows |
| 2026-02-26 | Line-by-line parsing instead of `sha256sum --check` | More portable and allows better error reporting per file |
| 2026-02-26 | Include signal-adapters and schema examples | These subdirectories contain governance-critical configuration |
