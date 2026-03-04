// Package statemachine implements the phase state machine for the orchestrator.
// It enforces valid phase transitions, performs capacity gate checks on every
// transition, and records a gate history for auditing.
//
// Ported from Python: governance/engine/orchestrator/state_machine.py
package statemachine

import (
	"fmt"

	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/capacity"
)

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

// InvalidTransition is returned when a phase transition is not permitted.
type InvalidTransition struct {
	From int
	To   int
}

func (e *InvalidTransition) Error() string {
	return fmt.Sprintf("invalid transition: phase %d → %d", e.From, e.To)
}

// ShutdownRequired is returned when a gate check demands checkpoint or stop.
type ShutdownRequired struct {
	Tier        capacity.Tier
	Action      capacity.Action
	GatesPassed int
	Signals     capacity.Signals
}

func (e *ShutdownRequired) Error() string {
	return fmt.Sprintf(
		"shutdown required: tier=%s action=%s gates_passed=%d",
		e.Tier, e.Action, e.GatesPassed,
	)
}

// ---------------------------------------------------------------------------
// Valid transitions
// ---------------------------------------------------------------------------

// validTransitions maps each phase to its set of legal target phases.
var validTransitions = map[int]map[int]bool{
	0: {1: true, 2: true, 3: true, 4: true, 5: true, 6: true, 7: true},
	1: {2: true},
	2: {3: true},
	3: {4: true},
	4: {3: true, 5: true},
	5: {1: true, 6: true},
	6: {7: true},
	7: {1: true},
}

// ---------------------------------------------------------------------------
// GateRecord
// ---------------------------------------------------------------------------

// GateRecord captures one gate-check evaluation for the audit log.
type GateRecord struct {
	Phase           int    `json:"phase"`
	Tier            string `json:"tier"`
	Action          string `json:"action"`
	ToolCalls       int    `json:"tool_calls"`
	Turns           int    `json:"turns"`
	IssuesCompleted int    `json:"issues_completed"`
}

// ---------------------------------------------------------------------------
// StateMachine
// ---------------------------------------------------------------------------

// StateMachine tracks the current orchestrator phase, runtime signals,
// and gate-check history.
type StateMachine struct {
	phase          int
	signals        capacity.Signals
	gateHistory    []GateRecord
	parallelCoders int
}

// New creates a StateMachine with the given parallel-coder count.
// If parallelCoders <= 0 it defaults to 5.
func New(parallelCoders int) *StateMachine {
	if parallelCoders <= 0 {
		parallelCoders = 5
	}
	return &StateMachine{
		phase:          0,
		signals:        capacity.Signals{ParallelCoders: parallelCoders},
		gateHistory:    nil,
		parallelCoders: parallelCoders,
	}
}

// Phase returns the current phase number.
func (sm *StateMachine) Phase() int { return sm.phase }

// Tier returns the current capacity tier based on accumulated signals.
func (sm *StateMachine) Tier() capacity.Tier {
	return capacity.ClassifyTier(sm.signals)
}

// Transition attempts to move from the current phase to target.
// It validates the transition, performs a gate check, and records the result.
// Returns the gate action or an error.
func (sm *StateMachine) Transition(target int) (capacity.Action, error) {
	// Validate transition.
	allowed, ok := validTransitions[sm.phase]
	if !ok || !allowed[target] {
		return "", &InvalidTransition{From: sm.phase, To: target}
	}

	// Gate check.
	tier := sm.Tier()
	action := capacity.GateAction(target, tier)

	// Record.
	sm.gateHistory = append(sm.gateHistory, GateRecord{
		Phase:           target,
		Tier:            string(tier),
		Action:          string(action),
		ToolCalls:       sm.signals.ToolCalls,
		Turns:           sm.signals.Turns,
		IssuesCompleted: sm.signals.IssuesCompleted,
	})

	// Shutdown actions.
	if action == capacity.Checkpoint || action == capacity.EmergencyStop {
		sm.phase = target
		return action, &ShutdownRequired{
			Tier:        tier,
			Action:      action,
			GatesPassed: len(sm.gateHistory),
			Signals:     sm.signals,
		}
	}

	sm.phase = target
	return action, nil
}

// RecordToolCall increments the tool-call counter and returns the new tier.
func (sm *StateMachine) RecordToolCall() capacity.Tier {
	sm.signals.ToolCalls++
	return sm.Tier()
}

// RecordTurn increments the turn counter and returns the new tier.
func (sm *StateMachine) RecordTurn() capacity.Tier {
	sm.signals.Turns++
	return sm.Tier()
}

// RecordIssueCompleted increments the issues-completed counter and returns the new tier.
func (sm *StateMachine) RecordIssueCompleted() capacity.Tier {
	sm.signals.IssuesCompleted++
	return sm.Tier()
}

// GateHistory returns a copy of the gate-check history.
func (sm *StateMachine) GateHistory() []GateRecord {
	out := make([]GateRecord, len(sm.gateHistory))
	copy(out, sm.gateHistory)
	return out
}

// ToDict serializes the state machine to a map for JSON persistence.
func (sm *StateMachine) ToDict() map[string]interface{} {
	history := make([]interface{}, len(sm.gateHistory))
	for i, r := range sm.gateHistory {
		history[i] = map[string]interface{}{
			"phase":            r.Phase,
			"tier":             r.Tier,
			"action":           r.Action,
			"tool_calls":       r.ToolCalls,
			"turns":            r.Turns,
			"issues_completed": r.IssuesCompleted,
		}
	}
	return map[string]interface{}{
		"phase":           sm.phase,
		"tool_calls":      sm.signals.ToolCalls,
		"turns":           sm.signals.Turns,
		"issues_completed": sm.signals.IssuesCompleted,
		"parallel_coders": sm.parallelCoders,
		"system_warning":  sm.signals.SystemWarning,
		"degraded_recall": sm.signals.DegradedRecall,
		"gate_history":    history,
	}
}

// FromDict restores a StateMachine from a serialized map (as produced by ToDict).
func FromDict(data map[string]interface{}) *StateMachine {
	sm := &StateMachine{}
	sm.phase = toInt(data["phase"])
	sm.signals.ToolCalls = toInt(data["tool_calls"])
	sm.signals.Turns = toInt(data["turns"])
	sm.signals.IssuesCompleted = toInt(data["issues_completed"])
	sm.parallelCoders = toInt(data["parallel_coders"])
	if sm.parallelCoders <= 0 {
		sm.parallelCoders = 5
	}
	sm.signals.ParallelCoders = sm.parallelCoders

	if sw, ok := data["system_warning"].(bool); ok {
		sm.signals.SystemWarning = sw
	}
	if dr, ok := data["degraded_recall"].(bool); ok {
		sm.signals.DegradedRecall = dr
	}

	if hist, ok := data["gate_history"].([]interface{}); ok {
		for _, entry := range hist {
			if m, ok := entry.(map[string]interface{}); ok {
				sm.gateHistory = append(sm.gateHistory, GateRecord{
					Phase:           toInt(m["phase"]),
					Tier:            fmt.Sprintf("%v", m["tier"]),
					Action:          fmt.Sprintf("%v", m["action"]),
					ToolCalls:       toInt(m["tool_calls"]),
					Turns:           toInt(m["turns"]),
					IssuesCompleted: toInt(m["issues_completed"]),
				})
			}
		}
	}

	return sm
}

// toInt converts an interface{} to int, handling both int and float64
// (the latter is common after JSON round-tripping).
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
