// Package capacity implements context-aware tier classification for the
// orchestrator. Each combination of phase and tier maps to a gate action
// that controls whether the orchestrator may proceed, must skip, or must
// checkpoint/stop.
//
// Ported from Python: governance/engine/orchestrator/capacity.py
package capacity

import "fmt"

// ---------------------------------------------------------------------------
// Tier
// ---------------------------------------------------------------------------

// Tier represents the current context-capacity level.
type Tier string

const (
	Green  Tier = "green"
	Yellow Tier = "yellow"
	Orange Tier = "orange"
	Red    Tier = "red"
)

// String returns the tier name.
func (t Tier) String() string { return string(t) }

// ---------------------------------------------------------------------------
// Action
// ---------------------------------------------------------------------------

// Action is the gate decision for a given phase+tier pair.
type Action string

const (
	Proceed       Action = "proceed"
	SkipDispatch  Action = "skip_dispatch"
	FinishCurrent Action = "finish_current"
	Checkpoint    Action = "checkpoint"
	EmergencyStop Action = "emergency_stop"
)

// String returns the action name.
func (a Action) String() string { return string(a) }

// ---------------------------------------------------------------------------
// Signals
// ---------------------------------------------------------------------------

// Signals aggregates the runtime counters used for tier classification.
type Signals struct {
	ToolCalls      int
	Turns          int
	IssuesCompleted int
	ParallelCoders int
	SystemWarning  bool
	DegradedRecall bool
}

// ---------------------------------------------------------------------------
// ClassifyTier
// ---------------------------------------------------------------------------

// ClassifyTier maps a set of runtime signals to a capacity tier.
func ClassifyTier(s Signals) Tier {
	// Hard red: system-level warnings override everything.
	if s.SystemWarning || s.DegradedRecall {
		return Red
	}

	pc := s.ParallelCoders
	if pc < 1 {
		pc = 1
	}

	// Red thresholds.
	redIssues := pc * 2
	if redIssues < 10 {
		redIssues = 10
	}
	if s.ToolCalls >= 200 || s.Turns >= 30 || s.IssuesCompleted >= redIssues {
		return Red
	}

	// Orange thresholds.
	orangeIssues := int(float64(pc) * 1.5)
	if orangeIssues < 7 {
		orangeIssues = 7
	}
	if s.ToolCalls >= 150 || s.Turns >= 20 || s.IssuesCompleted >= orangeIssues {
		return Orange
	}

	// Yellow thresholds.
	yellowIssues := pc
	if yellowIssues < 5 {
		yellowIssues = 5
	}
	if s.ToolCalls >= 100 || s.Turns >= 15 || s.IssuesCompleted >= yellowIssues {
		return Yellow
	}

	return Green
}

// ---------------------------------------------------------------------------
// GateAction — 8x4 decision matrix
// ---------------------------------------------------------------------------

// gateMatrix encodes the phase (0-7) x tier (Green/Yellow/Orange/Red) matrix.
// Index: gateMatrix[phase][tier]
var gateMatrix = map[int]map[Tier]Action{
	0: {Green: Proceed, Yellow: Proceed, Orange: Proceed, Red: Proceed},             // Recovery
	1: {Green: Proceed, Yellow: Proceed, Orange: SkipDispatch, Red: Checkpoint},      // Pre-flight
	2: {Green: Proceed, Yellow: SkipDispatch, Orange: SkipDispatch, Red: Checkpoint}, // Planning
	3: {Green: Proceed, Yellow: Proceed, Orange: FinishCurrent, Red: EmergencyStop},  // Dispatch
	4: {Green: Proceed, Yellow: Proceed, Orange: FinishCurrent, Red: Checkpoint},     // Collect
	5: {Green: Proceed, Yellow: Proceed, Orange: FinishCurrent, Red: Checkpoint},     // Merge
	6: {Green: Proceed, Yellow: Proceed, Orange: Checkpoint, Red: EmergencyStop},     // Build
	7: {Green: Proceed, Yellow: SkipDispatch, Orange: Checkpoint, Red: EmergencyStop}, // Deploy
}

// GateAction returns the prescribed action for a phase and tier.
// Unknown phases default to Checkpoint.
func GateAction(phase int, tier Tier) Action {
	row, ok := gateMatrix[phase]
	if !ok {
		return Checkpoint
	}
	action, ok := row[tier]
	if !ok {
		return Checkpoint
	}
	return action
}

// ---------------------------------------------------------------------------
// FormatGateBlock
// ---------------------------------------------------------------------------

// FormatGateBlock returns a human-readable gate-check summary block.
func FormatGateBlock(phase int, tier Tier, action Action) string {
	return fmt.Sprintf(
		"GATE CHECK — phase=%d tier=%s action=%s",
		phase, tier, action,
	)
}
