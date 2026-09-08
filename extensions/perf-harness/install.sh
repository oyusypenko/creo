#!/usr/bin/env bash
set -euo pipefail

main() {
    CREO_DIR="${HOME}/.claude/skills/creo"
    EXT_DIR="${HOME}/.claude/skills/creo-perf-harness"

    if [ ! -d "${CREO_DIR}" ]; then
        echo "✗ Creo core must be installed first."
        exit 1
    fi

    echo "→ Installing perf-harness extension..."
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

    for t in bash curl gzip python3 node; do
        command -v "$t" >/dev/null 2>&1 && echo "  ✓ $t" || echo "  ⚠ $t not found (required at capture time)"
    done
    command -v docker >/dev/null 2>&1 && echo "  ✓ docker" || echo "  ⚠ docker not found (container restarts / log harvest unavailable)"
    { command -v google-chrome || command -v chromium || command -v chromium-browser; } >/dev/null 2>&1 \
        && echo "  ✓ chrome (Lighthouse)" || echo "  ⚠ no Chrome binary (Lighthouse needs one; set CHROME_PATH)"

    rm -rf "${EXT_DIR}"
    mkdir -p "${EXT_DIR}"
    cp "${SCRIPT_DIR}/SKILL.md" "${EXT_DIR}/SKILL.md"
    cp "${SCRIPT_DIR}/README.md" "${EXT_DIR}/README.md"
    cp -r "${SCRIPT_DIR}/scripts" "${EXT_DIR}/scripts"
    cp -r "${SCRIPT_DIR}/templates" "${EXT_DIR}/templates"
    chmod +x "${EXT_DIR}/scripts/"*.sh "${EXT_DIR}/scripts/common/"*.py "${EXT_DIR}/scripts/common/"*.mjs 2>/dev/null || true

    echo ""
    echo "✓ perf-harness extension installed to ${EXT_DIR}"
    echo "  Usage: in a project, run /creo perf init  (scaffolds .claude/skills/creo-perf/)"
    echo "  Then:  .claude/skills/creo-perf/perf preflight && .claude/skills/creo-perf/perf audit-all before"
}

main "$@"
