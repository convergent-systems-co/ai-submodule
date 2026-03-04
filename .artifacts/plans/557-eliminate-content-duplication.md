# Eliminate Content Duplication Across Governance Artifacts (#557)

**Author:** Claude (Coder)
**Date:** 2026-03-01
**Status:** approved
**Issue:** #557
**Branch:** itsfwcp/refactor/557/eliminate-content-duplication

---

## 1. Objective

Eliminate duplicated content across 7 persona files and related governance artifacts, establishing single sources of truth per concept. Target: ~3,000-5,000 tokens saved per session by removing redundant inline content.

## 2. Rationale

Same information is copied 4-6 times across persona files, creating sync drift (e.g., capacity thresholds already diverged between files). Every duplication wastes context tokens and increases maintenance burden.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Full persona rewrite | Yes | Scope creep; save for #556 |
| Automated dedup tool | Yes | Overkill; manual is tractable for 6 files |
| Reference-only approach | Yes | Selected — keep unique content, reference shared |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| governance/personas/agentic/coder.md | Replace Containment Policy section with reference, remove CANCEL duplication, simplify capacity check to reference |
| governance/personas/agentic/iac-engineer.md | Same as coder — containment, CANCEL, anti-patterns |
| governance/personas/agentic/tester.md | Replace Containment Policy section with reference |
| governance/personas/agentic/team-lead.md | Replace Containment Policy section with reference |
| governance/personas/agentic/devops-engineer.md | Replace Containment Policy section with reference; keep capacity table (operational) |
| governance/personas/agentic/project-manager.md | Replace Containment Policy section with reference; keep capacity table (PM-specific) |

### Files to Delete

None.

## 4. Approach

1. For each persona file, replace the Containment Policy section (3-4 paragraphs, ~150 words) with a 2-line summary: persona-specific allowed/denied ops + reference to `agent-containment.yaml`
2. For Coder and IaC Engineer, remove duplicated CANCEL handling text (verbatim copies) and replace with: "On receiving CANCEL: follow the CANCEL receipt protocol in `governance/prompts/agent-protocol.md`."
3. For Coder, replace the inline capacity tier descriptions with: "Pre-task capacity check per the four-tier model in `governance/prompts/agent-protocol.md`."
4. Remove duplicated anti-pattern items (identical between Coder and IaC Engineer)
5. Remove the 6x duplicated violation logging sentence; fold into the containment reference

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | All 7 persona files | Verify references point to correct source files |
| Word count | All 7 files | Confirm token reduction |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Agent loses context on containment rules | Low | Medium | Keep persona-specific ops inline, only remove boilerplate |
| References become stale | Low | Low | References point to stable files (agent-containment.yaml, agent-protocol.md) |

## 7. Dependencies

- [x] None — standalone refactor

## 8. Backward Compatibility

Additive change — no code or schema modifications. Only cognitive artifacts (Markdown) are affected.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Content restructuring |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-01 | Keep capacity tables in DevOps + PM personas | They have persona-specific signals (issues completed vs active CMs) |
| 2026-03-01 | Keep CANCEL handling unique to Team Lead | CM has unique 5-step propagation logic, not duplicated from protocol |
