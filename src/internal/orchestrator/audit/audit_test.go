package audit

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLogAndReadEvents(t *testing.T) {
	dir := t.TempDir()
	logger := NewLogger(dir, "test-session")

	err := logger.Log("phase_transition", 1, "agent-1", map[string]interface{}{"from": 0, "to": 1})
	if err != nil {
		t.Fatalf("log event 1: %v", err)
	}

	err = logger.Log("tool_call", 1, "agent-1", map[string]interface{}{"tool": "bash"})
	if err != nil {
		t.Fatalf("log event 2: %v", err)
	}

	events, err := ReadEvents(dir, "test-session")
	if err != nil {
		t.Fatalf("read events: %v", err)
	}

	if len(events) != 2 {
		t.Fatalf("expected 2 events, got %d", len(events))
	}
	if events[0].EventType != "phase_transition" {
		t.Fatalf("expected phase_transition, got %q", events[0].EventType)
	}
	if events[0].SessionID != "test-session" {
		t.Fatalf("expected test-session, got %q", events[0].SessionID)
	}
	if events[1].EventType != "tool_call" {
		t.Fatalf("expected tool_call, got %q", events[1].EventType)
	}
}

func TestReadEvents_Nonexistent(t *testing.T) {
	dir := t.TempDir()
	_, err := ReadEvents(dir, "nonexistent")
	if err == nil {
		t.Fatal("expected error for nonexistent session")
	}
}

func TestLoggerCreatesDirectory(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "nested", "audit")
	logger := NewLogger(dir, "session-1")

	err := logger.Log("init", 0, "", nil)
	if err != nil {
		t.Fatalf("log: %v", err)
	}

	// Verify directory was created.
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		t.Fatal("expected directory to be created")
	}
}
