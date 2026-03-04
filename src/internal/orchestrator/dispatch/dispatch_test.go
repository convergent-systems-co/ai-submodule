package dispatch

import "testing"

func TestDispatchCreatesRecord(t *testing.T) {
	tr := NewTracker()
	r := tr.Dispatch("task-1", "coder", "parent-1", "corr-1", map[string]interface{}{"issue": "#42"})

	if r.TaskID != "task-1" {
		t.Fatalf("expected task-1, got %q", r.TaskID)
	}
	if r.Status != StatusPending {
		t.Fatalf("expected pending, got %q", r.Status)
	}
	if r.Persona != "coder" {
		t.Fatalf("expected coder, got %q", r.Persona)
	}
	if r.DispatchedAt == "" {
		t.Fatal("expected non-empty DispatchedAt")
	}
}

func TestComplete(t *testing.T) {
	tr := NewTracker()
	tr.Dispatch("task-1", "coder", "", "", nil)

	err := tr.Complete("task-1", map[string]interface{}{"success": true})
	if err != nil {
		t.Fatalf("complete: %v", err)
	}

	r := tr.GetRecord("task-1")
	if r.Status != StatusCompleted {
		t.Fatalf("expected completed, got %q", r.Status)
	}
	if r.CompletedAt == "" {
		t.Fatal("expected non-empty CompletedAt")
	}
}

func TestFail(t *testing.T) {
	tr := NewTracker()
	tr.Dispatch("task-1", "coder", "", "", nil)

	err := tr.Fail("task-1", map[string]interface{}{"error": "boom"})
	if err != nil {
		t.Fatalf("fail: %v", err)
	}

	r := tr.GetRecord("task-1")
	if r.Status != StatusFailed {
		t.Fatalf("expected failed, got %q", r.Status)
	}
}

func TestCompleteNotFound(t *testing.T) {
	tr := NewTracker()
	err := tr.Complete("nope", nil)
	if err == nil {
		t.Fatal("expected error for unknown task")
	}
}

func TestPendingCount(t *testing.T) {
	tr := NewTracker()
	tr.Dispatch("t1", "coder", "", "", nil)
	tr.Dispatch("t2", "coder", "", "", nil)
	tr.Dispatch("t3", "coder", "", "", nil)
	tr.Complete("t1", nil)

	if tr.PendingCount() != 2 {
		t.Fatalf("expected 2 pending, got %d", tr.PendingCount())
	}
}

func TestAllCompleted(t *testing.T) {
	tr := NewTracker()
	tr.Dispatch("t1", "coder", "", "", nil)
	tr.Dispatch("t2", "coder", "", "", nil)

	if tr.AllCompleted() {
		t.Fatal("expected not all completed")
	}

	tr.Complete("t1", nil)
	tr.Fail("t2", nil)

	if !tr.AllCompleted() {
		t.Fatal("expected all completed")
	}
}

func TestValidateDispatch_Valid(t *testing.T) {
	canSpawn := map[string][]string{
		"tech_lead": {"coder"},
	}
	maxConcurrent := map[string]int{
		"coder": 5,
	}
	activeCount := map[string]int{
		"coder": 2,
	}

	vr := ValidateDispatch("coder", "tech_lead", canSpawn, maxConcurrent, activeCount)
	if !vr.Valid {
		t.Fatalf("expected valid, got errors: %v", vr.Errors)
	}
}

func TestValidateDispatch_InvalidParent(t *testing.T) {
	canSpawn := map[string][]string{
		"tech_lead": {"coder"},
	}

	vr := ValidateDispatch("coder", "unknown_parent", canSpawn, nil, nil)
	if vr.Valid {
		t.Fatal("expected invalid for unknown parent persona")
	}
}

func TestValidateDispatch_NotAllowed(t *testing.T) {
	canSpawn := map[string][]string{
		"tech_lead": {"coder"},
	}

	vr := ValidateDispatch("devops", "tech_lead", canSpawn, nil, nil)
	if vr.Valid {
		t.Fatal("expected invalid when persona not in spawn list")
	}
}

func TestValidateDispatch_AtConcurrencyLimit(t *testing.T) {
	canSpawn := map[string][]string{
		"tech_lead": {"coder"},
	}
	maxConcurrent := map[string]int{
		"coder": 3,
	}
	activeCount := map[string]int{
		"coder": 3,
	}

	vr := ValidateDispatch("coder", "tech_lead", canSpawn, maxConcurrent, activeCount)
	if vr.Valid {
		t.Fatal("expected invalid at concurrency limit")
	}
}

func TestValidateDispatch_NoParent(t *testing.T) {
	// When parentPersona is empty, spawn check is skipped.
	vr := ValidateDispatch("coder", "", nil, nil, nil)
	if !vr.Valid {
		t.Fatalf("expected valid with no parent, got errors: %v", vr.Errors)
	}
}
