$ErrorActionPreference = "Stop"

$CreoDir = Join-Path $env:USERPROFILE ".claude\skills\creo"
$ExtDir = Join-Path $env:USERPROFILE ".claude\skills\creo-perf-harness"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path $CreoDir)) {
    Write-Host "x Creo core must be installed first."
    exit 1
}

Write-Host "-> Installing perf-harness extension..."
Write-Host "   Note: the harness scripts are bash + python3 + node; run captures from WSL or Git Bash."

if (Test-Path $ExtDir) { Remove-Item -Recurse -Force $ExtDir }
New-Item -ItemType Directory -Force -Path $ExtDir | Out-Null
Copy-Item (Join-Path $ScriptDir "SKILL.md") $ExtDir
Copy-Item (Join-Path $ScriptDir "README.md") $ExtDir
Copy-Item -Recurse (Join-Path $ScriptDir "scripts") (Join-Path $ExtDir "scripts")
Copy-Item -Recurse (Join-Path $ScriptDir "templates") (Join-Path $ExtDir "templates")

Write-Host ""
Write-Host "OK perf-harness extension installed to $ExtDir"
Write-Host "   Usage: in a project, run /creo perf init"
