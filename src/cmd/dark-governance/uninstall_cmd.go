package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/SET-Apps/ai-submodule/src/internal/home"
	"github.com/spf13/cobra"
)

var (
	uninstallAll bool
	uninstallYes bool
)

var uninstallCmd = &cobra.Command{
	Use:   "uninstall",
	Short: "Remove governance home cache and dependencies",
	Long: `Remove the governance home cache (~/.ai/versions/) and virtual environment (~/.ai/venv/).

By default, only the home cache and venv are removed. Use --all to
remove the entire home directory.

Examples:
  dark-governance uninstall                  # Remove versions + venv
  dark-governance uninstall --all            # Remove everything under ~/.ai/
  dark-governance uninstall --yes            # Skip confirmation`,
	RunE: runUninstall,
}

func init() {
	uninstallCmd.Flags().BoolVar(&uninstallAll, "all", false, "Remove entire home directory (versions, venv, all cached data)")
	uninstallCmd.Flags().BoolVar(&uninstallYes, "yes", false, "Skip confirmation prompt")
}

// uninstallTarget describes a directory or file to remove.
type uninstallTarget struct {
	Path        string `json:"path"`
	Description string `json:"description"`
	Exists      bool   `json:"exists"`
}

func runUninstall(cmd *cobra.Command, args []string) error {
	homeDir, err := home.DefaultHome()
	if err != nil {
		return fmt.Errorf("failed to determine home directory: %w", err)
	}

	// Build list of targets
	var targets []uninstallTarget

	if uninstallAll {
		targets = append(targets, uninstallTarget{
			Path:        homeDir,
			Description: "Entire home directory (versions, venv, all cached data)",
		})
	} else {
		versionsDir := filepath.Join(homeDir, "versions")
		venvDir := filepath.Join(homeDir, "venv")

		targets = append(targets,
			uninstallTarget{
				Path:        versionsDir,
				Description: "Installed governance versions",
			},
			uninstallTarget{
				Path:        venvDir,
				Description: "Python virtual environment",
			},
		)
	}

	// Check which targets exist
	anyExists := false
	for i := range targets {
		if _, statErr := os.Stat(targets[i].Path); statErr == nil {
			targets[i].Exists = true
			anyExists = true
		}
	}

	if !anyExists {
		if flagJSON {
			fmt.Fprintf(os.Stdout, `{"status": "nothing_to_remove", "home": %q}`+"\n", homeDir)
		} else {
			fmt.Fprintln(os.Stdout, "Nothing to uninstall. No governance data found.")
		}
		return nil
	}

	// Show what will be removed
	if !flagJSON && !uninstallYes {
		fmt.Fprintln(os.Stdout, "The following will be removed:")
		fmt.Fprintln(os.Stdout, "")
		for _, t := range targets {
			if t.Exists {
				fmt.Fprintf(os.Stdout, "  [REMOVE] %s\n", t.Path)
				fmt.Fprintf(os.Stdout, "           %s\n", t.Description)
			} else {
				fmt.Fprintf(os.Stdout, "  [SKIP]   %s (not found)\n", t.Path)
			}
		}
		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintln(os.Stdout, "Use --yes to skip this confirmation.")
		fmt.Fprintln(os.Stdout, "Dry run complete. Add --yes to proceed.")
		return nil
	}

	// Perform removal
	var removed []string
	var errors []string

	for _, t := range targets {
		if !t.Exists {
			continue
		}

		if err := os.RemoveAll(t.Path); err != nil {
			errors = append(errors, fmt.Sprintf("failed to remove %s: %v", t.Path, err))
		} else {
			removed = append(removed, t.Path)
		}
	}

	if flagJSON {
		output := map[string]interface{}{
			"status":  "uninstalled",
			"removed": removed,
			"errors":  errors,
			"home":    homeDir,
		}
		data, _ := json.MarshalIndent(output, "", "  ")
		fmt.Fprintln(os.Stdout, string(data))
		return nil
	}

	if len(removed) > 0 {
		fmt.Fprintln(os.Stdout, "Uninstalled successfully.")
		for _, r := range removed {
			fmt.Fprintf(os.Stdout, "  Removed: %s\n", r)
		}
	}
	if len(errors) > 0 {
		fmt.Fprintln(os.Stderr, "")
		for _, e := range errors {
			fmt.Fprintf(os.Stderr, "  Error: %s\n", e)
		}
	}

	return nil
}
