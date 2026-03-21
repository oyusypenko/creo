#!/usr/bin/env pwsh
# Creo uninstaller for Windows

$ErrorActionPreference = "Stop"

function Main {
    $SkillDir = Join-Path $env:USERPROFILE ".claude" "skills"
    $AgentDir = Join-Path $env:USERPROFILE ".claude" "agents"

    Write-Host "→ Uninstalling Creo..." -ForegroundColor Yellow

    # Remove main skill
    $creoDir = Join-Path $SkillDir "creo"
    if (Test-Path $creoDir) {
        Remove-Item -Recurse -Force $creoDir
        Write-Host "  Removed: $creoDir" -ForegroundColor Green
    }

    # Remove sub-skills
    $subSkills = @(
        "creo-design-review", "creo-design-implement", "creo-ux-internal",
        "creo-ux-competitor", "creo-content", "creo-image-prompt",
        "creo-seo", "creo-devops", "creo-pipeline",
        "creo-test", "creo-marketing-site", "creo-ai-generation"
    )
    foreach ($skill in $subSkills) {
        $skillPath = Join-Path $SkillDir $skill
        if (Test-Path $skillPath) {
            Remove-Item -Recurse -Force $skillPath
            Write-Host "  Removed: $skillPath" -ForegroundColor Green
        }
    }

    # Remove agents
    $agents = @(
        "creo-design-review", "creo-design-implement", "creo-ux-internal",
        "creo-ux-competitor", "creo-content", "creo-seo",
        "creo-unit-test", "creo-e2e-test", "creo-github-cli",
        "creo-cloudflare-cli", "creo-railway-cli", "creo-stripe-cli"
    )
    foreach ($agent in $agents) {
        $agentPath = Join-Path $AgentDir "$agent.md"
        if (Test-Path $agentPath) {
            Remove-Item -Force $agentPath
            Write-Host "  Removed: $agentPath" -ForegroundColor Green
        }
    }

    Write-Host ""
    Write-Host "✓ Creo uninstalled." -ForegroundColor Green
    Write-Host "  Note: Extensions must be uninstalled separately." -ForegroundColor Yellow
}

Main
