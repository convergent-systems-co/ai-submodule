// Package session implements on-disk persistence for orchestrator sessions.
// Each session is stored as a JSON file so that state survives context resets
// and process restarts.
//
// Ported from Python: governance/engine/orchestrator/session.py
package session

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

// validSessionID restricts IDs to safe filesystem characters.
var validSessionID = regexp.MustCompile(`^[a-zA-Z0-9_-]+$`)

// ---------------------------------------------------------------------------
// PersistedSession
// ---------------------------------------------------------------------------

// PersistedSession holds the full orchestrator state for a single session.
type PersistedSession struct {
	SessionID       string                 `json:"session_id"`
	Phase           int                    `json:"phase"`
	Tier            string                 `json:"tier"`
	ToolCalls       int                    `json:"tool_calls"`
	Turns           int                    `json:"turns"`
	IssuesCompleted int                    `json:"issues_completed"`
	ParallelCoders  int                    `json:"parallel_coders"`
	IssuesSelected  []string               `json:"issues_selected"`
	IssuesInFlight  []string               `json:"issues_in_flight"`
	IssuesCompletedList []string           `json:"issues_completed_list"`
	IssueFeedback   map[string][]string    `json:"issue_feedback"`
	PRsCreated      []int                  `json:"prs_created"`
	Plans           []interface{}          `json:"plans"`
	DispatchState   map[string]interface{} `json:"dispatch_state"`
	GateHistory     []interface{}          `json:"gate_history"`
	CircuitBreaker  map[string]interface{} `json:"circuit_breaker"`
	AgentRegistry   map[string]interface{} `json:"agent_registry"`
	LockState       map[string]interface{} `json:"lock_state"`
	Error           string                 `json:"error"`
	DeployState     map[string]interface{} `json:"deploy_state"`
	SystemWarning   bool                   `json:"system_warning"`
	DegradedRecall  bool                   `json:"degraded_recall"`
	StartedAt       string                 `json:"started_at"`
	UpdatedAt       string                 `json:"updated_at"`
	CompletedAt     string                 `json:"completed_at"`
}

// NewSession creates a PersistedSession with sensible defaults.
func NewSession(sessionID string) *PersistedSession {
	now := time.Now().UTC().Format(time.RFC3339)
	return &PersistedSession{
		SessionID:       sessionID,
		ParallelCoders:  5,
		IssuesSelected:  []string{},
		IssuesInFlight:  []string{},
		IssuesCompletedList: []string{},
		IssueFeedback:   make(map[string][]string),
		PRsCreated:      []int{},
		Plans:           []interface{}{},
		DispatchState:   make(map[string]interface{}),
		GateHistory:     []interface{}{},
		CircuitBreaker:  make(map[string]interface{}),
		AgentRegistry:   make(map[string]interface{}),
		LockState:       make(map[string]interface{}),
		DeployState:     make(map[string]interface{}),
		StartedAt:       now,
		UpdatedAt:       now,
	}
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

// Store manages session files in a directory.
type Store struct {
	dir string
}

// NewStore creates a Store backed by the given directory.
// The directory is created if it does not exist.
func NewStore(dir string) *Store {
	return &Store{dir: dir}
}

// Save persists the session to disk as JSON.
func (s *Store) Save(session *PersistedSession) error {
	if err := os.MkdirAll(s.dir, 0755); err != nil {
		return fmt.Errorf("session store: create dir: %w", err)
	}

	session.UpdatedAt = time.Now().UTC().Format(time.RFC3339)

	data, err := json.MarshalIndent(session, "", "  ")
	if err != nil {
		return fmt.Errorf("session store: marshal: %w", err)
	}
	data = append(data, '\n')

	path := filepath.Join(s.dir, session.SessionID+".json")
	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("session store: write %s: %w", path, err)
	}
	return nil
}

// Load reads a session by ID. Returns an error if the ID contains
// path-traversal characters or the file cannot be read.
func (s *Store) Load(sessionID string) (*PersistedSession, error) {
	if !validSessionID.MatchString(sessionID) {
		return nil, fmt.Errorf("session store: invalid session ID %q", sessionID)
	}

	path := filepath.Join(s.dir, sessionID+".json")
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("session store: read %s: %w", path, err)
	}

	var session PersistedSession
	if err := json.Unmarshal(data, &session); err != nil {
		return nil, fmt.Errorf("session store: unmarshal %s: %w", path, err)
	}
	return &session, nil
}

// LoadLatest returns the most recently modified session.
func (s *Store) LoadLatest() (*PersistedSession, error) {
	entries, err := os.ReadDir(s.dir)
	if err != nil {
		return nil, fmt.Errorf("session store: read dir: %w", err)
	}

	var newest string
	var newestTime time.Time

	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".json") {
			continue
		}
		info, err := e.Info()
		if err != nil {
			continue
		}
		if newest == "" || info.ModTime().After(newestTime) {
			newest = strings.TrimSuffix(e.Name(), ".json")
			newestTime = info.ModTime()
		}
	}

	if newest == "" {
		return nil, fmt.Errorf("session store: no sessions found in %s", s.dir)
	}
	return s.Load(newest)
}

// ListSessions returns the IDs of all persisted sessions.
func (s *Store) ListSessions() ([]string, error) {
	entries, err := os.ReadDir(s.dir)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, fmt.Errorf("session store: read dir: %w", err)
	}

	var ids []string
	for _, e := range entries {
		if !e.IsDir() && strings.HasSuffix(e.Name(), ".json") {
			ids = append(ids, strings.TrimSuffix(e.Name(), ".json"))
		}
	}
	return ids, nil
}
