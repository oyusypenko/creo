#!/usr/bin/env bash
set -euo pipefail

# Setup GitHub repository metadata for SEO optimization
# Run this script once after creating the repo: bash scripts/setup-github.sh

REPO="oyusypenko/creo"

echo "Setting repository description..."
gh repo edit "$REPO" \
  --description "AI-powered design review, UX analysis, SEO audit, content generation, DevOps & testing toolkit for Claude Code. 12 skills, 12 parallel subagents. One-liner install."

echo "Adding topic tags..."
gh repo edit "$REPO" \
  --add-topic claude-code \
  --add-topic claude-skills \
  --add-topic claude-code-skills \
  --add-topic claude-code-plugin \
  --add-topic agent-skills \
  --add-topic design-review \
  --add-topic ux-analysis \
  --add-topic seo-audit \
  --add-topic devops \
  --add-topic developer-tools \
  --add-topic ai-agents \
  --add-topic agentic-coding \
  --add-topic marketing \
  --add-topic testing \
  --add-topic ci-cd \
  --add-topic wcag \
  --add-topic anthropic

echo "Done! Topics and description updated."
echo ""
echo "Next steps:"
echo "  1. Create release: gh release create v1.0.0 -F .github/release-notes-v1.0.0.md --title 'Creo v1.0.0'"
echo "  2. Record demo GIF with asciinema or vhs"
echo "  3. Star your own repo for initial count"
