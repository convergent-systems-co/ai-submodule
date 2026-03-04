package registry

import "testing"

func TestRegisterAndGetAgent(t *testing.T) {
	reg := New()
	reg.Register("task-1", "coder", "corr-1", "")

	a := reg.GetAgent("task-1")
	if a == nil {
		t.Fatal("expected non-nil agent")
	}
	if a.TaskID != "task-1" {
		t.Fatalf("expected task-1, got %q", a.TaskID)
	}
	if a.Persona != "coder" {
		t.Fatalf("expected coder persona, got %q", a.Persona)
	}
	if a.Status != StatusRegistered {
		t.Fatalf("expected status registered, got %q", a.Status)
	}
}

func TestGetAgent_NotFound(t *testing.T) {
	reg := New()
	if reg.GetAgent("nope") != nil {
		t.Fatal("expected nil for unregistered agent")
	}
}

func TestUpdateStatus(t *testing.T) {
	reg := New()
	reg.Register("task-1", "coder", "corr-1", "")

	err := reg.UpdateStatus("task-1", StatusRunning, nil)
	if err != nil {
		t.Fatalf("update status: %v", err)
	}

	a := reg.GetAgent("task-1")
	if a.Status != StatusRunning {
		t.Fatalf("expected running, got %q", a.Status)
	}
}

func TestUpdateStatus_NotFound(t *testing.T) {
	reg := New()
	err := reg.UpdateStatus("nope", StatusRunning, nil)
	if err == nil {
		t.Fatal("expected error for unknown agent")
	}
}

func TestRecordHeartbeat(t *testing.T) {
	reg := New()
	reg.Register("task-1", "coder", "corr-1", "")

	err := reg.RecordHeartbeat("task-1")
	if err != nil {
		t.Fatalf("heartbeat: %v", err)
	}
}

func TestRecordHeartbeat_NotFound(t *testing.T) {
	reg := New()
	err := reg.RecordHeartbeat("nope")
	if err == nil {
		t.Fatal("expected error for unknown agent")
	}
}

func TestIsAlive_Fresh(t *testing.T) {
	reg := New()
	reg.Register("task-1", "coder", "corr-1", "")

	if !reg.IsAlive("task-1") {
		t.Fatal("freshly registered agent should be alive")
	}
}

func TestIsAlive_NotFound(t *testing.T) {
	reg := New()
	if reg.IsAlive("nope") {
		t.Fatal("non-existent agent should not be alive")
	}
}

func TestListByPersona(t *testing.T) {
	reg := New()
	reg.Register("t1", "coder", "", "")
	reg.Register("t2", "tech_lead", "", "")
	reg.Register("t3", "coder", "", "")

	coders := reg.ListByPersona("coder")
	if len(coders) != 2 {
		t.Fatalf("expected 2 coders, got %d", len(coders))
	}
}

func TestValidateTopology_Valid(t *testing.T) {
	reg := New()
	reg.Register("pm", "project_manager", "", "")
	reg.Register("tl", "tech_lead", "", "pm")

	issues := reg.ValidateTopology()
	if len(issues) != 0 {
		t.Fatalf("expected no issues, got %v", issues)
	}
}

func TestValidateTopology_MissingParent(t *testing.T) {
	reg := New()
	reg.Register("tl", "tech_lead", "", "missing-pm")

	issues := reg.ValidateTopology()
	if len(issues) != 1 {
		t.Fatalf("expected 1 issue, got %d", len(issues))
	}
}

func TestToDict_FromDict_RoundTrip(t *testing.T) {
	reg := New()
	reg.Register("task-1", "coder", "corr-1", "parent-1")
	reg.UpdateStatus("task-1", StatusRunning, map[string]string{"key": "val"})

	d := reg.ToDict()
	restored := FromDict(d)

	a := restored.GetAgent("task-1")
	if a == nil {
		t.Fatal("expected agent after restore")
	}
	if a.Persona != "coder" {
		t.Fatalf("expected coder, got %q", a.Persona)
	}
	if a.Status != StatusRunning {
		t.Fatalf("expected running, got %q", a.Status)
	}
}
