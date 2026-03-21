# Contributing to Creo

Thank you for your interest in contributing to Creo.

## Reporting Bugs

Open a GitHub issue with:
- Operating system and version
- Python/Node.js version (if using extensions)
- The `/creo` command you ran
- Full error output
- Steps to reproduce

## Suggesting Features

Open a GitHub Discussion with your idea. Include:
- What problem it solves
- Which domain it belongs to (design, content, SEO, DevOps, testing)
- Whether it should be a core skill or an extension

## Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test your changes (run the relevant `/creo` commands)
5. Submit a pull request

## Development Setup

```bash
git clone https://github.com/oyusypenko/creo.git
cd creo
# Core is pure markdown -- no build step needed
# For extensions, see their individual README.md files
```

## Guidelines

- SKILL.md files must stay under 500 lines
- Reference files must stay under 200 lines
- Agent files must stay under 200 lines
- Use kebab-case for all directory and file names
- No emojis in skill or agent files
- Keep dependencies minimal -- extensions should be self-contained
- All shell scripts must use `set -euo pipefail`
- Python scripts should output JSON and accept CLI arguments
