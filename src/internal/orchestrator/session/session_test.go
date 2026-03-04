package session

import (
	"os"
	"path/filepath"
	"testing"
)

func TestNewSession(t *testing.T) {
	s := NewSession("test-session")
	if s.SessionID != "test-session" {
		t.Fatalf("expected session ID 'test-session', got %q", s.SessionID)
	}
	if s.ParallelCoders != 5 {
		t.Fatalf("expected ParallelCoders=5, got %d", s.ParallelCoders)
	}
	if s.StartedAt == "" {
		t.Fatal("expected non-empty StartedAt")
	}
}

func TestSaveAndLoad(t *testing.T) {
	dir := t.TempDir()
	store := NewStore(dir)

	orig := NewSession("roundtrip")
	orig.Phase = 3
	orig.ToolCalls = 42

	if err := store.Save(orig); err != nil {
		t.Fatalf("save: %v", err)
	}

	loaded, err := store.Load("roundtrip")
	if err != nil {
		t.Fatalf("load: %v", err)
	}

	if loaded.SessionID != "roundtrip" {
		t.Fatalf("expected 'roundtrip', got %q", loaded.SessionID)
	}
	if loaded.Phase != 3 {
		t.Fatalf("expected phase 3, got %d", loaded.Phase)
	}
	if loaded.ToolCalls != 42 {
		t.Fatalf("expected tool_calls 42, got %d", loaded.ToolCalls)
	}
}

func TestLoadLatest(t *testing.T) {
	dir := t.TempDir()
	store := NewStore(dir)

	s1 := NewSession("first")
	s1.Phase = 1
	if err := store.Save(s1); err != nil {
		t.Fatalf("save first: %v", err)
	}

	s2 := NewSession("second")
	s2.Phase = 2
	if err := store.Save(s2); err != nil {
		t.Fatalf("save second: %v", err)
	}

	latest, err := store.LoadLatest()
	if err != nil {
		t.Fatalf("load latest: %v", err)
	}
	// The latest should be "second" since it was saved last.
	if latest.SessionID != "second" {
		t.Fatalf("expected 'second', got %q", latest.SessionID)
	}
}

func TestListSessions(t *testing.T) {
	dir := t.TempDir()
	store := NewStore(dir)

	for _, id := range []string{"alpha", "beta", "gamma"} {
		if err := store.Save(NewSession(id)); err != nil {
			t.Fatalf("save %s: %v", id, err)
		}
	}

	ids, err := store.ListSessions()
	if err != nil {
		t.Fatalf("list: %v", err)
	}
	if len(ids) != 3 {
		t.Fatalf("expected 3 sessions, got %d", len(ids))
	}
}

func TestLoadNonexistent(t *testing.T) {
	dir := t.TempDir()
	store := NewStore(dir)

	_, err := store.Load("does-not-exist")
	if err == nil {
		t.Fatal("expected error loading nonexistent session")
	}
}

func TestPathTraversalRejected(t *testing.T) {
	dir := t.TempDir()
	store := NewStore(dir)

	_, err := store.Load("../etc/passwd")
	if err == nil {
		t.Fatal("expected error for path traversal")
	}
}

func TestListSessionsEmptyDir(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "nonexistent")
	store := NewStore(dir)

	ids, err := store.ListSessions()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(ids) != 0 {
		t.Fatalf("expected 0 sessions, got %d", len(ids))
	}
}

func TestListSessionsIgnoresNonJSON(t *testing.T) {
	dir := t.TempDir()
	store := NewStore(dir)

	// Create a non-JSON file.
	os.WriteFile(filepath.Join(dir, "README.md"), []byte("hi"), 0644)
	store.Save(NewSession("real"))

	ids, err := store.ListSessions()
	if err != nil {
		t.Fatalf("list: %v", err)
	}
	if len(ids) != 1 {
		t.Fatalf("expected 1 session, got %d", len(ids))
	}
}
