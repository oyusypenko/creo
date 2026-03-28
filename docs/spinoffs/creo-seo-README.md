# creo-seo

AI-powered SEO audit & optimization skill for Claude Code.

[![GitHub Stars](https://img.shields.io/github/stars/oyusypenko/creo-seo?style=social)](https://github.com/oyusypenko/creo-seo/stargazers)
[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What It Does

Run `/creo-seo audit <url>` and get a comprehensive SEO analysis:

- **Technical SEO** -- Meta tags, canonical URLs, robots.txt, sitemap.xml
- **Structured Data** -- JSON-LD validation, Schema.org compliance
- **Content Optimization** -- Heading hierarchy, keyword density, readability
- **Performance Signals** -- Core Web Vitals indicators, image optimization
- **Actionable Report** -- Prioritized fixes with code snippets

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/oyusypenko/creo-seo/main/install.sh | bash
```

## Usage

```
/creo-seo audit https://example.com          # Full SEO audit
/creo-seo meta https://example.com           # Meta tags only
/creo-seo structured-data https://example.com # Schema.org check
```

## Part of Creo

This is a standalone extraction from [Creo](https://github.com/oyusypenko/creo) -- a full design & development toolkit with 12 skills covering design review, UX analysis, content generation, DevOps, CI/CD, testing, and more.

## Compatibility

Works with **Claude Code** (primary), and compatible with Codex CLI, Cursor, and Gemini CLI via standard SKILL.md format.

## License

[MIT](LICENSE)
