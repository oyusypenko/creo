# Architecture

## Overview

Creo follows a 3-layer architecture: **orchestration** (main skill), **specialization** (sub-skills), and **execution** (subagents). Optional extensions add tool-backed capabilities.

## Layers

### Layer 1: Orchestrator (`creo/SKILL.md`)

The entry point for all `/creo` commands. Routes requests to the appropriate sub-skill based on the command. For complex workflows (marketing-site, devops, test), spawns multiple subagents in parallel.

### Layer 2: Sub-Skills (`skills/creo-*/SKILL.md`)

12 specialized skills, each handling a specific domain. Contains detailed instructions, command routing, and references to on-demand knowledge files.

| Domain | Skills |
|--------|--------|
| Design & UX | design-review, design-implement, ux-internal, ux-competitor |
| Content & Marketing | content, image-prompt |
| SEO | seo |
| DevOps | devops, pipeline |
| Testing | test |
| Orchestration | marketing-site, ai-generation |

### Layer 3: Subagents (`agents/creo-*.md`)

12 lightweight agents optimized for parallel execution. Spawned by orchestrator skills via Task tool with `context: fork`.

| Skill Spawns | Subagents |
|-------------|-----------|
| creo-devops | creo-github-cli, creo-cloudflare-cli, creo-railway-cli, creo-stripe-cli |
| creo-test | creo-unit-test, creo-e2e-test |
| creo-marketing-site | creo-design-review, creo-content, creo-seo, creo-ux-competitor |

## Extensions

Self-contained packages that add tool-backed capabilities. Each extension provides:
- Its own skill (`SKILL.md`)
- Its own agent (`.md`)
- Install/uninstall scripts
- Tool code (Python or Node.js)

Extensions install to `~/.claude/skills/creo-{extension}/` and `~/.claude/agents/creo-{extension}.md`.

## Reference Files

12 on-demand knowledge files in `creo/references/`. Loaded only when needed by skills -- not at startup. Each under 200 lines.

## Installation Layout

```
~/.claude/
├── skills/
│   ├── creo/                    # Main skill + references
│   ├── creo-design-review/      # Sub-skill
│   ├── creo-design-implement/
│   ├── ...                      # (10 more sub-skills)
│   ├── creo-image-generation/   # Extension (if installed)
│   ├── creo-i18n/               # Extension (if installed)
│   └── creo-gsc/                # Extension (if installed)
└── agents/
    ├── creo-design-review.md    # Subagent
    ├── creo-design-implement.md
    ├── ...                      # (10 more subagents)
    ├── creo-image-generation.md # Extension agent (if installed)
    ├── creo-i18n.md             # Extension agent (if installed)
    └── creo-gsc.md              # Extension agent (if installed)
```

## Project Configuration

Skills check `.claude/project-config.md` at runtime for project-specific customization (colors, URLs, tech stack, locales, competitors). This replaces the old project-specific extension pattern from design-ux-toolkit.
