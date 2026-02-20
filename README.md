# Burundi Event Platform (Public + Admin)

Flask web application with:
- a public landing page and home experience featuring upcoming events in an Instagram-style layout
- an admin dashboard for events, blog posts, categories, media, and analytics

## Public site highlights
- Mobile-first header with logo, navigation, language switcher (Kirundi/French), and hamburger menu
- Global sticky header + unified footer quick links for cohesive site-wide navigation
- Breadcrumb navigation on deeper pages (event/post detail and section pages)
- Language-aware URLs (`/kirundi/...` and `/fr/...`) with Kirundi-first fallback when translations are unavailable
- Hero banner with featured event and CTA
- Upcoming events card grid with hover effects
- Real-time client-side search/filter/sort interactions
- Event detail page with full metadata (location, date/time, category, tags)
- Lightbox gallery and related-event suggestions
- Blog highlights section and footer contact/social links
- Dedicated Blog/News listing with search/filter, category widgets, and pagination
- Individual blog post pages with media, tags, and related post recommendations
- About and Contact public pages with community context and local trust info
- Contact form with server-side persistence and optional SMTP email delivery
- Public media gallery with image/video grid, filters, lightbox, and load-more interactions
- Sponsors, Local Guides, and FAQs pages with filters and accordion interactions
- Unified search and filter system across events, posts, and media with live API results
- Advanced analytics tracking (views, unique visitors, content performance, referrals, CSV export)
- SEO-ready metadata (dynamic title/description/keywords), Open Graph tags, canonical/alternate language links, and structured data for events/posts
- Auto-generated `sitemap.xml` and `robots.txt` for search engine discovery

## Admin highlights
- Admin login with hashed password storage (default: `admin` / `admin123`)
- Dashboard summary cards and quick actions
- Event and post CRUD with category assignment
- Dynamic categories management
- Media library with drag-and-drop upload support
- Analytics overview with Chart.js
# Burundi Event Admin Dashboard

Flask-based admin panel for managing events, blog posts, categories, media assets, and analytics.

## Features
- Admin login with hashed password storage (default: `admin` / `admin123`)
- Dashboard overview with quick actions and summary cards
- Event CRUD with category assignment, language, and filtering
- Blog post CRUD with category/tag style assignment and filtering
- Dynamic category management for events and posts
- Media library with upload, filtering, and delete actions
- Analytics page with charts for views and popularity
- Live content preview in event/post editors
- Drag-and-drop file upload support
- Responsive layout for desktop/tablet use

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5000`.
