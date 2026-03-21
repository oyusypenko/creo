#!/usr/bin/env bash
set -euo pipefail

main() {
    CREO_DIR="${HOME}/.claude/skills/creo"
    EXT_DIR="${HOME}/.claude/skills/creo-i18n"
    AGENT_DIR="${HOME}/.claude/agents"

    if [ ! -d "${CREO_DIR}" ]; then
        echo "✗ Creo core must be installed first."
        exit 1
    fi

    command -v python3 >/dev/null 2>&1 || { echo "✗ Python 3 is required."; exit 1; }
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "✓ Python ${PYTHON_VERSION} detected"

    echo "→ Installing i18n-translator extension..."
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

    mkdir -p "${EXT_DIR}/scripts"
    mkdir -p "${AGENT_DIR}"

    # Copy skill
    cp "${SCRIPT_DIR}/skills/creo-i18n/SKILL.md" "${EXT_DIR}/SKILL.md"

    # Copy agent
    cp "${SCRIPT_DIR}/agents/creo-i18n.md" "${AGENT_DIR}/creo-i18n.md"

    # Copy scripts
    cp "${SCRIPT_DIR}/scripts/"*.py "${EXT_DIR}/scripts/"
    cp "${SCRIPT_DIR}/config.json" "${EXT_DIR}/"
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
    echo "✓ i18n-translator extension installed!"
    echo "  Usage: /creo i18n translate en uk,pl,de"
    echo "  Note: LM Studio must be running on port 1234"
}

main "$@"
