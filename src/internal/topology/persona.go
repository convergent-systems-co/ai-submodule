// Package topology provides compile-time and runtime enforcement of PM mode
// topology rules. It validates persona hierarchies, parent-child relationships,
// action allowlists, and phase transition constraints.
package topology

// PersonaRole represents a governance agent persona.
type PersonaRole int

const (
	// RolePM is the Project Manager persona — top of the hierarchy.
	RolePM PersonaRole = iota
	// RoleTechLead plans, spawns coders, and reviews.
	RoleTechLead
	// RoleCoder implements, tests, and commits.
	RoleCoder
	// RoleDevOps handles PR lifecycle, merges, and rebases.
	RoleDevOps
)

// Action represents an operation a persona can perform.
type Action int

const (
	// ActionSpawn creates child agents.
	ActionSpawn Action = iota
	// ActionWait blocks until child agents complete.
	ActionWait
	// ActionAdvance moves to the next phase.
	ActionAdvance
	// ActionReview evaluates work products.
	ActionReview
	// ActionPlan creates implementation plans.
	ActionPlan
	// ActionImplement writes code.
	ActionImplement
	// ActionTest runs tests.
	ActionTest
	// ActionCommit creates git commits.
	ActionCommit
	// ActionMerge merges branches/PRs.
	ActionMerge
	// ActionRebase rebases branches.
	ActionRebase
	// ActionPush pushes to remote.
	ActionPush
)

// roleNames maps PersonaRole to human-readable names.
var roleNames = map[PersonaRole]string{
	RolePM:       "PM",
	RoleTechLead: "TechLead",
	RoleCoder:    "Coder",
	RoleDevOps:   "DevOps",
}

// actionNames maps Action to human-readable names.
var actionNames = map[Action]string{
	ActionSpawn:     "Spawn",
	ActionWait:      "Wait",
	ActionAdvance:   "Advance",
	ActionReview:    "Review",
	ActionPlan:      "Plan",
	ActionImplement: "Implement",
	ActionTest:      "Test",
	ActionCommit:    "Commit",
	ActionMerge:     "Merge",
	ActionRebase:    "Rebase",
	ActionPush:      "Push",
}

// allowedActions defines the exhaustive action allowlist per role.
var allowedActions = map[PersonaRole][]Action{
	RolePM:       {ActionSpawn, ActionWait, ActionReview, ActionAdvance},
	RoleTechLead: {ActionPlan, ActionSpawn, ActionReview},
	RoleCoder:    {ActionImplement, ActionTest, ActionCommit},
	RoleDevOps:   {ActionMerge, ActionRebase, ActionPush},
}

// String returns the human-readable name for a PersonaRole.
func (r PersonaRole) String() string {
	if name, ok := roleNames[r]; ok {
		return name
	}
	return "Unknown"
}

// String returns the human-readable name for an Action.
func (a Action) String() string {
	if name, ok := actionNames[a]; ok {
		return name
	}
	return "Unknown"
}

// AllowedActions returns the set of actions allowed for a given role.
func AllowedActions(role PersonaRole) []Action {
	if actions, ok := allowedActions[role]; ok {
		result := make([]Action, len(actions))
		copy(result, actions)
		return result
	}
	return nil
}

// CanExecute checks whether a role is allowed to perform an action.
func CanExecute(role PersonaRole, action Action) bool {
	actions, ok := allowedActions[role]
	if !ok {
		return false
	}
	for _, a := range actions {
		if a == action {
			return true
		}
	}
	return false
}

// ParseRole converts a string name to a PersonaRole.
// Returns RolePM and false if the string is not recognized.
func ParseRole(s string) (PersonaRole, bool) {
	for role, name := range roleNames {
		if name == s {
			return role, true
		}
	}
	return RolePM, false
}

// AllRoles returns all defined PersonaRole values.
func AllRoles() []PersonaRole {
	return []PersonaRole{RolePM, RoleTechLead, RoleCoder, RoleDevOps}
}
