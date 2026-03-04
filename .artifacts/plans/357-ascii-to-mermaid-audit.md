# Convert Remaining ASCII Diagrams to Mermaid

**Author:** Team Lead (agentic)
**Date:** 2026-02-25
**Status:** complete
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/357
**Branch:** NETWORK_ID/docs/357/ascii-to-mermaid-audit

---

## 1. Objective

Convert all remaining ASCII art diagrams to mermaid across all markdown files.

## 2. Rationale

PR #285 (closing #280) converted some but not all ASCII diagrams. A full audit found 14 remaining ASCII diagrams across 4 files.

## 3. Scope

### Files Modified

| File | Diagrams Converted |
|------|-------------------|
| `docs/architecture/governance-model.md` | 3: Section 6.6 Cognitive Routing, Section 7.6 Execution Flow, Appendix A.1 Full Pipeline |
| `docs/architecture/runtime-feedback.md` | 7: DI Generator Pipeline, Diff-Based Re-execution, Rate Limiting Hierarchy, Circuit Breaker State Machine, Drift Taxonomy, Baseline Lifecycle, Remediation Decision Tree |
| `docs/tutorials/end-to-end-walkthrough.md` | 2: PR Workflow, Governance Decision Flow |
| `docs/configuration/ci-gating.md` | 1: Check Ordering and Dependencies |
| `docs/architecture/runtime-feedback.md` | 1: Drift Detection Schedule (converted to markdown table) |

### Files NOT Modified (intentional)

- `governance/plans/*.md` — Immutable audit artifacts
- `docs/onboarding/project-structure.md` — Directory tree listing (not a diagram)
- `docs/architecture/session-state-persistence.md` — Directory tree listing
- `docs/research/technique-comparison.md` — Conceptual tree outline
- `governance/emissions/threat-model.md` — Directory tree listing
- `docs/tutorials/end-to-end-walkthrough.md` lines 109-123 — File tree listing (not a diagram)

## 4. Mermaid Types Used

| Diagram Type | Mermaid Block Type | Count |
|---|---|---|
| Flowchart / process flow | `flowchart TD` | 10 |
| Left-to-right flow | `flowchart LR` | 1 |
| State machine | `stateDiagram-v2` | 1 |
| Grid / taxonomy | `block-beta` | 1 |
| Table (not mermaid) | Markdown table | 1 |

## 5. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Drift Detection Schedule → markdown table | Content is tabular data, not a flow diagram |
| 2026-02-25 | Renamed Appendix A from "ASCII Architecture Diagrams" to "Architecture Diagrams" | No longer ASCII |
| 2026-02-25 | Excluded directory tree listings | Trees are structural notation, not process diagrams |
