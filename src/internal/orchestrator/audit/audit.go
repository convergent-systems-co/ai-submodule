// Package audit provides JSONL event logging for the orchestrator.
// Each session produces a single .jsonl file where every significant
// action is recorded as a JSON object on its own line.
//
// Ported from Python: governance/engine/orchestrator/audit.py
package audit

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// ---------------------------------------------------------------------------
// Event
// ---------------------------------------------------------------------------

// Event represents a single audit log entry.
type Event struct {
	Timestamp string                 `json:"timestamp"`
	EventType string                 `json:"event_type"`
	SessionID string                 `json:"session_id"`
	Phase     int                    `json:"phase"`
	AgentID   string                 `json:"agent_id,omitempty"`
	Details   map[string]interface{} `json:"details,omitempty"`
}

// ---------------------------------------------------------------------------
// Logger
// ---------------------------------------------------------------------------

// Logger writes audit events as JSONL to a per-session file.
type Logger struct {
	logDir    string
	sessionID string
}

// NewLogger creates a Logger that writes to logDir/sessionID.jsonl.
func NewLogger(logDir, sessionID string) *Logger {
	return &Logger{
		logDir:    logDir,
		sessionID: sessionID,
	}
}

// Log appends a single JSON event line to the session's audit file.
func (l *Logger) Log(eventType string, phase int, agentID string, details map[string]interface{}) error {
	if err := os.MkdirAll(l.logDir, 0755); err != nil {
		return fmt.Errorf("audit: create dir: %w", err)
	}

	event := Event{
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		EventType: eventType,
		SessionID: l.sessionID,
		Phase:     phase,
		AgentID:   agentID,
		Details:   details,
	}

	data, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("audit: marshal event: %w", err)
	}

	path := filepath.Join(l.logDir, l.sessionID+".jsonl")
	f, err := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("audit: open %s: %w", path, err)
	}
	defer f.Close()

	if _, err := f.Write(append(data, '\n')); err != nil {
		return fmt.Errorf("audit: write event: %w", err)
	}
	return nil
}

// ---------------------------------------------------------------------------
// ReadEvents
// ---------------------------------------------------------------------------

// ReadEvents reads and parses all audit events from a session's JSONL file.
func ReadEvents(logDir, sessionID string) ([]Event, error) {
	path := filepath.Join(logDir, sessionID+".jsonl")
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("audit: open %s: %w", path, err)
	}
	defer f.Close()

	var events []Event
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}
		var ev Event
		if err := json.Unmarshal(line, &ev); err != nil {
			return nil, fmt.Errorf("audit: parse line: %w", err)
		}
		events = append(events, ev)
	}
	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("audit: scan %s: %w", path, err)
	}
	return events, nil
}
