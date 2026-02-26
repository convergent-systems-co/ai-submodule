# Implement Instruction Decomposition

**Author:** Code Manager (agentic)
**Date:** 2026-02-20
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/11
**Branch:** itsfwcp/11-instruction-decomposition

---

## 1. Objective

Split instructions.md into composable units per the context management strategy. Keep base instructions under 200 tokens. Create domain-specific instruction files that can be loaded independently at Tier 1.

## 2. Rationale

The current instructions.md is ~180 tokens — close to budget. As instructions grow, decomposition prevents exceeding Tier 0 limits. Domain-specific files enable JIT loading based on task type.

## 3. Scope

### Files to Create

| File | Purpose | Budget |
|------|---------|--------|
| `instructions/code-quality.md` | Code standards, patterns, idioms | < 500 tokens |
| `instructions/testing.md` | Test strategy, coverage, practices | < 500 tokens |
| `instructions/security.md` | Security-sensitive task guidance | < 500 tokens |
| `instructions/communication.md` | PR/issue/documentation communication | < 500 tokens |
| `instructions/governance.md` | Governance pipeline task guidance | < 500 tokens |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `instructions.md` | Trim to universal principles only (< 200 tokens), add ANCHOR markers |

### Symlink Impact

Symlinks (CLAUDE.md → instructions.md, .cursorrules → instructions.md, copilot-instructions.md → instructions.md) continue to work — they point to instructions.md which remains the base file.

## 4. Approach

1. Create `instructions/` directory
2. Extract domain-specific content from instructions.md into decomposed files
3. Trim instructions.md to universal principles with ANCHOR markers
4. Each decomposed file: single responsibility, no cross-dependencies, under 500 tokens

## 5. Testing Strategy

- Verify instructions.md is under 200 tokens
- Verify each decomposed file is under 500 tokens
- Verify no cross-file dependencies
- Verify existing symlinks still resolve

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Symlinks break | None | High | Symlinks point to instructions.md which stays in place |

## 7. Dependencies

None.
