// dark-governance is the CLI entry point for the Dark Factory Governance platform.
//
// It provides a hardened, self-contained binary distribution of the governance
// framework that embeds all governance content (policies, schemas, prompts)
// directly into the binary via go:embed.
package main

import (
	"errors"
	"fmt"
	"os"

	"github.com/SET-Apps/ai-submodule/src/internal/exitcode"
)

func main() {
	if err := rootCmd.Execute(); err != nil {
		var exitErr *exitcode.ExitError
		if errors.As(err, &exitErr) {
			fmt.Fprintf(os.Stderr, "Error: %s\n", exitErr.Error())
			os.Exit(exitErr.Code)
		}
		fmt.Fprintf(os.Stderr, "Error: %s\n", err)
		os.Exit(1)
	}
}
