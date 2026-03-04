package main

import (
	"fmt"
	"os"

	govembed "github.com/SET-Apps/ai-submodule/src/internal/embed"
	"github.com/SET-Apps/ai-submodule/src/internal/lockfile"
	"github.com/SET-Apps/ai-submodule/src/internal/version"
	"github.com/spf13/cobra"
)

var (
	verifyLockfilePath string
)

var verifyCmd = &cobra.Command{
	Use:   "verify",
	Short: "Verify governance lockfile integrity",
	Long: `Verify that the .dark-governance.lock file matches the running binary.

Compares the content_hash in the lockfile against the SHA-256 hash of the
binary's embedded governance content. Exits 0 if they match, 1 if they don't.

This is used in CI to ensure the binary version matches what was installed
at init time.

Examples:
  dark-governance verify                              # Check default lockfile
  dark-governance verify --lockfile path/to/lockfile   # Check custom path`,
	RunE: runVerify,
}

func init() {
	verifyCmd.Flags().StringVar(&verifyLockfilePath, "lockfile", lockfile.DefaultPath, "Path to lockfile")
}

func runVerify(cmd *cobra.Command, args []string) error {
	currentHash := govembed.ContentHash()
	ver := version.Get()

	// Check if lockfile exists
	if !lockfile.Exists(verifyLockfilePath) {
		if flagJSON {
			fmt.Fprintf(os.Stdout, `{"status": "error", "message": "lockfile not found", "path": %q}`+"\n", verifyLockfilePath)
		} else {
			fmt.Fprintf(os.Stderr, "Error: lockfile not found at %s\n", verifyLockfilePath)
			fmt.Fprintln(os.Stderr, "Run 'dark-governance init' to create one.")
		}
		return fmt.Errorf("lockfile not found at %s", verifyLockfilePath)
	}

	// Read the lockfile
	info, err := lockfile.Read(verifyLockfilePath)
	if err != nil {
		if flagJSON {
			fmt.Fprintf(os.Stdout, `{"status": "error", "message": %q}`+"\n", err.Error())
		}
		return err
	}

	// Verify content hash
	if err := lockfile.Verify(verifyLockfilePath, currentHash); err != nil {
		if flagJSON {
			fmt.Fprintf(os.Stdout, `{"status": "mismatch", "lockfile_hash": %q, "binary_hash": %q, "lockfile_version": %q, "binary_version": %q}`+"\n",
				info.ContentHash, currentHash, info.Version, ver.Version)
		} else {
			fmt.Fprintln(os.Stderr, "FAIL: lockfile integrity check failed.")
			fmt.Fprintf(os.Stderr, "  Lockfile hash:    %s\n", info.ContentHash)
			fmt.Fprintf(os.Stderr, "  Binary hash:      %s\n", currentHash)
			fmt.Fprintf(os.Stderr, "  Lockfile version: %s\n", info.Version)
			fmt.Fprintf(os.Stderr, "  Binary version:   %s\n", ver.Version)
			fmt.Fprintln(os.Stderr, "")
			fmt.Fprintln(os.Stderr, "The governance binary does not match the lockfile.")
			fmt.Fprintln(os.Stderr, "Run 'dark-governance init --force' to update, or install the correct version.")
		}
		return err
	}

	// Success
	if flagJSON {
		fmt.Fprintf(os.Stdout, `{"status": "verified", "content_hash": %q, "version": %q, "lockfile_version": %q}`+"\n",
			currentHash, ver.Version, info.Version)
	} else {
		fmt.Fprintln(os.Stdout, "OK: lockfile integrity verified.")
		fmt.Fprintf(os.Stdout, "  Content hash: %s\n", currentHash)
		fmt.Fprintf(os.Stdout, "  Version:      %s (lockfile: %s)\n", ver.Version, info.Version)
	}

	return nil
}
