# Plan: Add Installation Hardening and Consuming Repo Parity Tests (#543)

## Objective
Create Python tests to validate installation artifacts, directory structure, integrity checks, and verification logic.

## Approach
- Validate governance directories are defined and .gitkeep-able
- Test the 9-point verification checks against known-good and known-bad states
- Test SHA-256 integrity verification for critical files
- Validate init.sh exists and has expected structure (flags, functions)
- Test modular scripts exist and are executable

## Files
- New: `governance/engine/tests/test_installation_hardening.py`
