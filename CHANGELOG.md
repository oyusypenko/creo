# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-03-21

### Added
- Initial release of Creo as a Claude Code skill
- Main orchestrator skill with `/creo` command routing
- 12 sub-skills: design-review, design-implement, ux-internal, ux-competitor, content, image-prompt, seo, devops, pipeline, test, marketing-site, ai-generation
- 12 parallel subagents for concurrent execution
- 12 on-demand reference files (design principles, UX methodologies, pain points framework, SEO checklists, etc.)
- 3 optional extensions: image-generation (Node.js), i18n-translator (Python), gsc-analyzer (Python)
- One-liner install/uninstall scripts for Unix and Windows
- Plugin manifest for Claude Code discovery
- Comprehensive documentation (CLAUDE.md, README, CONTRIBUTING, SECURITY)

### Changed
- Restructured from git submodule (design-ux-toolkit) to Claude Code skill format
- Tools (image-generation, i18n-translator, gsc-analyzer) moved to self-contained extensions
- Agents refactored from `dut_` prefix to `creo-` prefix
- Project-specific extension pattern replaced with `.claude/project-config.md` runtime check
