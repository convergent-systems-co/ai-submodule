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
    installs all required packages from .ai\governance\bin\requirements.txt.

.PARAMETER Refresh
    Re-apply structural setup (symlinks, workflows, directories, CODEOWNERS,
    repo settings) without checking submodule freshness or converting SSH URLs.
    Used by the agentic startup loop after submodule updates.

.PARAMETER CheckBranchProtection
    Query if the default branch requires PRs. Outputs REQUIRES_PR=true or
    REQUIRES_PR=false and exits. Used by the agentic startup loop.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .ai\bin\init.ps1
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .ai\bin\init.ps1 -InstallDeps
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .ai\bin\init.ps1 -Refresh
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .ai\bin\init.ps1 -CheckBranchProtection
#>

[CmdletBinding()]
param(
    [switch]$InstallDeps,
    [switch]$Refresh,
    [switch]$CheckBranchProtection
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path  # .ai/bin/
$AiDir = Split-Path -Parent $ScriptDir                        # .ai/
$ProjectRoot = Split-Path -Parent $AiDir                      # project root
$VenvDir = Join-Path $AiDir ".venv"
$RequirementsFile = Join-Path (Join-Path (Join-Path $AiDir "governance") "bin") "requirements.txt"
$PythonMinMajor = 3
$PythonMinMinor = 12

# --- Check branch protection (early exit) ---

if ($CheckBranchProtection) {
    # Check for gh CLI
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        Write-Output "REQUIRES_PR=false"
        exit 0
    }

    try {
        $repo = (gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>$null)
        if (-not $repo) { Write-Output "REQUIRES_PR=false"; exit 0 }

        $defaultBranch = (gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>$null)
        if (-not $defaultBranch) { $defaultBranch = "main" }

        # Try rulesets API
        $rulesJson = (gh api "repos/$repo/rules/branches/$defaultBranch" 2>$null)
        if ($rulesJson) {
            $rules = $rulesJson | ConvertFrom-Json
            $prRules = $rules | Where-Object { $_.type -eq "pull_request" }
            if ($prRules) {
                Write-Output "REQUIRES_PR=true"
                exit 0
            }
        }

        # Fallback: legacy branch protection
        $protectionJson = (gh api "repos/$repo/branches/$defaultBranch/protection" 2>$null)
        if ($protectionJson) {
            $protection = $protectionJson | ConvertFrom-Json
            if ($protection.required_pull_request_reviews) {
                Write-Output "REQUIRES_PR=true"
                exit 0
            }
        }
    }
    catch {
        # API failure — default to no protection
    }

    Write-Output "REQUIRES_PR=false"
    exit 0
}

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

function ConvertTo-Hashtable {
    param(
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [AllowNull()]
        $InputObject
    )

    if ($null -eq $InputObject) {
        return $null
    }

    if ($InputObject -is [System.Collections.IDictionary]) {
        $result = @{}
        foreach ($key in $InputObject.Keys) {
            $result[$key] = ConvertTo-Hashtable -InputObject $InputObject[$key]
        }
        return $result
    }

    if ($InputObject -is [pscustomobject]) {
        $result = @{}
        foreach ($prop in $InputObject.PSObject.Properties) {
            $result[$prop.Name] = ConvertTo-Hashtable -InputObject $prop.Value
        }
        return $result
    }

    if ($InputObject -is [System.Collections.IEnumerable] -and -not ($InputObject -is [string])) {
        $list = @()
        foreach ($item in $InputObject) {
            $list += , (ConvertTo-Hashtable -InputObject $item)
        }
        return $list
    }

    return $InputObject
}

function Get-ConfigData {
    if (Test-Path variable:script:AiMergedConfigCache) {
        return $script:AiMergedConfigCache
    }

    $config = @{}

    if (-not $pythonOk) {
        Write-Host "  [INFO] Python is not available; skipping config.yaml/project.yaml parsing and using defaults." -ForegroundColor Yellow
        return $config
    }

    $configScript = @"
import json
import os
import yaml

def deep_merge(base, override):
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            result[key] = result[key] + value
        else:
            result[key] = value
    return result

script_dir = os.environ.get('AI_SCRIPT_DIR')
project_root = os.environ.get('AI_PROJECT_ROOT')
files = [
    os.path.join(script_dir, 'config.yaml'),
    os.path.join(script_dir, 'project.yaml'),
    os.path.join(project_root, 'project.yaml')
]

merged = {}
for file_path in files:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
            merged = deep_merge(merged, data)

print(json.dumps(merged))
"@

    try {
        $env:AI_SCRIPT_DIR = $AiDir
        $env:AI_PROJECT_ROOT = $ProjectRoot
        $configJson = & python -c $configScript
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($configJson)) {
            $script:AiMergedConfigCache = $config
            return $script:AiMergedConfigCache
        }
        $configObject = $configJson | ConvertFrom-Json
        $config = ConvertTo-Hashtable -InputObject $configObject
        $script:AiMergedConfigCache = $config
    }
    catch {
        Write-Host "  [WARN] Failed to load configuration: $($_.Exception.Message)" -ForegroundColor Yellow
        $script:AiMergedConfigCache = @{}
        return $script:AiMergedConfigCache
    }
    finally {
        Remove-Item Env:AI_SCRIPT_DIR -ErrorAction SilentlyContinue
        Remove-Item Env:AI_PROJECT_ROOT -ErrorAction SilentlyContinue
    }

    return $script:AiMergedConfigCache
}

# --- Create symlinks/copies ---

Write-Host "Initializing .ai submodule configuration..." -ForegroundColor Cyan

$InstructionsSource = Join-Path $AiDir "instructions.md"

# instructions.md -> CLAUDE.md
foreach ($target in @("CLAUDE.md")) {
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
    $templateSrc = Join-Path $AiDir ".github\ISSUE_TEMPLATE"
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

    # Governance workflows
    $workflowSrc = Join-Path $AiDir ".github\workflows"
    $workflowDst = Join-Path $ProjectRoot ".github\workflows"
    if (Test-Path $workflowSrc) {
        if (-not (Test-Path $workflowDst)) {
            New-Item -ItemType Directory -Path $workflowDst -Force | Out-Null
        }

        $config = Get-ConfigData
        $requiredWorkflows = @('dark-factory-governance.yml')
        $optionalWorkflows = @()
        $requiredWorkflowsOverridden = $false

        if ($config -and $config.ContainsKey('workflows') -and $config.workflows -is [hashtable]) {
            if ($config.workflows.ContainsKey('required') -and $config.workflows.required) {
                $requiredWorkflows = @($config.workflows.required)
                $requiredWorkflowsOverridden = $true
            }
            if ($config.workflows.ContainsKey('optional') -and $config.workflows.optional) {
                $optionalWorkflows = @($config.workflows.optional)
            }
        }

        # Legacy fallback: support workflows_to_copy if new structure not present
        if (-not $requiredWorkflowsOverridden -and $config -and $config.ContainsKey('workflows_to_copy')) {
            $requiredWorkflows = @($config.workflows_to_copy)
        }

        foreach ($wf in $requiredWorkflows) {
            $srcFile = Join-Path $workflowSrc $wf
            $dstFile = Join-Path $workflowDst $wf
            if (Test-Path $srcFile) {
                if ($CanSymlink) {
                    $linkTarget = "..\..\.ai\.github\workflows\$wf"
                    New-LinkOrCopy -LinkPath $dstFile -TargetRelative $linkTarget -TargetAbsolute $srcFile
                }
                else {
                    if (Test-Path $dstFile -PathType Leaf) {
                        $dstItem = Get-Item -LiteralPath $dstFile -ErrorAction SilentlyContinue
                        if ($dstItem -and -not $dstItem.Attributes.HasFlag([IO.FileAttributes]::ReparsePoint)) {
                            Write-Host "  Workflow $wf exists as regular file, skipping (remove to use symlink)" -ForegroundColor Yellow
                            continue
                        }
                    }
                    Copy-Item -Path $srcFile -Destination $dstFile -Force
                    Write-Host "  Copied workflow $wf" -ForegroundColor Green
                }
            }
            else {
                Write-Host "  [WARN] Required workflow $wf not found in .ai\.github\workflows" -ForegroundColor Yellow
            }
        }

        foreach ($wf in $optionalWorkflows) {
            $srcFile = Join-Path $workflowSrc $wf
            $dstFile = Join-Path $workflowDst $wf
            if (Test-Path $srcFile) {
                if ($CanSymlink) {
                    $linkTarget = "..\..\.ai\.github\workflows\$wf"
                    New-LinkOrCopy -LinkPath $dstFile -TargetRelative $linkTarget -TargetAbsolute $srcFile
                }
                else {
                    if (Test-Path $dstFile -PathType Leaf) {
                        $dstItem = Get-Item -LiteralPath $dstFile -ErrorAction SilentlyContinue
                        if ($dstItem -and -not $dstItem.Attributes.HasFlag([IO.FileAttributes]::ReparsePoint)) {
                            Write-Host "  Workflow $wf exists as regular file, skipping (optional)" -ForegroundColor Yellow
                            continue
                        }
                    }
                    Copy-Item -Path $srcFile -Destination $dstFile -Force
                    Write-Host "  Copied workflow $wf (optional)" -ForegroundColor Green
                }
            }
        }
    }

    # Project directories
    $projectDirs = @('.governance/plans', '.governance/panels', '.governance/checkpoints', '.governance/state')
    $configForDirs = Get-ConfigData
    if ($configForDirs -and $configForDirs.ContainsKey('project_directories') -and $configForDirs.project_directories) {
        $projectDirs = @()
        foreach ($dirCfg in $configForDirs.project_directories) {
            if ($dirCfg.ContainsKey('path') -and -not [string]::IsNullOrWhiteSpace($dirCfg.path)) {
                $projectDirs += $dirCfg.path
            }
        }
        if ($projectDirs.Count -eq 0) {
            $projectDirs = @('.governance/plans', '.governance/panels', '.governance/checkpoints', '.governance/state')
        }
    }

    # Migrate old directory paths to new .governance/ structure
    $migrations = @{
        '.plans' = '.governance/plans'
        '.panels' = '.governance/panels'
        'governance/checkpoints' = '.governance/checkpoints'
        '.governance-state' = '.governance/state'
    }
    foreach ($oldDir in $migrations.Keys) {
        $oldPath = Join-Path $ProjectRoot $oldDir
        $newPath = Join-Path $ProjectRoot $migrations[$oldDir]
        if ((Test-Path $oldPath) -and -not (Test-Path $newPath)) {
            $newParent = Split-Path $newPath -Parent
            if (-not (Test-Path $newParent)) {
                New-Item -ItemType Directory -Path $newParent -Force | Out-Null
            }
            Move-Item -Path $oldPath -Destination $newPath -Force
            Write-Host "  Migrated $oldDir/ -> $($migrations[$oldDir])/" -ForegroundColor Yellow
        }
    }

    foreach ($dir in $projectDirs) {
        $dirPath = Join-Path $ProjectRoot $dir
        $createdDir = $false
        if (-not (Test-Path $dirPath)) {
            New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
            Write-Host "  Created $dir/" -ForegroundColor Green
            $createdDir = $true
        }
        # Only create .gitkeep in newly created dirs or empty existing dirs
        $gitkeep = Join-Path $dirPath '.gitkeep'
        if ($createdDir) {
            if (-not (Test-Path $gitkeep)) {
                New-Item -ItemType File -Path $gitkeep -Force | Out-Null
            }
        }
        else {
            $nonMetaItems = Get-ChildItem -Path $dirPath -Force | Where-Object { $_.Name -ne '.gitkeep' }
            if (-not $nonMetaItems -and -not (Test-Path $gitkeep)) {
                New-Item -ItemType File -Path $gitkeep -Force | Out-Null
            }
        }
    }

    # CODEOWNERS
    $codeownersPath = Join-Path $ProjectRoot 'CODEOWNERS'
    $configForOwners = Get-ConfigData

    # Respect codeowners.enabled flag (default: true)
    $codeownersEnabled = $true
    if ($configForOwners -and $configForOwners.ContainsKey('repository') -and
        $configForOwners.repository -is [hashtable] -and
        $configForOwners.repository.ContainsKey('codeowners') -and
        $configForOwners.repository.codeowners -is [hashtable] -and
        $configForOwners.repository.codeowners.ContainsKey('enabled')) {
        $codeownersEnabled = $configForOwners.repository.codeowners.enabled
    }

    if (-not $codeownersEnabled) {
        Write-Host "  [SKIP] CODEOWNERS generation disabled" -ForegroundColor DarkGray
    }
    else {
        $shouldCreateCodeowners = $true
        if (Test-Path $codeownersPath) {
            $existing = Get-Content $codeownersPath -Raw
            if (-not [string]::IsNullOrWhiteSpace($existing)) {
                $shouldCreateCodeowners = $false
            }
        }

        if ($shouldCreateCodeowners) {
            $defaultOwner = '@SET-Apps/approvers'
            $ownerRules = @(
                @{ pattern = '/.github/workflows/'; owners = @('@SET-Apps/devops_engineers') },
                @{ pattern = '/infra/'; owners = @('@SET-Apps/devops_engineers') },
                @{ pattern = '/.ai'; owners = @('@SET-Apps/approvers') }
            )

            if ($configForOwners -and $configForOwners.ContainsKey('repository') -and
                $configForOwners.repository -is [hashtable] -and
                $configForOwners.repository.ContainsKey('codeowners') -and
                $configForOwners.repository.codeowners -is [hashtable]) {

                if ($configForOwners.repository.codeowners.ContainsKey('default_owner') -and
                    -not [string]::IsNullOrWhiteSpace($configForOwners.repository.codeowners.default_owner)) {
                    $defaultOwner = $configForOwners.repository.codeowners.default_owner
                }

                if ($configForOwners.repository.codeowners.ContainsKey('rules') -and
                    $configForOwners.repository.codeowners.rules) {
                    $ownerRules = @($configForOwners.repository.codeowners.rules)
                }
            }

            $lines = @(
                '# CODEOWNERS — generated by .ai/bin/init.ps1 from config.yaml',
                '# Manual edits will be overwritten on next init run.',
                '#',
                '# NOTE: The Dark Factory governance workflow approves PRs as github-actions[bot].',
                '# Bot approvals do NOT satisfy code owner review requirements. See',
                '# .ai/docs/configuration/repository-setup.md for workarounds.',
                '',
                "* $defaultOwner",
                ''
            )
            foreach ($rule in $ownerRules) {
                if (-not $rule.ContainsKey('pattern') -or -not $rule.ContainsKey('owners')) {
                    continue
                }
                $owners = @($rule.owners) -join ' '
                $lines += "$($rule.pattern) $owners"
            }

            Set-Content -Path $codeownersPath -Value ($lines -join [Environment]::NewLine)
            Write-Host "  Generated CODEOWNERS" -ForegroundColor Green
        }
        else {
            Write-Host "  [OK] CODEOWNERS already populated" -ForegroundColor DarkGray
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
    & $venvPython -m pip install --quiet --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [ERROR] Failed to upgrade pip (exit code $LASTEXITCODE)." -ForegroundColor Red
        exit 1
    }
    & $venvPython -m pip install --quiet -r $RequirementsFile
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

# --- Migration warning: project.yaml location ---

$legacyProjectYaml = Join-Path $AiDir "project.yaml"
$rootProjectYaml = Join-Path $ProjectRoot "project.yaml"
if ((Test-Path $legacyProjectYaml) -and -not (Test-Path $rootProjectYaml)) {
    Write-Host ""
    Write-Host "  [MIGRATE] project.yaml found at .ai\project.yaml (legacy location)" -ForegroundColor Yellow
    Write-Host "            The preferred location is now the project root: .\project.yaml" -ForegroundColor Yellow
    Write-Host "            Move it with: Move-Item .ai\project.yaml project.yaml" -ForegroundColor Yellow
    Write-Host "            Both locations are read; root takes precedence." -ForegroundColor Yellow
}

# --- Done ---

Write-Host ""
if ($Refresh) {
    Write-Host "Refresh complete." -ForegroundColor Green
}
else {
    Write-Host "Done." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    if (-not $InstallDeps -and -not (Test-Path $VenvDir)) {
        Write-Host "  0. Install dependencies:     powershell -File .ai\bin\init.ps1 -InstallDeps"
    }
    Write-Host "  1. Copy a language template:  Copy-Item .ai\governance\templates\python\project.yaml project.yaml"
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
        Write-Host "Then run: powershell -File .ai\bin\init.ps1 -InstallDeps" -ForegroundColor Red
    }
}
