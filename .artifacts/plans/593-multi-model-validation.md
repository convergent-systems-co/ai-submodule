# Plan: Add multi-model validation support for review panels

**Issue:** #593
**Type:** Feature
**Priority:** Medium

## Problem

Review panels execute on a single model. No support for cross-model consensus to catch different issues.

## Solution

1. Add `multi_model` configuration to policy profiles
2. Create `multi_model_aggregator.py` in governance/engine/ for consensus logic
3. Policy engine aggregates multi-model emissions per panel
4. Configurable consensus thresholds (majority, supermajority, unanimous)
5. Backward compatible: default is single model

## Deliverables

1. `governance/engine/multi_model_aggregator.py` — consensus aggregation
2. Update policy engine to detect and aggregate multi-model emissions
3. Add multi_model config to default policy profile
4. Tests
