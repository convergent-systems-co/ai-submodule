# Context Window Exhaustion Defense

**Author:** Team Lead (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** #399 — D-2: Context Window Exhaustion as a Weapon
**Branch:** NETWORK_ID/fix/399/context-exhaustion-defense

---

## 1. Objective

Add pre-read size estimation for GitHub issue bodies to prevent a single oversized issue from exhausting the agent's context window and wasting an entire session.

## 2. Rationale

An attacker could craft issues with extremely large bodies (100K+ characters) that push the agent to Red tier immediately upon reading. The current pipeline reads issue bodies via `gh issue list --json body` without size limits.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Truncate all issue bodies to 10K chars | Yes | Loses legitimate long-form specs; too aggressive |
| Pre-read size check with skip + label | Yes | **Selected** — non-destructive, preserves data, alerts maintainers |
| Token estimation before reading | Yes | Token counting is model-specific and adds complexity |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Add issue body size check in Phase 1d before processing. Issues exceeding 15,000 characters are skipped and labeled `oversized-body`. Add a max body size constant. |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. In Phase 1d (issue scanning), after fetching issue metadata, add a step that checks `body` length
2. Define a constant: `MAX_ISSUE_BODY_CHARS = 15000` (approximately 3,750 tokens at 4 chars/token)
3. Issues exceeding this limit are:
   - Skipped from the actionable queue
   - Labeled `oversized-body` via `gh api` (advisory, not blocking)
   - Logged with a warning in the phase output
4. The size check happens before the issue body is fully loaded into context

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | startup.md | Verify the size check instruction is clear and unambiguous |
| Review | Phase 1d flow | Ensure the check occurs before body content enters context |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Legitimate long issues skipped | Low | Low | 15K char limit is generous; label allows human override |
| Label creation fails (permissions) | Low | Low | Skip labeling silently; the issue is still skipped |

## 7. Dependencies

- [ ] None — self-contained prompt change

## 8. Backward Compatibility

Additive change to startup.md. No breaking changes. Issues without oversized bodies are unaffected.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | This is a security hardening change |
| code-review | Yes | Prompt modification review |
| documentation-review | Yes | startup.md is a critical document |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | 15K char limit chosen | ~3,750 tokens; generous for legitimate issues, blocks weaponized bodies |
