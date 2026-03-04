package supplychain

import (
	"os"
	"path/filepath"
	"testing"
)

// setupTestRepo creates a temp directory with critical dirs and files
// matching the expected structure for GenerateManifest.
func setupTestRepo(t *testing.T) string {
	t.Helper()
	root := t.TempDir()

	dirs := []struct {
		path string
		file string
		ext  string
	}{
		{"governance/policy", "default.yaml", ".yaml"},
		{"governance/schemas", "panel-output.schema.json", ".json"},
		{"governance/personas/agentic", "coder.md", ".md"},
		{"governance/prompts/reviews", "code-review.md", ".md"},
	}

	for _, d := range dirs {
		dirPath := filepath.Join(root, d.path)
		os.MkdirAll(dirPath, 0755)
		filePath := filepath.Join(dirPath, d.file)
		os.WriteFile(filePath, []byte("content-of-"+d.file), 0644)
	}

	return root
}

func TestGenerateManifest(t *testing.T) {
	root := setupTestRepo(t)
	v := NewIntegrityVerifier(root)

	manifest, err := v.GenerateManifest()
	if err != nil {
		t.Fatalf("generate: %v", err)
	}

	files, ok := manifest["files"].(map[string]string)
	if !ok {
		t.Fatal("expected files to be map[string]string")
	}
	if len(files) != 4 {
		t.Fatalf("expected 4 files, got %d", len(files))
	}

	fileCount, ok := manifest["file_count"].(int)
	if !ok || fileCount != 4 {
		t.Fatalf("expected file_count=4, got %v", manifest["file_count"])
	}
}

func TestWriteManifest_LoadManifest_RoundTrip(t *testing.T) {
	root := setupTestRepo(t)
	v := NewIntegrityVerifier(root)

	manifestPath := filepath.Join(t.TempDir(), "manifest.json")
	if err := v.WriteManifest(manifestPath); err != nil {
		t.Fatalf("write: %v", err)
	}

	loaded, err := v.LoadManifest(manifestPath)
	if err != nil {
		t.Fatalf("load: %v", err)
	}

	if loaded["version"] != "1.0" {
		t.Fatalf("expected version 1.0, got %v", loaded["version"])
	}
}

func TestVerify_Valid(t *testing.T) {
	root := setupTestRepo(t)
	v := NewIntegrityVerifier(root)

	manifestPath := filepath.Join(t.TempDir(), "manifest.json")
	v.WriteManifest(manifestPath)

	result, err := v.Verify(manifestPath)
	if err != nil {
		t.Fatalf("verify: %v", err)
	}
	if !result.Valid {
		t.Fatalf("expected valid, got failures=%v missing=%v", result.Failures, result.MissingFiles)
	}
	if result.VerifiedFiles != 4 {
		t.Fatalf("expected 4 verified, got %d", result.VerifiedFiles)
	}
}

func TestVerify_TamperedFile(t *testing.T) {
	root := setupTestRepo(t)
	v := NewIntegrityVerifier(root)

	manifestPath := filepath.Join(t.TempDir(), "manifest.json")
	v.WriteManifest(manifestPath)

	// Tamper with a file.
	os.WriteFile(filepath.Join(root, "governance/policy/default.yaml"), []byte("TAMPERED"), 0644)

	result, err := v.Verify(manifestPath)
	if err != nil {
		t.Fatalf("verify: %v", err)
	}
	if result.Valid {
		t.Fatal("expected invalid after tampering")
	}
	if len(result.Failures) != 1 {
		t.Fatalf("expected 1 failure, got %d", len(result.Failures))
	}
}

func TestVerify_MissingFile(t *testing.T) {
	root := setupTestRepo(t)
	v := NewIntegrityVerifier(root)

	manifestPath := filepath.Join(t.TempDir(), "manifest.json")
	v.WriteManifest(manifestPath)

	// Remove a file.
	os.Remove(filepath.Join(root, "governance/schemas/panel-output.schema.json"))

	result, err := v.Verify(manifestPath)
	if err != nil {
		t.Fatalf("verify: %v", err)
	}
	if result.Valid {
		t.Fatal("expected invalid after removing file")
	}
	if len(result.MissingFiles) != 1 {
		t.Fatalf("expected 1 missing, got %d", len(result.MissingFiles))
	}
}

func TestVerify_NewFile(t *testing.T) {
	root := setupTestRepo(t)
	v := NewIntegrityVerifier(root)

	manifestPath := filepath.Join(t.TempDir(), "manifest.json")
	v.WriteManifest(manifestPath)

	// Add a new file.
	os.WriteFile(filepath.Join(root, "governance/policy/extra.yaml"), []byte("new"), 0644)

	result, err := v.Verify(manifestPath)
	if err != nil {
		t.Fatalf("verify: %v", err)
	}
	// The manifest should still be valid (new files don't invalidate).
	if !result.Valid {
		t.Fatalf("new files should not invalidate: failures=%v missing=%v", result.Failures, result.MissingFiles)
	}
	if len(result.NewFiles) != 1 {
		t.Fatalf("expected 1 new file, got %d", len(result.NewFiles))
	}
}
