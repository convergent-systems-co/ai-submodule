package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/config"
	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/locks"
	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/runner"
	"github.com/SET-Apps/ai-submodule/src/internal/orchestrator/session"
	"github.com/SET-Apps/ai-submodule/src/internal/preflight"
	"github.com/spf13/cobra"
)

// ---------------------------------------------------------------------------
// Flag variables
// ---------------------------------------------------------------------------

var (
	orchConfigPath string
	orchSessionID  string

	// step
	orchStepComplete int
	orchStepResult   string
	orchStepAgent    string

	// signal
	orchSignalType  string
	orchSignalCount int

	// gate
	orchGatePhase int

	// register
	orchRegPersona       string
	orchRegTaskID        string
	orchRegCorrelationID string
	orchRegParentTaskID  string

	// heartbeat
	orchHBAgent  string
	orchHBStatus string

	// dispatch
	orchDispatchPersona string
	orchDispatchParent  string
	orchDispatchAssign  string

	// preflight
	orchPreflightConfig string

	// locks
	orchLocksCleanup      bool
	orchLocksForceRelease string
)

// ---------------------------------------------------------------------------
// Parent command
// ---------------------------------------------------------------------------

var orchestratorCmd = &cobra.Command{
	Use:   "orchestrator",
	Short: "Orchestrator control-plane commands",
	Long: `Commands for the orchestrator control plane.

The orchestrator manages phase transitions, agent dispatch, capacity
gate checks, and session persistence for autonomous delivery.`,
}

// ---------------------------------------------------------------------------
// init — subcommand registration
// ---------------------------------------------------------------------------

func init() {
	// init subcommand
	orchInitCmd.Flags().StringVar(&orchConfigPath, "config", "project.yaml", "Path to project.yaml")
	orchInitCmd.Flags().StringVar(&orchSessionID, "session-id", "", "Session ID (auto-generated if empty)")

	// step subcommand
	orchStepCmd.Flags().IntVar(&orchStepComplete, "complete", 0, "Phase number just completed")
	orchStepCmd.Flags().StringVar(&orchStepResult, "result", "{}", "Phase result as JSON string")
	orchStepCmd.Flags().StringVar(&orchStepAgent, "agent", "", "Agent ID performing the step")
	orchStepCmd.Flags().StringVar(&orchSessionID, "session-id", "", "Session ID")

	// signal subcommand
	orchSignalCmd.Flags().StringVar(&orchSignalType, "type", "", "Signal type: tool_call, turn, issue_completed")
	orchSignalCmd.Flags().IntVar(&orchSignalCount, "count", 1, "Number of signals to record")

	// gate subcommand
	orchGateCmd.Flags().IntVar(&orchGatePhase, "phase", 0, "Target phase to check")

	// status subcommand
	orchStatusCmd.Flags().StringVar(&orchSessionID, "session-id", "", "Session ID")

	// tree subcommand
	orchTreeCmd.Flags().StringVar(&orchSessionID, "session-id", "", "Session ID")

	// register subcommand
	orchRegisterCmd.Flags().StringVar(&orchRegPersona, "persona", "", "Agent persona")
	orchRegisterCmd.Flags().StringVar(&orchRegTaskID, "task-id", "", "Task ID for the agent")
	orchRegisterCmd.Flags().StringVar(&orchRegCorrelationID, "correlation-id", "", "Correlation ID")
	orchRegisterCmd.Flags().StringVar(&orchRegParentTaskID, "parent-task-id", "", "Parent task ID")

	// heartbeat subcommand
	orchHeartbeatCmd.Flags().StringVar(&orchHBAgent, "agent", "", "Agent ID")
	orchHeartbeatCmd.Flags().StringVar(&orchHBStatus, "status", "", "Agent status update")

	// dispatch subcommand
	orchDispatchCmd.Flags().StringVar(&orchDispatchPersona, "persona", "", "Persona to dispatch")
	orchDispatchCmd.Flags().StringVar(&orchDispatchParent, "parent", "", "Parent task ID")
	orchDispatchCmd.Flags().StringVar(&orchDispatchAssign, "assign", "{}", "Assignment as JSON string")

	// preflight subcommand
	orchPreflightCmd.Flags().StringVar(&orchPreflightConfig, "config", "project.yaml", "Path to project.yaml")

	// locks subcommand
	orchLocksCmd.Flags().BoolVar(&orchLocksCleanup, "cleanup", false, "Clean up stale locks")
	orchLocksCmd.Flags().StringVar(&orchLocksForceRelease, "force-release", "", "Force-release a lock by work ID")

	// Wire subcommands.
	orchestratorCmd.AddCommand(orchInitCmd)
	orchestratorCmd.AddCommand(orchStepCmd)
	orchestratorCmd.AddCommand(orchSignalCmd)
	orchestratorCmd.AddCommand(orchGateCmd)
	orchestratorCmd.AddCommand(orchStatusCmd)
	orchestratorCmd.AddCommand(orchTreeCmd)
	orchestratorCmd.AddCommand(orchRegisterCmd)
	orchestratorCmd.AddCommand(orchHeartbeatCmd)
	orchestratorCmd.AddCommand(orchDispatchCmd)
	orchestratorCmd.AddCommand(orchPreflightCmd)
	orchestratorCmd.AddCommand(orchLocksCmd)

	// Register with root.
	rootCmd.AddCommand(orchestratorCmd)
}

// ---------------------------------------------------------------------------
// Helper: build a StepRunner from flags
// ---------------------------------------------------------------------------

// loadRunner creates a StepRunner by loading config and session store.
func loadRunner(configPath string) (*runner.StepRunner, *config.OrchestratorConfig, error) {
	cfg, err := config.LoadConfig(configPath)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to load config: %w", err)
	}
	store := session.NewStore(cfg.SessionDir)
	sr := runner.NewStepRunner(cfg, store)
	return sr, cfg, nil
}

// loadRunnerWithSession creates a StepRunner and initialises it with a session.
func loadRunnerWithSession(configPath, sessionID string) (*runner.StepRunner, error) {
	sr, _, err := loadRunner(configPath)
	if err != nil {
		return nil, err
	}

	// Resolve session ID: use provided, fall back to latest.
	if sessionID == "" {
		sessionID = "latest"
	}

	if _, initErr := sr.InitSession(sessionID); initErr != nil {
		return nil, fmt.Errorf("failed to init session %q: %w", sessionID, initErr)
	}
	return sr, nil
}

// outputJSON marshals v as indented JSON and writes to stdout.
func outputJSON(v interface{}) error {
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal output: %w", err)
	}
	fmt.Fprintln(os.Stdout, string(data))
	return nil
}

// ---------------------------------------------------------------------------
// 1. init
// ---------------------------------------------------------------------------

var orchInitCmd = &cobra.Command{
	Use:   "init",
	Short: "Initialise an orchestrator session",
	Long: `Create or resume an orchestrator session.

Loads configuration from project.yaml and initialises session state.
If --session-id is provided, that session is created or resumed.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		sr, _, err := loadRunner(orchConfigPath)
		if err != nil {
			return err
		}

		sid := orchSessionID
		if sid == "" {
			sid = fmt.Sprintf("session-%d", os.Getpid())
		}

		result, err := sr.InitSession(sid)
		if err != nil {
			return err
		}
		return outputJSON(result)
	},
}

// ---------------------------------------------------------------------------
// 2. step
// ---------------------------------------------------------------------------

var orchStepCmd = &cobra.Command{
	Use:   "step",
	Short: "Complete a phase and transition to the next",
	Long: `Record a completed phase and advance the state machine.

The --result flag carries phase-specific output as a JSON string.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		sr, err := loadRunnerWithSession(orchConfigPath, orchSessionID)
		if err != nil {
			return err
		}

		var resultMap map[string]interface{}
		if orchStepResult != "" {
			if jsonErr := json.Unmarshal([]byte(orchStepResult), &resultMap); jsonErr != nil {
				return fmt.Errorf("invalid --result JSON: %w", jsonErr)
			}
		}

		result, err := sr.Step(orchStepComplete, resultMap, orchStepAgent)
		if err != nil {
			return err
		}

		if outErr := outputJSON(result); outErr != nil {
			return outErr
		}

		if result.Shutdown {
			os.Exit(2)
		}
		return nil
	},
}

// ---------------------------------------------------------------------------
// 3. signal
// ---------------------------------------------------------------------------

var orchSignalCmd = &cobra.Command{
	Use:   "signal",
	Short: "Record runtime signals (tool_call, turn, issue_completed)",
	RunE: func(cmd *cobra.Command, args []string) error {
		sr, err := loadRunnerWithSession(orchConfigPath, orchSessionID)
		if err != nil {
			return err
		}

		result, err := sr.RecordSignal(orchSignalType, orchSignalCount)
		if err != nil {
			return err
		}

		if outErr := outputJSON(result); outErr != nil {
			return outErr
		}

		if result.Shutdown {
			os.Exit(2)
		}
		return nil
	},
}

// ---------------------------------------------------------------------------
// 4. gate
// ---------------------------------------------------------------------------

var orchGateCmd = &cobra.Command{
	Use:   "gate",
	Short: "Query the gate action for a target phase",
	RunE: func(cmd *cobra.Command, args []string) error {
		sr, err := loadRunnerWithSession(orchConfigPath, orchSessionID)
		if err != nil {
			return err
		}

		result, err := sr.QueryGate(orchGatePhase)
		if err != nil {
			return err
		}
		return outputJSON(result)
	},
}

// ---------------------------------------------------------------------------
// 5. status
// ---------------------------------------------------------------------------

var orchStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show current orchestrator state",
	RunE: func(cmd *cobra.Command, args []string) error {
		sr, err := loadRunnerWithSession(orchConfigPath, orchSessionID)
		if err != nil {
			return err
		}

		result, err := sr.GetStatus()
		if err != nil {
			return err
		}
		return outputJSON(result)
	},
}

// ---------------------------------------------------------------------------
// 6. tree
// ---------------------------------------------------------------------------

var orchTreeCmd = &cobra.Command{
	Use:   "tree",
	Short: "Display workload tree",
	Long:  `Builds and prints the agent workload tree as a text diagram.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		sr, err := loadRunnerWithSession(orchConfigPath, orchSessionID)
		if err != nil {
			return err
		}

		treeText, err := sr.GetWorkloadTree()
		if err != nil {
			return err
		}
		fmt.Fprint(os.Stdout, treeText)
		return nil
	},
}

// ---------------------------------------------------------------------------
// 7. register
// ---------------------------------------------------------------------------

var orchRegisterCmd = &cobra.Command{
	Use:   "register",
	Short: "Register a new agent in the registry",
	RunE: func(cmd *cobra.Command, args []string) error {
		sr, err := loadRunnerWithSession(orchConfigPath, orchSessionID)
		if err != nil {
			return err
		}

		if regErr := sr.RegisterAgent(orchRegPersona, orchRegTaskID, orchRegCorrelationID, orchRegParentTaskID); regErr != nil {
			return regErr
		}
		return outputJSON(map[string]interface{}{
			"status":   "registered",
			"task_id":  orchRegTaskID,
			"persona":  orchRegPersona,
		})
	},
}

// ---------------------------------------------------------------------------
// 8. heartbeat
// ---------------------------------------------------------------------------

var orchHeartbeatCmd = &cobra.Command{
	Use:   "heartbeat",
	Short: "Record a heartbeat for an agent",
	RunE: func(cmd *cobra.Command, args []string) error {
		sr, err := loadRunnerWithSession(orchConfigPath, orchSessionID)
		if err != nil {
			return err
		}

		if hbErr := sr.RecordHeartbeat(orchHBAgent, orchHBStatus); hbErr != nil {
			return hbErr
		}
		return outputJSON(map[string]interface{}{
			"status":  "ok",
			"agent":   orchHBAgent,
		})
	},
}

// ---------------------------------------------------------------------------
// 9. dispatch
// ---------------------------------------------------------------------------

var orchDispatchCmd = &cobra.Command{
	Use:   "dispatch",
	Short: "Dispatch a new agent",
	RunE: func(cmd *cobra.Command, args []string) error {
		sr, err := loadRunnerWithSession(orchConfigPath, orchSessionID)
		if err != nil {
			return err
		}

		var assignMap map[string]interface{}
		if orchDispatchAssign != "" {
			if jsonErr := json.Unmarshal([]byte(orchDispatchAssign), &assignMap); jsonErr != nil {
				return fmt.Errorf("invalid --assign JSON: %w", jsonErr)
			}
		}

		result, err := sr.DispatchAgent(orchDispatchPersona, orchDispatchParent, assignMap)
		if err != nil {
			return err
		}

		if outErr := outputJSON(result); outErr != nil {
			return outErr
		}

		if result.Shutdown {
			os.Exit(2)
		}
		return nil
	},
}

// ---------------------------------------------------------------------------
// 10. preflight
// ---------------------------------------------------------------------------

var orchPreflightCmd = &cobra.Command{
	Use:   "preflight",
	Short: "Validate project.yaml configuration",
	RunE: func(cmd *cobra.Command, args []string) error {
		result := preflight.ValidateProjectYAML(orchPreflightConfig)
		return outputJSON(result)
	},
}

// ---------------------------------------------------------------------------
// 11. locks
// ---------------------------------------------------------------------------

var orchLocksCmd = &cobra.Command{
	Use:   "locks",
	Short: "Manage work-unit locks",
	Long: `Clean up stale locks or force-release a specific lock.

Without flags, lists current lock state.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		// Determine lock directory from config if available.
		lockDir := ".artifacts/state/locks"
		if orchConfigPath != "" {
			if cfg, err := config.LoadConfig(orchConfigPath); err == nil && cfg.SessionDir != "" {
				// Put locks alongside sessions.
				lockDir = cfg.SessionDir + "/../locks"
			}
		}

		mgr := locks.NewManager(lockDir)

		if orchLocksForceRelease != "" {
			if err := mgr.ForceRelease(orchLocksForceRelease); err != nil {
				return err
			}
			return outputJSON(map[string]interface{}{
				"status":  "released",
				"work_id": orchLocksForceRelease,
			})
		}

		if orchLocksCleanup {
			cleaned, err := mgr.CleanupStale()
			if err != nil {
				return err
			}
			return outputJSON(map[string]interface{}{
				"status":  "cleaned",
				"removed": cleaned,
			})
		}

		// Default: report lock directory.
		return outputJSON(map[string]interface{}{
			"lock_dir": lockDir,
			"hint":     "use --cleanup or --force-release <work-id>",
		})
	},
}
