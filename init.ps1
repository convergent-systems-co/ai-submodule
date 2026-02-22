#Requires -Version 5.1
<#
.SYNOPSIS
    Initializes the .ai submodule for a consuming project on Windows.

.DESCRIPTION
    PowerShell equivalent of init.sh. Creates symlinks (or copies as fallback)
    for AI tool configuration files, validates dependencies, and optionally
    creates a Python virtual environment with all required packages.

    This script is idempotent — safe to run multiple times.

.PARAMETER InstallDeps
    When specified, creates a Python virtual environment at .ai\.venv and
    installs all required packages from requirements.txt.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .ai\init.ps1
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .ai\init.ps1 -InstallDeps
#>

[CmdletBinding()]
param(
    [switch]$InstallDeps
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$VenvDir = Join-Path $ScriptDir ".venv"
$RequirementsFile = Join-Path $ScriptDir "requirements.txt"
$PythonMinMajor = 3
$PythonMinMinor = 12

# --- Dependency checks ---

function Test-PythonInstalled {
    try {
        $version = & python --version 2>&1
        if ($version -match 'Python (\d+)\.(\d+)') {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if (($major -gt $PythonMinMajor) -or (($major -eq $PythonMinMajor) -and ($minor -ge $PythonMinMinor))) {
                Write-Host "  [OK] Python $major.$minor found" -ForegroundColor Green
                return $true
            }
            Write-Host "  [WARN] Python $major.$minor found, but ${PythonMinMajor}.${PythonMinMinor}+ required" -ForegroundColor Yellow
            return $false
        }
        Write-Host "  [WARN] Could not parse Python version from: $version" -ForegroundColor Yellow
        return $false
    }
    catch {
        Write-Host "  [WARN] Python is not installed or not in PATH" -ForegroundColor Yellow
        Write-Host "         The policy engine requires Python ${PythonMinMajor}.${PythonMinMinor}+ with 'jsonschema' and 'pyyaml' packages." -ForegroundColor Yellow
        Write-Host "         Install from: https://www.python.org/downloads/" -ForegroundColor Yellow
        return $false
    }
}

function Test-PipPackages {
    param(
        [string[]]$Packages,
        [string]$PythonPath = "python"
    )

    $missing = @()
    foreach ($pkg in $Packages) {
        $null = & $PythonPath -c "import $pkg" 2>&1
        if ($LASTEXITCODE -ne 0) {
            $missing += $pkg
        }
    }

    if ($missing.Count -gt 0) {
        $installPkgs = @()
        foreach ($m in $missing) {
            switch ($m) {
                'yaml' { $installPkgs += 'pyyaml' }
                default { $installPkgs += $m }
            }
        }

        Write-Host "  [WARN] Missing Python packages (imports): $($missing -join ', ')" -ForegroundColor Yellow
        Write-Host "         Install with: pip install $($installPkgs -join ' ')" -ForegroundColor Yellow
        return $false
    }

    Write-Host "  [OK] Required Python packages installed (jsonschema, pyyaml)" -ForegroundColor Green
    return $true
}

Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Cyan
$pythonOk = Test-PythonInstalled
if ($pythonOk -and -not $InstallDeps) {
    # Prefer the virtual environment's Python interpreter if it exists,
    # to avoid false warnings when packages are installed only in the venv.
    $pythonExe = "python"
    if (Test-Path $VenvDir) {
        $venvPythonCheck = Join-Path $VenvDir "Scripts\python.exe"
        if (Test-Path $venvPythonCheck) {
            $pythonExe = $venvPythonCheck
        }
    }
    Test-PipPackages -Packages @('jsonschema', 'yaml') -PythonPath $pythonExe | Out-Null
}
Write-Host ""

# --- Symlink/copy helpers ---

$CanSymlink = $false
try {
    $testLink = Join-Path $env:TEMP "ai_symlink_test_$(Get-Random)"
    $testTarget = Join-Path $env:TEMP "ai_symlink_target_$(Get-Random)"
    Set-Content -Path $testTarget -Value "test"
    New-Item -ItemType SymbolicLink -Path $testLink -Target $testTarget -ErrorAction Stop | Out-Null
    Remove-Item $testLink -Force
    Remove-Item $testTarget -Force
    $CanSymlink = $true
}
catch {
    Write-Host "  [INFO] Symbolic links not available (requires Developer Mode or admin)." -ForegroundColor Yellow
    Write-Host "         Falling back to file copies. Files will not auto-update with submodule changes." -ForegroundColor Yellow
    Write-Host "         To enable symlinks: Settings > Developer settings > Developer Mode > On" -ForegroundColor Yellow
    Write-Host ""
}

function New-LinkOrCopy {
    param(
        [string]$LinkPath,
        [string]$TargetRelative,
        [string]$TargetAbsolute
    )

    $linkName = [System.IO.Path]::GetFileName($LinkPath)
    $parentDir = Split-Path -Parent $LinkPath

    if (Test-Path $LinkPath) {
        $item = Get-Item $LinkPath -Force
        if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            $currentTarget = $item | Select-Object -ExpandProperty Target -ErrorAction SilentlyContinue
            if ($null -ne $currentTarget -and $currentTarget -eq $TargetRelative) {
                Write-Host "  $linkName already linked" -ForegroundColor DarkGray
                return
            }
            Write-Host "  Updating $linkName link target (was '$currentTarget', expected '$TargetRelative')" -ForegroundColor Yellow
            Remove-Item $LinkPath -Force
        }
        else {
            if (-not $CanSymlink) {
                Write-Host "  $linkName already exists (copy)" -ForegroundColor DarkGray
                return
            }
            Remove-Item $LinkPath -Force
        }
    }

    if ($CanSymlink) {
        New-Item -ItemType SymbolicLink -Path $LinkPath -Target $TargetRelative -Force | Out-Null
        Write-Host "  Linked $linkName -> $TargetRelative" -ForegroundColor Green
    }
    else {
        if (-not (Test-Path $parentDir)) {
            New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
        }
        Copy-Item -Path $TargetAbsolute -Destination $LinkPath -Force
        Write-Host "  Copied $linkName <- $TargetRelative" -ForegroundColor Green
    }
}

# --- Create symlinks/copies ---

Write-Host "Initializing .ai submodule configuration..." -ForegroundColor Cyan

$InstructionsSource = Join-Path $ScriptDir "instructions.md"

# instructions.md -> CLAUDE.md, .cursorrules
foreach ($target in @("CLAUDE.md", ".cursorrules")) {
    New-LinkOrCopy `
        -LinkPath (Join-Path $ProjectRoot $target) `
        -TargetRelative ".ai\instructions.md" `
        -TargetAbsolute $InstructionsSource
}

# GitHub Copilot instructions
$githubDir = Join-Path $ProjectRoot ".github"
if (-not (Test-Path $githubDir)) {
    New-Item -ItemType Directory -Path $githubDir -Force | Out-Null
}
New-LinkOrCopy `
    -LinkPath (Join-Path $githubDir "copilot-instructions.md") `
    -TargetRelative "..\.ai\instructions.md" `
    -TargetAbsolute $InstructionsSource

# --- Issue templates ---

$IsSubmodule = $false
$gitmodulesPath = Join-Path $ProjectRoot ".gitmodules"
if (Test-Path $gitmodulesPath) {
    $content = Get-Content $gitmodulesPath -Raw
    if ($content -match '\.ai') {
        $IsSubmodule = $true
    }
}

if ($IsSubmodule) {
    $templateSrc = Join-Path $ScriptDir ".github\ISSUE_TEMPLATE"
    $templateDst = Join-Path $ProjectRoot ".github\ISSUE_TEMPLATE"

    if (Test-Path $templateSrc) {
        if (-not (Test-Path $templateDst)) {
            New-Item -ItemType Directory -Path $templateDst -Force | Out-Null
        }

        Get-ChildItem -Path $templateSrc -Filter "*.yml" | ForEach-Object {
            $dstFile = Join-Path $templateDst $_.Name
            if (-not (Test-Path $dstFile)) {
                Copy-Item -Path $_.FullName -Destination $dstFile
                Write-Host "  Copied issue template $($_.Name)" -ForegroundColor Green
            }
            else {
                Write-Host "  Issue template $($_.Name) already exists, skipping" -ForegroundColor DarkGray
            }
        }
    }
}
else {
    Write-Host "  Skipping issue template copy (not a submodule context)" -ForegroundColor DarkGray
}

Write-Host ""

# --- Dependency installation ---

if ($InstallDeps) {
    Write-Host "Installing dependencies..." -ForegroundColor Cyan

    if (-not $pythonOk) {
        Write-Host "  [ERROR] Cannot install dependencies: Python ${PythonMinMajor}.${PythonMinMinor}+ is required but not found." -ForegroundColor Red
        Write-Host "          Install Python from https://www.python.org/downloads/ and re-run with -InstallDeps." -ForegroundColor Red
        exit 1
    }

    # Create virtual environment
    if (-not (Test-Path $VenvDir)) {
        Write-Host "  Creating virtual environment at .ai\.venv ..." -ForegroundColor Cyan
        & python -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [ERROR] Failed to create virtual environment (exit code $LASTEXITCODE)." -ForegroundColor Red
            exit 1
        }
        Write-Host "  [OK] Virtual environment created" -ForegroundColor Green
    }
    else {
        Write-Host "  [OK] Virtual environment already exists at .ai\.venv" -ForegroundColor Green
    }

    # Install requirements
    $venvPip = Join-Path $VenvDir "Scripts\pip.exe"
    $venvPython = Join-Path $VenvDir "Scripts\python.exe"

    if (-not (Test-Path $RequirementsFile)) {
        Write-Host "  [ERROR] requirements.txt not found at $RequirementsFile" -ForegroundColor Red
        Write-Host "          Cannot install dependencies without a requirements file." -ForegroundColor Red
        exit 1
    }

    Write-Host "  Installing packages from requirements.txt ..." -ForegroundColor Cyan
    & $venvPip install --quiet --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [ERROR] Failed to upgrade pip (exit code $LASTEXITCODE)." -ForegroundColor Red
        exit 1
    }
    & $venvPip install --quiet -r $RequirementsFile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [ERROR] Failed to install requirements (exit code $LASTEXITCODE)." -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] Packages installed" -ForegroundColor Green

    # Verify installation
    Write-Host ""
    Write-Host "Verifying installation..." -ForegroundColor Cyan
    $verifyResult = & $venvPython -c "import jsonschema; import yaml; print('[OK] jsonschema and pyyaml verified')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  $verifyResult" -ForegroundColor Green
    }
    else {
        Write-Host "  [ERROR] Package verification failed. Check the install output above." -ForegroundColor Red
        exit 1
    }
}
else {
    if ($pythonOk -and (Test-Path $VenvDir)) {
        Write-Host "  [OK] Virtual environment exists at .ai\.venv" -ForegroundColor Green
    }
    elseif ($pythonOk) {
        Write-Host "  [INFO] No virtual environment found. Run with -InstallDeps to create one." -ForegroundColor Yellow
    }
}

# --- Done ---

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
if (-not $InstallDeps -and -not (Test-Path $VenvDir)) {
    Write-Host "  0. Install dependencies:     powershell -File .ai\init.ps1 -InstallDeps"
}
Write-Host "  1. Copy a language template:  Copy-Item .ai\templates\python\project.yaml .ai\project.yaml"
Write-Host "  2. Customize personas and conventions in project.yaml"
Write-Host "  3. Set governance profile:    governance.policy_profile: default"

if (Test-Path $VenvDir) {
    Write-Host ""
    Write-Host "To activate the virtual environment:" -ForegroundColor Cyan
    Write-Host "  .ai\.venv\Scripts\Activate.ps1"
}

if (-not $pythonOk -and -not $InstallDeps) {
    Write-Host ""
    Write-Host "WARNING: Python ${PythonMinMajor}.${PythonMinMinor}+ is required for the governance policy engine." -ForegroundColor Red
    Write-Host "Install Python from https://www.python.org/downloads/ and ensure it is in your PATH." -ForegroundColor Red
    Write-Host "Then run: powershell -File .ai\init.ps1 -InstallDeps" -ForegroundColor Red
}
