# Add Go Build & Release Pipeline

**Author:** Claude (PM Agent)
**Date:** 2026-03-03
**Status:** draft
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/745
**Branch:** itsfwcp/ci/745/go-build-release-pipeline

---

## 1. Objective

Add CI/CD pipelines to build, test, lint, sign, and release the Go binary (`dark-governance`) across all supported platforms (darwin/amd64, darwin/arm64, linux/amd64, linux/arm64, windows/amd64). This provides the distribution infrastructure required by #743 (Go binary rewrite) and #744 (go:embed distribution model). Without this pipeline, the Go binary has no automated path from source to user.

## 2. Rationale

The repository currently has no Go build or release infrastructure. One version tag (`v1.0.1`) exists but was created manually. Existing publish workflows (`publish-engine.yml`, `publish-mcp.yml`, `docker-publish.yml`) demonstrate established patterns: `release` event or `v*` tag triggers, `actions/checkout@v4`, artifact upload, and concurrency controls. The new Go pipeline follows these patterns while adding GoReleaser for cross-compilation and Cosign for keyless signing.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Manual `go build` per platform | Yes | Error-prone, no reproducibility, no signing, no changelog |
| GitHub Actions matrix build (no GoReleaser) | Yes | Requires custom cross-compilation scripts, manual checksums, manual release asset upload; GoReleaser handles all of this declaratively |
| goreleaser/goreleaser-action alone (no CI build job) | Yes | PRs would not be validated; bugs reach main before release |
| Tag-triggered release only (no PR CI) | Yes | No feedback loop on PRs touching Go source; regressions merge undetected |
| Automatic release on merge to main | Yes | Premature releases; governance pipeline must approve before tagging; manual tag push gives explicit release control |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.github/workflows/go-build.yml` | CI workflow: build, test, vet, lint on every PR/push touching `src/` |
| `.github/workflows/go-release.yml` | Release workflow: GoReleaser + Cosign on `v*` tag push |
| `src/.goreleaser.yaml` | GoReleaser v2 configuration for cross-compilation, signing, Homebrew tap, changelog |
| `src/scripts/install.sh` | Curl-pipe-bash install script for macOS/Linux |

### Files to Modify

| File | Change Description |
|------|-------------------|
| N/A | No existing files modified. The `src/` directory does not exist yet; it will be created by #743. These files are additive. |

### Files to Delete

N/A

## 4. Approach

### Step 1: Create CI Build & Test Workflow (`.github/workflows/go-build.yml`)

- **Trigger:** `pull_request` and `push` to `main`, filtered to `src/**`, `go.mod`, `go.sum` paths
- **Jobs:**
  - `test` — Matrix across `ubuntu-latest`, `macos-latest`, `windows-latest`. Steps: checkout, `actions/setup-go@v5` with `go-version-file: src/go.mod`, `go test ./... -race -coverprofile=coverage.out`, `go vet ./...`
  - `lint` — Single runner (`ubuntu-latest`). Steps: checkout, setup-go, `golangci/golangci-lint-action@v6` with `working-directory: src`
- **Pattern alignment:** Uses `actions/checkout@v4` and matrix strategy consistent with existing workflows. No concurrency group needed since GitHub auto-cancels superseded PR runs.

### Step 2: Create Release Workflow (`.github/workflows/go-release.yml`)

- **Trigger:** `push.tags: ['v*']` — matches existing `docker-publish.yml` pattern
- **Permissions:** `contents: write` (create releases, upload assets), `id-token: write` (Sigstore OIDC), `packages: write` (GHCR if needed)
- **Runner:** `macos-latest` — required for future macOS notarization; GoReleaser handles cross-compilation regardless of host OS
- **Steps:**
  1. `actions/checkout@v4` with `fetch-depth: 0` (GoReleaser needs full history for changelog)
  2. `actions/setup-go@v5` with `go-version-file: src/go.mod`
  3. `sigstore/cosign-installer@v3`
  4. `goreleaser/goreleaser-action@v6` with `version: '~> v2'`, `args: release --clean`, `workdir: src`
- **Secrets:** `GITHUB_TOKEN` (automatic), `HOMEBREW_TAP_TOKEN` (must be configured as repo secret — PAT with `repo` scope on `SET-Apps/homebrew-tap`)
- **Concurrency:** `group: release-${{ github.ref }}`, `cancel-in-progress: false` (never cancel a release in progress)

### Step 3: Create GoReleaser Configuration (`src/.goreleaser.yaml`)

- **Version:** GoReleaser v2 format (`version: 2`)
- **Build:** Single binary `dark-governance` from `./cmd/dark-governance`, `CGO_ENABLED=0`, ldflags inject `version`, `commit`, `date`
- **Targets:** darwin/amd64, darwin/arm64, linux/amd64, linux/arm64, windows/amd64 (windows/arm64 excluded)
- **Archives:** `.tar.gz` default, `.zip` override for Windows
- **Checksums:** SHA-256 in `checksums.txt`
- **Signing:** Cosign keyless signing of checksum file via Sigstore OIDC
- **Changelog:** Sort ascending, exclude `docs:`, `test:`, `chore:` commits
- **Homebrew:** Auto-update formula in `SET-Apps/homebrew-tap` repo, `Formula/` directory
- **Winget:** Submit manifest PR to `microsoft/winget-pkgs` (requires `WINGET_TOKEN` secret, can be deferred)
- **Release header:** Install instructions for `go install`, `brew`, `winget`, and `curl`

### Step 4: Create Install Script (`src/scripts/install.sh`)

- Detect OS (`uname -s`) and architecture (`uname -m`), normalize to Go conventions (`amd64`/`arm64`)
- Fetch latest release version from GitHub API if `$VERSION` not set
- Download and extract to `/usr/local/bin`
- Print installed version for verification
- Uploaded as release asset by GoReleaser (via `extra_files` or manual asset attachment)

### Step 5: Homebrew Tap Repository (external, manual)

- Create `SET-Apps/homebrew-tap` repo with empty `Formula/` directory and `README.md`
- GoReleaser auto-populates `Formula/dark-governance.rb` on each release
- Users install via `brew tap SET-Apps/tap && brew install dark-governance`
- This is a prerequisite but **not a code change in this repo** — document in the issue

### Step 6: Validation

- Validate workflow YAML syntax with `actionlint` locally before PR
- Dry-run GoReleaser locally: `cd src && goreleaser check` (validates `.goreleaser.yaml`)
- Test install script on macOS and Linux (manual or via CI)

## 5. Testing Strategy

| Test Type | Scope | Description |
|-----------|-------|-------------|
| Workflow YAML lint | `.github/workflows/go-*.yml` | `actionlint` validates syntax, action references, expression correctness |
| GoReleaser config validation | `src/.goreleaser.yaml` | `goreleaser check` validates config schema and build targets |
| CI build on PR | `go-build.yml` | Opening the implementation PR triggers the workflow on all 3 OS matrix entries |
| Cross-platform test matrix | `go-build.yml` | `go test ./... -race` on ubuntu, macos, windows catches platform-specific bugs |
| Release dry run | `go-release.yml` | `goreleaser release --snapshot --skip=publish` locally simulates a release without pushing |
| Install script smoke test | `src/scripts/install.sh` | Run on macOS and Linux (CI or manual) to verify download, extract, and version output |
| Cosign verification | Release artifacts | `cosign verify-blob` against checksums.txt after a real release |
| End-to-end release | Tag push `v*` | Push a test tag (e.g., `v0.0.1-rc.1`) to trigger the full pipeline before the real `v2.0.0` release |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| GoReleaser config error breaks release | Medium | High | Validate with `goreleaser check` in CI and locally; use `--snapshot` dry run |
| Cosign signing fails (Sigstore OIDC unavailable) | Low | Medium | `COSIGN_EXPERIMENTAL=true` uses keyless signing; Sigstore is a public service with high availability; signing step can be made non-blocking initially |
| `HOMEBREW_TAP_TOKEN` secret not configured | High (initially) | Low | Homebrew `brews:` section is a soft failure — GoReleaser skips it if the token is missing; document as prerequisite |
| macOS runner cost | Low | Low | Release workflow runs infrequently (per tag); cost is minimal |
| Tag pushed before governance approval | Medium | High | Document process: merge to main first, then tag. Governance pipeline runs on PRs, not tags. Include this in release checklist. |
| `src/` directory does not exist yet | High | Blocking | This pipeline depends on #743 creating `src/cmd/dark-governance/` and `src/go.mod`. Workflow files can be merged first (they only trigger on `src/**` paths) but GoReleaser config and install script require the Go module to exist. |
| Windows arm64 binary requested later | Low | Low | Add `windows/arm64` to `.goreleaser.yaml` when needed — single-line change |
| Existing `v1.0.1` tag conflicts with new versioning | Low | Medium | Next release should be `v2.0.0` (major bump for Go binary rewrite, breaking change from Python distribution). Document in semver strategy. |

## 7. Dependencies

- **#743 (Go binary rewrite)** — Creates `src/`, `src/cmd/dark-governance/`, `src/go.mod`. The build and release workflows reference these paths. **Blocking for functional operation but not for merging workflow files** (path filters prevent execution until `src/` exists).
- **#744 (go:embed distribution model)** — Defines what governance content is embedded in the binary. Affects ldflags and build steps but not the pipeline structure itself.
- **`SET-Apps/homebrew-tap` repository** — Must be created (empty, with `Formula/` directory) before the first release with Homebrew distribution. GoReleaser pushes the formula automatically. **Not blocking for pipeline merge.**
- **Repository secrets:**
  - `HOMEBREW_TAP_TOKEN` — PAT with `repo` scope on `SET-Apps/homebrew-tap`. Required for Homebrew formula auto-update.
  - `WINGET_TOKEN` — PAT for winget-pkgs PR submission. Optional, can be deferred.
  - `AC_USERNAME` / `AC_PASSWORD` — Apple Developer credentials for macOS notarization. Optional, can be added later.
- **GoReleaser v2** — Used via `goreleaser/goreleaser-action@v6`. No local installation required for CI.
- **Sigstore/Cosign** — Used via `sigstore/cosign-installer@v3`. Public infrastructure, no secrets needed (keyless OIDC signing).

## 8. Backward Compatibility

**No backward compatibility concerns.** This plan adds new files only:

- Two new workflow files (`.github/workflows/go-build.yml`, `.github/workflows/go-release.yml`) — these do not affect existing workflows. Path filters (`src/**`) ensure they only trigger on Go source changes.
- `src/.goreleaser.yaml` and `src/scripts/install.sh` — new files in the not-yet-created `src/` directory.
- Existing publish workflows (`publish-engine.yml`, `publish-mcp.yml`, `docker-publish.yml`) remain unchanged and continue to function independently.
- The `v*` tag pattern is shared with `docker-publish.yml`, which also triggers on `v*` tags. This is intentional: a version tag should trigger both the Go binary release and the Docker image publish. If separation is needed later, the Go release workflow can be scoped to `v[0-9]*` and Docker to `docker-v*`.

**Semver continuity:** The existing `v1.0.1` tag remains valid. The Go binary rewrite (#743) represents a breaking change in distribution model (Python to Go), so the first Go release should be `v2.0.0`.

## 9. Governance

### Panel Coverage

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes (default) | Validate workflow YAML structure, GoReleaser config correctness, install script quality |
| security-review | Yes (default) | CI pipeline security: permissions scope, secret handling, Cosign signing, install script trust |
| threat-modeling | Yes (default) | Supply chain threats: unsigned binaries, MITM on install script, compromised Homebrew tap token |
| cost-analysis | Yes (default) | macOS runner costs, cross-platform matrix runner minutes, release frequency impact |
| documentation-review | Yes (default) | Release process documentation, install instructions in release header |
| data-governance-review | Yes (default) | No PII/data concerns — CI/CD configuration only |
| architecture-review | Yes (optional, triggered by `.github/workflows/` paths) | Pipeline architecture, workflow composition, action version pinning |

### Policy Profile

**default** — Standard governance profile. CI/CD pipeline changes are classified as **chore** change type, but because they touch `.github/workflows/` they trigger the `security_sensitive_patterns` rule in `threat_model_tiers`, requiring a **Tier 2 (full) threat model**.

### Risk Level

**Medium** — New CI/CD infrastructure with secret handling (HOMEBREW_TAP_TOKEN), code signing (Cosign), and cross-platform binary distribution. No production application code changes, but pipeline misconfiguration could lead to unsigned or broken releases.

## 10. Decision Log

| Date | Decision | Rationale | Author |
|------|----------|-----------|--------|
| | | | |
