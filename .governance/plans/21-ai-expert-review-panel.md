# AI Expert Review Panel and Repo-Type Detection

**Author:** Coder (agentic)
**Date:** 2026-02-21
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/21
**Branch:** itsfwcp/21-ai-expert-review-panel

---

## 1. Objective

Ensure the governance system reviews this repository as an AI governance/agent-driving configuration repo, not just a documentation repo. Add repo-type detection so the correct panels are triggered, and create an AI Expert Review panel that evaluates changes for their impact on AI agent behavior, prompt engineering quality, and governance pipeline integrity.

## 2. Rationale

Currently, the `optional_panels` triggers in `policy/default.yaml` are path-based:
- `architecture-review` triggers on `src/`, `lib/`, `pkg/`
- `performance-review` triggers on `src/`, `bench/`
- `testing-review` triggers on test files
- `documentation-review` triggers on docs files

This repo has none of those directories. It contains `personas/`, `prompts/`, `policy/`, `schemas/`, and `.github/workflows/` — all of which drive AI agent behavior and governance pipelines. The result is that only `code-review` and `documentation-review` panels execute, missing critical reviews for AI safety, prompt quality, architecture, and threat modeling.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Only add path-based triggers for this repo | Yes | Doesn't solve the broader problem — other AI/config repos would have the same issue |
| Create a project.yaml config per-repo | Yes | Useful but insufficient alone — still need the AI Expert panel to exist |
| Add repo-type detection + AI Expert panel + updated triggers | **Selected** | Comprehensive solution that handles this repo and future governance repos |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `personas/panels/ai-expert-review.md` | New panel definition for AI expert review — evaluates persona quality, prompt engineering, governance pipeline integrity, and AI safety |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `policy/default.yaml` | Add `ai-expert-review` weight, add path-based triggers for governance-specific directories (`personas/`, `prompts/`, `policy/`, `schemas/`, `.github/workflows/`), add `threat-modeling` trigger for `policy/` and `schemas/` changes |
| `personas/panels/architecture-review.md` | Verify it can handle governance architecture (not just application code architecture) — may need scope note |
| `.github/workflows/governance-review.yml` | No changes needed — it already evaluates whatever emissions are present |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

### Step 1: Create the AI Expert Review Panel

Create `personas/panels/ai-expert-review.md` with:
- **Participants**: AI Safety Specialist, Prompt Engineer, Governance Architect
- **Scope**: Persona definitions, prompt templates, workflow definitions, policy rules, schema changes
- **Evaluates for**:
  - Persona clarity and completeness (role, evaluate-for, anti-patterns)
  - Prompt injection resistance in prompt templates
  - Governance pipeline integrity (gates not bypassed, emissions validated)
  - AI agent behavior predictability (do changes create non-deterministic behavior?)
  - Context management safety (token budget, checkpoint protocol)
  - Structured emission compliance
- **Output**: Standard `panel-output.schema.json` structured emission
- **Confidence calculation**: Similar to other panels but weighted for AI-specific concerns

### Step 2: Update Policy Profile Triggers

In `policy/default.yaml`, update `optional_panels` to add:

```yaml
optional_panels:
  # ... existing triggers ...
  - panel: ai-expert-review
    trigger: files_changed_in ["personas/", "prompts/", "policy/", "schemas/", "instructions/"]
  - panel: architecture-review
    trigger: files_changed_in ["src/", "lib/", "pkg/", "personas/panels/", "prompts/workflows/", ".github/workflows/"]
  - panel: threat-modeling
    trigger: files_changed_in ["policy/", "schemas/", "personas/agentic/", ".github/workflows/"]
  - panel: security-review
    trigger: always  # Already required, but make explicit in optional triggers for visibility
```

Add the `ai-expert-review` weight to the weighting model:

```yaml
weighting:
  weights:
    code-review: 0.20
    security-review: 0.20
    ai-expert-review: 0.15
    architecture-review: 0.15
    testing-review: 0.10
    performance-review: 0.05
    copilot-review: 0.10
    documentation-review: 0.05
```

Note: `code-review` drops from 0.25 to 0.20 to make room for `ai-expert-review` at 0.15. Total still sums to 1.0.

### Step 3: Verify Architecture Review Panel Scope

Read `personas/panels/architecture-review.md` and confirm it can handle governance-architecture changes (panel orchestration, policy evaluation flow, emission schemas). If not, add a scope note for governance-repo contexts.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | ai-expert-review panel output | Verify emission from new panel validates against panel-output.schema.json |
| Manual review | All modified files | Confirm triggers match this repo's directory structure |
| Governance run | Full PR | Verify the governance-review.yml workflow evaluates the new panel emission correctly |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Weight redistribution changes aggregate confidence for existing PRs | Medium | Low | Weights are close to original; redistribution handles missing panels |
| AI Expert panel is too broad in scope | Low | Medium | Clearly define evaluate-for criteria and limit to AI-specific concerns |
| Trigger paths overlap causing duplicate panel execution | Low | Low | Policy engine handles duplicate emissions gracefully |

## 7. Dependencies

- [x] No blocking dependencies

## 8. Backward Compatibility

- Adding new optional panel trigger is additive — existing repos without `personas/` directories are unaffected
- Weight redistribution means missing panels get their weight redistributed, so existing repos without the AI Expert panel see the same aggregate behavior
- The `profile_version` should be bumped to `1.1.0` (minor version for additive changes)

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Policy changes require review |
| security-review | Yes | Required panel |
| architecture-review | Yes | Governance architecture change |
| documentation-review | Yes | Panel definition is cognitive artifact |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Create new panel rather than extend existing | AI governance review is a distinct concern from code review or architecture review |
| 2026-02-21 | Adjust code-review weight from 0.25 to 0.20 | Minimal impact; makes room for ai-expert-review without exceeding 1.0 total |
| 2026-02-21 | Add architecture-review triggers for governance paths | This repo's personas/panels/ and workflows/ are its architecture |
