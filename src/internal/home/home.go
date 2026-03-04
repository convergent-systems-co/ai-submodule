// Package home manages the governance home directory (~/.ai/).
//
// The home directory stores versioned governance content, the Python venv,
// and other cached data. Multiple repositories share the same home cache.
package home

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
)

// DefaultHome returns the default home directory path.
//
// Resolution order:
//  1. DARK_GOVERNANCE_HOME environment variable
//  2. XDG_DATA_HOME/dark-governance (if XDG_DATA_HOME is set)
//  3. ~/.ai
func DefaultHome() (string, error) {
	if envHome := os.Getenv("DARK_GOVERNANCE_HOME"); envHome != "" {
		return envHome, nil
	}

	if xdg := os.Getenv("XDG_DATA_HOME"); xdg != "" {
		return filepath.Join(xdg, "dark-governance"), nil
	}

	userHome, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("failed to determine user home directory: %w", err)
	}
	return filepath.Join(userHome, ".ai"), nil
}

// HomeForInstall returns the home directory for installation.
// When ci is true, uses CI-appropriate paths.
func HomeForInstall(ci bool) (string, error) {
	if ci {
		if runnerTemp := os.Getenv("RUNNER_TEMP"); runnerTemp != "" {
			return filepath.Join(runnerTemp, ".ai"), nil
		}
	}
	return DefaultHome()
}

// VersionDir returns the path for a specific version within the home dir.
func VersionDir(homeDir, version string) string {
	return filepath.Join(homeDir, "versions", version)
}

// IsInstalled checks whether a specific version is installed.
func IsInstalled(homeDir, version string) bool {
	vdir := VersionDir(homeDir, version)
	info, err := os.Stat(vdir)
	return err == nil && info.IsDir()
}

// CleanVersion removes an installed version directory.
func CleanVersion(homeDir, version string) error {
	vdir := VersionDir(homeDir, version)
	return os.RemoveAll(vdir)
}

// Install extracts governance content from an fs.FS to the version directory.
// Returns the number of files extracted.
func Install(homeDir, version, contentHash string, content fs.FS) (int, error) {
	vdir := VersionDir(homeDir, version)
	if err := os.MkdirAll(vdir, 0755); err != nil {
		return 0, fmt.Errorf("failed to create version directory: %w", err)
	}

	count := 0
	err := fs.WalkDir(content, ".", func(path string, d fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if path == "." {
			return nil
		}

		// Ensure the walked path is a valid fs path and does not escape vdir.
		if !fs.ValidPath(path) {
			return fmt.Errorf("invalid path in content FS: %q", path)
		}

		dst := filepath.Join(vdir, path)
		dst = filepath.Clean(dst)

		// Ensure the cleaned destination remains within the version directory.
		if !strings.HasPrefix(dst, vdir+string(os.PathSeparator)) && dst != vdir {
			return fmt.Errorf("refusing to write outside version dir for path %q", path)
		}

		if d.IsDir() {
			return os.MkdirAll(dst, 0755)
		}

		data, readErr := fs.ReadFile(content, path)
		if readErr != nil {
			return fmt.Errorf("failed to read embedded %s: %w", path, readErr)
		}

		if mkErr := os.MkdirAll(filepath.Dir(dst), 0755); mkErr != nil {
			return fmt.Errorf("failed to create dir for %s: %w", path, mkErr)
		}

		if wErr := os.WriteFile(dst, data, 0644); wErr != nil {
			return fmt.Errorf("failed to write %s: %w", path, wErr)
		}

		count++
		return nil
	})

	if err != nil {
		return count, err
	}

	// Write a .content-hash marker file for integrity checks
	hashPath := filepath.Join(vdir, ".content-hash")
	if wErr := os.WriteFile(hashPath, []byte(contentHash+"\n"), 0644); wErr != nil {
		return count, fmt.Errorf("failed to write content hash: %w", wErr)
	}

	return count, nil
}

// ListVersions returns installed versions sorted by name (descending).
func ListVersions(homeDir string) ([]string, error) {
	versionsDir := filepath.Join(homeDir, "versions")
	entries, err := os.ReadDir(versionsDir)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}

	var versions []string
	for _, e := range entries {
		if e.IsDir() && !strings.HasPrefix(e.Name(), ".") {
			versions = append(versions, e.Name())
		}
	}

	sort.Sort(sort.Reverse(sort.StringSlice(versions)))
	return versions, nil
}

// VenvDir returns the path to the Python venv directory.
func VenvDir(homeDir string) string {
	return filepath.Join(homeDir, "venv")
}

// VenvPython returns the path to the Python interpreter inside the venv.
func VenvPython(homeDir string) string {
	if runtime.GOOS == "windows" {
		return filepath.Join(VenvDir(homeDir), "Scripts", "python.exe")
	}
	return filepath.Join(VenvDir(homeDir), "bin", "python3")
}
