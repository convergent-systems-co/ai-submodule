// Package stepresult defines the return type for orchestrator step operations.
// Every StepRunner method returns a StepResult that captures the current phase,
// tier, action, and optional dispatch instructions.
//
// Ported from Python: governance/engine/orchestrator/step_result.py
package stepresult

// StepResult is the unified return value for all orchestrator operations.
type StepResult struct {
	Phase      int                    `json:"phase"`
	Tier       string                 `json:"tier"`
	Action     string                 `json:"action"`
	SessionID  string                 `json:"session_id"`
	Shutdown   bool                   `json:"shutdown"`
	Details    map[string]interface{} `json:"details,omitempty"`
	Dispatches []DispatchInstruction  `json:"dispatches,omitempty"`
}

// DispatchInstruction tells the caller to spawn an agent.
type DispatchInstruction struct {
	Persona      string                 `json:"persona"`
	TaskID       string                 `json:"task_id"`
	ParentTaskID string                 `json:"parent_task_id,omitempty"`
	Assignment   map[string]interface{} `json:"assignment,omitempty"`
}
