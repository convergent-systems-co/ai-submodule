// Package lockfile manages the .dark-governance.lock file that pins
// the governance binary version and content hash for a consuming repository.
//
// The lockfile ensures reproducible CI — the version recorded at init time
// is the version CI downloads, and the content hash validates integrity.
package lockfile

import (
	"encoding/json"
	"fmt"
	"os"
	"time"
)

// DefaultPath is the default lockfile location relative to the repo root.
const DefaultPath = ".dark-governance.lock"

// LockInfo holds the data written to the lockfile.
type LockInfo struct {
	// Version is the semantic version of the governance binary (e.g., "0.1.0").
	Version string `json:"version"`

	// ContentHash is the SHA-256 hash of all embedded governance content.
	// Format: "sha256:<hex>"
	ContentHash string `json:"content_hash"`

	// InstalledAt is the RFC 3339 timestamp of when the lockfile was written.
	InstalledAt string `json:"installed_at"`

	// BinaryPath is the path to the governance binary that created this lockfile.
	BinaryPath string `json:"binary_path,omitempty"`
}

// Write writes a lockfile to the given path.
func Write(path string, info LockInfo) error {
	if info.InstalledAt == "" {
		info.InstalledAt = time.Now().UTC().Format(time.RFC3339)
	}

	data, err := json.MarshalIndent(info, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal lockfile: %w", err)
	}

	// Append newline for POSIX compliance
	data = append(data, '\n')

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write lockfile %s: %w", path, err)
	}

	return nil
}

// Read reads a lockfile from the given path.
func Read(path string) (LockInfo, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return LockInfo{}, fmt.Errorf("failed to read lockfile %s: %w", path, err)
	}

	var info LockInfo
	if err := json.Unmarshal(data, &info); err != nil {
		return LockInfo{}, fmt.Errorf("failed to parse lockfile %s: %w", path, err)
	}

	return info, nil
}

// Verify reads the lockfile at path and checks that the content hash matches
// the provided currentHash. Returns nil if valid, an error describing the
// mismatch otherwise.
func Verify(path string, currentHash string) error {
	info, err := Read(path)
	if err != nil {
		return err
	}

	if info.ContentHash != currentHash {
		return fmt.Errorf(
			"lockfile integrity check failed: lockfile content_hash=%s, binary content_hash=%s",
			info.ContentHash, currentHash,
		)
	}

	return nil
}

// Exists returns true if a lockfile exists at the given path.
func Exists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}
