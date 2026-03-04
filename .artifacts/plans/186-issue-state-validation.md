# Add Issue State Validation to Governance Framework

**Author:** Team Lead (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/186
**Branch:** NETWORK_ID/feat/186/issue-state-validation

---

## 1. Objective

Add an Issue State Validation rule to the governance framework so agents verify that associated GitHub issues are still open before continuing work. This prevents wasted effort on closed issues, especially after checkpoint restores or context resets.

## 2. Rationale

An agent resumed from a checkpoint and continued working on issue #63 which had been closed. It completed the work and created a PR for changes that were no longer needed.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add validation only to startup.md | Yes | Only protects agentic loop; the rule must be universal across all AI tooling |
| Add runtime check only | Yes | This is a config-only repo; the rule must be in instructions that all tools consume |
| Add to instructions.md in ANCHOR block | Yes | Selected — this propagates to CLAUDE.md, .cursorrules, and copilot-instructions.md via symlinks |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files needed |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `instructions.md` | Add "Issue State Validation" section inside ANCHOR block |
| `governance/prompts/startup.md` | Add issue state check at Step 4 (Validate Intent) and at checkpoint restore |
| `GOALS.md` | Add completed work entry |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

### Step 1: Add Rule to instructions.md (ANCHOR Block)

Add a new section "Issue State Validation" inside the `<!-- ANCHOR -->` block in `instructions.md`. The rule:

1. Before starting work on any issue, verify it is still open: `gh issue view <number> --json state`
2. If the issue is closed, stop — do not continue work
3. During checkpoint restores, re-validate all in-flight issues before resuming
4. If an issue is closed while work is in progress, stop at the next opportunity and notify the user

This will automatically propagate to CLAUDE.md, .cursorrules, and copilot-instructions.md via the symlink mechanism in init.sh.

### Step 2: Add Validation Steps to startup.md

Add issue state validation at two integration points:
1. **Step 4 (Validate Intent)** — Before validating intent, confirm the issue is still open
2. **Checkpoint restore** — When resuming from a checkpoint, verify all `issues_remaining` and `current_issue` are still open

### Step 3: Update Documentation

- GOALS.md — Add completed work entry

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual review | instructions.md | Verify rule is inside ANCHOR block and survives context resets |
| Manual review | startup.md | Verify validation steps are at correct integration points |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Rule too strict — agent stops on temporarily closed issues | Low | Low | Rule only checks current state; if user re-opens, agent will pick it up next session |
| Additional API call per issue adds latency | Low | Low | Single lightweight API call; negligible overhead |

## 7. Dependencies

- [ ] None — this is a standalone documentation change

## 8. Backward Compatibility

Fully backward compatible. Adding instructions to the ANCHOR block is additive. Existing workflows continue to work; they just gain an additional validation check.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Changes to core instruction files |
| security-review | Yes | Standard requirement |
| code-review | Yes | Standard requirement |
| threat-modeling | Yes | Standard requirement |
| cost-analysis | Yes | Standard requirement |
| data-governance-review | Yes | Standard requirement |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Place rule in instructions.md ANCHOR block | Ensures all AI tools receive the rule; survives context resets |
| 2026-02-24 | Keep rule brief and actionable | Instructions.md is Tier 0 context (~400 tokens); must be concise |
