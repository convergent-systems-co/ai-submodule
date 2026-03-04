# Per-Panel Model Assignment Configuration in project.yaml

**Author:** Team Lead (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/711
**Branch:** itsfwcp/feat/711/per-panel-model-assignment

---

## 1. Objective

Enable per-panel model assignment in `project.yaml` so users can assign specific AI models to specific governance panels (e.g., Claude Opus 4.6 for security-review, Claude Haiku 4.5 for documentation-review). The model router already supports this internally — this issue exposes it through the user-facing `governance.panels` config surface with defaults/overrides syntax, adds `model_id` to panel emissions, and validates model names at init time.

## 2. Rationale

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Use existing governance.models.panels config | Yes | Already exists! But the issue describes a `governance.panels.defaults.model` / `governance.panels.overrides.<panel>.model` syntax that is different from the current flat `governance.models.panels` structure |
| Add a new governance.panels section | Yes | Selected — provides more structured defaults/overrides pattern; backward compatible with existing flat config |
| Per-panel config in each panel prompt file | Yes | Scatters config; harder to manage globally |

**Key insight:** The model router (`model_router.py`) already fully supports per-panel model overrides via `governance.models.panels` in project.yaml. The schema (`project.schema.json`) already defines this. What is missing is:
1. The alternative `governance.panels.defaults.model` / `governance.panels.overrides` syntax from the issue
2. `model_id` in panel emission output
3. Init-time validation of model names
4. Documentation of the feature

## 3. Scope

### Files to Create

None — all changes are modifications to existing files.

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/engine/orchestrator/model_router.py` | Add `validate_model_names()` method that checks configured model names against a known-models list; add support for parsing the `governance.panels.defaults`/`overrides` syntax as an alternative to `governance.models.panels` |
| `governance/engine/orchestrator/config.py` | Parse `governance.panels.defaults.model` and `governance.panels.overrides` from project.yaml as an alternative panel model config surface; merge into ModelConfig |
| `governance/schemas/project.schema.json` | Add `governance.panels` object schema with `defaults.model` and `overrides` properties (alongside existing array-of-strings `panels` at root level) |
| `governance/schemas/panel-output.schema.json` | Add optional `model_id` field to panel emission schema |
| `governance/engine/tests/test_model_router.py` | Tests for model name validation |
| `governance/engine/tests/test_config.py` | Tests for parsing the new panel config syntax |

### Files to Delete

None.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `model_router.py` validate_model_names | Test valid/invalid model names are caught |
| Unit | `config.py` panel config parsing | Test both syntaxes: `governance.models.panels` and `governance.panels.defaults/overrides` |
| Unit | `config.py` merge logic | Test that overrides syntax merges correctly with existing ModelConfig |
| Unit | Schema validation | Test panel-output schema accepts model_id field |

## 4. Approach

1. **Extend `config.py`** to parse the alternative panel model config:
   ```yaml
   governance:
     panels:
       defaults:
         model: "claude-sonnet-4-6"
       overrides:
         security-review:
           model: "claude-opus-4-6"
         documentation-review:
           model: "claude-haiku-4-5"
   ```
   Map this into the existing `ModelConfig.panel_overrides` dict and `ModelConfig.default` field.

2. **Add `KNOWN_MODELS` list to `model_router.py`** — a set of recognized model shorthand names (opus, sonnet, haiku, claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5, gpt-4o, etc.). Add `validate_model_names()` that returns warnings for unrecognized names (not errors — custom model names should be allowed with a warning).

3. **Update `panel-output.schema.json`** to add an optional `model_id` string field in the panel emission schema. This records which model produced the panel output for auditability.

4. **Update `project.schema.json`** to document the new `governance.panels` object format alongside the existing root-level `panels` array. Note: the root-level `panels` is a list of panel filenames to activate; `governance.panels` is model assignment config. These are different concerns and do not conflict.

5. **Write tests** covering both config syntaxes, model validation, and schema changes.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Confusion between root `panels` (list) and `governance.panels` (config) | Med | Med | Clear schema descriptions; document the distinction |
| Breaking existing governance.models.panels config | Low | High | Both syntaxes are supported; existing config continues to work |
| Invalid model names silently accepted | Low | Med | validate_model_names() warns on unrecognized names |

## 7. Dependencies

- [ ] None — extends existing model router infrastructure

## 8. Backward Compatibility

Fully backward compatible. The existing `governance.models.panels` flat config continues to work. The new `governance.panels.defaults`/`overrides` syntax is an alternative that takes precedence when both are present. Existing panel emissions without `model_id` remain valid.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Engine changes |
| security-review | Yes | Model routing affects security panel depth |
| documentation-review | Yes | Schema and config surface changes |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Support both config syntaxes | Backward compatibility; gentle migration path |
| 2026-03-02 | Model validation is warnings, not errors | Users may use custom/private model names we don't know about |
| 2026-03-02 | model_id in emissions is optional | Existing emissions without it remain valid |
