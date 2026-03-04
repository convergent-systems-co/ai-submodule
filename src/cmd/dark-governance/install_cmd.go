package main

import (
	"fmt"
	"io/fs"
	"os"

	govembed "github.com/SET-Apps/ai-submodule/src/internal/embed"
	"github.com/SET-Apps/ai-submodule/src/internal/home"
	"github.com/SET-Apps/ai-submodule/src/internal/version"
	"github.com/spf13/cobra"
)

var (
	installCI    bool
	installForce bool
)

var installCmd = &cobra.Command{
	Use:   "install",
	Short: "Install governance content to the home directory",
	Long: `Install embedded governance content to the home directory cache.

Extracts all governance content (policies, schemas, prompts, personas, commands,
templates) from the binary to ~/.ai/versions/<version>/. This allows multiple
repositories to share the same governance content without requiring a git submodule.

The home directory location can be configured via:
  - DARK_GOVERNANCE_HOME environment variable
  - XDG_DATA_HOME/dark-governance (if XDG_DATA_HOME is set)
  - ~/.ai (default)

In CI environments, use --ci to write to $RUNNER_TEMP/.ai/ or $HOME/.ai/.

Examples:
  dark-governance install                         # Install to ~/.ai/
  dark-governance install --ci                    # Install for CI
  dark-governance install --force                 # Reinstall even if version exists
  DARK_GOVERNANCE_HOME=/opt/gov dark-governance install  # Custom location`,
	RunE: runInstall,
}

func init() {
	installCmd.Flags().BoolVar(&installCI, "ci", false, "Use CI-appropriate home directory ($RUNNER_TEMP/.ai/ or $HOME/.ai/)")
	installCmd.Flags().BoolVar(&installForce, "force", false, "Reinstall even if the version already exists")
}

func runInstall(cmd *cobra.Command, args []string) error {
	if !govembed.HasContent() {
		return fmt.Errorf("binary does not contain governance content — was it built with 'make prepare-embed'?")
	}

	ver := version.Get().Version
	contentHash := govembed.ContentHash()

	// Determine home directory
	homeDir, err := home.HomeForInstall(installCI)
	if err != nil {
		return fmt.Errorf("failed to determine home directory: %w", err)
	}

	// Check if already installed
	if !installForce && home.IsInstalled(homeDir, ver) {
		if flagJSON {
			fmt.Fprintf(os.Stdout, `{"status": "already_installed", "version": %q, "home": %q}`+"\n", ver, homeDir)
		} else {
			fmt.Fprintf(os.Stdout, "Version %s is already installed at %s\n", ver, home.VersionDir(homeDir, ver))
			fmt.Fprintln(os.Stdout, "Use --force to reinstall.")
		}
		return nil
	}

	// If force-installing over existing version, clean it first
	if installForce && home.IsInstalled(homeDir, ver) {
		if err := home.CleanVersion(homeDir, ver); err != nil {
			return fmt.Errorf("failed to clean existing version: %w", err)
		}
	}

	// Get the content filesystem (strip _content/ prefix)
	contentFS, err := fs.Sub(govembed.GovernanceFS(), "_content")
	if err != nil {
		return fmt.Errorf("failed to access embedded content: %w", err)
	}

	// Install
	extracted, err := home.Install(homeDir, ver, contentHash, contentFS)
	if err != nil {
		return fmt.Errorf("installation failed: %w", err)
	}

	// Print result
	versionDir := home.VersionDir(homeDir, ver)
	if flagJSON {
		fmt.Fprintf(os.Stdout, `{"status": "installed", "version": %q, "content_hash": %q, "home": %q, "version_dir": %q, "files_extracted": %d}`+"\n",
			ver, contentHash, homeDir, versionDir, extracted)
	} else {
		fmt.Fprintln(os.Stdout, "Governance content installed successfully.")
		fmt.Fprintf(os.Stdout, "  Version:    %s\n", ver)
		fmt.Fprintf(os.Stdout, "  Content:    %s\n", contentHash)
		fmt.Fprintf(os.Stdout, "  Location:   %s\n", versionDir)
		fmt.Fprintf(os.Stdout, "  Files:      %d extracted\n", extracted)

		if installCI {
			fmt.Fprintln(os.Stdout, "  Mode:       CI")
		} else {
			fmt.Fprintln(os.Stdout, "  Mode:       home-cache")
		}

		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintln(os.Stdout, "Run 'dark-governance init' in a repository to set up governance.")
	}

	return nil
}
