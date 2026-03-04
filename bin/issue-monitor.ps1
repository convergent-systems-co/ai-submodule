#Requires -Version 5.1
<#
.SYNOPSIS
    Background issue monitor for Windows.

.DESCRIPTION
    Polls GitHub for actionable issues and dispatches them to Claude or Copilot.
    This script is the Windows equivalent of issue-monitor.sh.

    Security note: Only run on repositories where issue authors are trusted
    (org-internal or with restricted issue creation). Untrusted issue content
    could be used for prompt injection.

    This script is idempotent — safe to run multiple times.

.PARAMETER Backend
    AI backend to use: "claude" or "copilot" (default: claude)

.PARAMETER Interval
    Poll interval in seconds (default: 300)

.PARAMETER Model
    Claude model to use (default: claude-opus-4-6)

.PARAMETER DryRun
    Log actions without actually dispatching

.PARAMETER Repo
    Repository in owner/repo format (auto-detected from git remote)

.EXAMPLE
    powershell -File .ai\scripts\issue-monitor.ps1
.EXAMPLE
    powershell -File .ai\scripts\issue-monitor.ps1 -Backend copilot -DryRun
.EXAMPLE
    powershell -File .ai\scripts\issue-monitor.ps1 -Interval 120 -Model claude-opus-4-6
#>

[CmdletBinding()]
param(
    [ValidateSet("claude", "copilot")]
    [string]$Backend = "claude",

    [int]$Interval = 300,

    [string]$Model = "claude-opus-4-6",

    [switch]$DryRun,

    [string]$Repo = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AiDir = Split-Path -Parent $ScriptDir
$StateFile = Join-Path $ScriptDir ".issue-monitor-state"
$LogFile = if ($env:AI_MONITOR_LOG) { $env:AI_MONITOR_LOG } else { Join-Path $ScriptDir "issue-monitor.log" }

# Apply environment variable overrides
if ($env:AI_MONITOR_INTERVAL) { $Interval = [int]$env:AI_MONITOR_INTERVAL }
if ($env:AI_MONITOR_BACKEND) { $Backend = $env:AI_MONITOR_BACKEND }
if ($env:AI_MONITOR_MODEL) { $Model = $env:AI_MONITOR_MODEL }
if ($env:AI_MONITOR_DRY_RUN -eq "true") { $DryRun = $true }
if ($env:AI_MONITOR_REPO -and -not $Repo) { $Repo = $env:AI_MONITOR_REPO }

# --- Detect repository ---

function Get-RepoName {
    if ($Repo) { return $Repo }

    $remoteUrl = & git remote get-url upstream 2>$null
    if (-not $remoteUrl) {
        $remoteUrl = & git remote get-url origin 2>$null
    }
    if (-not $remoteUrl) { return "" }

    # Extract owner/repo from SSH or HTTPS URLs
    $remoteUrl -replace '.*github\.com[:/]', '' -replace '\.git$', ''
}

$NetworkId = $env:USERNAME
$RepoName = Get-RepoName
if (-not $RepoName) {
    Write-Error "Could not detect repository. Set -Repo owner/repo or AI_MONITOR_REPO env var."
    exit 1
}

# --- Logging ---

function Write-Log {
    param([string]$Message)
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $line = "[$ts] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

# --- State management (line-per-issue for robustness) ---

function Initialize-State {
    if (-not (Test-Path $StateFile)) {
        New-Item -Path $StateFile -ItemType File -Force | Out-Null
    }
}

function Test-IssueSeen {
    param([string]$IssueNumber)
    if (-not (Test-Path $StateFile)) { return $false }
    $content = Get-Content -Path $StateFile -ErrorAction SilentlyContinue
    if (-not $content) { return $false }
    return $content -contains $IssueNumber
}

function Set-IssueSeen {
    param([string]$IssueNumber)
    Add-Content -Path $StateFile -Value $IssueNumber
}

# --- Issue filtering ---

function Test-IssueActionable {
    param(
        [object]$Issue,
        [string]$IssueNumber
    )

    # Check exclusion labels
    $excludeLabels = @("blocked", "wontfix", "duplicate", "refine")
    if ($Issue.labels) {
        foreach ($label in $Issue.labels) {
            if ($excludeLabels -contains $label.name) {
                return $false
            }
        }
    }

    # Check if assigned to a human (bot assignees are OK per startup.md)
    if ($Issue.assignees -and $Issue.assignees.Count -gt 0) {
        $humanAssignees = @($Issue.assignees | Where-Object { $_.type -ne "Bot" -and $_.type -ne "bot" })
        if ($humanAssignees.Count -gt 0) {
            return $false
        }
    }

    # Check if updated by a human in the last 24 hours (per startup.md)
    if ($Issue.updatedAt) {
        try {
            $updatedAt = [DateTime]::Parse($Issue.updatedAt).ToUniversalTime()
            $now = [DateTime]::UtcNow
            $ageHours = ($now - $updatedAt).TotalHours
            if ($ageHours -lt 24) {
                return $false
            }
        }
        catch {
            # If we can't parse the date, skip the check
        }
    }

    # Check if branch exists
    $branches = & gh api "repos/$RepoName/branches" --jq '.[].name' 2>$null
    if ($branches) {
        foreach ($branch in $branches) {
            if ($branch -match "($NetworkId|feature)/[^/]+/$IssueNumber/") {
                return $false
            }
        }
    }

    return $true
}

# --- Dispatch ---

function Invoke-Claude {
    param(
        [string]$IssueNumber,
        [string]$IssueTitle
    )

    Write-Log "Dispatching issue #$IssueNumber to Claude ($Model)..."

    if ($DryRun) {
        Write-Log "[DRY RUN] Would invoke Claude Code for issue #${IssueNumber}: $IssueTitle"
        return
    }

    # Check if claude CLI is available
    $claudePath = Get-Command claude -ErrorAction SilentlyContinue
    if (-not $claudePath) {
        Write-Log "ERROR: Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
        return
    }

    # Write prompt to a temp file to avoid quoting issues
    $promptFile = [System.IO.Path]::GetTempFileName()
    @"
You are the Team Lead persona from the Dark Factory governance platform.
Read governance/prompts/startup.md for the full agentic loop specification.

An issue needs processing:
- Issue #${IssueNumber}: $IssueTitle
- Repository: $RepoName

Enter the Startup Sequence at Step 4 (Validate Intent) for issue #${IssueNumber}.
Follow all governance steps through Step 7 (PR Monitoring & Review Loop).
"@ | Set-Content -Path $promptFile -Encoding UTF8

    $prompt = Get-Content -Path $promptFile -Raw
    Remove-Item -Path $promptFile -Force

    # Start Claude in a background job
    Start-Job -ScriptBlock {
        param($ClaudePath, $Model, $Prompt, $LogFile)
        & $ClaudePath --model $Model --print --prompt $Prompt *>> $LogFile
    } -ArgumentList $claudePath.Source, $Model, $prompt, $LogFile | Out-Null

    Write-Log "Claude Code launched in background job"
}

function Invoke-Copilot {
    param(
        [string]$IssueNumber,
        [string]$IssueTitle
    )

    Write-Log "Dispatching issue #$IssueNumber to Copilot coding agent..."

    if ($DryRun) {
        Write-Log "[DRY RUN] Would assign issue #$IssueNumber to Copilot"
        return
    }

    $result = & gh api "repos/$RepoName/issues/$IssueNumber/assignees" --method POST -f "assignees[]=copilot" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Issue #$IssueNumber assigned to Copilot coding agent"
    }
    else {
        Write-Log "WARNING: Failed to assign issue #$IssueNumber to Copilot. Agent may not be enabled."
    }
}

function Invoke-Dispatch {
    param(
        [string]$IssueNumber,
        [string]$IssueTitle
    )

    switch ($Backend) {
        "claude" { Invoke-Claude -IssueNumber $IssueNumber -IssueTitle $IssueTitle }
        "copilot" { Invoke-Copilot -IssueNumber $IssueNumber -IssueTitle $IssueTitle }
        default { Write-Log "ERROR: Unknown backend '$Backend'. Use 'claude' or 'copilot'." }
    }
}

# --- Main loop ---

function Start-Monitor {
    Initialize-State
    Write-Log "Issue monitor started (repo=$RepoName, backend=$Backend, interval=${Interval}s, dry_run=$DryRun)"
    Write-Log "Log file: $LogFile"
    Write-Log "State file: $StateFile"

    while ($true) {
        Write-Log "Polling for open issues..."

        try {
            $issuesJson = & gh issue list --repo $RepoName --state open --json number,title,labels,assignees,updatedAt --limit 50 2>$null
            if (-not $issuesJson) { $issuesJson = "[]" }
            $issues = @($issuesJson | ConvertFrom-Json)
        }
        catch {
            Write-Log "ERROR: Failed to fetch issues: $_"
            $issues = @()
        }

        Write-Log "Found $($issues.Count) open issues"

        foreach ($issue in $issues) {
            $number = [string]$issue.number
            $title = $issue.title

            # Skip if already seen
            if (Test-IssueSeen -IssueNumber $number) {
                continue
            }

            # Check actionability
            if (Test-IssueActionable -Issue $issue -IssueNumber $number) {
                Write-Log "Actionable issue found: #$number - $title"
                Invoke-Dispatch -IssueNumber $number -IssueTitle $title
                Set-IssueSeen -IssueNumber $number
            }
            else {
                Write-Log "Skipping issue #$number (not actionable)"
                Set-IssueSeen -IssueNumber $number
            }
        }

        Write-Log "Next poll in ${Interval}s..."
        Start-Sleep -Seconds $Interval
    }
}

# --- Entry point ---

try {
    Start-Monitor
}
catch {
    if ($_.Exception.GetType().Name -eq "PipelineStoppedException") {
        Write-Log "Issue monitor stopped by user."
    }
    else {
        Write-Log "ERROR: $($_.Exception.Message)"
        throw
    }
}
finally {
    Write-Log "Issue monitor shut down."
}
