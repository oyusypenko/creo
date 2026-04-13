# Marketplace Publishing Plan

Plan for publishing `creo` to the official Claude Code plugin marketplace.

## Why publish?

Anthropic's plugin marketplace has **no monetization** — no paid plugins, no revenue share. Publishing is worth it for:

1. **Distribution / reach** — one-click install via `/plugin install creo` vs. "clone this repo and copy files"
2. **Reputation & portfolio** — public proof of craft; useful for hiring, consulting, speaking, audience-building
3. **Top-of-funnel for paid products** — free plugin → SaaS / Pro tier / agency services upsell
4. **Community feedback loop** — issues and PRs surface bugs and missing features
5. **Dogfooding forcing-function** — publishing raises the quality bar on docs, versioning, and breaking-change discipline
6. **Fun / craft** — legitimate reason on its own

### When NOT to publish

- The plugin is tightly coupled to one project's conventions
- You don't want the support burden (issues, questions, maintenance)
- The skills are trade secrets or client-specific

## Current state

The repo is already structured as a plugin:

- `.claude-plugin/plugin.json` — manifest present (`name`, `version: 1.0.0`, `description`, `author`, `license`, `homepage`, `skills[]`, `agents[]`)
- `skills/` — 12 sub-skills (creo-design-review, creo-seo, creo-content, creo-devops, creo-pipeline, creo-test, etc.)
- `agents/` — corresponding specialized agents
- `LICENSE` (MIT), `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`
- Install scripts: `install.sh`, `install.ps1`, `update.sh`, `uninstall.sh`

## What's needed to publish

### 1. Manifest audit — `.claude-plugin/plugin.json`

- [ ] Confirm `name`, `version`, `description`, `author`, `homepage`, `repository`, `license` are accurate
- [ ] Add `keywords` array (e.g. `["design", "seo", "devops", "testing", "ux", "nextjs", "wcag", "jtbd"]`) if missing — improves discoverability
- [ ] Confirm every path in `skills[]` and `agents[]` resolves to an existing file
- [ ] Pin to semver discipline: `PATCH` for fixes, `MINOR` for new skills, `MAJOR` for breaking changes

### 2. README polish

The README is what users see before installing — it makes or breaks adoption.

- [ ] Clear one-liner above the fold
- [ ] Install command (`/plugin install creo`) front and center
- [ ] Screenshots or GIF demos of at least the headline skills (design-review, seo, content)
- [ ] Full skill index with a one-line description each
- [ ] Quick-start example for 2–3 top skills
- [ ] Link to per-skill docs

### 3. Audit skills for project-specific leaks

Decouple from any single project's conventions before public release.

- [ ] Remove hardcoded references to Railway, Cloudflare project IDs, tier systems, env var names, file paths specific to a client/project
- [ ] Replace domain-specific examples with generic ones (or mark them as "example")
- [ ] Confirm no private tokens, URLs, or client names in SKILL.md files

### 4. Quality gates

- [ ] Every skill has a `SKILL.md` with: purpose, trigger keywords, inputs, outputs, example
- [ ] Every agent has a matching agent file under `agents/`
- [ ] `CHANGELOG.md` entry for `1.0.0` (or whatever version gets submitted)
- [ ] `LICENSE` present (MIT — already done)

### 5. Submission

1. Push branch / merge to `main`
2. Ensure GitHub repo is **public**
3. Submit via the plugin submission form:
   - `https://platform.claude.com/plugins/submit` or
   - `https://claude.ai/settings/plugins/submit`
4. Fill in: plugin name (`creo`), description, GitHub URL, version
5. Anthropic reviews for quality and safety
6. On approval: plugin appears in official marketplace; users install with `/plugin install creo`

### 6. Post-publish

- [ ] Monitor issues / discussions on the GitHub repo
- [ ] Follow semantic versioning on every release
- [ ] Tag releases (`git tag v1.0.0 && git push --tags`) so users can pin versions
- [ ] Update `CHANGELOG.md` on every release
- [ ] Consider adding a `docs/` page per skill for deep-dive documentation

## Minimum viable checklist

- [ ] `.claude-plugin/plugin.json` audit + `keywords` added
- [ ] README has install command, skill index, and at least one screenshot/GIF
- [ ] Project-specific leaks audited across all SKILL.md files
- [ ] `CHANGELOG.md` updated for the submitted version
- [ ] GitHub repo is public
- [ ] Submission form filled at `platform.claude.com/plugins/submit`

## References

- Plugins: https://code.claude.com/docs/en/plugins.md
- Plugin marketplaces: https://code.claude.com/docs/en/plugin-marketplaces.md
- Plugins reference: https://code.claude.com/docs/en/plugins-reference.md

## Alternative: custom marketplace

If you'd rather distribute privately (e.g. to an agency's team or paying clients), skip the official submission and publish a `marketplace.json` on GitHub listing `creo`. Teams add the marketplace URL in Claude Code settings and install from there. Good fit for team-internal distribution or gated commercial use.