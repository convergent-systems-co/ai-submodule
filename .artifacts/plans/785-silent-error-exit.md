# Plan: Fix silent error exit in dark-governance CLI (#785)

## Problem

`dark-governance init` (and potentially all commands) silently exit with code 1 when an error occurs. No error message is printed because:
1. `SilenceErrors = true` in root.go suppresses cobra's error printing
2. `main.go` catches the error but never prints it before `os.Exit(1)`
3. `make build` doesn't depend on `prepare-embed`, so `make clean build` produces a binary with no content

## Changes

### 1. `src/cmd/dark-governance/main.go`
- Print error to stderr before `os.Exit(1)`

### 2. `src/Makefile`
- Make `build` depend on `prepare-embed`

### 3. Tests
- Add test for error output behavior

## Acceptance Criteria
- `dark-governance init` (without content) prints error message to stderr
- `make build` automatically runs `prepare-embed`
- Exit code remains 1 on error
