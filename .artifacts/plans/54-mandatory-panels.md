# Plan: Panels that must ALWAYS run

**Issue:** #54 — Panels that must ALWAYS run
**Type:** enhancement
**Status:** in_progress

## Problem

Security (general + threat model), cost analysis, and documentation review panels only run conditionally based on file changes. They should run on every PR.

## Solution

Add `threat-modeling`, `cost-analysis`, and `documentation-review` to `required_panels` in all three policy profiles. Remove them from `optional_panels` where present. Add weights where missing.

## Files Changed

- `governance/policy/default.yaml` — Add 3 panels to required, remove from optional, add cost-analysis weight
- `governance/policy/fin_pii_high.yaml` — Add 3 panels to required, remove documentation-review from optional, add weights
- `governance/policy/infrastructure_critical.yaml` — Add 3 panels to required, add weights
- `GOALS.md` — Note completion
- `CLAUDE.md` — No changes needed (panel counts unchanged, just configuration)
