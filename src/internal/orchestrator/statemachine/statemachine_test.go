package statemachine

import (
	"testing"

	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/capacity"
)

func TestValidTransition_1to2(t *testing.T) {
	sm := New(5)
	// Move to phase 1 first (0->1 is valid).
	if _, err := sm.Transition(1); err != nil {
		t.Fatalf("0->1: %v", err)
	}
	// Then 1->2.
	action, err := sm.Transition(2)
	if err != nil {
		t.Fatalf("1->2: %v", err)
	}
	if action != capacity.Proceed {
		t.Fatalf("expected Proceed, got %s", action)
	}
	if sm.Phase() != 2 {
		t.Fatalf("expected phase 2, got %d", sm.Phase())
	}
}

func TestValidTransition_2to3(t *testing.T) {
	sm := New(5)
	sm.Transition(1)
	sm.Transition(2)
	action, err := sm.Transition(3)
	if err != nil {
		t.Fatalf("2->3: %v", err)
	}
	if action != capacity.Proceed {
		t.Fatalf("expected Proceed, got %s", action)
	}
}

func TestInvalidTransition(t *testing.T) {
	sm := New(5)
	sm.Transition(1)
	// 1->5 is not valid.
	_, err := sm.Transition(5)
	if err == nil {
		t.Fatal("expected error for invalid transition 1->5")
	}
	if _, ok := err.(*InvalidTransition); !ok {
		t.Fatalf("expected *InvalidTransition, got %T", err)
	}
}

func TestRecordToolCall(t *testing.T) {
	sm := New(5)
	tier := sm.RecordToolCall()
	if tier != capacity.Green {
		t.Fatalf("expected Green, got %s", tier)
	}
}

func TestRecordTurn(t *testing.T) {
	sm := New(5)
	tier := sm.RecordTurn()
	if tier != capacity.Green {
		t.Fatalf("expected Green, got %s", tier)
	}
}

func TestRecordIssueCompleted(t *testing.T) {
	sm := New(5)
	tier := sm.RecordIssueCompleted()
	if tier != capacity.Green {
		t.Fatalf("expected Green, got %s", tier)
	}
}

func TestGateHistory(t *testing.T) {
	sm := New(5)
	sm.Transition(1)
	history := sm.GateHistory()
	if len(history) != 1 {
		t.Fatalf("expected 1 gate record, got %d", len(history))
	}
	if history[0].Phase != 1 {
		t.Fatalf("expected phase 1 in history, got %d", history[0].Phase)
	}
}

func TestToDict_FromDict_RoundTrip(t *testing.T) {
	sm := New(3)
	sm.Transition(1) // 0->1
	sm.RecordToolCall()
	sm.RecordTurn()

	d := sm.ToDict()
	restored := FromDict(d)

	if restored.Phase() != sm.Phase() {
		t.Fatalf("phase mismatch: %d vs %d", restored.Phase(), sm.Phase())
	}
	if restored.Tier() != sm.Tier() {
		t.Fatalf("tier mismatch: %s vs %s", restored.Tier(), sm.Tier())
	}
	if len(restored.GateHistory()) != len(sm.GateHistory()) {
		t.Fatalf("gate history len mismatch: %d vs %d", len(restored.GateHistory()), len(sm.GateHistory()))
	}
}

func TestFromDict_Float64Values(t *testing.T) {
	// Simulate JSON round-trip where ints become float64.
	d := map[string]interface{}{
		"phase":            float64(2),
		"tool_calls":       float64(10),
		"turns":            float64(3),
		"issues_completed": float64(1),
		"parallel_coders":  float64(5),
		"system_warning":   false,
		"degraded_recall":  false,
		"gate_history":     []interface{}{},
	}
	sm := FromDict(d)
	if sm.Phase() != 2 {
		t.Fatalf("expected phase 2, got %d", sm.Phase())
	}
}

func TestFromDict_IntValues(t *testing.T) {
	d := map[string]interface{}{
		"phase":            3,
		"tool_calls":       15,
		"turns":            5,
		"issues_completed": 2,
		"parallel_coders":  5,
		"system_warning":   false,
		"degraded_recall":  false,
		"gate_history":     []interface{}{},
	}
	sm := FromDict(d)
	if sm.Phase() != 3 {
		t.Fatalf("expected phase 3, got %d", sm.Phase())
	}
}
