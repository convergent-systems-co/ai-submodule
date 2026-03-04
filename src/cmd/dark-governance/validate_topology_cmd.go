package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/SET-Apps/ai-submodule/src/internal/topology"
	"github.com/spf13/cobra"
)

var (
	validateTopologySessionDir string
	validateTopologyStrict     bool
	validateTopologyOutput     string
)

var validateTopologyCmd = &cobra.Command{
	Use:   "validate-topology",
	Short: "Validate agent topology constraints",
	Long: `Validate the agent topology tree against PM mode constraints.

Reads agent registry from session state and validates:
  - Every TechLead has at least one Coder child
  - Every Coder has a TechLead parent
  - DevOps exists when PM mode is enabled
  - No persona acts outside its allowed actions
  - Parent-child relationships are valid (no cycles, no orphans)

Exit codes:
  0  Topology valid
  1  Warnings present (degraded but functional) — only if --strict not set
  2  Violation detected (hard block)

Examples:
  dark-governance validate-topology
  dark-governance validate-topology --strict
  dark-governance validate-topology --session-dir .artifacts/state/sessions/
  dark-governance validate-topology --output json`,
	RunE: runValidateTopology,
}

func init() {
	validateTopologyCmd.Flags().StringVar(&validateTopologySessionDir, "session-dir", ".artifacts/state/sessions/",
		"Path to session state directory")
	validateTopologyCmd.Flags().BoolVar(&validateTopologyStrict, "strict", false,
		"Fail on any violation including warnings")
	validateTopologyCmd.Flags().StringVar(&validateTopologyOutput, "output", "human",
		"Output format: human or json")
}

// topologySessionState represents the minimal session state structure
// needed for topology validation.
type topologySessionState struct {
	Agents        []topology.AgentRegistration `json:"agents"`
	PMEnabled     bool                         `json:"pm_mode_enabled"`
	TopologyValid bool                         `json:"topology_valid"`
}

// topologyReport is the JSON output structure for topology validation.
type topologyReport struct {
	Status     string   `json:"status"` // valid, warning, violation
	PMEnabled  bool     `json:"pm_mode_enabled"`
	AgentCount int      `json:"agent_count"`
	Violations []string `json:"violations,omitempty"`
	Warnings   []string `json:"warnings,omitempty"`
}

func runValidateTopology(cmd *cobra.Command, args []string) error {
	// Load topology rules
	rulesPath := filepath.Join(filepath.Dir(validateTopologySessionDir), "topology-rules.json")
	rules, err := topology.LoadRules(rulesPath)
	if err != nil {
		return fmt.Errorf("failed to load topology rules: %w", err)
	}

	// Load session state
	sessionPath := filepath.Join(validateTopologySessionDir, "latest.json")
	registry, pmEnabled, loadErr := loadTopologyRegistry(sessionPath, rules)
	if loadErr != nil {
		// If no session state, use an empty registry and validate rules only
		registry = nil
		pmEnabled = rules.PMEnabled
	}

	// Run validation
	result := topology.ValidateTopology(registry, pmEnabled)

	// Build report
	report := topologyReport{
		PMEnabled:  pmEnabled,
		AgentCount: len(registry),
		Violations: result.Violations,
		Warnings:   result.Warnings,
	}

	switch {
	case !result.Valid:
		report.Status = "violation"
	case len(result.Warnings) > 0:
		report.Status = "warning"
	default:
		report.Status = "valid"
	}

	// Output
	if validateTopologyOutput == "json" {
		return outputTopologyJSON(cmd, report)
	}
	return outputTopologyHuman(cmd, report)
}

func loadTopologyRegistry(sessionPath string, rules *topology.TopologyRules) ([]topology.AgentRegistration, bool, error) {
	data, err := os.ReadFile(sessionPath)
	if err != nil {
		return nil, false, err
	}

	var state topologySessionState
	if err := json.Unmarshal(data, &state); err != nil {
		return nil, false, fmt.Errorf("failed to parse session state: %w", err)
	}

	pmEnabled := state.PMEnabled
	if !pmEnabled {
		pmEnabled = rules.PMEnabled
	}

	return state.Agents, pmEnabled, nil
}

func outputTopologyJSON(cmd *cobra.Command, report topologyReport) error {
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal report: %w", err)
	}
	fmt.Fprintln(os.Stdout, string(data))

	switch report.Status {
	case "violation":
		cmd.SilenceErrors = true
		os.Exit(2)
	case "warning":
		if validateTopologyStrict {
			cmd.SilenceErrors = true
			os.Exit(2)
		}
	}
	return nil
}

func outputTopologyHuman(cmd *cobra.Command, report topologyReport) error {
	fmt.Fprintln(os.Stdout, "Topology Validation Report")
	fmt.Fprintln(os.Stdout, "==========================")
	fmt.Fprintf(os.Stdout, "PM Mode:  %v\n", report.PMEnabled)
	fmt.Fprintf(os.Stdout, "Agents:   %d\n", report.AgentCount)
	fmt.Fprintln(os.Stdout, "")

	if len(report.Violations) > 0 {
		fmt.Fprintln(os.Stdout, "Violations:")
		for _, v := range report.Violations {
			fmt.Fprintf(os.Stdout, "  [FAIL] %s\n", v)
		}
		fmt.Fprintln(os.Stdout, "")
	}

	if len(report.Warnings) > 0 {
		fmt.Fprintln(os.Stdout, "Warnings:")
		for _, w := range report.Warnings {
			fmt.Fprintf(os.Stdout, "  [WARN] %s\n", w)
		}
		fmt.Fprintln(os.Stdout, "")
	}

	switch report.Status {
	case "valid":
		fmt.Fprintln(os.Stdout, "Overall: VALID")
	case "warning":
		fmt.Fprintln(os.Stdout, "Overall: WARNING (degraded but functional)")
		if validateTopologyStrict {
			fmt.Fprintln(os.Stdout, "  --strict mode: treating warnings as violations")
			cmd.SilenceErrors = true
			os.Exit(2)
		}
	case "violation":
		fmt.Fprintf(os.Stdout, "Overall: VIOLATION (%d issues)\n", len(report.Violations))
		cmd.SilenceErrors = true
		os.Exit(2)
	}

	return nil
}
