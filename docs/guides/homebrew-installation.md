# Homebrew Installation Guide

Install the `dark-governance` CLI via Homebrew on macOS or Linux.

## Prerequisites

- [Homebrew](https://brew.sh/) installed
- GitHub personal access token with `repo` scope (required for private repo)

## Authentication Setup

The convergent-systems-co/dark-forge repository is private. Homebrew needs a GitHub
token to access the tap and download bottles.

### Create a Token

1. Go to [GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Select scopes:
   - `repo` (full private repo access)
   - `read:packages` (download bottles from GitHub Packages)
4. Set expiration to 90 days (rotate quarterly)
5. Copy the token

### Store the Token

**Option A: Environment variable (simple)**

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export HOMEBREW_GITHUB_API_TOKEN="ghp_your_token_here"
```

Then reload:

```bash
source ~/.zshrc
```

**Option B: macOS Keychain (recommended)**

```bash
# Store the token
security add-generic-password \
  -a "$USER" \
  -s "homebrew-github-token" \
  -w "ghp_your_token_here"

# Add retrieval to shell profile (~/.zshrc)
export HOMEBREW_GITHUB_API_TOKEN=$(security find-generic-password \
  -a "$USER" \
  -s "homebrew-github-token" \
  -w 2>/dev/null)
```

### Verify Authentication

```bash
# Should return your GitHub username
gh auth status
```

## Installation

### Step 1: Add the Tap

```bash
brew tap SET-Apps/tap
```

This adds the `SET-Apps/tap` repository as a Homebrew tap. Homebrew's
standard naming convention auto-discovers `SET-Apps/homebrew-tap`.

### Step 2: Install

```bash
brew install dark-governance
```

If prebuilt bottles are available for your platform, Homebrew downloads
the binary directly. Otherwise, it falls back to building from source
(requires Go 1.22+).

### Step 3: Verify

```bash
dark-governance version
```

Expected output:

```
dark-governance version 0.x.x (commit: abc1234, built: 2026-03-03T12:00:00Z)
```

## Upgrading

```bash
# Update Homebrew and all taps
brew update

# Upgrade dark-governance
brew upgrade dark-governance

# Verify the new version
dark-governance version
```

## Uninstalling

```bash
# Remove the formula
brew uninstall dark-governance

# Remove the tap (optional)
brew untap SET-Apps/tap
```

## Pinning a Version

To prevent automatic upgrades:

```bash
brew pin dark-governance
```

To unpin:

```bash
brew unpin dark-governance
```

## Building from Source

If bottles are unavailable or you want a source build:

```bash
brew install --build-from-source dark-governance
```

This requires Go 1.22+ as a build dependency.

## Troubleshooting

### Error: 403 Forbidden

**Cause:** Missing or invalid GitHub token.

```bash
# Verify token is set (checks non-empty without printing the value)
[ -n "$HOMEBREW_GITHUB_API_TOKEN" ] && echo "Token is set" || echo "Token is NOT set"

# Test token access
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: token $HOMEBREW_GITHUB_API_TOKEN" \
  https://api.github.com/repos/convergent-systems-co/dark-forge
```

**Fix:** Regenerate your token and ensure it has `repo` scope.

### Error: 404 Not Found

**Cause:** Token lacks `repo` scope or you do not have access to the
private repository.

**Fix:** Verify your GitHub account has read access to convergent-systems-co/dark-forge.
Contact your org admin if needed.

### Error: Tap Already Tapped

```bash
# Remove and re-add
brew untap SET-Apps/tap
brew tap SET-Apps/tap
```

### Error: No Bottle Available

**Cause:** Bottles have not been built for your platform/OS version.

**Fix:** Install from source:

```bash
brew install --build-from-source dark-governance
```

### Error: SHA256 Mismatch

**Cause:** Bottle checksum does not match the formula. Usually means the
formula is out of date.

```bash
# Force update
brew update --force
brew reinstall dark-governance
```

### Slow Install (Building from Source)

If Homebrew is compiling from source instead of using a bottle:

1. Check if bottles exist: `brew info dark-governance`
2. Ensure your macOS version matches a supported bottle platform
3. Update Homebrew: `brew update`

### Token Rotation

Tokens should be rotated quarterly (every 90 days):

1. Generate a new token on GitHub
2. Update your stored token:
   - **Environment variable:** Edit `~/.zshrc`
   - **Keychain:** `security delete-generic-password -a "$USER" -s "homebrew-github-token"` then re-add
3. Verify: `brew update`

### Clearing Homebrew Cache

If you encounter stale package issues:

```bash
brew cleanup -s dark-governance
```

## Platform Support

| Platform | Architecture | Bottle | Source Build |
|----------|-------------|--------|-------------|
| macOS Sonoma+ | arm64 (Apple Silicon) | Yes | Yes |
| macOS Sonoma+ | x86_64 (Intel) | Yes | Yes |
| Linux | x86_64 | Yes | Yes |
| Linux | arm64 | No | Yes |
| Windows | x86_64 | No | No (use WSL) |

## For Maintainers

Formula lives in the dedicated [SET-Apps/homebrew-tap](https://github.com/SET-Apps/homebrew-tap) repository.
GoReleaser and the homebrew-bottle workflow update it automatically on each release.
