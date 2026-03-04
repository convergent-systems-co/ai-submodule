package deliveryintent

import (
	"crypto/sha256"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// Checker compares a consumer repository's actual state against a delivery intent.
type Checker struct {
	intent  *DeliveryIntent
	rootDir string
}

// NewChecker creates a new Checker for the given intent and repository root.
func NewChecker(intent *DeliveryIntent, rootDir string) *Checker {
	return &Checker{
		intent:  intent,
		rootDir: rootDir,
	}
}

// safePath resolves a relative path within rootDir and ensures it does not
// escape via traversal or absolute components.
func (c *Checker) safePath(relPath string) (string, error) {
	joined := filepath.Join(c.rootDir, relPath)
	cleaned := filepath.Clean(joined)
	if !strings.HasPrefix(cleaned, filepath.Clean(c.rootDir)+string(filepath.Separator)) &&
		cleaned != filepath.Clean(c.rootDir) {
		return "", fmt.Errorf("path %q escapes repository root", relPath)
	}
	return cleaned, nil
}

// CheckAll runs all verification checks and returns an aggregated report.
func (c *Checker) CheckAll() *VerificationReport {
	report := &VerificationReport{
		IntentID: c.intent.IntentID,
	}

	// Check each deliverable. Handle "delete" action first so that a
	// directory deliverable with action "delete" is verified absent rather
	// than verified present.
	for _, d := range c.intent.Deliverables {
		switch {
		case d.Action == "delete":
			c.checkDeleted(d, report)
		case d.Type == "directory":
			c.checkDirectory(d, report)
		default:
			c.checkFile(d, report)
		}
	}

	// Check required directories
	c.checkRequiredDirectories(report)

	// Check required workflows
	c.checkRequiredWorkflows(report)

	// Tally results
	for _, r := range report.Results {
		switch r.Status {
		case StatusPass:
			report.Passed++
		case StatusFail:
			report.Failed++
		case StatusWarning:
			report.Warnings++
		case StatusSkipped:
			report.Skipped++
		}
	}

	report.OverallPass = report.Failed == 0

	return report
}

// checkFile verifies a file deliverable exists and optionally matches its checksum.
func (c *Checker) checkFile(d Deliverable, report *VerificationReport) {
	fullPath, err := c.safePath(d.Path)
	if err != nil {
		report.Results = append(report.Results, CheckResult{
			Name:    fmt.Sprintf("file_exists:%s", d.Path),
			Status:  StatusFail,
			Message: fmt.Sprintf("unsafe path: %v", err),
		})
		return
	}

	info, err := os.Stat(fullPath)
	if os.IsNotExist(err) {
		report.Results = append(report.Results, CheckResult{
			Name:        fmt.Sprintf("file_exists:%s", d.Path),
			Status:      StatusFail,
			Message:     fmt.Sprintf("file not found: %s", d.Path),
			Remediation: fmt.Sprintf("Run 'dark-governance init' or manually restore %s", d.Path),
		})
		return
	}
	if err != nil {
		report.Results = append(report.Results, CheckResult{
			Name:    fmt.Sprintf("file_exists:%s", d.Path),
			Status:  StatusFail,
			Message: fmt.Sprintf("failed to stat %s: %v", d.Path, err),
		})
		return
	}

	if info.IsDir() {
		report.Results = append(report.Results, CheckResult{
			Name:    fmt.Sprintf("file_exists:%s", d.Path),
			Status:  StatusFail,
			Message: fmt.Sprintf("expected file but found directory: %s", d.Path),
		})
		return
	}

	report.Results = append(report.Results, CheckResult{
		Name:    fmt.Sprintf("file_exists:%s", d.Path),
		Status:  StatusPass,
		Message: fmt.Sprintf("file exists: %s", d.Path),
	})

	// Checksum verification
	if d.Checksum != "" {
		c.checkFileChecksum(d, report)
	}
}

// checkFileChecksum compares a file's SHA-256 hash against the expected checksum.
func (c *Checker) checkFileChecksum(d Deliverable, report *VerificationReport) {
	fullPath, err := c.safePath(d.Path)
	if err != nil {
		report.Results = append(report.Results, CheckResult{
			Name:    fmt.Sprintf("checksum:%s", d.Path),
			Status:  StatusFail,
			Message: fmt.Sprintf("unsafe path: %v", err),
		})
		return
	}

	data, err := os.ReadFile(fullPath)
	if err != nil {
		report.Results = append(report.Results, CheckResult{
			Name:    fmt.Sprintf("checksum:%s", d.Path),
			Status:  StatusFail,
			Message: fmt.Sprintf("failed to read %s for checksum: %v", d.Path, err),
		})
		return
	}

	hash := fmt.Sprintf("sha256:%x", sha256.Sum256(data))
	if hash != d.Checksum {
		report.Results = append(report.Results, CheckResult{
			Name:        fmt.Sprintf("checksum:%s", d.Path),
			Status:      StatusFail,
			Message:     fmt.Sprintf("checksum mismatch for %s: expected %s, got %s (local edit)", d.Path, d.Checksum, hash),
			Remediation: fmt.Sprintf("File has been locally modified. Run 'dark-governance verify-environment --fix' to restore or accept the local change."),
		})
		return
	}

	report.Results = append(report.Results, CheckResult{
		Name:    fmt.Sprintf("checksum:%s", d.Path),
		Status:  StatusPass,
		Message: fmt.Sprintf("checksum matches: %s", d.Path),
	})
}

// checkDirectory verifies a directory deliverable exists.
func (c *Checker) checkDirectory(d Deliverable, report *VerificationReport) {
	fullPath, err := c.safePath(d.Path)
	if err != nil {
		report.Results = append(report.Results, CheckResult{
			Name:    fmt.Sprintf("dir_exists:%s", d.Path),
			Status:  StatusFail,
			Message: fmt.Sprintf("unsafe path: %v", err),
		})
		return
	}

	info, err := os.Stat(fullPath)
	if os.IsNotExist(err) {
		report.Results = append(report.Results, CheckResult{
			Name:        fmt.Sprintf("dir_exists:%s", d.Path),
			Status:      StatusFail,
			Message:     fmt.Sprintf("directory not found: %s", d.Path),
			Remediation: fmt.Sprintf("Create directory: mkdir -p %s", d.Path),
		})
		return
	}
	if err != nil {
		report.Results = append(report.Results, CheckResult{
			Name:    fmt.Sprintf("dir_exists:%s", d.Path),
			Status:  StatusFail,
			Message: fmt.Sprintf("failed to stat %s: %v", d.Path, err),
		})
		return
	}

	if !info.IsDir() {
		report.Results = append(report.Results, CheckResult{
			Name:    fmt.Sprintf("dir_exists:%s", d.Path),
			Status:  StatusFail,
			Message: fmt.Sprintf("expected directory but found file: %s", d.Path),
		})
		return
	}

	report.Results = append(report.Results, CheckResult{
		Name:    fmt.Sprintf("dir_exists:%s", d.Path),
		Status:  StatusPass,
		Message: fmt.Sprintf("directory exists: %s", d.Path),
	})
}

// checkDeleted verifies a deleted deliverable no longer exists.
func (c *Checker) checkDeleted(d Deliverable, report *VerificationReport) {
	fullPath, pathErr := c.safePath(d.Path)
	if pathErr != nil {
		report.Results = append(report.Results, CheckResult{
			Name:    fmt.Sprintf("deleted:%s", d.Path),
			Status:  StatusFail,
			Message: fmt.Sprintf("unsafe path: %v", pathErr),
		})
		return
	}

	_, err := os.Stat(fullPath)
	if err == nil {
		// Path still exists but was expected to be deleted.
		report.Results = append(report.Results, CheckResult{
			Name:        fmt.Sprintf("deleted:%s", d.Path),
			Status:      StatusWarning,
			Message:     fmt.Sprintf("file still exists but was expected to be deleted: %s", d.Path),
			Remediation: fmt.Sprintf("Remove file: rm %s", d.Path),
		})
		return
	}
	if os.IsNotExist(err) {
		report.Results = append(report.Results, CheckResult{
			Name:    fmt.Sprintf("deleted:%s", d.Path),
			Status:  StatusPass,
			Message: fmt.Sprintf("file correctly absent: %s", d.Path),
		})
		return
	}

	// An unexpected error occurred while checking the path; treat as failure.
	report.Results = append(report.Results, CheckResult{
		Name:    fmt.Sprintf("deleted:%s", d.Path),
		Status:  StatusFail,
		Message: fmt.Sprintf("failed to stat %s: %v", d.Path, err),
	})
}

// checkRequiredDirectories verifies all expected_state.required_directories exist.
func (c *Checker) checkRequiredDirectories(report *VerificationReport) {
	for _, dir := range c.intent.ExpectedState.RequiredDirectories {
		fullPath, pathErr := c.safePath(dir)
		if pathErr != nil {
			report.Results = append(report.Results, CheckResult{
				Name:    fmt.Sprintf("required_dir:%s", dir),
				Status:  StatusFail,
				Message: fmt.Sprintf("unsafe path: %v", pathErr),
			})
			continue
		}

		info, err := os.Stat(fullPath)
		if os.IsNotExist(err) {
			report.Results = append(report.Results, CheckResult{
				Name:        fmt.Sprintf("required_dir:%s", dir),
				Status:      StatusFail,
				Message:     fmt.Sprintf("required directory missing: %s", dir),
				Remediation: fmt.Sprintf("Create directory: mkdir -p %s", dir),
			})
			continue
		}
		if err != nil {
			report.Results = append(report.Results, CheckResult{
				Name:    fmt.Sprintf("required_dir:%s", dir),
				Status:  StatusFail,
				Message: fmt.Sprintf("failed to stat %s: %v", dir, err),
			})
			continue
		}
		if !info.IsDir() {
			report.Results = append(report.Results, CheckResult{
				Name:    fmt.Sprintf("required_dir:%s", dir),
				Status:  StatusFail,
				Message: fmt.Sprintf("expected directory but found file: %s", dir),
			})
			continue
		}

		report.Results = append(report.Results, CheckResult{
			Name:    fmt.Sprintf("required_dir:%s", dir),
			Status:  StatusPass,
			Message: fmt.Sprintf("required directory exists: %s", dir),
		})
	}
}

// checkRequiredWorkflows verifies all expected_state.required_workflows exist.
func (c *Checker) checkRequiredWorkflows(report *VerificationReport) {
	for _, wf := range c.intent.ExpectedState.RequiredWorkflows {
		wfPath := filepath.Join(".github", "workflows", wf)
		fullPath := filepath.Join(c.rootDir, wfPath)

		if _, err := os.Stat(fullPath); os.IsNotExist(err) {
			report.Results = append(report.Results, CheckResult{
				Name:        fmt.Sprintf("required_workflow:%s", wf),
				Status:      StatusFail,
				Message:     fmt.Sprintf("required workflow missing: %s", wfPath),
				Remediation: fmt.Sprintf("Run 'dark-governance init' to extract the workflow, or manually create %s", wfPath),
			})
			continue
		} else if err != nil {
			report.Results = append(report.Results, CheckResult{
				Name:    fmt.Sprintf("required_workflow:%s", wf),
				Status:  StatusFail,
				Message: fmt.Sprintf("failed to stat %s: %v", wfPath, err),
			})
			continue
		}

		report.Results = append(report.Results, CheckResult{
			Name:    fmt.Sprintf("required_workflow:%s", wf),
			Status:  StatusPass,
			Message: fmt.Sprintf("required workflow exists: %s", wfPath),
		})
	}
}

// ComputeFileChecksum returns the SHA-256 checksum of a file in the format
// "sha256:<hex>".
func ComputeFileChecksum(path string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", fmt.Errorf("failed to read file %s: %w", path, err)
	}
	return fmt.Sprintf("sha256:%x", sha256.Sum256(data)), nil
}
