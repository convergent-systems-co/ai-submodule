package tree

import (
	"strings"
	"testing"
)

func TestBuild_SimpleTree(t *testing.T) {
	records := map[string]map[string]interface{}{
		"pm-1": {
			"task_id": "pm-1",
			"persona": "project_manager",
			"status":  "running",
		},
		"coder-1": {
			"task_id":        "coder-1",
			"persona":        "coder",
			"status":         "completed",
			"parent_task_id": "pm-1",
		},
	}

	roots := Build(records, nil)
	if len(roots) != 1 {
		t.Fatalf("expected 1 root, got %d", len(roots))
	}
	if roots[0].TaskID != "pm-1" {
		t.Fatalf("expected root pm-1, got %q", roots[0].TaskID)
	}
	if len(roots[0].Children) != 1 {
		t.Fatalf("expected 1 child, got %d", len(roots[0].Children))
	}
	if roots[0].Children[0].TaskID != "coder-1" {
		t.Fatalf("expected child coder-1, got %q", roots[0].Children[0].TaskID)
	}
}

func TestBuild_MultipleRoots(t *testing.T) {
	records := map[string]map[string]interface{}{
		"tl-1": {
			"task_id": "tl-1",
			"persona": "tech_lead",
			"status":  "running",
		},
		"tl-2": {
			"task_id": "tl-2",
			"persona": "tech_lead",
			"status":  "registered",
		},
	}

	roots := Build(records, nil)
	if len(roots) != 2 {
		t.Fatalf("expected 2 roots, got %d", len(roots))
	}
}

func TestFormat_StatusIcons(t *testing.T) {
	records := map[string]map[string]interface{}{
		"pm": {
			"task_id": "pm",
			"persona": "pm",
			"status":  "running",
		},
		"c1": {
			"task_id":        "c1",
			"persona":        "coder",
			"status":         "completed",
			"parent_task_id": "pm",
		},
		"c2": {
			"task_id":        "c2",
			"persona":        "coder",
			"status":         "failed",
			"parent_task_id": "pm",
		},
	}

	roots := Build(records, nil)
	out := Format(roots)

	// Check status icons are present.
	if !strings.Contains(out, "\u25cf") { // ● running
		t.Fatalf("expected running icon (●) in output: %s", out)
	}
	if !strings.Contains(out, "\u2713") { // ✓ completed
		t.Fatalf("expected completed icon (✓) in output: %s", out)
	}
	if !strings.Contains(out, "\u2717") { // ✗ failed
		t.Fatalf("expected failed icon (✗) in output: %s", out)
	}
}

func TestFormat_Empty(t *testing.T) {
	out := Format(nil)
	if out != "(no agents)" {
		t.Fatalf("expected '(no agents)', got %q", out)
	}
}
