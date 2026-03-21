# Phase-Based SEO Audit Checklists

## Phase 1: Codebase Audit - Foundation Analysis

**MOST IMPORTANT PHASE** - 80% of SEO problems are visible in code.

### 1. Page Inventory & Structure Analysis
- [ ] Find all pages: `Glob **/page.tsx **/layout.tsx`
- [ ] Find markdown content: `Glob **/*.md`
- [ ] Check sitemap config: `Glob **/sitemap*.ts **/sitemap*.js`
- [ ] Analyze locale structure and route patterns
- [ ] Generate page inventory with expected URLs
- [ ] Validate page hierarchy and parent-child relationships

### 2. Framework Configuration Deep Dive
- [ ] Static export config verified
- [ ] Trailing slash configured for static export
- [ ] Image loader implemented for static export
- [ ] Compression enabled
- [ ] Build scripts verified
- [ ] i18n middleware and routing validated
- [ ] Sitemap generation configured

### 3. Metadata API Implementation
- [ ] Metadata objects in layout.tsx/page.tsx files
- [ ] Title templates with proper fallbacks
- [ ] Dynamic metadata via generateMetadata where needed
- [ ] Title length: 50-60 characters
- [ ] Meta descriptions: 150-160 characters
- [ ] Localized metadata using translation functions (not hardcoded)
- [ ] Canonical URLs include locale prefix
- [ ] Language alternates (hreflang) properly configured

### 4. Open Graph & Social Media
- [ ] OG title, description, images (1200x630px min)
- [ ] OG type, URL, site name
- [ ] Twitter card: summary_large_image
- [ ] Twitter title/description optimized

### 5. Structured Data (JSON-LD)
- [ ] Organization, Product/Service, FAQ, Breadcrumb schemas
- [ ] Valid JSON-LD syntax
- [ ] All required fields populated

### 6. Image & Media Optimization
- [ ] next/image used consistently
- [ ] Alt text on all images
- [ ] WebP/AVIF formats supported
- [ ] Responsive images, lazy loading, CLS prevention

### 7. Internal Linking & Navigation
- [ ] next/link for internal navigation
- [ ] Breadcrumb implementation
- [ ] All pages reachable within 3 clicks

---

## Phase 2: Content Quality & E-E-A-T Analysis

### Author Credibility
- [ ] Author bylines on content
- [ ] Professional credentials displayed
- [ ] Bio pages with detailed information

### Content Structure for AI Optimization
- [ ] H1 hierarchy: single H1 per page, logical H2-H6
- [ ] Direct answers in first paragraph
- [ ] FAQ sections with direct answers
- [ ] Long-tail keyword coverage

### Content Metrics
- [ ] Pillar content 1500+ words
- [ ] Appropriate reading level
- [ ] Natural keyword density (1-2%)
- [ ] Original, non-duplicated content

---

## Phase 3: Build Audit - Static Generation Analysis

### Local Build Execution
- [ ] Build completes without errors
- [ ] Zero TypeScript compilation errors
- [ ] Bundle sizes analyzed and optimized

### Static Output Analysis
- [ ] All pages from inventory generated
- [ ] All locale versions present
- [ ] Generated HTML passes validation
- [ ] Assets properly minified

### Sitemap & Robots Generation
- [ ] Sitemap includes all pages with correct priorities
- [ ] Locale sitemaps generated
- [ ] Robots.txt with proper crawler guidance

---

## Phase 4: Live Site Audit - Performance & Functionality

### Core Web Vitals
- [ ] LCP < 2.5s
- [ ] INP < 200ms
- [ ] CLS < 0.10
- [ ] TTFB < 800ms
- [ ] Performance Score: 90+ on mobile and desktop

### Mobile Optimization
- [ ] Responsive design at all breakpoints
- [ ] Touch targets 44px+ minimum
- [ ] Readable font sizes

### Schema Validation
- [ ] Google Rich Results test passed
- [ ] Rich snippets preview correctly

---

## Phase 5: Competitive Analysis - Market Position

### Competitor Technical Analysis
- [ ] Core Web Vitals comparison
- [ ] SEO implementation comparison
- [ ] Content quality and depth comparison
- [ ] Mobile experience comparison

### Content Gap Analysis
- [ ] Missing content areas identified
- [ ] Unranked high-value keywords found
- [ ] Content format gaps identified

---

## Issue Severity Classification

| Severity | Examples | Action |
|----------|---------|--------|
| **CRITICAL** | Missing metadata, CWV failures, broken hreflang, build failures | Fix immediately |
| **HIGH** | Missing alt text, suboptimal CWV, missing E-E-A-T signals | Fix this week |
| **MEDIUM** | AI search optimization, additional structured data, internal linking | Fix this month |
| **LOW** | Advanced schema, competitive gaps, additional languages | Plan for next quarter |

---

## Usage Patterns

### Full audit sequence:
1. codebase-audit -> 2. content-quality -> 3. build-audit -> 4. live-site-audit -> 5. competitive-analysis

### Maintenance checks:
- **After code changes**: codebase-audit
- **After content updates**: content-quality
- **After deployment**: live-site-audit
- **Strategic planning**: competitive-analysis
