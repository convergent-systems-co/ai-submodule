# End-to-End Testing with VHS

This guide covers how to run and write VHS-based end-to-end tests for the `dark-governance` CLI.

---

## What is VHS?

[VHS](https://github.com/charmbracelet/vhs) is a CLI tool by Charm that records terminal sessions from declarative `.tape` files. Each tape file specifies keystrokes, waits, and output formats. VHS produces GIF/MP4 recordings and can serve as both documentation and regression testing.

## Prerequisites

### Install VHS

```bash
# macOS (Homebrew)
brew install charmbracelet/tap/vhs

# Go install
go install github.com/charmbracelet/vhs@latest

# See full instructions: https://github.com/charmbracelet/vhs#installation
```

### Build the dark-governance binary

```bash
cd src
make build
export PATH="$PWD/bin:$PATH"
```

Verify it works:

```bash
dark-governance version
```

## Running Tests

### Run all E2E tests

```bash
bash tests/e2e/run-tests.sh
```

### Run a specific test

```bash
bash tests/e2e/run-tests.sh install-test
bash tests/e2e/run-tests.sh init-test
```

### List available tests

```bash
bash tests/e2e/run-tests.sh --list
```

### CI mode (skip if VHS not installed)

```bash
bash tests/e2e/run-tests.sh --ci
```

In CI mode, the runner exits 0 if VHS or the binary is not available, rather than failing the pipeline.

### Using Make

From the `src/` directory:

```bash
make test-e2e
```

## Available Tape Files

| Tape | Purpose |
|------|---------|
| `install-test.tape` | Tests `dark-governance install` — extracts governance content to home directory cache |
| `init-test.tape` | Tests `dark-governance init` — scaffolds governance into a consumer repo |

## Writing New Tape Files

### Tape file structure

```tape
# my-test.tape — Short description
#
# What this tests and why.

Output tests/e2e/output/my-test.gif

Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"

# Setup
Type "export TEST_DIR=$(mktemp -d)"
Enter
Sleep 500ms

# Exercise
Type "dark-governance <subcommand> --json"
Enter
Sleep 2s

# Verify
Type "test -f expected-file && echo 'PASS' || echo 'FAIL'"
Enter
Sleep 500ms

# Cleanup
Type "rm -rf $TEST_DIR"
Enter
Sleep 500ms
```

### Key VHS commands

| Command | Description |
|---------|-------------|
| `Type "text"` | Types text into the terminal |
| `Enter` | Presses Enter |
| `Sleep 500ms` | Waits for the specified duration |
| `Output path.gif` | Sets the output file path |
| `Set Shell "bash"` | Sets the shell to use |
| `Set Width 1200` | Sets terminal width in pixels |
| `Set Height 600` | Sets terminal height in pixels |
| `Set Theme "name"` | Sets the color theme |

### Conventions

1. **Self-contained**: Each tape creates its own temp directory and cleans up after itself.
2. **Deterministic**: Use `--json` output where possible to avoid formatting variations.
3. **Verification**: Include explicit PASS/FAIL checks so failures are visible in the recording.
4. **Output directory**: GIF output goes to `tests/e2e/output/` (gitignored).
5. **Comments**: Start each tape with a header comment explaining what it tests.
6. **Environment isolation**: Use `DARK_GOVERNANCE_HOME` to avoid touching the user's real home cache.

### Adding a new tape

1. Create `tests/e2e/my-test.tape` following the conventions above.
2. Run it locally: `vhs tests/e2e/my-test.tape`
3. Verify the GIF in `tests/e2e/output/`.
4. The `run-tests.sh` script will automatically pick up new `.tape` files.

## Output Files

GIF recordings are written to `tests/e2e/output/`. This directory is gitignored — recordings are generated locally and are not committed. To share recordings, embed them in documentation or upload to the docs site.

## Troubleshooting

### "dark-governance: command not found"

Build the binary and add it to your PATH:

```bash
cd src && make build
export PATH="$PWD/bin:$PATH"
```

### "vhs: command not found"

Install VHS per the instructions above, or run with `--ci` to skip gracefully.

### Tape fails but binary works manually

Check that environment variables set in the tape (`DARK_GOVERNANCE_HOME`, `TEST_REPO`) are not conflicting with your shell environment. VHS runs tapes in a fresh shell session.

---

**See also**: [Developer Quickstart](developer-quickstart.md) | [Unified CLI Reference](unified-cli-reference.md)
