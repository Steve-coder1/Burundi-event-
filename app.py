from __future__ import annotations

import os
from datetime import datetime
from functools import wraps
from uuid import uuid4

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
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


content_categories = db.Table(
    "content_categories",
    db.Column("category_id", db.Integer, db.ForeignKey("category.id"), primary_key=True),
    db.Column("event_id", db.Integer, db.ForeignKey("event.id"), nullable=True),
    db.Column("post_id", db.Integer, db.ForeignKey("post.id"), nullable=True),
)


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
    language = db.Column(db.String(10), default="en")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
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




def slugify_text(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return cleaned or "item"


def event_slug(event: Event) -> str:
    return slugify_text(event.title)


def post_slug(post: Post) -> str:
    return slugify_text(post.title)


def event_public_url(event: Event, lang: str | None = None, external: bool = False) -> str:
    chosen = normalize_public_lang(lang or event.language or PRIMARY_PUBLIC_LANG)
    return url_for("event_detail", lang=get_lang_segment(chosen), slug=event_slug(event), event_id=event.id, _external=external)


def post_public_url(post: Post, lang: str | None = None, external: bool = False) -> str:
    chosen = normalize_public_lang(lang or post.language or PRIMARY_PUBLIC_LANG)
    return url_for("blog_post_detail", lang=get_lang_segment(chosen), slug=post_slug(post), post_id=post.id, _external=external)


def build_seo_meta(title: str, description: str, language: str, keywords: str = "", image_url: str = "", url: str = "", content_type: str = "website") -> dict:
    return {
        "title": title,
        "description": description[:160],
        "keywords": keywords,
        "lang": language,
        "url": url or request.url,
        "image": image_url,
        "type": content_type,
    }



def build_breadcrumbs() -> list[dict[str, str]]:
    endpoint = request.endpoint or ""
    if endpoint.startswith("admin") or endpoint in {"login", "logout", "api_search", "api_autocomplete", "api_track", "sitemap_xml", "robots_txt", "static"}:
        return []

    current_lang = get_public_lang()
    segment = get_lang_segment(current_lang)
    crumbs = [{"label": "Home", "url": url_for("index", lang=segment)}]

    if endpoint in {"home", "public_events", "event_detail"}:
        crumbs.append({"label": "Events", "url": url_for("home", lang=segment)})
    if endpoint in {"blog_home", "blog_post_detail"}:
        crumbs.append({"label": "Blog", "url": url_for("blog_home", lang=segment)})
    if endpoint == "media_gallery":
        crumbs.append({"label": "Media", "url": url_for("media_gallery", lang=segment)})
    if endpoint == "sponsors_page":
        crumbs.append({"label": "Sponsors", "url": url_for("sponsors_page", lang=segment)})
    if endpoint == "guides_page":
        crumbs.append({"label": "Guides", "url": url_for("guides_page", lang=segment)})
    if endpoint == "faqs_page":
        crumbs.append({"label": "FAQs", "url": url_for("faqs_page", lang=segment)})
    if endpoint == "about_page":
        crumbs.append({"label": "About", "url": url_for("about_page", lang=segment)})
    if endpoint == "contact_page":
        crumbs.append({"label": "Contact", "url": url_for("contact_page", lang=segment)})
    if endpoint == "search_page":
        crumbs.append({"label": "Search", "url": url_for("search_page", lang=segment)})

    if endpoint == "event_detail":
        event = Event.query.get(request.view_args.get("event_id")) if request.view_args else None
        if event:
            crumbs.append({"label": event.title, "url": event_public_url(event, current_lang)})
    if endpoint == "blog_post_detail":
        post = Post.query.get(request.view_args.get("post_id")) if request.view_args else None
        if post:
            crumbs.append({"label": post.title, "url": post_public_url(post, current_lang)})

    return crumbs

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
    db.session.commit()


@app.before_request
def ensure_seed_data():
    db.create_all()
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    admin = AdminUser.query.filter_by(username="admin").first()
    if not admin:
        admin = AdminUser(username="admin", two_factor_enabled=False)
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()


@app.route("/")
def index():
    if session.get("admin_user"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
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
    return redirect(url_for("login"))


@app.route("/dashboard")
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
@app.route("/events")
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


@app.route("/events/add", methods=["GET", "POST"])
@login_required
def add_event():
    categories = Category.query.filter_by(content_type="event").all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        date_str = request.form.get("event_date", "")
        language = request.form.get("language", "en")
        selected_ids = request.form.getlist("categories")

        if not title or not description or not date_str:
            flash("Title, description, and date are required.", "danger")
            return render_template("event_form.html", categories=categories, event=None)

        event = Event(
            title=title,
            description=description,
            event_date=datetime.strptime(date_str, "%Y-%m-%dT%H:%M"),
            language=language,
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


@app.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(event_id: int):
    event = Event.query.get_or_404(event_id)
    categories = Category.query.filter_by(content_type="event").all()
    if request.method == "POST":
        event.title = request.form.get("title", event.title)
        event.description = request.form.get("description", event.description)
        event.language = request.form.get("language", event.language)
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


@app.route("/events/<int:event_id>/delete", methods=["POST"])
@login_required
def delete_event(event_id: int):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted.", "info")
    return redirect(url_for("events_list"))


@app.route("/posts")
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


@app.route("/posts/add", methods=["GET", "POST"])
@login_required
def add_post():
    categories = Category.query.filter_by(content_type="post").all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        published_at = request.form.get("published_at", "")
        selected_ids = request.form.getlist("categories")

        if not title or not body:
            flash("Title and body are required.", "danger")
            return render_template("post_form.html", categories=categories, post=None)

        post = Post(
            title=title,
            body=body,
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


@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id: int):
    post = Post.query.get_or_404(post_id)
    categories = Category.query.filter_by(content_type="post").all()
    if request.method == "POST":
        post.title = request.form.get("title", post.title)
        post.body = request.form.get("body", post.body)
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


@app.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id: int):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("posts_list"))


@app.route("/categories", methods=["GET", "POST"])
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


@app.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def delete_category(category_id: int):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for("manage_categories"))


@app.route("/media", methods=["GET", "POST"])
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


@app.route("/media/<int:media_id>/delete", methods=["POST"])
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


@app.route("/analytics")
@login_required
def analytics():
    rows = Analytics.query.order_by(Analytics.views.desc()).all()
    labels = [row.page for row in rows]
    view_values = [row.views for row in rows]
    popularity_values = [row.popularity_score for row in rows]
    return render_template(
        "analytics.html",
        rows=rows,
        labels=labels,
        view_values=view_values,
        popularity_values=popularity_values,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
