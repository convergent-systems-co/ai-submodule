// Package checkpoint implements session checkpoint persistence for the
// orchestrator. Checkpoints capture enough state to resume work after a
// context reset or emergency stop.
//
// Ported from Python: governance/engine/orchestrator/checkpoint.py
package checkpoint

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// ---------------------------------------------------------------------------
// Checkpoint
// ---------------------------------------------------------------------------

// Checkpoint captures orchestrator state at a point in time.
type Checkpoint struct {
	SessionID     string                 `json:"session_id"`
	Phase         int                    `json:"phase"`
	Tier          string                 `json:"tier"`
	Reason        string                 `json:"reason"`
	Timestamp     string                 `json:"timestamp"`
	CompletedWork []string               `json:"completed_work"`
	RemainingWork []string               `json:"remaining_work"`
	GitBranch     string                 `json:"git_branch"`
	State         map[string]interface{} `json:"state,omitempty"`
}

// ---------------------------------------------------------------------------
// Manager
// ---------------------------------------------------------------------------

// Manager handles reading and writing checkpoint files.
type Manager struct {
	checkpointDir string
}

// NewManager creates a Manager that stores checkpoints in dir.
func NewManager(dir string) *Manager {
	return &Manager{checkpointDir: dir}
}

// Save writes a checkpoint to dir/sessionID-phaseN-YYYYMMDD-HHMMSS.json.
// If Timestamp is empty it is set to the current time.
// Returns the path of the written file.
func (m *Manager) Save(cp *Checkpoint) (string, error) {
	if err := os.MkdirAll(m.checkpointDir, 0755); err != nil {
		return "", fmt.Errorf("checkpoint: create dir: %w", err)
	}

	if cp.Timestamp == "" {
		cp.Timestamp = time.Now().UTC().Format(time.RFC3339)
	}

	ts := formatFileTimestamp(cp.Timestamp)
	filename := fmt.Sprintf("%s-phase%d-%s.json", cp.SessionID, cp.Phase, ts)
	path := filepath.Join(m.checkpointDir, filename)

	data, err := json.MarshalIndent(cp, "", "  ")
	if err != nil {
		return "", fmt.Errorf("checkpoint: marshal: %w", err)
	}
	data = append(data, '\n')

	if err := os.WriteFile(path, data, 0644); err != nil {
		return "", fmt.Errorf("checkpoint: write %s: %w", path, err)
	}
	return path, nil
}

// SaveEmergency writes an emergency checkpoint to
// dir/emergency-sessionID-YYYYMMDD-HHMMSS.json.
// Returns the path of the written file.
func (m *Manager) SaveEmergency(cp *Checkpoint) (string, error) {
	if err := os.MkdirAll(m.checkpointDir, 0755); err != nil {
		return "", fmt.Errorf("checkpoint: create dir: %w", err)
	}

	if cp.Timestamp == "" {
		cp.Timestamp = time.Now().UTC().Format(time.RFC3339)
	}

	ts := formatFileTimestamp(cp.Timestamp)
	filename := fmt.Sprintf("emergency-%s-%s.json", cp.SessionID, ts)
	path := filepath.Join(m.checkpointDir, filename)

	data, err := json.MarshalIndent(cp, "", "  ")
	if err != nil {
		return "", fmt.Errorf("checkpoint: marshal: %w", err)
	}
	data = append(data, '\n')

	if err := os.WriteFile(path, data, 0644); err != nil {
		return "", fmt.Errorf("checkpoint: write %s: %w", path, err)
	}
	return path, nil
}

// Load reads a checkpoint from the given file path.
func (m *Manager) Load(path string) (*Checkpoint, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("checkpoint: read %s: %w", path, err)
	}
	var cp Checkpoint
	if err := json.Unmarshal(data, &cp); err != nil {
		return nil, fmt.Errorf("checkpoint: unmarshal %s: %w", path, err)
	}
	return &cp, nil
}

// ListCheckpoints returns paths of all .json checkpoint files in the dir.
func (m *Manager) ListCheckpoints() ([]string, error) {
	entries, err := os.ReadDir(m.checkpointDir)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, fmt.Errorf("checkpoint: read dir: %w", err)
	}

	var paths []string
	for _, e := range entries {
		if !e.IsDir() && strings.HasSuffix(e.Name(), ".json") {
			paths = append(paths, filepath.Join(m.checkpointDir, e.Name()))
		}
	}
	return paths, nil
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

// formatFileTimestamp converts an RFC3339 timestamp to YYYYMMDD-HHMMSS.
// Falls back to current time if parsing fails.
func formatFileTimestamp(ts string) string {
	t, err := time.Parse(time.RFC3339, ts)
	if err != nil {
		t = time.Now().UTC()
	}
	return t.Format("20060102-150405")
}
