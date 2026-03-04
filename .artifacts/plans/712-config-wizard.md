# Guided Prompt-Chain Wizard for project.yaml Configuration

**Author:** Team Lead (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/712
**Branch:** itsfwcp/feat/712/config-wizard

---

## 1. Objective

Create a guided, step-by-step configuration wizard that leads users through `project.yaml` setup without requiring them to read documentation. The wizard uses progressive disclosure — each step builds on the previous answer. Implemented as both a set of prompt-chain files (for agentic use) and an MCP skill (for IDE integration).

## 2. Rationale

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Interactive CLI wizard (Python input()) | Yes | Requires terminal; doesn't work in IDE agents |
| MCP skill only | Yes | Not everyone has MCP configured |
| Prompt-chain files only | Yes | Not discoverable without knowing the path |
| Prompt-chain + MCP skill + init integration | Yes | Selected — maximum reach across usage modes |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/prompts/configuration/step-1-basics.md` | Wizard step 1: project basics (language, framework auto-detection) |
| `governance/prompts/configuration/step-2-governance-level.md` | Wizard step 2: governance level selection (light/standard/strict) |
| `governance/prompts/configuration/step-3-panels.md` | Wizard step 3: panel configuration and model assignment |
| `governance/prompts/configuration/step-4-automation.md` | Wizard step 4: automation level (parallel agents, PM mode) |
| `governance/prompts/configuration/step-5-review.md` | Wizard step 5: review generated config and write to disk |
| `governance/prompts/configuration/wizard-runner.md` | Main wizard prompt that chains all steps together |
| `mcp-server/skills/configure-project.skill.md` | MCP skill wrapping the wizard for IDE invocation |
| `governance/schemas/configure-wizard-state.schema.json` | JSON Schema for wizard state file |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/init.md` | Add reference to the configuration wizard as an alternative to manual setup |

### Files to Delete

None.

## 4. Approach

1. **Create wizard state schema** — define the JSON Schema for `.governance/state/configure-wizard.json` that stores accumulated answers across steps:
   ```json
   {
     "step": 1,
     "project_name": "my-app",
     "languages": ["python"],
     "framework": "fastapi",
     "governance_level": "standard",
     "panels": [...],
     "panel_models": {...},
     "parallel_coders": 5,
     "use_project_manager": false,
     "generated_config": {}
   }
   ```

2. **Create step prompt files** — each step is a standalone prompt in `governance/prompts/configuration/`:
   - **Step 1 (Basics):** Instruct the agent to run auto-detection (from #705's `auto_detect.py`), show results, ask user to confirm/modify language and framework. Write to wizard state.
   - **Step 2 (Governance Level):** Present three options with descriptions. Map to policy profile and panel set. Write to wizard state.
   - **Step 3 (Panels):** Based on governance level, show which panels will run. Offer model assignment per panel (using #711's config surface). Write to wizard state.
   - **Step 4 (Automation):** Suggest parallel_coders based on repo size. Explain PM mode trade-offs. Write to wizard state.
   - **Step 5 (Review):** Generate complete project.yaml from wizard state. Show to user. On confirmation, write to disk and validate.

3. **Create wizard-runner.md** — the main entry prompt that chains all steps sequentially, reading wizard state between steps.

4. **Create MCP skill** — `configure-project.skill.md` that invokes the wizard-runner prompt.

5. **Update init.md** — add a section pointing users to the wizard for guided setup.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | Wizard state schema | Validate schema against sample wizard state files |
| Unit | Each step prompt | Verify each step prompt file is valid markdown with required sections |
| Integration | Full wizard flow | End-to-end test: run all steps with mock inputs, verify generated project.yaml |
| Schema validation | Generated config | Verify wizard output passes project.schema.json validation |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Wizard generates invalid config | Low | High | Final step validates against schema before writing |
| Step prompts become stale as config surface evolves | Med | Med | Reference schema definitions rather than hardcoding options |
| Users skip wizard and edit YAML directly | Low | None | Wizard is additive; manual editing always works |

## 7. Dependencies

- [ ] #705 (auto-detection) — soft dependency. The wizard can function without auto-detection by asking users directly, but auto-detection makes Step 1 much smoother. The wizard should gracefully handle the case where `auto_detect.py` is not available.
- [ ] #711 (per-panel model assignment) — soft dependency. Step 3 can offer model assignment if the feature is available, or skip that sub-step if not.

## 8. Backward Compatibility

Fully backward compatible. The wizard is an additive feature. Existing `project.yaml` files are unaffected. Users who prefer manual editing continue to do so. The wizard only writes `project.yaml` when the user explicitly confirms in Step 5.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | MCP skill and schema files |
| documentation-review | Yes | User-facing prompts |
| security-review | Yes | File write operations |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Prompt-chain architecture over Python CLI | Works in any agent context (IDE, CLI, MCP) without terminal dependency |
| 2026-03-02 | Wizard state persisted to disk | Enables step resumption after context resets |
| 2026-03-02 | Soft dependencies on #705 and #711 | Wizard works standalone; enhanced when those features are available |
