package main

import (
	"fmt"
	"os"

	"github.com/SET-Apps/ai-submodule/src/internal/version"
	"github.com/spf13/cobra"
)

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print version information",
	Long:  "Print detailed version information including commit, build date, Go version, and platform.",
	RunE:  runVersion,
}

func runVersion(cmd *cobra.Command, args []string) error {
	info := version.Get()

	if flagJSON {
		jsonStr, err := info.JSON()
		if err != nil {
			return fmt.Errorf("failed to format version as JSON: %w", err)
		}
		fmt.Fprintln(os.Stdout, jsonStr)
		return nil
	}

	fmt.Fprintln(os.Stdout, info.String())
	return nil
}
