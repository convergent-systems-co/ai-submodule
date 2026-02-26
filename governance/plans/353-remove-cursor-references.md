# Remove All References to Cursor Tooling

**Author:** Code Manager (agentic)
**Date:** 2026-02-25
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/353
**Branch:** itsfwcp/refactor/353/remove-cursor-references

---

## 1. Objective

Remove all references to Cursor IDE tooling from the governance framework. After this change, the only supported AI tools are Claude Code and GitHub Copilot.

## 2. Rationale

Cursor is no longer part of the supported AI tooling chain. Keeping references to it creates confusion about what tools the framework supports.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep Cursor references | Yes | Cursor is no longer supported; references are misleading |
| Remove only `.cursorrules` symlink | Yes | Incomplete — docs and scripts also reference Cursor |
| Full removal (chosen) | Yes | Clean, complete, matches the actual supported toolset |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files needed |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `README.md` | Remove Cursor from tool listing (lines ~313, ~402) |
| `.gitignore` | Remove `.cursor/` entry (line ~22) |
| `docs/onboarding/team-starter.html` | Remove Cursor from AI tool mentions (lines ~238, ~312) |
| `docs/onboarding/windows-onboarding.md` | Remove Cursor from AI tool mentions (lines ~28, ~86) |
| `docs/onboarding/ai-assisted-install.md` | Remove entire Cursor section (lines ~83-97) |
| `docs/onboarding/developer-guide.md` | Remove Cursor from tool listings (lines ~15, ~46) |
| `docs/contributing.md` | Remove Cursor from tool listing (line ~421) |
| `CLAUDE.md` | Update if any Cursor reference exists |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

### Files NOT Modified (intentional)

| File | Reason |
|------|--------|
| `governance/plans/*.md` | Historical plans are audit artifacts — immutable per conventions |
| `governance/prompts/reviews/api-design-review.md` | "cursor" refers to pagination cursor, not Cursor IDE |
| `docs/onboarding/risks-mitigation.html` | `cursor: pointer` is CSS, not Cursor IDE |
| `bin/init.sh` | No `.cursorrules` symlink creation exists in current code |
| `bin/init.ps1` | No `.cursorrules` symlink creation exists in current code |
| `config.yaml` | No `.cursorrules` symlink target exists in current config |

## 4. Approach

1. Edit `README.md` — remove Cursor from tool references, update to "Claude Code and GitHub Copilot"
2. Edit `.gitignore` — remove `.cursor/` entry
3. Edit `docs/onboarding/team-starter.html` — update AI tool references
4. Edit `docs/onboarding/windows-onboarding.md` — update AI tool references
5. Edit `docs/onboarding/ai-assisted-install.md` — remove Cursor section entirely
6. Edit `docs/onboarding/developer-guide.md` — update tool listings
7. Edit `docs/contributing.md` — update tool listing
8. Verify no remaining actionable Cursor references with grep

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Grep verification | All files | Confirm no remaining Cursor IDE references (excluding plans, CSS cursor, pagination cursor) |
| Link check | Modified HTML/MD files | Ensure no broken internal links after edits |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Missing a reference | Low | Low | Final grep verification step |
| Breaking HTML formatting | Low | Low | Careful editing of HTML files |
| Modifying immutable plans | Low | High | Explicitly excluded from scope |

## 7. Dependencies

- [x] No blocking dependencies — standalone cleanup task

## 8. Backward Compatibility

This is a purely subtractive change removing references to a tool that is no longer supported. No migration needed. Consuming repos that still use Cursor can continue to set up their own `.cursorrules` manually.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Primary change is documentation |
| code-review | Yes | Standard review |
| security-review | Yes | Always required |
| threat-modeling | Yes | Always required |
| cost-analysis | Yes | Always required |
| data-governance-review | Yes | Always required |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Exclude governance/plans/ from changes | Plans are immutable audit artifacts |
| 2026-02-25 | Exclude CSS cursor: pointer and pagination cursor references | Not related to Cursor IDE |
| 2026-02-25 | No changes to init.sh/init.ps1/config.yaml | No .cursorrules symlink exists in current code |
