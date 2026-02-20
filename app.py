from __future__ import annotations

import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
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
from sqlalchemy import text
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


def increment_analytics(page: str, score: float = 0.5) -> None:
    record = Analytics.query.filter_by(page=page).first()
    if not record:
        record = Analytics(page=page, views=0, popularity_score=0)
        db.session.add(record)
    record.views += 1
    record.popularity_score += score
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


@app.route("/")
def index():
    return redirect(url_for("home"))


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
