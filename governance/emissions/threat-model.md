# Threat Model — PR #217: Move Language Templates to governance/templates/

**Panel:** threat-modeling v1.0.0
**Date:** 2026-02-24
**Policy Profile:** default
**Repository:** SET-Apps/ai-submodule
**PR:** #217
**Triggered by:** manual

---

## 1. System Scope and Trust Boundaries

**Change description:** Moved root-level `templates/` directory (14 language scaffolding files: bicep, csharp, go, node, python, react, terraform + GOALS.md + project.yaml) to `governance/templates/`. Updated path references in 11 files.

**Trust boundaries:**

```mermaid
graph TD
    subgraph REPO["ai-submodule repository (governance repo)"]
        subgraph GOV["governance/"]
            T["templates/ (NEW) — Language files"]
            PR["prompts/ — Cognitive files"]
            PO["policy/ — Enforcement"]
            S["schemas/ — Enforcement"]
        end
        INIT["init.sh / init.ps1\n(bootstrap scripts)"]
        INIT -->|"copies GOALS.md template\nprints help text with paths"| TB["TRUST BOUNDARY:\nsubmodule <-> consuming repo"]
    end
    TB -->|"git submodule update"| CONSUMING
    subgraph CONSUMING["Consuming repository"]
        AI[".ai/ (pinned submodule)"]
        PY["project.yaml (copied from template)"]
        GM["GOALS.md (copied from template)"]
    end
```

**Data flows affected:**
1. `init.sh` → reads `governance/templates/GOALS.md` → copies to consuming repo root (unchanged logic, new source path)
2. User manually runs `cp .ai/governance/templates/{lang}/project.yaml project.yaml` (documentation-guided, not automated)

---

## 2. MITRE Specialist — ATT&CK Mapping

### Attack Surface Analysis

This change modifies **zero executable logic**. All changes are path string updates in configuration files, documentation, and shell script help text. The `init.sh` GOALS template copy operation (`cp "$GOALS_TEMPLATE" "$GOALS_DST"`) uses the same `$SCRIPT_DIR`-relative pattern — only the subdirectory depth changed.

### Threat Enumeration

| ID | Threat | ATT&CK Technique | Likelihood | Impact | Risk |
|----|--------|-------------------|------------|--------|------|
| T1 | Path traversal via init.sh template path | [T1059.004](https://attack.mitre.org/techniques/T1059/004/) — Unix Shell | Very Low | Low | **Negligible** |
| T2 | Supply chain: stale paths in consuming repo scripts/history | [T1195.002](https://attack.mitre.org/techniques/T1195/002/) — Compromise Software Supply Chain | Low | Low | **Low** |
| T3 | Confusion between governance/templates/ and governance/prompts/templates/ | N/A (operational risk) | Low | Negligible | **Negligible** |

### T1 — Path Traversal Analysis

**Attack vector:** An attacker modifies `$SCRIPT_DIR` or the hardcoded path to cause `init.sh` to copy from an unintended location.

**Assessment:** Not viable.
- `SCRIPT_DIR` is computed via `$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)` — this resolves to the absolute path of the script's own directory. It cannot be influenced by user input.
- `GOALS_TEMPLATE` is `"$SCRIPT_DIR/governance/templates/GOALS.md"` — a hardcoded relative path concatenated with an absolute base. No dynamic components.
- The `cp` command copies a single file to a known destination. No glob expansion, no symlink following beyond OS defaults.

**Detection:** N/A — no attack path exists.

### T2 — Supply Chain Stale Path Analysis

**Attack vector:** A consuming repo has `cp .ai/templates/python/project.yaml project.yaml` in a CI script, Makefile, or developer documentation. After updating the submodule, this command fails silently or produces unexpected results.

**Assessment:** Low risk.
- `cp` of a nonexistent source file fails with exit code 1 and a clear error message — it does not fail silently.
- Consuming repos pin to a submodule SHA. The path change only affects repos that deliberately update.
- All documentation (README, DEVELOPER_GUIDE, init.md) was updated atomically with the path change.
- `init.sh` handles the GOALS.md copy internally — consuming repos do not need to reference that path directly.

**Detection:** Standard CI failure on missing file. No additional detection needed.

### T3 — Naming Collision Analysis

**Attack vector:** Developer or automated tooling confuses `governance/templates/` (language scaffolding) with `governance/prompts/templates/` (cognitive prompt templates).

**Assessment:** Negligible.
- The two directories serve clearly distinct purposes documented in multiple locations.
- `governance/templates/` contains `project.yaml` and `instructions.md` per language.
- `governance/prompts/templates/` contains `plan-template.md`, `runtime-di-template.md`, `weekly-report-template.md`.
- No tooling traverses both directories in the same operation.

**Detection:** Code review — any reference to the wrong templates directory would be caught by the governance panel.

### Kill Chain Analysis

No complete kill chain can be constructed from this change. The change:
- Introduces no new network operations
- Introduces no new authentication or authorization logic
- Introduces no dynamic path resolution or user input handling
- Does not modify any policy evaluation logic
- Does not modify any schema validation logic

### Detection Gap Matrix

| ATT&CK Technique | Prevention | Detection | Gap |
|-------------------|------------|-----------|-----|
| T1059.004 (Unix Shell) | Hardcoded paths; no user input | N/A | None |
| T1195.002 (Supply Chain) | Submodule pinning; atomic doc updates | CI failure on missing file | None |

---

## 3. Security Auditor — Vulnerability Assessment

### OWASP / CWE Checklist

| Check | CWE | Result | Evidence |
|-------|-----|--------|----------|
| Command injection | CWE-78 | **Clean** | `init.sh:299` — `GOALS_TEMPLATE` is hardcoded, not user-derived |
| Path traversal | CWE-22 | **Clean** | All paths are `$SCRIPT_DIR` + hardcoded relative path |
| Secret exposure | CWE-798 | **Clean** | No secrets in any changed file. Templates contain only coding conventions (linter configs, test runner settings) |
| Sensitive data in templates | CWE-200 | **Clean** | Template `project.yaml` files contain project names like "my-app" and tooling preferences — no PII, credentials, or internal URLs |
| Insecure file permissions | CWE-732 | **Clean** | `git mv` preserves original file permissions. No `chmod` or permission changes. |
| Symlink exploitation | CWE-59 | **Clean** | No symlinks created or modified by this change |

### init.sh Specific Review

```bash
# Line 299 (after change):
GOALS_TEMPLATE="$SCRIPT_DIR/governance/templates/GOALS.md"
```

- `$SCRIPT_DIR` — set via `$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)` at line 13. Resolves to absolute path. Safe.
- Path concatenation uses no variable interpolation from external sources.
- Destination `$GOALS_DST` is `"$PROJECT_ROOT/GOALS.md"` — also computed from script location. Safe.
- The `cp` at line 305 copies a single file. No wildcards. No `-r` flag.

### init.ps1 Specific Review

```powershell
# Line 627 (after change):
Write-Host "  1. Copy a language template:  Copy-Item .ai\governance\templates\python\project.yaml project.yaml"
```

- This is a `Write-Host` string literal — it prints help text, does not execute the command. No execution risk.

### Findings

**Critical:** 0
**High:** 0
**Medium:** 0
**Low:** 0
**Info:** 0

---

## 4. Infrastructure Engineer — Deployment Impact

| Dimension | Assessment |
|-----------|------------|
| **IAM / Permissions** | No changes. No new permissions required to read from `governance/templates/` vs `templates/`. Both are within the same git repository. |
| **Network boundaries** | No network operations added or modified. |
| **Encryption** | N/A — no encrypted data or TLS endpoints involved. |
| **CI pipeline** | Governance workflow (`dark-factory-governance.yml`) passed on both push cycles. No new CI steps required. The workflow detects governance root dynamically and is path-agnostic for template files. |
| **Rollback safety** | Safe. `git revert` of the squash merge commit restores all 14 files to `templates/` and reverts all 11 reference updates atomically. |
| **Consuming repo impact** | `init.sh` GOALS template copy path updated. Consuming repos running `bash .ai/init.sh` after submodule update will use the new path automatically — no manual intervention needed for the automated path. Only manual `cp` commands from developer documentation need updating (handled by doc changes in this PR). |

### Findings

**Critical:** 0
**High:** 0
**Medium:** 0
**Low:** 0

---

## 5. Adversarial Reviewer — Stress Testing

### Hidden Assumptions

| Assumption | Valid? | Risk if Violated |
|------------|--------|------------------|
| `$SCRIPT_DIR` always resolves to the .ai submodule directory | Yes — `BASH_SOURCE[0]` points to init.sh, `dirname` + `pwd` gives its directory | If somehow incorrect, GOALS template copy fails with clear error |
| Consuming repos don't have automation referencing old `templates/` path | Mostly — some may have cached CI scripts or Makefiles | `cp` fails with exit code 1, not silent. Low impact. |
| `git mv` preserves file content and git history | Yes — standard git operation | No risk |
| Collision domains YAML is consumed by the parallelization orchestrator | Yes, but orchestrator is Phase 5d (not yet runtime) | Zero current impact. Future orchestrator will read the updated path. |

### Edge Cases Tested

1. **What if `governance/templates/` already exists?** — It did not. `governance/prompts/templates/` exists but is a different path. `git mv` would fail if the target existed — it succeeded, confirming no collision.

2. **What if init.sh runs inside the ai-submodule repo itself (not a consuming repo)?** — The GOALS template copy is guarded by `if [ "$IS_SUBMODULE" = "true" ]` (line 202). When running inside the submodule repo directly, this block is skipped entirely. No path dependency.

3. **What if a consuming repo has both old and new submodule versions?** — Not possible. A repo pins to a single submodule SHA. On update, all paths change atomically.

4. **What about the `project.yaml` template under `governance/templates/`?** — This is the generic project configuration template. It is never referenced by init.sh directly — only used when developers manually copy it per documentation instructions.

### Logical Consistency Check

- README directory listing shows `templates/` nested under `governance/` — **consistent** with the move.
- `collision-domains.yaml` shows `governance/templates/**` — **consistent** with the move.
- `artifact-classification.md` shows `governance/templates/` — **consistent**.
- `context-management.md` shows `governance/templates/{language}/instructions.md` — **consistent**.
- All 11 modified files reference the new path — **verified via post-change grep**.

### Findings

| Severity | Count | Description |
|----------|-------|-------------|
| Low | 1 | Consuming repos with cached manual `cp .ai/templates/...` commands will need to update after submodule update. Mitigated by documentation and `cp` failure being non-silent. |
| Negligible | 1 | Two directories named `templates` exist at different paths. Well-documented, no functional overlap. |

---

## 6. Architect — Structural Assessment

### Before

```
.ai/
├── templates/          ← language scaffolding (developer-facing)
├── governance/
│   ├── prompts/
│   │   └── templates/  ← cognitive templates (AI-facing)
│   ├── personas/
│   ├── policy/
│   └── schemas/
```

The `templates/` directory was an exception to the PR #46 consolidation that moved all other top-level directories under `governance/`.

### After

```
.ai/
├── governance/
│   ├── templates/      ← language scaffolding (developer-facing)
│   ├── prompts/
│   │   └── templates/  ← cognitive templates (AI-facing)
│   ├── personas/
│   ├── policy/
│   └── schemas/
```

All governance machinery now lives under `governance/`. The root contains only bootstrap files (`init.sh`, `init.ps1`, `instructions.md`, `config.yaml`).

### Structural Verdict

The change **improves architectural consistency** by eliminating the last top-level exception. The separation between `governance/templates/` (language conventions) and `governance/prompts/templates/` (prompt templates) is clear and well-documented. No new coupling introduced.

---

## 7. Consolidated Summary

### Threat Model Verdict: **APPROVE**

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Confidence score | 0.89 | >= 0.75 | **Pass** |
| Critical findings | 0 | 0 allowed | **Pass** |
| High findings | 0 | 0 allowed | **Pass** |
| Compliance score | 0.95 | >= 0.85 | **Pass** |
| Aggregate verdict | approve | approve | **Pass** |

### Finding Summary

| Severity | Count | Description |
|----------|-------|-------------|
| Critical | 0 | — |
| High | 0 | — |
| Medium | 0 | — |
| Low | 1 | Consuming repos may have cached `cp .ai/templates/...` commands. Fails non-silently. |
| Negligible | 2 | Path traversal not viable (hardcoded paths); naming collision well-documented. |

### Mitigation Roadmap

No mitigations required. All identified concerns are addressed by existing mechanisms:
- Submodule pinning prevents unintended path changes
- `cp` failure is non-silent (exit code 1)
- Documentation updated atomically with the path change

### Residual Risk

**Low.** The only material risk is consuming repo developer workflows referencing the old path. This is a one-time transition cost absorbed at the next submodule update.

---

<!-- STRUCTURED_EMISSION_START -->
```json
{
  "panel_name": "threat-modeling",
  "panel_version": "1.0.0",
  "confidence_score": 0.89,
  "risk_level": "low",
  "compliance_score": 0.95,
  "policy_flags": [],
  "requires_human_review": false,
  "timestamp": "2026-02-24T21:40:00Z",
  "findings": [
    {
      "persona": "compliance/mitre-specialist",
      "verdict": "approve",
      "confidence": 0.92,
      "rationale": "No viable attack surface. All path changes are hardcoded constants with no user input. No kill chain exists for this change. Three threats enumerated (path traversal, supply chain stale paths, naming collision) — all negligible to low.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 1,
        "info": 0
      }
    },
    {
      "persona": "compliance/security-auditor",
      "verdict": "approve",
      "confidence": 0.90,
      "rationale": "Zero security findings across OWASP/CWE checklist. No secrets, injection vectors, permission changes, or symlink exploitation. init.sh path construction uses hardcoded $SCRIPT_DIR-relative paths.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0
      }
    },
    {
      "persona": "operations/infrastructure-engineer",
      "verdict": "approve",
      "confidence": 0.90,
      "rationale": "No infrastructure impact. No IAM, network, or encryption changes. CI pipeline passed on both push cycles. Rollback is safe via git revert.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0
      }
    },
    {
      "persona": "quality/adversarial-reviewer",
      "verdict": "approve",
      "confidence": 0.85,
      "rationale": "Consuming repo path breakage is the only material concern (low severity). Mitigated by submodule pinning, non-silent cp failure, and atomic documentation updates. Four edge cases tested — all safe. Two hidden assumptions validated.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 1,
        "info": 1
      }
    },
    {
      "persona": "architecture/architect",
      "verdict": "approve",
      "confidence": 0.90,
      "rationale": "Change improves architectural consistency by eliminating the last top-level directory exception from PR #46 consolidation. No new trust boundaries, coupling, or data flow changes introduced.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0
      }
    }
  ],
  "aggregate_verdict": "approve",
  "execution_context": {
    "repository": "SET-Apps/ai-submodule",
    "pr_number": 217,
    "policy_profile": "default",
    "model_version": "claude-opus-4-6",
    "triggered_by": "manual"
  }
}
```
<!-- STRUCTURED_EMISSION_END -->
