#!/usr/bin/env bash
# install.sh — Download and install the dark-governance CLI binary.
#
# Usage:
#   curl -sSfL https://raw.githubusercontent.com/convergent-systems-co/dark-forge/main/src/scripts/install.sh | sh
#   curl -sSfL ... | VERSION=0.1.0 sh
#   curl -sSfL ... | INSTALL_DIR=/usr/local/bin sh
#
# Environment variables:
#   VERSION          — Specific version to install (default: latest)
#   INSTALL_DIR      — Installation directory (default: /usr/local/bin)
#   CHECKSUM_VERIFY  — Set to 0 to skip checksum verification (default: 1)
#   COSIGN_VERIFY    — Set to 1 to verify cosign signature (default: 0)

set -euo pipefail

REPO="convergent-systems-co/dark-forge"
BINARY_NAME="dark-governance"
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"
CHECKSUM_VERIFY="${CHECKSUM_VERIFY:-1}"
COSIGN_VERIFY="${COSIGN_VERIFY:-0}"

# Detect OS
detect_os() {
  local os
  os="$(uname -s)"
  case "$os" in
    Linux)  echo "linux" ;;
    Darwin) echo "darwin" ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *)
      echo "Error: unsupported operating system: $os" >&2
      echo "Supported: Linux, macOS (Darwin), Windows (via MSYS/Cygwin)" >&2
      exit 1
      ;;
  esac
}

# Detect architecture
detect_arch() {
  local arch
  arch="$(uname -m)"
  case "$arch" in
    x86_64|amd64) echo "amd64" ;;
    arm64|aarch64) echo "arm64" ;;
    *)
      echo "Error: unsupported architecture: $arch" >&2
      echo "Supported: x86_64/amd64, arm64/aarch64" >&2
      exit 1
      ;;
  esac
}

# Get latest version from GitHub API
get_latest_version() {
  local version
  version="$(curl -sSf "https://api.github.com/repos/${REPO}/releases/latest" \
    | grep '"tag_name"' \
    | sed -E 's/.*"tag_name": *"([^"]+)".*/\1/' \
    | sed 's/^v//')"

  if [ -z "$version" ]; then
    echo "Error: could not determine latest version" >&2
    echo "Check https://github.com/${REPO}/releases for available versions" >&2
    exit 1
  fi
  echo "$version"
}

# Verify SHA-256 checksum
verify_checksum() {
  local archive_path="$1"
  local checksums_path="$2"
  local archive_name="$3"

  if [ "$CHECKSUM_VERIFY" = "0" ]; then
    echo "Skipping checksum verification (CHECKSUM_VERIFY=0)"
    return 0
  fi

  if [ ! -f "$checksums_path" ]; then
    echo "Error: checksums file not available; cannot verify archive integrity" >&2
    echo "Set CHECKSUM_VERIFY=0 to bypass checksum verification (not recommended)." >&2
    exit 1
  fi

  # Extract expected checksum for our archive using exact filename match in second column
  local expected
  local matches
  matches="$(awk -v name="$archive_name" '$2 == name {print $1}' "$checksums_path")"

  if [ -z "$matches" ]; then
    echo "Error: no checksum found for ${archive_name} in checksums file" >&2
    exit 1
  fi

  # Ensure exactly one checksum entry was found
  if [ "$(printf '%s\n' "$matches" | wc -l | tr -d ' ')" -ne 1 ]; then
    echo "Error: multiple checksum entries found for ${archive_name} in checksums file" >&2
    exit 1
  fi

  expected="$matches"

  # Calculate actual checksum
  local actual
  if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$archive_path" | awk '{print $1}')"
  elif command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "$archive_path" | awk '{print $1}')"
  else
    echo "Warning: neither sha256sum nor shasum found, skipping checksum verification" >&2
    return 0
  fi

  if [ "$expected" != "$actual" ]; then
    echo "Error: checksum verification failed!" >&2
    echo "  Expected: $expected" >&2
    echo "  Actual:   $actual" >&2
    echo "" >&2
    echo "The downloaded archive may be corrupted or tampered with." >&2
    echo "Set CHECKSUM_VERIFY=0 to bypass (not recommended)." >&2
    exit 1
  fi

  echo "Checksum verified: $actual"
}

# Verify cosign signature (stub — requires cosign to be installed)
verify_cosign() {
  local archive_path="$1"
  local version="$2"

  if [ "$COSIGN_VERIFY" != "1" ]; then
    return 0
  fi

  if ! command -v cosign >/dev/null 2>&1; then
    echo "Warning: cosign not found, skipping signature verification" >&2
    echo "  Install cosign: https://docs.sigstore.dev/cosign/installation/" >&2
    echo "  Or set COSIGN_VERIFY=0 to skip" >&2
    return 0
  fi

  local sig_url="https://github.com/${REPO}/releases/download/v${version}/${BINARY_NAME}_${version}.sig"

  echo "Checking for cosign signature..."
  echo "Note: COSIGN_VERIFY=1 is a placeholder. Full cosign signature verification" >&2
  echo "is not yet implemented. The binary integrity relies on CHECKSUM_VERIFY." >&2
  echo "See: https://github.com/${REPO}/blob/main/docs/guides/installation.md" >&2
}

main() {
  local os arch version archive_name download_url checksums_url tmp_dir

  os="$(detect_os)"
  arch="$(detect_arch)"

  if [ -n "${VERSION:-}" ]; then
    version="${VERSION#v}"
  else
    echo "Fetching latest version..."
    version="$(get_latest_version)"
  fi

  echo "Installing ${BINARY_NAME} v${version} (${os}/${arch})..."

  archive_name="${BINARY_NAME}_${version}_${os}_${arch}.tar.gz"
  download_url="https://github.com/${REPO}/releases/download/v${version}/${archive_name}"
  checksums_url="https://github.com/${REPO}/releases/download/v${version}/checksums.txt"

  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT

  echo "Downloading ${download_url}..."
  if ! curl -sSfL -o "${tmp_dir}/${archive_name}" "$download_url"; then
    echo "Error: failed to download ${download_url}" >&2
    echo "Check that version v${version} exists at https://github.com/${REPO}/releases" >&2
    exit 1
  fi

  # Download checksums (best-effort — don't fail if not available)
  curl -sSfL -o "${tmp_dir}/checksums.txt" "$checksums_url" 2>/dev/null || true

  # Verify checksum
  verify_checksum "${tmp_dir}/${archive_name}" "${tmp_dir}/checksums.txt" "$archive_name"

  # Verify cosign signature (if enabled)
  verify_cosign "${tmp_dir}/${archive_name}" "$version"

  echo "Extracting..."
  tar -xzf "${tmp_dir}/${archive_name}" -C "$tmp_dir"

  echo "Installing to ${INSTALL_DIR}/${BINARY_NAME}..."
  if [ -w "$INSTALL_DIR" ]; then
    mv "${tmp_dir}/${BINARY_NAME}" "${INSTALL_DIR}/${BINARY_NAME}"
  else
    echo "Note: ${INSTALL_DIR} requires elevated permissions, using sudo..."
    sudo mv "${tmp_dir}/${BINARY_NAME}" "${INSTALL_DIR}/${BINARY_NAME}"
  fi
  chmod +x "${INSTALL_DIR}/${BINARY_NAME}"

  echo ""
  echo "Successfully installed ${BINARY_NAME} v${version}"
  "${INSTALL_DIR}/${BINARY_NAME}" version
}

main "$@"
