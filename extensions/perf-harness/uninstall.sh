#!/usr/bin/env bash
set -euo pipefail

main() {
    echo "→ Uninstalling perf-harness extension..."
    rm -rf "${HOME}/.claude/skills/creo-perf-harness"
    echo "✓ perf-harness extension uninstalled. (Project files under .claude/skills/creo-perf/ are left untouched.)"
}

main "$@"
