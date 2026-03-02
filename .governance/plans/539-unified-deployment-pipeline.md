# Plan: Unified deployment pipeline template for consuming repos

**Issue:** #539
**Type:** Feature
**Priority:** Medium

## Problem

Consuming repos often have multiple manually-triggered deployment workflows that operators must chain manually. No unified orchestrating pipeline exists.

## Solution

Create reusable templates:
1. Pipeline workflow template (`governance/templates/workflows/pipeline.yml`)
2. Validate-promotion composite action (`governance/templates/actions/validate-promotion/action.yml`)
3. Adoption guide documentation

## Deliverables

1. `governance/templates/workflows/pipeline.yml` — orchestrating workflow with conditional phases
2. `governance/templates/actions/validate-promotion/action.yml` — reusable promotion validation
3. `docs/guides/unified-deployment-pipeline.md` — adoption guide
4. Run tests

## Design

- Existing individual workflows remain manually usable via `workflow_dispatch`
- Pipeline calls them via `workflow_call` (no step duplication)
- Promotion validation is centralized
- Skip flags for inapplicable phases
- Language/framework agnostic
