# Plan: Add Agentic Loop Protocol and Persona Validation Tests (#541)

## Objective
Create test files validating the agentic protocol (message types, circuit breaker rules, phase transitions) and persona file structure.

## Approach
- Create `test_agentic_protocol.py` for protocol validation, CSP, issue size checks, phase transitions
- Create `test_persona_structure.py` for persona markdown structure validation

## Files
- New: `governance/engine/tests/test_agentic_protocol.py`
- New: `governance/engine/tests/test_persona_structure.py`
