# install.ps1 — Configure IDE MCP server entries for ai-submodule-mcp (Windows)
# Supports: Claude Code, VS Code, Cursor
# Usage: powershell -ExecutionPolicy Bypass -File install.ps1 [-GovernanceRoot <path>]

param(
    [string]$GovernanceRoot = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerScript = Join-Path $ScriptDir "dist\index.js"

if (-not (Test-Path $ServerScript)) {
    Write-Error "Error: dist\index.js not found. Run 'npm run build' first."
    exit 1
}

# Build args array
$McpArgs = @($ServerScript)
if ($GovernanceRoot -ne "") {
    $McpArgs += "--governance-root"
    $McpArgs += $GovernanceRoot
}

$NodeCmd = "node"
try {
    $NodeCmd = (Get-Command node -ErrorAction Stop).Source
} catch {
    Write-Warning "node not found in PATH, using 'node' directly"
}

Write-Host "=== ai-submodule-mcp installer ===" -ForegroundColor Cyan
Write-Host "Server: $ServerScript"
Write-Host ""

function Set-JsonConfig {
    param(
        [string]$FilePath,
        [string]$ServerKey,
        [string]$NodePath,
        [string[]]$Args
    )

    if (-not (Test-Path $FilePath)) {
        Set-Content -Path $FilePath -Value "{}"
    }

    $config = Get-Content -Path $FilePath -Raw | ConvertFrom-Json

    # Ensure the server key path exists
    $serverEntry = @{
        command = $NodePath
        args = $Args
    }

    return @{
        Config = $config
        Entry = $serverEntry
    }
}

# --- Claude Code ---
function Configure-ClaudeCode {
    $configFile = Join-Path $env:USERPROFILE ".claude.json"

    if (-not (Test-Path $configFile)) {
        Set-Content -Path $configFile -Value "{}"
    }

    $config = Get-Content -Path $configFile -Raw | ConvertFrom-Json

    if (-not (Get-Member -InputObject $config -Name "mcpServers" -MemberType NoteProperty)) {
        $config | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue ([PSCustomObject]@{})
    }

    $serverConfig = [PSCustomObject]@{
        command = $NodeCmd
        args = $McpArgs
    }

    if (Get-Member -InputObject $config.mcpServers -Name "ai-submodule-mcp" -MemberType NoteProperty) {
        $config.mcpServers."ai-submodule-mcp" = $serverConfig
    } else {
        $config.mcpServers | Add-Member -NotePropertyName "ai-submodule-mcp" -NotePropertyValue $serverConfig
    }

    $config | ConvertTo-Json -Depth 10 | Set-Content -Path $configFile
    Write-Host "[OK] Claude Code: $configFile" -ForegroundColor Green
}

# --- VS Code ---
function Configure-VSCode {
    $settingsDir = Join-Path $env:APPDATA "Code\User"
    $settingsFile = Join-Path $settingsDir "settings.json"

    if (-not (Test-Path $settingsDir)) {
        Write-Host "[SKIP] VS Code: settings directory not found at $settingsDir" -ForegroundColor Yellow
        return
    }

    if (-not (Test-Path $settingsFile)) {
        Set-Content -Path $settingsFile -Value "{}"
    }

    $config = Get-Content -Path $settingsFile -Raw | ConvertFrom-Json

    if (-not (Get-Member -InputObject $config -Name "mcp.servers" -MemberType NoteProperty)) {
        $config | Add-Member -NotePropertyName "mcp.servers" -NotePropertyValue ([PSCustomObject]@{})
    }

    $serverConfig = [PSCustomObject]@{
        command = $NodeCmd
        args = $McpArgs
    }

    $servers = $config."mcp.servers"
    if (Get-Member -InputObject $servers -Name "ai-submodule-mcp" -MemberType NoteProperty) {
        $servers."ai-submodule-mcp" = $serverConfig
    } else {
        $servers | Add-Member -NotePropertyName "ai-submodule-mcp" -NotePropertyValue $serverConfig
    }

    $config | ConvertTo-Json -Depth 10 | Set-Content -Path $settingsFile
    Write-Host "[OK] VS Code: $settingsFile" -ForegroundColor Green
}

# --- Cursor ---
function Configure-Cursor {
    $configDir = Join-Path $env:USERPROFILE ".cursor"
    $configFile = Join-Path $configDir "mcp.json"

    if (-not (Test-Path $configDir)) {
        Write-Host "[SKIP] Cursor: ~/.cursor directory not found" -ForegroundColor Yellow
        return
    }

    if (-not (Test-Path $configFile)) {
        Set-Content -Path $configFile -Value "{}"
    }

    $config = Get-Content -Path $configFile -Raw | ConvertFrom-Json

    if (-not (Get-Member -InputObject $config -Name "mcpServers" -MemberType NoteProperty)) {
        $config | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue ([PSCustomObject]@{})
    }

    $serverConfig = [PSCustomObject]@{
        command = $NodeCmd
        args = $McpArgs
    }

    if (Get-Member -InputObject $config.mcpServers -Name "ai-submodule-mcp" -MemberType NoteProperty) {
        $config.mcpServers."ai-submodule-mcp" = $serverConfig
    } else {
        $config.mcpServers | Add-Member -NotePropertyName "ai-submodule-mcp" -NotePropertyValue $serverConfig
    }

    $config | ConvertTo-Json -Depth 10 | Set-Content -Path $configFile
    Write-Host "[OK] Cursor: $configFile" -ForegroundColor Green
}

Configure-ClaudeCode
Configure-VSCode
Configure-Cursor

Write-Host ""
Write-Host "Done. Restart your IDE to pick up the new MCP server configuration." -ForegroundColor Cyan
