// Package runner implements the central StepRunner that ties together
// all orchestrator subsystems: state machine, sessions, circuit breaker,
// agent registry, audit logging, checkpoints, and dispatch tracking.
//
// Ported from Python: governance/engine/orchestrator/runner.py
package runner

import (
	"errors"
	"fmt"
	"time"

	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/audit"
	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/capacity"
	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/checkpoint"
	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/circuitbreaker"
	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/config"
	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/dispatch"
	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/registry"
	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/session"
	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/statemachine"
	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/stepresult"
	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/tree"
)

// ---------------------------------------------------------------------------
// StepRunner
// ---------------------------------------------------------------------------

// StepRunner is the central orchestrator controller. It coordinates phase
// transitions, capacity checks, agent dispatch, and session persistence.
type StepRunner struct {
	config    *config.OrchestratorConfig
	session   *session.PersistedSession
	store     *session.Store
	sm        *statemachine.StateMachine
	cb        *circuitbreaker.CircuitBreaker
	registry  *registry.AgentRegistry
	audit     *audit.Logger
	cpManager *checkpoint.Manager
	dispatch  *dispatch.Tracker
}

// NewStepRunner creates a StepRunner from configuration and a session store.
// Internal subsystems are initialised to defaults; call InitSession to wire
// them to a concrete session.
func NewStepRunner(cfg *config.OrchestratorConfig, store *session.Store) *StepRunner {
	return &StepRunner{
		config:    cfg,
		store:     store,
		sm:        statemachine.New(cfg.ParallelCoders),
		cb:        circuitbreaker.New(cfg.MaxFeedbackCycles, cfg.MaxTotalEvalCycles),
		registry:  registry.New(),
		cpManager: checkpoint.NewManager(cfg.CheckpointDir),
		dispatch:  dispatch.NewTracker(),
	}
}

// ---------------------------------------------------------------------------
// InitSession
// ---------------------------------------------------------------------------

// InitSession creates (or loads) a session and prepares the runner for work.
func (sr *StepRunner) InitSession(sessionID string) (*stepresult.StepResult, error) {
	// Try to load existing session first.
	sess, err := sr.store.Load(sessionID)
	if err != nil {
		// New session.
		sess = session.NewSession(sessionID)
		sess.ParallelCoders = sr.config.ParallelCoders
	}

	sr.session = sess
	sr.audit = audit.NewLogger(sr.config.AuditLogDir, sessionID)

	// Restore subsystem state from session if present.
	if len(sr.session.GateHistory) > 0 || sr.session.Phase > 0 {
		smData := map[string]interface{}{
			"phase":           sr.session.Phase,
			"tool_calls":      sr.session.ToolCalls,
			"turns":           sr.session.Turns,
			"issues_completed": sr.session.IssuesCompleted,
			"parallel_coders": sr.session.ParallelCoders,
			"system_warning":  sr.session.SystemWarning,
			"degraded_recall": sr.session.DegradedRecall,
			"gate_history":    sr.session.GateHistory,
		}
		sr.sm = statemachine.FromDict(smData)
	}

	if len(sr.session.CircuitBreaker) > 0 {
		sr.cb = circuitbreaker.FromDict(sr.session.CircuitBreaker)
	}

	if len(sr.session.AgentRegistry) > 0 {
		sr.registry = registry.FromDict(sr.session.AgentRegistry)
	}

	// Persist initial state.
	if saveErr := sr.saveSession(); saveErr != nil {
		return nil, saveErr
	}

	_ = sr.audit.Log("session_init", sr.sm.Phase(), "", map[string]interface{}{
		"session_id": sessionID,
	})

	return sr.buildResult(nil), nil
}

// ---------------------------------------------------------------------------
// Step
// ---------------------------------------------------------------------------

// Step completes a phase and transitions to the next. The result map
// carries phase-specific output (e.g. issues_selected). agentID identifies
// the caller for audit purposes.
func (sr *StepRunner) Step(completedPhase int, result map[string]interface{}, agentID string) (*stepresult.StepResult, error) {
	if sr.session == nil {
		return nil, fmt.Errorf("runner: no active session — call InitSession first")
	}

	// Determine target phase (next sequential).
	targetPhase := completedPhase + 1

	action, err := sr.sm.Transition(targetPhase)

	// Log the transition attempt.
	_ = sr.audit.Log("step", targetPhase, agentID, map[string]interface{}{
		"completed_phase": completedPhase,
		"action":          string(action),
		"result":          result,
	})

	// Handle shutdown errors from gate checks.
	var shutdownErr *statemachine.ShutdownRequired
	if errors.As(err, &shutdownErr) {
		// Save checkpoint before reporting shutdown.
		cp := &checkpoint.Checkpoint{
			SessionID:     sr.session.SessionID,
			Phase:         targetPhase,
			Tier:          string(shutdownErr.Tier),
			Reason:        shutdownErr.Error(),
			CompletedWork: sr.session.IssuesCompletedList,
			RemainingWork: sr.session.IssuesInFlight,
			State:         result,
		}
		cpPath, _ := sr.cpManager.Save(cp)
		_ = sr.audit.Log("checkpoint_saved", targetPhase, agentID, map[string]interface{}{
			"path": cpPath,
		})

		sr.syncSessionFromSM()
		if saveErr := sr.saveSession(); saveErr != nil {
			return nil, saveErr
		}

		res := sr.buildResult(nil)
		res.Shutdown = true
		res.Details = map[string]interface{}{
			"shutdown_reason": shutdownErr.Error(),
			"checkpoint_path": cpPath,
		}
		return res, nil
	}

	if err != nil {
		return nil, fmt.Errorf("runner: step failed: %w", err)
	}

	sr.syncSessionFromSM()
	if saveErr := sr.saveSession(); saveErr != nil {
		return nil, saveErr
	}

	return sr.buildResult(nil), nil
}

// ---------------------------------------------------------------------------
// RecordSignal
// ---------------------------------------------------------------------------

// RecordSignal records runtime signals (tool_call, turn, issue_completed).
func (sr *StepRunner) RecordSignal(signalType string, count int) (*stepresult.StepResult, error) {
	if sr.session == nil {
		return nil, fmt.Errorf("runner: no active session")
	}

	for i := 0; i < count; i++ {
		switch signalType {
		case "tool_call":
			sr.sm.RecordToolCall()
		case "turn":
			sr.sm.RecordTurn()
		case "issue_completed":
			sr.sm.RecordIssueCompleted()
		default:
			return nil, fmt.Errorf("runner: unknown signal type %q", signalType)
		}
	}

	_ = sr.audit.Log("signal", sr.sm.Phase(), "", map[string]interface{}{
		"signal_type": signalType,
		"count":       count,
	})

	sr.syncSessionFromSM()
	if saveErr := sr.saveSession(); saveErr != nil {
		return nil, saveErr
	}

	return sr.buildResult(nil), nil
}

// ---------------------------------------------------------------------------
// QueryGate
// ---------------------------------------------------------------------------

// QueryGate checks the gate action for a target phase without transitioning.
func (sr *StepRunner) QueryGate(targetPhase int) (*stepresult.StepResult, error) {
	if sr.session == nil {
		return nil, fmt.Errorf("runner: no active session")
	}

	tier := sr.sm.Tier()
	action := capacity.GateAction(targetPhase, tier)

	res := sr.buildResult(nil)
	res.Details = map[string]interface{}{
		"target_phase": targetPhase,
		"gate_action":  string(action),
		"gate_tier":    string(tier),
	}
	return res, nil
}

// ---------------------------------------------------------------------------
// GetStatus
// ---------------------------------------------------------------------------

// GetStatus returns the current orchestrator state without modifying it.
func (sr *StepRunner) GetStatus() (*stepresult.StepResult, error) {
	if sr.session == nil {
		return nil, fmt.Errorf("runner: no active session")
	}

	res := sr.buildResult(nil)
	res.Details = map[string]interface{}{
		"session_id":       sr.session.SessionID,
		"tool_calls":       sr.session.ToolCalls,
		"turns":            sr.session.Turns,
		"issues_completed": sr.session.IssuesCompleted,
		"issues_selected":  sr.session.IssuesSelected,
		"issues_in_flight": sr.session.IssuesInFlight,
		"prs_created":      sr.session.PRsCreated,
		"parallel_coders":  sr.session.ParallelCoders,
		"started_at":       sr.session.StartedAt,
		"updated_at":       sr.session.UpdatedAt,
		"gate_history":     sr.sm.GateHistory(),
		"dispatch_state":   sr.dispatch.ToDict(),
		"circuit_breaker":  sr.cb.ToDict(),
		"agent_registry":   sr.registry.ToDict(),
	}
	return res, nil
}

// ---------------------------------------------------------------------------
// GetWorkloadTree
// ---------------------------------------------------------------------------

// GetWorkloadTree builds and formats the workload tree as a text diagram.
func (sr *StepRunner) GetWorkloadTree() (string, error) {
	if sr.session == nil {
		return "", fmt.Errorf("runner: no active session")
	}

	// Convert dispatch records and registry to the tree builder's format.
	dispatchRecords := sr.dispatch.ToDict()
	registryData := sr.registry.ToDict()

	records := toStringMap(dispatchRecords)
	regMap := make(map[string]map[string]interface{})
	if agents, ok := registryData["agents"].(map[string]interface{}); ok {
		regMap = toStringMap(agents)
	}

	roots := tree.Build(records, regMap)
	return tree.Format(roots), nil
}

// ---------------------------------------------------------------------------
// RegisterAgent
// ---------------------------------------------------------------------------

// RegisterAgent registers a new agent in the registry.
func (sr *StepRunner) RegisterAgent(persona, taskID, correlationID, parentTaskID string) error {
	if sr.session == nil {
		return fmt.Errorf("runner: no active session")
	}

	sr.registry.Register(taskID, persona, correlationID, parentTaskID)

	_ = sr.audit.Log("agent_registered", sr.sm.Phase(), taskID, map[string]interface{}{
		"persona":        persona,
		"correlation_id": correlationID,
		"parent_task_id": parentTaskID,
	})

	sr.session.AgentRegistry = sr.registry.ToDict()
	return sr.saveSession()
}

// ---------------------------------------------------------------------------
// RecordHeartbeat
// ---------------------------------------------------------------------------

// RecordHeartbeat updates the heartbeat for an agent and optionally updates status.
func (sr *StepRunner) RecordHeartbeat(agentID, status string) error {
	if sr.session == nil {
		return fmt.Errorf("runner: no active session")
	}

	if err := sr.registry.RecordHeartbeat(agentID); err != nil {
		return err
	}

	if status != "" {
		if err := sr.registry.UpdateStatus(agentID, registry.AgentStatus(status), nil); err != nil {
			return err
		}
	}

	sr.session.AgentRegistry = sr.registry.ToDict()
	return sr.saveSession()
}

// ---------------------------------------------------------------------------
// DispatchAgent
// ---------------------------------------------------------------------------

// DispatchAgent creates a dispatch record and registers the agent.
func (sr *StepRunner) DispatchAgent(persona, parentTaskID string, assignment map[string]interface{}) (*stepresult.StepResult, error) {
	if sr.session == nil {
		return nil, fmt.Errorf("runner: no active session")
	}

	// Generate a task ID.
	taskID := fmt.Sprintf("%s-%s-%d", persona, sr.session.SessionID, time.Now().UnixNano())
	correlationID := sr.session.SessionID

	// Create dispatch record.
	sr.dispatch.Dispatch(taskID, persona, parentTaskID, correlationID, assignment)

	// Register in agent registry.
	sr.registry.Register(taskID, persona, correlationID, parentTaskID)

	_ = sr.audit.Log("agent_dispatched", sr.sm.Phase(), taskID, map[string]interface{}{
		"persona":        persona,
		"parent_task_id": parentTaskID,
		"assignment":     assignment,
	})

	sr.session.AgentRegistry = sr.registry.ToDict()
	sr.session.DispatchState = sr.dispatch.ToDict()
	if saveErr := sr.saveSession(); saveErr != nil {
		return nil, saveErr
	}

	res := sr.buildResult([]stepresult.DispatchInstruction{
		{
			Persona:      persona,
			TaskID:       taskID,
			ParentTaskID: parentTaskID,
			Assignment:   assignment,
		},
	})
	return res, nil
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

// buildResult constructs a StepResult from current state.
func (sr *StepRunner) buildResult(dispatches []stepresult.DispatchInstruction) *stepresult.StepResult {
	tier := sr.sm.Tier()
	action := capacity.GateAction(sr.sm.Phase(), tier)
	return &stepresult.StepResult{
		Phase:      sr.sm.Phase(),
		Tier:       string(tier),
		Action:     string(action),
		SessionID:  sr.session.SessionID,
		Dispatches: dispatches,
	}
}

// syncSessionFromSM copies state machine counters back to the session.
func (sr *StepRunner) syncSessionFromSM() {
	smDict := sr.sm.ToDict()
	sr.session.Phase = toInt(smDict["phase"])
	sr.session.Tier = string(sr.sm.Tier())
	sr.session.ToolCalls = toInt(smDict["tool_calls"])
	sr.session.Turns = toInt(smDict["turns"])
	sr.session.IssuesCompleted = toInt(smDict["issues_completed"])

	// Persist gate history.
	if gh, ok := smDict["gate_history"].([]interface{}); ok {
		sr.session.GateHistory = gh
	}

	sr.session.CircuitBreaker = sr.cb.ToDict()
	sr.session.AgentRegistry = sr.registry.ToDict()
	sr.session.DispatchState = sr.dispatch.ToDict()
}

// saveSession persists the session to disk.
func (sr *StepRunner) saveSession() error {
	return sr.store.Save(sr.session)
}

// toInt converts interface{} to int, handling float64 from JSON.
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

// toStringMap converts a map[string]interface{} where values are
// map[string]interface{} into a map[string]map[string]interface{}.
func toStringMap(m map[string]interface{}) map[string]map[string]interface{} {
	out := make(map[string]map[string]interface{}, len(m))
	for k, v := range m {
		if vm, ok := v.(map[string]interface{}); ok {
			out[k] = vm
		}
	}
	return out
}
