#!/usr/bin/env bash
set -euo pipefail

main() {
    echo "→ Uninstalling gsc-analyzer extension..."
    rm -rf "${HOME}/.claude/skills/creo-gsc"
    rm -f "${HOME}/.claude/agents/creo-gsc.md"
    echo "✓ GSC Analyzer extension uninstalled."
}

main "$@"
