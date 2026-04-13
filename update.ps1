# Creo updater (Windows) -- reinstalls Creo from the upstream main branch.

$ErrorActionPreference = 'Stop'

$RepoUrl = if ($env:CREO_REPO_URL) { $env:CREO_REPO_URL } else { 'https://github.com/oyusypenko/creo' }

Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "║   Creo — Updater                     ║" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$VersionFile = "$env:USERPROFILE\.claude\skills\creo\.version"
if (Test-Path $VersionFile) {
    $Current = (Get-Content $VersionFile -Raw).Trim()
    Write-Host "Current: $($Current.Substring(0, [Math]::Min(7, $Current.Length)))"
}

Write-Host "-> Removing previous install..." -ForegroundColor Yellow
try {
    Invoke-Expression ((Invoke-WebRequest -Uri "$RepoUrl/raw/main/uninstall.ps1" -UseBasicParsing).Content)
} catch {
    Write-Host "  (uninstall skipped or failed; continuing)"
}

Write-Host "-> Installing latest..." -ForegroundColor Yellow
Invoke-Expression ((Invoke-WebRequest -Uri "$RepoUrl/raw/main/install.ps1" -UseBasicParsing).Content)

Write-Host ""
Write-Host "Creo updated." -ForegroundColor Green
