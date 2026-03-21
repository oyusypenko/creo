#Requires -Version 5.1
<#
.SYNOPSIS
    Installs the gsc-analyzer extension for Creo.
.DESCRIPTION
    Copies gsc_toolkit package, skill, and agent files to the Creo skills directory.
    Creates a Python virtual environment and installs dependencies.
#>

$ErrorActionPreference = "Stop"

function Main {
    $CreoDir = Join-Path $env:USERPROFILE ".claude\skills\creo"
    $ExtDir  = Join-Path $env:USERPROFILE ".claude\skills\creo-gsc"
    $AgentDir = Join-Path $env:USERPROFILE ".claude\agents"

    if (-not (Test-Path $CreoDir)) {
        Write-Host "X Creo core must be installed first." -ForegroundColor Red
        exit 1
    }

    # Check Python
    try {
        $pythonVersion = & python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if (-not $pythonVersion) {
            $pythonVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        }
    } catch {
        Write-Host "X Python 3 is required." -ForegroundColor Red
        exit 1
    }
    Write-Host "OK Python $pythonVersion detected" -ForegroundColor Green

    Write-Host "-> Installing gsc-analyzer extension..."
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

    # Create directories
    New-Item -ItemType Directory -Force -Path (Join-Path $ExtDir "gsc_toolkit") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $ExtDir "scripts") | Out-Null
    New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null

    # Copy skill
    Copy-Item (Join-Path $ScriptDir "skills\creo-gsc\SKILL.md") (Join-Path $ExtDir "SKILL.md") -Force

    # Copy agent
    Copy-Item (Join-Path $ScriptDir "agents\creo-gsc.md") (Join-Path $AgentDir "creo-gsc.md") -Force

    # Copy gsc_toolkit package
    Copy-Item (Join-Path $ScriptDir "gsc_toolkit\*") (Join-Path $ExtDir "gsc_toolkit") -Recurse -Force

    # Copy legacy script
    $scriptsSource = Join-Path $ScriptDir "scripts\*.py"
    if (Test-Path $scriptsSource) {
        Copy-Item $scriptsSource (Join-Path $ExtDir "scripts") -Force
    }

    # Copy requirements
    Copy-Item (Join-Path $ScriptDir "requirements.txt") $ExtDir -Force

    # Install Python deps
    Write-Host "-> Installing Python dependencies..."
    $VenvDir = Join-Path $ExtDir ".venv"
    try {
        & python3 -m venv $VenvDir 2>$null
        if (-not $?) { & python -m venv $VenvDir }

        $pipPath = Join-Path $VenvDir "Scripts\pip.exe"
        & $pipPath install --quiet -r (Join-Path $ScriptDir "requirements.txt") 2>$null
        Write-Host "  OK Installed in venv" -ForegroundColor Green
    } catch {
        Write-Host "  WARNING Could not auto-install. Run: pip install -r $(Join-Path $ExtDir 'requirements.txt')" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "OK GSC Analyzer extension installed!" -ForegroundColor Green
    Write-Host "  Usage: /creo gsc full-seo https://example.com"
    Write-Host "  Note: For GSC API access, configure a Google service account"
}

Main
