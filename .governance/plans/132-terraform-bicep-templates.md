# Terraform and Bicep Language Defaults

**Author:** Coder (agentic)
**Date:** 2026-02-23
**Status:** in_progress
**Issue:** #132
**Branch:** itsfwcp/feat/132/terraform-bicep-templates

---

## 1. Objective

Create project.yaml templates for Terraform and Bicep following existing template patterns, configured with JM-Terraform org modules and SET-Apps Bicep registry.

## 2. Rationale

Existing templates (python, csharp, go, node, react) provide language-specific conventions. IaC projects need equivalent defaults pointing at organizational module registries.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Generic IaC template | Yes | Terraform and Bicep have fundamentally different toolchains |
| Separate templates per cloud | Yes | Over-engineering; framework field covers this |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| templates/bicep/project.yaml | Bicep template with SET-Apps ACR registry config |
| templates/terraform/project.yaml | Terraform template with JM-Terraform org module config |

### Files to Modify

None.

### Files to Delete

None.

## 4. Approach

1. Create Bicep template with ACR registry alias from banking-app's bicepconfig.json
2. Create Terraform template with JM-Terraform org module references
3. Both follow existing template structure (name, language, personas, panels, conventions, instructions)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | YAML syntax | Verify valid YAML |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Registry URL changes | Low | Low | URL is in conventions, easily updated |

## 7. Dependencies

N/A.

## 8. Backward Compatibility

Additive only — new templates, no existing files modified.

## 9. Governance

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Used banking-app bicepconfig.json as reference | Real-world usage from consuming repo |
| 2026-02-23 | Pointed Terraform at JM-Terraform GitHub org | Per issue requirements |
