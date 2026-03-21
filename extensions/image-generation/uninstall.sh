#!/usr/bin/env bash
set -euo pipefail

main() {
    echo "→ Uninstalling image-generation extension..."
    rm -rf "${HOME}/.claude/skills/creo-image-generation"
    rm -f "${HOME}/.claude/agents/creo-image-generation.md"
    echo "✓ Image generation extension uninstalled."
}

main "$@"
