# Plan: Add State Persistence and Cross-Session Recovery Tests (#545)

## Objective
Create tests for state persistence lifecycle (agent log, ADO sync, session state, merge strategy).

## Approach
- Test JSONL agent log append/read/ordering
- Test session ID format validation
- Test ADO sync ledger and error schema validation
- Test state merge strategy (numeric max, array dedup, deep merge)
- Test checkpoint-to-state handoff
- Test directory creation for missing state dirs

## Files
- New: `governance/engine/tests/test_state_persistence.py`
