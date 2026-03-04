# Plan: Enforce Agent Containment by Default (#591)

## Summary
Change the default enforcement mode in `agent-containment.yaml` from `advisory` to `enforced`, add a containment enforcement module, and update orchestrator status to show enforcement mode.

## Changes

### 1. Update: `governance/policy/agent-containment.yaml`
- Change `enforcement.mode` from `advisory` to `enforced`
- Add documentation comment about opt-in advisory mode for development

### 2. New file: `governance/engine/containment.py`
- Containment checker that evaluates file paths and operations against persona rules
- Returns block/allow decisions based on enforcement mode
- Logs violations to the containment violations JSONL file

### 3. New file: `governance/engine/tests/test_containment.py`
- Tests for enforced mode blocking
- Tests for advisory mode logging
- Tests for all persona path restrictions
- Tests for denied operations

## Test Plan
- `python -m pytest governance/engine/ -x --tb=short`
