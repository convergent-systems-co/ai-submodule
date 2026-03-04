# Support Windows

**Author:** Team Lead (agentic)
**Date:** 2026-02-22
**Status:** completed
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/59
**Branch:** NETWORK_ID/feat/59/support-windows

---

## 1. Objective

Enable Windows users to bootstrap the governance submodule without WSL by providing a PowerShell equivalent of `init.sh` with dependency validation.

## 2. Rationale

The existing `init.sh` uses bash-specific features (symlinks via `ln -sf`, `readlink`, `set -euo pipefail`) that don't work on native Windows without WSL. Windows users need a PowerShell script that achieves the same result using Windows-native mechanisms.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Require WSL for all users | Yes | Adds unnecessary dependency; many Windows devs don't use WSL |
| Cross-platform Node.js script | Yes | Adds Node.js as a dependency; not all consumers are JS projects |
| PowerShell script | Yes | **Selected** — PowerShell is pre-installed on all modern Windows |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `init.ps1` | PowerShell bootstrap script — Windows equivalent of `init.sh` |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `README.md` | Add Windows bootstrap instructions |
| `DEVELOPER_GUIDE.md` | Add Windows setup section if applicable |

### Files to Delete

N/A

## 4. Approach

1. Create `init.ps1` that:
   - Checks for Python 3 installation, warns if missing
   - Checks for `pip` packages (`jsonschema`, `pyyaml`), warns if missing
   - Creates symlinks using PowerShell `New-Item -ItemType SymbolicLink` (requires Developer Mode or admin)
   - Falls back to file copy if symlink creation fails (non-admin users)
   - Copies issue templates (same logic as init.sh)
   - Prints next steps
2. Update README.md with Windows bootstrap instructions
3. Test idempotency (safe to run multiple times)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | init.ps1 | Verify script syntax with PowerShell linter |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Symlinks require admin/dev mode on Windows | Medium | Medium | Fall back to file copy with warning |
| PowerShell execution policy blocks script | Medium | Low | Document `Set-ExecutionPolicy` in README |

## 7. Dependencies

- [x] None

## 8. Backward Compatibility

Fully additive. `init.sh` is unchanged and continues to work on Unix systems.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New script with platform-specific logic |
| copilot-review | Yes | Standard PR review |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-22 | Fall back to copy when symlinks fail | Windows symlinks require Developer Mode or admin; copy provides a working fallback |
