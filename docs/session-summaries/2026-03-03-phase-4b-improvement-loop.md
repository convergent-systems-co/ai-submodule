# Session Summary: Phase 4b Agentic Improvement Loop

**Date:** 2026-03-03
**Session type:** PM-mode agentic loop
**Topology:** 1 Project Manager, 1 DevOps Engineer, 3 Tech Leads (parallel)
**Result:** 10 PRs covering 8 closed issues + 2 open PRs across two context windows

---

## Overview

A full PM-mode agentic improvement loop dispatched three Tech Leads and one DevOps Engineer in parallel across two context windows. The session delivered foundational changes across four areas: Go binary distribution, developer experience, agent architecture hardening, and integration testing. This document summarizes every PR, its impact, and the key files introduced.

---

## Changes by Area

### 1. Go Binary Distribution

These PRs complete the shift from git-submodule-only distribution to a compiled Go binary (`dark-governance`) that consumers can install via Homebrew or direct download.

#### PR #761 -- Home-Rooted Governance Engine (`~/.ai/` Cache)

| | |
|---|---|
| **Title** | feat: add home-rooted governance engine with ~/.ai/ cache |
| **State** | Merged |
| **Closes** | #758 |
| **Additions / Deletions** | +1111 / -5 |

**What changed:**

- New `internal/home` package for home directory management with three-tier file resolution: repo-local `.ai/` > home cache `~/.ai/versions/` > embedded fallback
- `dark-governance install` extracts embedded governance content (96 files) into `~/.ai/versions/<version>/`
- `DARK_GOVERNANCE_HOME` and `XDG_DATA_HOME` environment variable support for configurable storage location
- CI mode (`install --ci`) uses `$RUNNER_TEMP/.ai/` or `$HOME/.ai/`
- `update` subcommand stub for future version management

**Key new files:**

| File | Purpose |
|------|---------|
| `src/internal/home/home.go` | Home directory management, resolution, CI detection |
| `src/internal/home/home_test.go` | 23 unit tests with temp dirs |
| `src/cmd/dark-governance/install_cmd.go` | `install` subcommand |
| `src/cmd/dark-governance/update_cmd.go` | `update` subcommand (stub) |

**Developer impact:** The binary now manages its own content cache at `~/.ai/`. Consumers no longer need `git submodule add` -- a single `dark-governance install` extracts everything needed.

---

#### PR #767 -- One-Binary Installer

| | |
|---|---|
| **Title** | feat: ship dark-governance one-binary installer |
| **State** | Open (needs rebase; merge conflicts pending) |
| **Issue** | #738 (not yet closed) |
| **Additions / Deletions** | +1397 / -614 |

**What changed:**

- `deps setup/status` -- creates and manages Python virtual environment for the governance engine bridge
- `mcp install/status` -- installs MCP server configuration for Claude and Cursor IDEs
- `configure` -- generates default `project.yaml` (non-interactive; interactive wizard is a stub)
- `uninstall` -- removes home cache (`~/.ai/versions/`) and venv with `--all` and `--yes` flags
- Updated `install.sh` with SHA-256 checksum verification and Cosign signature verification stub
- Comprehensive installation guide covering local, CI, and offline/airgapped modes

**Key new files:**

| File | Purpose |
|------|---------|
| `src/cmd/dark-governance/deps_cmd.go` | `deps setup` + `deps status` |
| `src/cmd/dark-governance/mcp_cmd.go` | `mcp install` + `mcp status` |
| `src/cmd/dark-governance/configure_cmd.go` | `configure` -- project.yaml generation |
| `src/cmd/dark-governance/uninstall_cmd.go` | `uninstall` -- home cache removal |
| `src/scripts/install.sh` | Checksum + Cosign verification |
| `docs/guides/installation.md` | Comprehensive installation guide |

**Developer impact:** The `dark-governance` binary is now a self-contained installer. `deps setup` bridges to the Python governance engine, `mcp install` configures IDE integration, and `uninstall` provides clean teardown.

---

#### PR #771 -- Homebrew Tap with Bottles on GitHub Packages

| | |
|---|---|
| **Title** | feat(homebrew): implement Homebrew tap with bottles on GitHub Packages |
| **State** | Open |
| **Closes** | #766 |
| **Additions / Deletions** | +1299 / -2 |

**What changed:**

- In-repo Homebrew tap (`homebrew/Formula/dark-governance.rb`) for `brew install` distribution
- CI workflow (`.github/workflows/homebrew-bottle.yml`) builds bottles on macOS arm64, macOS x86_64, and Linux x86_64, publishes to GHCR, and auto-updates formula checksums via PR
- Updated GoReleaser config (`src/.goreleaser.yaml`) to target in-repo tap with PR-based formula updates
- Developer onboarding docs (`docs/guides/homebrew-installation.md`) covering auth, install/upgrade, troubleshooting, and token rotation

**Key new files:**

| File | Purpose |
|------|---------|
| `homebrew/Formula/dark-governance.rb` | Homebrew formula |
| `.github/workflows/homebrew-bottle.yml` | Bottle build + publish CI |
| `docs/guides/homebrew-installation.md` | Homebrew installation guide |

**Developer impact:** Consumers will be able to run `brew tap SET-Apps/tap && brew install dark-governance` for one-command installation with automatic updates.

---

### 2. Developer Experience

#### PR #763 -- VHS Tape End-to-End Tests

| | |
|---|---|
| **Title** | test: add VHS tape end-to-end tests for consumer repo installation |
| **State** | Merged |
| **Closes** | #748 |
| **Additions / Deletions** | +611 / -1 |

**What changed:**

- VHS tape-based E2E test infrastructure for the `dark-governance` CLI
- `tests/e2e/install-test.tape` validates `dark-governance install` (home cache extraction, force reinstall)
- `tests/e2e/init-test.tape` validates `dark-governance init` (scaffolding, lockfile, verify, idempotency)
- `tests/e2e/run-tests.sh` runner with `--ci` mode that skips gracefully when VHS is not installed
- `make test-e2e` target in `src/Makefile`
- Developer guide at `docs/guides/e2e-testing.md`

**Key new files:**

| File | Purpose |
|------|---------|
| `tests/e2e/install-test.tape` | Install flow E2E tape |
| `tests/e2e/init-test.tape` | Init flow E2E tape |
| `tests/e2e/run-tests.sh` | Test runner with CI skip |
| `docs/guides/e2e-testing.md` | E2E testing developer guide |

**Developer impact:** E2E tests now record terminal sessions as GIFs via VHS tapes. `make test-e2e` runs them locally; CI skips gracefully when VHS is not available.

---

#### PR #764 -- Unified CLI Reference

| | |
|---|---|
| **Title** | docs: unified CLI reference replacing fragmented tooling |
| **State** | Merged |
| **Closes** | #741 |
| **Additions / Deletions** | +394 / -14 |

**What changed:**

- New `docs/guides/unified-cli-reference.md` with comprehensive CLI reference showing how `dark-governance` replaces 4 fragmented shell scripts, Python modules, and Node tools
- Updated `docs/guides/developer-quickstart.md` to offer binary installation as the recommended path
- Restructured `CLAUDE.md` Commands section to lead with unified CLI commands

**Key new files:**

| File | Purpose |
|------|---------|
| `docs/guides/unified-cli-reference.md` | Complete CLI reference |

**Developer impact:** One CLI reference document replaces scattered tool-specific pages. Binary installation is now the recommended onboarding path.

---

#### PR #772 -- Delivery Intent Manifests + verify-environment

| | |
|---|---|
| **Title** | feat: delivery intent manifests + verify-environment CLI command |
| **State** | Open |
| **Closes** | #749 |
| **Additions / Deletions** | +1752 / -1 |

**What changed:**

- Delivery intent schema (`governance/schemas/delivery-intent.schema.json`) defining immutable manifest structure for deliverables, expected state, and source metadata
- Go verification package (`src/internal/deliveryintent/`) with loader, checker, and types for parsing intents and detecting drift (file existence, checksums, directories, workflows)
- `dark-governance verify-environment` CLI command with `--intent`, `--output` (human/json), and `--fix` flags. Exit codes: 0=OK, 1=drift, 2=critical, 3=no intent
- Updated document-writer persona to emit delivery intents during Phase 4
- `governance.delivery_intent.enabled` config in `project.yaml`

**Key new files:**

| File | Purpose |
|------|---------|
| `governance/schemas/delivery-intent.schema.json` | Delivery intent JSON Schema |
| `src/internal/deliveryintent/` | Go loader + checker package |
| `docs/guides/delivery-intent.md` | User-facing guide |

**Developer impact:** The document-writer persona now emits delivery intent manifests, and `verify-environment` detects drift between the manifest and the actual repository state. CI pipelines can gate on exit code.

---

### 3. Agent Architecture

These PRs harden the multi-agent orchestration layer with topology enforcement and context isolation.

#### PR #765 -- PM Mode Topology Enforcement

| | |
|---|---|
| **Title** | fix: enforce PM mode topology at orchestrator dispatch time |
| **State** | Merged |
| **Closes** | #759 |
| **Additions / Deletions** | +1900 / -3 |

**What changed:**

- `orchestrator dispatch` command validates parent-to-child agent spawn relationships against a spawn DAG defined in `governance/policy/agent-topology.yaml`
- Phase-persona binding validation on `step --complete --agent` ensures only the designated persona can complete each phase in PM mode
- Invalid spawns (e.g., PM spawning a Coder directly, bypassing Tech Lead) are rejected with structured error messages
- `max_concurrent` limits per persona (e.g., 1 DevOps Engineer, up to N Tech Leads)

**Key new files:**

| File | Purpose |
|------|---------|
| `governance/policy/agent-topology.yaml` | Spawn DAG policy |
| `governance/engine/orchestrator/topology.py` | Topology loader, validator, dispatch descriptor |
| `governance/engine/tests/test_topology.py` | 36 unit + integration tests |

**Developer impact (breaking for agent developers):** The orchestrator now validates the spawn DAG at dispatch time. A PM can only spawn Tech Leads and DevOps Engineers, not Coders directly. Existing custom dispatch logic that bypasses the hierarchy will fail.

---

#### PR #768 -- Per-Agent Context Boundaries with Envelope-Based Dispatch

| | |
|---|---|
| **Title** | feat: enforce per-agent context boundaries with envelope-based dispatch |
| **State** | Merged |
| **Closes** | #751 |
| **Additions / Deletions** | +1506 / -0 |

**What changed:**

- Per-persona `receives`/`never_receives` boundaries in `governance/policy/agent-context-boundaries.yaml` for all 9 agentic personas
- `governance/schemas/agent-envelope.schema.json` -- structured message envelope schema with authentication, persona context, and content-addressed attachments
- `governance/engine/envelope.py` -- `EnvelopeBuilder`, `validate_envelope()`, and `strip_unauthorized_context()` with HMAC signing
- Updated `governance/prompts/agent-protocol.md` with Message Envelope and Message Authentication sections
- Updated `docs/architecture/agent-architecture.md` with Context Boundary Model section

**Key new files:**

| File | Purpose |
|------|---------|
| `governance/policy/agent-context-boundaries.yaml` | Per-persona boundary specs |
| `governance/schemas/agent-envelope.schema.json` | Envelope JSON Schema |
| `governance/engine/envelope.py` | Envelope builder, validator, signer |
| `governance/engine/tests/test_envelope.py` | 33 tests |

**Developer impact (breaking for agent developers):** Agent messages are now wrapped in HMAC-signed envelopes with per-persona context boundaries. `strip_unauthorized_context()` removes content that a persona should never receive. This prevents context leakage between agents in multi-agent sessions.

---

#### PR #769 -- Configurable Storage Backend

| | |
|---|---|
| **Title** | feat: add configurable storage backend for governance state |
| **State** | Open (merge conflicts; needs rebase) |
| **Issue** | #757 (not yet closed) |
| **Additions / Deletions** | +375 / -2 |

**What changed:**

- `governance/engine/storage.py` -- `StorageAdapter` protocol with `put`/`get`/`list`/`delete` + `LocalAdapter` (XDG-compliant) and `RepoAdapter` (`.artifacts/` backward-compatible)
- Updated `governance/schemas/project.schema.json` with `governance.storage` section (`state`, `archive`, `config`, `retention` properties)
- `SessionStore.from_adapter()` factory method for externalized session state
- Storage configuration guide at `docs/guides/storage-configuration.md`

**Key new files:**

| File | Purpose |
|------|---------|
| `governance/engine/storage.py` | Storage adapter protocol + implementations |
| `governance/engine/tests/test_storage.py` | 32 tests |
| `docs/guides/storage-configuration.md` | Storage configuration guide |

**Developer impact:** Governance state can now be stored outside the repo via `LocalAdapter` (XDG paths) or inside via `RepoAdapter` (backward-compatible `.artifacts/`). Configure via `governance.storage` in `project.yaml`.

---

### 4. Integration Testing

#### PR #773 -- ADO Bidirectional Sync E2E Test Suite

| | |
|---|---|
| **Title** | test: E2E test suite for ADO bidirectional sync |
| **State** | Merged |
| **Closes** | #747 |
| **Additions / Deletions** | +2443 / -0 |

**What changed:**

- 56 E2E tests across 9 phases covering the full Azure DevOps bidirectional sync pipeline
- Test fixtures (YAML config, GitHub/ADO webhook templates) for reproducible mock testing
- CI workflow (`test-ado-e2e.yml`) with mock tests on push/PR and live ADO tests on daily schedule
- Updated ADO integration docs with E2E testing section

**Test phases:**

| Phase | Tests | Description |
|-------|-------|-------------|
| 1 | 5 | Connection and configuration (health checks, config loading) |
| 2 | 8 | Forward sync GitHub to ADO (create, update, close, reopen, labels, assignees, milestones, errors) |
| 3 | 6 | Reverse sync ADO to GitHub (state, title, assignee, deletion, state machine) |
| 4 | 4 | Echo detection (grace period, last_sync_source tracking) |
| 5 | 10 | Comments sync (prefix filtering, formatting, duplicate prevention) |
| 6 | 4 | Bulk sync (dry-run, actual, dedup, error handling) |
| 7 | 7 | Error recovery (retry, dead-letter, dry-run, count tracking) |
| 8 | 8 | Health and dashboard (metrics, malformed data, JSON schema) |
| 9 | 3 | Ledger integrity (lifecycle consistency, no duplicates, monotonic timestamps) |

**Key new files:**

| File | Purpose |
|------|---------|
| `governance/integrations/ado/tests/test_bidirectional_e2e.py` | 56-test E2E suite |
| `.github/workflows/test-ado-e2e.yml` | ADO E2E CI workflow |

**Developer impact:** All 56 mock tests run without credentials. Live tests (`@pytest.mark.ado_live`) activate only when `ADO_PAT`, `ADO_ORGANIZATION`, and `ADO_PROJECT` are set.

---

## Agent Topology

The session used PM-mode orchestration with the following spawn tree:

```
Project Manager -- Phase 1-5 orchestration -- [completed]
|-- DevOps Engineer -- PR lifecycle loop -- [completed, merged 5 PRs]
|-- Tech Lead A -- #759 + #738 -- [completed, PRs #765, #767]
|-- Tech Lead B -- #751 + #757 -- [completed, PRs #768, #769]
|-- Tech Lead C -- #748 + #741 -- [completed, PRs #763, #764]
```

A second context window dispatched additional work for issues #766, #749, #747, producing PRs #771, #772, #773.

---

## Test Suite Impact

| Suite | Count | Status |
|-------|-------|--------|
| Governance engine (Python) | ~2,330 | Passing |
| Go CLI (`make test`) | 34+ | Passing |
| ADO E2E (mock) | 56 | Passing |
| Topology tests | 36 | Passing |
| Envelope tests | 33 | Passing |
| Storage tests | 32 | Passing |
| VHS E2E tapes | 2 | Passing (when VHS installed) |

---

## Breaking Changes

Two changes in this session are **breaking for agent developers** who extend the orchestration layer:

1. **Topology enforcement (#765):** The orchestrator now validates the spawn DAG. Custom dispatch logic that bypasses the hierarchy (e.g., PM spawning Coder directly) will be rejected. Update dispatch calls to go through Tech Lead.

2. **Context boundaries (#768):** Agent messages are now wrapped in signed envelopes. Code that constructs raw protocol messages without envelopes will fail validation. Use `EnvelopeBuilder` from `governance/engine/envelope.py`.

---

## Lessons Learned

1. **Branch collision is real:** Without worktree isolation, agents sharing the primary working tree caused `git checkout` conflicts. This is tracked for future improvement.

2. **Rebase after merge storms:** When 5+ PRs merge in rapid succession, remaining open PRs will conflict. Future sessions should rebase in-flight branches incrementally.

3. **Auto-merge limitation:** GitHub rejected auto-merge enablement mid-session. The DevOps Engineer fell back to manual squash merge successfully.

4. **Two-window sessions work:** Splitting work across context windows with checkpoint-based handoff allowed the session to cover more ground without hitting context limits.

---

## PR Summary Table

| PR | Title | State | Issue | Area |
|----|-------|-------|-------|------|
| [#761](https://github.com/convergent-systems-co/dark-forge/pull/761) | Home-rooted governance engine | Merged | #758 | Go binary |
| [#763](https://github.com/convergent-systems-co/dark-forge/pull/763) | VHS tape E2E tests | Merged | #748 | Developer experience |
| [#764](https://github.com/convergent-systems-co/dark-forge/pull/764) | Unified CLI reference | Merged | #741 | Developer experience |
| [#765](https://github.com/convergent-systems-co/dark-forge/pull/765) | PM mode topology enforcement | Merged | #759 | Agent architecture |
| [#767](https://github.com/convergent-systems-co/dark-forge/pull/767) | One-binary installer | Open (merge conflicts) | #738 | Go binary |
| [#768](https://github.com/convergent-systems-co/dark-forge/pull/768) | Context boundaries + envelopes | Merged | #751 | Agent architecture |
| [#769](https://github.com/convergent-systems-co/dark-forge/pull/769) | Configurable storage backend | Open (merge conflicts) | #757 | Agent architecture |
| [#771](https://github.com/convergent-systems-co/dark-forge/pull/771) | Homebrew tap | Open | #766 | Go binary |
| [#772](https://github.com/convergent-systems-co/dark-forge/pull/772) | Delivery intent + verify-environment | Open | #749 | Developer experience |
| [#773](https://github.com/convergent-systems-co/dark-forge/pull/773) | ADO bidirectional sync E2E | Merged | #747 | Integration testing |
