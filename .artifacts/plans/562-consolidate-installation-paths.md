# Plan: Consolidate to two clear installation paths

**Issue:** #562
**Type:** Feature
**Priority:** High

## Problem

Four installation paths exist with subtle behavioral differences. `quick-install.sh` is redundant with `init.sh`. MCP server installation is disconnected. init.sh uses SSH URLs while quick-install already uses HTTPS.

## Solution

1. Fold `quick-install.sh` into `init.sh --quick` (add submodule + run init)
2. Add `init.sh --uninstall` for clean removal
3. Add `init.sh --mcp` to optionally install MCP server
4. Default to HTTPS URLs
5. Update documentation to clearly present two paths: init.md (agentic) and init.sh (script)
6. Deprecate `quick-install.sh` with a redirect to `init.sh --quick`

## Deliverables

1. Update `bin/init.sh` with `--quick`, `--uninstall`, `--mcp` flags
2. Update `bin/quick-install.sh` to emit deprecation warning and delegate to `init.sh --quick`
3. Update `init.md` to reference MCP installation
4. Update `docs/configuration/repository-setup.md` with two-path model
5. Run tests

## Testing

- Existing policy engine tests must pass
- Verify new flags are parsed correctly
