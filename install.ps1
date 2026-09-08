# Creo Installer for Windows
# PowerShell installation script

$ErrorActionPreference = "Stop"

Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "║   Creo — Installer                  ║" -ForegroundColor Cyan
Write-Host "║   Design & Development Toolkit       ║" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
try {
    git --version | Out-Null
    Write-Host "✓ Git detected" -ForegroundColor Green
} catch {
    Write-Host "✗ Git is required but not installed." -ForegroundColor Red
    exit 1
}

# Set paths
$SkillDir = "$env:USERPROFILE\.claude\skills\creo"
$AgentDir = "$env:USERPROFILE\.claude\agents"
$RepoUrl = "https://github.com/oyusypenko/creo"

# Create directories
New-Item -ItemType Directory -Force -Path $SkillDir | Out-Null
New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null

# Clone to temp directory
$TempDir = Join-Path $env:TEMP "creo-install"
if (Test-Path $TempDir) {
    Remove-Item -Recurse -Force $TempDir
}

try {
    Write-Host "↓ Downloading Creo..." -ForegroundColor Yellow
    git clone --depth 1 $RepoUrl $TempDir 2>&1 | Out-Null

    # Copy main skill files
    Write-Host "→ Installing skill files..." -ForegroundColor Yellow
    Copy-Item -Recurse -Force (Join-Path $TempDir 'creo' '*') $SkillDir

    # Copy sub-skills
    $SkillsPath = Join-Path $TempDir 'skills'
    if (Test-Path $SkillsPath) {
        Get-ChildItem -Directory $SkillsPath | ForEach-Object {
            $target = "$env:USERPROFILE\.claude\skills\$($_.Name)"
            New-Item -ItemType Directory -Force -Path $target | Out-Null
            Copy-Item -Recurse -Force "$($_.FullName)\*" $target
        }
    }

    # Copy agents
    Write-Host "→ Installing subagents..." -ForegroundColor Yellow
    $AgentsPath = Join-Path $TempDir 'agents'
    if (Test-Path $AgentsPath) {
        Copy-Item -Force (Join-Path $AgentsPath '*.md') $AgentDir -ErrorAction SilentlyContinue
    }

    # Copy docs
    $DocsPath = Join-Path $TempDir 'docs'
    if (Test-Path $DocsPath) {
        $SkillDocs = Join-Path $SkillDir 'docs'
        New-Item -ItemType Directory -Force -Path $SkillDocs | Out-Null
        Copy-Item -Recurse -Force "$DocsPath\*" $SkillDocs
    }

    # Copy update scripts
    foreach ($script in @('update.sh', 'update.ps1', 'update-check.sh', 'update-check.ps1')) {
        $src = Join-Path $TempDir $script
        if (Test-Path $src) { Copy-Item -Force $src (Join-Path $SkillDir $script) }
    }

    # Stamp installed version
    $InstalledSha = (git -C $TempDir rev-parse HEAD).Trim()
    Set-Content -Path (Join-Path $SkillDir '.version') -Value $InstalledSha -NoNewline
    Set-Content -Path (Join-Path $SkillDir '.installed-at') -Value ([DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')) -NoNewline
} catch {
    Write-Host ""
    Write-Host "✗ Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    throw
} finally {
    if (Test-Path $TempDir) {
        Remove-Item -Recurse -Force $TempDir
    }
}

Write-Host ""
$shortSha = if ($InstalledSha) { $InstalledSha.Substring(0, 7) } else { "unknown" }
Write-Host "✓ Creo installed successfully! ($shortSha)" -ForegroundColor Green
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  1. Start Claude Code:  claude"
Write-Host "  2. Run commands:       /creo design-review http://localhost:3000"
Write-Host ""
Write-Host "Optional extensions:" -ForegroundColor Cyan
Write-Host "  Image Generation:  .\extensions\image-generation\install.ps1"
Write-Host "  i18n Translator:   .\extensions\i18n-translator\install.ps1"
Write-Host "  GSC Analyzer:      .\extensions\gsc-analyzer\install.ps1"
Write-Host "  Perf Harness:      .\extensions\perf-harness\install.ps1"
