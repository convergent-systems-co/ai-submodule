# Incident Response Playbooks

Documented procedures for handling governance pipeline failures, compromises, and anomalies. Each playbook includes detection criteria, immediate actions, investigation steps, and recovery procedures.

## Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| P0 — Critical | Active compromise or data exfiltration | Immediate |
| P1 — High | Governance bypass or containment breach | Within 1 hour |
| P2 — Medium | Model degradation or policy gap | Within 4 hours |
| P3 — Low | Documentation gap or configuration drift | Within 24 hours |

---

## Playbook 1: Governance Pipeline Compromise

**Severity:** P0 — Critical

**Trigger:** CI governance workflow (`dark-factory-governance.yml`) was modified by a PR, or governance panel emissions were forged or tampered with.

### Detection Criteria

- `dark-factory-governance.yml` appears in PR diff
- Panel emissions fail schema validation unexpectedly
- Run manifest signature verification fails
- Audit trail shows gaps or inconsistencies
- `github-actions[bot]` approves a PR that should have been blocked

### Immediate Actions

1. **Block all merges** to the affected repository immediately
2. **Revoke any active auto-merge** PRs using `gh pr merge --disable-auto`
3. **Notify security lead and tech lead** via the configured escalation channels
4. **Preserve evidence**: Do not delete or modify any branch, workflow run, or emission file

### Investigation Steps

1. Identify the PR that modified the governance workflow:
   ```bash
   git log --all --oneline -- .github/workflows/dark-factory-governance.yml
   ```
2. Audit all merges since the workflow was modified:
   ```bash
   git log --oneline --since="<modification-date>" --merges
   ```
3. For each merge, verify the run manifest exists and has a valid signature:
   ```bash
   python governance/bin/verify-audit-chain.py --since "<modification-date>"
   ```
4. Check if any panel emissions were modified after creation:
   ```bash
   git log --all --diff-filter=M -- "governance/emissions/**"
   ```
5. Review the workflow modification diff for:
   - Removed or weakened panel requirements
   - Modified approval conditions
   - Added bypass logic
   - Changed the policy profile reference

### Recovery

1. Revert the workflow to the last known-good state:
   ```bash
   git checkout <last-good-commit> -- .github/workflows/dark-factory-governance.yml
   ```
2. Re-evaluate all merges that occurred while the workflow was compromised
3. For any merge that would have been blocked under the original workflow:
   - Create a revert PR
   - Run the governance pipeline on the revert
4. Update CODEOWNERS to require additional reviewers for workflow files
5. Document the incident in a post-mortem

### Prevention

- Add branch protection rule requiring CODEOWNER approval for `.github/workflows/` changes
- Enable signed commits for the governance workflow
- Add integrity verification for workflow files in `governance/integrity-manifest.json`

---

## Playbook 2: Model Blind Spot Discovery

**Severity:** P2 — Medium

**Trigger:** A pattern of governance panel emissions is discovered where the LLM consistently missed a category of vulnerability, code quality issue, or compliance requirement.

### Detection Criteria

- Security vulnerability found in production that was present in code reviewed by governance panels
- Canary calibration pass rate drops below threshold for a specific panel
- Multiple similar findings missed across different PRs
- External audit identifies issues that governance panels should have caught

### Immediate Actions

1. **Document the blind spot** with specific examples (PR numbers, file paths, vulnerability descriptions)
2. **Assess blast radius**: How many PRs were affected? What time period?
3. **Check canary calibration data** for the affected panel:
   ```bash
   cat .artifacts/state/canary-results.jsonl | grep "<panel-name>"
   ```

### Investigation Steps

1. Identify all PRs reviewed during the blind spot period:
   ```bash
   gh pr list --state merged --search "merged:>YYYY-MM-DD" --json number,mergedAt
   ```
2. For each affected PR, re-run the relevant governance panel manually
3. Compare the original emission with the re-run emission
4. Identify the pattern: Is it a specific language? Framework? File type? Pattern?
5. Check if the model version changed during the period
6. Review the review prompt for the affected panel for gaps

### Recovery

1. Create a retroactive audit report documenting:
   - Affected time period
   - Number of PRs affected
   - Specific vulnerabilities or issues missed
   - Root cause (model limitation, prompt gap, etc.)
2. For each affected PR, assess whether remediation is needed
3. If remediation is needed, create issues for each affected PR
4. Update the review prompt to address the blind spot
5. Add canary test cases that specifically target the discovered blind spot

### Prevention

- Maintain a library of canary test cases in `governance/policy/canary-calibration.yaml`
- Run periodic retroactive audits on merged PRs
- Track detection rates by category over time
- Update review prompts when new vulnerability patterns emerge

---

## Playbook 3: Emergency Merge Revert

**Severity:** P1 — High

**Trigger:** A merge was completed that passed all governance gates but should not have been approved. The merged code has a serious defect, security vulnerability, or compliance violation.

### Detection Criteria

- Production incident traced to a recently merged PR
- Security scan finds a critical vulnerability in merged code
- Compliance audit identifies a violation in merged code
- Run manifest indicates auto_merge but post-merge review finds issues

### Immediate Actions

1. **Create a revert PR immediately**:
   ```bash
   git revert -m 1 <merge-commit-sha>
   git push origin revert-<pr-number>
   gh api repos/OWNER/REPO/pulls -f title="revert: emergency revert of #<PR>" \
     -f head="revert-<pr-number>" -f base="main" \
     -f body="Emergency revert. See incident response."
   ```
2. **Run governance pipeline on the revert** — do not skip governance even for emergency reverts
3. **Notify stakeholders**: tech lead, security lead (if security issue), compliance officer (if compliance issue)

### Investigation Steps

1. Pull the run manifest for the original merge:
   ```bash
   cat governance/emissions/run-manifest-<id>.json | python -m json.tool
   ```
2. Review each panel emission for the original PR:
   - Did all required panels execute?
   - Were confidence scores reasonable?
   - Did any panel flag the issue but it was below the threshold?
3. Check if the plausibility checks should have caught the issue:
   - Was there a zero-findings anomaly?
   - Were identical scores detected?
4. Check the policy profile conditions:
   - Would a stricter profile have caught this?
   - Are the auto-merge thresholds appropriate?

### Recovery

1. Merge the revert PR through governance
2. Create a post-mortem documenting:
   - What was merged and what the impact was
   - Why governance panels did not catch it
   - What policy or prompt changes would have prevented it
3. Implement the identified improvements
4. Re-review the original changes with the improved pipeline before re-merging

### Prevention

- Tighten auto-merge thresholds if they were too permissive
- Add specific panel rules or canary tests for the missed category
- Consider adding a manual review requirement for the affected change type

---

## Playbook 4: Agent Containment Breach

**Severity:** P1 — High

**Trigger:** An agent persona performed an action outside its containment boundaries — modified files it should not have access to, performed a denied operation, or exceeded resource limits.

### Detection Criteria

- Containment violation logged to `.artifacts/state/containment-violations.jsonl`
- Coder branch modified governance infrastructure files
- Git diff shows changes to denied paths from a worker agent branch
- Resource limits exceeded (files per PR, lines per commit)

### Immediate Actions

1. **Stop the affected agent session** — emit CANCEL if still running
2. **Review the violation log**:
   ```bash
   cat .artifacts/state/containment-violations.jsonl | python -m json.tool
   ```
3. **Assess the changes**: Were governance-critical files actually modified?
4. **If files were modified**: Create a revert for the unauthorized changes

### Investigation Steps

1. Identify the branch and commits where the breach occurred:
   ```bash
   git log --oneline <branch> --diff-filter=M -- "governance/**"
   ```
2. Determine the root cause:
   - Was enforcement mode set to `advisory` instead of `enforced`?
   - Did the containment checker fail to evaluate the path?
   - Was the violation a false negative in path matching?
   - Did the agent bypass the hook (e.g., `--no-verify`)?
3. Check if the mechanical containment hook was installed:
   ```bash
   cat .git/hooks/pre-commit
   ```
4. Verify the agent-containment.yaml enforcement mode:
   ```bash
   grep "mode:" governance/policy/agent-containment.yaml
   ```

### Recovery

1. Revert any unauthorized changes to governance infrastructure
2. If enforcement mode was `advisory`, switch to `enforced`
3. Install or repair the pre-commit hook
4. Re-run the governance pipeline on any PRs affected by the breach

### Prevention

- Ensure `enforcement.mode: enforced` is the default (not `advisory`)
- Install the mechanical containment hook as a pre-commit hook
- Add CI-level validation via the containment hook in the governance workflow
- Regularly audit the containment violation log

---

## Incident Response Template

For any incident not covered by the playbooks above, use this template:

```markdown
# Incident Report: [Title]

**Date:** YYYY-MM-DD
**Severity:** P0/P1/P2/P3
**Status:** Active / Investigating / Resolved
**Reporter:** [name]

## Summary
[One paragraph describing what happened]

## Timeline
- HH:MM — [Event]
- HH:MM — [Event]

## Impact
- [What was affected]
- [Number of PRs/merges/repos impacted]

## Root Cause
[Why it happened]

## Resolution
[What was done to fix it]

## Prevention
[What changes will prevent recurrence]

## Action Items
- [ ] [Specific action with owner and deadline]
```

---

## Escalation Contacts

| Role | Responsibility |
|------|---------------|
| Security Lead | P0/P1 security incidents, containment breaches |
| Tech Lead | All P0/P1 incidents, governance pipeline issues |
| Compliance Officer | Compliance violations, audit failures |
| Engineering Manager | Resource allocation for incident response |

Escalation contacts are configured per-repository in `project.yaml` under `governance.escalation_contacts`.
