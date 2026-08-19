this file is also on github...ensure you are updating it.

# **URXION Website Modernization & SEO Overhaul**
## *Project Specification Document v1.0*

---

## 1. Executive Summary

This document specifies a full technical migration and enhancement of the URXION website (currently a Flask/Jinja application) to a modern, SEO-optimized Jamstack architecture while preserving all existing content, URL structures, and search equity. The goal is to transform the site into a high‑performance, content‑driven B2B service website that:

- Achieves **Lighthouse scores > 90** (Performance, Accessibility, SEO)
- Implements **hub‑and‑spoke content architecture** with automatic internal linking
- Enables **non‑technical content editors** to publish via a Git‑based CMS (Decap)
- Maintains **full backwards compatibility** for all legacy URLs (book chapters, assessments, etc.)
- Introduces **comprehensive structured data** (LocalBusiness, FAQ, Article, Person)
- Adds **continuous performance monitoring** via CI and weekly audits
- Remains **fully open‑source and free to operate**

All existing functionality, including the RFP and Compliance interactive demos (Flask‑based LLM orchestration), will be preserved and integrated as a standalone microservice.

---

## 2. Project Scope & Non‑Negotiables

### 2.1 In‑Scope
- Complete frontend rebuild using **Next.js (App Router)** with static generation (SSG)
- Migration of all marketing content (pages, services, blog, authors) to **Markdown + Decap CMS**
- Preservation of **all existing URL paths** (no 404s for old pages)
- Implementation of **hub‑and‑spoke linking** between services and blog posts
- Full **schema markup** (JSON‑LD) per page type
- **Image optimisation** via Next.js Image component
- **CI/CD pipeline** with Lighthouse CI enforcement
- **Weekly performance dashboard** (Google Sheets + PageSpeed Insights API)
- Integration with existing **Flask demo engine** (RFP & Compliance) via API proxying

### 2.2 Out‑of‑Scope
- Rewriting the Flask demo engine itself (LLM logic, file handling) – it remains untouched
- Changing business logic or pricing models
- Migrating the demo run state files (they stay with Flask)

### 2.3 Preservation Requirements
- **All legacy book chapter pages** (e.g., `/blog/sell_chapter_1`, `/blog/challenger_chapter_2`) must remain accessible under the same URLs
- **Assessment tools** (`/business-assessment`, `/cold-calling-assessment`, `/sales-assessment`) must continue to function (they are static pages – can be recreated as Markdown or kept as templates if embedded)
- **Contact form**, **unsubscribe**, and other utility endpoints must remain operational
- **All existing external backlinks** must not break – URL patterns must be identical

---

## 3. Technical Architecture

### 3.1 High‑Level Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| **Frontend** | Next.js 15 (App Router) | SSG for all content pages |
| **CMS** | Decap CMS (Git‑based) | Editors commit Markdown to GitHub |
| **Hosting** | Vercel (Free tier) | Automatic deploys on push to `main` |
| **Backend (Demo)** | Existing Flask app | Runs as a separate service (e.g., on Render or Vercel serverless) |
| **Data Storage** | GitHub repo + Markdown | All content in repo; images in `/public` |
| **Performance Monitoring** | Lighthouse CI + GitHub Actions | Fail build if scores drop |
| **Analytics** | Google Analytics 4 + Search Console | Free tiers |

### 3.2 Repository Structure

```
urxion-website/
├── app/                          # Next.js App Router
│   ├── (marketing)/              # All static/content routes
│   │   ├── page.js               # Homepage (content from Markdown)
│   │   ├── services/             # Service pillar pages
│   │   │   └── [slug]/page.js
│   │   ├── blog/                 # Blog posts (spokes)
│   │   │   └── [slug]/page.js
│   │   ├── authors/              # Author profiles
│   │   │   └── [slug]/page.js
│   │   ├── resources/            # Static resource pages (checklists, etc.)
│   │   │   └── [...slug]/page.js # Catch‑all for legacy pages
│   │   ├── demo/                 # Demo landing pages (static)
│   │   │   ├── page.js           # /demo
│   │   │   ├── try-rfp/          # Static intro page, then redirects to Flask
│   │   │   └── try-compliance/   # Same
│   │   ├── contact/              # Contact page (static form)
│   │   ├── privacy/              # Privacy, terms, etc.
│   │   └── sitemap.xml/          # Dynamic sitemap (route handler)
│   ├── api/                      # API routes for proxying Flask demos
│   │   └── demo/                 # Proxy to Flask endpoints
│   │       ├── rfp/              # Forward to Flask /try-rfp
│   │       └── compliance/       # Forward to Flask /try-compliance
│   ├── layout.js                 # Root layout (header, footer, scripts)
│   └── robots.txt/               # Dynamic route
├── content/                      # All Markdown content
│   ├── settings/                 # Site settings (business info, social links)
│   │   └── site.yaml
│   ├── pages/                    # Static pages (home, about, contact, privacy, terms)
│   │   ├── home.md
│   │   ├── about.md
│   │   └── ...
│   ├── services/                 # Service pillar pages
│   │   ├── rfp.md
│   │   ├── compliance.md
│   │   ├── sdr.md
│   │   └── custom-agents.md
│   ├── blog/                     # Blog posts (including legacy chapters)
│   │   ├── sell_chapter_1.md
│   │   ├── challenger_chapter_1.md
│   │   └── ... (all 50+ chapter files)
│   ├── authors/                  # Author profiles
│   │   └── sean-brennan.md
│   ├── legacy/                   # Catch‑all for non‑blog static pages
│   │   ├── business-assessment.md
│   │   ├── cold-calling-assessment.md
│   │   └── sales-assessment.md
│   └── resources/                # Checklists, guides, etc.
│       ├── founder-led-workflow-pilot.md
│       ├── rfp-intake-checklist.md
│       └── compliance-package-checklist.md
├── public/                       # Static assets
│   ├── images/                   # Optimized images (Next.js will process)
│   └── favicon.ico
├── lib/                          # Utility functions
│   ├── content.js                # Markdown parsing and data fetching
│   ├── schema.js                 # JSON‑LD generators
│   └── seo.js                    # Title, meta description helpers
├── cms/                          # Decap CMS configuration
│   └── config.yml
├── scripts/                      # Build and monitoring scripts
│   ├── lighthouse-ci.js          # Run Lighthouse in CI
│   ├── weekly-audit.js           # Call PageSpeed Insights, save to Google Sheets
│   └── generate-sitemap.js       # (handled by Next.js route)
├── .github/workflows/
│   ├── deploy.yml                # Build and deploy on push to main
│   ├── lighthouse.yml            # Run Lighthouse CI on PR
│   └── weekly-audit.yml          # Cron job for weekly performance audit
├── next.config.js
├── package.json
└── README.md
```

### 3.3 Content Management (Decap CMS)

Editors will access `/admin` on the live site; changes are committed to GitHub and trigger redeployment. The CMS configuration defines collections:

```yaml
collections:
  - name: "pages"
    label: "Pages"
    files:
      - file: "content/pages/home.md"
        label: "Home"
        fields:
          - { name: "title", label: "Title", widget: "string" }
          - { name: "hero_headline", label: "Hero Headline", widget: "string" }
          - { name: "hero_subhead", label: "Hero Subhead", widget: "text" }
          - { name: "body", label: "Body", widget: "markdown" }
          - { name: "cta_primary_text", label: "Primary CTA Text", widget: "string" }
          - { name: "cta_primary_url", label: "Primary CTA URL", widget: "string" }
          # ... etc.
  - name: "services"
    label: "Services"
    folder: "content/services"
    create: true
    fields:
      - { name: "title", label: "Title", widget: "string" }
      - { name: "slug", label: "Slug", widget: "string" }
      - { name: "description", label: "Meta Description", widget: "text" }
      - { name: "body", label: "Body", widget: "markdown" }
      - { name: "featured_image", label: "Featured Image", widget: "image" }
      - { name: "related_posts", label: "Related Blog Posts", widget: "list", fields: [{ name: "post", label: "Post", widget: "relation", collection: "blog", value_field: "slug", search_fields: ["title"] }] }
      - { name: "faq", label: "FAQ", widget: "list", fields: [{ name: "question", label: "Question", widget: "string" }, { name: "answer", label: "Answer", widget: "text" }] }
  - name: "blog"
    label: "Blog"
    folder: "content/blog"
    create: true
    fields:
      - { name: "title", label: "Title", widget: "string" }
      - { name: "slug", label: "Slug", widget: "string" }
      - { name: "author", label: "Author", widget: "relation", collection: "authors", value_field: "slug", search_fields: ["name"] }
      - { name: "date", label: "Date", widget: "datetime" }
      - { name: "categories", label: "Categories", widget: "list", default: ["General"] }
      - { name: "excerpt", label: "Excerpt", widget: "text" }
      - { name: "body", label: "Body", widget: "markdown" }
      - { name: "featured_image", label: "Featured Image", widget: "image" }
      - { name: "related_services", label: "Related Services", widget: "list", fields: [{ name: "service", label: "Service", widget: "relation", collection: "services", value_field: "slug", search_fields: ["title"] }] }
  - name: "authors"
    label: "Authors"
    folder: "content/authors"
    create: true
    fields:
      - { name: "name", label: "Name", widget: "string" }
      - { name: "slug", label: "Slug", widget: "string" }
      - { name: "bio", label: "Bio", widget: "text" }
      - { name: "photo", label: "Photo", widget: "image" }
      - { name: "linkedin_url", label: "LinkedIn URL", widget: "string", required: false }
```

### 3.4 Routing & URL Preservation

The key challenge is maintaining all old Flask routes under the new Next.js structure. We achieve this with:

- **Catch‑all routes** for legacy pages that aren't blog posts or services.
- **Explicit redirects** where necessary (old `/blog/*` to new `/blog/*` is automatic if slugs are identical).
- **Proxy API routes** for the interactive demos.

**Specific mapping:**

| Old Flask Route | New Next.js Route | Handling |
|-----------------|-------------------|----------|
| `/` | `/` | Markdown `home.md` |
| `/rfp` | `/services/rfp` | Service pillar (preserve path with rewrites) |
| `/compliance` | `/services/compliance` | Same |
| `/sdr` | `/services/sdr` | Same |
| `/custom-agents` | `/services/custom-agents` | Same |
| `/try-rfp` | `/demo/try-rfp` (static page) + `/api/demo/rfp` (proxy) | Static intro page, then form posts to Next.js API route, which proxies to Flask backend |
| `/try-compliance` | `/demo/try-compliance` + `/api/demo/compliance` | Same |
| `/try-rfp/opportunities/<run_id>` | `/demo/rfp/opportunities/<run_id>` (proxy) | Proxy to Flask |
| `/try-rfp/results/<run_id>` | `/demo/rfp/results/<run_id>` (proxy) | Proxy |
| `/try-rfp/download/<run_id>` | `/demo/rfp/download/<run_id>` (proxy) | Proxy |
| `/try-compliance/results/<run_id>` | `/demo/compliance/results/<run_id>` (proxy) | Proxy |
| `/try-compliance/download/<run_id>` | `/demo/compliance/download/<run_id>` (proxy) | Proxy |
| `/blog/*` (all book chapters) | `/blog/*` (same slug) | Each becomes a Markdown file in `content/blog` |
| `/resources/*` (checklists, etc.) | `/resources/*` | Markdown files in `content/resources` |
| `/business-assessment` | `/legacy/business-assessment` | Markdown in `content/legacy` (use rewrite to preserve URL) |
| `/cold-calling-assessment` | `/legacy/cold-calling-assessment` | Same |
| `/sales-assessment` | `/legacy/sales-assessment` | Same |
| `/contact` | `/contact` | Static form page |
| `/privacy`, `/terms` | `/privacy`, `/terms` | Markdown pages |
| `/demo` | `/demo` | Static landing page |
| `/why-urxion` | `/about` (rewrite to preserve URL) | Markdown page |
| `/data-security` | `/data-security` | Markdown page |
| `/sample-outputs` | `/sample-outputs` | Markdown page |
| `/demo-vs-production` | `/demo-vs-production` | Markdown page |
| `/unsubscribe` | `/unsubscribe` | Static form (POST to Flask? Or implement in Next.js API) |
| `/robots.txt` | `/robots.txt` (dynamic route) | Next.js handles |
| `/sitemap.xml` | `/sitemap.xml` (dynamic route) | Next.js generates |
| `/.well-known/*` | `/.well-known/*` | Serve static from `public/.well-known` |

For preservation, we use **Next.js rewrites** in `next.config.js` to keep the old paths visible without changing the URL. For example:

```js
// next.config.js
module.exports = {
  rewrites: async () => [
    { source: '/rfp', destination: '/services/rfp' },
    { source: '/compliance', destination: '/services/compliance' },
    { source: '/why-urxion', destination: '/about' },
    { source: '/business-assessment', destination: '/legacy/business-assessment' },
    // ... etc.
  ],
  // ... other config
}
```

This ensures old bookmarks and search indexes continue to work seamlessly.

### 3.5 Hub‑and‑Spoke Implementation

**Pillar pages** (services) will display a list of related blog posts (via the `related_posts` field) at the bottom. **Spoke pages** (blog posts) will show a list of related services (via `related_services`) in a sidebar or footer.

The linking is data‑driven; the UI will be consistent across all pages.

### 3.6 Schema Markup (JSON‑LD)

We will inject per‑page schemas using Next.js `script` tags in the `<head>`. Generators in `lib/schema.js` will produce:

- **Homepage**: `Organization` + `WebSite`
- **Service pages**: `Service` + `FAQPage` + `LocalBusiness` (site‑wide)
- **Blog posts**: `Article` + `Person` (author) + `BlogPosting`
- **Author pages**: `Person` + `ProfilePage`
- **Contact page**: `ContactPage`
- **All pages**: `BreadcrumbList` (auto‑generated from path)

The `LocalBusiness` schema will include:
- `name`: URXION
- `address`: (from site settings)
- `telephone`: (from site settings)
- `priceRange`: "$$$" (or dynamic)
- `areaServed`: "Ontario, Canada"
- `sameAs`: LinkedIn URL

### 3.7 Performance Optimizations

- **Images**: Use Next.js `<Image>` component with `width`, `height`, `sizes`, `loading="lazy"`. All images stored in `/public/images` and optimized at build time.
- **Fonts**: Use `next/font/google` for system fonts (or self‑host) to avoid layout shifts.
- **CSS**: Use Tailwind CSS (optional) or CSS Modules; critical CSS inlined via Next.js built‑in.
- **JavaScript**: Minimize client‑side JS; keep as much as possible in build‑time SSG.
- **Caching**: Leverage Vercel's edge caching for static assets.

### 3.8 Integration with Flask Demo Engine

The Flask app will continue to serve the `/try-rfp/*` and `/try-compliance/*` routes. However, we want a unified domain. We have two options:

1. **Subdomain**: Deploy Flask on `demo.urxion.com` and proxy from Next.js.
2. **Same domain via rewrite**: Use Vercel's rewrites to forward `/api/demo/*` requests to the Flask backend (which runs on a separate server, e.g., a Render web service).

We choose **option 2** for user experience. The Next.js API route will act as a reverse proxy:

```js
// app/api/demo/[...path]/route.js
export async function POST(req, { params }) {
  const path = params.path.join('/');
  const url = `https://flask-backend.vercel.app/${path}`;
  const body = await req.text();
  const headers = { 'Content-Type': req.headers.get('content-type') };
  const response = await fetch(url, { method: 'POST', headers, body });
  return new Response(response.body, { status: response.status });
}
```

All Flask routes are prefixed with `/api/demo/`; the Flask app must be configured to strip that prefix or accept it.

### 3.9 Legacy Content Migration Strategy

For the 50+ book chapter pages, we will:

- Write a migration script that reads the existing Jinja templates (if they are still in the Flask code) and converts them to Markdown frontmatter and body. However, many of these are likely plain HTML. Since we can't predict the exact content, we will:

  - **Option A**: Keep those pages as HTML files in the `public` directory (mimic Flask's static serving) and rewrite routes to serve them. This is quick but not CMS‑editable.
  - **Option B**: Manually create Markdown files for each, copying the content from the old templates.

Given the volume (50+), and that these are mostly book summaries, we will choose **Option B** but write a quick Node.js script to scrape the current live site's HTML for those pages and generate Markdown. The script will:

- Fetch the HTML from `https://www.urxion.com/blog/sell_chapter_1` etc.
- Extract the main content (likely inside `<main>`).
- Convert to Markdown using a library like `turndown`.
- Write to `content/blog/[slug].md` with frontmatter (title, slug, date, author, categories).

This preserves the exact content and allows future edits via CMS.

### 3.10 Deployment & CI/CD

We will use **Vercel** for hosting. The GitHub repository is connected; every push to `main` triggers a build and deploy. We will have two environments:

- **Preview**: Each PR deploys a unique preview URL for testing.
- **Production**: The `main` branch deploys to the live domain.

**CI Steps**:

1. Run `npm run build` – generate static site.
2. Run `npx lhci autorun` – Lighthouse CI checks against production URL (or preview URL).
   - Thresholds: Performance >= 90, Accessibility >= 95, SEO >= 90, Best Practices >= 90.
3. If scores fail, the build fails.

**Weekly Audits**:

A GitHub Action cron job runs weekly:
- Fetch all pages from the sitemap.
- For each page, call the PageSpeed Insights API.
- Store results in a Google Sheets document (via a simple script using Google Sheets API).
- If any page has a performance score < 90, send a Slack/email alert (optional).

We'll provide a Node.js script that handles this.

### 3.11 Analytics & Search Console

- **Google Analytics 4**: Tracking code in the root layout. We'll use a `next/script` with `strategy="afterInteractive"`.
- **Google Search Console**: Verify via meta tag or DNS; submit the generated sitemap automatically via the Vercel integration (or manually).

---

## 4. Implementation Plan & Timeline

### Phase 1: Foundation (Days 1–5)
- Set up Next.js project with App Router.
- Configure Decap CMS with all collections.
- Create `lib/content.js` to fetch Markdown files.
- Build basic layout (header, footer) using site settings.

### Phase 2: Content Migration (Days 6–10)
- Write migration script to convert existing HTML content (book chapters, legacy pages) to Markdown.
- Manually create service pages (5 pillars) and author pages.
- Migrate all static resources (checklists, etc.).
- Create a rewrite map for all old URLs.

### Phase 3: Core Pages & SEO (Days 11–15)
- Build dynamic route handlers for services, blog, authors.
- Implement schema generators.
- Add FAQ and breadcrumbs to pages.
- Build the hub‑and‑spoke linking components.
- Ensure all metadata (title, description) is pulled from frontmatter.

### Phase 4: Demos & API Proxy (Days 16–18)
- Build static demo landing pages (`/demo/try-rfp`, `/demo/try-compliance`).
- Implement API routes that proxy to the Flask backend.
- Test the full demo flow.

### Phase 5: CI/CD & Monitoring (Days 19–21)
- Set up GitHub Actions for deployment and Lighthouse CI.
- Write the weekly audit script and schedule.
- Configure Vercel project and connect repository.

### Phase 6: Testing & Launch (Days 22–25)
- Run full regression test (all old URLs must 200).
- Test CMS editing flow.
- Run Lighthouse on all pages (fix any issues).
- Deploy to production and verify search console sitemap.

### Total: 25 business days (5 weeks)

---

## 5. Detailed Tasks for the Coder

### 5.1 Setup & Initial Configuration
1. **Create Next.js project**: `npx create-next-app@latest urxion-website --typescript --tailwind --eslint`
2. **Install dependencies**:
   ```bash
   npm install gray-matter reading-time remark remark-html
   npm install -D @types/node
   ```
3. **Configure `next.config.js`** with rewrites for old URLs and image domains.
4. **Set up environment variables** for:
   - `NEXT_PUBLIC_FLASK_BACKEND_URL` (the URL of the Flask service)
   - `GA_MEASUREMENT_ID`
   - `GOOGLE_SHEETS_PRIVATE_KEY` (for weekly audit, optional)

### 5.2 Content Layer
1. **Create `lib/content.js`** with functions:
   - `getAllServices()`
   - `getServiceBySlug(slug)`
   - `getAllPosts()`
   - `getPostBySlug(slug)`
   - `getAllAuthors()`
   - `getAuthorBySlug(slug)`
   - `getPageBySlug(slug)` (for static pages like home, privacy)
   - `getAllLegacyPages()`
   - `getSettings()`
   All functions should read from the `content/` directory.

2. **Create `lib/schema.js`** with functions that return JSON-LD objects:
   - `localBusinessSchema()`
   - `serviceSchema(service)`
   - `faqSchema(faqItems)`
   - `articleSchema(post, author)`
   - `personSchema(author)`
   - `breadcrumbSchema(path)` – generate from current route.

3. **Create `lib/seo.js`** with helpers for meta titles, descriptions, and Open Graph tags.

### 5.3 CMS Configuration
1. **Write `cms/config.yml`** as per the collections above.
2. **Create the `/admin` route** by placing the Decap CMS `index.html` in `app/admin/page.js` (or using the official Next.js starter).
3. **Set up authentication** using GitHub OAuth (or the simpler `netlify-identity` if deploying on Netlify). For Vercel, we can use `git-gateway` with Netlify Identity (but that's not free). Alternative: Use `decap-cms-app` with GitHub backend (requires a personal access token). We'll document how to set up a GitHub OAuth app for CMS.

### 5.4 Page Routes
- **`app/page.js`**: fetch home.md data and render.
- **`app/services/[slug]/page.js`**: fetch service by slug; render with related posts.
- **`app/blog/[slug]/page.js`**: fetch post; render with related services.
- **`app/authors/[slug]/page.js`**: fetch author; list their posts.
- **`app/[slug]/page.js`**: catch‑all for static pages (privacy, terms, etc.) – but we need to exclude certain slugs (like `demo`). We'll define a list of reserved paths.
- **`app/legacy/[slug]/page.js`**: for old assessments.
- **`app/demo/try-rfp/page.js`**: static page with the form.
- **`app/demo/try-compliance/page.js`**: same.
- **`app/contact/page.js`**: contact form page.
- **`app/unsubscribe/page.js`**: static unsubscribe page.
- **`app/api/demo/[...path]/route.js`**: proxy to Flask.
- **`app/sitemap.xml/route.js`**: generate sitemap dynamically.
- **`app/robots.txt/route.js`**: serve robots.txt.

### 5.5 Component Design
- **`components/Layout.js`**: header, footer, meta tags.
- **`components/Header.js`**: navigation with dropdown for services.
- **`components/Footer.js`**: footer with NAP, social links.
- **`components/ServiceList.js`**: grid of services.
- **`components/PostCard.js`**: excerpt card for blog.
- **`components/RelatedPosts.js`**: show related posts on service page.
- **`components/RelatedServices.js`**: show related services on blog.
- **`components/FAQ.js`**: render FAQ with structured data.
- **`components/AuthorBio.js`**: author box with Person schema.
- **`components/Hero.js`**: hero section with CTA.
- **`components/TrustStrip.js`**: trust badges.
- **`components/Form.js`**: generic form handling (for demo and contact).

### 5.6 Migration Scripts
1. **`scripts/migrate-html-to-markdown.js`**:
   - Accepts a list of URLs (e.g., all book chapters).
   - Fetches each, extracts main content, converts to Markdown, writes to `content/blog/[slug].md` with frontmatter.
   - Should also fetch author info if possible.
2. **`scripts/generate-redirect-map.js`**: output a JSON file mapping old paths to new paths for rewrites.

### 5.7 CI & Monitoring
1. **GitHub Workflow `.github/workflows/lighthouse.yml`**:
   - On push to `main` and on PR.
   - Build the site.
   - Run Lighthouse CI against the built site (using `lhci autorun --config=./lighthouserc.js`).
   - Set thresholds and fail if not met.
2. **`lighthouserc.js`**:
   ```js
   module.exports = {
     ci: {
       collect: {
         startServerCommand: 'npm run start',
         url: ['http://localhost:3000/'],
         numberOfRuns: 3,
       },
       assert: {
         assertions: {
           'categories:performance': ['warn', { minScore: 0.9 }],
           'categories:accessibility': ['error', { minScore: 0.95 }],
           'categories:seo': ['error', { minScore: 0.9 }],
           'categories:best-practices': ['error', { minScore: 0.9 }],
         },
       },
     },
   };
   ```
3. **Weekly audit script `scripts/weekly-audit.js`**:
   - Fetch sitemap URLs.
   - For each, call `https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=...&strategy=mobile`.
   - Collect scores and store in Google Sheets (using Google Sheets API).
   - We'll provide a sample script with instructions for setting up a service account.

### 5.8 Testing & Validation
- **Run `npm run build`** and ensure no errors.
- **Test all old URLs**: use a tool like `curl` or a script to hit every known old path and check status 200.
- **Verify schema** with Google's Rich Results Test.
- **Check forms**: contact form, demo forms submit and work.
- **Test CMS**: log in, edit a page, commit, verify redeploy.

---

## 6. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **Legacy URLs break** | Use rewrites extensively; test all known paths before launch. |
| **CMS authentication fails** | Use GitHub OAuth; provide clear setup documentation. |
| **Flask demo integration fails** | Run Flask locally with proxy; test all endpoints. |
| **Lighthouse CI fails** | Tweak thresholds initially; allow warnings. Optimize images, scripts. |
| **Content migration incomplete** | Keep a backup of old templates; manually recreate if script fails. |
| **Search ranking drop** | Maintain same content and URLs; add structured data to boost rankings. Monitor Search Console. |

---

## 7. Deliverables for the Coder

Upon completion, the coder must deliver:

1. **A full Next.js project** with all code, configurations, and content (Markdown files) committed to a GitHub repository.
2. **A CMS configuration** that works (editors can log in and publish).
3. **A migration script** (or the resulting migrated content) for all legacy pages.
4. **A `README.md`** with:
   - Setup instructions (clone, install, environment variables, run dev).
   - Deployment instructions (Vercel).
   - CMS usage guide.
   - How to run Lighthouse locally.
   - How to add new services, blog posts, authors.
5. **GitHub Actions workflows** for CI and weekly audits.
6. **Documentation** for the weekly audit script (how to set up Google Sheets API).
7. **Verification** that all old URLs return 200 and contain expected content.

---

## 8. Out‑of‑Scope / Exclusions

- **Redesign**: The visual design (colors, layout) will remain largely the same; we are not doing a full brand overhaul.
- **New features**: No new major functionality (like user accounts, payments) is added; only the migration and SEO enhancements.
- **Database**: No database; all content is file‑based.
- **Flask backend**: No changes to the Flask code; it remains as is.

---

## 9. Success Criteria

- **Lighthouse scores**: Performance ≥ 90, Accessibility ≥ 95, SEO ≥ 90, Best Practices ≥ 90 for all pages.
- **CMS**: Non‑technical team member can update a service page and see it live within 5 minutes.
- **Search visibility**: No drop in organic traffic; ideally improvement due to structured data and internal linking.
- **All legacy URLs**: 100% of old URLs return 200 and display content.

---

## 10. Appendices

### Appendix A: List of All Legacy URLs to Preserve
(To be extracted from current Flask app routes; we will provide a full list of known pages, including all `/blog/*` chapter pages, `/business-assessment`, etc. The coder must ensure all are covered.)

### Appendix B: Example Frontmatter for a Blog Post
```yaml
---
title: "The Challenger Sale: Chapter 1"
slug: "challenger_chapter_1"
author: "sean-brennan"
date: "2023-01-15"
categories: ["Book Summaries", "Sales"]
excerpt: "Summary of Chapter 1 of The Challenger Sale..."
featured_image: "/images/challenger.jpg"
related_services:
  - rfp
  - sdr
---
<!-- markdown content -->
```

### Appendix C: Environment Variables
```bash
NEXT_PUBLIC_FLASK_BACKEND_URL=https://flask-backend.herokuapp.com
GA_MEASUREMENT_ID=G-XXXXXXXX
GOOGLE_SHEETS_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
GOOGLE_SHEETS_CLIENT_EMAIL=service-account@project.iam.gserviceaccount.com
```

---

## 11. Final Instructions for the Coder

- Begin by cloning the current Flask repository for reference, but do not modify it.
- Use the rewrites approach to preserve old URLs.
- When migrating content, keep the exact same text to avoid content changes that could affect SEO.
- Test thoroughly on a preview environment before merging to main.
- After deployment, monitor Google Search Console for any crawl errors.

---

