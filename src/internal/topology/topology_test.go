package topology

import (
	"os"
	"path/filepath"
	"testing"
)

// --- PersonaRole tests ---

func TestPersonaRoleString(t *testing.T) {
	tests := []struct {
		role PersonaRole
		want string
	}{
		{RolePM, "PM"},
		{RoleTechLead, "TechLead"},
		{RoleCoder, "Coder"},
		{RoleDevOps, "DevOps"},
		{PersonaRole(99), "Unknown"},
	}

	for _, tt := range tests {
		got := tt.role.String()
		if got != tt.want {
			t.Errorf("PersonaRole(%d).String() = %q, want %q", tt.role, got, tt.want)
		}
	}
}

func TestActionString(t *testing.T) {
	tests := []struct {
		action Action
		want   string
	}{
		{ActionSpawn, "Spawn"},
		{ActionWait, "Wait"},
		{ActionAdvance, "Advance"},
		{ActionReview, "Review"},
		{ActionPlan, "Plan"},
		{ActionImplement, "Implement"},
		{ActionTest, "Test"},
		{ActionCommit, "Commit"},
		{ActionMerge, "Merge"},
		{ActionRebase, "Rebase"},
		{ActionPush, "Push"},
		{Action(99), "Unknown"},
	}

	for _, tt := range tests {
		got := tt.action.String()
		if got != tt.want {
			t.Errorf("Action(%d).String() = %q, want %q", tt.action, got, tt.want)
		}
	}
}

func TestCanExecute(t *testing.T) {
	tests := []struct {
		name   string
		role   PersonaRole
		action Action
		want   bool
	}{
		// PM allowed actions
		{"PM can Spawn", RolePM, ActionSpawn, true},
		{"PM can Wait", RolePM, ActionWait, true},
		{"PM can Review", RolePM, ActionReview, true},
		{"PM can Advance", RolePM, ActionAdvance, true},
		// PM disallowed actions
		{"PM cannot Implement", RolePM, ActionImplement, false},
		{"PM cannot Commit", RolePM, ActionCommit, false},
		{"PM cannot Push", RolePM, ActionPush, false},
		{"PM cannot Plan", RolePM, ActionPlan, false},
		{"PM cannot Test", RolePM, ActionTest, false},
		{"PM cannot Merge", RolePM, ActionMerge, false},

		// TechLead allowed actions
		{"TechLead can Plan", RoleTechLead, ActionPlan, true},
		{"TechLead can Spawn", RoleTechLead, ActionSpawn, true},
		{"TechLead can Review", RoleTechLead, ActionReview, true},
		// TechLead disallowed actions
		{"TechLead cannot Implement", RoleTechLead, ActionImplement, false},
		{"TechLead cannot Commit", RoleTechLead, ActionCommit, false},
		{"TechLead cannot Merge", RoleTechLead, ActionMerge, false},

		// Coder allowed actions
		{"Coder can Implement", RoleCoder, ActionImplement, true},
		{"Coder can Test", RoleCoder, ActionTest, true},
		{"Coder can Commit", RoleCoder, ActionCommit, true},
		// Coder disallowed actions
		{"Coder cannot Spawn", RoleCoder, ActionSpawn, false},
		{"Coder cannot Review", RoleCoder, ActionReview, false},
		{"Coder cannot Merge", RoleCoder, ActionMerge, false},
		{"Coder cannot Push", RoleCoder, ActionPush, false},

		// DevOps allowed actions
		{"DevOps can Merge", RoleDevOps, ActionMerge, true},
		{"DevOps can Rebase", RoleDevOps, ActionRebase, true},
		{"DevOps can Push", RoleDevOps, ActionPush, true},
		// DevOps disallowed actions
		{"DevOps cannot Implement", RoleDevOps, ActionImplement, false},
		{"DevOps cannot Spawn", RoleDevOps, ActionSpawn, false},
		{"DevOps cannot Plan", RoleDevOps, ActionPlan, false},

		// Unknown role
		{"Unknown role cannot do anything", PersonaRole(99), ActionSpawn, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := CanExecute(tt.role, tt.action)
			if got != tt.want {
				t.Errorf("CanExecute(%s, %s) = %v, want %v", tt.role, tt.action, got, tt.want)
			}
		})
	}
}

func TestAllowedActions(t *testing.T) {
	tests := []struct {
		role     PersonaRole
		wantLen  int
		contains Action
	}{
		{RolePM, 4, ActionSpawn},
		{RoleTechLead, 3, ActionPlan},
		{RoleCoder, 3, ActionImplement},
		{RoleDevOps, 3, ActionMerge},
	}

	for _, tt := range tests {
		actions := AllowedActions(tt.role)
		if len(actions) != tt.wantLen {
			t.Errorf("AllowedActions(%s) returned %d actions, want %d", tt.role, len(actions), tt.wantLen)
		}
		found := false
		for _, a := range actions {
			if a == tt.contains {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("AllowedActions(%s) does not contain %s", tt.role, tt.contains)
		}
	}

	// Unknown role returns nil
	if actions := AllowedActions(PersonaRole(99)); actions != nil {
		t.Errorf("AllowedActions(Unknown) = %v, want nil", actions)
	}
}

func TestParseRole(t *testing.T) {
	tests := []struct {
		input string
		want  PersonaRole
		ok    bool
	}{
		{"PM", RolePM, true},
		{"TechLead", RoleTechLead, true},
		{"Coder", RoleCoder, true},
		{"DevOps", RoleDevOps, true},
		{"invalid", RolePM, false},
		{"", RolePM, false},
	}

	for _, tt := range tests {
		got, ok := ParseRole(tt.input)
		if ok != tt.ok {
			t.Errorf("ParseRole(%q) ok = %v, want %v", tt.input, ok, tt.ok)
		}
		if ok && got != tt.want {
			t.Errorf("ParseRole(%q) = %v, want %v", tt.input, got, tt.want)
		}
	}
}

func TestAllRoles(t *testing.T) {
	roles := AllRoles()
	if len(roles) != 4 {
		t.Errorf("AllRoles() returned %d roles, want 4", len(roles))
	}
}

// --- ValidateRegistration tests ---

func TestValidateRegistration(t *testing.T) {
	tests := []struct {
		name          string
		reg           AgentRegistration
		pmModeEnabled bool
		wantErr       bool
		errContains   string
	}{
		{
			name:          "valid PM registration",
			reg:           AgentRegistration{AgentID: "pm-1", Role: RolePM},
			pmModeEnabled: true,
			wantErr:       false,
		},
		{
			name:          "PM with parent task ID is invalid",
			reg:           AgentRegistration{AgentID: "pm-1", Role: RolePM, ParentTaskID: "some-parent"},
			pmModeEnabled: true,
			wantErr:       true,
			errContains:   "pm_no_parent",
		},
		{
			name:          "empty agent ID",
			reg:           AgentRegistration{Role: RoleCoder},
			pmModeEnabled: false,
			wantErr:       true,
			errContains:   "agent_id_required",
		},
		{
			name:          "Coder without parent in PM mode",
			reg:           AgentRegistration{AgentID: "coder-1", Role: RoleCoder},
			pmModeEnabled: true,
			wantErr:       true,
			errContains:   "parent_required_in_pm_mode",
		},
		{
			name:          "Coder without parent in non-PM mode is ok",
			reg:           AgentRegistration{AgentID: "coder-1", Role: RoleCoder},
			pmModeEnabled: false,
			wantErr:       false,
		},
		{
			name:          "TechLead with parent in PM mode",
			reg:           AgentRegistration{AgentID: "tl-1", Role: RoleTechLead, ParentTaskID: "pm-1"},
			pmModeEnabled: true,
			wantErr:       false,
		},
		{
			name:          "DevOps with parent in PM mode",
			reg:           AgentRegistration{AgentID: "devops-1", Role: RoleDevOps, ParentTaskID: "pm-1"},
			pmModeEnabled: true,
			wantErr:       false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateRegistration(tt.reg, tt.pmModeEnabled)
			if tt.wantErr {
				if err == nil {
					t.Fatalf("expected error containing %q, got nil", tt.errContains)
				}
				if tt.errContains != "" && !containsStr(err.Error(), tt.errContains) {
					t.Errorf("error %q does not contain %q", err.Error(), tt.errContains)
				}
			} else if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
		})
	}
}

// --- PhaseTransition tests ---

func TestPhaseTransition(t *testing.T) {
	validPMRegistry := []AgentRegistration{
		{AgentID: "pm-1", Role: RolePM, Phase: 0},
		{AgentID: "tl-1", Role: RoleTechLead, ParentTaskID: "pm-1", Phase: 0},
		{AgentID: "coder-1", Role: RoleCoder, ParentTaskID: "tl-1", Phase: 0},
		{AgentID: "devops-1", Role: RoleDevOps, ParentTaskID: "pm-1", Phase: 0},
	}

	tests := []struct {
		name          string
		currentPhase  int
		targetPhase   int
		registry      []AgentRegistration
		pmModeEnabled bool
		wantErr       bool
		errContains   string
	}{
		{
			name:          "valid PM transition 0->1",
			currentPhase:  0,
			targetPhase:   1,
			registry:      validPMRegistry,
			pmModeEnabled: true,
			wantErr:       false,
		},
		{
			name:          "phase skip 0->2",
			currentPhase:  0,
			targetPhase:   2,
			registry:      validPMRegistry,
			pmModeEnabled: true,
			wantErr:       true,
			errContains:   "sequential_phases",
		},
		{
			name:          "phase backward 2->1",
			currentPhase:  2,
			targetPhase:   1,
			registry:      validPMRegistry,
			pmModeEnabled: true,
			wantErr:       true,
			errContains:   "sequential_phases",
		},
		{
			name:         "missing TechLead parent for coder",
			currentPhase: 0,
			targetPhase:  1,
			registry: []AgentRegistration{
				{AgentID: "pm-1", Role: RolePM, Phase: 0},
				{AgentID: "coder-1", Role: RoleCoder, ParentTaskID: "pm-1", Phase: 0},
				{AgentID: "devops-1", Role: RoleDevOps, ParentTaskID: "pm-1", Phase: 0},
			},
			pmModeEnabled: true,
			wantErr:       true,
			errContains:   "coder_has_techlead",
		},
		{
			name:         "no DevOps in PM mode",
			currentPhase: 0,
			targetPhase:  1,
			registry: []AgentRegistration{
				{AgentID: "pm-1", Role: RolePM, Phase: 0},
				{AgentID: "tl-1", Role: RoleTechLead, ParentTaskID: "pm-1", Phase: 0},
				{AgentID: "coder-1", Role: RoleCoder, ParentTaskID: "tl-1", Phase: 0},
			},
			pmModeEnabled: true,
			wantErr:       true,
			errContains:   "devops_exists",
		},
		{
			name:         "non-PM mode skips tree checks",
			currentPhase: 0,
			targetPhase:  1,
			registry: []AgentRegistration{
				{AgentID: "coder-1", Role: RoleCoder, Phase: 0},
			},
			pmModeEnabled: false,
			wantErr:       false,
		},
		{
			name:         "invalid registration in registry",
			currentPhase: 0,
			targetPhase:  1,
			registry: []AgentRegistration{
				{AgentID: "", Role: RoleCoder, Phase: 0},
			},
			pmModeEnabled: false,
			wantErr:       true,
			errContains:   "invalid_registration",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := PhaseTransition(tt.currentPhase, tt.targetPhase, tt.registry, tt.pmModeEnabled)
			if tt.wantErr {
				if err == nil {
					t.Fatalf("expected error containing %q, got nil", tt.errContains)
				}
				if tt.errContains != "" && !containsStr(err.Error(), tt.errContains) {
					t.Errorf("error %q does not contain %q", err.Error(), tt.errContains)
				}
			} else if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
		})
	}
}

// --- ValidateTopology tests ---

func TestValidateTopology(t *testing.T) {
	t.Run("valid PM topology", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "pm-1", Role: RolePM},
			{AgentID: "tl-1", Role: RoleTechLead, ParentTaskID: "pm-1"},
			{AgentID: "coder-1", Role: RoleCoder, ParentTaskID: "tl-1"},
			{AgentID: "devops-1", Role: RoleDevOps, ParentTaskID: "pm-1"},
		}
		result := ValidateTopology(registry, true)
		if !result.Valid {
			t.Errorf("expected valid topology, got violations: %v", result.Violations)
		}
	})

	t.Run("techlead without coders is warning", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "pm-1", Role: RolePM},
			{AgentID: "tl-1", Role: RoleTechLead, ParentTaskID: "pm-1"},
			{AgentID: "devops-1", Role: RoleDevOps, ParentTaskID: "pm-1"},
		}
		result := ValidateTopology(registry, true)
		if !result.Valid {
			t.Errorf("expected valid topology (warning only), got violations: %v", result.Violations)
		}
		if len(result.Warnings) == 0 {
			t.Error("expected warning for TechLead without coders")
		}
	})

	t.Run("collects multiple violations", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "pm-1", Role: RolePM, ParentTaskID: "invalid"},
			{AgentID: "coder-1", Role: RoleCoder},
		}
		result := ValidateTopology(registry, true)
		if result.Valid {
			t.Error("expected invalid topology")
		}
		if len(result.Violations) < 2 {
			t.Errorf("expected at least 2 violations, got %d: %v", len(result.Violations), result.Violations)
		}
	})
}

// --- CheckParentChildRelationships tests ---

func TestCheckParentChildRelationships(t *testing.T) {
	t.Run("valid tree", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "pm-1", Role: RolePM},
			{AgentID: "tl-1", Role: RoleTechLead, ParentTaskID: "pm-1"},
			{AgentID: "coder-1", Role: RoleCoder, ParentTaskID: "tl-1"},
		}
		if err := CheckParentChildRelationships(registry); err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
	})

	t.Run("orphan reference", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "coder-1", Role: RoleCoder, ParentTaskID: "nonexistent"},
		}
		err := CheckParentChildRelationships(registry)
		if err == nil {
			t.Fatal("expected error for orphan reference")
		}
		if !containsStr(err.Error(), "parent_exists") {
			t.Errorf("expected parent_exists constraint, got: %v", err)
		}
	})

	t.Run("cycle detection", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "a", Role: RoleTechLead, ParentTaskID: "b"},
			{AgentID: "b", Role: RoleTechLead, ParentTaskID: "a"},
		}
		err := CheckParentChildRelationships(registry)
		if err == nil {
			t.Fatal("expected error for cycle")
		}
		if !containsStr(err.Error(), "no_cycles") {
			t.Errorf("expected no_cycles constraint, got: %v", err)
		}
	})
}

// --- CheckCodersHaveTechLeads tests ---

func TestCheckCodersHaveTechLeads(t *testing.T) {
	t.Run("coder with TechLead parent", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "tl-1", Role: RoleTechLead},
			{AgentID: "coder-1", Role: RoleCoder, ParentTaskID: "tl-1"},
		}
		if err := CheckCodersHaveTechLeads(registry); err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
	})

	t.Run("coder with no parent", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "coder-1", Role: RoleCoder},
		}
		err := CheckCodersHaveTechLeads(registry)
		if err == nil {
			t.Fatal("expected error for coder without parent")
		}
	})

	t.Run("coder with PM parent", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "pm-1", Role: RolePM},
			{AgentID: "coder-1", Role: RoleCoder, ParentTaskID: "pm-1"},
		}
		err := CheckCodersHaveTechLeads(registry)
		if err == nil {
			t.Fatal("expected error for coder with PM parent")
		}
		if !containsStr(err.Error(), "expected TechLead") {
			t.Errorf("expected 'expected TechLead' in error, got: %v", err)
		}
	})
}

// --- CheckTechLeadsHaveCoders tests ---

func TestCheckTechLeadsHaveCoders(t *testing.T) {
	t.Run("TechLead with coder child", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "tl-1", Role: RoleTechLead},
			{AgentID: "coder-1", Role: RoleCoder, ParentTaskID: "tl-1"},
		}
		if err := CheckTechLeadsHaveCoders(registry); err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
	})

	t.Run("TechLead without coders", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "tl-1", Role: RoleTechLead},
		}
		err := CheckTechLeadsHaveCoders(registry)
		if err == nil {
			t.Fatal("expected warning for TechLead without coders")
		}
		if !containsStr(err.Error(), "techLead_has_coders") {
			t.Errorf("expected techLead_has_coders constraint, got: %v", err)
		}
	})

	t.Run("no tech leads returns nil", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "coder-1", Role: RoleCoder},
		}
		if err := CheckTechLeadsHaveCoders(registry); err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
	})
}

// --- CheckDevOpsExists tests ---

func TestCheckDevOpsExists(t *testing.T) {
	t.Run("DevOps present", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "devops-1", Role: RoleDevOps},
		}
		if err := CheckDevOpsExists(registry); err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
	})

	t.Run("no DevOps", func(t *testing.T) {
		registry := []AgentRegistration{
			{AgentID: "pm-1", Role: RolePM},
		}
		err := CheckDevOpsExists(registry)
		if err == nil {
			t.Fatal("expected error for missing DevOps")
		}
		if !containsStr(err.Error(), "devops_required") {
			t.Errorf("expected devops_required constraint, got: %v", err)
		}
	})

	t.Run("empty registry", func(t *testing.T) {
		err := CheckDevOpsExists(nil)
		if err == nil {
			t.Fatal("expected error for empty registry")
		}
	})
}

// --- Rules tests ---

func TestDefaultRules(t *testing.T) {
	rules := DefaultRules()
	if rules.PMEnabled {
		t.Error("default rules should have PM disabled")
	}
	if rules.ParallelCoders != 5 {
		t.Errorf("default parallel coders = %d, want 5", rules.ParallelCoders)
	}
	if !rules.Constraints.EveryCoderMustHaveParent {
		t.Error("default constraint every_coder_must_have_parent should be true")
	}
	if !rules.Constraints.DevOpsRequiredInPMMode {
		t.Error("default constraint devops_required_in_pm_mode should be true")
	}
}

func TestLoadRules(t *testing.T) {
	t.Run("file not found returns defaults", func(t *testing.T) {
		rules, err := LoadRules("/nonexistent/path/rules.json")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if rules.PMEnabled {
			t.Error("expected defaults (PM disabled)")
		}
	})

	t.Run("valid file", func(t *testing.T) {
		dir := t.TempDir()
		path := filepath.Join(dir, "rules.json")

		rules := &TopologyRules{
			PMEnabled:         true,
			ParallelTeamLeads: 3,
			ParallelCoders:    10,
			RequiredPersonas:  []string{"PM", "TechLead", "Coder"},
			Constraints: TopologyConstraints{
				EveryTechLeadMustHaveCoders: true,
				EveryCoderMustHaveParent:    true,
				DevOpsRequiredInPMMode:      false,
			},
		}

		if err := SaveRules(path, rules); err != nil {
			t.Fatalf("failed to save rules: %v", err)
		}

		loaded, err := LoadRules(path)
		if err != nil {
			t.Fatalf("failed to load rules: %v", err)
		}
		if !loaded.PMEnabled {
			t.Error("expected PM enabled")
		}
		if loaded.ParallelTeamLeads != 3 {
			t.Errorf("parallel team leads = %d, want 3", loaded.ParallelTeamLeads)
		}
		if loaded.ParallelCoders != 10 {
			t.Errorf("parallel coders = %d, want 10", loaded.ParallelCoders)
		}
		if loaded.Constraints.DevOpsRequiredInPMMode {
			t.Error("expected DevOpsRequiredInPMMode to be false")
		}
	})

	t.Run("invalid JSON", func(t *testing.T) {
		dir := t.TempDir()
		path := filepath.Join(dir, "bad.json")
		if err := os.WriteFile(path, []byte("not json"), 0644); err != nil {
			t.Fatal(err)
		}

		_, err := LoadRules(path)
		if err == nil {
			t.Fatal("expected error for invalid JSON")
		}
	})
}

// --- Error type tests ---

func TestTopologyViolationError(t *testing.T) {
	err := &TopologyViolation{Constraint: "test", Message: "something broke"}
	want := "topology violation [test]: something broke"
	if err.Error() != want {
		t.Errorf("got %q, want %q", err.Error(), want)
	}
}

func TestInvalidPhaseTransitionError(t *testing.T) {
	err := &InvalidPhaseTransition{
		CurrentPhase: 1,
		TargetPhase:  3,
		Constraint:   "sequential",
		Message:      "cannot skip",
	}
	want := "invalid phase transition 1 -> 3 [sequential]: cannot skip"
	if err.Error() != want {
		t.Errorf("got %q, want %q", err.Error(), want)
	}
}

func TestTopologyWarningError(t *testing.T) {
	err := &TopologyWarning{Constraint: "test", Message: "degraded"}
	want := "topology warning [test]: degraded"
	if err.Error() != want {
		t.Errorf("got %q, want %q", err.Error(), want)
	}
}

// containsStr is a test helper for substring matching.
func containsStr(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
