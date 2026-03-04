# Go Instructions

Extends the base AI instructions with Go-specific conventions.

## Naming

- Exported: PascalCase (`NewServer`, `ErrNotFound`). Unexported: camelCase (`parseHeader`)
- Acronyms: all-caps when exported (`HTTPClient`, `ID`), all-lower when unexported (`httpClient`)
- Packages: lowercase, single word, no underscores (`strconv`, not `str_conv`)
- Interfaces: method name + `-er` suffix for single-method (`Reader`, `Writer`); behavior name for multi-method
- No `I` prefix on interfaces, no `Get` prefix on getters (`obj.Name()`, not `obj.GetName()`)
- Receivers: short 1-2 letter abbreviations, consistent across methods (`func (s *Server)`)
- Constructors: `NewTypeName()` returns `*TypeName`; `New()` if the package has one main type
- Error variables: `Err` prefix (`ErrNotFound`), error types: suffix with `Error`

## Code Style

- `gofmt` is non-negotiable -- run on every save
- Group imports: stdlib, blank line, third-party, blank line, internal
- Prefer early return over nested if/else
- Keep functions short and focused
- Avoid `init()` functions -- they make testing hard and create hidden dependencies
- Use `const` blocks with `iota` for enumerations
- Use named return values sparingly and only in short functions
- Be consistent with pointer vs value receivers per type

## Error Handling

- Always add context when wrapping: `fmt.Errorf("opening config %s: %w", path, err)`
- Use `%w` to wrap (allows `errors.Is`/`errors.As`), `%v` to obscure
- Define sentinel errors at package level: `var ErrNotFound = errors.New("not found")`
- Use custom error types when callers need to extract structured data
- Handle errors at the appropriate level -- don't log AND return
- Error messages: lowercase, no trailing punctuation, no "failed to" prefix
- Never ignore errors silently; if intentional, `_ = fn()` with a comment

## Concurrency

- Always pass `context.Context` as the first parameter; never store in structs
- Never start a goroutine without knowing how it will stop
- Use `errgroup.WithContext` for fan-out work with error collection
- Use channels for communication, mutexes for state protection
- `select` with `ctx.Done()` to prevent goroutine leaks
- Sender closes channels; receiver checks with `range` or `, ok`
- Use `sync.Once` for lazy initialization, `sync.Map` only for stable-key-set read-heavy maps

## Interfaces

- Accept interfaces, return structs
- Define interfaces where they are consumed, not where they are implemented
- Keep interfaces small: 1-2 methods is ideal, rarely exceed 3
- Don't define interfaces preemptively -- wait until you need to mock or have multiple implementations
- Use standard library interfaces when possible (`io.Reader`, `io.Writer`, `fmt.Stringer`, `error`)

## Testing

- Table-driven tests with `t.Run()` subtests
- Use `t.Helper()` in test helper functions
- Use `t.Cleanup()` for teardown
- Use `testdata/` directory for fixtures
- Black-box tests (`package foo_test`) for public API; white-box (`package foo`) when needed
- Use `testing.Short()` to skip slow tests: `if testing.Short() { t.Skip("...") }`
- Use `go-cmp` for deep struct comparison

## Common Pitfalls

- Nil maps panic on write -- always initialize with `make()`
- Sub-slices share underlying arrays -- use full slice expression `a[1:3:3]` to limit capacity
- `defer` in loops accumulates until function returns -- wrap in a closure
- `range` over maps is non-deterministic -- never depend on iteration order
- `time.After` in select loops leaks timers -- use `time.NewTimer` with `Stop()`/`Reset()`

## Modules

- One `go.mod` per repository unless there's a compelling reason for multi-module
- Run `go mod tidy` before committing
- Commit `go.sum` to version control
- Use `go.work` for multi-module local development
- Remove `replace` directives before merging

---

*Extends .ai/instructions.md with Go-specific conventions.*
