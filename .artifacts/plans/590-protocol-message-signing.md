# Plan: Cryptographic Signing for Inter-Agent Protocol Messages (#590)

## Summary
Add HMAC-based message signing to all inter-agent protocol messages to prevent
protocol spoofing and provide cryptographic proof of message origin.

## Changes

### 1. New file: `governance/engine/message_signing.py`
- HMAC-SHA256 signing/verification for protocol messages
- Per-persona key derivation from a session secret
- Sign all message types: ASSIGN, STATUS, RESULT, FEEDBACK, APPROVE, BLOCK, CANCEL, ESCALATE, WATCH
- Verification function that validates signature before processing

### 2. New file: `governance/engine/tests/test_message_signing.py`
- Tests for signing and verification
- Tests for key derivation per persona
- Tests for tamper detection (modified message fails verification)
- Tests for wrong-persona key rejection

## Test Plan
- `python -m pytest governance/engine/ -x --tb=short`
