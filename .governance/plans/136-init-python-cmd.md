# Fix: init.sh crashes with unbound PYTHON_CMD variable

**Author:** Coder (agentic)
**Date:** 2026-02-23
**Status:** completed
**Issue:** #136
**Branch:** itsfwcp/fix/136/init-python-cmd

---

## 1. Objective

Fix init.sh crash caused by `PYTHON_CMD` being referenced before initialization under `set -u`.

## 2. Rationale

Moving Python detection earlier is the cleanest fix — it initializes `PYTHON_CMD` and `PYTHON_OK` before any code that references them.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Use `${PYTHON_CMD:-}` default | Yes | Band-aid; doesn't fix execution order |
| Initialize `PYTHON_CMD=""` early | Yes | Still leaves detection output in wrong place |
| Move detection block earlier | Yes — **chosen** | Correct ordering; detection output appears logically |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| init.sh | Move find_python/check_python_version functions and detection block before symlinks section; fix `local` outside function |

## 4. Approach

1. Move `find_python()`, `check_python_version()` functions + detection logic to after platform detection
2. Remove duplicated block from original position
3. Fix `local link_target` → `link_target` (local outside function)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Syntax | init.sh | `bash -n init.sh` passes |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Output ordering changes | Low | Low | Dependencies output before symlinks is acceptable |

## 7. Dependencies

N/A.

## 8. Backward Compatibility

Fully backward compatible. Same behavior, fixed execution order.

## 9. Governance

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Move entire detection block, not just init | Keeps functions near their usage |
