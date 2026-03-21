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
| `/creo seo audit <url>` | Full SEO audit |
| `/creo seo technical <url>` | Technical SEO checks |
| `/creo seo content <url>` | Content quality analysis |
| `/creo seo schema <url>` | Structured data validation |

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
