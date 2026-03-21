#Requires -Version 5.1
<#
.SYNOPSIS
    Uninstalls the gsc-analyzer extension for Creo.
#>

$ErrorActionPreference = "Stop"

function Main {
    Write-Host "-> Uninstalling gsc-analyzer extension..."

    $ExtDir = Join-Path $env:USERPROFILE ".claude\skills\creo-gsc"
    $AgentFile = Join-Path $env:USERPROFILE ".claude\agents\creo-gsc.md"

    if (Test-Path $ExtDir) {
        Remove-Item -Recurse -Force $ExtDir
    }
    if (Test-Path $AgentFile) {
        Remove-Item -Force $AgentFile
    }

    Write-Host "OK GSC Analyzer extension uninstalled." -ForegroundColor Green
}

Main
