# Simplify Install

**Author:** Code Manager (agentic)
**Date:** 2026-02-21
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/71
**Branch:** itsfwcp/fix/71/simplify-install

---

## 1. Objective

Make the .ai submodule installation a single-command experience that handles platform detection, Python virtual environment creation, dependency installation, and symlink setup — eliminating all manual steps.

## 2. Rationale

The current `init.sh` only creates symlinks. The current `init.ps1` checks for Python but does not install packages or create a virtual environment. Users must manually install Python packages and know which ones are needed. The issue requests consolidation into a single command per platform.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Go CLI application | Yes | SSO-gated repos make `go install` impractical; adds a compile-time dependency to a config-only repo |
| Python-based installer | Yes | Adds a chicken-and-egg problem (need Python to run the installer that installs Python deps) |
| Shell scripts with venv support | Yes (chosen) | Minimal dependencies (bash/PowerShell already available), handles venv creation natively |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies for the governance policy engine (`jsonschema`, `pyyaml`) |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `init.sh` | Add platform detection (macOS/Linux), Python 3.12+ check, venv creation at `.ai/.venv`, pip install from `requirements.txt`, `--install-deps` flag, preserve existing symlink logic |
| `init.ps1` | Add venv creation at `.ai\.venv`, pip install from `requirements.txt`, `-InstallDeps` switch, integrate with existing dependency checks |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. **Create `requirements.txt`** at repo root with `jsonschema` and `pyyaml`
2. **Enhance `init.sh`**:
   - Add `--install-deps` flag (when passed, auto-install everything; without it, check-and-warn like today)
   - Add platform detection function (macOS vs Linux) for informational output
   - Add Python version check (3.12+ per `.governance/README.md`)
   - Add venv creation at `.ai/.venv` (using `python3 -m venv`)
   - Add pip install from `requirements.txt` inside the venv
   - Keep existing symlink logic unchanged
   - Print clear next-steps summary
3. **Enhance `init.ps1`**:
   - Add `-InstallDeps` switch parameter
   - Add venv creation at `.ai\.venv` (using `python -m venv`)
   - Add pip install from `requirements.txt` inside the venv
   - Integrate with existing `Test-PythonInstalled` and `Test-PipPackages` functions
   - Keep existing symlink/copy logic unchanged
   - Print clear next-steps summary

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | `init.sh` | Run on macOS, verify symlinks + venv + packages installed |
| Manual | `init.ps1` | N/A (no Windows available), but script logic mirrors init.sh |
| Idempotency | Both scripts | Run twice, verify no errors and no duplicate work |

Note: This is a config-only repo with no test framework. Manual verification is appropriate.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Python not installed on user machine | Medium | Medium | Clear error message with install instructions; `--install-deps` only attempts venv if Python found |
| Venv path conflicts with existing installs | Low | Low | Script checks for existing `.ai/.venv` before creating |
| requirements.txt drift from actual deps | Low | Medium | Single source of truth — both scripts and docs reference it |

## 7. Dependencies

- [x] Python 3.12+ on user machine (soft dependency — scripts degrade gracefully)
- [x] No blocking dependencies

## 8. Backward Compatibility

Fully backward compatible. Without `--install-deps`, both scripts behave identically to current behavior. The flag is additive.

## 9. Governance

Expected panel reviews and policy profile:

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Script changes need review |
| security-review | No | No security-sensitive changes |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Shell scripts over Go CLI | Issue body acknowledges SSO limitation; shell is zero-dependency |
| 2026-02-21 | Python 3.12+ (not 3.9+) | `.governance/README.md` specifies 3.12+; init.ps1 had stale 3.9+ check |
| 2026-02-21 | Venv at `.ai/.venv` | Keeps venv inside the submodule directory, isolated from consuming project |
