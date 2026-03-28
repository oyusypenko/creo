# Creo v1.0.0

First public release of the Creo design & development toolkit for Claude Code.

## What's Included

### 12 Skills
- **design-review** -- Responsive testing (375-1920px), WCAG AA, Nielsen's heuristics
- **design-implement** -- Execute fixes from review reports
- **ux-internal** -- Analyze your own app's UX flows
- **ux-competitor** -- Analyze competitor websites
- **content** -- Marketing copy with JTBD framework
- **image-prompt** -- Optimized prompts for DALL-E 3, Midjourney, SDXL
- **seo** -- Technical SEO audit, meta tags, structured data
- **devops** -- GitHub, Cloudflare, Railway, Stripe CLI operations
- **pipeline** -- GitHub Actions workflow creation & debugging
- **test** -- Unit (Vitest/Jest) and E2E (Playwright) orchestration
- **marketing-site** -- 7-stage orchestrated site creation
- **ai-generation** -- LLM pipeline expertise

### 12 Parallel Subagents
Each skill has a dedicated subagent for parallel execution.

### 3 Optional Extensions
- **image-generation** -- DALL-E 3 & ComfyUI (Node.js)
- **i18n-translator** -- Batch translation for 39+ languages (Python + LM Studio)
- **gsc-analyzer** -- Google Search Console analysis with 15+ analyzers (Python)

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/oyusypenko/creo/main/install.sh | bash
```

## Compatibility

Works with Claude Code (primary), and compatible with Codex CLI, Cursor, and Gemini CLI via standard SKILL.md format.
