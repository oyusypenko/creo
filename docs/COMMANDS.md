# Command Reference

## Core Commands

### Design & UX

| Command | Description |
|---------|-------------|
| `/creo design-review <url>` | Full UI/UX review: responsive (375-1920px), WCAG AA, Nielsen's heuristics |
| `/creo design-review mobile <url>` | Mobile-focused review (375px, 768px) |
| `/creo design-review a11y <url>` | Accessibility-focused review |
| `/creo design-implement <report>` | Implement fixes from a design review report |
| `/creo design-implement auto` | Auto-detect latest report and implement fixes |
| `/creo ux-internal <flow>` | Analyze a specific UX flow in your app |
| `/creo ux-internal full` | Full UX audit of your application |
| `/creo ux-competitor <url>` | Analyze a competitor website |
| `/creo ux-competitor compare <url1> <url2>` | Compare two competitors |

### Content & Marketing

| Command | Description |
|---------|-------------|
| `/creo content landing` | Generate landing page copy |
| `/creo content feature` | Generate feature page copy |
| `/creo content pricing` | Generate pricing page copy |
| `/creo content <page-type>` | Generate copy for any page type |
| `/creo image-prompt hero` | Generate hero image prompts |
| `/creo image-prompt feature` | Generate feature illustration prompts |
| `/creo image-prompt batch` | Batch generate prompts for all pages |

### SEO

| Command | Description |
|---------|-------------|
| `/creo seo onboard <url>` | Full lifecycle: audit, plan, guided GSC setup, monitoring, cadence |
| `/creo seo plan <url>` | Audit + prioritized implementation plan (DEV/YOU tagged) |
| `/creo seo init` | Scan codebase, cache project profile |
| `/creo seo audit <url>` | Full 7-phase SEO + GEO audit |
| `/creo seo audit --brief <url>` | Fast audit (technical + build + live + scoring) |
| `/creo seo technical <url>` | Technical SEO checks |
| `/creo seo content <url>` | Content quality analysis |
| `/creo seo schema <url>` | Structured data validation |
| `/creo seo sitemap` | Sitemap audit + generation recommendations |
| `/creo seo citability <url>` | Passage-level AI citability score |
| `/creo seo llms-txt [--generate]` | Validate or generate /llms.txt |
| `/creo seo crawlers [--fix]` | AI crawler robots.txt audit |
| `/creo seo compare <old> <new>` | Delta between two prior audits |
| `/creo seo autofix [--dry-run]` | Closed-loop GSC remediation (allowlist + ledger + verify) |
| `/creo seo triage <bucket>` | Triage a GSC coverage bucket (expected vs concern) |
| `/creo seo semantic-core` | Focused query core with noise filter and P0-P3 priorities |
| `/creo seo freshness` | Freshness-signal divergence + year-staleness audit |
| `/creo seo offpage` | Off-page authority plan + trust-killer sweep |
| `/creo seo weekly [--setup]` | Weekly rank/LLM-citability snapshot (read or scaffold) |
| `/creo seo page-rules` | Generate project-scoped page-creation SEO rules |

### DevOps

| Command | Description |
|---------|-------------|
| `/creo devops deploy` | Deploy application |
| `/creo devops github <cmd>` | GitHub CLI operations (PRs, Issues, Actions) |
| `/creo devops cloudflare <cmd>` | Cloudflare operations (Workers, Pages, R2, D1, KV) |
| `/creo devops railway <cmd>` | Railway operations (projects, services, deployments) |
| `/creo devops stripe <cmd>` | Stripe operations (payments, subscriptions, webhooks) |

### CI/CD

| Command | Description |
|---------|-------------|
| `/creo pipeline create` | Create GitHub Actions workflow |
| `/creo pipeline debug` | Debug failing workflow |
| `/creo pipeline optimize` | Optimize workflow (caching, matrix builds) |

### Testing

| Command | Description |
|---------|-------------|
| `/creo test unit` | Run/create unit tests (Vitest/Jest) |
| `/creo test e2e` | Run/create E2E tests (Playwright) |
| `/creo test plan` | Create test plan |
| `/creo test coverage` | Analyze test coverage |

### Performance

| Command | Description |
|---------|-------------|
| `/creo perf init` | Scaffold `.claude/skills/creo-perf/`, detect the stack, fill targets, propose scenarios, verify with preflight |
| `/creo perf preflight` | Check tools, targets, DB access, scenarios, SQL mode |
| `/creo perf baseline [label]` | Full immutable capture sweep (platform, schema, scenarios, fe, workload) |
| `/creo perf audit [baseline\|after\|discover]` | Six-layer findings report via the `creo-perf-audit` subagent |
| `/creo perf optimize [finding]` | Fix loop: one concern, re-measure, verify correctness, commit |
| `/creo perf scenario <id> <label>` | Re-capture one scenario |
| `/creo perf fe <label>` | Initial load / build / Lighthouse capture |
| `/creo perf platform <label>` / `schema <label>` | Config-fact captures |
| `/creo perf workload <label>` | pg_stat_statements discovery window |
| `/creo perf after <label> [ids]` | Re-measure touched scenarios and show deltas |
| `/creo perf dashboard` | Rebuild `results/dashboard.md` |
| `/creo perf report` | SOLUTION-style per-finding write-up from the dashboard |
| `/creo perf observability [--teardown]` | Enable or revert pg_stat_statements + auto_explain + hypopg |

### Orchestration

| Command | Description |
|---------|-------------|
| `/creo marketing-site full` | Full 7-stage marketing site creation |
| `/creo marketing-site content` | Content generation stage only |
| `/creo marketing-site review` | Design review stage only |
| `/creo ai-generation debug` | Debug AI generation pipeline |
| `/creo ai-generation optimize` | Optimize prompts and flows |
| `/creo ai-generation pipeline` | Design generation pipeline architecture |

## Extension Commands

Available after installing the corresponding extension.

### Image Generation (requires extension)

| Command | Description |
|---------|-------------|
| `/creo image-generation generate` | Generate images using DALL-E 3 or ComfyUI |
| `/creo image-generation estimate` | Estimate generation costs |
| `/creo image-generation optimize` | Optimize existing images |
| `/creo image-generation comfyui` | Generate via local ComfyUI |

### i18n Translator (requires extension)

| Command | Description |
|---------|-------------|
| `/creo i18n translate <src> <targets>` | Batch translate JSON locales |
| `/creo i18n validate` | Validate translation structure |
| `/creo i18n status` | Check translation coverage |

### GSC Analyzer (requires extension)

| Command | Description |
|---------|-------------|
| `/creo gsc list-sites` | List GSC properties |
| `/creo gsc inspect <url>` | Inspect URL in GSC |
| `/creo gsc analytics` | Search analytics report |
| `/creo gsc full-seo <url>` | Full page SEO analysis |
| `/creo gsc site-audit <url>` | Site-wide audit (up to 500 pages) |
| `/creo gsc security <url>` | Security headers check |
| `/creo gsc schema <url>` | Schema markup validation |
| `/creo gsc hreflang <url>` | Hreflang tag validation |
| `/creo gsc ui-export` | Export GSC Page-Indexing drilldown CSVs (UI-only data) |
| `/creo gsc validate-fix` | Trigger GSC "Validate Fix" for issue classes (UI-only action) |
| `/creo gsc open [<surface>]` | Open a GSC report in the user's browser and operate it (browser-first) |

### Perf Harness (requires extension)

Scripts behind `/creo perf`, callable directly through the project wrapper written by `/creo perf init`:

| Command | Description |
|---------|-------------|
| `.claude/skills/creo-perf/perf preflight` | Tools, targets, scenarios |
| `.claude/skills/creo-perf/perf audit-all <label>` | Every capture in configured order + workload window |
| `.claude/skills/creo-perf/perf audit-scenario <id> <label> [--runs N] [--force]` | One scenario capture |
| `.claude/skills/creo-perf/perf audit-fe <label> [--skip-build] [--skip-composition]` | Assets, build, composition, Lighthouse |
| `.claude/skills/creo-perf/perf audit-platform <label>` | Backend + PostgreSQL config facts |
| `.claude/skills/creo-perf/perf audit-schema <label>` | Tables, columns, indexes, hypopg verdicts |
| `.claude/skills/creo-perf/perf observability-setup [--with-hypopg]` | Enable pg_stat_statements + auto_explain (restarts DB) |
| `.claude/skills/creo-perf/perf workload-pre` / `workload-drive` / `workload-post <label> [--teardown]` | Discovery window lifecycle |
| `.claude/skills/creo-perf/perf dashboard` | Rebuild `results/dashboard.md` |
