# Cross-Repo Issue Escalation for Consuming Repos

**Author:** Team Lead (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/184
**Branch:** NETWORK_ID/feat/184/cross-repo-escalation

---

## 1. Objective

Enable consuming repositories to automatically detect and escalate framework-level issues to the Dark Forge repository (`convergent-systems-co/dark-forge`), with duplicate prevention and configurable criteria.

## 2. Rationale

Currently, when a consuming repo's agent encounters a governance framework issue (e.g., schema validation failure, policy gap, workflow bug), the issue is logged locally but never escalated upstream. This means framework bugs go undetected until they affect multiple repos independently. A structured escalation mechanism routes framework-level issues to the submodule maintainers, closing the feedback loop between consuming repos and the governance platform.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Manual escalation only | Yes | Defeats the purpose of autonomous governance; agents can't create upstream issues |
| GitHub Actions bot with cross-repo PAT | Yes | Requires PAT management; selected as the recommended auth approach (simplest, documented in GitHub docs) |
| GitHub App installation | Yes | Higher setup complexity; overkill for issue creation; listed as alternative for orgs with stricter token policies |
| Webhook-based escalation | Yes | Requires webhook infrastructure; the governance framework is config-only |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/cross-repo-escalation.schema.json` | JSON Schema for escalation records — tracks what was escalated, from where, dedup key, and resolution |
| `governance/prompts/cross-repo-escalation-workflow.md` | Agentic workflow prompt defining the detection → evaluate → escalate → track flow |
| `governance/docs/cross-repo-escalation.md` | Setup guide for consuming repos: authentication, configuration, and usage |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/project.schema.json` | Add `escalation` configuration section for consuming repos to enable/disable and customize criteria |
| `governance/policy/default.yaml` | Add escalation trigger rules for framework-level issue detection |
| `config.yaml` | Add default escalation configuration (disabled by default) |
| `GOALS.md` | Add completed work entry for this issue |
| `CLAUDE.md` | Update schema count (18 → 19) |
| `governance/docs/dark-factory-governance-model.md` | Add cross-repo escalation to architecture overview if referenced |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

### Step 1: Create the Escalation Schema

Define `governance/schemas/cross-repo-escalation.schema.json` with:
- `escalation_id` — unique identifier
- `source_repository` — consuming repo in `owner/repo` format
- `source_issue_number` — the local issue that triggered escalation
- `target_repository` — always `convergent-systems-co/dark-forge` (configurable)
- `detection_criteria` — which criteria matched (path-based, workflow failure, policy gap, schema validation)
- `dedup_key` — hash of (criteria_type + criteria_detail) for duplicate prevention
- `severity` — critical/high/medium/low
- `description` — what the consuming repo's agent detected
- `upstream_issue_number` — populated after escalation succeeds
- `status` — detected/escalated/duplicate/resolved
- `timestamp` — ISO 8601

### Step 2: Define Detection Criteria

In the escalation workflow, define what makes an issue framework-level vs. project-local:

**Framework-level signals (escalate):**
1. **Path-based** — Issue involves files under `.ai/governance/` (schemas, policies, personas, panels, prompts)
2. **Workflow failure** — `dark-factory-governance.yml` fails with errors in governance framework code (not project code)
3. **Policy gap** — Agent encounters a scenario not covered by any policy rule
4. **Schema validation** — Panel emission or manifest fails schema validation against a governance schema
5. **Init failure** — `init.sh` fails during bootstrap

**Project-local signals (do not escalate):**
1. Issue involves only project source code (not `.ai/` paths)
2. CI failure in project tests (not governance workflow)
3. Copilot recommendations on project code

### Step 3: Create the Escalation Workflow Prompt

Define `governance/prompts/cross-repo-escalation-workflow.md` with the flow:

1. **Detect** — Agent identifies a framework-level issue during normal operation
2. **Classify** — Apply detection criteria to confirm it's framework-level
3. **Dedup check** — Compute dedup_key, search upstream repo for existing open issues with matching key:
   ```bash
   gh search issues --repo convergent-systems-co/dark-forge "dedup:{dedup_key}" --state open
   ```
   The dedup_key is embedded in the upstream issue body as a machine-readable marker.
4. **Create upstream issue** — If no duplicate found:
   ```bash
   gh issue create --repo convergent-systems-co/dark-forge \
     --title "escalation({source_repo}): {summary}" \
     --body "{structured body with dedup marker}" \
     --label "escalation"
   ```
5. **Link back** — Comment on the local issue with the upstream issue reference
6. **Record** — Write an escalation record conforming to the schema

### Step 4: Add Configuration to project.schema.json and config.yaml

Extend `project.schema.json` with an `escalation` section:
```yaml
escalation:
  enabled: false  # opt-in
  target_repository: "convergent-systems-co/dark-forge"
  criteria:
    path_based: true
    workflow_failure: true
    policy_gap: true
    schema_validation: true
    init_failure: true
  auth_method: "GITHUB_TOKEN"  # or "PAT" or "GITHUB_APP"
```

Default in `config.yaml`: `escalation.enabled: false` (consuming repos opt in via `project.yaml`).

### Step 5: Add Escalation Policy Rules

Add to `governance/policy/default.yaml` under a new `cross_repo_escalation` section:
- Trigger conditions mapping to detection criteria
- Severity classification rules
- Rate limiting (max 3 escalations per session to prevent spam)

### Step 6: Write Documentation

Create `governance/docs/cross-repo-escalation.md` covering:
- Architecture overview (detecting → dedup → escalate → track)
- Setup for consuming repos (authentication, project.yaml config)
- Authentication options (GITHUB_TOKEN with cross-repo scope, PAT, GitHub App)
- Dedup mechanism explanation
- Examples of framework-level vs. project-local issues

### Step 7: Update Existing Documentation

- `GOALS.md` — Add completed work entry
- `CLAUDE.md` — Update schema count
- Check `governance/docs/dark-factory-governance-model.md` for needed updates

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | `cross-repo-escalation.schema.json` | Validate JSON with `python -m json.tool` |
| Schema validation | `project.schema.json` | Validate updated schema is valid JSON Schema |
| Policy validation | `default.yaml` | Verify YAML syntax and structure consistency |
| Manual review | Workflow prompt | Verify the escalation flow is complete and references correct schemas/policies |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Consuming repos create duplicate upstream issues | Medium | Low | Dedup mechanism using hash-based markers in issue body |
| Authentication token scope too broad | Low | Medium | Document minimum required permissions; recommend fine-grained PAT |
| Spam from misconfigured consuming repos | Low | Medium | Rate limiting in policy (max 3 per session); disabled by default |
| Breaking change to project.schema.json | Medium | High | Additive change only — new optional `escalation` property with no required fields |

## 7. Dependencies

- [x] Governance compliance monitoring (#176) — provides the step tracking that escalation builds on (non-blocking, already merged)
- [ ] GitHub cross-repo issue creation requires appropriate token permissions (documented, not enforced by this change)

## 8. Backward Compatibility

Fully backward compatible. All changes are additive:
- New schema file (no existing schema modified structurally)
- New optional property in `project.schema.json` (consuming repos without `escalation` config are unaffected)
- New optional section in `default.yaml` (existing policy evaluation unchanged)
- `config.yaml` default is `enabled: false`

## 9. Governance

Expected panel reviews and policy profile:

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Schema and YAML correctness |
| security-review | Yes | Authentication model, cross-repo token handling |
| documentation-review | Yes | New documentation artifact |
| threat-modeling | Yes | Cross-repo trust boundary |
| cost-analysis | Yes | No cost impact (config-only) |
| data-governance-review | Yes | No PII implications |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Use issue body markers for dedup instead of labels | Labels require label management permissions; issue body search is simpler |
| 2026-02-24 | Default to disabled | Escalation requires cross-repo auth; consuming repos must opt in |
| 2026-02-24 | Rate limit at 3 per session | Prevents runaway escalation from a misconfigured consuming repo |
