# Plan: Create appropriate cost personas and panels

**Issue:** #75 — Create appropriate cost personas and panels
**Priority:** P2
**Type:** enhancement
**Status:** in_progress

## Problem

The cost-analysis panel exists but lacks specialized personas for cloud infrastructure costing (Azure/AWS from Bicep/Terraform) and LLM/AI development costing.

## Solution

1. Create `finops/cloud-cost-analyst.md` persona — evaluates Azure/AWS infrastructure costs from IaC (Bicep, Terraform)
2. Create `finops/llm-cost-analyst.md` persona — evaluates LLM token costs, agentic AI development costs
3. Update `panels/cost-analysis.md` to include the two new personas
4. Update `personas/index.md` with the new persona entries
5. Update documentation (CLAUDE.md, GOALS.md) with new persona counts

## Files Changed

- `governance/personas/finops/cloud-cost-analyst.md` — New persona
- `governance/personas/finops/llm-cost-analyst.md` — New persona
- `governance/personas/panels/cost-analysis.md` — Add new participants
- `governance/personas/index.md` — Add new entries
- `CLAUDE.md` — Update persona count (57 → 59)
- `GOALS.md` — Add to completed work
