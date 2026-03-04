# Plan: Migrate governance CLI to hardened Go binary — Initial Scaffold

**Issue:** #743
**Type:** feat
**Phase:** Scaffold only (no full migration)

## Objective

Create the initial Go project scaffold for the `dark-governance` CLI binary. This establishes the module structure, CLI framework (cobra), build-time version injection, and go:embed declarations for governance content.

## Files to Create

1. `src/go.mod` — Go module definition
2. `src/cmd/dark-governance/main.go` — CLI entry point
3. `src/cmd/dark-governance/root.go` — root cobra command with --version, --json, --config flags
4. `src/cmd/dark-governance/version_cmd.go` — version subcommand (text + JSON output)
5. `src/cmd/dark-governance/init_cmd.go` — init subcommand stub
6. `src/internal/version/version.go` — build-time version injection via ldflags
7. `src/internal/embed/embed.go` — go:embed declarations for governance content
8. `src/internal/embed/embed_test.go` — validates embedded content present
9. `src/internal/version/version_test.go` — version formatting tests
10. `src/Makefile` — build, test, lint, vet targets
11. `src/.golangci.yml` — linter configuration

## Acceptance Criteria

- `go build ./cmd/dark-governance/` succeeds
- `go test ./...` passes
- Binary outputs version info with `--version` and `version` subcommand
- JSON output available via `--json` flag on version subcommand
- Makefile targets: build, test, lint, vet, clean, prepare-embed
- Minimum Go version: 1.22

## Out of Scope

- Actual governance logic migration
- CI/CD pipeline for Go builds
- Release automation
- Platform-specific packaging
