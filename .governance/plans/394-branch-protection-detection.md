# Detect branch protection in pre-flight and route commits through PRs

**Author:** Code Manager (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/394
**Branch:** `itsfwcp/feat/394/branch-protection-detection`

---

## 1. Objective

Enable the agentic pre-flight to detect whether the default branch requires pull requests (via GitHub rulesets or legacy branch protection), and route all direct commits (submodule pointer updates, CODEOWNERS changes) through branch→commit→push→PR→merge when PRs are required.

## 2. Rationale

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Always use PRs for structural commits | Yes | Unnecessary overhead for repos without branch protection; creates noise |
| Add a config flag only (no auto-detection) | Yes | Requires manual configuration; auto-detection is more robust and discoverable |
| Auto-detect + config override (chosen) | Yes | Best of both worlds — automatic with manual escape hatch |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| None | — |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `bin/init.sh` | Add `check_branch_protection()` function that queries the GitHub API and outputs a machine-readable result (`REQUIRES_PR=true\|false`) |
| `bin/init.ps1` | Add equivalent `Test-BranchProtection` function |
| `governance/prompts/startup.md` | Phase 1a: add step 6 for branch protection detection; Phase 1a step 4: conditional routing for submodule commits |
| `governance/personas/agentic/devops-engineer.md` | Pre-flight Checks: add branch protection detection bullet; Evaluate For: add branch protection question |
| `governance/personas/agentic/code-manager.md` | Add awareness of `REQUIRES_PR` for structural commits during Phase 2a (project.yaml updates) |
| `docs/configuration/repository-setup.md` | Document branch protection detection behavior and protected vs unprotected branch routing |
| `README.md` | Update pre-flight section to mention branch protection awareness |
| `instructions.md` | Add note about branch protection detection in Repository Configuration section |
| `CLAUDE.md` | Add sentence about branch protection awareness in Agentic Startup Sequence |
| `config.yaml` | Add `branch_protection.require_pr_for_structural_commits` override option (default: `auto`) |
| `tests/bats/test_init.bats` | Add tests for `check_branch_protection()` function |

### Files to Delete

| File | Reason |
|------|--------|
| None | — |

## 4. Approach

### Step 1: Add `check_branch_protection()` to `init.sh`

Add a new function after `validate_rulesets()` that:
1. Queries `gh api repos/{owner}/{repo}/rules/branches/{default_branch}` for ruleset-based protection
2. Falls back to `gh api repos/{owner}/{repo}/branches/{default_branch}/protection` for legacy protection
3. Checks if any rule has `type == "pull_request"` (rulesets) or `required_pull_request_reviews` is present (legacy)
4. Reads `repository.branch_protection.require_pr_for_structural_commits` from config — if set to `true`/`false`, uses that; if `auto` (default), uses API detection
5. Outputs `REQUIRES_PR=true` or `REQUIRES_PR=false` to stdout (machine-readable for callers)
6. Degrades gracefully — if API calls fail, defaults to `false` (direct commits allowed, matching current behavior)

### Step 2: Add `--check-branch-protection` flag to `init.sh`

Add a new flag that runs only `check_branch_protection()` and exits with the result. This is the entry point for the agentic loop to query the status.

### Step 3: Add `Test-BranchProtection` to `init.ps1`

PowerShell equivalent with same logic and output format.

### Step 4: Update `startup.md` Phase 1a

Insert step 6 (after refresh, before 1b) for branch protection detection:
```bash
REQUIRES_PR=$(bash .ai/bin/init.sh --check-branch-protection 2>/dev/null | grep '^REQUIRES_PR=' | cut -d= -f2)
```

Update step 4 (submodule update commit) with conditional routing:
- If `REQUIRES_PR=true`: create branch `chore/update-ai-submodule`, commit, push, `gh pr create`, wait for CI, `gh pr merge --squash --delete-branch`
- If `REQUIRES_PR=false` (default): commit directly to main (current behavior)

Add similar conditional for `init.sh --refresh` artifacts that modify tracked files (CODEOWNERS).

### Step 5: Update DevOps Engineer persona

Add branch protection detection to Pre-flight Checks and Evaluate For sections.

### Step 6: Update Code Manager persona

Add note about `REQUIRES_PR` awareness for structural commits during orchestration (e.g., `project.yaml` updates in Phase 2a).

### Step 7: Update documentation

- `docs/configuration/repository-setup.md`: Add "Branch Protection Detection" subsection
- `README.md`: Add branch protection awareness to pre-flight description
- `instructions.md`: Note in Repository Configuration section
- `CLAUDE.md`: Note in Agentic Startup Sequence table
- `config.yaml`: Add `branch_protection.require_pr_for_structural_commits: auto`

### Step 8: Add BATS tests

- Test `check_branch_protection()` with mocked `gh api` responses
- Test `--check-branch-protection` flag output format
- Test config override (`true`/`false`/`auto`)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `check_branch_protection()` | Mocked `gh api` responses: rulesets with pull_request rule, legacy protection, no protection, API failure |
| Unit | `--check-branch-protection` flag | Output format validation (`REQUIRES_PR=true\|false`) |
| Unit | Config override | `require_pr_for_structural_commits` values: `auto`, `true`, `false` |
| Integration | `init.sh --check-branch-protection` | End-to-end flag execution in a sandbox repo |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| API rate limiting on branch protection queries | Low | Low | Single query per session, cached result |
| Insufficient permissions to query rulesets | Medium | Low | Graceful degradation to `false` (direct commits) |
| Rulesets API not available (older GHES) | Low | Low | Fallback to legacy branch protection API |
| Config override conflicts with auto-detection | Low | Low | Config override is explicit and intentional; document precedence clearly |

## 7. Dependencies

- [x] `validate_rulesets()` exists in `init.sh` (established pattern) — non-blocking
- [x] `gh api repos/{owner}/{repo}/rules/branches/` endpoint available — non-blocking (fallback to legacy)

## 8. Backward Compatibility

Fully backward compatible:
- Default behavior unchanged (`require_pr_for_structural_commits: auto`, API failure → `false`)
- No existing flags or functions modified
- New function and flag are additive
- Consuming repos that don't have branch protection see no difference

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Script changes touch repo API queries |
| documentation-review | Yes | Heavy documentation changes across 6+ files |
| threat-modeling | Yes | Mandatory per policy |
| cost-analysis | Yes | Mandatory per policy |
| data-governance-review | Yes | Mandatory per policy |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Use `--check-branch-protection` as a separate flag rather than embedding in `--refresh` | Separation of concerns: detection is read-only, refresh modifies state |
| 2026-02-26 | Default to `auto` detection rather than `false` | Auto-detection is the correct default for repos that add protection after initial setup |
| 2026-02-26 | Use rulesets API first, legacy branch protection as fallback | Rulesets are the modern API; legacy still needed for repos that haven't migrated |
