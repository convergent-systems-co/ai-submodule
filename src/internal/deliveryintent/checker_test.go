package deliveryintent

import (
	"crypto/sha256"
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

func makeTestIntent() *DeliveryIntent {
	return &DeliveryIntent{
		SchemaVersion: "1.0.0",
		IntentID:      "di-2026-03-03-abc123",
		CreatedAt:     "2026-03-03T12:00:00Z",
		Source:        Source{Branch: "main", Commit: "abc123"},
		Deliverables:  []Deliverable{},
		ExpectedState: ExpectedState{
			GovernanceVersion: "1.0.0",
			PolicyProfile:     "default",
		},
	}
}

func TestChecker_FileExists(t *testing.T) {
	dir := t.TempDir()

	// Create a test file
	testFile := filepath.Join(dir, "test.yml")
	if err := os.WriteFile(testFile, []byte("content"), 0644); err != nil {
		t.Fatalf("failed to create test file: %v", err)
	}

	intent := makeTestIntent()
	intent.Deliverables = []Deliverable{
		{Type: "workflow", Path: "test.yml", Action: "create"},
	}

	checker := NewChecker(intent, dir)
	report := checker.CheckAll()

	if report.Failed != 0 {
		t.Errorf("expected 0 failures, got %d", report.Failed)
		for _, r := range report.Results {
			if r.Status == StatusFail {
				t.Logf("  FAIL: %s - %s", r.Name, r.Message)
			}
		}
	}
}

func TestChecker_FileMissing(t *testing.T) {
	dir := t.TempDir()

	intent := makeTestIntent()
	intent.Deliverables = []Deliverable{
		{Type: "workflow", Path: "missing.yml", Action: "create"},
	}

	checker := NewChecker(intent, dir)
	report := checker.CheckAll()

	if report.Failed != 1 {
		t.Errorf("expected 1 failure, got %d", report.Failed)
	}
	if report.OverallPass {
		t.Error("expected overall_pass to be false")
	}
}

func TestChecker_ChecksumMatch(t *testing.T) {
	dir := t.TempDir()

	content := []byte("governance workflow content")
	testFile := filepath.Join(dir, "test.yml")
	if err := os.WriteFile(testFile, content, 0644); err != nil {
		t.Fatalf("failed to create test file: %v", err)
	}

	hash := fmt.Sprintf("sha256:%x", sha256.Sum256(content))

	intent := makeTestIntent()
	intent.Deliverables = []Deliverable{
		{Type: "workflow", Path: "test.yml", Action: "create", Checksum: hash},
	}

	checker := NewChecker(intent, dir)
	report := checker.CheckAll()

	if report.Failed != 0 {
		t.Errorf("expected 0 failures, got %d", report.Failed)
		for _, r := range report.Results {
			if r.Status == StatusFail {
				t.Logf("  FAIL: %s - %s", r.Name, r.Message)
			}
		}
	}
}

func TestChecker_ChecksumMismatch(t *testing.T) {
	dir := t.TempDir()

	testFile := filepath.Join(dir, "test.yml")
	if err := os.WriteFile(testFile, []byte("local edit"), 0644); err != nil {
		t.Fatalf("failed to create test file: %v", err)
	}

	intent := makeTestIntent()
	intent.Deliverables = []Deliverable{
		{
			Type:     "workflow",
			Path:     "test.yml",
			Action:   "create",
			Checksum: "sha256:0000000000000000000000000000000000000000000000000000000000000000",
		},
	}

	checker := NewChecker(intent, dir)
	report := checker.CheckAll()

	// Should have: file_exists pass + checksum fail
	var checksumFail bool
	for _, r := range report.Results {
		if r.Name == "checksum:test.yml" && r.Status == StatusFail {
			checksumFail = true
		}
	}
	if !checksumFail {
		t.Error("expected checksum failure for modified file")
	}
}

func TestChecker_DirectoryExists(t *testing.T) {
	dir := t.TempDir()

	// Create the directory
	if err := os.MkdirAll(filepath.Join(dir, "artifacts", "plans"), 0755); err != nil {
		t.Fatalf("failed to create test dir: %v", err)
	}

	intent := makeTestIntent()
	intent.Deliverables = []Deliverable{
		{Type: "directory", Path: "artifacts/plans", Action: "create"},
	}

	checker := NewChecker(intent, dir)
	report := checker.CheckAll()

	if report.Failed != 0 {
		t.Errorf("expected 0 failures, got %d", report.Failed)
	}
}

func TestChecker_DirectoryMissing(t *testing.T) {
	dir := t.TempDir()

	intent := makeTestIntent()
	intent.Deliverables = []Deliverable{
		{Type: "directory", Path: "missing/dir", Action: "create"},
	}

	checker := NewChecker(intent, dir)
	report := checker.CheckAll()

	if report.Failed != 1 {
		t.Errorf("expected 1 failure, got %d", report.Failed)
	}
}

func TestChecker_DeletedFileStillExists(t *testing.T) {
	dir := t.TempDir()

	// Create a file that should have been deleted
	testFile := filepath.Join(dir, "old.yml")
	if err := os.WriteFile(testFile, []byte("old content"), 0644); err != nil {
		t.Fatalf("failed to create test file: %v", err)
	}

	intent := makeTestIntent()
	intent.Deliverables = []Deliverable{
		{Type: "config", Path: "old.yml", Action: "delete"},
	}

	checker := NewChecker(intent, dir)
	report := checker.CheckAll()

	// Should be a warning, not a failure
	if report.Warnings != 1 {
		t.Errorf("expected 1 warning, got %d", report.Warnings)
	}
	if report.Failed != 0 {
		t.Errorf("expected 0 failures, got %d", report.Failed)
	}
}

func TestChecker_DeletedFileGone(t *testing.T) {
	dir := t.TempDir()

	intent := makeTestIntent()
	intent.Deliverables = []Deliverable{
		{Type: "config", Path: "old.yml", Action: "delete"},
	}

	checker := NewChecker(intent, dir)
	report := checker.CheckAll()

	if report.Passed != 1 {
		t.Errorf("expected 1 pass, got %d", report.Passed)
	}
}

func TestChecker_RequiredDirectories(t *testing.T) {
	dir := t.TempDir()

	// Create some but not all required directories
	if err := os.MkdirAll(filepath.Join(dir, ".artifacts", "plans"), 0755); err != nil {
		t.Fatalf("failed to create dir: %v", err)
	}

	intent := makeTestIntent()
	intent.Deliverables = []Deliverable{
		{Type: "config", Path: "dummy.txt", Action: "create"},
	}

	// Create the dummy file
	if err := os.WriteFile(filepath.Join(dir, "dummy.txt"), []byte("x"), 0644); err != nil {
		t.Fatalf("failed to create dummy: %v", err)
	}

	intent.ExpectedState.RequiredDirectories = []string{
		".artifacts/plans",
		".artifacts/missing",
	}

	checker := NewChecker(intent, dir)
	report := checker.CheckAll()

	var foundPass, foundFail bool
	for _, r := range report.Results {
		if r.Name == "required_dir:.artifacts/plans" && r.Status == StatusPass {
			foundPass = true
		}
		if r.Name == "required_dir:.artifacts/missing" && r.Status == StatusFail {
			foundFail = true
		}
	}

	if !foundPass {
		t.Error("expected pass for existing required directory")
	}
	if !foundFail {
		t.Error("expected fail for missing required directory")
	}
}

func TestChecker_RequiredWorkflows(t *testing.T) {
	dir := t.TempDir()

	// Create workflow directory with one workflow
	wfDir := filepath.Join(dir, ".github", "workflows")
	if err := os.MkdirAll(wfDir, 0755); err != nil {
		t.Fatalf("failed to create workflow dir: %v", err)
	}
	if err := os.WriteFile(filepath.Join(wfDir, "governance.yml"), []byte("name: test"), 0644); err != nil {
		t.Fatalf("failed to create workflow: %v", err)
	}

	intent := makeTestIntent()
	intent.Deliverables = []Deliverable{
		{Type: "config", Path: "dummy.txt", Action: "create"},
	}
	if err := os.WriteFile(filepath.Join(dir, "dummy.txt"), []byte("x"), 0644); err != nil {
		t.Fatalf("failed to create dummy: %v", err)
	}

	intent.ExpectedState.RequiredWorkflows = []string{
		"governance.yml",
		"missing-workflow.yml",
	}

	checker := NewChecker(intent, dir)
	report := checker.CheckAll()

	var foundPass, foundFail bool
	for _, r := range report.Results {
		if r.Name == "required_workflow:governance.yml" && r.Status == StatusPass {
			foundPass = true
		}
		if r.Name == "required_workflow:missing-workflow.yml" && r.Status == StatusFail {
			foundFail = true
		}
	}

	if !foundPass {
		t.Error("expected pass for existing workflow")
	}
	if !foundFail {
		t.Error("expected fail for missing workflow")
	}
}

func TestChecker_OverallPass(t *testing.T) {
	dir := t.TempDir()

	testFile := filepath.Join(dir, "test.yml")
	if err := os.WriteFile(testFile, []byte("content"), 0644); err != nil {
		t.Fatalf("failed to create test file: %v", err)
	}

	intent := makeTestIntent()
	intent.Deliverables = []Deliverable{
		{Type: "workflow", Path: "test.yml", Action: "create"},
	}

	checker := NewChecker(intent, dir)
	report := checker.CheckAll()

	if !report.OverallPass {
		t.Error("expected overall_pass to be true when all checks pass")
	}
}

func TestComputeFileChecksum(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test.txt")

	content := []byte("hello world")
	if err := os.WriteFile(path, content, 0644); err != nil {
		t.Fatalf("failed to create test file: %v", err)
	}

	expected := fmt.Sprintf("sha256:%x", sha256.Sum256(content))

	got, err := ComputeFileChecksum(path)
	if err != nil {
		t.Fatalf("ComputeFileChecksum failed: %v", err)
	}

	if got != expected {
		t.Errorf("checksum: got %q, want %q", got, expected)
	}
}

func TestComputeFileChecksum_MissingFile(t *testing.T) {
	_, err := ComputeFileChecksum("/nonexistent/file.txt")
	if err == nil {
		t.Fatal("expected error for missing file")
	}
}
