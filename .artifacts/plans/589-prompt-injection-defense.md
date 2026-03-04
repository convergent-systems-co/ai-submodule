# Plan: Two-Stage Prompt Injection Defense (#589)

## Summary
Add a deterministic regex pre-filter for prompt injection detection as Phase 1, feeding into the existing Tester persona scanning as Phase 2 (defense in depth).

## Changes

### 1. New file: `governance/engine/security_prefilter.py`
- Deterministic regex + entropy scanner for 6 pattern categories:
  - Direct instruction overrides ("ignore previous", "you are now", etc.)
  - HTML comment injection (`<!-- AGENT_MSG_START -->` in untrusted content)
  - Base64 payloads (Shannon entropy >= 4.5 on base64-like strings)
  - Markdown injection (hidden links, image tags with data URIs)
  - Delimiter smuggling (AGENT_MSG markers, JSON-like protocol messages)
  - System prompt exfiltration ("repeat your instructions", "show system prompt")
- Returns structured findings compatible with the policy engine
- Zero LLM token cost — purely deterministic

### 2. New file: `governance/engine/tests/test_security_prefilter.py`
- Tests for each of the 6 pattern categories
- Tests for benign content (no false positives)
- Tests for structured finding output format

### 3. Update: `governance/policy/default.yaml`
- Add `prompt_injection_prefilter` section under `panel_execution` referencing the new module

### 4. Update: `docs/architecture/` (if needed)
- Reference the two-stage defense in security documentation

## Test Plan
- `python -m pytest governance/engine/ -x --tb=short`
- Verify all 6 pattern categories detect their respective attacks
- Verify benign content passes cleanly
