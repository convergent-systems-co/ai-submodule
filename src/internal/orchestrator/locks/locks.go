// Package locks provides cross-session work-unit locking via the filesystem.
// Lock files are created atomically (O_CREATE|O_EXCL) and support heartbeat
// updates and stale-lock detection.
//
// Ported from Python: governance/engine/orchestrator/locks.py
package locks

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// DefaultStaleTimeout is how long a lock can go without a heartbeat
// before it is considered stale.
const DefaultStaleTimeout = 10 * time.Minute

// ---------------------------------------------------------------------------
// Entry
// ---------------------------------------------------------------------------

// Entry represents a single lock record.
type Entry struct {
	WorkID    string `json:"work_id"`
	SessionID string `json:"session_id"`
	AgentID   string `json:"agent_id"`
	ClaimedAt string `json:"claimed_at"`
	Heartbeat string `json:"heartbeat"`
}

// ---------------------------------------------------------------------------
// Manager
// ---------------------------------------------------------------------------

// Manager manages lock files in a directory.
type Manager struct {
	lockDir      string
	StaleTimeout time.Duration
}

// NewManager creates a Manager backed by lockDir.
func NewManager(lockDir string) *Manager {
	return &Manager{
		lockDir:      lockDir,
		StaleTimeout: DefaultStaleTimeout,
	}
}

// Claim attempts to acquire a lock for workID. If a stale lock exists, it
// is replaced. Returns an error if the lock is held by another live session.
func (m *Manager) Claim(workID, sessionID, agentID string) error {
	if err := os.MkdirAll(m.lockDir, 0755); err != nil {
		return fmt.Errorf("locks: mkdir: %w", err)
	}

	path := m.lockPath(workID)

	// Check for existing lock.
	if existing, err := m.readEntry(path); err == nil {
		if !m.isStale(existing) {
			if existing.SessionID == sessionID {
				// Re-claim by same session is OK — update heartbeat.
				return m.writeEntry(path, &Entry{
					WorkID:    workID,
					SessionID: sessionID,
					AgentID:   agentID,
					ClaimedAt: existing.ClaimedAt,
					Heartbeat: now(),
				})
			}
			return fmt.Errorf("locks: work %q already claimed by session %s", workID, existing.SessionID)
		}
		// Stale lock — remove and re-claim.
		_ = os.Remove(path)
	}

	// Attempt atomic create.
	entry := &Entry{
		WorkID:    workID,
		SessionID: sessionID,
		AgentID:   agentID,
		ClaimedAt: now(),
		Heartbeat: now(),
	}

	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	if err != nil {
		if os.IsExist(err) {
			return fmt.Errorf("locks: work %q claimed concurrently", workID)
		}
		return fmt.Errorf("locks: create lock: %w", err)
	}
	defer f.Close()

	data, _ := json.MarshalIndent(entry, "", "  ")
	_, err = f.Write(data)
	return err
}

// Release removes the lock for workID if it is owned by sessionID.
func (m *Manager) Release(workID, sessionID string) error {
	path := m.lockPath(workID)
	entry, err := m.readEntry(path)
	if err != nil {
		return fmt.Errorf("locks: no lock for %q: %w", workID, err)
	}
	if entry.SessionID != sessionID {
		return fmt.Errorf("locks: work %q owned by session %s, not %s", workID, entry.SessionID, sessionID)
	}
	return os.Remove(path)
}

// Heartbeat updates the heartbeat timestamp for a lock.
func (m *Manager) Heartbeat(workID, sessionID string) error {
	path := m.lockPath(workID)
	entry, err := m.readEntry(path)
	if err != nil {
		return fmt.Errorf("locks: no lock for %q: %w", workID, err)
	}
	if entry.SessionID != sessionID {
		return fmt.Errorf("locks: work %q owned by session %s, not %s", workID, entry.SessionID, sessionID)
	}
	entry.Heartbeat = now()
	return m.writeEntry(path, entry)
}

// CleanupStale removes all stale locks and returns their work IDs.
func (m *Manager) CleanupStale() ([]string, error) {
	entries, err := os.ReadDir(m.lockDir)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, fmt.Errorf("locks: read dir: %w", err)
	}

	var cleaned []string
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".lock") {
			continue
		}
		path := filepath.Join(m.lockDir, e.Name())
		entry, err := m.readEntry(path)
		if err != nil {
			continue
		}
		if m.isStale(entry) {
			_ = os.Remove(path)
			cleaned = append(cleaned, entry.WorkID)
		}
	}
	return cleaned, nil
}

// ForceRelease removes the lock for workID regardless of ownership.
func (m *Manager) ForceRelease(workID string) error {
	path := m.lockPath(workID)
	if err := os.Remove(path); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("locks: force release %q: %w", workID, err)
	}
	return nil
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

// lockPath sanitizes workID and returns the lock file path.
func (m *Manager) lockPath(workID string) string {
	safe := strings.ReplaceAll(workID, "/", "_")
	safe = strings.ReplaceAll(safe, "..", "")
	return filepath.Join(m.lockDir, safe+".lock")
}

func (m *Manager) readEntry(path string) (*Entry, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var entry Entry
	if err := json.Unmarshal(data, &entry); err != nil {
		return nil, err
	}
	return &entry, nil
}

func (m *Manager) writeEntry(path string, entry *Entry) error {
	data, _ := json.MarshalIndent(entry, "", "  ")
	return os.WriteFile(path, data, 0644)
}

func (m *Manager) isStale(entry *Entry) bool {
	t, err := time.Parse(time.RFC3339, entry.Heartbeat)
	if err != nil {
		return true // unparseable heartbeat → stale
	}
	return time.Since(t) > m.StaleTimeout
}

func now() string {
	return time.Now().UTC().Format(time.RFC3339)
}
