package deliveryintent

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// validIntentJSON returns a minimal valid delivery intent JSON string.
func validIntentJSON() string {
	return `{
  "schema_version": "1.0.0",
  "intent_id": "di-2026-03-03-abc123",
  "created_at": "2026-03-03T12:00:00Z",
  "source": {
    "pr": "#750",
    "branch": "itsfwcp/feat/750/new-feature",
    "commit": "abc123def456"
  },
  "deliverables": [
    {
      "type": "workflow",
      "path": ".github/workflows/dark-factory-governance.yml",
      "action": "create",
      "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
  ],
  "expected_state": {
    "governance_version": "1.0.0",
    "policy_profile": "default",
    "required_panels": ["code-review", "security-review"],
    "required_workflows": ["dark-factory-governance.yml"],
    "required_directories": [".artifacts/plans"]
  }
}`
}

func TestLoadFromPath_ValidIntent(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "intent.json")

	if err := os.WriteFile(path, []byte(validIntentJSON()), 0644); err != nil {
		t.Fatalf("failed to write test file: %v", err)
	}

	intent, err := LoadFromPath(path)
	if err != nil {
		t.Fatalf("LoadFromPath failed: %v", err)
	}

	if intent.IntentID != "di-2026-03-03-abc123" {
		t.Errorf("intent_id: got %q, want %q", intent.IntentID, "di-2026-03-03-abc123")
	}
	if intent.SchemaVersion != "1.0.0" {
		t.Errorf("schema_version: got %q, want %q", intent.SchemaVersion, "1.0.0")
	}
	if intent.Source.Branch != "itsfwcp/feat/750/new-feature" {
		t.Errorf("source.branch: got %q, want %q", intent.Source.Branch, "itsfwcp/feat/750/new-feature")
	}
	if len(intent.Deliverables) != 1 {
		t.Errorf("deliverables count: got %d, want 1", len(intent.Deliverables))
	}
	if intent.ExpectedState.PolicyProfile != "default" {
		t.Errorf("policy_profile: got %q, want %q", intent.ExpectedState.PolicyProfile, "default")
	}
}

func TestLoadFromPath_MissingFile(t *testing.T) {
	_, err := LoadFromPath("/nonexistent/path/intent.json")
	if err == nil {
		t.Fatal("expected error for missing file")
	}
	if !strings.Contains(err.Error(), "not found") {
		t.Errorf("expected 'not found' in error, got: %v", err)
	}
}

func TestLoadFromPath_InvalidJSON(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "intent.json")

	if err := os.WriteFile(path, []byte("not json"), 0644); err != nil {
		t.Fatalf("failed to write test file: %v", err)
	}

	_, err := LoadFromPath(path)
	if err == nil {
		t.Fatal("expected error for invalid JSON")
	}
	if !strings.Contains(err.Error(), "invalid JSON") {
		t.Errorf("expected 'invalid JSON' in error, got: %v", err)
	}
}

func TestLoadFromPath_ValidationFailure(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "intent.json")

	// Missing required fields
	data := `{"schema_version": "1.0.0", "intent_id": "bad-id"}`
	if err := os.WriteFile(path, []byte(data), 0644); err != nil {
		t.Fatalf("failed to write test file: %v", err)
	}

	_, err := LoadFromPath(path)
	if err == nil {
		t.Fatal("expected validation error")
	}
	if !strings.Contains(err.Error(), "validation failed") {
		t.Errorf("expected 'validation failed' in error, got: %v", err)
	}
}

func TestLoadLatest(t *testing.T) {
	dir := t.TempDir()
	intentDir := filepath.Join(dir, DefaultIntentDir)
	if err := os.MkdirAll(intentDir, 0755); err != nil {
		t.Fatalf("failed to create intent dir: %v", err)
	}

	latestPath := filepath.Join(dir, DefaultLatestPath)
	if err := os.WriteFile(latestPath, []byte(validIntentJSON()), 0644); err != nil {
		t.Fatalf("failed to write latest intent: %v", err)
	}

	intent, err := LoadLatest(dir)
	if err != nil {
		t.Fatalf("LoadLatest failed: %v", err)
	}
	if intent.IntentID != "di-2026-03-03-abc123" {
		t.Errorf("intent_id: got %q, want %q", intent.IntentID, "di-2026-03-03-abc123")
	}
}

func TestLoadByID(t *testing.T) {
	dir := t.TempDir()
	intentDir := filepath.Join(dir, DefaultIntentDir)
	if err := os.MkdirAll(intentDir, 0755); err != nil {
		t.Fatalf("failed to create intent dir: %v", err)
	}

	intentPath := filepath.Join(intentDir, "di-2026-03-03-abc123.json")
	if err := os.WriteFile(intentPath, []byte(validIntentJSON()), 0644); err != nil {
		t.Fatalf("failed to write intent: %v", err)
	}

	intent, err := LoadByID(dir, "di-2026-03-03-abc123")
	if err != nil {
		t.Fatalf("LoadByID failed: %v", err)
	}
	if intent.IntentID != "di-2026-03-03-abc123" {
		t.Errorf("intent_id: got %q, want %q", intent.IntentID, "di-2026-03-03-abc123")
	}
}

func TestValidate_MissingSchemaVersion(t *testing.T) {
	intent := &DeliveryIntent{}
	err := Validate(intent)
	if err == nil {
		t.Fatal("expected validation error")
	}
	if !strings.Contains(err.Error(), "schema_version") {
		t.Errorf("expected 'schema_version' in error, got: %v", err)
	}
}

func TestValidate_UnsupportedSchemaVersion(t *testing.T) {
	intent := &DeliveryIntent{SchemaVersion: "99.0.0"}
	err := Validate(intent)
	if err == nil {
		t.Fatal("expected validation error")
	}
	if !strings.Contains(err.Error(), "unsupported schema_version") {
		t.Errorf("expected 'unsupported schema_version' in error, got: %v", err)
	}
}

func TestValidate_InvalidIntentID(t *testing.T) {
	intent := &DeliveryIntent{
		SchemaVersion: "1.0.0",
		IntentID:      "bad-format",
	}
	err := Validate(intent)
	if err == nil {
		t.Fatal("expected validation error")
	}
	if !strings.Contains(err.Error(), "invalid intent_id") {
		t.Errorf("expected 'invalid intent_id' in error, got: %v", err)
	}
}

func TestValidate_EmptyDeliverables(t *testing.T) {
	intent := &DeliveryIntent{
		SchemaVersion: "1.0.0",
		IntentID:      "di-2026-03-03-abc123",
		CreatedAt:     "2026-03-03T12:00:00Z",
		Source:        Source{Branch: "main", Commit: "abc123"},
		Deliverables:  []Deliverable{},
		ExpectedState: ExpectedState{GovernanceVersion: "1.0.0", PolicyProfile: "default"},
	}
	err := Validate(intent)
	if err == nil {
		t.Fatal("expected validation error for empty deliverables")
	}
	if !strings.Contains(err.Error(), "at least one") {
		t.Errorf("expected 'at least one' in error, got: %v", err)
	}
}

func TestValidate_MissingDeliverableFields(t *testing.T) {
	intent := &DeliveryIntent{
		SchemaVersion: "1.0.0",
		IntentID:      "di-2026-03-03-abc123",
		CreatedAt:     "2026-03-03T12:00:00Z",
		Source:        Source{Branch: "main", Commit: "abc123"},
		Deliverables:  []Deliverable{{Type: "workflow"}},
		ExpectedState: ExpectedState{GovernanceVersion: "1.0.0", PolicyProfile: "default"},
	}
	err := Validate(intent)
	if err == nil {
		t.Fatal("expected validation error for incomplete deliverable")
	}
	if !strings.Contains(err.Error(), "deliverable[0]") {
		t.Errorf("expected 'deliverable[0]' in error, got: %v", err)
	}
}

func TestValidate_ValidIntent(t *testing.T) {
	intent := &DeliveryIntent{
		SchemaVersion: "1.0.0",
		IntentID:      "di-2026-03-03-abc123",
		CreatedAt:     "2026-03-03T12:00:00Z",
		Source:        Source{Branch: "main", Commit: "abc123"},
		Deliverables: []Deliverable{
			{Type: "workflow", Path: ".github/workflows/test.yml", Action: "create"},
		},
		ExpectedState: ExpectedState{GovernanceVersion: "1.0.0", PolicyProfile: "default"},
	}
	if err := Validate(intent); err != nil {
		t.Errorf("expected valid intent, got error: %v", err)
	}
}

func TestLoadFromPath_MissingFileWrapsNotExist(t *testing.T) {
	_, err := LoadFromPath("/nonexistent/path/intent.json")
	if err == nil {
		t.Fatal("expected error for missing file")
	}
	// Verify the error wraps os.ErrNotExist for structural detection.
	if !errors.Is(err, os.ErrNotExist) {
		t.Errorf("expected wrapped os.ErrNotExist, got: %v", err)
	}
}

func TestValidate_InvalidCreatedAtFormat(t *testing.T) {
	intent := &DeliveryIntent{
		SchemaVersion: "1.0.0",
		IntentID:      "di-2026-03-03-abc123",
		CreatedAt:     "not-a-date",
		Source:        Source{Branch: "main", Commit: "abc123"},
		Deliverables: []Deliverable{
			{Type: "workflow", Path: "test.yml", Action: "create"},
		},
		ExpectedState: ExpectedState{GovernanceVersion: "1.0.0", PolicyProfile: "default"},
	}
	err := Validate(intent)
	if err == nil {
		t.Fatal("expected validation error for invalid created_at")
	}
	if !strings.Contains(err.Error(), "RFC3339") {
		t.Errorf("expected 'RFC3339' in error, got: %v", err)
	}
}

func TestValidate_InvalidDeliverableAction(t *testing.T) {
	intent := &DeliveryIntent{
		SchemaVersion: "1.0.0",
		IntentID:      "di-2026-03-03-abc123",
		CreatedAt:     "2026-03-03T12:00:00Z",
		Source:        Source{Branch: "main", Commit: "abc123"},
		Deliverables: []Deliverable{
			{Type: "workflow", Path: "test.yml", Action: "invalid_action"},
		},
		ExpectedState: ExpectedState{GovernanceVersion: "1.0.0", PolicyProfile: "default"},
	}
	err := Validate(intent)
	if err == nil {
		t.Fatal("expected validation error for invalid action")
	}
	if !strings.Contains(err.Error(), "invalid action") {
		t.Errorf("expected 'invalid action' in error, got: %v", err)
	}
}

func TestValidate_InvalidDeliverableType(t *testing.T) {
	intent := &DeliveryIntent{
		SchemaVersion: "1.0.0",
		IntentID:      "di-2026-03-03-abc123",
		CreatedAt:     "2026-03-03T12:00:00Z",
		Source:        Source{Branch: "main", Commit: "abc123"},
		Deliverables: []Deliverable{
			{Type: "unknown_type", Path: "test.yml", Action: "create"},
		},
		ExpectedState: ExpectedState{GovernanceVersion: "1.0.0", PolicyProfile: "default"},
	}
	err := Validate(intent)
	if err == nil {
		t.Fatal("expected validation error for invalid type")
	}
	if !strings.Contains(err.Error(), "invalid type") {
		t.Errorf("expected 'invalid type' in error, got: %v", err)
	}
}

func TestValidate_PathTraversal(t *testing.T) {
	intent := &DeliveryIntent{
		SchemaVersion: "1.0.0",
		IntentID:      "di-2026-03-03-abc123",
		CreatedAt:     "2026-03-03T12:00:00Z",
		Source:        Source{Branch: "main", Commit: "abc123"},
		Deliverables: []Deliverable{
			{Type: "config", Path: "../../etc/passwd", Action: "create"},
		},
		ExpectedState: ExpectedState{GovernanceVersion: "1.0.0", PolicyProfile: "default"},
	}
	err := Validate(intent)
	if err == nil {
		t.Fatal("expected validation error for path traversal")
	}
	if !strings.Contains(err.Error(), "must not contain") {
		t.Errorf("expected path traversal error, got: %v", err)
	}
}

func TestValidate_AbsolutePath(t *testing.T) {
	intent := &DeliveryIntent{
		SchemaVersion: "1.0.0",
		IntentID:      "di-2026-03-03-abc123",
		CreatedAt:     "2026-03-03T12:00:00Z",
		Source:        Source{Branch: "main", Commit: "abc123"},
		Deliverables: []Deliverable{
			{Type: "config", Path: "/etc/passwd", Action: "create"},
		},
		ExpectedState: ExpectedState{GovernanceVersion: "1.0.0", PolicyProfile: "default"},
	}
	err := Validate(intent)
	if err == nil {
		t.Fatal("expected validation error for absolute path")
	}
	if !strings.Contains(err.Error(), "must be relative") {
		t.Errorf("expected relative path error, got: %v", err)
	}
}

func TestValidate_InvalidChecksumFormat(t *testing.T) {
	intent := &DeliveryIntent{
		SchemaVersion: "1.0.0",
		IntentID:      "di-2026-03-03-abc123",
		CreatedAt:     "2026-03-03T12:00:00Z",
		Source:        Source{Branch: "main", Commit: "abc123"},
		Deliverables: []Deliverable{
			{Type: "workflow", Path: "test.yml", Action: "create", Checksum: "md5:abc"},
		},
		ExpectedState: ExpectedState{GovernanceVersion: "1.0.0", PolicyProfile: "default"},
	}
	err := Validate(intent)
	if err == nil {
		t.Fatal("expected validation error for invalid checksum format")
	}
	if !strings.Contains(err.Error(), "invalid checksum format") {
		t.Errorf("expected 'invalid checksum format' in error, got: %v", err)
	}
}
