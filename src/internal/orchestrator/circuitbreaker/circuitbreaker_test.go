package circuitbreaker

import "testing"

func TestCanDispatch_New(t *testing.T) {
	cb := New(2, 5)
	if !cb.CanDispatch("work-1") {
		t.Fatal("expected new work unit to be dispatchable")
	}
}

func TestRecordFeedback_UnderLimit(t *testing.T) {
	cb := New(3, 10)
	err := cb.RecordFeedback("work-1")
	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if !cb.CanDispatch("work-1") {
		t.Fatal("expected work-1 to still be dispatchable")
	}
}

func TestTripOnFeedbackLimit(t *testing.T) {
	cb := New(2, 10) // trips at feedback >= 2
	cb.RecordFeedback("work-1") // feedback=1, total=1
	err := cb.RecordFeedback("work-1") // feedback=2, total=2 -> trips
	if err == nil {
		t.Fatal("expected error when circuit trips on feedback limit")
	}
	if cb.CanDispatch("work-1") {
		t.Fatal("expected work-1 to be blocked after tripping")
	}
}

func TestTripOnTotalEvalLimit(t *testing.T) {
	cb := New(10, 3) // trips at total >= 3
	cb.RecordFeedback("work-1") // total=1
	cb.RecordFeedback("work-1") // total=2
	err := cb.RecordFeedback("work-1") // total=3 -> trips
	if err == nil {
		t.Fatal("expected error when circuit trips on total eval limit")
	}
	if cb.CanDispatch("work-1") {
		t.Fatal("expected work-1 to be blocked")
	}
}

func TestIndependentWorkUnits(t *testing.T) {
	cb := New(2, 5)
	cb.RecordFeedback("work-1")
	cb.RecordFeedback("work-1") // trips work-1

	// work-2 should still be dispatchable.
	if !cb.CanDispatch("work-2") {
		t.Fatal("expected work-2 to be independent and dispatchable")
	}
}

func TestGetUnit(t *testing.T) {
	cb := New(2, 5)
	cb.RecordFeedback("work-1")
	u := cb.GetUnit("work-1")
	if u == nil {
		t.Fatal("expected non-nil unit")
	}
	if u.FeedbackCycles != 1 {
		t.Fatalf("expected FeedbackCycles=1, got %d", u.FeedbackCycles)
	}
}

func TestGetUnit_NotFound(t *testing.T) {
	cb := New(2, 5)
	if cb.GetUnit("nope") != nil {
		t.Fatal("expected nil for unknown unit")
	}
}

func TestToDict_FromDict_RoundTrip(t *testing.T) {
	cb := New(3, 7)
	cb.RecordFeedback("w1")
	cb.RecordReassign("w1")

	d := cb.ToDict()
	restored := FromDict(d)

	if !restored.CanDispatch("w1") {
		t.Fatal("expected w1 to be dispatchable after restore")
	}
	u := restored.GetUnit("w1")
	if u == nil {
		t.Fatal("expected unit w1 after restore")
	}
	if u.FeedbackCycles != 1 {
		t.Fatalf("expected FeedbackCycles=1, got %d", u.FeedbackCycles)
	}
	if u.Reassignments != 1 {
		t.Fatalf("expected Reassignments=1, got %d", u.Reassignments)
	}
}

func TestRecordReassign(t *testing.T) {
	cb := New(2, 5)
	cb.RecordReassign("work-1")
	u := cb.GetUnit("work-1")
	if u == nil {
		t.Fatal("expected unit to exist")
	}
	if u.Reassignments != 1 {
		t.Fatalf("expected Reassignments=1, got %d", u.Reassignments)
	}
}
