# Copilot Context Management Parity

**Author:** Team Lead (agentic)
**Date:** 2026-02-22
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/80
**Branch:** NETWORK_ID/feat/80/copilot-context-parity

---

## 1. Objective

Make the governance framework's context management equally detailed and actionable for GitHub Copilot as it already is for Claude Code. The 80% shutdown protocol must be executable by Copilot agents, not just Claude.

## 2. Rationale

The existing context-management.md has 4 lines of concrete Claude Code detection guidance but only 2 vague lines for Copilot. Since not all users have access to Claude Code, Copilot must be a first-class citizen in the governance framework.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Only update docs | Yes | Need an instruction module for Tier 1 loading |
| Create a VS Code extension | Yes | Out of scope for config-only repo |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `instructions/copilot-context.md` | Tier 1 instruction module for Copilot context management |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/docs/context-management.md` | Expand Copilot section from 2 lines to full detection strategy |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. Expand the Copilot section in context-management.md with VS Code LM API, UI meter, heuristic estimation, context window sizes, and shutdown adaptations
2. Create instructions/copilot-context.md as a Tier 1 instruction module

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual review | Both files | Verify Copilot instructions match Claude Code detail level |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Copilot API changes | Medium | Low | Reference official docs; strategies are heuristic-based |

## 7. Dependencies

- [x] Context management doc exists
- [x] Instructions decomposition pattern established

## 8. Backward Compatibility

Purely additive. Expands existing documentation; no breaking changes.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Mandatory |
| documentation-review | Yes | Mandatory |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Align Copilot thresholds with base 70%/80% two-tier system | Copilot review identified conflict between proposed 80%/95% thresholds and base protocol's 80% hard stop. Reconciled to use the same two-tier system (70% checkpoint, 80% hard stop). |
| 2026-02-23 | Add refine label re-evaluation to startup.md | User feedback: agent cached refine assessment and re-added label after human removed it. Added Step 2a for live re-evaluation. |
