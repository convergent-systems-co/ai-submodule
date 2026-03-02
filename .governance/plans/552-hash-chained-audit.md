# Plan: Tamper-Evident Hash-Chained Audit Trail (#552)

## Summary
Add SHA-256 hash chaining to the existing audit system so each JSONL entry
includes the hash of the previous entry, creating a tamper-evident chain.
Add a verification command to detect retroactive modifications.

## Changes

### 1. Update: `governance/engine/orchestrator/audit.py`
- Add `previous_hash` field to each audit entry
- First entry uses a seed value derived from `session_id`
- Each subsequent entry includes SHA-256 hash of the previous entry
- Backward compatible: existing read_all/count still work

### 2. New file: `governance/engine/audit_chain.py`
- Verification function that validates the hash chain
- Reports the first broken link if tampering is detected
- Can be run as a CLI tool

### 3. Update: `governance/engine/tests/test_audit.py`
- Add tests for hash chaining
- Add tests for chain verification
- Add tests for tamper detection

## Test Plan
- `python -m pytest governance/engine/ -x --tb=short`
