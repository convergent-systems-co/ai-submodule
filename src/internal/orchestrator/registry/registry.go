// Package registry tracks agent lifecycle within the orchestrator.
// It is thread-safe and supports heartbeat-based liveness detection.
//
// Ported from Python: governance/engine/orchestrator/registry.py
package registry

import (
	"fmt"
	"sync"
	"time"
)

// ---------------------------------------------------------------------------
// AgentStatus
// ---------------------------------------------------------------------------

// AgentStatus represents the lifecycle state of a registered agent.
type AgentStatus string

const (
	StatusRegistered AgentStatus = "registered"
	StatusRunning    AgentStatus = "running"
	StatusCompleted  AgentStatus = "completed"
	StatusFailed     AgentStatus = "failed"
	StatusTimedOut   AgentStatus = "timed_out"
)

// ---------------------------------------------------------------------------
// RegisteredAgent
// ---------------------------------------------------------------------------

// RegisteredAgent holds metadata for one agent instance.
type RegisteredAgent struct {
	TaskID        string      `json:"task_id"`
	Persona       string      `json:"persona"`
	Status        AgentStatus `json:"status"`
	CorrelationID string      `json:"correlation_id"`
	ParentTaskID  string      `json:"parent_task_id"`
	RegisteredAt  time.Time   `json:"registered_at"`
	LastHeartbeat time.Time   `json:"last_heartbeat"`
	Result        interface{} `json:"result,omitempty"`
}

// ---------------------------------------------------------------------------
// AgentRegistry
// ---------------------------------------------------------------------------

// AgentRegistry is a thread-safe store for agent metadata.
type AgentRegistry struct {
	mu               sync.RWMutex
	agents           map[string]*RegisteredAgent
	heartbeatTimeout time.Duration
}

// New creates an AgentRegistry with a 5-minute heartbeat timeout.
func New() *AgentRegistry {
	return &AgentRegistry{
		agents:           make(map[string]*RegisteredAgent),
		heartbeatTimeout: 5 * time.Minute,
	}
}

// Register adds a new agent to the registry.
func (r *AgentRegistry) Register(taskID, persona, correlationID, parentTaskID string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	now := time.Now().UTC()
	r.agents[taskID] = &RegisteredAgent{
		TaskID:        taskID,
		Persona:       persona,
		Status:        StatusRegistered,
		CorrelationID: correlationID,
		ParentTaskID:  parentTaskID,
		RegisteredAt:  now,
		LastHeartbeat: now,
	}
}

// UpdateStatus sets the status (and optional result) for an agent.
func (r *AgentRegistry) UpdateStatus(taskID string, status AgentStatus, result interface{}) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	a, ok := r.agents[taskID]
	if !ok {
		return fmt.Errorf("registry: agent %q not found", taskID)
	}
	a.Status = status
	a.Result = result
	a.LastHeartbeat = time.Now().UTC()
	return nil
}

// RecordHeartbeat updates the last-heartbeat timestamp.
func (r *AgentRegistry) RecordHeartbeat(taskID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	a, ok := r.agents[taskID]
	if !ok {
		return fmt.Errorf("registry: agent %q not found", taskID)
	}
	a.LastHeartbeat = time.Now().UTC()
	return nil
}

// IsAlive returns true if the agent's last heartbeat is within the timeout.
func (r *AgentRegistry) IsAlive(taskID string) bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	a, ok := r.agents[taskID]
	if !ok {
		return false
	}
	return time.Since(a.LastHeartbeat) < r.heartbeatTimeout
}

// GetAgent returns a copy of the agent record, or nil if not found.
func (r *AgentRegistry) GetAgent(taskID string) *RegisteredAgent {
	r.mu.RLock()
	defer r.mu.RUnlock()
	a, ok := r.agents[taskID]
	if !ok {
		return nil
	}
	cpy := *a
	return &cpy
}

// ListByPersona returns copies of all agents matching the persona.
func (r *AgentRegistry) ListByPersona(persona string) []*RegisteredAgent {
	r.mu.RLock()
	defer r.mu.RUnlock()
	var result []*RegisteredAgent
	for _, a := range r.agents {
		if a.Persona == persona {
			cpy := *a
			result = append(result, &cpy)
		}
	}
	return result
}

// ValidateTopology checks that agent relationships are consistent:
// every ParentTaskID references an existing agent (or is empty).
func (r *AgentRegistry) ValidateTopology() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()
	var issues []string
	for id, a := range r.agents {
		if a.ParentTaskID != "" {
			if _, ok := r.agents[a.ParentTaskID]; !ok {
				issues = append(issues, fmt.Sprintf(
					"agent %s references missing parent %s", id, a.ParentTaskID))
			}
		}
	}
	return issues
}

// ToDict serializes the registry to a map for persistence.
func (r *AgentRegistry) ToDict() map[string]interface{} {
	r.mu.RLock()
	defer r.mu.RUnlock()
	agents := make(map[string]interface{}, len(r.agents))
	for id, a := range r.agents {
		agents[id] = map[string]interface{}{
			"task_id":        a.TaskID,
			"persona":        a.Persona,
			"status":         string(a.Status),
			"correlation_id": a.CorrelationID,
			"parent_task_id": a.ParentTaskID,
			"registered_at":  a.RegisteredAt.Format(time.RFC3339),
			"last_heartbeat": a.LastHeartbeat.Format(time.RFC3339),
			"result":         a.Result,
		}
	}
	return map[string]interface{}{
		"agents":            agents,
		"heartbeat_timeout": r.heartbeatTimeout.String(),
	}
}

// FromDict restores an AgentRegistry from a serialized map.
func FromDict(data map[string]interface{}) *AgentRegistry {
	reg := New()
	agents, ok := data["agents"].(map[string]interface{})
	if !ok {
		return reg
	}
	for id, raw := range agents {
		m, ok := raw.(map[string]interface{})
		if !ok {
			continue
		}
		a := &RegisteredAgent{
			TaskID:        id,
			Persona:       strVal(m, "persona"),
			Status:        AgentStatus(strVal(m, "status")),
			CorrelationID: strVal(m, "correlation_id"),
			ParentTaskID:  strVal(m, "parent_task_id"),
			Result:        m["result"],
		}
		if t, err := time.Parse(time.RFC3339, strVal(m, "registered_at")); err == nil {
			a.RegisteredAt = t
		}
		if t, err := time.Parse(time.RFC3339, strVal(m, "last_heartbeat")); err == nil {
			a.LastHeartbeat = t
		}
		reg.agents[id] = a
	}
	return reg
}

// strVal extracts a string from a map.
func strVal(m map[string]interface{}, key string) string {
	v, _ := m[key].(string)
	return v
}
