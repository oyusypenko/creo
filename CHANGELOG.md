# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `creo-perf` sub-skill (`/creo perf`): full-stack performance optimization with measured proof — six-layer audit, immutable labeled baselines, deterministic before/after captures, one-concern-per-commit fix loop, SOLUTION-style reporting, and `/creo perf init` which scaffolds and fills a project's `.claude/skills/creo-perf/` (targets, scenarios, SQL sources, FE probes, dashboard config, extension doc)
- `creo-perf-audit` subagent: measure-only six-layer auditor (baseline / after / discover modes)
- `perf-harness` extension: project-agnostic benchmark scripts (scenario captures with EXPLAIN medians, p50/p95 loops, wire bytes, ETag replay, Playwright interaction probe; Lighthouse initial-load audit; platform and schema audits with hypopg; pg_stat_statements workload discovery; auto-built dashboard with deltas) plus the templates `init-project.sh` copies into a project
- Plugin marketplace file (`.claude-plugin/marketplace.json`) so the repository is installable via `/plugin marketplace add oyusypenko/creo` in Claude Code and `codex plugin marketplace add oyusypenko/creo` in Codex
- Marketplace and Codex install instructions in README and INSTALLATION docs

### Fixed
- `plugin.json` now matches the Claude Code plugin manifest schema (`author` as object, directory-based `skills` paths, removed unrecognized `entry_point` field); passes `claude plugin validate --strict`

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
