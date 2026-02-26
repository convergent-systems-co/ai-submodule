# Consolidate Consumer Governance Outputs Under `.governance/`

**Author:** Code Manager (agent)
**Date:** 2026-02-25
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/339
**Branch:** itsfwcp/feat/339/governance-output-consolidation

---

## 1. Objective

Consolidate all consumer-repo governance output directories under a single hidden `.governance/` directory. Currently, outputs are scattered across `governance/plans/`, `governance/checkpoints/`, `.panels/`, and `.governance-state/`. After this change, consumers will have a single `.governance/` tree mirroring the ai-submodule's `governance/` layout.

## 2. Rationale

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep scattered dirs | Yes | User feedback: too much governance clutter in consumer repos |
| Use `governance/` (no dot) | Yes | Visible in root listing; consumers want minimal footprint |
| Use `.ai/governance/` | Yes | `.ai/` is the submodule — consumer outputs must not be inside it |
| **Use `.governance/`** | **Selected** | Single hidden dir, mirrors submodule layout, minimal consumer footprint |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| `config.yaml` | Update `project_directories` paths from scattered to `.governance/` subdirs |
| `bin/init.sh` | Create `.governance/` subdirs; add migration from old paths; update validation references |
| `governance/prompts/startup.md` | Update plan/checkpoint paths to use `.governance/` in consumer context |
| `governance/prompts/templates/plan-template.md` | Update save location guidance |
| `governance/prompts/checkpoint-resumption-workflow.md` | Update checkpoint path references |
| `governance/prompts/agent-protocol.md` | Update `.governance-state/` → `.governance/state/` |
| `CLAUDE.md` (`.ai/CLAUDE.md`) | Update directory references and descriptions |
| `instructions.md` | Update output path references |
| `docs/configuration/repository-setup.md` | Update documentation |
| `docs/architecture/session-state-persistence.md` | Update state directory references |
| `governance/prompts/reviews/governance-compliance-review.md` | Update path references |
| `governance/prompts/governance-compliance-checklist.md` | Update emission/plan path references |

### Files to Delete

None — old directories in consumer repos are migrated by init.sh, not deleted.

## 4. Approach

### Directory mapping (consumer repos)

| Old Path | New Path |
|----------|----------|
| `governance/plans/` | `.governance/plans/` |
| `governance/checkpoints/` | `.governance/checkpoints/` |
| `.panels/` | `.governance/panels/` |
| `.governance-state/` | `.governance/state/` |

### Context detection

The agentic loop (startup.md) and other prompts must detect context:
- **In ai-submodule repo**: Use `governance/plans/`, `governance/checkpoints/` (existing paths)
- **In consuming repo**: Use `.governance/plans/`, `.governance/checkpoints/`, etc.

Detection: if `.gitmodules` contains `.ai` submodule entry → consumer context → use `.governance/`. Otherwise → ai-submodule context → use `governance/`.

### Steps

1. Update `config.yaml` project_directories
2. Update `bin/init.sh` — create `.governance/` dirs, add migration logic for old paths
3. Update all prompt files to use context-aware paths
4. Update documentation (CLAUDE.md, instructions.md, docs/)
5. Test that init.sh correctly creates new structure

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | init.sh | Run init.sh in a test context, verify dirs created |
| Unit | policy engine | Existing tests still pass (engine paths unaffected) |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Consumer repos with old paths break | Medium | Medium | init.sh migrates old → new automatically |
| Prompts reference wrong paths | Low | Medium | Context detection in prompts |

## 7. Dependencies

- [ ] None — self-contained change

## 8. Backward Compatibility

init.sh will detect old directories and move their contents to the new `.governance/` locations. A migration message will inform the user.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Extensive doc updates |
| security-review | Yes | Default required |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Use `.governance/` not `.ai/governance/` | `.ai/` is the submodule; consumer outputs must be separate |
| 2026-02-25 | Keep ai-submodule paths as `governance/` | Submodule has its own convention; change is consumer-only |
