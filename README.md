<p align="center">
  <img src="screenshots/cover-image.svg" alt="Creo — Design & Development Toolkit" width="100%" />
</p>

<p align="center">
  AI-powered design, UX, content, DevOps, and testing toolkit for <a href="https://claude.com/claude-code">Claude Code</a>.
  <br />
  12 specialized skills, 12 parallel subagents, and 3 optional extensions.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT License" /></a>
  <a href="https://github.com/oyusypenko/creo"><img src="https://img.shields.io/badge/Claude_Code-Skill-6366f1" alt="Claude Code Skill" /></a>
  <a href="https://github.com/oyusypenko/creo/stargazers"><img src="https://img.shields.io/github/stars/oyusypenko/creo?style=social" alt="GitHub Stars" /></a>
  <a href="https://github.com/oyusypenko/creo/releases"><img src="https://img.shields.io/github/v/release/oyusypenko/creo" alt="Latest Release" /></a>
</p>

---

## Why Creo?

**Without Creo:** You manually check responsive layouts, accessibility, SEO tags, write marketing copy, configure CI/CD, and set up tests -- each requiring different tools and expertise.

**With Creo:** One toolkit handles all of it. Run `/creo design-review` and get a full responsive + WCAG + heuristic audit. Run `/creo seo` for a complete SEO analysis. Run `/creo marketing-site full` to orchestrate an entire marketing site build with content, SEO, design review, localization, and QA -- all in parallel.

- Zero dependencies -- pure markdown, one-liner install
- 12 skills run as parallel subagents for speed
- Works with Claude Code, compatible with Codex, Cursor, and Gemini CLI

## Features

- **Design Review** -- Responsive testing (375-1920px), WCAG AA accessibility, Nielsen's 10 heuristics, visual polish
- **Design Implementation** -- Execute fixes from review reports with verified code changes
- **UX Analysis** -- Analyze your own app flows (internal) or competitor websites (external)
- **Marketing Content** -- JTBD framework, customer pain points, i18n-ready JSON output
- **Image Prompts** -- Generate optimized prompts for DALL-E 3, Midjourney, Stable Diffusion XL
- **SEO Audit** -- Technical SEO, meta tags, structured data, sitemap, content optimization
- **DevOps** -- GitHub, Cloudflare, Railway, Stripe CLI operations via specialized subagents
- **CI/CD Pipelines** -- GitHub Actions workflow creation, debugging, optimization
- **Testing** -- Unit (Vitest/Jest) and E2E (Playwright) test orchestration
- **Marketing Site** -- 7-stage orchestrated site creation (content, SEO, design, localization, QA)
- **AI Generation** -- LLM pipeline expertise (prompt engineering, validation, queues, SSE)

## Quick Start

### Install (Unix/macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/oyusypenko/creo/main/install.sh | bash
```

### Install (Windows)

```powershell
irm https://raw.githubusercontent.com/oyusypenko/creo/main/install.ps1 | iex
```

### Install (Git Clone)

```bash
git clone https://github.com/oyusypenko/creo.git
cd creo
./install.sh
```

<!-- TODO: Add terminal demo GIF here once recorded with asciinema/vhs -->

### Usage

```
claude                                          # Start Claude Code
/creo design-review http://localhost:3000       # Review a page
/creo content landing                           # Generate landing page copy
/creo seo audit https://example.com             # SEO audit
/creo test unit                                 # Run unit tests
/creo marketing-site full                       # Build full marketing site
```

## Updating

Creo stamps the installed commit SHA to `~/.claude/skills/creo/.version` and ships both an updater and a non-blocking update check.

### Update to latest

**Unix/macOS:**

```bash
curl -fsSL https://raw.githubusercontent.com/oyusypenko/creo/main/update.sh | bash
# or, if already installed:
~/.claude/skills/creo/update.sh
```

**Windows:**

```powershell
irm https://raw.githubusercontent.com/oyusypenko/creo/main/update.ps1 | iex
```

The updater runs `uninstall.sh` first so removed files are actually cleaned up, then reinstalls from `main`.

### Auto-notify on Claude Code startup

Add a `SessionStart` hook in `.claude/settings.json` (project or user level) to check for updates when Claude Code starts. Silent on success, prints a one-line warning when an update is available. Never blocks or fails the session.

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "bash ~/.claude/skills/creo/update-check.sh"
      }]
    }]
  }
}
```

Windows:

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "powershell -ExecutionPolicy Bypass -File %USERPROFILE%/.claude/skills/creo/update-check.ps1"
      }]
    }]
  }
}
```

The check fetches the latest commit on `main` from the GitHub API (3s timeout, falls back to `git ls-remote`) and compares against the installed `.version`. Offline and rate-limited cases exit silently.

**Environment overrides** (rarely needed):

- `CREO_REPO` — repo slug (default: `oyusypenko/creo`)
- `CREO_SKILL_DIR` — install location (default: `~/.claude/skills/creo`)
- `CREO_TIMEOUT` — curl timeout in seconds (default: `3`)

## Project Extensions

Teach any Creo skill about your project's domain, conventions, and file paths without modifying Creo itself. Extensions live inside your project repo at `.claude/skills/creo-{skill}/creo-{skill}-{project_id}.md` and are loaded automatically at the start of every skill run.

**How it works:**

1. Set `project_id: "my-project"` in `.claude/project-config.md`
2. Create `.claude/skills/creo-{skill}/creo-{skill}-{project_id}.md` for any skill you want to customize
3. Creo skills auto-load the matching extension before doing work

**Example layout in your project:**

```
.claude/
├── project-config.md                                     # project_id, URLs, locales, etc.
└── skills/
    ├── creo-design-review/
    │   └── creo-design-review-my-project.md              # Design tokens, component rules
    ├── creo-pipeline/
    │   └── creo-pipeline-my-project.md                   # CI/CD ports, services, deploy targets
    ├── creo-seo/
    │   └── creo-seo-my-project.md                        # Keyword strategy, sitemap paths
    ├── creo-ai-generation/
    │   └── creo-ai-generation-my-project.md              # Zod schemas, prompts, queue names
    └── creo-unit-test/
        └── creo-unit-test-my-project.md                  # Test utilities, factories, mocks
```

**What extensions can contain:**

- Domain terminology and glossary (entity names, business concepts)
- File path conventions specific to your monorepo
- Tech stack specifics (Zod schemas, database tables, queue names)
- Design tokens and component standards
- CI/CD infrastructure (services, ports, secrets, deploy targets)
- Test utilities, factories, mock patterns, page objects
- Brand voice, tone, target audience, JTBD framing
- Competitor lists and positioning notes

**Why it matters:**

Upstream Creo skills stay generic and reusable across any codebase. Your project-specific knowledge lives in your repo, survives Creo updates, and stays version-controlled alongside the code it describes. The same pattern works for all 12 skills plus DevOps subagents (GitHub/Cloudflare/Railway/Stripe CLI).

## Compatibility

Creo skills use the standard SKILL.md format, making them compatible with:
- **Claude Code** (primary, fully tested)
- **Codex CLI** (OpenAI)
- **Cursor** (via agent skills)
- **Gemini CLI** (Google)

## Commands

| Command | Purpose |
|---------|---------|
| `/creo design-review <url>` | UI/UX review (responsive, WCAG AA, heuristics) |
| `/creo design-implement <report>` | Execute design fixes from review reports |
| `/creo ux-internal <flow>` | Analyze your own app's UX flows |
| `/creo ux-competitor <url>` | Analyze competitor websites |
| `/creo content <page-type>` | Generate marketing copy (JTBD, pain points) |
| `/creo image-prompt <context>` | Generate image prompts for AI models |
| `/creo seo <url>` | SEO audit & optimization |
| `/creo devops <command>` | Infrastructure (GitHub/Cloudflare/Railway/Stripe) |
| `/creo pipeline <command>` | CI/CD pipeline specialist (GitHub Actions) |
| `/creo test <command>` | Test orchestration (unit + E2E) |
| `/creo marketing-site <command>` | Full marketing site creation (7-stage) |
| `/creo ai-generation <command>` | AI generation pipeline expertise |

## Standalone Skills

Need just one skill? Each is available as a standalone install under [creo-kit](https://github.com/creo-kit):

| Skill | Repository | Install |
|-------|------------|---------|
| **SEO Audit** | [claude-seo-audit](https://github.com/creo-kit/claude-seo-audit) | `curl -fsSL https://raw.githubusercontent.com/creo-kit/claude-seo-audit/main/install.sh \| bash` |
| **Design Review** | [claude-design-review](https://github.com/creo-kit/claude-design-review) | `curl -fsSL https://raw.githubusercontent.com/creo-kit/claude-design-review/main/install.sh \| bash` |
| **Design Implement** | [claude-design-implement](https://github.com/creo-kit/claude-design-implement) | `curl -fsSL https://raw.githubusercontent.com/creo-kit/claude-design-implement/main/install.sh \| bash` |
| **UX Audit** | [claude-ux-audit](https://github.com/creo-kit/claude-ux-audit) | `curl -fsSL https://raw.githubusercontent.com/creo-kit/claude-ux-audit/main/install.sh \| bash` |
| **Competitor Analysis** | [claude-competitor-analysis](https://github.com/creo-kit/claude-competitor-analysis) | `curl -fsSL https://raw.githubusercontent.com/creo-kit/claude-competitor-analysis/main/install.sh \| bash` |
| **Marketing Content** | [claude-marketing-content](https://github.com/creo-kit/claude-marketing-content) | `curl -fsSL https://raw.githubusercontent.com/creo-kit/claude-marketing-content/main/install.sh \| bash` |
| **Image Prompt** | [claude-image-prompt](https://github.com/creo-kit/claude-image-prompt) | `curl -fsSL https://raw.githubusercontent.com/creo-kit/claude-image-prompt/main/install.sh \| bash` |
| **DevOps Toolkit** | [claude-devops-toolkit](https://github.com/creo-kit/claude-devops-toolkit) | `curl -fsSL https://raw.githubusercontent.com/creo-kit/claude-devops-toolkit/main/install.sh \| bash` |
| **CI/CD Pipeline** | [claude-ci-pipeline](https://github.com/creo-kit/claude-ci-pipeline) | `curl -fsSL https://raw.githubusercontent.com/creo-kit/claude-ci-pipeline/main/install.sh \| bash` |
| **Test Orchestrator** | [claude-test-orchestrator](https://github.com/creo-kit/claude-test-orchestrator) | `curl -fsSL https://raw.githubusercontent.com/creo-kit/claude-test-orchestrator/main/install.sh \| bash` |
| **Marketing Site** | [claude-marketing-site](https://github.com/creo-kit/claude-marketing-site) | `curl -fsSL https://raw.githubusercontent.com/creo-kit/claude-marketing-site/main/install.sh \| bash` |
| **AI Generation** | [claude-ai-generation](https://github.com/creo-kit/claude-ai-generation) | `curl -fsSL https://raw.githubusercontent.com/creo-kit/claude-ai-generation/main/install.sh \| bash` |

> Install the full Creo toolkit to get all 12 skills at once, or pick individual ones above.

## Optional Extensions

Extensions add tool-backed capabilities. Each is self-contained with its own install/uninstall.

| Extension | What it adds | Requirements |
|-----------|-------------|--------------|
| **image-generation** | DALL-E 3 & ComfyUI image generation | Node.js 18+, OPENAI_API_KEY |
| **i18n-translator** | Batch JSON translation (39+ languages) | Python 3, LM Studio |
| **gsc-analyzer** | Google Search Console analysis (15+ analyzers) | Python 3, Google service account |

### Install an extension

```bash
# After cloning the repo:
./extensions/image-generation/install.sh
./extensions/i18n-translator/install.sh
./extensions/gsc-analyzer/install.sh
```

Extension commands become available after install:
- `/creo image-generation generate` -- Generate marketing images
- `/creo i18n translate en uk,pl,de` -- Batch translate locales
- `/creo gsc full-seo https://example.com` -- Full GSC analysis

## Architecture

```
creo/
├── creo/SKILL.md                  # Main orchestrator (entry point)
├── creo/references/               # 12 on-demand knowledge files
├── skills/                        # 12 sub-skills
├── agents/                        # 12 parallel subagents
├── extensions/                    # 3 optional extensions
│   ├── image-generation/          # Node.js (DALL-E 3, ComfyUI)
│   ├── i18n-translator/           # Python (LM Studio)
│   └── gsc-analyzer/              # Python (Google Search Console)
├── install.sh / install.ps1       # One-liner installers
└── uninstall.sh / uninstall.ps1   # Clean removal
```

## Requirements

- [Claude Code](https://claude.com/claude-code) CLI
- Git (for installation)
- Extensions have additional requirements (see extension READMEs)

## Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/oyusypenko/creo/main/uninstall.sh | bash
```

Extensions must be uninstalled separately via their own uninstall scripts.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) -- System design overview
- [Commands](docs/COMMANDS.md) -- Full command reference
- [Installation](docs/INSTALLATION.md) -- Detailed install guide

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE)
