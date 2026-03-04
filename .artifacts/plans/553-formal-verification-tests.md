# Plan: Add Formal Verification and Property-Based Testing for Policy Engine (#553)

## Objective
Create comprehensive formal verification and property-based tests for the policy engine DSL.

## Approach
1. Define the DSL grammar structure and test it with Hypothesis strategies
2. Property-based testing: monotonicity (higher risk -> more restrictive), idempotency, determinism
3. Synthetic emission corpus for policy evaluation test mode
4. Decision tables for block and escalation rules
5. Full evaluate() round-trip with synthetic data

## Files
- New: `governance/engine/tests/test_formal_verification.py`
