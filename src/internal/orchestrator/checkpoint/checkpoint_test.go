package checkpoint

import (
	"path/filepath"
	"strings"
	"testing"
)

func TestSaveAndLoad(t *testing.T) {
	dir := t.TempDir()
	mgr := NewManager(dir)

	cp := &Checkpoint{
		SessionID:     "sess-1",
		Phase:         3,
		Tier:          "yellow",
		Reason:        "gate check",
		CompletedWork: []string{"issue-1"},
		RemainingWork: []string{"issue-2", "issue-3"},
		GitBranch:     "feature/test",
	}

	path, err := mgr.Save(cp)
	if err != nil {
		t.Fatalf("save: %v", err)
	}
	if path == "" {
		t.Fatal("expected non-empty path")
	}

	loaded, err := mgr.Load(path)
	if err != nil {
		t.Fatalf("load: %v", err)
	}

	if loaded.SessionID != "sess-1" {
		t.Fatalf("expected sess-1, got %q", loaded.SessionID)
	}
	if loaded.Phase != 3 {
		t.Fatalf("expected phase 3, got %d", loaded.Phase)
	}
	if loaded.Tier != "yellow" {
		t.Fatalf("expected yellow, got %q", loaded.Tier)
	}
	if len(loaded.CompletedWork) != 1 {
		t.Fatalf("expected 1 completed, got %d", len(loaded.CompletedWork))
	}
	if len(loaded.RemainingWork) != 2 {
		t.Fatalf("expected 2 remaining, got %d", len(loaded.RemainingWork))
	}
}

func TestSaveEmergency(t *testing.T) {
	dir := t.TempDir()
	mgr := NewManager(dir)

	cp := &Checkpoint{
		SessionID: "sess-1",
		Phase:     5,
		Tier:      "red",
		Reason:    "emergency stop",
	}

	path, err := mgr.SaveEmergency(cp)
	if err != nil {
		t.Fatalf("save emergency: %v", err)
	}

	filename := filepath.Base(path)
	if !strings.HasPrefix(filename, "emergency-") {
		t.Fatalf("expected emergency- prefix, got %q", filename)
	}

	loaded, err := mgr.Load(path)
	if err != nil {
		t.Fatalf("load emergency: %v", err)
	}
	if loaded.Reason != "emergency stop" {
		t.Fatalf("expected 'emergency stop', got %q", loaded.Reason)
	}
}

func TestListCheckpoints(t *testing.T) {
	dir := t.TempDir()
	mgr := NewManager(dir)

	cp1 := &Checkpoint{SessionID: "s1", Phase: 1}
	cp2 := &Checkpoint{SessionID: "s2", Phase: 2}

	mgr.Save(cp1)
	mgr.Save(cp2)

	paths, err := mgr.ListCheckpoints()
	if err != nil {
		t.Fatalf("list: %v", err)
	}
	if len(paths) != 2 {
		t.Fatalf("expected 2 checkpoints, got %d", len(paths))
	}
}

func TestListCheckpoints_EmptyDir(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "nonexistent")
	mgr := NewManager(dir)

	paths, err := mgr.ListCheckpoints()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(paths) != 0 {
		t.Fatalf("expected 0, got %d", len(paths))
	}
}

func TestLoad_Nonexistent(t *testing.T) {
	dir := t.TempDir()
	mgr := NewManager(dir)

	_, err := mgr.Load(filepath.Join(dir, "no-such-file.json"))
	if err == nil {
		t.Fatal("expected error for nonexistent checkpoint")
	}
}
