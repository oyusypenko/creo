#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Main {
    Write-Host "-> Uninstalling i18n-translator extension..."

    $ExtDir = Join-Path $env:USERPROFILE ".claude\skills\creo-i18n"
    $AgentFile = Join-Path $env:USERPROFILE ".claude\agents\creo-i18n.md"

    if (Test-Path $ExtDir) {
        Remove-Item -Recurse -Force $ExtDir
    }

    if (Test-Path $AgentFile) {
        Remove-Item -Force $AgentFile
    }

    Write-Host "[ok] i18n-translator extension uninstalled." -ForegroundColor Green
}

Main
