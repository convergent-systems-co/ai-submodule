// Package circuitbreaker implements per-work-unit failure detection for
// the orchestrator. When a work unit exceeds its feedback or evaluation
// cycle limits the circuit trips, preventing further dispatch.
//
// Ported from Python: governance/engine/orchestrator/circuit_breaker.py
package circuitbreaker

import "fmt"

// ---------------------------------------------------------------------------
// WorkUnit
// ---------------------------------------------------------------------------

// WorkUnit tracks failure counters for a single work item (issue / PR).
type WorkUnit struct {
	ID                 string `json:"id"`
	FeedbackCycles     int    `json:"feedback_cycles"`
	TotalEvalCycles    int    `json:"total_eval_cycles"`
	Reassignments      int    `json:"reassignments"`
	MaxFeedbackCycles  int    `json:"max_feedback_cycles"`
	MaxTotalEvalCycles int    `json:"max_total_eval_cycles"`
	Tripped            bool   `json:"tripped"`
}

// ---------------------------------------------------------------------------
// CircuitBreaker
// ---------------------------------------------------------------------------

// CircuitBreaker manages a collection of WorkUnits.
type CircuitBreaker struct {
	units              map[string]*WorkUnit
	maxFeedbackCycles  int
	maxTotalEvalCycles int
}

// New creates a CircuitBreaker. Defaults: maxFeedback=2, maxTotal=5.
func New(maxFeedback, maxTotal int) *CircuitBreaker {
	if maxFeedback <= 0 {
		maxFeedback = 2
	}
	if maxTotal <= 0 {
		maxTotal = 5
	}
	return &CircuitBreaker{
		units:              make(map[string]*WorkUnit),
		maxFeedbackCycles:  maxFeedback,
		maxTotalEvalCycles: maxTotal,
	}
}

// ensureUnit lazily initializes a WorkUnit.
func (cb *CircuitBreaker) ensureUnit(workID string) *WorkUnit {
	if u, ok := cb.units[workID]; ok {
		return u
	}
	u := &WorkUnit{
		ID:                 workID,
		MaxFeedbackCycles:  cb.maxFeedbackCycles,
		MaxTotalEvalCycles: cb.maxTotalEvalCycles,
	}
	cb.units[workID] = u
	return u
}

// RecordFeedback increments the feedback cycle counter for workID.
// Returns an error if the circuit trips.
func (cb *CircuitBreaker) RecordFeedback(workID string) error {
	u := cb.ensureUnit(workID)
	u.FeedbackCycles++
	u.TotalEvalCycles++
	if u.FeedbackCycles >= u.MaxFeedbackCycles || u.TotalEvalCycles >= u.MaxTotalEvalCycles {
		u.Tripped = true
		return fmt.Errorf("circuit tripped for %s: feedback=%d/%d total=%d/%d",
			workID, u.FeedbackCycles, u.MaxFeedbackCycles, u.TotalEvalCycles, u.MaxTotalEvalCycles)
	}
	return nil
}

// RecordReassign increments the reassignment counter.
func (cb *CircuitBreaker) RecordReassign(workID string) {
	u := cb.ensureUnit(workID)
	u.Reassignments++
}

// CanDispatch returns true if the work unit has not tripped.
func (cb *CircuitBreaker) CanDispatch(workID string) bool {
	u, ok := cb.units[workID]
	if !ok {
		return true
	}
	return !u.Tripped
}

// GetUnit returns the WorkUnit for workID, or nil if none exists.
func (cb *CircuitBreaker) GetUnit(workID string) *WorkUnit {
	return cb.units[workID]
}

// ToDict serializes the circuit breaker state to a map.
func (cb *CircuitBreaker) ToDict() map[string]interface{} {
	units := make(map[string]interface{}, len(cb.units))
	for id, u := range cb.units {
		units[id] = map[string]interface{}{
			"id":                  u.ID,
			"feedback_cycles":     u.FeedbackCycles,
			"total_eval_cycles":   u.TotalEvalCycles,
			"reassignments":       u.Reassignments,
			"max_feedback_cycles": u.MaxFeedbackCycles,
			"max_total_eval_cycles": u.MaxTotalEvalCycles,
			"tripped":             u.Tripped,
		}
	}
	return map[string]interface{}{
		"units":                units,
		"max_feedback_cycles":  cb.maxFeedbackCycles,
		"max_total_eval_cycles": cb.maxTotalEvalCycles,
	}
}

// FromDict restores a CircuitBreaker from a serialized map.
func FromDict(data map[string]interface{}) *CircuitBreaker {
	cb := &CircuitBreaker{
		units:              make(map[string]*WorkUnit),
		maxFeedbackCycles:  toInt(data["max_feedback_cycles"]),
		maxTotalEvalCycles: toInt(data["max_total_eval_cycles"]),
	}
	if cb.maxFeedbackCycles <= 0 {
		cb.maxFeedbackCycles = 2
	}
	if cb.maxTotalEvalCycles <= 0 {
		cb.maxTotalEvalCycles = 5
	}

	if units, ok := data["units"].(map[string]interface{}); ok {
		for id, raw := range units {
			m, ok := raw.(map[string]interface{})
			if !ok {
				continue
			}
			u := &WorkUnit{
				ID:                 id,
				FeedbackCycles:     toInt(m["feedback_cycles"]),
				TotalEvalCycles:    toInt(m["total_eval_cycles"]),
				Reassignments:      toInt(m["reassignments"]),
				MaxFeedbackCycles:  toInt(m["max_feedback_cycles"]),
				MaxTotalEvalCycles: toInt(m["max_total_eval_cycles"]),
			}
			if tripped, ok := m["tripped"].(bool); ok {
				u.Tripped = tripped
			}
			if u.MaxFeedbackCycles <= 0 {
				u.MaxFeedbackCycles = cb.maxFeedbackCycles
			}
			if u.MaxTotalEvalCycles <= 0 {
				u.MaxTotalEvalCycles = cb.maxTotalEvalCycles
			}
			cb.units[id] = u
		}
	}
	return cb
}

// toInt converts an interface{} to int, handling both int and float64.
func toInt(v interface{}) int {
	switch n := v.(type) {
	case int:
		return n
	case float64:
		return int(n)
	case int64:
		return int(n)
	default:
		return 0
	}
}
