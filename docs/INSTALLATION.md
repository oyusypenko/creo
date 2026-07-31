# Installation Guide

## Prerequisites

- [Claude Code](https://claude.com/claude-code) CLI installed
- Git

## Plugin Installation (recommended)

Creo is distributed as a Claude Code plugin through its own marketplace
(`.claude-plugin/marketplace.json` in this repository).

Inside Claude Code:

```
/plugin marketplace add oyusypenko/creo
/plugin install creo@creo
```

Or from the terminal:

```bash
claude plugin marketplace add oyusypenko/creo
claude plugin install creo@creo
```

This installs the orchestrator, all sub-skills, and all subagents in one step.
Update later with `/plugin marketplace update creo`. Uninstall with
`claude plugin uninstall creo`.

Do not combine the plugin install with the script install below -- pick one,
otherwise skills appear twice.

## Codex Installation

Codex (OpenAI) supports the same [Agent Skills](https://agentskills.io) format.
Either install the skills directly:

```bash
npx skills add oyusypenko/creo
```

or add this repository as a Codex plugin marketplace (Codex reads
`.claude-plugin/marketplace.json`):

```bash
codex plugin marketplace add oyusypenko/creo
```

Subagents (`agents/*.md`) are Claude Code-specific and are not installed in
Codex; the skills cover the same workflows.

## Script Installation (alternative)

The script install copies skills and agents into `~/.claude/` directly. It is
zero-dependency (pure markdown skills and agents).

### Unix/macOS (one-liner)

```bash
curl -fsSL https://raw.githubusercontent.com/oyusypenko/creo/main/install.sh | bash
```

### Windows (one-liner)

```powershell
irm https://raw.githubusercontent.com/oyusypenko/creo/main/install.ps1 | iex
```

### From source

```bash
git clone https://github.com/oyusypenko/creo.git
cd creo
./install.sh    # Unix/macOS
# or
.\install.ps1   # Windows
```

### What gets installed

```
~/.claude/skills/creo/              # Main skill + references
~/.claude/skills/creo-*/            # 12 sub-skills
~/.claude/agents/creo-*.md          # 12 subagents
```

## Extension Installation

Extensions are optional. Install only what you need.

### Image Generation

Adds DALL-E 3 and ComfyUI image generation.

**Requirements:** Node.js 18+, OPENAI_API_KEY (for DALL-E 3)

```bash
cd creo
./extensions/image-generation/install.sh
```

### i18n Translator

Adds batch JSON translation via local LLM.

**Requirements:** Python 3, [LM Studio](https://lmstudio.ai/) running on port 1234

```bash
cd creo
./extensions/i18n-translator/install.sh
```

### GSC Analyzer

Adds Google Search Console analysis with 15+ analyzers.

**Requirements:** Python 3, Google service account JSON key (for GSC API)

```bash
cd creo
./extensions/gsc-analyzer/install.sh
```

## Uninstallation

### Core

```bash
curl -fsSL https://raw.githubusercontent.com/oyusypenko/creo/main/uninstall.sh | bash
```

### Extensions (uninstall separately)

```bash
cd creo
./extensions/image-generation/uninstall.sh
./extensions/i18n-translator/uninstall.sh
./extensions/gsc-analyzer/uninstall.sh
```

## Troubleshooting

### Skills not appearing after install

Restart Claude Code after installation. Skills are loaded at startup.

### Extension install fails

Check that prerequisites are met (Node.js, Python, etc.). Extension install scripts check for Creo core first -- install core before extensions.

### Permission denied on install scripts

```bash
chmod +x install.sh
./install.sh
```
