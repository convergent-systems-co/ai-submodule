package main

import (
	"fmt"
	"os"

	"github.com/SET-Apps/ai-submodule/src/internal/docs"
	"github.com/SET-Apps/ai-submodule/src/internal/version"
	"github.com/spf13/cobra"
)

var (
	// Global flags
	flagJSON   bool
	flagConfig string
	flagDocs   bool
)

var rootCmd = &cobra.Command{
	Use:   "dark-governance",
	Short: "Dark Factory Governance CLI",
	Long: `dark-governance is the CLI for the Dark Factory Governance platform.

It provides governance enforcement, policy evaluation, and autonomous
delivery orchestration as a self-contained binary distribution.`,
	Version: version.Get().Version,
}

func init() {
	rootCmd.PersistentFlags().BoolVar(&flagJSON, "json", false, "Output in JSON format")
	rootCmd.PersistentFlags().StringVar(&flagConfig, "config", "", "Path to project.yaml config file")
	rootCmd.PersistentFlags().BoolVar(&flagDocs, "docs", false, "Open governance documentation site in browser")

	// Override the default version template to include full info
	rootCmd.SetVersionTemplate(fmt.Sprintf("%s\n", version.Get().String()))

	// --docs flag short-circuits to open the documentation site
	rootCmd.PersistentPreRunE = func(cmd *cobra.Command, args []string) error {
		if flagDocs {
			url := docs.DocsURL
			fmt.Fprintf(os.Stdout, "Opening documentation: %s\n", url)
			if _, err := docs.OpenBrowser(url); err != nil {
				return fmt.Errorf("could not open browser: %w\n\nOpen manually: %s", err, url)
			}
			os.Exit(0)
		}
		return nil
	}

	rootCmd.AddCommand(versionCmd)
	rootCmd.AddCommand(initCmd)
	rootCmd.AddCommand(installCmd)
	rootCmd.AddCommand(updateCmd)
	rootCmd.AddCommand(verifyCmd)
	rootCmd.AddCommand(engineCmd)
	rootCmd.AddCommand(depsCmd)
	rootCmd.AddCommand(mcpCmd)
	rootCmd.AddCommand(configureCmd)
	rootCmd.AddCommand(uninstallCmd)
	rootCmd.AddCommand(verifyEnvironmentCmd)
	rootCmd.AddCommand(validateTopologyCmd)
	rootCmd.AddCommand(docsCmd)

	// Silence usage on error — cobra prints usage by default on errors,
	// which is noisy for non-usage errors.
	rootCmd.SilenceUsage = true
	rootCmd.SilenceErrors = true

	// Set output to stderr for errors
	rootCmd.SetErr(os.Stderr)
}
