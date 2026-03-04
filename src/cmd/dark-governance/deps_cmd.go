package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"

	"github.com/SET-Apps/ai-submodule/src/internal/home"
	"github.com/spf13/cobra"
)

var (
	depsPython string
	depsForce  bool
)

var depsCmd = &cobra.Command{
	Use:   "deps",
	Short: "Manage runtime dependencies for the governance engine",
	Long: `Manage the Python virtual environment used to bridge to the governance
policy engine. The engine is written in Python; deps setup creates and
manages the venv automatically.`,
}

var depsSetupCmd = &cobra.Command{
	Use:   "setup",
	Short: "Create or update the Python virtual environment",
	Long: `Create a Python virtual environment for the governance policy engine bridge.

The venv is created at ~/.ai/venv/ (or DARK_GOVERNANCE_HOME/venv/) and
installs the minimum dependencies needed for the engine bridge (pyyaml).

Examples:
  dark-governance deps setup                        # Auto-detect Python
  dark-governance deps setup --python python3.11    # Use specific Python
  dark-governance deps setup --force                # Recreate even if exists`,
	RunE: runDepsSetup,
}

var depsStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show Python virtual environment status",
	Long:  `Display the current state of the Python virtual environment used by the governance engine.`,
	RunE:  runDepsStatus,
}

func init() {
	depsSetupCmd.Flags().StringVar(&depsPython, "python", "", "Path to Python interpreter (default: auto-detect)")
	depsSetupCmd.Flags().BoolVar(&depsForce, "force", false, "Recreate venv even if it already exists")

	depsCmd.AddCommand(depsSetupCmd)
	depsCmd.AddCommand(depsStatusCmd)
}

// venvDir returns the path to the venv directory.
func venvDir() (string, error) {
	homeDir, err := home.DefaultHome()
	if err != nil {
		return "", fmt.Errorf("failed to determine home directory: %w", err)
	}
	return filepath.Join(homeDir, "venv"), nil
}

// detectPython finds a suitable Python interpreter.
func detectPython() string {
	// Try common names in order of preference
	candidates := []string{"python3", "python"}
	if runtime.GOOS == "windows" {
		candidates = []string{"python", "python3", "py"}
	}

	for _, name := range candidates {
		path, err := exec.LookPath(name)
		if err == nil {
			// Verify it's Python 3.x
			out, cmdErr := exec.Command(path, "--version").CombinedOutput()
			if cmdErr == nil && strings.HasPrefix(string(out), "Python 3") {
				return path
			}
		}
	}
	return ""
}

// parsePythonMinor extracts the minor version number from a "Python 3.X.Y" string.
func parsePythonMinor(versionStr string) (int, error) {
	// Expected format: "Python 3.X.Y"
	trimmed := strings.TrimPrefix(versionStr, "Python 3.")
	if trimmed == versionStr {
		return 0, fmt.Errorf("not a Python 3 version string: %s", versionStr)
	}
	parts := strings.SplitN(trimmed, ".", 2)
	return strconv.Atoi(parts[0])
}

// pythonVersion returns the version string from a Python interpreter.
func pythonVersion(pythonPath string) string {
	out, err := exec.Command(pythonPath, "--version").CombinedOutput()
	if err != nil {
		return "unknown"
	}
	return strings.TrimSpace(string(out))
}

func runDepsSetup(cmd *cobra.Command, args []string) error {
	// Determine Python interpreter
	pythonPath := depsPython
	if pythonPath == "" {
		pythonPath = detectPython()
		if pythonPath == "" {
			return fmt.Errorf("no Python 3 interpreter found; install Python 3.9+ or use --python to specify the path")
		}
	}

	// Verify the Python interpreter exists and is Python 3.9+
	pyVer := pythonVersion(pythonPath)
	if !strings.HasPrefix(pyVer, "Python 3") {
		return fmt.Errorf("interpreter %q reports %q — Python 3.9+ required", pythonPath, pyVer)
	}
	// Enforce minimum minor version 3.9
	if minor, err := parsePythonMinor(pyVer); err == nil && minor < 9 {
		return fmt.Errorf("interpreter %q reports %q — Python 3.9+ required (found 3.%d)", pythonPath, pyVer, minor)
	}

	// Determine venv location
	vdir, err := venvDir()
	if err != nil {
		return err
	}

	// Check if venv already exists
	venvPython := filepath.Join(vdir, "bin", "python3")
	if runtime.GOOS == "windows" {
		venvPython = filepath.Join(vdir, "Scripts", "python.exe")
	}

	if !depsForce {
		if _, statErr := os.Stat(venvPython); statErr == nil {
			if flagJSON {
				fmt.Fprintf(os.Stdout, `{"status": "already_exists", "venv": %q, "python": %q}`+"\n", vdir, venvPython)
			} else {
				fmt.Fprintf(os.Stdout, "Python venv already exists at %s\n", vdir)
				fmt.Fprintln(os.Stdout, "Use --force to recreate.")
			}
			return nil
		}
	}

	// Remove existing venv if --force
	if depsForce {
		if err := os.RemoveAll(vdir); err != nil {
			return fmt.Errorf("failed to remove existing venv: %w", err)
		}
	}

	// Create the venv
	if !flagJSON {
		fmt.Fprintf(os.Stdout, "Creating Python venv at %s using %s (%s)...\n", vdir, pythonPath, pyVer)
	}

	createCmd := exec.Command(pythonPath, "-m", "venv", vdir)
	if flagJSON {
		// In JSON mode, suppress subprocess output to keep stdout valid JSON
		createCmd.Stdout = nil
		createCmd.Stderr = os.Stderr
	} else {
		createCmd.Stdout = os.Stdout
		createCmd.Stderr = os.Stderr
	}
	if err := createCmd.Run(); err != nil {
		return fmt.Errorf("failed to create venv: %w", err)
	}

	// Install minimum dependencies
	pipPath := filepath.Join(vdir, "bin", "pip")
	if runtime.GOOS == "windows" {
		pipPath = filepath.Join(vdir, "Scripts", "pip.exe")
	}

	if !flagJSON {
		fmt.Fprintln(os.Stdout, "Installing dependencies (pyyaml)...")
	}

	installCmd := exec.Command(pipPath, "install", "--quiet", "pyyaml")
	if flagJSON {
		// In JSON mode, suppress subprocess output to keep stdout valid JSON
		installCmd.Stdout = nil
		installCmd.Stderr = os.Stderr
	} else {
		installCmd.Stdout = os.Stdout
		installCmd.Stderr = os.Stderr
	}
	if err := installCmd.Run(); err != nil {
		return fmt.Errorf("failed to install dependencies: %w", err)
	}

	if flagJSON {
		fmt.Fprintf(os.Stdout, `{"status": "created", "venv": %q, "python": %q, "python_version": %q}`+"\n",
			vdir, venvPython, pyVer)
	} else {
		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintln(os.Stdout, "Python venv created successfully.")
		fmt.Fprintf(os.Stdout, "  Location: %s\n", vdir)
		fmt.Fprintf(os.Stdout, "  Python:   %s (%s)\n", venvPython, pyVer)
		fmt.Fprintln(os.Stdout, "  Packages: pyyaml")
	}

	return nil
}

func runDepsStatus(cmd *cobra.Command, args []string) error {
	vdir, err := venvDir()
	if err != nil {
		return err
	}

	venvPython := filepath.Join(vdir, "bin", "python3")
	if runtime.GOOS == "windows" {
		venvPython = filepath.Join(vdir, "Scripts", "python.exe")
	}

	exists := false
	pyVer := ""
	if _, statErr := os.Stat(venvPython); statErr == nil {
		exists = true
		pyVer = pythonVersion(venvPython)
	}

	if flagJSON {
		fmt.Fprintf(os.Stdout, `{"exists": %v, "venv": %q, "python": %q, "python_version": %q}`+"\n",
			exists, vdir, venvPython, pyVer)
		return nil
	}

	fmt.Fprintln(os.Stdout, "Python venv status")
	fmt.Fprintln(os.Stdout, "")
	fmt.Fprintf(os.Stdout, "  Location:  %s\n", vdir)
	fmt.Fprintf(os.Stdout, "  Exists:    %v\n", exists)

	if exists {
		fmt.Fprintf(os.Stdout, "  Python:    %s\n", venvPython)
		fmt.Fprintf(os.Stdout, "  Version:   %s\n", pyVer)
	} else {
		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintln(os.Stdout, "  No venv found. Run 'dark-governance deps setup' to create one.")
	}

	return nil
}
