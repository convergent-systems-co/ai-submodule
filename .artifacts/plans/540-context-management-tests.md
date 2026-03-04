# Plan: Add Context Management Unit Tests (#540)

## Objective
Create `governance/engine/tests/test_context_management.py` with comprehensive unit tests for the context management system including tier classification, checkpoint lifecycle, Phase 0 recovery, and gate action mapping.

## Approach
- Test tier classification edge cases (already partially covered in test_capacity.py but this adds focused context-management-specific integration tests)
- Test checkpoint schema validation using the actual checkpoint.schema.json
- Test checkpoint round-trip serialization
- Test Phase 0 recovery logic including closed issue handling
- Test malformed checkpoint handling
- Test context gate action mapping completeness

## Files
- New: `governance/engine/tests/test_context_management.py`

## Acceptance Criteria
- All tests pass
- Covers tier classification, escalation, unlimited mode, checkpoint schema, round-trip, Phase 0 recovery, malformed checkpoints, gate action mapping
