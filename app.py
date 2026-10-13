"""
CivicLens - Civic Issue Reporter for Smart Cities
A Flask application for reporting and tracking civic issues.
"""

import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, render_template, send_from_directory, g
from flask_cors import CORS
from werkzeug.utils import secure_filename

# ── Config ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
DATABASE = os.environ.get("DATABASE_PATH", str(BASE_DIR / "civiclens.db"))
UPLOAD_FOLDER = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

CATEGORIES = ["pothole", "garbage", "streetlight", "water", "drainage", "other"]
STATUSES = ["Open", "In-Progress", "Resolved"]

UPLOAD_FOLDER.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
CORS(app)


# ── Database helpers ────────────────────────────────────────────────
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            address TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            upvotes INTEGER NOT NULL DEFAULT 0,
            image_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def row_to_dict(row):
    return dict(row) if row else None


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Initialize DB on startup
init_db()

# ── Routes ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(str(UPLOAD_FOLDER), filename)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "CivicLens", "timestamp": datetime.utcnow().isoformat()})


# ── Issues API ──────────────────────────────────────────────────────

@app.route("/api/issues", methods=["GET"])
def list_issues():
    db = get_db()
    query = "SELECT * FROM issues"
    params = []
    conditions = []

    category = request.args.get("category")
    status = request.args.get("status")
    search = request.args.get("search")

    if category and category != "all":
        conditions.append("category = ?")
        params.append(category)
    if status and status != "all":
        conditions.append("status = ?")
        params.append(status)
    if search:
        conditions.append("(title LIKE ? OR description LIKE ? OR address LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    sort = request.args.get("sort", "newest")
    if sort == "upvotes":
        query += " ORDER BY upvotes DESC, created_at DESC"
    elif sort == "oldest":
        query += " ORDER BY created_at ASC"
    else:
        query += " ORDER BY created_at DESC"

    rows = db.execute(query, params).fetchall()
    return jsonify([row_to_dict(r) for r in rows])


@app.route("/api/issues", methods=["POST"])
def create_issue():
    # Support both JSON and multipart/form-data (with image)
    if request.content_type and "multipart/form-data" in request.content_type:
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        latitude = request.form.get("latitude", "").strip()
        longitude = request.form.get("longitude", "").strip()
        address = request.form.get("address", "").strip()
        file = request.files.get("image")
    else:
        data = request.get_json(force=True, silent=True) or {}
        title = str(data.get("title", "")).strip()
        description = str(data.get("description", "")).strip()
        category = str(data.get("category", "")).strip()
        latitude = str(data.get("latitude", "")).strip()
        longitude = str(data.get("longitude", "")).strip()
        address = str(data.get("address", "")).strip()
        file = None

    # Validation
    errors = []
    if not title or len(title) < 3:
        errors.append("Title must be at least 3 characters.")
    if not description or len(description) < 10:
        errors.append("Description must be at least 10 characters.")
    if category not in CATEGORIES:
        errors.append(f"Category must be one of: {', '.join(CATEGORIES)}")
    try:
        lat = float(latitude)
        lng = float(longitude)
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            errors.append("Invalid coordinates.")
    except (ValueError, TypeError):
        errors.append("Latitude and longitude are required and must be numbers.")
        lat = lng = 0
    if not address or len(address) < 3:
        errors.append("Address is required.")

    if errors:
        return jsonify({"errors": errors}), 400

    # Handle image upload
    image_path = None
    if file and file.filename and allowed_file(file.filename):
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        image_path = filename

    issue_id = uuid.uuid4().hex[:8]
    now = datetime.utcnow().isoformat()

    db = get_db()
    db.execute("""
        INSERT INTO issues (id, title, description, category, latitude, longitude, address, status, upvotes, image_path, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Open', 0, ?, ?, ?)
    """, (issue_id, title, description, category, lat, lng, address, image_path, now, now))
    db.commit()

    row = db.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    return jsonify(row_to_dict(row)), 201


@app.route("/api/issues/<issue_id>", methods=["GET"])
def get_issue(issue_id):
    db = get_db()
    row = db.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if not row:
        return jsonify({"error": "Issue not found"}), 404
    return jsonify(row_to_dict(row))


@app.route("/api/issues/<issue_id>/status", methods=["PATCH"])
def update_status(issue_id):
    data = request.get_json(force=True, silent=True) or {}
    new_status = str(data.get("status", "")).strip()

    if new_status not in STATUSES:
        return jsonify({"error": f"Status must be one of: {', '.join(STATUSES)}"}), 400

    db = get_db()
    row = db.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if not row:
        return jsonify({"error": "Issue not found"}), 404

    now = datetime.utcnow().isoformat()
    db.execute("UPDATE issues SET status = ?, updated_at = ? WHERE id = ?", (new_status, now, issue_id))
    db.commit()

    updated = db.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    return jsonify(row_to_dict(updated))


@app.route("/api/issues/<issue_id>/upvote", methods=["POST"])
def upvote_issue(issue_id):
    db = get_db()
    row = db.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if not row:
        return jsonify({"error": "Issue not found"}), 404

    db.execute("UPDATE issues SET upvotes = upvotes + 1, updated_at = ? WHERE id = ?", (datetime.utcnow().isoformat(), issue_id))
    db.commit()

    updated = db.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    return jsonify(row_to_dict(updated))


@app.route("/api/issues/<issue_id>", methods=["DELETE"])
def delete_issue(issue_id):
    db = get_db()
    row = db.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if not row:
        return jsonify({"error": "Issue not found"}), 404

    # Delete associated image
    if row["image_path"]:
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], row["image_path"]))
        except OSError:
            pass

    db.execute("DELETE FROM issues WHERE id = ?", (issue_id,))
    db.commit()
    return jsonify({"message": "Issue deleted"}), 200


@app.route("/api/stats", methods=["GET"])
def stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) as c FROM issues").fetchone()["c"]
    open_c = db.execute("SELECT COUNT(*) as c FROM issues WHERE status='Open'").fetchone()["c"]
    progress_c = db.execute("SELECT COUNT(*) as c FROM issues WHERE status='In-Progress'").fetchone()["c"]
    resolved_c = db.execute("SELECT COUNT(*) as c FROM issues WHERE status='Resolved'").fetchone()["c"]

    by_category = {}
    for cat in CATEGORIES:
        by_category[cat] = db.execute("SELECT COUNT(*) as c FROM issues WHERE category=?", (cat,)).fetchone()["c"]

    return jsonify({
        "total": total,
        "open": open_c,
        "inProgress": progress_c,
        "resolved": resolved_c,
        "byCategory": by_category
    })


# ── Error handlers ─────────────────────────────────────────────────
@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Max 5MB."}), 413


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    return render_template("index.html"), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
