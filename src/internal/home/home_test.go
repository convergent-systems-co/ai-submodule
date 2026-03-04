package home

import (
	"os"
	"path/filepath"
	"testing"
	"testing/fstest"
)

func TestDefaultHome(t *testing.T) {
	// Clear env vars that might interfere
	origDGH := os.Getenv("DARK_GOVERNANCE_HOME")
	origXDG := os.Getenv("XDG_DATA_HOME")
	defer func() {
		os.Setenv("DARK_GOVERNANCE_HOME", origDGH)
		os.Setenv("XDG_DATA_HOME", origXDG)
	}()

	t.Run("uses DARK_GOVERNANCE_HOME if set", func(t *testing.T) {
		os.Setenv("DARK_GOVERNANCE_HOME", "/custom/home")
		os.Setenv("XDG_DATA_HOME", "")
		home, err := DefaultHome()
		if err != nil {
			t.Fatal(err)
		}
		if home != "/custom/home" {
			t.Errorf("expected /custom/home, got %s", home)
		}
	})

	t.Run("uses XDG_DATA_HOME if set", func(t *testing.T) {
		os.Setenv("DARK_GOVERNANCE_HOME", "")
		os.Setenv("XDG_DATA_HOME", "/xdg/data")
		home, err := DefaultHome()
		if err != nil {
			t.Fatal(err)
		}
		expected := filepath.Join("/xdg/data", "dark-governance")
		if home != expected {
			t.Errorf("expected %s, got %s", expected, home)
		}
	})

	t.Run("falls back to ~/.ai", func(t *testing.T) {
		os.Setenv("DARK_GOVERNANCE_HOME", "")
		os.Setenv("XDG_DATA_HOME", "")
		home, err := DefaultHome()
		if err != nil {
			t.Fatal(err)
		}
		userHome, _ := os.UserHomeDir()
		expected := filepath.Join(userHome, ".ai")
		if home != expected {
			t.Errorf("expected %s, got %s", expected, home)
		}
	})
}

func TestVersionDir(t *testing.T) {
	dir := VersionDir("/home/user/.ai", "0.1.0")
	expected := filepath.Join("/home/user/.ai", "versions", "0.1.0")
	if dir != expected {
		t.Errorf("expected %s, got %s", expected, dir)
	}
}

func TestIsInstalled(t *testing.T) {
	tmpDir := t.TempDir()

	// Not installed
	if IsInstalled(tmpDir, "0.1.0") {
		t.Error("expected not installed")
	}

	// Create version directory
	vdir := VersionDir(tmpDir, "0.1.0")
	if err := os.MkdirAll(vdir, 0755); err != nil {
		t.Fatalf("failed to create version directory: %v", err)
	}

	if !IsInstalled(tmpDir, "0.1.0") {
		t.Error("expected installed")
	}
}

func TestCleanVersion(t *testing.T) {
	tmpDir := t.TempDir()
	vdir := VersionDir(tmpDir, "0.1.0")
	if err := os.MkdirAll(vdir, 0755); err != nil {
		t.Fatalf("failed to create version directory: %v", err)
	}
	if err := os.WriteFile(filepath.Join(vdir, "test.txt"), []byte("test"), 0644); err != nil {
		t.Fatalf("failed to write test file: %v", err)
	}

	if err := CleanVersion(tmpDir, "0.1.0"); err != nil {
		t.Fatal(err)
	}

	if IsInstalled(tmpDir, "0.1.0") {
		t.Error("expected version to be cleaned")
	}
}

func TestInstall(t *testing.T) {
	tmpDir := t.TempDir()

	// Create a test filesystem
	content := fstest.MapFS{
		"policy/default.yaml": &fstest.MapFile{Data: []byte("test: true\n")},
		"schemas/test.json":   &fstest.MapFile{Data: []byte("{}\n")},
	}

	count, err := Install(tmpDir, "0.1.0", "abc123", content)
	if err != nil {
		t.Fatal(err)
	}

	if count != 2 {
		t.Errorf("expected 2 files extracted, got %d", count)
	}

	if !IsInstalled(tmpDir, "0.1.0") {
		t.Error("expected installed after Install()")
	}

	// Verify content hash marker
	hashPath := filepath.Join(VersionDir(tmpDir, "0.1.0"), ".content-hash")
	data, err := os.ReadFile(hashPath)
	if err != nil {
		t.Fatal(err)
	}
	if string(data) != "abc123\n" {
		t.Errorf("expected content hash abc123, got %s", string(data))
	}
}

func TestListVersions(t *testing.T) {
	tmpDir := t.TempDir()

	// No versions
	versions, err := ListVersions(tmpDir)
	if err != nil {
		t.Fatal(err)
	}
	if len(versions) != 0 {
		t.Errorf("expected 0 versions, got %d", len(versions))
	}

	// Create some versions
	for _, v := range []string{"0.1.0", "0.2.0", "0.3.0"} {
		if err := os.MkdirAll(VersionDir(tmpDir, v), 0755); err != nil {
			t.Fatalf("failed to create version directory for %s: %v", v, err)
		}
	}

	versions, err = ListVersions(tmpDir)
	if err != nil {
		t.Fatal(err)
	}
	if len(versions) != 3 {
		t.Errorf("expected 3 versions, got %d", len(versions))
	}
	// Should be sorted descending
	if versions[0] != "0.3.0" {
		t.Errorf("expected first version to be 0.3.0, got %s", versions[0])
	}
}
