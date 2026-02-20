from __future__ import annotations

import os
import csv
import smtplib
from io import StringIO
from datetime import datetime
from email.message import EmailMessage
from functools import wraps
from uuid import uuid4
from urllib.parse import urlparse

from flask import (
    Flask,
    flash,
    jsonify,
    Response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "mp4", "mov", "webm"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///admin_dashboard.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    two_factor_enabled = db.Column(db.Boolean, default=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # event | post
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200), default="TBD")
    tags = db.Column(db.String(255), default="")
    language = db.Column(db.String(10), default="en")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default="fr")
    tags = db.Column(db.String(255), default="")
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EventCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)


class PostCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)


class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)  # image | video
    linked_type = db.Column(db.String(20), nullable=True)  # event | post
    linked_id = db.Column(db.Integer, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Analytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(100), nullable=False)
    views = db.Column(db.Integer, default=0)
    popularity_score = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    website_url = db.Column(db.String(255), nullable=False)
    logo_url = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(255), default="")
    sponsor_type = db.Column(db.String(50), default="community")
    language = db.Column(db.String(10), default="fr")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LocalGuide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    content = db.Column(db.Text, nullable=False)
    guide_type = db.Column(db.String(50), default="community")
    image_url = db.Column(db.String(255), nullable=True)
    language = db.Column(db.String(10), default="fr")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default="fr")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TrackingEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.String(64), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # page|event|post|media
    content_id = db.Column(db.String(64), nullable=False)
    content_title = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(120), nullable=True)
    interaction = db.Column(db.String(20), default="view")
    referrer_domain = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Relation helpers
Event.categories = db.relationship(
    "Category",
    secondary="event_category",
    primaryjoin=Event.id == EventCategory.event_id,
    secondaryjoin=Category.id == EventCategory.category_id,
    lazy="joined",
)
Post.categories = db.relationship(
    "Category",
    secondary="post_category",
    primaryjoin=Post.id == PostCategory.post_id,
    secondaryjoin=Category.id == PostCategory.category_id,
    lazy="joined",
)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_user"):
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


def get_referrer_domain() -> str:
    referrer = request.referrer or ""
    if not referrer:
        return "direct"
    try:
        return urlparse(referrer).netloc or "direct"
    except Exception:
        return "direct"


def log_tracking_event(
    content_type: str,
    content_id: str,
    title: str = "",
    category: str = "",
    interaction: str = "view",
) -> None:
    visitor_id = session.get("visitor_id", "anonymous")
    db.session.add(
        TrackingEvent(
            visitor_id=visitor_id,
            content_type=content_type,
            content_id=str(content_id),
            content_title=title,
            category=category,
            interaction=interaction,
            referrer_domain=get_referrer_domain(),
        )
    )


def increment_analytics(page: str, score: float = 0.5) -> None:
    record = Analytics.query.filter_by(page=page).first()
    if not record:
        record = Analytics(page=page, views=0, popularity_score=0)
        db.session.add(record)
    record.views += 1
    record.popularity_score += score
    log_tracking_event(content_type="page", content_id=page, title=page)
    db.session.commit()


def get_event_image(event_id: int) -> str | None:
    media = (
        Media.query.filter_by(linked_type="event", linked_id=event_id, media_type="image")
        .order_by(Media.uploaded_at.desc())
        .first()
    )
    return media.filename if media else None


def build_event_card(event: Event) -> dict:
    return {
        "id": event.id,
        "title": event.title,
        "date": event.event_date.strftime("%Y-%m-%d"),
        "time": event.event_date.strftime("%H:%M"),
        "category": event.categories[0].name if event.categories else "General",
        "category_id": event.categories[0].id if event.categories else 0,
        "image": get_event_image(event.id),
        "description": event.description,
        "location": event.location or "TBD",
        "tags": [tag.strip() for tag in (event.tags or "").split(",") if tag.strip()],
    }


def get_post_image(post_id: int) -> str | None:
    media = (
        Media.query.filter_by(linked_type="post", linked_id=post_id, media_type="image")
        .order_by(Media.uploaded_at.desc())
        .first()
    )
    return media.filename if media else None


def build_post_card(post: Post) -> dict:
    return {
        "id": post.id,
        "title": post.title,
        "excerpt": f"{post.body[:160]}..." if len(post.body) > 160 else post.body,
        "published": post.published_at.strftime("%Y-%m-%d"),
        "category": post.categories[0].name if post.categories else "General",
        "category_id": post.categories[0].id if post.categories else 0,
        "image": get_post_image(post.id),
        "tags": [tag.strip() for tag in (post.tags or "").split(",") if tag.strip()],
    }





def build_media_card(item: Media) -> dict:
    linked_title = "Unassigned"
    linked_category = "General"
    linked_language = "fr"

    if item.linked_type == "event" and item.linked_id:
        event = Event.query.get(item.linked_id)
        if event:
            linked_title = event.title
            linked_category = event.categories[0].name if event.categories else "General"
            linked_language = event.language
    elif item.linked_type == "post" and item.linked_id:
        post = Post.query.get(item.linked_id)
        if post:
            linked_title = post.title
            linked_category = post.categories[0].name if post.categories else "General"
            linked_language = post.language

    return {
        "id": item.id,
        "filename": item.filename,
        "media_type": item.media_type,
        "linked_type": item.linked_type or "other",
        "linked_id": item.linked_id,
        "linked_title": linked_title,
        "linked_category": linked_category,
        "linked_language": linked_language,
        "uploaded_at": item.uploaded_at.strftime("%Y-%m-%d"),
    }



def serialize_search_results(language: str) -> list[dict]:
    rows: list[dict] = []

    events = Event.query.filter(Event.language == language).all()
    for event in events:
        card = build_event_card(event)
        rows.append(
            {
                "content_type": "event",
                "id": event.id,
                "title": card["title"],
                "description": event.description,
                "date": event.event_date.strftime("%Y-%m-%d"),
                "category": card["category"],
                "tags": card["tags"],
                "media_type": "",
                "url": url_for("event_detail", event_id=event.id),
                "thumbnail": url_for("static", filename=f"uploads/{card['image']}") if card["image"] else "",
            }
        )

    posts = Post.query.filter(Post.language == language).all()
    for post in posts:
        card = build_post_card(post)
        rows.append(
            {
                "content_type": "post",
                "id": post.id,
                "title": card["title"],
                "description": card["excerpt"],
                "date": card["published"],
                "category": card["category"],
                "tags": card["tags"],
                "media_type": "",
                "url": url_for("blog_post_detail", post_id=post.id),
                "thumbnail": url_for("static", filename=f"uploads/{card['image']}") if card["image"] else "",
            }
        )

    media_items = [build_media_card(item) for item in Media.query.order_by(Media.uploaded_at.desc()).all()]
    for media in media_items:
        if media["linked_language"] != language:
            continue
        rows.append(
            {
                "content_type": "media",
                "id": media["id"],
                "title": media["linked_title"],
                "description": f"{media['linked_type'].title()} media highlight",
                "date": media["uploaded_at"],
                "category": media["linked_category"],
                "tags": [],
                "media_type": media["media_type"],
                "url": url_for("media_gallery"),
                "thumbnail": url_for("static", filename=f"uploads/{media['filename']}"),
            }
        )

    return rows


def filter_search_results(rows: list[dict], params: dict) -> list[dict]:
    keyword = params.get("q", "").strip().lower()
    content_type = params.get("content_type", "")
    event_category = params.get("event_category", "")
    post_category = params.get("post_category", "")
    post_tag = params.get("post_tag", "").strip().lower()
    media_type = params.get("media_type", "")
    date_from = params.get("date_from", "")
    date_to = params.get("date_to", "")

    filtered: list[dict] = []
    for row in rows:
        if content_type and row["content_type"] != content_type:
            continue
        if keyword and keyword not in f"{row['title']} {row['description']}".lower():
            continue

        if row["content_type"] == "event" and event_category and row["category"] != event_category:
            continue
        if row["content_type"] == "post" and post_category and row["category"] != post_category:
            continue
        if row["content_type"] == "post" and post_tag and post_tag not in ",".join(row["tags"]).lower():
            continue
        if row["content_type"] == "media" and media_type and row["media_type"] != media_type:
            continue

        if date_from and row["date"] < date_from:
            continue
        if date_to and row["date"] > date_to:
            continue

        filtered.append(row)

    sort_by = params.get("sort", "date_desc")
    if sort_by == "date_asc":
        filtered.sort(key=lambda x: x["date"])
    elif sort_by == "category_asc":
        filtered.sort(key=lambda x: (x["category"], x["date"]), reverse=False)
    else:
        filtered.sort(key=lambda x: x["date"], reverse=True)

    return filtered


def send_contact_email(name: str, email: str, phone: str, message: str) -> tuple[bool, str]:
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    admin_email = os.environ.get("ADMIN_CONTACT_EMAIL")

    if not smtp_host or not admin_email:
        return False, "SMTP is not configured. Message saved for admin review."

    mail = EmailMessage()
    mail["Subject"] = f"New Contact Message from {name}"
    mail["From"] = smtp_username or admin_email
    mail["To"] = admin_email
    mail.set_content(
        f"Name: {name}\nEmail: {email}\nPhone: {phone or 'N/A'}\n\nMessage:\n{message}"
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.send_message(mail)
        return True, "Message sent successfully."
    except Exception:
        return False, "Message saved, but email delivery failed."


@app.context_processor
def inject_globals():
    return {
        "current_public_lang": session.get("public_lang", "fr"),
    }


@app.before_request
def ensure_seed_data():
    if not session.get("visitor_id"):
        session["visitor_id"] = uuid4().hex
    db.create_all()
    with db.engine.connect() as conn:
        event_columns = {row[1] for row in conn.execute(text("PRAGMA table_info(event)"))}
        if "location" not in event_columns:
            conn.execute(text("ALTER TABLE event ADD COLUMN location VARCHAR(200) DEFAULT 'TBD'"))
        if "tags" not in event_columns:
            conn.execute(text("ALTER TABLE event ADD COLUMN tags VARCHAR(255) DEFAULT ''"))

        post_columns = {row[1] for row in conn.execute(text("PRAGMA table_info(post)"))}
        if "language" not in post_columns:
            conn.execute(text("ALTER TABLE post ADD COLUMN language VARCHAR(10) DEFAULT 'fr'"))
        if "tags" not in post_columns:
            conn.execute(text("ALTER TABLE post ADD COLUMN tags VARCHAR(255) DEFAULT ''"))
        conn.commit()

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    admin = AdminUser.query.filter_by(username="admin").first()
    if not admin:
        admin = AdminUser(username="admin", two_factor_enabled=False)
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

    if Sponsor.query.count() == 0:
        db.session.add_all(
            [
                Sponsor(
                    name="Burundi Creative Hub",
                    website_url="https://example.org/creative-hub",
                    logo_url="",
                    description="Supports youth-led music and arts programs.",
                    sponsor_type="arts",
                    language="fr",
                ),
                Sponsor(
                    name="Lake Tanganyika Sports",
                    website_url="https://example.org/lake-sports",
                    logo_url="",
                    description="Partner for community sports festivals.",
                    sponsor_type="sports",
                    language="fr",
                ),
            ]
        )

    if LocalGuide.query.count() == 0:
        db.session.add_all(
            [
                LocalGuide(
                    title="Best Evening Venues in Bujumbura",
                    content="Look for venues near the waterfront and arrive early during festival nights.",
                    guide_type="music",
                    language="fr",
                ),
                LocalGuide(
                    title="Community Event Etiquette",
                    content="Respect local customs, support local vendors, and keep public spaces clean.",
                    guide_type="community",
                    language="fr",
                ),
                LocalGuide(
                    title="Getting Around for Sports Events",
                    content="Use trusted taxi points and plan return transport before late matches.",
                    guide_type="sports",
                    language="fr",
                ),
            ]
        )

    if FAQ.query.count() == 0:
        db.session.add_all(
            [
                FAQ(
                    question="How are events selected?",
                    answer="Events are reviewed from local organizers and verified before publication.",
                    language="fr",
                ),
                FAQ(
                    question="Can I submit my event?",
                    answer="Yes. Use the contact form with event details and your team will review it.",
                    language="fr",
                ),
                FAQ(
                    question="Are events free to attend?",
                    answer="Some are free and others are ticketed. Check each event detail page for guidance.",
                    language="fr",
                ),
            ]
        )

    db.session.commit()


@app.route("/")
def index():
    current_lang = session.get("public_lang", "fr")
    upcoming_events = (
        Event.query.filter(Event.language == current_lang)
        .order_by(Event.event_date.asc())
        .limit(6)
        .all()
    )
    featured_cards = [build_event_card(event) for event in upcoming_events]
    recent_posts = [build_post_card(post) for post in Post.query.order_by(Post.published_at.desc()).limit(3).all()]
    return render_template("landing.html", featured_events=featured_cards, recent_posts=recent_posts)


@app.route("/home")
def home():
    increment_analytics("home", 1.0)
    keyword = request.args.get("keyword", "").strip().lower()
    category_id = request.args.get("category", type=int)
    sort_order = request.args.get("sort", "asc")
    page = request.args.get("page", 1, type=int)
    per_page = 9
    current_lang = session.get("public_lang", "fr")

    query = Event.query.filter(Event.language == current_lang)
    if keyword:
        query = query.filter(Event.title.ilike(f"%{keyword}%"))
    if category_id:
        query = query.join(EventCategory, Event.id == EventCategory.event_id).filter(EventCategory.category_id == category_id)

    query = query.order_by(Event.event_date.asc() if sort_order == "asc" else Event.event_date.desc())
    events = query.paginate(page=page, per_page=per_page, error_out=False)

    cards = [build_event_card(event) for event in events.items]

    featured_event = cards[0] if cards else None
    blog_highlights = [build_post_card(post) for post in Post.query.order_by(Post.published_at.desc()).limit(3).all()]
    event_categories = Category.query.filter_by(content_type="event").order_by(Category.name.asc()).all()
    return render_template(
        "home.html",
        featured_event=featured_event,
        event_cards=cards,
        pagination=events,
        categories=event_categories,
        blog_highlights=blog_highlights,
    )


@app.route("/events")
def public_events():
    return redirect(url_for("home"))


@app.route("/events/<int:event_id>")
def event_detail(event_id: int):
    event = Event.query.get_or_404(event_id)
    log_tracking_event(
        content_type="event",
        content_id=str(event.id),
        title=event.title,
        category=event.categories[0].name if event.categories else "General",
    )
    gallery = Media.query.filter_by(linked_type="event", linked_id=event.id).order_by(Media.uploaded_at.desc()).all()

    related_query = Event.query.filter(Event.id != event.id, Event.language == event.language)
    if event.categories:
        cat_ids = [category.id for category in event.categories]
        related_query = related_query.join(EventCategory, Event.id == EventCategory.event_id).filter(
            EventCategory.category_id.in_(cat_ids)
        )
    related_events = related_query.order_by(Event.event_date.asc()).limit(6).all()
    related_cards = [build_event_card(item) for item in related_events]

    return render_template("event_detail.html", event=event, gallery=gallery, related_events=related_cards)


@app.route("/set-language/<lang>")
def set_language(lang: str):
    if lang in {"rn", "fr"}:
        session["public_lang"] = "rn" if lang == "rn" else "fr"
    return redirect(request.referrer or url_for("home"))


@app.route("/search")
def search_page():
    increment_analytics("search", 0.7)
    current_lang = session.get("public_lang", "fr")
    event_categories = Category.query.filter_by(content_type="event").order_by(Category.name.asc()).all()
    post_categories = Category.query.filter_by(content_type="post").order_by(Category.name.asc()).all()
    post_tags = sorted({tag.strip() for p in Post.query.filter(Post.language == current_lang).all() for tag in (p.tags or "").split(",") if tag.strip()})
    return render_template(
        "search.html",
        event_categories=event_categories,
        post_categories=post_categories,
        post_tags=post_tags,
    )


@app.route("/api/search")
def api_search():
    current_lang = session.get("public_lang", "fr")
    rows = serialize_search_results(current_lang)
    filtered = filter_search_results(rows, request.args)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 12, type=int)
    start = (page - 1) * per_page
    end = start + per_page
    payload = {
        "results": filtered[start:end],
        "total": len(filtered),
        "page": page,
        "per_page": per_page,
        "has_next": end < len(filtered),
    }
    return jsonify(payload)


@app.route("/api/autocomplete")
def api_autocomplete():
    current_lang = session.get("public_lang", "fr")
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify({"suggestions": []})

    titles = [row["title"] for row in serialize_search_results(current_lang)]
    seen = []
    for title in titles:
        if q in title.lower() and title not in seen:
            seen.append(title)
        if len(seen) >= 8:
            break
    return jsonify({"suggestions": seen})


@app.route("/api/track", methods=["POST"])
def api_track():
    payload = request.get_json(silent=True) or {}
    content_type = payload.get("content_type", "page")
    content_id = str(payload.get("content_id", "unknown"))
    title = payload.get("title", "")
    category = payload.get("category", "")
    interaction = payload.get("interaction", "click")

    log_tracking_event(
        content_type=content_type,
        content_id=content_id,
        title=title,
        category=category,
        interaction=interaction,
    )
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/gallery")
def media_gallery():
    increment_analytics("media_gallery", 0.8)
    log_tracking_event(content_type="media", content_id="gallery", title="Public Media Gallery")
    selected_type = request.args.get("type", "")
    selected_linked_type = request.args.get("linked_type", "")
    selected_category = request.args.get("category", "")
    selected_event = request.args.get("event", type=int)
    selected_language = session.get("public_lang", "fr")

    media_items = Media.query.order_by(Media.uploaded_at.desc()).all()
    cards = [build_media_card(item) for item in media_items]

    filtered_cards = []
    for card in cards:
        if selected_type in {"image", "video"} and card["media_type"] != selected_type:
            continue
        if selected_linked_type in {"event", "post"} and card["linked_type"] != selected_linked_type:
            continue
        if selected_event and not (card["linked_type"] == "event" and card["linked_id"] == selected_event):
            continue
        if selected_category and card["linked_category"] != selected_category:
            continue
        if card["linked_language"] != selected_language:
            continue
        filtered_cards.append(card)

    event_options = Event.query.filter(Event.language == selected_language).order_by(Event.event_date.desc()).limit(100).all()
    category_options = sorted({card["linked_category"] for card in cards if card["linked_category"]})

    return render_template(
        "media_gallery.html",
        media_cards=filtered_cards,
        event_options=event_options,
        category_options=category_options,
    )


@app.route("/sponsors")
def sponsors_page():
    increment_analytics("sponsors", 0.5)
    selected_type = request.args.get("type", "")
    current_lang = session.get("public_lang", "fr")

    query = Sponsor.query.filter(Sponsor.language == current_lang)
    if selected_type:
        query = query.filter(Sponsor.sponsor_type == selected_type)

    sponsors = query.order_by(Sponsor.name.asc()).all()
    sponsor_types = sorted({row.sponsor_type for row in Sponsor.query.filter(Sponsor.language == current_lang).all()})
    return render_template("sponsors.html", sponsors=sponsors, sponsor_types=sponsor_types)


@app.route("/guides")
def guides_page():
    increment_analytics("guides", 0.5)
    selected_type = request.args.get("type", "")
    current_lang = session.get("public_lang", "fr")

    query = LocalGuide.query.filter(LocalGuide.language == current_lang)
    if selected_type:
        query = query.filter(LocalGuide.guide_type == selected_type)

    guides = query.order_by(LocalGuide.created_at.desc()).all()
    guide_types = sorted({row.guide_type for row in LocalGuide.query.filter(LocalGuide.language == current_lang).all()})
    return render_template("guides.html", guides=guides, guide_types=guide_types)


@app.route("/faqs")
def faqs_page():
    increment_analytics("faqs", 0.5)
    keyword = request.args.get("q", "").strip().lower()
    current_lang = session.get("public_lang", "fr")

    query = FAQ.query.filter(FAQ.language == current_lang)
    if keyword:
        query = query.filter(
            db.or_(
                FAQ.question.ilike(f"%{keyword}%"),
                FAQ.answer.ilike(f"%{keyword}%"),
            )
        )

    faqs = query.order_by(FAQ.created_at.desc()).all()
    return render_template("faqs.html", faqs=faqs)


@app.route("/about")
def about_page():
    increment_analytics("about", 0.4)
    highlighted_regions = [
        "Bujumbura waterfront venues",
        "Gitega cultural centers",
        "Ngozi youth and university hubs",
    ]
    return render_template("about.html", highlighted_regions=highlighted_regions)


@app.route("/contact", methods=["GET", "POST"])
def contact_page():
    increment_analytics("contact", 0.6)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Name, email, and message are required.", "danger")
            return render_template("contact.html")

        db.session.add(ContactMessage(name=name, email=email, phone=phone or None, message=message))
        db.session.commit()

        sent, feedback = send_contact_email(name, email, phone, message)
        flash(feedback, "success" if sent else "warning")
        return redirect(url_for("contact_page"))

    return render_template("contact.html")


@app.route("/blog")
def blog_home():
    increment_analytics("blog", 0.9)
    keyword = request.args.get("keyword", "").strip().lower()
    category_id = request.args.get("category", type=int)
    page = request.args.get("page", 1, type=int)
    per_page = 6
    current_lang = session.get("public_lang", "fr")

    query = Post.query.filter(Post.language == current_lang)
    if keyword:
        query = query.filter(Post.title.ilike(f"%{keyword}%"))
    if category_id:
        query = query.join(PostCategory, Post.id == PostCategory.post_id).filter(PostCategory.category_id == category_id)

    posts = query.order_by(Post.published_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    post_cards = [build_post_card(post) for post in posts.items]
    recent_posts = [build_post_card(post) for post in Post.query.filter(Post.language == current_lang).order_by(Post.published_at.desc()).limit(5).all()]
    post_categories = Category.query.filter_by(content_type="post").order_by(Category.name.asc()).all()
    return render_template(
        "blog.html",
        posts=post_cards,
        pagination=posts,
        post_categories=post_categories,
        recent_posts=recent_posts,
    )


@app.route("/blog/<int:post_id>")
def blog_post_detail(post_id: int):
    post = Post.query.get_or_404(post_id)
    log_tracking_event(
        content_type="post",
        content_id=str(post.id),
        title=post.title,
        category=post.categories[0].name if post.categories else "General",
    )
    media_items = Media.query.filter_by(linked_type="post", linked_id=post.id).order_by(Media.uploaded_at.desc()).all()

    related_query = Post.query.filter(Post.id != post.id, Post.language == post.language)
    if post.categories:
        category_ids = [category.id for category in post.categories]
        related_query = related_query.join(PostCategory, Post.id == PostCategory.post_id).filter(
            PostCategory.category_id.in_(category_ids)
        )

    related_posts = [build_post_card(item) for item in related_query.order_by(Post.published_at.desc()).limit(4).all()]
    recent_posts = [build_post_card(item) for item in Post.query.filter(Post.language == post.language).order_by(Post.published_at.desc()).limit(5).all()]
    post_categories = Category.query.filter_by(content_type="post").order_by(Category.name.asc()).all()
    return render_template(
        "blog_detail.html",
        post=post,
        media_items=media_items,
        related_posts=related_posts,
        recent_posts=recent_posts,
        post_categories=post_categories,
    )


@app.route("/admin/login", methods=["GET", "POST"])
def login():
    increment_analytics("login", 0.2)
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["admin_user"] = user.username
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/admin/logout")
@login_required
def logout():
    session.pop("admin_user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/admin/dashboard")
@login_required
def dashboard():
    increment_analytics("dashboard", 1.0)
    stats = {
        "events": Event.query.count(),
        "posts": Post.query.count(),
        "media": Media.query.count(),
        "categories": Category.query.count(),
    }
    top_pages = Analytics.query.order_by(Analytics.popularity_score.desc()).limit(5).all()
    return render_template("dashboard.html", stats=stats, top_pages=top_pages)


@app.route("/admin/events")
@login_required
def events_list():
    increment_analytics("events", 0.8)
    keyword = request.args.get("keyword", "").strip()
    category_id = request.args.get("category", type=int)
    date_filter = request.args.get("date", "")

    query = Event.query
    if keyword:
        query = query.filter(Event.title.ilike(f"%{keyword}%"))
    if date_filter:
        try:
            dt = datetime.strptime(date_filter, "%Y-%m-%d")
            query = query.filter(db.func.date(Event.event_date) == dt.date())
        except ValueError:
            flash("Date filter must be YYYY-MM-DD", "warning")
    events = query.order_by(Event.event_date.desc()).all()

    if category_id:
        events = [e for e in events if any(c.id == category_id for c in e.categories)]

    event_categories = Category.query.filter_by(content_type="event").all()
    return render_template("events.html", events=events, event_categories=event_categories)


@app.route("/admin/events/add", methods=["GET", "POST"])
@login_required
def add_event():
    categories = Category.query.filter_by(content_type="event").all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        date_str = request.form.get("event_date", "")
        language = request.form.get("language", "en")
        location = request.form.get("location", "").strip() or "TBD"
        tags = request.form.get("tags", "").strip()
        selected_ids = request.form.getlist("categories")

        if not title or not description or not date_str:
            flash("Title, description, and date are required.", "danger")
            return render_template("event_form.html", categories=categories, event=None)

        event = Event(
            title=title,
            description=description,
            event_date=datetime.strptime(date_str, "%Y-%m-%dT%H:%M"),
            language=language,
            location=location,
            tags=tags,
        )

        for cid in selected_ids:
            category = Category.query.get(int(cid))
            if category:
                event.categories.append(category)

        db.session.add(event)
        db.session.commit()
        flash("Event created successfully.", "success")
        return redirect(url_for("events_list"))

    return render_template("event_form.html", categories=categories, event=None)


@app.route("/admin/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(event_id: int):
    event = Event.query.get_or_404(event_id)
    categories = Category.query.filter_by(content_type="event").all()
    if request.method == "POST":
        event.title = request.form.get("title", event.title)
        event.description = request.form.get("description", event.description)
        event.language = request.form.get("language", event.language)
        event.location = request.form.get("location", event.location)
        event.tags = request.form.get("tags", event.tags)
        date_str = request.form.get("event_date", "")
        if date_str:
            event.event_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")

        event.categories.clear()
        for cid in request.form.getlist("categories"):
            category = Category.query.get(int(cid))
            if category:
                event.categories.append(category)

        db.session.commit()
        flash("Event updated successfully.", "success")
        return redirect(url_for("events_list"))
    return render_template("event_form.html", event=event, categories=categories)


@app.route("/admin/events/<int:event_id>/delete", methods=["POST"])
@login_required
def delete_event(event_id: int):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted.", "info")
    return redirect(url_for("events_list"))


@app.route("/admin/posts")
@login_required
def posts_list():
    increment_analytics("posts", 0.8)
    keyword = request.args.get("keyword", "").strip()
    category_id = request.args.get("category", type=int)
    date_filter = request.args.get("date", "")

    query = Post.query
    if keyword:
        query = query.filter(Post.title.ilike(f"%{keyword}%"))
    if date_filter:
        try:
            dt = datetime.strptime(date_filter, "%Y-%m-%d")
            query = query.filter(db.func.date(Post.published_at) == dt.date())
        except ValueError:
            flash("Date filter must be YYYY-MM-DD", "warning")

    posts = query.order_by(Post.published_at.desc()).all()
    if category_id:
        posts = [p for p in posts if any(c.id == category_id for c in p.categories)]

    post_categories = Category.query.filter_by(content_type="post").all()
    return render_template("posts.html", posts=posts, post_categories=post_categories)


@app.route("/admin/posts/add", methods=["GET", "POST"])
@login_required
def add_post():
    categories = Category.query.filter_by(content_type="post").all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        published_at = request.form.get("published_at", "")
        language = request.form.get("language", "fr")
        tags = request.form.get("tags", "").strip()
        selected_ids = request.form.getlist("categories")

        if not title or not body:
            flash("Title and body are required.", "danger")
            return render_template("post_form.html", categories=categories, post=None)

        post = Post(
            title=title,
            body=body,
            language=language,
            tags=tags,
            published_at=datetime.strptime(published_at, "%Y-%m-%dT%H:%M") if published_at else datetime.utcnow(),
        )

        for cid in selected_ids:
            category = Category.query.get(int(cid))
            if category:
                post.categories.append(category)

        db.session.add(post)
        db.session.commit()
        flash("Post created successfully.", "success")
        return redirect(url_for("posts_list"))

    return render_template("post_form.html", categories=categories, post=None)


@app.route("/admin/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id: int):
    post = Post.query.get_or_404(post_id)
    categories = Category.query.filter_by(content_type="post").all()
    if request.method == "POST":
        post.title = request.form.get("title", post.title)
        post.body = request.form.get("body", post.body)
        post.language = request.form.get("language", post.language)
        post.tags = request.form.get("tags", post.tags)
        published_at = request.form.get("published_at", "")
        if published_at:
            post.published_at = datetime.strptime(published_at, "%Y-%m-%dT%H:%M")

        post.categories.clear()
        for cid in request.form.getlist("categories"):
            category = Category.query.get(int(cid))
            if category:
                post.categories.append(category)

        db.session.commit()
        flash("Post updated successfully.", "success")
        return redirect(url_for("posts_list"))
    return render_template("post_form.html", categories=categories, post=post)


@app.route("/admin/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id: int):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("posts_list"))


@app.route("/admin/messages")
@login_required
def admin_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("messages.html", messages=messages)


@app.route("/admin/categories", methods=["GET", "POST"])
@login_required
def manage_categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        content_type = request.form.get("content_type", "event")
        if name:
            category = Category(name=name, content_type=content_type)
            db.session.add(category)
            db.session.commit()
            flash("Category added.", "success")
        else:
            flash("Category name is required.", "danger")
    categories = Category.query.order_by(Category.created_at.desc()).all()
    return render_template("categories.html", categories=categories)


@app.route("/admin/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def delete_category(category_id: int):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for("manage_categories"))


@app.route("/admin/media", methods=["GET", "POST"])
@login_required
def media_library():
    increment_analytics("media", 0.6)
    if request.method == "POST":
        files = request.files.getlist("media_files")
        linked_type = request.form.get("linked_type") or None
        linked_id = request.form.get("linked_id", type=int)

        added = 0
        for media_file in files:
            if media_file and allowed_file(media_file.filename):
                ext = media_file.filename.rsplit(".", 1)[1].lower()
                media_type = "video" if ext in {"mp4", "mov", "webm"} else "image"
                filename = f"{uuid4().hex}_{secure_filename(media_file.filename)}"
                media_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                db.session.add(
                    Media(
                        filename=filename,
                        media_type=media_type,
                        linked_type=linked_type,
                        linked_id=linked_id,
                    )
                )
                added += 1
        db.session.commit()
        flash(f"Uploaded {added} media files.", "success")
        return redirect(url_for("media_library"))

    media_type = request.args.get("type", "")
    query = Media.query
    if media_type in {"image", "video"}:
        query = query.filter_by(media_type=media_type)
    media_items = query.order_by(Media.uploaded_at.desc()).all()
    return render_template("media.html", media_items=media_items)


@app.route("/admin/media/<int:media_id>/delete", methods=["POST"])
@login_required
def delete_media(media_id: int):
    media = Media.query.get_or_404(media_id)
    path = os.path.join(app.config["UPLOAD_FOLDER"], media.filename)
    if os.path.exists(path):
        os.remove(path)
    db.session.delete(media)
    db.session.commit()
    flash("Media item removed.", "info")
    return redirect(url_for("media_library"))


@app.route("/admin/analytics")
@login_required
def analytics():
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    content_type = request.args.get("content_type", "")
    category = request.args.get("category", "")

    query = TrackingEvent.query.filter_by(interaction="view")
    if content_type in {"page", "event", "post", "media"}:
        query = query.filter(TrackingEvent.content_type == content_type)
    if category:
        query = query.filter(TrackingEvent.category == category)
    if date_from:
        query = query.filter(func.date(TrackingEvent.created_at) >= date_from)
    if date_to:
        query = query.filter(func.date(TrackingEvent.created_at) <= date_to)

    rows = Analytics.query.order_by(Analytics.views.desc()).all()
    labels = [row.page for row in rows]
    view_values = [row.views for row in rows]
    popularity_values = [row.popularity_score for row in rows]

    total_page_views = query.count()
    unique_visitors = query.with_entities(TrackingEvent.visitor_id).distinct().count()

    event_performance = (
        query.filter(TrackingEvent.content_type == "event")
        .with_entities(
            TrackingEvent.content_id,
            TrackingEvent.content_title,
            TrackingEvent.category,
            func.count(TrackingEvent.id).label("views"),
        )
        .group_by(TrackingEvent.content_id, TrackingEvent.content_title, TrackingEvent.category)
        .order_by(func.count(TrackingEvent.id).desc())
        .all()
    )

    post_performance = (
        query.filter(TrackingEvent.content_type == "post")
        .with_entities(
            TrackingEvent.content_id,
            TrackingEvent.content_title,
            TrackingEvent.category,
            func.count(TrackingEvent.id).label("views"),
        )
        .group_by(TrackingEvent.content_id, TrackingEvent.content_title, TrackingEvent.category)
        .order_by(func.count(TrackingEvent.id).desc())
        .all()
    )

    traffic_daily = (
        query.with_entities(func.date(TrackingEvent.created_at).label("day"), func.count(TrackingEvent.id).label("count"))
        .group_by(func.date(TrackingEvent.created_at))
        .order_by(func.date(TrackingEvent.created_at).asc())
        .all()
    )
    traffic_labels = [str(item.day) for item in traffic_daily]
    traffic_values = [item.count for item in traffic_daily]

    referrers = (
        query.with_entities(TrackingEvent.referrer_domain, func.count(TrackingEvent.id).label("count"))
        .group_by(TrackingEvent.referrer_domain)
        .order_by(func.count(TrackingEvent.id).desc())
        .limit(8)
        .all()
    )

    categories = sorted(
        {
            category_name
            for category_name, in db.session.query(TrackingEvent.category)
            .filter(TrackingEvent.category.isnot(None), TrackingEvent.category != "")
            .distinct()
            .all()
        }
    )

    return render_template(
        "analytics.html",
        rows=rows,
        labels=labels,
        view_values=view_values,
        popularity_values=popularity_values,
        total_page_views=total_page_views,
        unique_visitors=unique_visitors,
        top_events=event_performance[:5],
        top_posts=post_performance[:5],
        event_performance=event_performance,
        post_performance=post_performance,
        traffic_labels=traffic_labels,
        traffic_values=traffic_values,
        referrers=referrers,
        categories=categories,
    )


@app.route("/admin/analytics/export")
@login_required
def analytics_export():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["content_type", "content_id", "title", "category", "interaction", "referrer", "created_at"])

    events = TrackingEvent.query.order_by(TrackingEvent.created_at.desc()).all()
    for item in events:
        writer.writerow(
            [
                item.content_type,
                item.content_id,
                item.content_title or "",
                item.category or "",
                item.interaction,
                item.referrer_domain or "",
                item.created_at.isoformat(),
            ]
        )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=analytics_report.csv"},
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
