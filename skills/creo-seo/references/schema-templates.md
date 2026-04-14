# JSON-LD Schema Templates for Next.js

Canonical JSON-LD templates for Next.js apps. Inline as `<script type="application/ld+json">` in layouts/pages, or via Metadata API.

## Rendering pattern (App Router)

```tsx
// app/page.tsx or app/layout.tsx
export default function Page() {
  const jsonLd = { "@context": "https://schema.org", "@type": "Article", "headline": "..." }
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, '\\u003c') }}
      />
      {/* page content */}
    </>
  )
}
```

Always escape `<` to `\u003c` to prevent `</script>` injection.

## Schema catalog by page type

| Page type | Primary schema | Complementary |
|-----------|---------------|---------------|
| Homepage | Organization + WebSite | sameAs, SearchAction |
| About | Organization, Person | AboutPage |
| Product | Product | Offer, AggregateRating, Review, MerchantReturnPolicy |
| Pricing | Product or Offer catalog | — |
| Blog post | Article / NewsArticle / BlogPosting | Person (author), BreadcrumbList |
| FAQ | FAQPage (restricted: only gov/health/consumer) | — |
| How-to | HowTo (**deprecated Sept 2023 for rich results** — still valid markup) | — |
| Recipe | Recipe | VideoObject, AggregateRating |
| Event | Event | Offer, Place, VirtualLocation |
| Course | Course | CourseInstance |
| Job | JobPosting | Organization |
| Video | VideoObject | Clip, BroadcastEvent, SeekToAction |
| Local business | LocalBusiness (+ subtype) | PostalAddress, GeoCoordinates, OpeningHoursSpecification |
| Vacation rental | VacationRental | LocationFeatureSpecification |
| Profile | ProfilePage | Person |
| Discussion/forum | DiscussionForumPosting | Comment |
| App | SoftwareApplication / MobileApplication | AggregateRating, Offer |
| Dataset | Dataset | DataDownload |
| Quiz | Quiz | Question |
| Comparison/alternatives | ItemList + Product | — |
| Search results | WebSite + SearchAction | — |
| Breadcrumbs | BreadcrumbList | — |

## Core templates

### Organization (homepage, footer)

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Acme Corp",
  "url": "https://acme.com",
  "logo": "https://acme.com/logo.png",
  "sameAs": [
    "https://twitter.com/acme",
    "https://linkedin.com/company/acme",
    "https://github.com/acme",
    "https://youtube.com/@acme"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+1-555-0123",
    "contactType": "customer support",
    "availableLanguage": ["en", "es"]
  }
}
```

### WebSite with SearchAction (homepage)

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Acme",
  "url": "https://acme.com",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://acme.com/search?q={search_term_string}",
    "query-input": "required name=search_term_string"
  }
}
```

### Article / BlogPosting / NewsArticle

```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Title (max 110 chars)",
  "description": "Summary",
  "image": ["https://acme.com/hero.jpg"],
  "datePublished": "2026-04-14T08:00:00+00:00",
  "dateModified": "2026-04-14T08:00:00+00:00",
  "author": {
    "@type": "Person",
    "name": "Jane Doe",
    "url": "https://acme.com/author/jane-doe"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Acme",
    "logo": { "@type": "ImageObject", "url": "https://acme.com/logo.png" }
  },
  "mainEntityOfPage": { "@type": "WebPage", "@id": "https://acme.com/post" }
}
```

`dateModified` defaults to `datePublished` if missing. Use `@type: "NewsArticle"` for news, `"Article"` for general.

### BreadcrumbList

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://acme.com" },
    { "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://acme.com/blog" },
    { "@type": "ListItem", "position": 3, "name": "Post Title" }
  ]
}
```

Last item may omit `item`.

### Product with Offer + AggregateRating + Review

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Wireless Headphones Pro",
  "image": ["https://acme.com/hp-1.jpg"],
  "description": "Noise-cancelling Bluetooth headphones",
  "sku": "WH-1000",
  "gtin13": "0194252123456",
  "brand": { "@type": "Brand", "name": "Acme" },
  "offers": {
    "@type": "Offer",
    "url": "https://acme.com/products/wh-1000",
    "priceCurrency": "USD",
    "price": "299.00",
    "availability": "https://schema.org/InStock",
    "itemCondition": "https://schema.org/NewCondition",
    "hasMerchantReturnPolicy": {
      "@type": "MerchantReturnPolicy",
      "applicableCountry": "US",
      "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
      "merchantReturnDays": 30,
      "returnMethod": "https://schema.org/ReturnByMail",
      "returnFees": "https://schema.org/FreeReturn"
    },
    "shippingDetails": {
      "@type": "OfferShippingDetails",
      "shippingRate": { "@type": "MonetaryAmount", "value": "0", "currency": "USD" },
      "shippingDestination": { "@type": "DefinedRegion", "addressCountry": "US" }
    }
  },
  "aggregateRating": { "@type": "AggregateRating", "ratingValue": "4.5", "reviewCount": "2500" }
}
```

### LocalBusiness (+ industry subtype)

```json
{
  "@context": "https://schema.org",
  "@type": "Restaurant",
  "name": "Mario's Pizza",
  "image": "https://marios.com/photo.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "500 Broadway",
    "addressLocality": "New York",
    "addressRegion": "NY",
    "postalCode": "10012",
    "addressCountry": "US"
  },
  "geo": { "@type": "GeoCoordinates", "latitude": 40.7223, "longitude": -74.0015 },
  "telephone": "+1-555-0199",
  "url": "https://marios.com",
  "priceRange": "$$",
  "servesCuisine": "Italian",
  "openingHoursSpecification": [
    { "@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday"], "opens": "11:00", "closes": "22:00" },
    { "@type": "OpeningHoursSpecification", "dayOfWeek": ["Friday","Saturday"], "opens": "11:00", "closes": "23:00" }
  ]
}
```

Subtypes: `Restaurant`, `Store`, `Dentist`, `LegalService`, `Physician`, `Plumber`, `HairSalon`, `AutoRepair`, `RealEstateAgent`, `BankOrCreditUnion`, etc.

### FAQPage (⚠ restricted — gov/health/consumer only for rich results since 2023)

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is your return policy?",
      "acceptedAnswer": { "@type": "Answer", "text": "30-day returns..." }
    }
  ]
}
```

### HowTo (⚠ deprecated for rich results Sept 2023 — still valid markup)

```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "How to Tie a Tie",
  "totalTime": "PT5M",
  "step": [
    { "@type": "HowToStep", "name": "Wrap", "text": "Cross the wide end..." },
    { "@type": "HowToStep", "name": "Loop", "text": "Bring the wide end..." }
  ]
}
```

### Recipe

```json
{
  "@context": "https://schema.org",
  "@type": "Recipe",
  "name": "Chocolate Chip Cookies",
  "author": { "@type": "Person", "name": "Julia Child" },
  "prepTime": "PT15M",
  "cookTime": "PT12M",
  "totalTime": "PT27M",
  "recipeYield": "24 cookies",
  "recipeIngredient": ["2 cups flour", "1 cup sugar", "1 cup butter"],
  "recipeInstructions": [
    { "@type": "HowToStep", "text": "Preheat to 350F..." }
  ],
  "nutrition": { "@type": "NutritionInformation", "calories": "150 calories" }
}
```

### Event

```json
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "React Summit 2026",
  "startDate": "2026-06-15T09:00:00+00:00",
  "endDate": "2026-06-16T18:00:00+00:00",
  "eventStatus": "https://schema.org/EventScheduled",
  "eventAttendanceMode": "https://schema.org/MixedEventAttendanceMode",
  "location": [
    { "@type": "Place", "name": "Miami Convention Center", "address": "123 Main St, Miami, FL" },
    { "@type": "VirtualLocation", "url": "https://acme.com/stream" }
  ],
  "organizer": { "@type": "Organization", "name": "React Foundation", "url": "https://react.org" },
  "offers": { "@type": "Offer", "price": "299", "priceCurrency": "USD", "availability": "https://schema.org/InStock", "url": "https://acme.com/tickets" }
}
```

### Course

```json
{
  "@context": "https://schema.org",
  "@type": "Course",
  "name": "Advanced TypeScript",
  "description": "Master TS patterns",
  "provider": { "@type": "Organization", "name": "TechAcademy", "url": "https://techacademy.com" },
  "hasCourseInstance": {
    "@type": "CourseInstance",
    "courseMode": "online",
    "courseWorkload": "PT20H"
  }
}
```

### JobPosting

```json
{
  "@context": "https://schema.org",
  "@type": "JobPosting",
  "title": "Senior React Developer",
  "description": "<p>Build scalable web apps...</p>",
  "datePosted": "2026-04-01",
  "validThrough": "2026-05-01T00:00",
  "employmentType": "FULL_TIME",
  "hiringOrganization": { "@type": "Organization", "name": "TechCorp", "sameAs": "https://techcorp.com" },
  "jobLocation": {
    "@type": "Place",
    "address": { "@type": "PostalAddress", "streetAddress": "1 Market St", "addressLocality": "San Francisco", "addressRegion": "CA", "postalCode": "94105", "addressCountry": "US" }
  },
  "baseSalary": {
    "@type": "MonetaryAmount",
    "currency": "USD",
    "value": { "@type": "QuantitativeValue", "value": 120000, "unitText": "YEAR" }
  }
}
```

### SoftwareApplication (SaaS)

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "TodoPro",
  "operatingSystem": "Web, iOS, Android",
  "applicationCategory": "BusinessApplication",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "aggregateRating": { "@type": "AggregateRating", "ratingValue": "4.6", "ratingCount": "5000" }
}
```

### VideoObject

```json
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "How to Make Coffee",
  "description": "Quick brewing tutorial",
  "thumbnailUrl": ["https://acme.com/thumb.jpg"],
  "uploadDate": "2026-04-01T08:00:00+00:00",
  "duration": "PT5M30S",
  "contentUrl": "https://acme.com/video.mp4",
  "embedUrl": "https://youtube.com/embed/abc123"
}
```

### ImageObject (with credits)

```json
{
  "@context": "https://schema.org",
  "@type": "ImageObject",
  "contentUrl": "https://acme.com/photo.jpg",
  "creator": { "@type": "Person", "name": "Jane Doe" },
  "creditText": "Photo by Jane Doe",
  "copyrightNotice": "© 2026 Jane Doe",
  "license": "https://creativecommons.org/licenses/by/4.0/"
}
```

### Review / AggregateRating

```json
{
  "@context": "https://schema.org",
  "@type": "Review",
  "itemReviewed": { "@type": "Product", "name": "WH-1000" },
  "author": { "@type": "Person", "name": "John R." },
  "datePublished": "2026-03-01",
  "reviewBody": "Exceeded expectations.",
  "reviewRating": { "@type": "Rating", "ratingValue": "5", "bestRating": "5" }
}
```

### ProfilePage (author/person)

```json
{
  "@context": "https://schema.org",
  "@type": "ProfilePage",
  "mainEntity": {
    "@type": "Person",
    "name": "Jane Doe",
    "jobTitle": "Senior Engineer",
    "worksFor": { "@type": "Organization", "name": "Acme" },
    "sameAs": ["https://twitter.com/janedoe", "https://linkedin.com/in/janedoe"],
    "knowsAbout": ["React", "TypeScript", "SEO"]
  }
}
```

### DiscussionForumPosting (forums, user-generated)

```json
{
  "@context": "https://schema.org",
  "@type": "DiscussionForumPosting",
  "headline": "How to optimize React performance?",
  "datePublished": "2026-04-10T10:00:00+00:00",
  "author": { "@type": "Person", "name": "DevAlice" },
  "interactionStatistic": [
    { "@type": "InteractionCounter", "interactionType": "https://schema.org/LikeAction", "userInteractionCount": 42 },
    { "@type": "InteractionCounter", "interactionType": "https://schema.org/CommentAction", "userInteractionCount": 12 }
  ]
}
```

### VacationRental

```json
{
  "@context": "https://schema.org",
  "@type": "VacationRental",
  "name": "Beachfront Villa",
  "address": { "@type": "PostalAddress", "addressLocality": "Miami", "addressRegion": "FL", "addressCountry": "US" },
  "numberOfBedrooms": 3,
  "numberOfBathroomsTotal": 2,
  "occupancy": { "@type": "QuantitativeValue", "maxValue": 8 },
  "petsAllowed": true
}
```

### Dataset

```json
{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "name": "Climate Research 2026",
  "description": "Global temperature records",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "creator": { "@type": "Organization", "name": "NOAA" },
  "distribution": [{ "@type": "DataDownload", "encodingFormat": "CSV", "contentUrl": "https://acme.com/data.csv" }]
}
```

### Carousel (ItemList)

```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "url": "https://acme.com/recipe-1" },
    { "@type": "ListItem", "position": 2, "url": "https://acme.com/recipe-2" }
  ]
}
```

### MerchantReturnPolicy (standalone)

```json
{
  "@context": "https://schema.org",
  "@type": "MerchantReturnPolicy",
  "applicableCountry": "US",
  "returnPolicyCountry": "US",
  "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
  "merchantReturnDays": 30,
  "returnMethod": "https://schema.org/ReturnByMail",
  "returnFees": "https://schema.org/FreeReturn"
}
```

## Deprecation calendar (as of 2026-04-14)

| Type | Status | Since | Action |
|------|--------|-------|--------|
| HowTo | Rich results removed | Sept 2023 | Keep markup, don't expect rich snippet |
| FAQPage | Restricted to gov/health/consumer sites | Aug 2023 | Remove from commercial sites |
| SpecialAnnouncement | Removed | July 2025 | Replace with Article |
| CourseInfo | Removed | 2024 | Use Course |
| EstimatedSalary | Removed | 2024 | — |
| LearningVideo | Removed | 2024 | Use VideoObject |
| ClaimReview | Restricted to accredited fact-checkers | — | — |
| VehicleListing | Limited regional availability | — | Check per-country |

## Required fields quick-reference

| @type | Required |
|-------|----------|
| Organization | name, url |
| WebSite | name, url |
| Article | headline, image, datePublished, author |
| Product | name, image, offers OR aggregateRating OR review |
| Offer | price, priceCurrency, availability |
| LocalBusiness | name, address, telephone |
| Event | name, startDate, location |
| JobPosting | title, description, datePosted, hiringOrganization, jobLocation |
| Recipe | name, image, recipeIngredient, recipeInstructions |
| VideoObject | name, thumbnailUrl, uploadDate |
| Course | name, description, provider |
| BreadcrumbList | itemListElement |
| FAQPage | mainEntity (Question+Answer) |

## Next.js helper pattern (type-safe emitter)

```ts
// lib/jsonld.ts
export function JsonLd<T extends Record<string, unknown>>({ data }: { data: T }) {
  const json = JSON.stringify(data)
    .replace(/</g, '\\u003c')
    .replace(/-->/g, '--\\u003e')
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: json }} />
}
```

Use `next-seo` npm package for pre-built React components covering all 23 types if you want to skip handwriting JSON.

## Validation

- Test with https://search.google.com/test/rich-results
- Validate against schema.org with https://validator.schema.org
- See `schema-validation-checklist.md` for CI-friendly pre-publish checks
