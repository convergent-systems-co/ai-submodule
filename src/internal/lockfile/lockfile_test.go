package lockfile

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestWriteAndRead(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, ".dark-governance.lock")

	info := LockInfo{
		Version:     "0.1.0",
		ContentHash: "sha256:abc123def456",
		InstalledAt: "2026-03-03T14:30:00Z",
		BinaryPath:  "/usr/local/bin/dark-governance",
	}

	if err := Write(path, info); err != nil {
		t.Fatalf("Write failed: %v", err)
	}

	// Verify file exists
	if !Exists(path) {
		t.Fatal("lockfile does not exist after Write")
	}

	// Read it back
	got, err := Read(path)
	if err != nil {
		t.Fatalf("Read failed: %v", err)
	}

	if got.Version != info.Version {
		t.Errorf("version: got %q, want %q", got.Version, info.Version)
	}
	if got.ContentHash != info.ContentHash {
		t.Errorf("content_hash: got %q, want %q", got.ContentHash, info.ContentHash)
	}
	if got.InstalledAt != info.InstalledAt {
		t.Errorf("installed_at: got %q, want %q", got.InstalledAt, info.InstalledAt)
	}
	if got.BinaryPath != info.BinaryPath {
		t.Errorf("binary_path: got %q, want %q", got.BinaryPath, info.BinaryPath)
	}
}

func TestWriteAutoTimestamp(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, ".dark-governance.lock")

	info := LockInfo{
		Version:     "0.1.0",
		ContentHash: "sha256:abc123",
	}

	if err := Write(path, info); err != nil {
		t.Fatalf("Write failed: %v", err)
	}

	got, err := Read(path)
	if err != nil {
		t.Fatalf("Read failed: %v", err)
	}

	if got.InstalledAt == "" {
		t.Error("expected auto-generated installed_at timestamp")
	}
}

func TestVerifySuccess(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, ".dark-governance.lock")

	hash := "sha256:abc123def456"
	info := LockInfo{
		Version:     "0.1.0",
		ContentHash: hash,
	}

	if err := Write(path, info); err != nil {
		t.Fatalf("Write failed: %v", err)
	}

	if err := Verify(path, hash); err != nil {
		t.Errorf("Verify failed for matching hash: %v", err)
	}
}

func TestVerifyMismatch(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, ".dark-governance.lock")

	info := LockInfo{
		Version:     "0.1.0",
		ContentHash: "sha256:abc123",
	}

	if err := Write(path, info); err != nil {
		t.Fatalf("Write failed: %v", err)
	}

	err := Verify(path, "sha256:different_hash")
	if err == nil {
		t.Fatal("expected error for mismatched hash")
	}
	if !strings.Contains(err.Error(), "integrity check failed") {
		t.Errorf("expected integrity check error, got: %v", err)
	}
}

func TestVerifyMissingFile(t *testing.T) {
	err := Verify("/nonexistent/path/.dark-governance.lock", "sha256:abc")
	if err == nil {
		t.Fatal("expected error for missing lockfile")
	}
}

func TestReadInvalidJSON(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, ".dark-governance.lock")

	if err := os.WriteFile(path, []byte("not json"), 0644); err != nil {
		t.Fatalf("failed to write test file: %v", err)
	}

	_, err := Read(path)
	if err == nil {
		t.Fatal("expected error for invalid JSON")
	}
}

func TestExistsReturnsFalse(t *testing.T) {
	if Exists("/definitely/not/a/real/path") {
		t.Error("Exists returned true for nonexistent path")
	}
}

func TestWritePOSIXNewline(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, ".dark-governance.lock")

	info := LockInfo{
		Version:     "0.1.0",
		ContentHash: "sha256:abc123",
	}

	if err := Write(path, info); err != nil {
		t.Fatalf("Write failed: %v", err)
	}

	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("failed to read file: %v", err)
	}

	if !strings.HasSuffix(string(data), "\n") {
		t.Error("lockfile does not end with newline (POSIX compliance)")
	}
}
