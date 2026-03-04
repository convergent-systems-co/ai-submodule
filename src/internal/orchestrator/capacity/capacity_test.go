package capacity

import "testing"

func TestClassifyTier_Green(t *testing.T) {
	tier := ClassifyTier(Signals{ToolCalls: 5, Turns: 2, IssuesCompleted: 0})
	if tier != Green {
		t.Fatalf("expected Green, got %s", tier)
	}
}

func TestClassifyTier_Yellow_ToolCalls(t *testing.T) {
	tier := ClassifyTier(Signals{ToolCalls: 100, Turns: 0, IssuesCompleted: 0})
	if tier != Yellow {
		t.Fatalf("expected Yellow, got %s", tier)
	}
}

func TestClassifyTier_Orange_ToolCalls(t *testing.T) {
	tier := ClassifyTier(Signals{ToolCalls: 150, Turns: 0, IssuesCompleted: 0})
	if tier != Orange {
		t.Fatalf("expected Orange, got %s", tier)
	}
}

func TestClassifyTier_Red_ToolCalls(t *testing.T) {
	tier := ClassifyTier(Signals{ToolCalls: 200, Turns: 0, IssuesCompleted: 0})
	if tier != Red {
		t.Fatalf("expected Red, got %s", tier)
	}
}

func TestClassifyTier_Red_SystemWarning(t *testing.T) {
	tier := ClassifyTier(Signals{ToolCalls: 0, SystemWarning: true})
	if tier != Red {
		t.Fatalf("expected Red for SystemWarning, got %s", tier)
	}
}

func TestClassifyTier_Red_DegradedRecall(t *testing.T) {
	tier := ClassifyTier(Signals{ToolCalls: 0, DegradedRecall: true})
	if tier != Red {
		t.Fatalf("expected Red for DegradedRecall, got %s", tier)
	}
}

func TestGateAction_Phase0_Green(t *testing.T) {
	action := GateAction(0, Green)
	if action != Proceed {
		t.Fatalf("phase 0 Green: expected Proceed, got %s", action)
	}
}

func TestGateAction_Phase0_Red(t *testing.T) {
	action := GateAction(0, Red)
	if action != Proceed {
		t.Fatalf("phase 0 Red: expected Proceed, got %s", action)
	}
}

func TestGateAction_Phase1_Orange(t *testing.T) {
	action := GateAction(1, Orange)
	if action != SkipDispatch {
		t.Fatalf("phase 1 Orange: expected SkipDispatch, got %s", action)
	}
}

func TestGateAction_Phase3_Red(t *testing.T) {
	action := GateAction(3, Red)
	if action != EmergencyStop {
		t.Fatalf("phase 3 Red: expected EmergencyStop, got %s", action)
	}
}

func TestGateAction_Phase7_Yellow(t *testing.T) {
	action := GateAction(7, Yellow)
	if action != SkipDispatch {
		t.Fatalf("phase 7 Yellow: expected SkipDispatch, got %s", action)
	}
}

func TestGateAction_InvalidPhase(t *testing.T) {
	action := GateAction(99, Green)
	if action != Checkpoint {
		t.Fatalf("invalid phase: expected Checkpoint, got %s", action)
	}
}

func TestFormatGateBlock(t *testing.T) {
	result := FormatGateBlock(3, Red, EmergencyStop)
	expected := "GATE CHECK — phase=3 tier=red action=emergency_stop"
	if result != expected {
		t.Fatalf("expected %q, got %q", expected, result)
	}
}
