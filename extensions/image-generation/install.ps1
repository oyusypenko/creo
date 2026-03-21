#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Main {
    $CreoDir = Join-Path $env:USERPROFILE ".claude\skills\creo"
    $ExtDir = Join-Path $env:USERPROFILE ".claude\skills\creo-image-generation"
    $AgentDir = Join-Path $env:USERPROFILE ".claude\agents"

    # Check Creo core is installed
    if (-not (Test-Path $CreoDir)) {
        Write-Host "[x] Creo core must be installed first. Run the main install.ps1." -ForegroundColor Red
        exit 1
    }

    # Check Node.js
    try {
        $nodeVersion = & node -v 2>$null
        Write-Host "[+] Node.js $nodeVersion detected" -ForegroundColor Green
    }
    catch {
        Write-Host "[x] Node.js is required." -ForegroundColor Red
        exit 1
    }

    Write-Host "[-] Installing image-generation extension..."

    # Determine script directory
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

    # Create directories
    New-Item -ItemType Directory -Force -Path (Join-Path $ExtDir "lib") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $ExtDir "comfyui\workflows") | Out-Null
    New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null

    # Copy skill
    Copy-Item (Join-Path $ScriptDir "skills\creo-image-generation\SKILL.md") (Join-Path $ExtDir "SKILL.md") -Force

    # Copy agent
    Copy-Item (Join-Path $ScriptDir "agents\creo-image-generation.md") (Join-Path $AgentDir "creo-image-generation.md") -Force

    # Copy lib
    Copy-Item (Join-Path $ScriptDir "lib\*.js") (Join-Path $ExtDir "lib\") -Force
    Copy-Item (Join-Path $ScriptDir "package.json") $ExtDir -Force
    Copy-Item (Join-Path $ScriptDir "index.js") $ExtDir -Force

    # Copy comfyui
    Copy-Item (Join-Path $ScriptDir "comfyui\generate-batch.js") (Join-Path $ExtDir "comfyui\") -Force
    Copy-Item (Join-Path $ScriptDir "comfyui\SETUP.md") (Join-Path $ExtDir "comfyui\") -Force
    if (Test-Path (Join-Path $ScriptDir "comfyui\workflows\*")) {
        Copy-Item (Join-Path $ScriptDir "comfyui\workflows\*") (Join-Path $ExtDir "comfyui\workflows\") -Force
    }

    # Copy .env.example
    $envExample = Join-Path $ScriptDir ".env.example"
    if (Test-Path $envExample) {
        Copy-Item $envExample $ExtDir -Force
    }

    # Install npm dependencies
    Write-Host "[-] Installing npm dependencies..."
    try {
        Push-Location $ExtDir
        & npm install --production 2>$null
        Pop-Location
    }
    catch {
        Write-Host "[!] npm install failed. Run: cd $ExtDir && npm install" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "[+] Image generation extension installed!" -ForegroundColor Green
    Write-Host "  Usage: /creo image-generation generate"
    Write-Host "  Note: Set OPENAI_API_KEY in your environment for DALL-E 3"
}

Main
