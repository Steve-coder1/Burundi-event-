# Burundi Event Platform (Public + Admin)

Flask web application with:
- a public home page featuring upcoming events in an Instagram-style layout
- an admin dashboard for events, blog posts, categories, media, and analytics

## Public site highlights
- Mobile-first header with logo, navigation, language switcher (Kirundi/French), and hamburger menu
- Hero banner with featured event and CTA
- Upcoming events card grid with hover effects
- Real-time client-side search/filter/sort interactions
- Event detail page with full metadata (location, date/time, category, tags)
- Lightbox gallery and related-event suggestions
- Blog highlights section and footer contact/social links
- Dedicated Blog/News listing with search/filter, category widgets, and pagination
- Individual blog post pages with media, tags, and related post recommendations

## Admin highlights
- Admin login with hashed password storage (default: `admin` / `admin123`)
- Dashboard summary cards and quick actions
- Event and post CRUD with category assignment
- Dynamic categories management
- Media library with drag-and-drop upload support
- Analytics overview with Chart.js

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Routes
- Public home: `http://localhost:5000/home`
- Admin login: `http://localhost:5000/admin/login`

- Public blog: `http://localhost:5000/blog`
