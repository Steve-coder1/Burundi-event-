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
