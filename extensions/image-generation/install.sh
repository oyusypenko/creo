#!/usr/bin/env bash
set -euo pipefail

main() {
    CREO_DIR="${HOME}/.claude/skills/creo"
    EXT_DIR="${HOME}/.claude/skills/creo-image-generation"
    AGENT_DIR="${HOME}/.claude/agents"

    # Check Creo core is installed
    if [ ! -d "${CREO_DIR}" ]; then
        echo "✗ Creo core must be installed first. Run the main install.sh."
        exit 1
    fi

    # Check Node.js
    command -v node >/dev/null 2>&1 || { echo "✗ Node.js is required."; exit 1; }
    NODE_VERSION=$(node -v)
    echo "✓ Node.js ${NODE_VERSION} detected"

    echo "→ Installing image-generation extension..."

    # Determine script directory
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

    # Create directories
    mkdir -p "${EXT_DIR}/lib"
    mkdir -p "${EXT_DIR}/comfyui/workflows"

    # Copy skill
    mkdir -p "${HOME}/.claude/skills/creo-image-generation"
    cp "${SCRIPT_DIR}/skills/creo-image-generation/SKILL.md" "${EXT_DIR}/SKILL.md"

    # Copy agent
    mkdir -p "${AGENT_DIR}"
    cp "${SCRIPT_DIR}/agents/creo-image-generation.md" "${AGENT_DIR}/creo-image-generation.md"

    # Copy lib
    cp "${SCRIPT_DIR}/lib/"*.js "${EXT_DIR}/lib/"
    cp "${SCRIPT_DIR}/package.json" "${EXT_DIR}/"
    cp "${SCRIPT_DIR}/index.js" "${EXT_DIR}/"

    # Copy comfyui
    cp "${SCRIPT_DIR}/comfyui/generate-batch.js" "${EXT_DIR}/comfyui/"
    cp "${SCRIPT_DIR}/comfyui/SETUP.md" "${EXT_DIR}/comfyui/"
    cp -r "${SCRIPT_DIR}/comfyui/workflows/"* "${EXT_DIR}/comfyui/workflows/" 2>/dev/null || true

    # Copy .env.example if it exists
    if [ -f "${SCRIPT_DIR}/.env.example" ]; then
        cp "${SCRIPT_DIR}/.env.example" "${EXT_DIR}/.env.example"
    fi

    # Install npm dependencies
    echo "→ Installing npm dependencies..."
    cd "${EXT_DIR}" && npm install --production 2>/dev/null || echo "⚠ npm install failed. Run: cd ${EXT_DIR} && npm install"

    echo ""
    echo "✓ Image generation extension installed!"
    echo "  Usage: /creo image-generation generate"
    echo "  Note: Set OPENAI_API_KEY in your environment for DALL-E 3"
}

main "$@"
