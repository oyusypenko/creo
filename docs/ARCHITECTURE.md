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
- Optionally: automation scripts (`scripts/`), copy-into-project templates (`templates/`), reference docs (`references/`, `docs/`)

The gsc-analyzer extension additionally powers the creo-seo skill's operations mode (`/creo seo onboard`, `autofix`, `weekly`, `semantic-core`): the skill holds the generic playbooks (`skills/creo-seo/references/`), the extension holds the executable scripts. Skills degrade gracefully when the extension is absent.

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

Skills check `.claude/project-config.md` at runtime for baseline project settings (colors, URLs, tech stack, locales, competitors). The `project_id` field is used to resolve per-skill extension files.

## Project Extensions

Per-skill extension files let you teach any Creo skill about your project's domain, conventions, and file paths without modifying Creo itself.

**Location:** `.claude/skills/creo-{skill}/creo-{skill}-{project_id}.md` (inside the project repo, not the Creo install).

**Loading:** Every skill and subagent reads `.claude/project-config.md`, resolves `{project_id}`, then loads the matching extension file if it exists. The extension is consulted before any work begins.

**Covered skills and subagents:**

| Skill/Agent | Extension path |
|-------------|----------------|
| creo-design-review | `.claude/skills/creo-design-review/creo-design-review-{project_id}.md` |
| creo-design-implement | `.claude/skills/creo-design-implement/creo-design-implement-{project_id}.md` |
| creo-ux-internal | `.claude/skills/creo-ux-internal/creo-ux-internal-{project_id}.md` |
| creo-ux-competitor | `.claude/skills/creo-ux-competitor/creo-ux-competitor-{project_id}.md` |
| creo-content | `.claude/skills/creo-content/creo-content-{project_id}.md` |
| creo-image-prompt | `.claude/skills/creo-image-prompt/creo-image-prompt-{project_id}.md` |
| creo-seo | `.claude/skills/creo-seo/creo-seo-{project_id}.md` |
| creo-devops | `.claude/skills/creo-devops/creo-devops-{project_id}.md` |
| creo-pipeline | `.claude/skills/creo-pipeline/creo-pipeline-{project_id}.md` |
| creo-test | `.claude/skills/creo-test/creo-test-{project_id}.md` |
| creo-marketing-site | `.claude/skills/creo-marketing-site/creo-marketing-site-{project_id}.md` |
| creo-ai-generation | `.claude/skills/creo-ai-generation/creo-ai-generation-{project_id}.md` |
| creo-unit-test | `.claude/skills/creo-unit-test/creo-unit-test-{project_id}.md` |
| creo-e2e-test | `.claude/skills/creo-e2e-test/creo-e2e-test-{project_id}.md` |
| creo-github-cli | `.claude/skills/creo-github-cli/creo-github-cli-{project_id}.md` |
| creo-cloudflare-cli | `.claude/skills/creo-cloudflare-cli/creo-cloudflare-cli-{project_id}.md` |
| creo-railway-cli | `.claude/skills/creo-railway-cli/creo-railway-cli-{project_id}.md` |
| creo-stripe-cli | `.claude/skills/creo-stripe-cli/creo-stripe-cli-{project_id}.md` |

**Design rationale:** Keeps upstream Creo skills generic and reusable across any codebase, while project-specific knowledge lives in the project repo, is version-controlled with the code it describes, and survives Creo updates.
