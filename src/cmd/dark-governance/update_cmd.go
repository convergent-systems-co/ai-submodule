package main

import (
	"fmt"
	"os"

	"github.com/SET-Apps/ai-submodule/src/internal/home"
	"github.com/SET-Apps/ai-submodule/src/internal/version"
	"github.com/spf13/cobra"
)

var updateCmd = &cobra.Command{
	Use:   "update",
	Short: "Check for and apply governance updates",
	Long: `Check if a newer version of governance content is available.

This command checks the current installed version against what is available
and reports whether an update is needed. In a future release, it will
support downloading and installing newer versions automatically.

Currently, to update:
  1. Download the latest dark-governance binary
  2. Run 'dark-governance install --force'

Examples:
  dark-governance update          # Check for updates
  dark-governance update --json   # Machine-readable output`,
	RunE: runUpdate,
}

func runUpdate(cmd *cobra.Command, args []string) error {
	ver := version.Get().Version

	homeDir, err := home.DefaultHome()
	if err != nil {
		return fmt.Errorf("failed to determine home directory: %w", err)
	}

	// List installed versions
	versions, err := home.ListVersions(homeDir)
	if err != nil {
		versions = nil
	}

	// Check if the current binary version is installed
	isCurrentInstalled := home.IsInstalled(homeDir, ver)

	if flagJSON {
		fmt.Fprintf(os.Stdout, `{"current_version": %q, "home": %q, "installed": %v, "installed_versions": [`, ver, homeDir, isCurrentInstalled)
		for i, v := range versions {
			if i > 0 {
				fmt.Fprint(os.Stdout, ", ")
			}
			fmt.Fprintf(os.Stdout, "%q", v)
		}
		fmt.Fprintln(os.Stdout, `], "update_available": false, "message": "automatic updates not yet supported"}`)
		return nil
	}

	fmt.Fprintln(os.Stdout, "Governance update check")
	fmt.Fprintln(os.Stdout, "")
	fmt.Fprintf(os.Stdout, "  Binary version:  %s\n", ver)
	fmt.Fprintf(os.Stdout, "  Home directory:   %s\n", homeDir)

	if len(versions) > 0 {
		fmt.Fprintln(os.Stdout, "  Installed versions:")
		for _, v := range versions {
			marker := "  "
			if v == ver {
				marker = "* "
			}
			fmt.Fprintf(os.Stdout, "    %s%s\n", marker, v)
		}
	} else {
		fmt.Fprintln(os.Stdout, "  No versions installed.")
	}

	if !isCurrentInstalled {
		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintf(os.Stdout, "  Version %s is not installed. Run 'dark-governance install' first.\n", ver)
	}

	fmt.Fprintln(os.Stdout, "")
	fmt.Fprintln(os.Stdout, "  Automatic updates are not yet supported.")
	fmt.Fprintln(os.Stdout, "  To update manually: download the latest binary and run 'dark-governance install --force'.")

	return nil
}
