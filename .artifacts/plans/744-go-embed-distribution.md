# Plan: Implement go:embed governance distribution model

**Issue:** #744
**Type:** feat
**Phase:** Core implementation (subset of full migration)
**Depends on:** #743 (Go binary scaffold — merged in PR #752)

## Objective

Expand the Go binary scaffold to actually embed governance content and provide working `init`, `verify`, and `engine run` subcommands. This transforms the binary from a scaffold into a functional distribution vehicle.

## Scope

### In Scope
1. Expand `go:embed` to bundle all governance content (policies, schemas, prompts, personas, commands, workflows, templates, instructions)
2. Update Makefile `prepare-embed` to copy full governance content tree
3. Expand `init` subcommand to extract embedded content to consuming repos
4. Add lockfile support (`.dark-governance.lock`) with version + sha256
5. Add `verify` subcommand to check lockfile integrity
6. Add `engine run` subcommand stub (reads emissions, evaluates against embedded policy)
7. Add `engine status` subcommand

### Out of Scope
- `migrate` subcommand (separate PR — converts submodule repos)
- brew/winget/npx packaging (#738)
- Home cache / `~/.ai/` (#758)
- `update` subcommand
- Full Go policy engine port (engine run is a stub that validates structure)

## Architecture

### Embed Layer (`src/internal/embed/`)

The embed package uses `//go:embed` with the `all:` prefix to capture the full `_content/` tree. Content is organized as:

```
_content/
├── policy/              ← governance/policy/*.yaml (not future/)
├── schemas/             ← governance/schemas/*.json (not future/, examples/)
├── prompts/
│   └── reviews/         ← governance/prompts/reviews/*.md
├── personas/
│   └── agentic/         ← governance/personas/agentic/*.md
├── commands/            ← governance/commands/*.md
├── templates/
│   ├── workflows/       ← governance/templates/workflows/*.yml
│   ├── languages/       ← governance/templates/languages/*/
│   └── panels/          ← governance/templates/panels/
├── instructions.md      ← root instructions.md
└── CLAUDE.md            ← root CLAUDE.md
```

Accessor functions:
- `GovernanceFS() embed.FS` — raw embedded filesystem
- `ReadFile(path string) ([]byte, error)` — read single file
- `ReadDir(path string) ([]fs.DirEntry, error)` — list directory
- `ListPolicies() []string` — list available policy profiles
- `ListSchemas() []string` — list available schemas
- `GetPolicy(name string) ([]byte, error)` — get policy by name
- `GetSchema(name string) ([]byte, error)` — get schema by name
- `ContentHash() string` — sha256 of all embedded content (deterministic)

### Init Subcommand (`src/cmd/dark-governance/init_cmd.go`)

Extracts embedded content to the current working directory:

| Extracted To | Source (embedded) | Condition |
|---|---|---|
| `.github/workflows/dark-factory-governance.yml` | `templates/workflows/pipeline.yml` | Always |
| `CLAUDE.md` | `instructions.md` | Only if missing |
| `.claude/commands/*.md` | `commands/*.md` | Always (overwrite) |
| `project.yaml` | `templates/languages/{detected}/project.yaml` | Only if missing |
| `.artifacts/plans/.gitkeep` | N/A | Created empty |
| `.artifacts/panels/.gitkeep` | N/A | Created empty |
| `.artifacts/checkpoints/.gitkeep` | N/A | Created empty |
| `.artifacts/emissions/.gitkeep` | N/A | Created empty |
| `.dark-governance.lock` | Generated | Always |

Flags:
- `--dry-run` — show what would be extracted without writing
- `--force` — overwrite existing files (default: skip existing)
- `--language <lang>` — language hint for project.yaml template selection

### Lockfile (`src/internal/lockfile/`)

New package. Schema:

```json
{
  "version": "0.1.0",
  "content_hash": "sha256:abc123...",
  "installed_at": "2026-03-03T14:30:00Z",
  "binary_path": "/usr/local/bin/dark-governance"
}
```

Functions:
- `Write(path string, info LockInfo) error`
- `Read(path string) (LockInfo, error)`
- `Verify(path string, currentHash string) error`

### Verify Subcommand (`src/cmd/dark-governance/verify_cmd.go`)

Reads `.dark-governance.lock` and compares `content_hash` against the running binary's embedded content hash. Exits 0 if match, 1 if mismatch.

Flags:
- `--lockfile <path>` — custom lockfile path (default: `.dark-governance.lock`)

### Engine Run Subcommand (`src/cmd/dark-governance/engine_cmd.go`)

Stub implementation that:
1. Reads emissions from `--emissions-dir` (default: `.artifacts/emissions/`)
2. Validates emission files against embedded `panel-output.schema.json`
3. Loads the policy profile from embedded content (default: `default.yaml`)
4. Outputs a structural validation result (not full policy evaluation yet)

```bash
dark-governance engine run --emissions-dir .artifacts/emissions/ --profile default
dark-governance engine status
```

### Engine Status Subcommand

Reports:
- Embedded content version
- Available policy profiles
- Available schemas
- Content hash

## Files to Create/Modify

### New Files
1. `src/internal/lockfile/lockfile.go` — lockfile read/write/verify
2. `src/internal/lockfile/lockfile_test.go` — lockfile tests
3. `src/cmd/dark-governance/verify_cmd.go` — verify subcommand
4. `src/cmd/dark-governance/engine_cmd.go` — engine run/status subcommands

### Modified Files
5. `src/internal/embed/embed.go` — expand with accessor functions, content hash
6. `src/internal/embed/embed_test.go` — validate actual governance content
7. `src/cmd/dark-governance/init_cmd.go` — full implementation
8. `src/cmd/dark-governance/root.go` — register new commands
9. `src/Makefile` — expand `prepare-embed` target
10. `src/go.mod` — add `gopkg.in/yaml.v3` dependency (for policy parsing)

## Implementation Order

1. Update Makefile `prepare-embed` to copy full governance content
2. Expand `embed.go` with accessor functions and content hash
3. Update `embed_test.go` to validate governance content present
4. Create `lockfile` package
5. Expand `init_cmd.go` with full extraction logic
6. Create `verify_cmd.go`
7. Create `engine_cmd.go` with run and status subcommands
8. Update `root.go` to register all commands
9. Run `make prepare-embed && make build && make test`

## Testing Strategy

- `embed_test.go`: Validate all expected directories/files are present in embedded FS after `prepare-embed`
- `lockfile_test.go`: Write/read/verify round-trip, tamper detection
- Integration: `make prepare-embed && make build` succeeds, binary runs `init --dry-run`, `verify`, `engine status`

## Acceptance Criteria

- [ ] `make prepare-embed && make build` succeeds
- [ ] `make test` passes all Go tests
- [ ] `./dark-governance init --dry-run` shows what would be extracted
- [ ] `./dark-governance verify` validates lockfile
- [ ] `./dark-governance engine status` shows embedded content info
- [ ] `./dark-governance engine run --emissions-dir <dir>` validates emissions
- [ ] Embedded content matches source `governance/` directory
- [ ] Content hash is deterministic (same input = same hash)

## Risks

- **Embed size**: Full governance content may be large. Mitigated by excluding docs/, tests, Python engine source, future/ subdirectories.
- **go:embed limitations**: Cannot use `..` in embed paths — Makefile must copy content into `_content/` first. Already handled by scaffold.
- **YAML dependency**: Adding `gopkg.in/yaml.v3` increases binary size slightly. Acceptable for policy parsing.
