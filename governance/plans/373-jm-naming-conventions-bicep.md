# Feat: JM Naming Convention Governance for Bicep

**Author:** Coder (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/373
**Branch:** NETWORK_ID/feat/373/jm-naming-conventions

---

## 1. Objective

Ensure JM Family naming conventions are enforced by requiring consuming repos to use `getResourceNames()` from the centralized Bicep registry util module (`br/acr-prod:modules/util:v0`). Resource names must be derived from this function, not hardcoded or interpolated.

## 2. Scope

### Files to Modify

| File | Change |
|------|--------|
| `governance/personas/agentic/iac-engineer.md` | Add "Resource Naming via Registry Util Module" section requiring `getResourceNames()` usage |
| `governance/templates/bicep/project.yaml` | Add `naming` config section under `conventions` |
| `governance/prompts/reviews/architecture-review.md` | Add naming convention compliance criteria to Infrastructure Engineer perspective |

### Files to Create

| File | Purpose |
|------|---------|
| `docs/guides/naming-convention-adoption.md` | Step-by-step guide for consuming repos to adopt JM naming conventions |

## 3. Approach

1. Add an explicit section to the IaC Engineer persona documenting the `getResourceNames()` requirement, usage patterns, compliance rules, and naming pattern types (standard, mini, small)
2. Extend the Bicep project template with a `naming` convention block that declares the util module path and enforces its use
3. Add naming convention compliance checks to the architecture review panel under the Infrastructure Engineer perspective
4. Create a comprehensive adoption guide with examples, pattern reference tables, and common mistakes

## 4. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing IaC Engineer persona | Low | Additive section only, no existing content modified |
| project.yaml backward compatibility | Low | New `naming` key is additive, existing keys unchanged |
| Adoption friction for consuming repos | Medium | Detailed guide with copy-paste examples provided |

## 5. Acceptance Criteria

- [ ] IaC Engineer persona requires `getResourceNames()` import from `br/acr-prod:modules/util:v0`
- [ ] Bicep project template includes naming convention config
- [ ] Architecture review panel checks for naming convention compliance
- [ ] Documentation guide covers import, usage, destroy/purge pipelines, and all three naming patterns
