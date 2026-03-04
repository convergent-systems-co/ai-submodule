// Package dispatch tracks agent dispatch lifecycle within the orchestrator.
// Each dispatch creates a Record that transitions through
// pending -> running -> completed/failed.
//
// Ported from Python: governance/engine/orchestrator/dispatch.py
package dispatch

import (
	"fmt"
	"time"
)

// ---------------------------------------------------------------------------
// Status constants
// ---------------------------------------------------------------------------

const (
	StatusPending   = "pending"
	StatusRunning   = "running"
	StatusCompleted = "completed"
	StatusFailed    = "failed"
)

// ---------------------------------------------------------------------------
// Record
// ---------------------------------------------------------------------------

// Record tracks a single dispatched agent assignment.
type Record struct {
	TaskID        string                 `json:"task_id"`
	Persona       string                 `json:"persona"`
	ParentTaskID  string                 `json:"parent_task_id,omitempty"`
	CorrelationID string                 `json:"correlation_id,omitempty"`
	Status        string                 `json:"status"`
	DispatchedAt  string                 `json:"dispatched_at"`
	CompletedAt   string                 `json:"completed_at,omitempty"`
	Assignment    map[string]interface{} `json:"assignment,omitempty"`
	Result        map[string]interface{} `json:"result,omitempty"`
}

// ---------------------------------------------------------------------------
// ValidationResult
// ---------------------------------------------------------------------------

// ValidationResult captures dispatch-time topology and concurrency checks.
type ValidationResult struct {
	Valid    bool     `json:"valid"`
	Errors   []string `json:"errors,omitempty"`
	Warnings []string `json:"warnings,omitempty"`
}

// ---------------------------------------------------------------------------
// Tracker
// ---------------------------------------------------------------------------

// Tracker manages dispatch records for a session.
type Tracker struct {
	records map[string]*Record
}

// NewTracker creates an empty Tracker.
func NewTracker() *Tracker {
	return &Tracker{
		records: make(map[string]*Record),
	}
}

// Dispatch creates a new Record in pending status and returns it.
func (t *Tracker) Dispatch(taskID, persona, parentTaskID, correlationID string, assignment map[string]interface{}) *Record {
	r := &Record{
		TaskID:        taskID,
		Persona:       persona,
		ParentTaskID:  parentTaskID,
		CorrelationID: correlationID,
		Status:        StatusPending,
		DispatchedAt:  time.Now().UTC().Format(time.RFC3339),
		Assignment:    assignment,
	}
	t.records[taskID] = r
	return r
}

// Complete marks a record as completed with the given result.
func (t *Tracker) Complete(taskID string, result map[string]interface{}) error {
	r, ok := t.records[taskID]
	if !ok {
		return fmt.Errorf("dispatch: record %q not found", taskID)
	}
	r.Status = StatusCompleted
	r.CompletedAt = time.Now().UTC().Format(time.RFC3339)
	r.Result = result
	return nil
}

// Fail marks a record as failed with the given result.
func (t *Tracker) Fail(taskID string, result map[string]interface{}) error {
	r, ok := t.records[taskID]
	if !ok {
		return fmt.Errorf("dispatch: record %q not found", taskID)
	}
	r.Status = StatusFailed
	r.CompletedAt = time.Now().UTC().Format(time.RFC3339)
	r.Result = result
	return nil
}

// GetRecord returns the Record for taskID, or nil if not found.
func (t *Tracker) GetRecord(taskID string) *Record {
	return t.records[taskID]
}

// PendingCount returns the number of records in pending or running status.
func (t *Tracker) PendingCount() int {
	count := 0
	for _, r := range t.records {
		if r.Status == StatusPending || r.Status == StatusRunning {
			count++
		}
	}
	return count
}

// AllCompleted returns true if every record has reached completed or failed.
func (t *Tracker) AllCompleted() bool {
	for _, r := range t.records {
		if r.Status == StatusPending || r.Status == StatusRunning {
			return false
		}
	}
	return true
}

// ToDict serializes all records to a map for persistence.
func (t *Tracker) ToDict() map[string]interface{} {
	out := make(map[string]interface{}, len(t.records))
	for id, r := range t.records {
		out[id] = map[string]interface{}{
			"task_id":        r.TaskID,
			"persona":        r.Persona,
			"parent_task_id": r.ParentTaskID,
			"correlation_id": r.CorrelationID,
			"status":         r.Status,
			"dispatched_at":  r.DispatchedAt,
			"completed_at":   r.CompletedAt,
			"assignment":     r.Assignment,
			"result":         r.Result,
		}
	}
	return out
}

// ---------------------------------------------------------------------------
// ValidateDispatch
// ---------------------------------------------------------------------------

// ValidateDispatch checks whether a dispatch is permitted given topology
// constraints (canSpawn maps persona -> allowed child personas) and
// concurrency limits (maxConcurrent per persona, activeCount per persona).
func ValidateDispatch(persona, parentPersona string, canSpawn map[string][]string, maxConcurrent map[string]int, activeCount map[string]int) *ValidationResult {
	vr := &ValidationResult{Valid: true}

	// Check spawn permission.
	if parentPersona != "" {
		allowed, ok := canSpawn[parentPersona]
		if !ok {
			vr.Valid = false
			vr.Errors = append(vr.Errors, fmt.Sprintf(
				"persona %q is not allowed to spawn agents", parentPersona))
		} else {
			found := false
			for _, p := range allowed {
				if p == persona {
					found = true
					break
				}
			}
			if !found {
				vr.Valid = false
				vr.Errors = append(vr.Errors, fmt.Sprintf(
					"persona %q cannot spawn %q", parentPersona, persona))
			}
		}
	}

	// Check concurrency limit.
	if max, ok := maxConcurrent[persona]; ok {
		current := activeCount[persona]
		if current >= max {
			vr.Valid = false
			vr.Errors = append(vr.Errors, fmt.Sprintf(
				"persona %q at concurrency limit (%d/%d)", persona, current, max))
		} else if current >= max-1 {
			vr.Warnings = append(vr.Warnings, fmt.Sprintf(
				"persona %q approaching concurrency limit (%d/%d)", persona, current, max))
		}
	}

	return vr
}
