#!/usr/bin/env bash
set -euo pipefail

main() {
    echo "→ Uninstalling Creo..."

    # Remove main skill
    rm -rf "${HOME}/.claude/skills/creo"

    # Remove sub-skills
    for skill in creo-design-review creo-design-implement creo-ux-internal creo-ux-competitor creo-content creo-image-prompt creo-seo creo-devops creo-pipeline creo-test creo-marketing-site creo-ai-generation; do
        rm -rf "${HOME}/.claude/skills/${skill}"
    done

    # Remove agents
    for agent in creo-design-review creo-design-implement creo-ux-internal creo-ux-competitor creo-content creo-seo creo-unit-test creo-e2e-test creo-github-cli creo-cloudflare-cli creo-railway-cli creo-stripe-cli; do
        rm -f "${HOME}/.claude/agents/${agent}.md"
    done

    echo "✓ Creo uninstalled."
    echo "  Note: Extensions must be uninstalled separately."
}

main "$@"
