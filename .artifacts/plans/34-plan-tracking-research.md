# Research and Implement Plan Tracking Best Practices

**Author:** Coder (agentic)
**Date:** 2026-02-21
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/34
**Branch:** NETWORK_ID/feat/34/plan-tracking-research

---

## 1. Objective

Implement a plan lifecycle system that: (a) archives plans to GitHub Release assets on PR merge so the repo tree stays clean, (b) generates a "How we got here" summary on issue close, and (c) provides a retrospective prompt for process improvement evaluation.

## 2. Rationale

Plans currently accumulate in `.plans/` permanently. The issue requests that plans be tracked as deletable artifacts rather than permanent repo files, and that they feed a process improvement loop.

**Research findings:**

| Storage Option | Deletable | Expires | Searchable | Cost |
|----------------|-----------|---------|------------|------|
| GitHub Release assets | Yes (API) | Never | Via release page | Free (public) |
| GitHub Actions artifacts | Yes (UI/API) | 90 days max | Via workflow | Counts against storage quota |
| Repo files (current) | Yes (git rm) | Never | git grep | Pollutes history |

**Decision: GitHub Release assets** — they are deletable, never expire, do not pollute the repo tree, and are free for public repositories.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep plans permanently in repo | Yes | Issue explicitly requests removal from repo |
| GitHub Actions artifacts | Yes | 90-day expiration, storage quotas |
| Issue comment only | Yes | Not diffable, hard to discover post-close |
| GitHub Release assets | **Selected** | Deletable, no expiration, clean repo |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.github/workflows/plan-archival.yml` | Workflow triggered on PR merge: archives plan to release, deletes from repo |
| `prompts/retrospective.md` | Prompt template for AI to evaluate completed plans for process improvements |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `prompts/startup.md` | Add Step 7h: Post-merge retrospective using retrospective prompt |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions (existing plans will be archived over time by the new workflow) |

## 4. Approach

### Step 1: Plan Archival Workflow

Create `.github/workflows/plan-archival.yml` that triggers on `pull_request` close (merged only):

1. **Detect plan files**: Check if the PR's changes include files in `.plans/`
2. **Generate "How we got here" summary**: Extract the plan title, objective, decision log, and key commits from the PR
3. **Archive to release**: Create or update a release tagged `plans-archive`, upload plan files as release assets
4. **Post summary**: Comment the "How we got here" summary on the associated issue
5. **Clean up**: Create a follow-up commit on `main` removing the archived plan file from `.plans/`

### Step 2: Retrospective Prompt

Create `prompts/retrospective.md` that the AI agent uses after completing an issue to evaluate:
- What went well in the planning/execution process
- What could be improved (templates, panels, prompts, decomposition)
- Token cost observations (were unnecessary personas loaded? Was context managed well?)
- Recommendations for governance process improvement

### Step 3: Integrate into Startup Sequence

Add to `prompts/startup.md` after Step 7g (merge) and before Step 8 (continue):
- Run the retrospective prompt on the just-completed issue
- Log findings as an issue comment
- If findings warrant governance changes, create a new issue

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Workflow syntax | YAML | Verify workflow parses correctly |
| PR test | Full workflow | This PR's merge will trigger the archival workflow on itself |
| Manual verification | Release page | Confirm plan appears as release asset after merge |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Workflow fails to create release | Low | Low | Release creation is idempotent; retry safe |
| Plan deletion commit conflicts | Low | Medium | Use bot commit on main after merge; no branches involved |
| Retrospective adds too much token cost | Medium | Low | Use Haiku-tier model for retrospective; keep prompt compact |

## 7. Dependencies

- [x] GitHub CLI with release management permissions
- [x] Governance workflow (dark-factory-governance.yml) — merged in #31

## 8. Backward Compatibility

Existing plans in `.plans/` are unaffected. The archival workflow only processes plans that are part of newly merged PRs. Existing plans can be manually archived later or left in place.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New workflow and prompt files |
| documentation-review | Yes | Modifying startup.md |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Use GitHub Release assets over Actions artifacts | No expiration, deletable, free, clean repo |
| 2026-02-21 | Single `plans-archive` release tag | Avoids release sprawl; all plans in one place |
| 2026-02-21 | Retrospective uses Haiku-tier model suggestion | Minimize token cost for self-evaluation |
| 2026-02-21 | Plan deletion is a separate commit post-merge | Avoids complicating the PR diff |
