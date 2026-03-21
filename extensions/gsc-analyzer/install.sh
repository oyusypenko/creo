#!/usr/bin/env bash
set -euo pipefail

main() {
    CREO_DIR="${HOME}/.claude/skills/creo"
    EXT_DIR="${HOME}/.claude/skills/creo-gsc"
    AGENT_DIR="${HOME}/.claude/agents"

    if [ ! -d "${CREO_DIR}" ]; then
        echo "✗ Creo core must be installed first."
        exit 1
    fi

    command -v python3 >/dev/null 2>&1 || { echo "✗ Python 3 is required."; exit 1; }
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "✓ Python ${PYTHON_VERSION} detected"

    echo "→ Installing gsc-analyzer extension..."
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

    mkdir -p "${EXT_DIR}/gsc_toolkit"
    mkdir -p "${EXT_DIR}/scripts"

    # Copy skill
    cp "${SCRIPT_DIR}/skills/creo-gsc/SKILL.md" "${EXT_DIR}/SKILL.md"

    # Copy agent
    mkdir -p "${AGENT_DIR}"
    cp "${SCRIPT_DIR}/agents/creo-gsc.md" "${AGENT_DIR}/creo-gsc.md"

    # Copy gsc_toolkit package
    cp -r "${SCRIPT_DIR}/gsc_toolkit/"* "${EXT_DIR}/gsc_toolkit/"

    # Copy legacy script
    cp "${SCRIPT_DIR}/scripts/"*.py "${EXT_DIR}/scripts/" 2>/dev/null || true

    # Copy requirements
    cp "${SCRIPT_DIR}/requirements.txt" "${EXT_DIR}/"

    # Install Python deps
    echo "→ Installing Python dependencies..."
    VENV_DIR="${EXT_DIR}/.venv"
    if python3 -m venv "${VENV_DIR}" 2>/dev/null; then
        "${VENV_DIR}/bin/pip" install --quiet -r "${SCRIPT_DIR}/requirements.txt" 2>/dev/null && \
            echo "  ✓ Installed in venv" || \
            echo "  ⚠ Venv pip failed. Run: ${VENV_DIR}/bin/pip install -r ${EXT_DIR}/requirements.txt"
    else
        pip install --quiet --user -r "${SCRIPT_DIR}/requirements.txt" 2>/dev/null || \
        echo "  ⚠ Could not auto-install. Run: pip install --user -r ${EXT_DIR}/requirements.txt"
    fi

    echo ""
    echo "✓ GSC Analyzer extension installed!"
    echo "  Usage: /creo gsc full-seo https://example.com"
    echo "  Note: For GSC API access, configure a Google service account"
}

main "$@"
