#!/usr/bin/env bash
set -euo pipefail

# Creo Installer
# Wraps everything in main() to prevent partial execution on network failure

main() {
    SKILL_DIR="${HOME}/.claude/skills/creo"
    AGENT_DIR="${HOME}/.claude/agents"
    REPO_URL="https://github.com/oyusypenko/creo"

    echo "════════════════════════════════════════"
    echo "║   Creo — Installer                  ║"
    echo "║   Design & Development Toolkit       ║"
    echo "════════════════════════════════════════"
    echo ""

    # Check prerequisites
    command -v git >/dev/null 2>&1 || { echo "✗ Git is required but not installed."; exit 1; }
    echo "✓ Git detected"

    # Create directories
    mkdir -p "${SKILL_DIR}"
    mkdir -p "${AGENT_DIR}"

    # Clone to temp
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf ${TEMP_DIR}" EXIT

    echo "↓ Downloading Creo..."
    git clone --depth 1 "${REPO_URL}" "${TEMP_DIR}/creo" 2>/dev/null

    # Copy main skill files (creo/SKILL.md + creo/references/)
    echo "→ Installing skill files..."
    cp -r "${TEMP_DIR}/creo/creo/"* "${SKILL_DIR}/"

    # Copy sub-skills
    if [ -d "${TEMP_DIR}/creo/skills" ]; then
        for skill_dir in "${TEMP_DIR}/creo/skills"/*/; do
            skill_name=$(basename "${skill_dir}")
            target="${HOME}/.claude/skills/${skill_name}"
            mkdir -p "${target}"
            cp -r "${skill_dir}"* "${target}/"
        done
    fi

    # Copy agents
    echo "→ Installing subagents..."
    cp -r "${TEMP_DIR}/creo/agents/"*.md "${AGENT_DIR}/" 2>/dev/null || true

    # Copy docs
    if [ -d "${TEMP_DIR}/creo/docs" ]; then
        mkdir -p "${SKILL_DIR}/docs"
        cp -r "${TEMP_DIR}/creo/docs/"* "${SKILL_DIR}/docs/"
    fi

    # Copy update scripts alongside the skill so users can run them without re-cloning
    for s in update.sh update-check.sh; do
        if [ -f "${TEMP_DIR}/creo/${s}" ]; then
            cp "${TEMP_DIR}/creo/${s}" "${SKILL_DIR}/${s}"
            chmod +x "${SKILL_DIR}/${s}"
        fi
    done

    # Stamp installed commit SHA + timestamp (used by update-check)
    INSTALLED_SHA=$(cd "${TEMP_DIR}/creo" && git rev-parse HEAD 2>/dev/null || echo "unknown")
    echo "${INSTALLED_SHA}" > "${SKILL_DIR}/.version"
    date -u +"%Y-%m-%dT%H:%M:%SZ" > "${SKILL_DIR}/.installed-at"

    echo ""
    echo "✓ Creo installed successfully! (${INSTALLED_SHA:0:7})"
    echo ""
    echo "Usage:"
    echo "  1. Start Claude Code:  claude"
    echo "  2. Run commands:       /creo design-review http://localhost:3000"
    echo ""
    echo "Optional extensions:"
    echo "  Image Generation:  ./extensions/image-generation/install.sh"
    echo "  i18n Translator:   ./extensions/i18n-translator/install.sh"
    echo "  GSC Analyzer:      ./extensions/gsc-analyzer/install.sh"
    echo ""
    echo "To uninstall: curl -fsSL ${REPO_URL}/raw/main/uninstall.sh | bash"
}

main "$@"
