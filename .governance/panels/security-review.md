# Security Review: PR #587 — feat: retire prompt chaining -- orchestrator CLI as sole control plane

**Panel:** security-review v1.0.0
**PR:** #587 (`feat/retire-prompt-chaining` -> `main`)
**Repository:** SET-Apps/ai-submodule
**Date:** 2026-03-02
**Model:** claude-opus-4-6

---

## Threat Model and Trust Boundaries

This PR replaces the prompt-chained agentic loop with a Python CLI-based orchestrator (`python -m governance.engine.orchestrator`). The change introduces:

1. **New CLI entry point** (`__main__.py`) — accepts `--config`, `--result`, `--session-id`, `--type`, `--count`, `--phase` arguments from the LLM caller.
2. **Persistent session state** (`session.py`) — writes/reads JSON files to `.governance/state/sessions/`.
3. **Shell wrapper** (`bin/auto-clear.sh`) — outer loop that restarts `claude` processes with configurable arguments.
4. **State machine serialization** — `to_dict()`/`from_dict()` round-trips for the orchestrator's state machine.
5. **Subprocess call** — `_get_current_branch()` invokes `git branch --show-current`.

**Trust boundaries:**
- LLM-to-CLI: The LLM constructs CLI arguments (including `--result` JSON payloads). The CLI parses these via `argparse` and `json.loads()`.
- Disk-to-process: Session state is read from JSON files on disk and deserialized into dataclass instances.
- Shell-to-process: `auto-clear.sh` passes `--prompt` and `--max-retries` arguments to the `claude` binary.

---

## Per-Perspective Findings

### 1. Security Auditor

**Threats Identified:**

#### Finding SA-1: JSON injection via `--result` CLI argument (Low)

**File:** `governance/engine/orchestrator/__main__.py`, line ~96 (diff line 694-697)
**Evidence:**
```python
try:
    phase_result = json.loads(args.result)
except json.JSONDecodeError as e:
    print(json.dumps({"error": f"Invalid JSON in --result: {e}"}))
```

The `--result` parameter accepts arbitrary JSON from the caller. However, `json.loads()` produces a Python dict which is then consumed by `_absorb_result()` that only reads specific keys (`issues_selected`, `plans`, `dispatched_task_ids`, `prs_created`, `prs_resolved`, `issues_completed`, `merged_prs`). Unexpected keys are silently ignored.

**Severity:** Low
**Mitigations already present:** `argparse` provides basic parsing. `json.loads()` decodes to native Python types (not executable). `_absorb_result()` reads only expected keys.
**Recommendation:** Consider adding JSON schema validation on the `--result` payload to reject unexpected keys and enforce type constraints on expected values. This is defense-in-depth, not a blocking issue.

#### Finding SA-2: No secrets detected (Info)

No hardcoded credentials, API keys, tokens, or secrets were found in the diff. The code does not handle authentication or secret material.

**Severity:** Info

#### Finding SA-3: Error message information leakage (Info)

**File:** `governance/engine/orchestrator/__main__.py`, lines ~96-97 (diff line 697)
**Evidence:**
```python
print(json.dumps({"error": f"Invalid JSON in --result: {e}"}))
```

JSON decode error details are printed to stdout. In this context (local CLI tool called by the LLM within the same session), this is informational and aids debugging. No sensitive data is exposed since the input is LLM-generated.

**Severity:** Info
**Recommendation:** No action required. This is appropriate for a local CLI tool.

---

### 2. Infrastructure Engineer

**Threats Identified:**

#### Finding IE-1: Session directory auto-creation with `mkdir -p` equivalent (Info)

**File:** `governance/engine/orchestrator/session.py`, line ~93 (diff line 994)
**Evidence:**
```python
self.session_dir.mkdir(parents=True, exist_ok=True)
```

The `SessionStore` creates directories with default permissions (0o777 modified by umask, typically resulting in 0o755). Session files are written with `open(path, "w")` which uses default file permissions (typically 0o644).

**Severity:** Info
**Assessment:** The session state contains orchestrator metadata (phase numbers, issue references, signal counts) -- not secrets or credentials. Default permissions are acceptable for this data classification.

#### Finding IE-2: File write without atomic operation (Low)

**File:** `governance/engine/orchestrator/session.py`, line ~1004 (diff line 1004-1005)
**Evidence:**
```python
with open(path, "w") as f:
    json.dump(asdict(session), f, indent=2)
```

Session files are written directly (not atomically). If the process is killed during a write, the file could be left in a partial/corrupted state. On the next `load()`, `json.load()` would raise a `JSONDecodeError`, and the session would be treated as non-existent (load returns `None` on missing files, but would raise on corrupt files).

**Severity:** Low
**Recommendation:** Use atomic write pattern (write to a temporary file, then `os.rename()`). Alternatively, wrap `load()` in a try/except for `JSONDecodeError` to handle corrupted files gracefully. This is a robustness improvement, not a security vulnerability.

---

### 3. Compliance Officer

**Threats Identified:**

#### Finding CO-1: No PII or regulated data handling introduced (Info)

This PR introduces orchestrator control-plane logic. The data model (`PersistedSession`) stores:
- Issue references (e.g., `#42`) -- public GitHub references
- Phase numbers and signal counters -- operational metadata
- PR references -- public GitHub references
- Timestamps -- operational metadata

No PII, PHI, cardholder data, or regulated data classes are introduced or processed. No cross-border data transfer implications.

**Severity:** Info

#### Finding CO-2: Audit trail maintained (Info)

The `AuditLog` continues to record events as append-only JSONL. New event types (`session_init`, `session_restored`, `session_done`) are added. The audit trail is preserved and extended.

**Severity:** Info
**Assessment:** Compliant with SOC2 change management and audit trail requirements. No gaps introduced.

---

### 4. Adversarial Reviewer

**Threats Identified:**

#### Finding AR-1: Session ID path construction allows directory traversal (Low)

**File:** `governance/engine/orchestrator/session.py`, line ~97 (diff line 997-998)
**Evidence:**
```python
def _path_for(self, session_id: str) -> Path:
    safe_id = session_id.replace("/", "-").replace(" ", "-")
    return self.session_dir / f"{safe_id}.json"
```

The `_path_for()` method sanitizes `/` and space characters, but does not sanitize `..` sequences. A session ID like `....foo` would become `....foo.json` (harmless). However, a session ID containing `..` without `/` separators is unlikely to escape the directory since `Path("/base") / "..foo.json"` resolves to `/base/..foo.json`, not `/foo.json`. The replacement of `/` to `-` is the key defense -- `../../etc/passwd` becomes `..-..-etc-passwd.json`.

**Severity:** Low
**Assessment:** The sanitization is sufficient in practice because: (1) `/` is replaced with `-`, preventing directory traversal via `../`; (2) the LLM generates session IDs (not external users); (3) even CLI users would need local access to invoke the tool. However, a more robust approach would be to validate the session ID against a strict pattern (e.g., `^[a-zA-Z0-9_-]+$`).
**Recommendation:** Add a regex validation: `if not re.match(r'^[a-zA-Z0-9._-]+$', session_id): raise ValueError("Invalid session ID")`. This is defense-in-depth.

#### Finding AR-2: Idempotent double-complete hides stale state (Info)

**File:** `governance/engine/orchestrator/step_runner.py`, line ~1345 (diff line 1345-1346)
**Evidence:**
```python
if completed_phase in self._session.completed_phases:
    return self._current_result("execute_phase")
```

Double-completing a phase is a no-op. If the LLM replays a step due to a context reset, it gets the current state. This is the correct behavior for idempotency. No vulnerability here.

**Severity:** Info

#### Finding AR-3: Broad exception swallowing in circuit breaker restoration (Low)

**File:** `governance/engine/orchestrator/step_runner.py`, lines ~1496-1505 (diff lines 1496-1505)
**Evidence:**
```python
for _ in range(state.get("feedback_cycles", 0)):
    try:
        self._breaker.record_feedback(cid)
    except Exception:
        break
```

All exceptions are caught and silently swallowed during circuit breaker state restoration. If the breaker's internal state is inconsistent (e.g., corrupted session data), the restoration silently degrades. The `except Exception` pattern masks both expected errors (e.g., `CircuitBreakerTripped`) and unexpected ones (e.g., `TypeError` from corrupted data).

**Severity:** Low
**Recommendation:** Catch only `CircuitBreakerTripped` (the expected exception) and log a warning for other exception types. This improves debuggability without affecting functionality.

---

### 5. Backend Engineer

**Threats Identified:**

#### Finding BE-1: Subprocess invocation with hardcoded command (Info)

**File:** `governance/engine/orchestrator/step_runner.py`, lines ~1855-1858 (diff lines 1855-1858)
**Evidence:**
```python
result = subprocess.run(
    ["git", "branch", "--show-current"],
    capture_output=True, text=True, timeout=5,
)
```

The subprocess call uses a list-based argument form (not shell=True), which prevents command injection. The command is hardcoded with no user-controlled inputs. The 5-second timeout prevents hangs. Exception handling covers `TimeoutExpired`, `FileNotFoundError`, and `OSError`.

**Severity:** Info
**Assessment:** This is a well-implemented subprocess call. No injection risk.

#### Finding BE-2: Shell script argument handling in auto-clear.sh (Info)

**File:** `bin/auto-clear.sh`, lines ~89-95 (diff lines 89-95)
**Evidence:**
```bash
case "$1" in
    --max-retries) MAX_RETRIES="$2"; shift 2 ;;
    --prompt) PROMPT="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
esac
```

The shell script accepts `--prompt` which is passed directly to `claude --prompt "$PROMPT"`. The `$PROMPT` variable is quoted, preventing word splitting and glob expansion. The default value is `/startup` (a safe string). Since this script is run locally by the user (not exposed as a network service), the attack surface is limited to local privilege.

**Severity:** Info
**Assessment:** Properly quoted variable expansion. No command injection vector.

#### Finding BE-3: JSON deserialization from disk files (Info)

**File:** `governance/engine/orchestrator/session.py`, lines ~1013-1015 (diff lines 1013-1015)
**Evidence:**
```python
with open(path) as f:
    data = json.load(f)
return PersistedSession(**{k: v for k, v in data.items() if k in PersistedSession.__dataclass_fields__})
```

The `load()` method reads JSON from disk and constructs a `PersistedSession` dataclass. The dict comprehension filters to known fields only (`k in PersistedSession.__dataclass_fields__`), preventing unknown key injection. Python's `json.load()` produces native types (dicts, lists, strings, numbers, booleans, None) -- no code execution risk.

**Severity:** Info
**Assessment:** Safe deserialization pattern. The field-filtering dict comprehension is a good defense-in-depth measure.

---

## Consolidated Output

### Critical Vulnerabilities

None.

### High-Risk Findings

None.

### Compliance Gaps

None identified. No regulated data is handled. Audit trail is preserved and extended.

### Defense-in-Depth Recommendations

1. **Session ID validation** (AR-1): Add strict regex validation for session IDs (`^[a-zA-Z0-9._-]+$`). The current `/` and space replacement is functional but a strict allowlist is more robust.

2. **Atomic file writes** (IE-2): Use write-to-temp-then-rename pattern for session persistence to prevent corrupted state files on process death.

3. **Targeted exception handling** (AR-3): Replace `except Exception` with `except CircuitBreakerTripped` in circuit breaker restoration. Log unexpected exceptions.

4. **JSON schema validation for CLI input** (SA-1): Validate `--result` payload structure against expected schemas per phase. Currently only `json.loads()` validation is performed.

5. **Corrupt file handling** (IE-2): Add `try/except JSONDecodeError` in `SessionStore.load()` and `load_latest()` to gracefully handle corrupted session files.

### Security Posture Assessment

This change **improves** the security posture:

- **Reduces attack surface**: Moves from prompt-chained orchestration (where the LLM holds the program counter and all state in volatile context) to deterministic Python code with persisted state. The control plane is now in compiled/interpreted code rather than free-form LLM instructions, reducing the risk of prompt injection affecting orchestration decisions.
- **Adds explicit boundary**: The CLI interface creates a clear trust boundary between the LLM and the orchestrator. Arguments are parsed via `argparse`, results are validated via `json.loads()`, and only expected keys are consumed.
- **Maintains audit trail**: The existing append-only JSONL audit log is preserved and extended with new event types.
- **No new secrets or sensitive data**: The change operates entirely on operational metadata (phase numbers, issue references, signal counts).
- **Proper subprocess handling**: The single subprocess call uses list-based arguments with timeout and exception handling.

The low-severity findings are defense-in-depth improvements, not exploitable vulnerabilities. None block merge.

---

## Scoring

| Finding | Severity | Impact |
|---------|----------|--------|
| SA-1: JSON injection via --result | Low | -0.01 |
| IE-2: Non-atomic file write | Low | -0.01 |
| AR-1: Session ID path construction | Low | -0.01 |
| AR-3: Broad exception swallowing | Low | -0.01 |

**Confidence:** `max(0.0, 0.90 - (0 * 0.30) - (0 * 0.20) - (0 * 0.05) - (4 * 0.01))` = **0.86**

**Pass/Fail:**
- Confidence score: 0.86 >= 0.75 -- PASS
- Critical findings: 0 -- PASS
- High findings: 0 -- PASS
- Compliance score: 0.95 >= 0.85 -- PASS
- Aggregate verdict: approve -- PASS

---

<!-- STRUCTURED_EMISSION_START -->
```json
{
  "panel_name": "security-review",
  "panel_version": "1.0.0",
  "confidence_score": 0.86,
  "risk_level": "low",
  "compliance_score": 0.95,
  "policy_flags": [],
  "requires_human_review": false,
  "timestamp": "2026-03-02T12:00:00Z",
  "findings": [
    {
      "persona": "compliance/security-auditor",
      "verdict": "approve",
      "confidence": 0.90,
      "rationale": "No injection vectors exploitable in practice. JSON input parsed via json.loads() with only expected keys consumed by _absorb_result(). No secrets or credentials exposed. Error messages contain only debug-level JSON parse error details.",
      "findings_count": {"critical": 0, "high": 0, "medium": 0, "low": 1, "info": 2}
    },
    {
      "persona": "operations/infrastructure-engineer",
      "verdict": "approve",
      "confidence": 0.88,
      "rationale": "File permissions use platform defaults appropriate for non-sensitive orchestrator metadata. Session directory auto-creation is correctly scoped. Non-atomic file writes are a robustness concern but not a security vulnerability in the local CLI context.",
      "findings_count": {"critical": 0, "high": 0, "medium": 0, "low": 1, "info": 1}
    },
    {
      "persona": "compliance/compliance-officer",
      "verdict": "approve",
      "confidence": 0.95,
      "rationale": "No PII, PHI, or regulated data introduced. Audit trail preserved and extended with new event types (session_init, session_restored, session_done). No cross-border data transfer implications. Compliant with SOC2 change management requirements.",
      "findings_count": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 2}
    },
    {
      "persona": "quality/adversarial-reviewer",
      "verdict": "approve",
      "confidence": 0.87,
      "rationale": "Session ID sanitization replaces / and space, preventing directory traversal via ../. Idempotent double-complete is correct. Broad exception swallowing in circuit breaker restoration is a debuggability concern. No exploitable state corruption paths identified.",
      "findings_count": {"critical": 0, "high": 0, "medium": 0, "low": 2, "info": 1}
    },
    {
      "persona": "domain/backend-engineer",
      "verdict": "approve",
      "confidence": 0.92,
      "rationale": "Subprocess call uses list-based arguments (no shell=True) with timeout. Shell script variables are properly quoted. JSON deserialization filters to known dataclass fields only. No command injection, deserialization, or path traversal vectors.",
      "findings_count": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 3}
    }
  ],
  "aggregate_verdict": "approve",
  "data_classification": {
    "level": "internal",
    "contains_sensitive_evidence": false,
    "redaction_applied": false
  },
  "execution_trace": {
    "files_read": [
      "governance/engine/orchestrator/__main__.py",
      "governance/engine/orchestrator/session.py",
      "governance/engine/orchestrator/step_runner.py",
      "governance/engine/orchestrator/step_result.py",
      "governance/engine/orchestrator/claude_code_dispatcher.py",
      "governance/engine/orchestrator/config.py",
      "governance/engine/orchestrator/state_machine.py",
      "governance/engine/orchestrator/__init__.py",
      "bin/auto-clear.sh",
      "governance/engine/tests/test_cli.py",
      "governance/engine/tests/test_session.py",
      "governance/engine/tests/test_step_runner.py",
      "governance/engine/tests/test_step_result.py",
      "governance/engine/tests/test_claude_code_dispatcher.py",
      "governance/engine/tests/test_state_machine.py",
      "governance/prompts/startup.md",
      "governance/prompts/startup-legacy.md",
      "project.yaml",
      "CLAUDE.md",
      "README.md",
      "docs/architecture/orchestrator.md",
      "docs/architecture/context-management.md",
      "docs/configuration/slash-commands.md",
      "docs/onboarding/developer-guide.md"
    ],
    "diff_lines_analyzed": 5417,
    "grounding_references": [
      {"file": "governance/engine/orchestrator/__main__.py", "line": 96, "finding_id": "SA-1"},
      {"file": "governance/engine/orchestrator/session.py", "line": 97, "finding_id": "AR-1"},
      {"file": "governance/engine/orchestrator/session.py", "line": 93, "finding_id": "IE-1"},
      {"file": "governance/engine/orchestrator/session.py", "line": 1004, "finding_id": "IE-2"},
      {"file": "governance/engine/orchestrator/step_runner.py", "line": 1496, "finding_id": "AR-3"},
      {"file": "governance/engine/orchestrator/step_runner.py", "line": 1855, "finding_id": "BE-1"},
      {"file": "bin/auto-clear.sh", "line": 89, "finding_id": "BE-2"},
      {"file": "governance/engine/orchestrator/session.py", "line": 1013, "finding_id": "BE-3"}
    ]
  },
  "schema_version": "1.2.0",
  "execution_context": {
    "repository": "SET-Apps/ai-submodule",
    "branch": "feat/retire-prompt-chaining",
    "pr_number": 587,
    "model_id": "claude-opus-4-6",
    "provider": "anthropic",
    "triggered_by": "manual"
  }
}
```
<!-- STRUCTURED_EMISSION_END -->
