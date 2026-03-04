# Add Explicit Context Capacity Checks at Pipeline Phase Boundaries

**Author:** Team Lead (agent)
**Date:** 2026-02-26
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/381
**Branch:** NETWORK_ID/feat/381/context-capacity-phase-gates

---

## 1. Objective

Add structured context capacity gates at every phase boundary in the startup loop, define capacity tiers (green/yellow/orange/red) with specific thresholds, ensure cross-platform compatibility (Claude Code + Copilot), and document the approach in context-management.md.

## 2. Rationale

Context pressure can build mid-phase and go undetected, risking compaction with dirty state. Explicit gates at phase boundaries provide deterministic checkpoints.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Continuous monitoring only | Yes | No deterministic check points; relies on heuristic signals alone |
| Phase-level gates (chosen) | Yes | — |
| External watchdog process | Yes | Not portable across Claude Code and Copilot |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files needed |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Add context gate check block before each phase (1-5). Define green/yellow/orange/red capacity tiers with thresholds in the Context Capacity section. |
| `docs/architecture/context-management.md` | Add capacity tiers table, document phase boundary gate protocol, add platform-specific gate detection. |
| `governance/personas/agentic/coder.md` | Add pre-task capacity check instruction with tier-aware behavior. |
| `governance/personas/agentic/devops-engineer.md` | Update threshold table to include 4-tier model (green/yellow/orange/red). |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. Define the 4-tier capacity model in `startup.md` Context Capacity section:
   - Green (<60%): Normal operation
   - Yellow (60-70%): No new Coder dispatches; finish in-flight work
   - Orange (70-80%): Stop after current PR; checkpoint
   - Red (>=80%): Stop immediately; emergency checkpoint
2. Add a "Context Gate" block before each phase (1-5) in startup.md that checks tool call count, issues completed, and degraded recall signals
3. Update context-management.md with the tier definitions, phase gate protocol, and platform-specific detection signals
4. Add pre-task capacity check to the Coder persona
5. Update DevOps Engineer persona threshold table to align with 4-tier model

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual review | All modified files | Verify gates are present at each phase boundary |
| Consistency check | Cross-file | Verify thresholds are consistent across startup.md, context-management.md, devops-engineer.md |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Thresholds too aggressive causing premature shutdown | Low | Medium | Based on existing operational experience; thresholds match existing 70%/80% model |
| Inconsistent thresholds across files | Medium | High | Single source of truth in startup.md; other files reference it |

## 7. Dependencies

- None — all changes are additive documentation/cognitive artifacts

## 8. Backward Compatibility

Fully backward compatible. Adds gates that are advisory — agents that don't implement them continue to work with existing heuristic signals.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Significant documentation changes |
| security-review | Yes | Default policy requirement |
| threat-modeling | Yes | Default policy requirement |
| cost-analysis | Yes | Default policy requirement |
| data-governance-review | Yes | Default policy requirement |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Use 4-tier model (green/yellow/orange/red) | Matches issue proposal and provides finer-grained control than existing 2-tier (70%/80%) |
