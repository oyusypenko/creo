$ErrorActionPreference = "Stop"
$ExtDir = Join-Path $env:USERPROFILE ".claude\skills\creo-perf-harness"
Write-Host "-> Uninstalling perf-harness extension..."
if (Test-Path $ExtDir) { Remove-Item -Recurse -Force $ExtDir }
Write-Host "OK perf-harness extension uninstalled. Project files under .claude\skills\creo-perf\ are left untouched."
