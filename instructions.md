# AI Instructions

<!-- ANCHOR: Base instructions — must survive context resets -->

## Core Principles

- Be concise and direct
- Show, don't tell — prefer code over explanations
- Follow project conventions (see `project.yaml`)
- Ask clarifying questions when requirements are ambiguous
- Prefer iterative changes over large rewrites
- Check `project.yaml` (project root) for project configuration

## Enterprise-Locked Files

- `jm-compliance.yml` is enterprise-locked and must **never** be modified, moved, or overridden. It is managed centrally and any local changes will be rejected.

## Context Capacity Protocol

**Hard stop at 80% context capacity. No exceptions.**

When approaching 80% of context window:
1. Stop current work immediately — do not start new tasks
2. Ensure git working tree is clean (commit, stash, or abort in-progress merges)
3. Write a checkpoint to `.artifacts/checkpoints/` with: current task, completed work, remaining work, git branch state
4. Summarize the checkpoint to the user
5. Request a context reset (`/clear`)

Never allow context to reach compaction with uncommitted changes, merge conflicts, or untracked state. A dirty compaction loses instructions and context that cannot be recovered.

## Repository Configuration

Repository settings (auto-merge, CODEOWNERS, branch protection) are declared in `config.yaml` and `project.yaml`. To apply:
- **CLI:** `bash .ai/bin/init.sh` (or `bash .ai/bin/init.sh --install-deps` for full setup)
- **After submodule update:** `bash .ai/bin/init.sh --refresh` (re-applies structural setup; done automatically by the agentic startup loop)
- **Branch protection check:** `bash .ai/bin/init.sh --check-branch-protection` (outputs `REQUIRES_PR=true|false`; done automatically by the agentic startup loop to route structural commits through PRs when required)
- **Troubleshooting:** `bash .ai/bin/init.sh --debug` for verbose output, `--dry-run` for no-op preview. Individual modular scripts in `governance/bin/` can be run standalone. See `docs/troubleshooting/init-failures.md`.
- **Agentic:** Tell your AI assistant to read and execute `governance/prompts/init.md` for an interactive, guided setup

See `docs/configuration/repository-setup.md` for details.

## Issue State Validation

Before starting or resuming work on any GitHub issue, verify it is still open:

```bash
gh issue view <number> --json state --jq '.state'
```

- If the issue is **closed**, do not start or continue work on it — even if a checkpoint or branch exists for it.
- During checkpoint restores, re-validate all in-flight and remaining issues before resuming.
- If an issue is closed while an agent is mid-flight, stop work at the next opportunity and notify the user.

Closed issues represent a user decision. Continuing work on them wastes compute and creates noise.

## Governance Pipeline — Mandatory

**The governance pipeline applies to ALL work, in ALL modes (local and remote). No exceptions.**

Every code change — regardless of size, urgency, or operating mode — must follow this sequence:

1. **Plan first** — Create a plan in `.artifacts/plans/` before writing any code. No implementation without a plan.
2. **Panels must run** — Default panels (code-review, security-review, threat-modeling, cost-analysis, documentation-review, data-governance-review) must execute on every change. If panel emissions are missing, the change is not governance-approved.
3. **Documentation with every change** — Update affected docs in the same commit (GOALS.md, CLAUDE.md, README.md, governance docs).

### Local Mode (no GitHub remote)

When operating without a GitHub remote (no issues, PRs, or CI):
- Plans are still mandatory — write to `.artifacts/plans/` before implementing.
- Panel evaluation still applies — the policy engine can run locally via `python governance/bin/policy-engine.py`.
- Commit messages must still use conventional commit format.
- Skip only GitHub-specific steps (issue comments, PR creation, Copilot polling).

### PR Approval Is Automated

**Never manually approve PRs or seek manual approval.** The `dark-factory-governance.yml` workflow evaluates panel emissions and approves via `github-actions[bot]`, which is listed as a CODEOWNER. After creating a PR:

1. Wait for the governance workflow to complete
2. Verify `github-actions[bot]` has approved (check reviews)
3. Merge the PR

The only exception is when the policy engine decision is `human_review_required` — in that case, escalate to the user. Do not attempt to find or use other accounts to approve PRs.

### Missing Panels

If required panel emissions are not present in `governance/emissions/`:
- **Do not merge.** A merge without governance approval violates the pipeline.
- Run the required panels or escalate to human review.
- See `governance/policy/default.yaml` for the list of required panels.

## Compact Instructions

After compaction, conversation context may be lost. Immediately:
1. Check for emergency checkpoints: `ls -t .artifacts/checkpoints/*emergency* 2>/dev/null | head -1`
2. If an emergency checkpoint exists (written in last 5 minutes), an agentic loop was interrupted
3. Report to user: "Context was compacted mid-session. Emergency checkpoint saved at {path}. Run `/startup` to resume."
4. Do NOT continue previous work without `/startup` — the checkpoint has the recovery state

<!-- /ANCHOR -->

*Domain-specific guidance in `instructions/`. Project-specific instructions extend this.*
