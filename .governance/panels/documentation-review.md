# Documentation Review: PR #587 — feat: retire prompt chaining

**Panel:** documentation-review v1.0.0
**PR:** #587 (`feat/retire-prompt-chaining` -> `main`)
**Repository:** SET-Apps/ai-submodule
**Date:** 2026-03-02

---

## Scope

PR #587 replaces ~1,200 lines of prompt-chained startup logic (`startup.md`) with a Python orchestrator CLI (`python -m governance.engine.orchestrator`) as the sole control plane. The PR touches 25 files, including 7 documentation files:

- `CLAUDE.md` — Added orchestrator CLI commands, session state directory, orchestrator introduction
- `README.md` — Updated pipeline description and context management references
- `docs/architecture/orchestrator.md` — Rewritten to reflect CLI step-function architecture
- `docs/architecture/context-management.md` — Replaced inline shell loop with auto-clear.sh reference
- `docs/configuration/slash-commands.md` — Updated `/startup` documentation to orchestrator-driven model
- `docs/onboarding/developer-guide.md` — Replaced prompt-chain pipeline diagram and description
- `governance/prompts/startup.md` — Rewritten from ~1,200 lines to ~130 lines of orchestrator protocol

---

## Per-Participant Findings

### Documentation Reviewer

**Gaps Identified:**

1. **MEDIUM — Module line counts are inaccurate in `orchestrator.md`.** The modules table reports `state_machine.py` as `~100` lines; the actual file is 248 lines. `step_runner.py` is documented as `~350` lines but is actually 672 lines. `__main__.py` is documented as `~170` lines and is actually 181 (close enough). `session.py` is documented as `~90` and is actually 114. `claude_code_dispatcher.py` is documented as `~90` and is actually 122. The `~` prefix suggests approximation, but the `state_machine.py` and `step_runner.py` figures are off by 2x. Users reading the modules table for architectural sizing will get a misleading impression.

2. **HIGH — ASCII art / box-drawing diagrams in `orchestrator.md`.** The architecture diagram at `docs/architecture/orchestrator.md` lines 14-32 uses box-drawing characters (lines with `+`, `-`, `|` Unicode box characters). Per the documentation review panel prompt, all diagrams must use mermaid code blocks. ASCII art and box-drawing characters are blocking findings. The same box-drawing style also appears in the "Step-Based Loop" section (lines 104-119) and the "Phase Loop" section (lines 123-145) using tree-drawing characters. The Phase Loop section uses a tree-like format (indented with special characters) which is exempt as a directory-tree-style listing, but the architecture box diagram is not exempt.

3. **LOW — Test count "964+" is vague.** The testing section in `orchestrator.md` states "964+ tests across 11 test files" but the actual count is exactly 964. The `+` suffix implies there are more, which is misleading.

**Usability Issues:**

4. **LOW — `--prompt` flag undocumented in docs.** `bin/auto-clear.sh` supports a `--prompt` flag (documented in the script's header comment), but none of the documentation pages (`CLAUDE.md`, `context-management.md`, `orchestrator.md`, `slash-commands.md`) mention this option. Only `--max-retries` is shown in examples.

5. **INFO — `auto-clear.sh` uses `python` in one line and `python3` in another.** Line 54 uses `python -m governance.engine.orchestrator status` while line 55 uses `python3 -c ...`. This inconsistency could cause failures on systems where `python` is not aliased to `python3`.

**Accuracy Issues:**

6. **MEDIUM — `runner.py` description changed but file not modified.** The modules table in `orchestrator.md` changes `runner.py`'s description from "Entry point -- Phase 0-5 loop" to "Legacy single-pass runner (preserved for backward compatibility)" but `runner.py` itself was not modified in this PR. This is a documentation change that should be verified against actual code behavior.

---

### Documentation Writer

**Gaps Identified:**

1. **LOW — Startup.md lost significant operational detail.** The old `startup.md` contained detailed instructions for issue body validation (malformed input defense, size checks, untrusted content handling), submodule update procedures, repository configuration checks, and platform-specific handoff instructions. The new ~130-line version delegates all this to the orchestrator but does not explain where this logic now lives. A developer reading `startup.md` for operational understanding will not find the filtering criteria, validation rules, or edge-case handling that previously existed. While the orchestrator owns the control flow, the LLM still performs the creative work of each phase -- and needs to know the rules.

2. **LOW — No migration guide for teams on the old prompt-chain model.** The PR archives the old startup.md as `startup-legacy.md` and rewrites the active one, but no documentation explains the transition: what changed, how to verify the new model works, or what to do if rollback is needed. The backward compatibility section was removed from `orchestrator.md`.

3. **INFO — `developer-guide.md` mermaid diagram is a significant improvement.** The old diagram had 20+ nodes with complex branching; the new diagram has 8 nodes with clear flow. This is a substantial readability gain.

**Cross-Reference Issues:**

4. **LOW — CLAUDE.md still references "See `governance/prompts/startup.md`" without noting the rewrite.** The "Agentic Startup" section points to startup.md but does not indicate the file was fundamentally rewritten from a prompt chain to an orchestrator protocol. Readers following the reference will find a very different document than what the CLAUDE.md description implies.

---

### API Consumer

**Gaps Identified:**

1. **LOW — CLI error responses not fully documented.** The `__main__.py` CLI returns JSON error objects (`{"error": "..."}`) on failures, and exit code 2 on shutdown. This contract is mentioned briefly ("All output is JSON to stdout. Exit code 2 on shutdown.") but the error response schema and exit code 1 for errors are not explicitly documented in `orchestrator.md`.

2. **INFO — `StepResult` action values well-documented.** The `step_result.py` docstring thoroughly enumerates all action values (`execute_phase`, `dispatch`, `collect`, `merge`, `loop`, `shutdown`, `done`). This matches the documentation in `startup.md` and `slash-commands.md`.

**Usability Issues:**

3. **INFO — `--session-id` flag behavior is consistent.** All subcommands accept `--session-id` with auto-resolution for non-init commands. This is documented implicitly via the CLI help text but not explicitly in the docs.

---

### Mentor

**Gaps Identified:**

1. **LOW — No conceptual explanation of why prompt chaining was retired.** The PR title and description explain the what, but the documentation does not explain the why. Why is a CLI step function better than a prompt chain? What problems did prompt chaining cause? This context would help developers understand the architectural decision and avoid recreating the anti-pattern.

2. **INFO — The step-based loop diagram in `orchestrator.md` is an excellent teaching tool.** The `LLM: [command] -> {response}` format clearly shows the request-response pattern and is immediately understandable.

---

### UX Engineer

**Gaps Identified:**

1. **LOW — `auto-clear.sh` completion detection relies on `python` being available.** On line 54 of the script, `python -m governance.engine.orchestrator status` is used, but the PR also lowered the Python requirement from 3.12 to 3.9. On some systems, `python` may not exist (only `python3`). The script mixes `python` and `python3` invocations. This is a functional issue more than a docs issue, but the documentation should note the Python requirement.

2. **INFO — CLI subcommand design follows standard patterns.** The `init`, `step`, `signal`, `gate`, `status` subcommands are intuitive and well-named. The `--config` default to `project.yaml` is sensible.

---

### GitHub Pages Requirement

- No GitHub Pages deployment workflow was found in `.github/workflows/`.
- No documentation site URL was found in `README.md`.
- No MkDocs or static site generator configuration was found.
- **Advisory (medium severity):** The project would benefit from a documentation site deployed via GitHub Pages at `https://SET-Apps.github.io/ai-submodule`. This is not a blocking finding.

---

## Consolidated Findings

### Critical Missing Documentation (Blocking User Tasks)

None. All documentation files are updated to reflect the new orchestrator-driven model. The CLI protocol is documented in multiple locations with consistent examples.

### Accuracy Issues Requiring Immediate Fix

1. **HIGH — ASCII art / box-drawing architecture diagram in `orchestrator.md` (lines 14-32).** Must be converted to a mermaid code block per documentation standards. Box-drawing characters are not acceptable.

2. **MEDIUM — Module line counts in `orchestrator.md` are significantly inaccurate.** `state_machine.py` is 248 lines (documented as ~100), `step_runner.py` is 672 lines (documented as ~350). These should be corrected.

### Structure Improvements

3. **LOW — Document the `--prompt` flag for `auto-clear.sh`** in at least one documentation page (suggest `orchestrator.md` or `context-management.md`).

4. **LOW — Add a brief note in startup.md Phase Details explaining where validation/filtering logic lives** now that the detailed instructions have been removed (or reference the legacy file).

### Example Additions Needed

5. **LOW — Document CLI error response format and exit codes** explicitly in `orchestrator.md` (exit 0 = success, exit 1 = error, exit 2 = shutdown).

### Maintenance Recommendations

6. **INFO — Module line counts will drift.** Consider removing exact line counts from the modules table or generating them automatically. The `~` approximation is insufficient when modules differ by 2x from the documented value.

7. **INFO — `auto-clear.sh` should use consistent Python invocation** (`python3` throughout, or document the requirement for `python` to be available).

---

## Verdict

The documentation changes are comprehensive and well-structured. The orchestrator CLI is consistently documented across 7 files, the mermaid diagram in `developer-guide.md` is a clear improvement, and the startup.md rewrite correctly simplifies the LLM's operational instructions. The primary blocking finding is the ASCII art architecture diagram in `orchestrator.md` which must be converted to mermaid format. The inaccurate module line counts are a medium-severity accuracy issue. All other findings are low severity or informational.

**Aggregate Verdict: request_changes** (due to the box-drawing diagram in `orchestrator.md`)

---

<!-- STRUCTURED_EMISSION_START -->
```json
{
  "panel_name": "documentation-review",
  "panel_version": "1.0.0",
  "confidence_score": 0.66,
  "risk_level": "low",
  "compliance_score": 0.75,
  "policy_flags": [
    {
      "flag": "non_mermaid_diagram",
      "severity": "high",
      "description": "Architecture diagram in docs/architecture/orchestrator.md (lines 14-32) uses ASCII box-drawing characters instead of mermaid. Documentation standards require all diagrams to use mermaid code blocks.",
      "remediation": "Convert the ASCII architecture diagram to a mermaid block diagram or flowchart.",
      "auto_remediable": true
    },
    {
      "flag": "inaccurate_line_counts",
      "severity": "medium",
      "description": "Module line counts in docs/architecture/orchestrator.md are significantly inaccurate: state_machine.py documented as ~100 (actual 248), step_runner.py documented as ~350 (actual 672).",
      "remediation": "Update the line counts in the modules table to reflect actual file sizes, or remove exact counts.",
      "auto_remediable": true
    },
    {
      "flag": "undocumented_cli_flag",
      "severity": "low",
      "description": "The --prompt flag for bin/auto-clear.sh is supported by the script but not mentioned in any documentation page.",
      "remediation": "Add --prompt flag documentation to at least one docs page (orchestrator.md or context-management.md).",
      "auto_remediable": true
    },
    {
      "flag": "inconsistent_python_invocation",
      "severity": "low",
      "description": "bin/auto-clear.sh uses 'python' on line 54 and 'python3' on line 55, which may fail on systems where 'python' is not available.",
      "remediation": "Use 'python3' consistently throughout the script, or add a PYTHON variable that resolves the correct interpreter.",
      "auto_remediable": true
    }
  ],
  "requires_human_review": false,
  "timestamp": "2026-03-02T15:30:00Z",
  "findings": [
    {
      "persona": "documentation/documentation-reviewer",
      "verdict": "request_changes",
      "confidence": 0.78,
      "rationale": "Architecture diagram in orchestrator.md uses ASCII box-drawing characters instead of mermaid — this is a blocking finding per documentation standards. Module line counts in the same file are inaccurate by 2x for two modules. Test count uses misleading '964+' notation. The --prompt flag for auto-clear.sh is undocumented in all docs pages.",
      "findings_count": {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 2,
        "info": 1
      }
    },
    {
      "persona": "documentation/documentation-writer",
      "verdict": "approve",
      "confidence": 0.72,
      "rationale": "Documentation accurately reflects the new orchestrator-driven model across all 7 files. The startup.md rewrite is clean and focused. Cross-references are consistent. However, significant operational detail from the old startup.md (validation rules, filtering criteria, platform-specific handoffs) was removed without documenting where this logic now lives. No migration guide exists for the prompt-chain to orchestrator transition.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 4,
        "info": 1
      }
    },
    {
      "persona": "specialist/api-consumer",
      "verdict": "approve",
      "confidence": 0.80,
      "rationale": "CLI protocol is well-documented with consistent examples across multiple files. StepResult action values are thoroughly enumerated. Exit code semantics and JSON output format are mentioned but could be more explicit. --session-id auto-resolution behavior is correct but undocumented.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 1,
        "info": 2
      }
    },
    {
      "persona": "leadership/mentor",
      "verdict": "approve",
      "confidence": 0.75,
      "rationale": "The step-based loop diagram is an excellent teaching tool. The request-response pattern is immediately understandable. However, no conceptual explanation exists for why prompt chaining was retired — the 'why' behind the architecture change is missing from documentation.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 1,
        "info": 1
      }
    },
    {
      "persona": "engineering/ux-engineer",
      "verdict": "approve",
      "confidence": 0.82,
      "rationale": "CLI subcommand design follows standard patterns with intuitive naming. Configuration defaults are sensible (project.yaml, auto session-id). Auto-clear wrapper is well-designed with backoff and retry cap. Minor issue with mixed python/python3 invocations in the script.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 1,
        "info": 1
      }
    }
  ],
  "aggregate_verdict": "request_changes",
  "execution_context": {
    "repository": "SET-Apps/ai-submodule",
    "branch": "feat/retire-prompt-chaining",
    "commit_sha": "f3c7d18",
    "pr_number": 587,
    "policy_profile": "default",
    "triggered_by": "manual"
  }
}
```
<!-- STRUCTURED_EMISSION_END -->
