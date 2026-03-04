# Installation Guide

This guide covers installing and configuring the `dark-governance` CLI binary.

## Quick Install

### curl (macOS / Linux)

```bash
curl -sSfL https://raw.githubusercontent.com/convergent-systems-co/dark-forge/main/src/scripts/install.sh | sh
```

Pin a specific version:

```bash
curl -sSfL https://raw.githubusercontent.com/convergent-systems-co/dark-forge/main/src/scripts/install.sh | VERSION=0.1.0 sh
```

### Manual Download

1. Download the archive for your platform from [Releases](https://github.com/convergent-systems-co/dark-forge/releases)
2. Verify the checksum: `sha256sum dark-governance_*.tar.gz` and compare with `checksums.txt`
3. Extract: `tar -xzf dark-governance_*.tar.gz`
4. Move to PATH: `mv dark-governance /usr/local/bin/`

## CI Installation

For GitHub Actions, pin the version explicitly:

```yaml
- name: Install dark-governance
  run: |
    curl -sSfL https://raw.githubusercontent.com/convergent-systems-co/dark-forge/main/src/scripts/install.sh \
      | VERSION=0.1.0 INSTALL_DIR=$RUNNER_TEMP sh
    echo "$RUNNER_TEMP" >> $GITHUB_PATH

- name: Verify integrity
  run: dark-governance verify
```

Important: in CI, always pin `VERSION` to a specific release to avoid unexpected upgrades. When `VERSION` is unset, the installer fetches and installs the latest released version.

## Post-Install Setup

### 1. Install governance content

```bash
dark-governance install
```

This extracts governance content (policies, schemas, prompts) to `~/.ai/versions/<version>/`.

### 2. Initialize a repository

```bash
cd /path/to/your/repo
dark-governance init
```

This creates:
- `.github/workflows/dark-factory-governance.yml` (CI workflow)
- `.dark-governance.lock` (version pin)
- `.artifacts/` directories
- `CLAUDE.md` (if not present)

### 3. Set up Python bridge (optional)

If you need to run the Python policy engine:

```bash
dark-governance deps setup
```

This creates a virtual environment at `~/.ai/venv/` with the required Python dependencies.

### 4. Install MCP server (optional)

For IDE integration with Claude or Cursor:

```bash
dark-governance mcp install
dark-governance mcp install --target claude    # Claude only
dark-governance mcp install --target cursor    # Cursor only
```

### 5. Generate configuration

```bash
dark-governance configure --non-interactive
```

Or edit `project.yaml` manually.

## Verification

After installation, verify the binary matches the lockfile:

```bash
dark-governance verify
```

Check engine status:

```bash
dark-governance engine status
```

## Offline / Airgapped Install

For environments without internet access:

1. On a connected machine, download the archive and checksums:
   ```bash
   VERSION=0.1.0
   OS=linux    # or darwin
   ARCH=amd64  # or arm64
   curl -LO "https://github.com/convergent-systems-co/dark-forge/releases/download/v${VERSION}/dark-governance_${VERSION}_${OS}_${ARCH}.tar.gz"
   curl -LO "https://github.com/convergent-systems-co/dark-forge/releases/download/v${VERSION}/checksums.txt"
   ```

2. Transfer both files to the airgapped machine

3. Verify and install:
   ```bash
   sha256sum -c checksums.txt --ignore-missing
   tar -xzf dark-governance_*.tar.gz
   mv dark-governance /usr/local/bin/
   dark-governance install
   ```

## Uninstall

Remove home cache and virtual environment:

```bash
dark-governance uninstall --yes
```

Remove everything including the home directory:

```bash
dark-governance uninstall --all --yes
```

## Supported Platforms

| OS      | Architecture | Status |
|---------|-------------|--------|
| macOS   | amd64       | Supported |
| macOS   | arm64       | Supported |
| Linux   | amd64       | Supported |
| Linux   | arm64       | Supported |
| Windows | amd64       | Experimental (MSYS/Cygwin) |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DARK_GOVERNANCE_HOME` | `~/.ai` | Override home directory location |
| `XDG_DATA_HOME` | (none) | If set, uses `$XDG_DATA_HOME/dark-governance` |
| `VERSION` | latest | Pin installer to a specific version |
| `INSTALL_DIR` | `/usr/local/bin` | Binary installation directory |
| `CHECKSUM_VERIFY` | `1` | Set to `0` to skip checksum verification |
| `COSIGN_VERIFY` | `0` | Set to `1` to verify cosign signature |
