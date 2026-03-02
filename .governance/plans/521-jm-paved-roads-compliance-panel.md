# JM Paved Roads Compliance Panel

**Author:** Code Manager (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/521
**Branch:** NETWORK_ID/feat/521/jm-paved-roads-compliance-panel

---

## 1. Objective

Add a new governance review panel (`jm-standards-compliance-review`) that evaluates code and infrastructure changes against JM Family Paved Roads standards (https://github.com/JM-Paved-Roads). The panel checks whether approved technologies, frameworks, and patterns are being used, flags deviations, and requires documented justification for any approved overrides configured in `project.yaml`.

## 2. Rationale

JM Family has established "Paved Roads" — pre-approved technology choices and patterns for infrastructure and code. Currently, there is no automated governance check enforcing these standards. Adding a review panel integrates Paved Roads compliance into the existing multi-panel governance pipeline, ensuring every PR is evaluated before merge.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Manual review checklist | Yes | Does not scale, easily bypassed, not integrated with governance pipeline |
| Lint rule per technology | Yes | Too fragmented, hard to maintain, no central policy definition |
| New governance panel | Yes (selected) | Integrates with existing pipeline, follows established patterns, centralized configuration |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/prompts/reviews/jm-standards-compliance-review.md` | Review panel prompt with perspectives for evaluating Paved Roads compliance |
| `governance/emissions/jm-standards-compliance-review.json` | Baseline emission for fallback/calibration |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/policy/default.yaml` | Add `jm-standards-compliance-review` to `optional_panels` with trigger for code/infra changes |
| `governance/prompts/shared-perspectives.md` | Add "Standards Compliance Reviewer" perspective if reusable |
| `CLAUDE.md` | Document the new panel in the architecture section |
| `docs/architecture/ci-workflows.md` | Reference new panel in the panel listing if applicable |

### Files to Delete

None.

## 4. Approach

1. **Create the review panel prompt** (`jm-standards-compliance-review.md`) following the Anthropic Parallelization (Voting) pattern used by all 19 existing panels:
   - Perspective 1: **Standards Compliance Reviewer** — evaluates technology choices against Paved Roads catalog
   - Perspective 2: **Infrastructure Engineer** — evaluates infrastructure patterns (Bicep/Terraform/networking) against approved patterns
   - Perspective 3: **Deviation Auditor** — checks for documented justification of any overrides in `project.yaml`
   - Each perspective produces independent findings with evidence

2. **Create baseline emission** (`jm-standards-compliance-review.json`) matching `panel-output.schema.json`

3. **Register the panel** in `governance/policy/default.yaml` under `optional_panels` with trigger on code and infrastructure file changes

4. **Update shared perspectives** if the Standards Compliance Reviewer perspective is needed by other panels

5. **Update documentation** — CLAUDE.md, architecture docs

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | Baseline emission | Validate baseline emission against `panel-output.schema.json` |
| Manual | Panel prompt | Verify panel produces valid structured emission when invoked |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Panel blocks legitimate deviations | Medium | Medium | Override mechanism in `project.yaml` with `paved_roads.approved_deviations` |
| Paved Roads catalog unavailable | Low | Low | Panel operates on known standards; catalog is reference only |
| Too noisy for repos not using JM standards | Low | Low | Optional panel, only triggered on code/infra changes |

## 7. Dependencies

- [x] Existing panel infrastructure (review prompts, emissions, policy engine) — available
- [ ] JM Paved Roads catalog at https://github.com/JM-Paved-Roads — external reference, non-blocking

## 8. Backward Compatibility

Fully additive. The panel is optional (not added to `required_panels`). Existing repos are unaffected unless they opt in.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New governance code |
| security-review | Yes | Always required |
| threat-modeling | Yes | Always required |
| cost-analysis | Yes | Always required |
| documentation-review | Yes | Docs updated |
| governance-compliance-review | Yes | Governance artifact |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Panel is optional, not required | Not all consuming repos use JM Paved Roads |
| 2026-02-27 | Override mechanism via project.yaml | Allows documented deviations (e.g., DAPR approved for specific use cases) |
