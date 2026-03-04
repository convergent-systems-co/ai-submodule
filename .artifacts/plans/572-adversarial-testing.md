# Plan: Adversarial Testing Framework for Governance Defenses (#572)

## Summary
Create a red-team test suite that validates prompt injection defenses,
agent protocol spoofing prevention, and role-switching detection.

## Changes

### 1. New directory: `governance/engine/tests/adversarial/`
- `__init__.py`
- `test_prompt_injection.py` — attack vectors for issue bodies, PR descriptions, commit messages
- `test_protocol_spoofing.py` — forged APPROVE, ASSIGN, BLOCK messages
- `test_role_switching.py` — persona override attempts
- `test_encoded_instructions.py` — base64, unicode, obfuscation attacks

### 2. New file: `governance/engine/tests/adversarial/vectors.py`
- Central repository of attack vectors for reuse across tests

## Test Plan
- `python -m pytest governance/engine/ -x --tb=short`
