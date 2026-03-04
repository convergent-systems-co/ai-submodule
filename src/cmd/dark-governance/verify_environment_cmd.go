package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/SET-Apps/ai-submodule/src/internal/deliveryintent"
	"github.com/SET-Apps/ai-submodule/src/internal/exitcode"
	"github.com/SET-Apps/ai-submodule/src/internal/topology"
	"github.com/spf13/cobra"
)

// ExitError is a type alias to the shared exitcode.ExitError.
type ExitError = exitcode.ExitError

var (
	verifyEnvIntentPath    string
	verifyEnvOutput        string
	verifyEnvFix           bool
	verifyEnvCheckTopology bool
)

var verifyEnvironmentCmd = &cobra.Command{
	Use:   "verify-environment",
	Short: "Verify repository state against a delivery intent",
	Long: `Compare the current repository state against a delivery intent manifest.

A delivery intent declares what files should exist, their expected checksums,
required directories, and required workflows. This command checks the actual
repository state and reports any drift.

Exit codes:
  0  Environment matches delivery intent
  1  Drift detected (fixable with --fix)
  2  Critical error (invalid intent, read failure, or topology violation with --check-topology)
  3  No delivery intent found

Examples:
  dark-governance verify-environment
  dark-governance verify-environment --intent .artifacts/delivery-intents/di-2026-03-03-abc123.json
  dark-governance verify-environment --output json
  dark-governance verify-environment --fix
  dark-governance verify-environment --check-topology`,
	RunE: runVerifyEnvironment,
}

func init() {
	verifyEnvironmentCmd.Flags().StringVar(&verifyEnvIntentPath, "intent", "",
		"Path to a specific delivery intent manifest (default: .artifacts/delivery-intents/latest.json)")
	verifyEnvironmentCmd.Flags().StringVar(&verifyEnvOutput, "output", "human",
		"Output format: human or json")
	verifyEnvironmentCmd.Flags().BoolVar(&verifyEnvFix, "fix", false,
		"Attempt auto-remediation of drift (creates missing directories)")
	verifyEnvironmentCmd.Flags().BoolVar(&verifyEnvCheckTopology, "check-topology", false,
		"Also validate topology constraints against session state")
}

func runVerifyEnvironment(cmd *cobra.Command, args []string) error {
	// Validate --output flag early so invalid values fail fast.
	switch verifyEnvOutput {
	case "human", "json":
		// ok
	default:
		return fmt.Errorf("invalid --output value %q; supported values are \"human\" or \"json\"", verifyEnvOutput)
	}

	cwd, err := os.Getwd()
	if err != nil {
		return fmt.Errorf("failed to get working directory: %w", err)
	}

	// Determine intent path
	intentPath := verifyEnvIntentPath
	if intentPath == "" {
		intentPath = deliveryintent.DefaultLatestPath
	}

	// Load intent
	var intent *deliveryintent.DeliveryIntent
	var loadErr error

	if verifyEnvIntentPath != "" {
		// Explicit path provided
		intent, loadErr = deliveryintent.LoadFromPath(intentPath)
	} else {
		// Use default latest
		intent, loadErr = deliveryintent.LoadLatest(cwd)
	}

	if loadErr != nil {
		if errors.Is(loadErr, os.ErrNotExist) {
			if verifyEnvOutput == "json" {
				fmt.Fprintf(os.Stdout, `{"status":"no_intent","message":"No delivery intent found","path":%q}`+"\n", intentPath)
			} else {
				fmt.Fprintln(os.Stderr, "No delivery intent found.")
				fmt.Fprintf(os.Stderr, "  Looked for: %s\n", intentPath)
				fmt.Fprintln(os.Stderr, "  Run 'dark-governance init' to initialize governance.")
			}
			cmd.SilenceErrors = true
			return &ExitError{Code: 3, Message: "no delivery intent found"}
		}

		if verifyEnvOutput == "json" {
			fmt.Fprintf(os.Stdout, `{"status":"error","message":%q}`+"\n", loadErr.Error())
		} else {
			fmt.Fprintf(os.Stderr, "Error loading delivery intent: %v\n", loadErr)
		}
		cmd.SilenceErrors = true
		return &ExitError{Code: 2, Message: loadErr.Error()}
	}

	// Run verification
	checker := deliveryintent.NewChecker(intent, cwd)
	report := checker.CheckAll()

	// Apply fixes if requested
	if verifyEnvFix && !report.OverallPass {
		applyFixes(intent, cwd, report)
	}

	// Run topology check if requested
	if verifyEnvCheckTopology {
		rulesPath := filepath.Join(cwd, ".artifacts", "state", "topology-rules.json")
		rules, rulesErr := topology.LoadRules(rulesPath)
		if rulesErr != nil {
			if verifyEnvOutput == "json" {
				fmt.Fprintf(os.Stdout, `{"status":"error","message":"failed to load topology rules: %s"}`+"\n", rulesErr.Error())
			} else {
				fmt.Fprintf(os.Stderr, "Warning: failed to load topology rules: %v (using defaults)\n", rulesErr)
			}
			rules = topology.DefaultRules()
		}

		sessionPath := filepath.Join(cwd, ".artifacts", "state", "sessions", "latest.json")
		registry, pmEnabled, sessionErr := loadTopologyRegistry(sessionPath, rules)
		if sessionErr != nil {
			// No session state — skip topology check with a warning
			report.Results = append(report.Results, deliveryintent.CheckResult{
				Name:    "topology_check",
				Status:  deliveryintent.StatusWarning,
				Message: "No session state found; topology check skipped",
			})
			report.Warnings++
		} else {
			topoResult := topology.ValidateTopology(registry, pmEnabled)
			if !topoResult.Valid {
				for _, v := range topoResult.Violations {
					report.Results = append(report.Results, deliveryintent.CheckResult{
						Name:    "topology_violation",
						Status:  deliveryintent.StatusFail,
						Message: v,
					})
					report.Failed++
				}
				report.OverallPass = false
			} else {
				report.Results = append(report.Results, deliveryintent.CheckResult{
					Name:    "topology_check",
					Status:  deliveryintent.StatusPass,
					Message: "Topology validation passed",
				})
				report.Passed++
			}
			for _, w := range topoResult.Warnings {
				report.Results = append(report.Results, deliveryintent.CheckResult{
					Name:    "topology_warning",
					Status:  deliveryintent.StatusWarning,
					Message: w,
				})
				report.Warnings++
			}
		}
	}

	// Output results
	if verifyEnvOutput == "json" {
		return outputVerifyJSON(report)
	}
	return outputVerifyHuman(report)
}

// outputVerifyJSON writes the verification report as JSON.
func outputVerifyJSON(report *deliveryintent.VerificationReport) error {
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal report: %w", err)
	}
	fmt.Fprintln(os.Stdout, string(data))

	if !report.OverallPass {
		return &ExitError{Code: 1, Message: "drift detected"}
	}
	return nil
}

// outputVerifyHuman writes the verification report in human-readable format.
func outputVerifyHuman(report *deliveryintent.VerificationReport) error {
	fmt.Fprintln(os.Stdout, "Environment Verification Report")
	fmt.Fprintln(os.Stdout, "================================")
	fmt.Fprintf(os.Stdout, "Intent: %s\n", report.IntentID)
	fmt.Fprintln(os.Stdout, "")

	// Print results grouped by status
	for _, r := range report.Results {
		var indicator string
		switch r.Status {
		case deliveryintent.StatusPass:
			indicator = "PASS"
		case deliveryintent.StatusFail:
			indicator = "FAIL"
		case deliveryintent.StatusWarning:
			indicator = "WARN"
		case deliveryintent.StatusSkipped:
			indicator = "SKIP"
		}
		fmt.Fprintf(os.Stdout, "  [%s] %s\n", indicator, r.Message)
		if r.Remediation != "" && r.Status != deliveryintent.StatusPass {
			fmt.Fprintf(os.Stdout, "         -> %s\n", r.Remediation)
		}
	}

	fmt.Fprintln(os.Stdout, "")
	fmt.Fprintf(os.Stdout, "Summary: %d passed, %d failed, %d warnings, %d skipped\n",
		report.Passed, report.Failed, report.Warnings, report.Skipped)

	issueCount := report.Failed + report.Warnings
	if report.OverallPass && report.Warnings == 0 {
		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintln(os.Stdout, "Overall: OK")
	} else if report.OverallPass && report.Warnings > 0 {
		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintf(os.Stdout, "Overall: OK with warnings (%d warnings)\n", report.Warnings)
	} else {
		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintf(os.Stdout, "Overall: DRIFT DETECTED (%d issues)\n", issueCount)
		fmt.Fprintln(os.Stdout, "Run 'dark-governance verify-environment --fix' to remediate.")
		return &ExitError{Code: 1, Message: "drift detected"}
	}

	return nil
}

// applyFixes attempts safe auto-remediation: creating missing directories.
func applyFixes(_ *deliveryintent.DeliveryIntent, rootDir string, report *deliveryintent.VerificationReport) {
	cleanRoot := filepath.Clean(rootDir)

	for i, r := range report.Results {
		if r.Status != deliveryintent.StatusFail {
			continue
		}

		var dirPath string
		// Only auto-fix missing directories (safe operation)
		if len(r.Name) > 13 && r.Name[:13] == "required_dir:" {
			dirPath = r.Name[13:]
		} else if len(r.Name) > 11 && r.Name[:11] == "dir_exists:" {
			dirPath = r.Name[11:]
		} else {
			continue
		}

		// Build a safe path and ensure it remains within rootDir.
		fullPath := filepath.Clean(filepath.Join(cleanRoot, dirPath))
		if !strings.HasPrefix(fullPath, cleanRoot+string(filepath.Separator)) && fullPath != cleanRoot {
			continue // path would escape rootDir; skip silently
		}

		if err := os.MkdirAll(fullPath, 0755); err == nil {
			report.Results[i] = deliveryintent.CheckResult{
				Name:    r.Name,
				Status:  deliveryintent.StatusPass,
				Message: fmt.Sprintf("fixed: created directory %s", dirPath),
			}
			report.Failed--
			report.Passed++
		}
	}

	report.OverallPass = report.Failed == 0
}
