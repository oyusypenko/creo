# Workflow Stages - Marketing Site Creation

Detailed checklists for each stage of marketing site creation.

---

## Stage 1: Infrastructure

### 1.1 Project Creation

```bash
mkdir marketing-site && cd marketing-site
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*"
```

**Checklist:**
- [ ] `app/` directory exists
- [ ] `tailwind.config.ts` exists
- [ ] `tsconfig.json` configured
- [ ] `package.json` has correct dependencies

### 1.2 Copy Reference Components

Copy base components from reference project (see project config for paths).

### 1.3 i18n Setup

```
i18n/
  config.ts              # LANGS, DEFAULT_LANG
  request.ts             # getRequestConfig
  routing.ts             # createNavigation
  navigation.ts          # Link, useRouter
  components/
    LanguageSwitcher.tsx
```

**Checklist:**
- [ ] LANGS defined
- [ ] getRequestConfig works
- [ ] LanguageSwitcher renders
- [ ] Routes include [locale]

### 1.4 UI Component Library Setup

```bash
npx shadcn@latest init
npx shadcn@latest add button card badge accordion tabs dialog dropdown-menu navigation-menu sheet separator input textarea select table
```

### 1.5 SEO Setup

Create `app/robots.ts`, `app/sitemap.ts`, `app/manifest.ts`.

### Quality Gate 1
- [ ] Build succeeds with no errors
- [ ] No TypeScript errors
- [ ] Home page renders

---

## Stage 2: Content Generation

### 2.1 Directory Structure

```
messages/
  en/
    core/
      brand.json, common.json, navigation.json, footer.json, errors.json
    pages/
      landing.json, pricing.json, features/, use-cases/, sources/, resources/
```

### 2.2 Content Generation

Call `creo-content-strategist` with project-specific configuration:
- Core content (brand, navigation, common)
- Feature pages
- Use case pages
- Resource pages

### Quality Gate 2
- [ ] All JSON files created
- [ ] All pass schema validation
- [ ] No duplicate keys

---

## Stage 3: Page Components

### 3.1 Section Components

| Component | Description |
|-----------|-------------|
| HeroSection | Page hero with CTA |
| PainPointsSection | Problem/solution pairs |
| FeaturesSection | Feature grid |
| HowItWorksSection | Step-by-step |
| BenefitsSection | Benefits list |
| ComparisonSection | Comparison table |
| TestimonialSection | Quote card |
| FAQSection | Accordion FAQ |
| CTASection | Final call to action |

### 3.2 UnifiedPage Component

Create a unified page component that assembles sections based on content.

### 3.3 Dynamic Route Pages

```
app/[locale]/
  features/[slug]/page.tsx
  use-cases/[slug]/page.tsx
  resources/[slug]/page.tsx
```

### Quality Gate 3
- [ ] All section components render
- [ ] UnifiedPage assembles correctly
- [ ] Dynamic routes work
- [ ] i18n displays translations

---

## Stage 4: SEO Optimization

Run `creo-seo` codebase-audit. Add JSON-LD to each page type. Ensure every page has unique title (50-60 chars), meta description (150-160 chars), canonical URL. Configure AI bot access in robots.ts.

### Quality Gate 4
- [ ] All pages have unique titles and descriptions
- [ ] JSON-LD validates
- [ ] Sitemap includes all pages

---

## Stage 5: Design Review

Run `creo-design-review`. Test at 375px, 768px, 1440px, 1920px. Check color contrast >= 4.5:1, touch targets >= 44x44px, focus states, alt text, keyboard navigation.

If issues found, run `creo-design-implement`.

### Quality Gate 5
- [ ] No critical issues in report
- [ ] WCAG 2.1 AA compliance
- [ ] No horizontal scroll on mobile

---

## Stage 6: Localization

Call `creo-content-strategist` with locale parameter. Verify key parity across all locales.

### Quality Gate 6
- [ ] All JSON files in each locale
- [ ] Key parity verified
- [ ] Text fits UI (no overflow)

---

## Stage 7: Final QA

```bash
npm run build  # Must pass with no errors
```

### Lighthouse Targets

| Metric | Target |
|--------|--------|
| Performance | >= 90 |
| Accessibility | >= 90 |
| Best Practices | >= 90 |
| SEO | >= 90 |

Run final SEO audit via `creo-seo`.

### Quality Gate 7
- [ ] Build succeeds
- [ ] No broken links
- [ ] Lighthouse >= 90 all categories
- [ ] Ready for production

---

## Progress Tracking

```
| Stage | Status | Started | Completed |
|-------|--------|---------|-----------|
| 1. Infrastructure | -- | [date] | [date] |
| 2. Content | -- | [date] | [date] |
| 3. Components | -- | [date] | [date] |
| 4. SEO | -- | [date] | [date] |
| 5. Design Review | -- | [date] | [date] |
| 6. Localization | -- | [date] | [date] |
| 7. Final QA | -- | [date] | [date] |
```
