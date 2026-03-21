#!/usr/bin/env bash
set -euo pipefail

main() {
    echo "→ Uninstalling i18n-translator extension..."
    rm -rf "${HOME}/.claude/skills/creo-i18n"
    rm -f "${HOME}/.claude/agents/creo-i18n.md"
    echo "✓ i18n-translator extension uninstalled."
}

main "$@"
