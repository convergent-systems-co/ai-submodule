# Create Importable Azure Dashboards

**Author:** Team Lead (agent)
**Date:** 2026-02-26
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/371
**Branch:** NETWORK_ID/feat/371/azure-dashboards

---

## 1. Objective

Add dashboard configuration support to `project.yaml`, create importable Azure dashboard JSON templates, and add GitHub Pages documentation pipeline guidance for consuming repos.

## 2. Rationale

SREs and developers need quick access to resource overviews, performance metrics, and AKS pod status. Importable dashboard JSON files reduce manual setup. GitHub Pages standardization ensures consistent documentation across consuming repos.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Dashboard templates + project.yaml config (chosen) | Yes | — |
| Full dashboard automation (auto-import to Azure) | Yes | Requires Azure API permissions consuming repos may not have; JSON import is simpler |
| Dashboard-as-code with Bicep | Yes | Complements this but out of scope — Bicep dashboard resource can reference these JSON templates |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/templates/dashboards/hub-dashboard.json` | Hub dashboard template — links to per-environment dashboards |
| `governance/templates/dashboards/environment-dashboard.json` | Per-environment dashboard template — resource group resources, App Insights, AKS status |
| `governance/templates/dashboards/README.md` | Usage guide for dashboard templates |
| `docs/guides/github-pages-setup.md` | Guide for enabling GitHub Pages with the Dark Forge theme |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/templates/project.yaml` (base template) | Add `dashboards` and `github_pages` configuration sections |
| `governance/templates/bicep/project.yaml` | Add `dashboards` section with Azure-specific defaults |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | — |

## 4. Approach

1. Add `dashboards` and `github_pages` config sections to the base project.yaml template
2. Create hub dashboard JSON template with parameterized placeholders for resource group, subscription, and environment
3. Create environment dashboard JSON template with tiles for: resource group resources, App Insights performance metrics, AKS reader view (pods, logs)
4. Create dashboard README with import instructions
5. Add `dashboards` section to the Bicep project.yaml template
6. Create GitHub Pages setup guide documenting how to enable Pages with the Dark Forge theme (referencing the existing deploy-docs.yml as the template)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| JSON validation | Dashboard templates | Verify JSON is valid and matches Azure dashboard schema |
| Manual review | project.yaml changes | Verify config sections are clear and well-documented |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Dashboard JSON schema changes in Azure | Low | Low | Templates use stable tile types; version comment in JSON |
| Consuming repos have different Azure resource sets | Medium | Low | Templates use parameterized placeholders; README explains customization |

## 7. Dependencies

- None — templates are standalone JSON files

## 8. Backward Compatibility

Fully backward compatible. New sections in project.yaml are optional. Existing consuming repos are unaffected.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | New documentation and guides |
| security-review | Yes | Default policy requirement |
| threat-modeling | Yes | Default policy requirement |
| cost-analysis | Yes | Default policy requirement (dashboards themselves are free in Azure) |
| data-governance-review | Yes | Default policy requirement |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | JSON template approach (not Bicep dashboard resources) | More portable; can be imported manually or automated later |
| 2026-02-26 | Parameterized placeholders instead of hard-coded values | Consuming repos will have different resource groups, subscriptions |
