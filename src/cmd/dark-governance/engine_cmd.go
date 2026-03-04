package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	govembed "github.com/SET-Apps/ai-submodule/src/internal/embed"
	"github.com/SET-Apps/ai-submodule/src/internal/engine"
	"github.com/SET-Apps/ai-submodule/src/internal/exitcode"
	"github.com/SET-Apps/ai-submodule/src/internal/topology"
	"github.com/SET-Apps/ai-submodule/src/internal/version"
	"github.com/spf13/cobra"
)

var (
	engineEmissionsDir string
	engineProfile      string
	engineOutputFile   string
	engineStrict       bool
	engineLogFile      string
	engineCIPassed     bool
	engineCommitSHA    string
	enginePRNumber     int
	engineRepo         string
	engineDryRun       bool
)

var engineCmd = &cobra.Command{
	Use:   "engine",
	Short: "Governance policy engine commands",
	Long: `Commands for the governance policy engine.

The engine evaluates panel emissions against embedded policy profiles
and produces governance manifests.`,
}

var engineRunCmd = &cobra.Command{
	Use:   "run",
	Short: "Evaluate emissions against policy",
	Long: `Read panel emissions from disk and evaluate them against an embedded policy profile.

The engine reads JSON emission files from the emissions directory, validates
their structure against the embedded panel-output schema, and evaluates them
against the specified policy profile.

Examples:
  dark-governance engine run
  dark-governance engine run --emissions-dir .artifacts/emissions/ --profile default
  dark-governance engine run --output manifest.json`,
	RunE: runEngineRun,
}

var engineStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show governance engine status",
	Long: `Display information about the embedded governance engine.

Shows the binary version, content hash, available policy profiles,
schemas, review prompts, and personas.`,
	RunE: runEngineStatus,
}

func init() {
	engineRunCmd.Flags().StringVar(&engineEmissionsDir, "emissions-dir", ".artifacts/emissions", "Path to emissions directory")
	engineRunCmd.Flags().StringVar(&engineProfile, "profile", "default", "Policy profile to evaluate against")
	engineRunCmd.Flags().StringVar(&engineOutputFile, "output", "", "Output manifest file path (default: stdout)")
	engineRunCmd.Flags().BoolVar(&engineStrict, "strict", false, "Fail on topology violations before evaluating emissions")
	engineRunCmd.Flags().StringVar(&engineLogFile, "log-file", "", "Write evaluation log to file")
	engineRunCmd.Flags().BoolVar(&engineCIPassed, "ci-checks-passed", true, "Whether CI checks passed")
	engineRunCmd.Flags().StringVar(&engineCommitSHA, "commit-sha", "", "Expected commit SHA for freshness validation")
	engineRunCmd.Flags().IntVar(&enginePRNumber, "pr-number", 0, "Pull request number")
	engineRunCmd.Flags().StringVar(&engineRepo, "repo", "", "Repository (owner/name)")
	engineRunCmd.Flags().BoolVar(&engineDryRun, "dry-run", false, "Evaluate but always exit 0")

	engineCmd.AddCommand(engineRunCmd)
	engineCmd.AddCommand(engineStatusCmd)
}

func runEngineRun(cmd *cobra.Command, args []string) error {
	if !govembed.HasContent() {
		return fmt.Errorf("binary does not contain governance content — was it built with 'make prepare-embed'?")
	}

	// Run topology validation in strict mode
	if engineStrict {
		cwd, cwdErr := os.Getwd()
		if cwdErr != nil {
			return fmt.Errorf("failed to get working directory: %w", cwdErr)
		}
		rulesPath := filepath.Join(cwd, ".artifacts", "state", "topology-rules.json")
		rules, rulesErr := topology.LoadRules(rulesPath)
		if rulesErr != nil {
			rules = topology.DefaultRules()
		}

		sessionPath := filepath.Join(cwd, ".artifacts", "state", "sessions", "latest.json")
		registry, pmEnabled, sessionErr := loadTopologyRegistry(sessionPath, rules)
		if sessionErr == nil {
			topoResult := topology.ValidateTopology(registry, pmEnabled)
			if !topoResult.Valid {
				if flagJSON {
					fmt.Fprintf(os.Stdout, `{"status":"topology_violation","violations":%q}`+"\n", strings.Join(topoResult.Violations, "; "))
				} else {
					fmt.Fprintln(os.Stderr, "Topology validation failed (--strict mode):")
					for _, v := range topoResult.Violations {
						fmt.Fprintf(os.Stderr, "  [FAIL] %s\n", v)
					}
				}
				cmd.SilenceErrors = true
				return &exitcode.ExitError{Code: 2, Message: "topology violation"}
			}
		}
	}

	// Load profile data
	profileData, err := govembed.GetPolicy(engineProfile)
	if err != nil {
		available, _ := govembed.ListPolicies()
		return fmt.Errorf("policy profile %q not found; available: %s", engineProfile, strings.Join(available, ", "))
	}

	// Load schema for validation (optional)
	schemaData, _ := govembed.GetSchema("panel-output.schema.json")

	// Set up log writer
	var logWriter = os.Stderr
	if engineLogFile != "" {
		f, err := os.Create(engineLogFile)
		if err != nil {
			return fmt.Errorf("failed to create log file: %w", err)
		}
		defer f.Close()
		logWriter = f
	}

	// Run the full evaluation pipeline
	result, err := engine.Evaluate(engine.EvaluateParams{
		EmissionsDir: engineEmissionsDir,
		ProfileData:  profileData,
		SchemaData:   schemaData,
		CIPassed:     engineCIPassed,
		CommitSHA:    engineCommitSHA,
		PRNumber:     enginePRNumber,
		Repo:         engineRepo,
		DryRun:       engineDryRun,
		LogWriter:    logWriter,
	})
	if err != nil {
		return err
	}

	// Output manifest
	data, err := json.MarshalIndent(result.Manifest, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal manifest: %w", err)
	}

	if engineOutputFile != "" {
		if err := os.MkdirAll(filepath.Dir(engineOutputFile), 0755); err != nil {
			return fmt.Errorf("failed to create output directory: %w", err)
		}
		if err := os.WriteFile(engineOutputFile, append(data, '\n'), 0644); err != nil {
			return fmt.Errorf("failed to write output: %w", err)
		}
		if !flagJSON {
			fmt.Fprintf(os.Stderr, "Manifest written to %s\n", engineOutputFile)
		}
	}

	if flagJSON || engineOutputFile == "" {
		fmt.Fprintln(os.Stdout, string(data))
	}

	// Print decision summary to stderr
	if !flagJSON {
		fmt.Fprintf(os.Stderr, "\nDecision: %s (exit %d)\n", result.Manifest.Decision.Action, result.ExitCode)
		fmt.Fprintf(os.Stderr, "  Rationale: %s\n", result.Manifest.Decision.Rationale)
	}

	if result.ExitCode != 0 {
		cmd.SilenceErrors = true
		return &exitcode.ExitError{Code: result.ExitCode, Message: result.Manifest.Decision.Action}
	}
	return nil
}

func runEngineStatus(cmd *cobra.Command, args []string) error {
	ver := version.Get()
	contentHash := govembed.ContentHash()
	hasContent := govembed.HasContent()

	if flagJSON {
		status := map[string]interface{}{
			"version":      ver.Version,
			"commit":       ver.Commit,
			"content_hash": contentHash,
			"has_content":  hasContent,
		}

		if hasContent {
			content := listExtractableContent()
			counts := make(map[string]int)
			for k, v := range content {
				counts[k] = len(v)
			}
			status["content_counts"] = counts
			status["content"] = content
		}

		data, err := json.MarshalIndent(status, "", "  ")
		if err != nil {
			return fmt.Errorf("failed to marshal status: %w", err)
		}
		fmt.Fprintln(os.Stdout, string(data))
		return nil
	}

	// Human-readable output
	fmt.Fprintln(os.Stdout, "Dark Factory Governance Engine")
	fmt.Fprintln(os.Stdout, "")
	fmt.Fprintf(os.Stdout, "  Version:      %s\n", ver.Version)
	fmt.Fprintf(os.Stdout, "  Commit:       %s\n", ver.Commit)
	fmt.Fprintf(os.Stdout, "  Content hash: %s\n", contentHash)
	fmt.Fprintf(os.Stdout, "  Has content:  %v\n", hasContent)

	if hasContent {
		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintln(os.Stdout, "  Embedded content:")

		content := listExtractableContent()
		for category, items := range content {
			fmt.Fprintf(os.Stdout, "    %-20s %d items\n", category+":", len(items))
		}

		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintln(os.Stdout, "  Available policy profiles:")
		if policies, err := govembed.ListPolicies(); err == nil {
			for _, p := range policies {
				fmt.Fprintf(os.Stdout, "    - %s\n", p)
			}
		}
	}

	return nil
}
