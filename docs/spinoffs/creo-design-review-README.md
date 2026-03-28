# creo-design-review

AI-powered design review skill for Claude Code -- responsive testing, WCAG accessibility, and UX heuristics.

[![GitHub Stars](https://img.shields.io/github/stars/oyusypenko/creo-design-review?style=social)](https://github.com/oyusypenko/creo-design-review/stargazers)
[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What It Does

Run `/creo-design-review <url>` and get a full UI/UX audit:

- **Responsive Testing** -- 375px to 1920px breakpoints
- **WCAG AA Accessibility** -- Color contrast, ARIA, keyboard navigation, screen reader
- **Nielsen's 10 Heuristics** -- Visibility, consistency, error prevention, flexibility
- **Visual Polish** -- Spacing, typography, alignment, color harmony
- **Actionable Report** -- Prioritized issues with fix suggestions

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/oyusypenko/creo-design-review/main/install.sh | bash
```

## Usage

```
/creo-design-review http://localhost:3000     # Review local dev
/creo-design-review https://example.com       # Review live site
```

## Part of Creo

This is a standalone extraction from [Creo](https://github.com/oyusypenko/creo) -- a full design & development toolkit with 12 skills covering SEO, content generation, DevOps, CI/CD, testing, and more.

## Compatibility

Works with **Claude Code** (primary), and compatible with Codex CLI, Cursor, and Gemini CLI via standard SKILL.md format.

## License

[MIT](LICENSE)
