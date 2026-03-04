package locks

import (
	"testing"
	"time"
)

func TestClaimAndRelease(t *testing.T) {
	dir := t.TempDir()
	mgr := NewManager(dir)

	err := mgr.Claim("issue-1", "session-a", "agent-1")
	if err != nil {
		t.Fatalf("claim: %v", err)
	}

	err = mgr.Release("issue-1", "session-a")
	if err != nil {
		t.Fatalf("release: %v", err)
	}
}

func TestDoubleClaimFails(t *testing.T) {
	dir := t.TempDir()
	mgr := NewManager(dir)

	err := mgr.Claim("issue-1", "session-a", "agent-1")
	if err != nil {
		t.Fatalf("first claim: %v", err)
	}

	err = mgr.Claim("issue-1", "session-b", "agent-2")
	if err == nil {
		t.Fatal("expected error on double claim by different session")
	}
}

func TestReclaimBySameSession(t *testing.T) {
	dir := t.TempDir()
	mgr := NewManager(dir)

	err := mgr.Claim("issue-1", "session-a", "agent-1")
	if err != nil {
		t.Fatalf("first claim: %v", err)
	}

	// Re-claim by same session should succeed.
	err = mgr.Claim("issue-1", "session-a", "agent-1")
	if err != nil {
		t.Fatalf("re-claim by same session should succeed: %v", err)
	}
}

func TestReleaseWrongOwnerFails(t *testing.T) {
	dir := t.TempDir()
	mgr := NewManager(dir)

	mgr.Claim("issue-1", "session-a", "agent-1")

	err := mgr.Release("issue-1", "session-b")
	if err == nil {
		t.Fatal("expected error releasing lock owned by different session")
	}
}

func TestHeartbeat(t *testing.T) {
	dir := t.TempDir()
	mgr := NewManager(dir)

	mgr.Claim("issue-1", "session-a", "agent-1")

	err := mgr.Heartbeat("issue-1", "session-a")
	if err != nil {
		t.Fatalf("heartbeat: %v", err)
	}
}

func TestCleanupStale(t *testing.T) {
	dir := t.TempDir()
	mgr := NewManager(dir)
	mgr.StaleTimeout = 1 * time.Millisecond

	mgr.Claim("issue-1", "session-a", "agent-1")

	// Wait for the lock to become stale.
	time.Sleep(5 * time.Millisecond)

	cleaned, err := mgr.CleanupStale()
	if err != nil {
		t.Fatalf("cleanup: %v", err)
	}
	if len(cleaned) != 1 {
		t.Fatalf("expected 1 cleaned, got %d", len(cleaned))
	}
	if cleaned[0] != "issue-1" {
		t.Fatalf("expected issue-1, got %q", cleaned[0])
	}
}

func TestForceRelease(t *testing.T) {
	dir := t.TempDir()
	mgr := NewManager(dir)

	mgr.Claim("issue-1", "session-a", "agent-1")

	err := mgr.ForceRelease("issue-1")
	if err != nil {
		t.Fatalf("force release: %v", err)
	}

	// After force release, a new claim should succeed.
	err = mgr.Claim("issue-1", "session-b", "agent-2")
	if err != nil {
		t.Fatalf("claim after force release: %v", err)
	}
}

func TestStaleLockOverwriteOnClaim(t *testing.T) {
	dir := t.TempDir()
	mgr := NewManager(dir)
	mgr.StaleTimeout = 1 * time.Millisecond

	mgr.Claim("issue-1", "session-a", "agent-1")

	// Wait for stale.
	time.Sleep(5 * time.Millisecond)

	// New session should be able to claim over the stale lock.
	err := mgr.Claim("issue-1", "session-b", "agent-2")
	if err != nil {
		t.Fatalf("expected stale overwrite to succeed: %v", err)
	}
}

func TestForceRelease_Nonexistent(t *testing.T) {
	dir := t.TempDir()
	mgr := NewManager(dir)

	// ForceRelease on nonexistent should not error.
	err := mgr.ForceRelease("nope")
	if err != nil {
		t.Fatalf("force release nonexistent: %v", err)
	}
}
