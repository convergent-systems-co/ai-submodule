# Plan: Home-Rooted Governance Engine (#758)

## Objective

Implement a home directory cache mechanism (`~/.ai/`) for the `dark-governance` binary so that governance content can be extracted once and shared across repos, eliminating the need for the git submodule in consuming repositories.

## Scope

### In Scope
1. `internal/home` package — home directory management, version directories, file resolution
2. `install` subcommand — extracts embedded content to `~/.ai/versions/<version>/`
3. `update` subcommand — stub for future version checking
4. File resolution precedence: repo-local -> home cache -> embedded fallback
5. `DARK_GOVERNANCE_HOME` env var override
6. XDG compliance (`$XDG_DATA_HOME/dark-governance`)
7. CI mode (`install --ci` uses `$RUNNER_TEMP` or `$HOME/.ai/`)
8. Update `init` subcommand to use home cache resolution when available

### Out of Scope
- brew/winget/npx packaging (#738)
- `migrate` subcommand (future)
- External state storage (#757)

## Design

### Home Directory Structure

```
~/.ai/                          # Default, overridden by DARK_GOVERNANCE_HOME or XDG_DATA_HOME
├── versions/
│   └── <version>/
│       ├── governance/         # Policy, schemas, prompts, personas
│       ├── templates/          # Workflow + language templates
│       ├── commands/           # Slash commands
│       ├── instructions.md     # CLAUDE.md source
│       └── .metadata.json      # Version metadata (hash, installed_at)
└── config.yaml                 # Future: global user preferences
```

### Resolution Precedence

`Resolve(path string) -> (data []byte, source string, err error)`

1. **Repo-local** `.ai/` directory (submodule backward compatibility)
2. **Home cache** `~/.ai/versions/<locked-version>/`
3. **Embedded** fallback from `go:embed`

### CI Detection

`IsCI()` returns true when any of: `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, `JENKINS_URL`, `TF_BUILD`, `BUILDKITE` env vars are set.

In CI mode, `install --ci` writes to `$RUNNER_TEMP/.ai/` if `RUNNER_TEMP` is set, otherwise `$HOME/.ai/`.

## Files

### New Files
| File | Purpose |
|------|---------|
| `src/internal/home/home.go` | Home directory management, resolution, CI detection |
| `src/internal/home/home_test.go` | Unit tests with temp dirs |
| `src/cmd/dark-governance/install_cmd.go` | `install` subcommand |
| `src/cmd/dark-governance/update_cmd.go` | `update` subcommand (stub) |

### Modified Files
| File | Change |
|------|--------|
| `src/cmd/dark-governance/root.go` | Register `install` and `update` commands |
| `src/cmd/dark-governance/init_cmd.go` | Use home cache resolution for content when available |

## Testing

```bash
cd src && make prepare-embed && make build && make test
```

All existing tests must continue to pass. New tests cover:
- `DefaultHome()` with and without env overrides
- `VersionDir()` path construction
- `Install()` content extraction to temp dir
- `Resolve()` precedence (repo-local > home cache > embedded)
- `IsCI()` detection
- Install subcommand integration

## Acceptance Criteria

- [ ] `dark-governance install` creates `~/.ai/versions/<version>/` with governance content
- [ ] `DARK_GOVERNANCE_HOME` overrides default location
- [ ] `XDG_DATA_HOME` is respected when set
- [ ] `install --ci` works in CI environments
- [ ] File resolution follows precedence: repo-local -> home cache -> embedded
- [ ] All tests pass (`make prepare-embed && make build && make test`)
- [ ] Backward compatibility: repos with `.ai/` submodule work unchanged
