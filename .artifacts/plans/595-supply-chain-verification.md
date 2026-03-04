# Plan: Supply Chain Verification for Submodule Consumers (#595)

## Summary
Add content integrity verification for consuming repos so they can verify
the dark-forge has not been tampered with after `git submodule update`.

## Changes

### 1. New file: `governance/engine/supply_chain.py`
- Generate SHA-256 content hashes for critical files (policy profiles, schemas, personas, review prompts)
- Write hashes to a manifest file (`governance/integrity-manifest.json`)
- Verification function that compares current file hashes against manifest
- Integration with `bin/init.sh --verify`

### 2. New file: `governance/integrity-manifest.json`
- Auto-generated manifest of file hashes for critical governance files

### 3. New file: `governance/engine/tests/test_supply_chain.py`
- Tests for manifest generation
- Tests for verification (pass and fail cases)
- Tests for tamper detection

## Test Plan
- `python -m pytest governance/engine/ -x --tb=short`
