# Fix: Startup Loop Must Read Issue Comments Before Evaluating

**Author:** Code Manager (agent)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/462
**Branch:** itsfwcp/fix/462/read-issue-comments

---

## 1. Objective

Ensure the startup loop reads all issue comments (not just the body) before evaluating, triaging, or planning work for any issue. User comments frequently contain additional requirements, clarifications, and instructions that are critical for correct implementation.

## 2. Rationale

The current `gh issue list` call in Phase 1d returns only the issue body. Comments are never fetched. This means the agent misses user-provided context that may change scope, add requirements, or provide critical instructions.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add `comments` to `gh issue list --json` | Yes | `gh issue list` does not support `comments` in `--json` fields |
| Fetch comments in Phase 2b only | Yes | Phase 1d also evaluates body for size/validation — needs full context |
| Use `gh issue view` per issue | Yes — **selected** | Reliable way to get body + comments; minor API overhead acceptable |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files needed |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Phase 1d: add step to fetch comments per actionable issue via `gh issue view`; Phase 2b: explicitly require reading comments before intent validation; size check to account for combined body + comments length |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. **Phase 1d — Add comment fetching step:** After the initial `gh issue list` call filters the candidate set, add an instruction for the agent to fetch full issue details (including comments) for each candidate issue using `gh issue view <number> --json number,title,body,comments,labels,assignees`. This replaces the body-only data from `gh issue list` for evaluation purposes.

2. **Phase 1d — Update size check:** Extend the MAX_ISSUE_BODY_CHARS check to account for combined body + comments length. Add a `MAX_ISSUE_COMMENTS` constant (default 50) to cap the number of comments loaded per issue.

3. **Phase 2b — Explicit comment reading:** Update the "Read the issue body" instruction to "Read the issue body and all comments." Add a note that comments may contain additional requirements, acceptance criteria modifications, or user instructions that override or extend the original body.

4. **Phase 2b — Comment content policy:** Add a note that comments from the issue author or repo members should be treated as authoritative extensions of the issue body. Comments from other users should be treated as advisory.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | startup.md | Verify the modified startup prompt correctly instructs comment reading when executed |
| Integration | Agent execution | Next `/startup` session validates by reading comments on live issues |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| API rate limiting from per-issue `gh issue view` calls | Low | Low | Only fetch for actionable candidates (filtered set), not all 50 |
| Oversized comments exhausting context | Med | Med | Apply MAX_ISSUE_BODY_CHARS to combined body + comments; cap comments count |

## 7. Dependencies

- [x] None — self-contained prompt modification

## 8. Backward Compatibility

Fully backward compatible. This adds instructions to the startup prompt; it does not change any schema, policy, or enforcement artifact.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Always required |
| documentation-review | Yes | Modifying core governance prompt |
| threat-modeling | Yes | Always required |
| cost-analysis | Yes | Always required |
| data-governance-review | Yes | Always required |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Use `gh issue view` per issue rather than modifying `gh issue list` | `gh issue list` does not support `comments` field; `gh issue view` is the reliable approach |
