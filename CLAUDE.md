# Creo -- Design & Development Toolkit

## Project Overview

Creo is a Claude Code skill providing 12 sub-skills, 12 parallel subagents, and 3 optional
extensions covering design review, UX analysis, marketing content, SEO, DevOps, CI/CD,
testing, and marketing site orchestration.

## Architecture

```
creo/
  CLAUDE.md                            # Project instructions (this file)
  .claude-plugin/plugin.json           # Plugin manifest (v1.0.0)
  creo/                                # Main orchestrator skill
    SKILL.md                           # Entry point, routing table, core rules
    references/                        # On-demand knowledge files (12 files)
  skills/                              # 12 specialized sub-skills
    creo-design-review/SKILL.md        # UI/UX review (responsive, WCAG, heuristics)
    creo-design-implement/SKILL.md     # Execute design fixes from reports
    creo-ux-internal/SKILL.md          # Analyze own app UX flows
    creo-ux-competitor/SKILL.md        # Analyze competitor UX
    creo-content/SKILL.md              # Marketing content (JTBD, pain points)
    creo-image-prompt/SKILL.md         # Image prompt generation
    creo-seo/SKILL.md                  # SEO audit & optimization
    creo-devops/SKILL.md               # Infrastructure (GitHub/Cloudflare/Railway/Stripe)
    creo-pipeline/SKILL.md             # CI/CD pipeline specialist
    creo-test/SKILL.md                 # Test orchestration (unit + E2E)
    creo-marketing-site/SKILL.md       # Marketing site creation (7-stage)
    creo-ai-generation/SKILL.md        # AI generation pipelines
  agents/                              # 12 parallel subagents
    creo-design-review.md
    creo-design-implement.md
    creo-ux-internal.md
    creo-ux-competitor.md
    creo-content.md
    creo-seo.md
    creo-unit-test.md
    creo-e2e-test.md
    creo-github-cli.md
    creo-cloudflare-cli.md
    creo-railway-cli.md
    creo-stripe-cli.md
  extensions/                          # Optional extensions
    image-generation/                  # DALL-E 3 & ComfyUI (Node.js)
    i18n-translator/                   # Batch translation via LM Studio (Python)
    gsc-analyzer/                      # Google Search Console (Python)
  docs/                                # Extended documentation
    ARCHITECTURE.md
    COMMANDS.md
    INSTALLATION.md
```

## Commands

| Command | Purpose |
|---------|---------|
| `/creo design-review <url>` | UI/UX review (responsive, WCAG AA, heuristics) |
| `/creo design-implement <report>` | Execute design fixes from review reports |
| `/creo ux-internal <flow>` | Analyze own app UX flows |
| `/creo ux-competitor <url>` | Analyze competitor websites |
| `/creo content <page-type>` | Marketing content generation |
| `/creo image-prompt <context>` | Generate image prompts |
| `/creo seo <url>` | SEO audit & optimization |
| `/creo devops <command>` | Infrastructure management |
| `/creo pipeline <command>` | CI/CD pipeline specialist |
| `/creo test <command>` | Test orchestration |
| `/creo marketing-site <command>` | Marketing site creation |
| `/creo ai-generation <command>` | AI generation pipelines |

## Development Rules

- Keep SKILL.md files under 500 lines / 5000 tokens
- Reference files should be focused and under 200 lines
- Follow kebab-case naming for all skill directories
- Agents invoked via Task tool with `context: fork`, never via Bash
- No emojis in skill or agent files
- Replace project-specific references with generic patterns
- Extensions are self-contained with own install/uninstall scripts

## Key Principles

1. **Progressive Disclosure**: Metadata always loaded, instructions on activation, references on demand
2. **Zero-Dependency Core**: Core install is pure markdown -- no Python/Node.js required
3. **Parallel Execution**: Orchestrator skills spawn subagents simultaneously
4. **Extension System**: Tools (image-gen, i18n, GSC) are optional extensions with own lifecycle
5. **Project Configuration**: Skills check `.claude/project-config.md` at runtime for customization
6. **Project Extensions**: Each skill auto-loads `.claude/skills/creo-{skill}/creo-{skill}-{project_id}.md` if it exists, letting projects inject domain knowledge without modifying Creo
