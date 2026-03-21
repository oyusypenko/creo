#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Main {
    $CreoDir = Join-Path $env:USERPROFILE ".claude\skills\creo"
    $ExtDir = Join-Path $env:USERPROFILE ".claude\skills\creo-i18n"
    $AgentDir = Join-Path $env:USERPROFILE ".claude\agents"

    if (-not (Test-Path $CreoDir)) {
        Write-Host "[x] Creo core must be installed first." -ForegroundColor Red
        exit 1
    }

    # Check Python
    try {
        $pythonVersion = & python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if (-not $pythonVersion) {
            $pythonVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        }
        if (-not $pythonVersion) { throw "not found" }
        Write-Host "[ok] Python $pythonVersion detected" -ForegroundColor Green
    } catch {
        Write-Host "[x] Python 3 is required." -ForegroundColor Red
        exit 1
    }

    Write-Host "-> Installing i18n-translator extension..."
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

    # Create directories
    New-Item -ItemType Directory -Force -Path (Join-Path $ExtDir "scripts") | Out-Null
    New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null

    # Copy skill
    Copy-Item (Join-Path $ScriptDir "skills\creo-i18n\SKILL.md") (Join-Path $ExtDir "SKILL.md") -Force

    # Copy agent
    Copy-Item (Join-Path $ScriptDir "agents\creo-i18n.md") (Join-Path $AgentDir "creo-i18n.md") -Force

    # Copy scripts
    Get-ChildItem (Join-Path $ScriptDir "scripts\*.py") | ForEach-Object {
        Copy-Item $_.FullName (Join-Path $ExtDir "scripts" $_.Name) -Force
    }
    Copy-Item (Join-Path $ScriptDir "config.json") (Join-Path $ExtDir "config.json") -Force
    Copy-Item (Join-Path $ScriptDir "requirements.txt") (Join-Path $ExtDir "requirements.txt") -Force

    # Install Python deps
    Write-Host "-> Installing Python dependencies..."
    $VenvDir = Join-Path $ExtDir ".venv"
    try {
        & python3 -m venv $VenvDir 2>$null
        $pipExe = Join-Path $VenvDir "Scripts\pip.exe"
        if (Test-Path $pipExe) {
            & $pipExe install --quiet -r (Join-Path $ScriptDir "requirements.txt") 2>$null
            Write-Host "  [ok] Installed in venv" -ForegroundColor Green
        }
    } catch {
        try {
            & pip install --quiet --user -r (Join-Path $ScriptDir "requirements.txt") 2>$null
        } catch {
            Write-Host "  [!] Could not auto-install. Run: pip install --user -r $(Join-Path $ExtDir 'requirements.txt')" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "[ok] i18n-translator extension installed!" -ForegroundColor Green
    Write-Host "  Usage: /creo i18n translate en uk,pl,de"
    Write-Host "  Note: LM Studio must be running on port 1234"
}

Main
