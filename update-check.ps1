# Creo update checker (Windows) -- silent on success, warns on mismatch.
# Run as a Claude Code SessionStart hook. Never fails.

$ErrorActionPreference = 'SilentlyContinue'

$SkillDir = if ($env:CREO_SKILL_DIR) { $env:CREO_SKILL_DIR } else { "$env:USERPROFILE\.claude\skills\creo" }
$Repo     = if ($env:CREO_REPO)      { $env:CREO_REPO }      else { 'oyusypenko/creo' }
$Timeout  = if ($env:CREO_TIMEOUT)   { [int]$env:CREO_TIMEOUT } else { 3 }

$VersionFile = Join-Path $SkillDir '.version'
if (-not (Test-Path $VersionFile)) { exit 0 }

$LocalSha = (Get-Content $VersionFile -Raw).Trim()
if (-not $LocalSha -or $LocalSha -eq 'unknown') { exit 0 }

try {
    $resp = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/commits/main" -TimeoutSec $Timeout
    $RemoteSha = $resp.sha
} catch {
    $RemoteSha = $null
}

if (-not $RemoteSha) { exit 0 }

if ($LocalSha -ne $RemoteSha) {
    Write-Host ("Creo update available: installed {0} -> remote {1}" -f $LocalSha.Substring(0,7), $RemoteSha.Substring(0,7))
    Write-Host ("  Update: irm https://raw.githubusercontent.com/{0}/main/update.ps1 | iex" -f $Repo)
}

exit 0
