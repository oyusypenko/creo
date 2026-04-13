#!/usr/bin/env bash
# Creo updater -- reinstalls Creo from the upstream main branch.
# Safe to re-run. Preserves project-specific extensions in project repos
# (those live under the project's .claude/skills/, not ~/.claude/skills/).

set -euo pipefail

REPO_URL="${CREO_REPO_URL:-https://github.com/oyusypenko/creo}"

echo "════════════════════════════════════════"
echo "║   Creo — Updater                     ║"
echo "════════════════════════════════════════"
echo ""

# Show current version if present.
LOCAL_SHA_FILE="${HOME}/.claude/skills/creo/.version"
if [ -f "${LOCAL_SHA_FILE}" ]; then
    CURRENT=$(tr -d '[:space:]' < "${LOCAL_SHA_FILE}")
    echo "Current: ${CURRENT:0:7}"
fi

# Run uninstall to clear stale files (deletions are only picked up this way).
echo "→ Removing previous install..."
curl -fsSL "${REPO_URL}/raw/main/uninstall.sh" | bash >/dev/null 2>&1 || true

# Run install fresh.
echo "→ Installing latest..."
curl -fsSL "${REPO_URL}/raw/main/install.sh" | bash

echo ""
echo "✓ Creo updated."
