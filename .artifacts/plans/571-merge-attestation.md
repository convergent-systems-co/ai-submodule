# Plan: Cryptographic Attestation for Governance Merge Decisions (#571)

## Summary
Add signed run manifest generation with content hashes of all panel
emissions, linking panel outputs to merge decisions cryptographically.

## Changes

### 1. New file: `governance/engine/attestation.py`
- Generate signed run manifests with HMAC-SHA256
- Include content hashes of all panel emissions
- Store manifest hash for inclusion in merge commit messages
- Verification function for manifest integrity

### 2. New file: `governance/engine/tests/test_attestation.py`
- Tests for manifest signing
- Tests for emission hash inclusion
- Tests for tamper detection on manifests

## Test Plan
- `python -m pytest governance/engine/ -x --tb=short`
