package topology

import "fmt"

// AgentRegistration represents a registered agent in the topology tree.
type AgentRegistration struct {
	AgentID      string      `json:"agent_id"`
	Role         PersonaRole `json:"role"`
	ParentTaskID string      `json:"parent_task_id,omitempty"`
	ChildTaskIDs []string    `json:"child_task_ids,omitempty"`
	Phase        int         `json:"phase"`
}

// ValidationResult holds the outcome of a topology validation.
type ValidationResult struct {
	Valid      bool     `json:"valid"`
	Warnings  []string `json:"warnings,omitempty"`
	Violations []string `json:"violations,omitempty"`
}

// ValidateRegistration validates a single agent registration.
func ValidateRegistration(reg AgentRegistration, pmModeEnabled bool) error {
	if reg.AgentID == "" {
		return &TopologyViolation{
			Constraint: "agent_id_required",
			Message:    "AgentID must not be empty",
		}
	}

	// PM must have no parent
	if reg.Role == RolePM && reg.ParentTaskID != "" {
		return &TopologyViolation{
			Constraint: "pm_no_parent",
			Message:    "PM persona must not have a ParentTaskID",
		}
	}

	// In PM mode, non-PM agents must have a parent
	if pmModeEnabled && reg.Role != RolePM && reg.ParentTaskID == "" {
		return &TopologyViolation{
			Constraint: "parent_required_in_pm_mode",
			Message:    fmt.Sprintf("ParentTaskID required in PM mode for %s agent %q", reg.Role, reg.AgentID),
		}
	}

	return nil
}

// PhaseTransition validates a phase transition against the agent registry.
func PhaseTransition(currentPhase, targetPhase int, registry []AgentRegistration, pmModeEnabled bool) error {
	// Validate sequential phase progression (no skipping)
	if targetPhase != currentPhase+1 {
		return &InvalidPhaseTransition{
			CurrentPhase: currentPhase,
			TargetPhase:  targetPhase,
			Constraint:   "sequential_phases",
			Message:      fmt.Sprintf("phases must be sequential; expected %d, got %d", currentPhase+1, targetPhase),
		}
	}

	// Validate individual registrations
	for _, reg := range registry {
		if err := ValidateRegistration(reg, pmModeEnabled); err != nil {
			return &InvalidPhaseTransition{
				CurrentPhase: currentPhase,
				TargetPhase:  targetPhase,
				Constraint:   "invalid_registration",
				Message:      err.Error(),
			}
		}
	}

	// Check tree constraints in PM mode
	if pmModeEnabled {
		if err := CheckCodersHaveTechLeads(registry); err != nil {
			return &InvalidPhaseTransition{
				CurrentPhase: currentPhase,
				TargetPhase:  targetPhase,
				Constraint:   "coders_have_techleads",
				Message:      err.Error(),
			}
		}

		if err := CheckDevOpsExists(registry); err != nil {
			return &InvalidPhaseTransition{
				CurrentPhase: currentPhase,
				TargetPhase:  targetPhase,
				Constraint:   "devops_exists",
				Message:      err.Error(),
			}
		}

		if err := CheckParentChildRelationships(registry); err != nil {
			return &InvalidPhaseTransition{
				CurrentPhase: currentPhase,
				TargetPhase:  targetPhase,
				Constraint:   "parent_child",
				Message:      err.Error(),
			}
		}
	}

	return nil
}

// ValidateTopology runs all topology checks and returns a ValidationResult.
// Unlike PhaseTransition, this collects all violations and warnings instead
// of failing on the first error.
func ValidateTopology(registry []AgentRegistration, pmModeEnabled bool) *ValidationResult {
	result := &ValidationResult{Valid: true}

	// Validate individual registrations
	for _, reg := range registry {
		if err := ValidateRegistration(reg, pmModeEnabled); err != nil {
			result.Valid = false
			result.Violations = append(result.Violations, err.Error())
		}
	}

	if pmModeEnabled {
		// Check coders have tech leads
		if err := CheckCodersHaveTechLeads(registry); err != nil {
			result.Valid = false
			result.Violations = append(result.Violations, err.Error())
		}

		// Check devops exists
		if err := CheckDevOpsExists(registry); err != nil {
			result.Valid = false
			result.Violations = append(result.Violations, err.Error())
		}

		// Check parent-child relationships (cycles)
		if err := CheckParentChildRelationships(registry); err != nil {
			result.Valid = false
			result.Violations = append(result.Violations, err.Error())
		}

		// Check tech leads have coders (warning, not violation)
		if err := CheckTechLeadsHaveCoders(registry); err != nil {
			result.Warnings = append(result.Warnings, err.Error())
		}
	}

	return result
}

// CheckParentChildRelationships validates that all parent references point
// to agents that exist in the registry, and detects cycles.
func CheckParentChildRelationships(registry []AgentRegistration) error {
	agentByID := make(map[string]*AgentRegistration, len(registry))
	for i := range registry {
		agentByID[registry[i].AgentID] = &registry[i]
	}

	// Check that all parent references are valid
	for _, reg := range registry {
		if reg.ParentTaskID == "" {
			continue
		}
		if _, exists := agentByID[reg.ParentTaskID]; !exists {
			return &TopologyViolation{
				Constraint: "parent_exists",
				Message:    fmt.Sprintf("agent %q references parent %q which does not exist in registry", reg.AgentID, reg.ParentTaskID),
			}
		}
	}

	// Detect cycles using a visited set per traversal
	for _, reg := range registry {
		if reg.ParentTaskID == "" {
			continue
		}
		visited := make(map[string]bool)
		current := reg.AgentID
		for current != "" {
			if visited[current] {
				return &TopologyViolation{
					Constraint: "no_cycles",
					Message:    fmt.Sprintf("cycle detected involving agent %q", current),
				}
			}
			visited[current] = true
			parent, exists := agentByID[current]
			if !exists {
				break
			}
			current = parent.ParentTaskID
		}
	}

	return nil
}

// CheckCodersHaveTechLeads verifies that every Coder has a TechLead parent.
func CheckCodersHaveTechLeads(registry []AgentRegistration) error {
	agentByID := make(map[string]*AgentRegistration, len(registry))
	for i := range registry {
		agentByID[registry[i].AgentID] = &registry[i]
	}

	for _, reg := range registry {
		if reg.Role != RoleCoder {
			continue
		}
		if reg.ParentTaskID == "" {
			return &TopologyViolation{
				Constraint: "coder_has_techlead",
				Message:    fmt.Sprintf("Coder agent %q has no parent; every Coder must have a TechLead parent", reg.AgentID),
			}
		}
		parent, exists := agentByID[reg.ParentTaskID]
		if !exists {
			return &TopologyViolation{
				Constraint: "coder_has_techlead",
				Message:    fmt.Sprintf("Coder agent %q references parent %q which does not exist", reg.AgentID, reg.ParentTaskID),
			}
		}
		if parent.Role != RoleTechLead {
			return &TopologyViolation{
				Constraint: "coder_has_techlead",
				Message:    fmt.Sprintf("Coder agent %q has parent %q with role %s; expected TechLead", reg.AgentID, reg.ParentTaskID, parent.Role),
			}
		}
	}

	return nil
}

// CheckTechLeadsHaveCoders verifies that every TechLead has at least one Coder child.
// This returns a TopologyWarning (not a hard violation) since a TechLead without
// coders is degraded but functional.
func CheckTechLeadsHaveCoders(registry []AgentRegistration) error {
	techLeadIDs := make(map[string]bool)
	for _, reg := range registry {
		if reg.Role == RoleTechLead {
			techLeadIDs[reg.AgentID] = true
		}
	}

	if len(techLeadIDs) == 0 {
		return nil
	}

	// Find which tech leads have coder children
	techLeadsWithCoders := make(map[string]bool)
	for _, reg := range registry {
		if reg.Role == RoleCoder && reg.ParentTaskID != "" {
			techLeadsWithCoders[reg.ParentTaskID] = true
		}
	}

	for id := range techLeadIDs {
		if !techLeadsWithCoders[id] {
			return &TopologyWarning{
				Constraint: "techLead_has_coders",
				Message:    fmt.Sprintf("TechLead agent %q has no Coder children; topology is degraded", id),
			}
		}
	}

	return nil
}

// CheckDevOpsExists verifies that at least one DevOps agent exists in PM mode.
func CheckDevOpsExists(registry []AgentRegistration) error {
	for _, reg := range registry {
		if reg.Role == RoleDevOps {
			return nil
		}
	}
	return &TopologyViolation{
		Constraint: "devops_required",
		Message:    "no DevOps agent found in registry; DevOps is required in PM mode",
	}
}
