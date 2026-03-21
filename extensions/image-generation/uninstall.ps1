#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Main {
    Write-Host "[-] Uninstalling image-generation extension..."

    $ExtDir = Join-Path $env:USERPROFILE ".claude\skills\creo-image-generation"
    $AgentFile = Join-Path $env:USERPROFILE ".claude\agents\creo-image-generation.md"

    if (Test-Path $ExtDir) {
        Remove-Item -Recurse -Force $ExtDir
    }

    if (Test-Path $AgentFile) {
        Remove-Item -Force $AgentFile
    }

    Write-Host "[+] Image generation extension uninstalled." -ForegroundColor Green
}

Main
