# Implement JM Homebrew Tap with Bottles Hosted on GitHub Packages

**Author:** Planning Agent (Claude Code)
**Date:** 2026-03-03
**Status:** draft
**Issue:** [#766](https://github.com/convergent-systems-co/dark-forge/issues/766)
**Branch:** JM/{feature}/{766}/homebrew-tap-github-packages

---

## 1. Objective

Establish a secure, repeatable Homebrew distribution system for JM-internal CLI tools using a private Homebrew tap repository (SET-Apps/homebrew-tap) with bottles (prebuilt binaries) hosted on GitHub Packages (GHCR). Developers will install via `brew tap jm-family/homebrew-jm` and `brew install jm-family/homebrew-jm/<formula>`, authenticated via GitHub tokens stored in Keychain.

This plan covers:
- Homebrew tap repository scaffolding with GitHub Packages integration
- CI/CD pipeline for cross-architecture bottle building (darwin arm64 + x86_64)
- Integration with existing GoReleaser pipeline
- Developer onboarding and troubleshooting
- Security hardening and token management
- Operational runbooks (release, rollback)

---

## 2. Rationale

### Context

The Dark Forge (dark-governance CLI) is distributed via GoReleaser to GitHub Releases. This proposal extends distribution to Homebrew, targeting JM engineers on macOS who prefer `brew install` over manual binary downloads.

### Why GitHub Packages (not GitHub Releases)

| Criterion | GitHub Releases | GitHub Packages |
|-----------|-----------------|-----------------|
| Private access control | Per-repo PAT | Per-repo PAT + OIDC |
| Auditing/SBOM | Basic | Enhanced (vulnerability scanning) |
| Package management | No versioning UI | Dedicated registry UI |
| Bottle hosting | Requires custom domain | Native GHCR support |
| Access model | Read: public (unauthenticated) | Read/write: authenticated only |

**Decision:** GitHub Packages provides better auditability and enforces authentication by design.

### Why a separate tap repo

Homebrew conventions recommend:
- Tap repos live outside the source repo (decouples release cadence)
- Formulas are authored in the tap, not the source repo
- Enables multiple formulas/binaries from a single organization

**Decision:** Create SET-Apps/homebrew-tap (follows Homebrew convention `owner/homebrew-name`).

### Bottles vs. source installation

| Method | Build time | Storage | Security |
|--------|-----------|---------|----------|
| Source (--HEAD) | ~2 min | Minimal | Source + build env exposure |
| Bottles (prebuilt) | None (download) | ~20 MB | Signed binaries, immutable |

**Decision:** Bottles provide speed and determinism; bottles are signed and published to GHCR.

### Why GitHub Actions for bottle building

- Tight integration with GHCR
- Native OIDC support (no secrets needed)
- macOS runners available (darwin arm64 + x86_64)
- Audit trail in Actions history

**Decision:** Use GitHub Actions matrix to build darwin_amd64 and darwin_arm64 bottles in parallel.

---

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.artifacts/plans/766-homebrew-tap-github-packages.md` | This implementation plan |
| `src/.goreleaser.yaml` (updated) | Add `brews:` section for bottle publishing to GHCR |
| `.github/workflows/homebrew-bottle-build.yml` | CI workflow for building bottles and pushing to GHCR |
| `.github/workflows/homebrew-formula-update.yml` | Workflow to auto-update formula SHA256 after release |
| `docs/guides/homebrew-installation.md` | Developer onboarding guide |
| `docs/guides/homebrew-release-process.md` | Release runbook for maintainers |
| `docs/guides/homebrew-troubleshooting.md` | Auth and fetch troubleshooting |
| `.artifacts/risk-register/766-homebrew-risks.md` | Risk register with 8+ risks and mitigations |

**Assumption:** SET-Apps/homebrew-tap repository already exists (or will be created). If not, a prerequisite step is needed.

### Files to Modify

| File | Change Description |
|------|-------------------|
| `src/.goreleaser.yaml` | Add `brews:` block to publish formulas and bottles to GitHub Packages + homebrew-tap repo. Update to reference GHCR URLs. |
| `src/Makefile` | No changes needed; existing build system is sufficient. |
| `README.md` (root) | Add Homebrew installation instructions section |
| `project.yaml` | No changes needed; already defines Go build conventions. |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files are removed in this plan. |

---

## 4. Approach

### Phase 1: Homebrew Tap Repository Setup

**Assumption:** We assume SET-Apps/homebrew-tap exists as a private GitHub repository. If not, it must be created first.

1. **Repository scaffolding** (if needed)
   - Clone/create SET-Apps/homebrew-tap
   - Initialize with Homebrew standard structure:
     ```
     homebrew-tap/
     ├── Formula/
     │   ├── dark-governance.rb
     │   └── jm-hello.rb (example placeholder)
     ├── README.md
     ├── LICENSE
     └── .github/workflows/
     ```
   - Add CODEOWNERS file (governance requirement)

2. **Branch protection rules**
   - Require PR reviews before merge (2 reviewers)
   - Require "governance-checks" status (if available)
   - Dismiss stale reviews on push

3. **Access control**
   - Restrict write access to convergent-systems-co/dark-forge admins
   - Grant read access to JM engineers via GitHub team (e.g., `jm-family/engineers`)
   - Document token rotation process (quarterly minimum)

### Phase 2: Formula Definition

**Step 1: Craft formula template**
   - Use Homebrew formula API v2 (Ruby DSL)
   - Define bottle blocks for darwin arm64 and x86_64
   - Include install, test, and post_install blocks
   - Add SHA256 checksums for bottles (populated by CI)

**Step 2: Create jm-hello example formula**
   - Placeholder formula for testing pipeline
   - Structure mirrors dark-governance.rb but points to a stub binary
   - Use this to validate bottle building and GHCR publishing

**Step 3: Create dark-governance.rb formula**
   - References releases in convergent-systems-co/dark-forge
   - Bottle URLs point to GHCR (ghcr.io/set-apps/homebrew-tap)
   - SHA256 checksums auto-populated by CI
   - Includes version constraint (e.g., `>= 0.5.0`)

### Phase 3: GitHub Actions Workflows

**Step 1: Bottle Build Workflow** (`homebrew-bottle-build.yml`)
   - Triggered on: release published in convergent-systems-co/dark-forge
   - Matrix: `[macos-latest-large] x [arm64, x86_64]`
   - Steps:
     1. Checkout source repo
     2. Extract binary from release assets (or build locally)
     3. Create bottle tarball (Homebrew format)
     4. Compute SHA256 checksums
     5. Push bottles to GHCR using Actions credentials
     6. Dispatch event to homebrew-tap repo with bottle metadata

**Step 2: Formula Update Workflow** (`homebrew-formula-update.yml`)
   - Triggered by: event from bottle-build workflow
   - Runs in SET-Apps/homebrew-tap repo
   - Steps:
     1. Update Formula/dark-governance.rb with new version and SHA256 checksums
     2. Commit to `main` or create PR (depending on strategy)
     3. Push updated formula to homebrew-tap repo

### Phase 4: GoReleaser Integration

**Step 1: Update src/.goreleaser.yaml**
   - Add `brews:` section with Homebrew tap configuration:
     ```yaml
     brews:
       - name: dark-governance
         repository:
           owner: SET-Apps
           name: homebrew-tap
           token: "{{ .Env.HOMEBREW_TAP_TOKEN }}"
         directory: Formula
         homepage: https://github.com/convergent-systems-co/dark-forge
         description: AI governance framework CLI for autonomous software delivery
         license: MIT
         install: |
           bin.install "dark-governance"
         test: |
           system "#{bin}/dark-governance", "version"
         bottles:
           - cellar: :any_skip_relocation
             sha256:
               arm64_monterey: "{{ .Env.ARM64_BOTTLE_SHA }}"
               x86_64_big_sur: "{{ .Env.X86_64_BOTTLE_SHA }}"
     ```
   - Token `HOMEBREW_TAP_TOKEN` must be a GitHub PAT with:
     - Scopes: `repo` (private repo access) + `read:packages` (GHCR read)
     - Rotation: quarterly minimum

**Step 2: Bottle publishing**
   - GoReleaser will auto-create/update formula in homebrew-tap
   - Bottles are hosted on GitHub Releases (existing behavior)
   - Future iteration: publish bottles to GHCR instead

### Phase 5: Developer Onboarding

**Step 1: Create `docs/guides/homebrew-installation.md`**
   - Prerequisites: macOS + Homebrew
   - Token setup: how to create, store in Keychain, export `HOMEBREW_GITHUB_API_TOKEN`
   - Install steps:
     ```bash
     brew tap jm-family/homebrew-tap
     brew install dark-governance
     ```
   - Verify: `dark-governance version`
   - Upgrade: `brew upgrade dark-governance`

**Step 2: Create `docs/guides/homebrew-troubleshooting.md`**
   - Common errors: 403 (auth), 404 (package not found), SSL errors
   - Debug steps: check token scope, verify private tap access, test with `curl`
   - Token rotation and management

**Step 3: Create `docs/guides/homebrew-release-process.md`**
   - Maintainer runbook:
     1. Tag release in convergent-systems-co/dark-forge (e.g., `v1.0.0`)
     2. GoReleaser builds binaries and creates GitHub release
     3. Bottle build workflow runs automatically
     4. Formula is auto-updated in homebrew-tap
     5. Verify: test `brew install` on both arm64 and x86_64 Macs
   - Rollback: pin version in formula, revert to previous release

### Phase 6: Testing & Validation

**Step 1: Local testing (developer machine)**
   - Clone homebrew-tap repo
   - Test formula syntax: `brew formula Formula/dark-governance.rb`
   - Simulate install (without actual download): `brew install --build-from-source dark-governance`

**Step 2: CI testing (Actions)**
   - Validate YAML syntax
   - Test GHCR authentication
   - Verify bottle checksums

**Step 3: End-to-end (integration)**
   - Create a test release (e.g., `v0.9.0-rc.1`)
   - Run bottle build workflow
   - Verify bottles in GHCR
   - Install via `brew` on staging Mac

---

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| **Unit** | Formula syntax | Test `.rb` formula files with `brew formula` linter |
| **Integration** | Bottle build | GitHub Actions matrix test: compile binaries on darwin arm64 + x86_64, create tarballs, push to GHCR |
| **Integration** | GHCR auth | Verify Actions OIDC token can read/write GHCR packages |
| **Integration** | Formula update | Verify CI can commit updated formula to homebrew-tap |
| **E2E** | Install flow | Install dark-governance via `brew install` on real macOS machines (arm64 + x86_64); run smoke test (`dark-governance version`) |
| **E2E** | Auth flow | Test dev onboarding: create token, store in Keychain, tap/install with authentication |
| **E2E** | Upgrade flow | Test `brew upgrade dark-governance` from v1.0.0 → v1.1.0 |
| **E2E** | Rollback | Revert to previous version via `brew switch dark-governance@1.0.0` (if multi-version support) or manual downgrade |

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **GitHub token leak** | Medium | Critical | Rotate tokens quarterly; use OIDC where possible; scan logs for secrets; implement GitHub secret scanning on tap repo; educate devs on Keychain usage |
| **Bottle checksum mismatch** | Low | High | Automated CI validation; manual verification before release; audit trail in git history |
| **GHCR package deletion** | Low | High | Immutable release tags; GitHub admin approval required for package deletion; document retention policy |
| **Cross-arch build failure** (e.g., arm64 only) | Medium | High | Use GitHub Actions matrix + macOS runners for both architectures; test each build independently; fallback to source install (`brew install --build-from-source`) |
| **Authentication (403/404) for private tap** | Medium | Medium | Clear error messages; troubleshooting guide; link to onboarding docs; verify GITHUB_TOKEN scope before release |
| **Stale formula in homebrew-tap** | Low | Medium | Automate formula updates via CI; require PR review before merge; CI validates formula syntax before commit |
| **Supply chain attack** (compromised bottle binary) | Low | Critical | Sign binaries (GPG); verify signatures in install scripts; audit source code in each release; CI reproducibility checks |
| **Homebrew registry outage** | Low | Medium | Document fallback: manual binary download from GitHub Releases; pin versions locally; maintain vendored copy of previous releases |

---

## 7. Dependencies

- [x] GitHub CLI (`gh`) installed and authenticated (already assumed in repo)
- [x] Homebrew installed on macOS dev machines (end-user dependency)
- [x] SET-Apps/homebrew-tap repository exists (prerequisite; assumes repo creation is out of scope)
- [x] GitHub Actions runners available (macOS-latest-large for arm64 + x86_64)
- [x] GoReleaser v1.18+ (supports `brews:` section; check current version in src/.goreleaser.yaml)
- [ ] HOMEBREW_TAP_TOKEN (GitHub PAT) created and stored in Actions secrets
- [ ] GitHub OIDC configured in SET-Apps/homebrew-tap (optional; reduces reliance on PATs)

---

## 8. Backward Compatibility

This change is **additive only**. Existing distribution methods are NOT affected:

- `go install github.com/convergent-systems-co/dark-forge/src/cmd/dark-governance@latest` → unchanged
- Curl install script (if present) → unchanged
- GitHub Releases → unchanged

Homebrew installation is a *new* option, not a replacement. No migration path needed.

---

## 9. Governance

Expected panel reviews and policy profile:

| Panel | Required | Rationale |
|-------|----------|-----------|
| **code-review** | Yes | CI workflows (YAML), formula Ruby code, documentation |
| **security-review** | Yes | Token management, GHCR authentication, private repo access, secret handling |
| **threat-modeling** | Yes | Supply chain attack vectors, token leakage, cross-arch build compromise |
| **cost-analysis** | Yes | GHCR storage costs, GitHub Actions runner costs (matrix builds) |
| **documentation-review** | Yes | Onboarding guides, troubleshooting, release process |
| **data-governance-review** | Yes | Token storage, audit logging, PII in logs (none expected) |
| **architecture-review** | Yes | Repository structure, CI/CD pipeline design, integration with GoReleaser |

**Policy Profile:** `infrastructure_critical` (controls distribution channel; impacts all JM engineers)

**Expected Risk Level:** `high` (token management, supply chain, authentication)

---

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-03 | Use GitHub Packages (GHCR) instead of GitHub Releases for bottles | Better access control, auditability, and enforced authentication by design |
| 2026-03-03 | Separate tap repo (SET-Apps/homebrew-tap) instead of inline formulas | Follows Homebrew conventions; decouples release cadence; enables multi-formula organization |
| 2026-03-03 | GitHub Actions for bottle building | Native OIDC support, tight GHCR integration, audit trail, cost-effective for matrix builds |
| 2026-03-03 | Include jm-hello example formula | Validates end-to-end pipeline before production (dark-governance) use; reduces risk of failed releases |
| 2026-03-03 | Document troubleshooting for 403/404/auth | Private repo + packages require developer onboarding; clear guidance reduces support burden |
| 2026-03-03 | Quarterly token rotation | Balances security (minimize token lifetime) with operational burden (avoid over-rotation) |

---

## Implementation Notes

### Assumptions

1. **SET-Apps/homebrew-tap repository exists.** If not, creation is a prerequisite step (likely automated via `brew tap-new` or manual GitHub API).

2. **GoReleaser v1.18+.** The `brews:` section is stable in recent GoReleaser versions. Verify version in `src/.goreleaser.yaml`.

3. **GitHub OIDC available.** OIDC is optional but recommended for reducing secret footprint. If unavailable, fallback to GitHub PATs (current approach).

4. **Bottle format vs. source.** Bottles are Homebrew-specific; if upstream build system changes, bottles may need rebuilding. GoReleaser handles this.

5. **Cross-architecture builds.** GitHub Actions macOS runners support both arm64 and x86_64; no cross-compilation needed.

### Known Constraints

- **Private tap = private formulas.** Public Homebrew repos cannot point to private taps. This is intentional; JM is internal.
- **Bottle lifetimes.** Homebrew caches bottles; if a bottle is yanked, developers must clear cache (`brew cache clean`) and reinstall.
- **Version constraints in formulas.** Homebrew does not support SemVer constraints (e.g., `>=1.0.0, <2.0.0`). Formula updates must be manual.
- **Signature verification.** Current approach does not include GPG signing. Future iteration recommended for production hardening.

### Recommended Future Work

1. **GPG signing for bottles.** Adds source authenticity; requires key management.
2. **SBOM (Software Bill of Materials).** GitHub Packages supports SBOM; can be generated by GoReleaser or CI.
3. **Multi-formula support.** Once dark-governance is stable, add jm-hello and other tools to the same tap.
4. **Cask support.** Homebrew Cask extends to apps; useful if GUI tools are added later.
5. **Auto-update notifications.** Homebrew has built-in update checks; consider push notifications via GitHub Discussions or Teams.

---

## Implementation Checklist (Definition of Done)

- [ ] **Planning**
  - [ ] This plan is reviewed and approved by Tech Lead
  - [ ] All assumptions documented and validated
  - [ ] Risk register signed off

- [ ] **Tap Repository**
  - [ ] SET-Apps/homebrew-tap repository created/verified
  - [ ] Branch protection rules configured
  - [ ] CODEOWNERS file added
  - [ ] Access control (read: engineers, write: admins) enforced

- [ ] **Formula Definitions**
  - [ ] `Formula/dark-governance.rb` created with bottle blocks
  - [ ] `Formula/jm-hello.rb` (example) created and tested
  - [ ] Syntax validated with `brew formula`
  - [ ] README with formula usage added

- [ ] **CI/CD Workflows**
  - [ ] `homebrew-bottle-build.yml` written, tested, and merged
  - [ ] `homebrew-formula-update.yml` written, tested, and merged
  - [ ] Both workflows pass Actions checks
  - [ ] GHCR authentication verified (OIDC or PAT)
  - [ ] Matrix build for arm64 + x86_64 validated

- [ ] **GoReleaser Integration**
  - [ ] `src/.goreleaser.yaml` updated with `brews:` section
  - [ ] `HOMEBREW_TAP_TOKEN` secret created in convergent-systems-co/dark-forge Actions
  - [ ] Test release run (v0.9.0-rc.1) triggers bottle build and formula update
  - [ ] Formula auto-updated in homebrew-tap with correct SHA256 checksums

- [ ] **Documentation**
  - [ ] `docs/guides/homebrew-installation.md` written (onboarding)
  - [ ] `docs/guides/homebrew-release-process.md` written (maintainer runbook)
  - [ ] `docs/guides/homebrew-troubleshooting.md` written (auth/fetch/errors)
  - [ ] Root `README.md` updated with Homebrew install section
  - [ ] All docs pass markdownlint and are reviewed

- [ ] **Testing & Validation**
  - [ ] Local formula syntax validation passes
  - [ ] Test release triggers CI; bottles build and push to GHCR
  - [ ] Developer onboarding flow tested on real macOS (arm64 + x86_64)
  - [ ] `brew install dark-governance` succeeds with correct binary
  - [ ] `dark-governance version` smoke test passes
  - [ ] `brew upgrade dark-governance` works end-to-end
  - [ ] Troubleshooting guide verified with intentional auth errors

- [ ] **Security & Governance**
  - [ ] All panel reviews completed (code, security, threat-modeling, cost, docs, data-governance, architecture)
  - [ ] Token rotation policy documented and enforced
  - [ ] No secrets leaked in logs or git history
  - [ ] GHCR package access restricted to authenticated users
  - [ ] Risk register reviewed and signed off

- [ ] **Operational Readiness**
  - [ ] Release runbook tested (tag → bottle build → formula update → install)
  - [ ] Rollback procedure documented and tested
  - [ ] Troubleshooting guide linked from installer
  - [ ] Support rotation plan in place for token issues

- [ ] **Merge & Close**
  - [ ] Implementation PR approved by Tech Lead + governance
  - [ ] Feature merged to main
  - [ ] Issue #766 closed with release notes
  - [ ] Plan status updated to `completed`

