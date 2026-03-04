# Plan: Unified CLI Reference — Fragmented Tooling (#741)

## Objective

Document how the unified `dark-governance` Go binary replaces the fragmented set of shell scripts, Python modules, and Node tools. This issue is largely resolved by the Go binary work (#743, #744, #758, #738) — the remaining deliverable is documentation that ties it together.

## Scope

Documentation-only changes:
1. New unified CLI reference guide
2. Update developer quickstart to reference unified CLI
3. Update CLAUDE.md Commands section to show unified CLI alongside legacy commands

## Files to Create/Modify

### 1. `docs/guides/unified-cli-reference.md` (NEW)
Comprehensive CLI reference showing how `dark-governance` replaces fragmented tools:

| Old Tool | New Command |
|----------|-------------|
| `bash .ai/bin/init.sh` | `dark-governance install` + `dark-governance init` |
| `python governance/bin/policy-engine.py` | `dark-governance engine run` |
| `bash mcp-server/install.sh` | `dark-governance mcp install` (planned) |
| Manual submodule + init flow | `dark-governance init` |
| Manual integrity checks | `dark-governance verify` |
| `bash .ai/bin/governance-status.sh` | `dark-governance engine status` |
| `bash .ai/bin/update.sh` | `dark-governance update` |

Includes: all subcommands, flags, environment variables, examples, JSON output mode.

### 2. `docs/guides/developer-quickstart.md` (MODIFY)
- Add "Option B: Binary Installation" section alongside existing submodule instructions
- Reference `dark-governance init` as the recommended path
- Keep existing submodule instructions as "Option A: Submodule Installation" for backward compatibility

### 3. `CLAUDE.md` (MODIFY)
- Update Commands section to add unified CLI commands prominently
- Show `dark-governance` commands first, legacy commands second with "(legacy)" label
- Keep legacy commands for backward compatibility during transition

## Design Decisions

- Both old and new commands are documented — no breaking changes to docs
- Unified CLI is presented as the recommended path, submodule as legacy
- CLI reference follows the same structure as existing guides in `docs/guides/`

## Dependencies

- Go binary source in `src/` (for accurate command/flag reference)
- Existing docs in `docs/guides/` (for style consistency)

## Acceptance Criteria

- [ ] `docs/guides/unified-cli-reference.md` covers all current CLI subcommands
- [ ] `docs/guides/developer-quickstart.md` includes binary installation option
- [ ] `CLAUDE.md` Commands section updated with unified CLI
- [ ] All conventional commits on branch `itsfwcp/feat/741/unified-tooling`
