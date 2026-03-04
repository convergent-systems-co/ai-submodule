package topology

import "fmt"

// TopologyViolation is returned when a topology constraint is violated.
type TopologyViolation struct {
	Constraint string
	Message    string
}

func (e *TopologyViolation) Error() string {
	return fmt.Sprintf("topology violation [%s]: %s", e.Constraint, e.Message)
}

// InvalidPhaseTransition is returned when a phase transition violates constraints.
type InvalidPhaseTransition struct {
	CurrentPhase int
	TargetPhase  int
	Constraint   string
	Message      string
}

func (e *InvalidPhaseTransition) Error() string {
	return fmt.Sprintf("invalid phase transition %d -> %d [%s]: %s",
		e.CurrentPhase, e.TargetPhase, e.Constraint, e.Message)
}

// TopologyWarning represents a non-fatal topology issue.
// It is not an error but indicates a degraded configuration.
type TopologyWarning struct {
	Constraint string
	Message    string
}

func (w *TopologyWarning) Error() string {
	return fmt.Sprintf("topology warning [%s]: %s", w.Constraint, w.Message)
}
