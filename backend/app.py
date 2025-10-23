import os, sqlite3, io, csv, smtplib, requests, pytz
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, jsonify, request, g, session, send_file, send_from_directory
from flask_cors import CORS
from passlib.hash import pbkdf2_sha256
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from email.message import EmailMessage

APP_DB = os.environ.get("APP_DB", "/app/data/cards.db")
FLASK_SECRET = os.environ.get("FLASK_SECRET", "please-change")
TIMEZONE = os.environ.get("TIMEZONE", "America/Indiana/Indianapolis")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "changeme")

# Seedable settings from env (only used to initialize DB settings when empty)
ENV_SETTINGS = {
    "SMTP_HOST": os.environ.get("SMTP_HOST", ""),
    "SMTP_PORT": os.environ.get("SMTP_PORT", "587"),
    "SMTP_USER": os.environ.get("SMTP_USER", ""),
    "SMTP_PASS": os.environ.get("SMTP_PASS", ""),
    "ALERT_EMAIL": os.environ.get("ALERT_EMAIL", ""),
    "WEBHOOK_URL": os.environ.get("WEBHOOK_URL", ""),
    "TWILIO_SID": os.environ.get("TWILIO_SID", ""),
    "TWILIO_TOKEN": os.environ.get("TWILIO_TOKEN", ""),
    "TWILIO_FROM": os.environ.get("TWILIO_FROM", ""),
    "TWILIO_TO": os.environ.get("TWILIO_TO", ""),
}

# serve built React from /app/frontend_build
app = Flask(__name__, static_folder="frontend_build", static_url_path="/")
app.secret_key = FLASK_SECRET
CORS(app, supports_credentials=True)

# ---------- DB ----------
def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        os.makedirs(os.path.dirname(APP_DB) or ".", exist_ok=True)
        db = g._db = sqlite3.connect(APP_DB, check_same_thread=False)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    db.execute("""
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        last4 TEXT NOT NULL,
        due_day INTEGER NOT NULL,
        notes TEXT DEFAULT '',
        paid INTEGER NOT NULL DEFAULT 0,
        payment_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    db.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_id INTEGER NOT NULL,
        payment_date DATE NOT NULL,
        method TEXT,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(card_id) REFERENCES cards(id)
    )""")
    db.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    db.commit()

    # Seed admin (idempotent)
    count = db.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    if count == 0 and ADMIN_USER and ADMIN_PASS:
        pw = pbkdf2_sha256.hash(ADMIN_PASS)
        if db.execute("SELECT 1 FROM users WHERE username=?", (ADMIN_USER,)).fetchone() is None:
            db.execute("INSERT INTO users (username,password,is_admin) VALUES (?,?,1)", (ADMIN_USER, pw))
            db.commit()

    # Seed settings from env only if settings empty
    s_count = db.execute("SELECT COUNT(*) c FROM settings").fetchone()["c"]
    if s_count == 0:
        for k, v in ENV_SETTINGS.items():
            db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (k, v or ""))
        db.commit()

# ---------- decorators ----------
def login_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        if not session.get("user_id"):
            return jsonify({"error":"unauthenticated"}), 401
        return f(*a, **kw)
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        if not session.get("user_id"):
            return jsonify({"error":"unauthenticated"}), 401
        if not session.get("is_admin"):
            return jsonify({"error":"admin required"}), 403
        return f(*a, **kw)
    return wrap

# ---------- auth ----------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    u, p = data.get("user"), data.get("pass")
    if not u or not p:
        return jsonify({"error":"missing"}), 400
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
    if not row or not pbkdf2_sha256.verify(p, row["password"]):
        return jsonify({"error":"invalid"}), 401
    session.clear()
    session["user_id"] = row["id"]
    session["username"] = row["username"]
    session["is_admin"] = bool(row["is_admin"])
    return jsonify({"ok": True, "username": row["username"], "is_admin": bool(row["is_admin"])})

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json or {}
    u, p = data.get("user"), data.get("pass")
    if not u or not p:
        return jsonify({"error":"missing"}), 400
    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
        return jsonify({"error":"username exists"}), 400
    pw = pbkdf2_sha256.hash(p)
    db.execute("INSERT INTO users (username,password,is_admin) VALUES (?,?,0)", (u, pw))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/api/whoami")
def whoami():
    if not session.get("user_id"):
        return jsonify({"user": None})
    return jsonify({"user":{"username":session["username"],"is_admin":session["is_admin"]}})

# ---------- admin users ----------
@app.route("/api/users", methods=["GET","POST"])
@admin_required
def users():
    db = get_db()
    if request.method == "POST":
        d = request.json or {}
        u, p = d.get("username"), d.get("password")
        is_admin = 1 if d.get("is_admin") else 0
        if not u or not p:
            return jsonify({"error":"missing"}), 400
        if db.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
            return jsonify({"error":"exists"}), 400
        pw = pbkdf2_sha256.hash(p)
        cur = db.execute("INSERT INTO users (username,password,is_admin) VALUES (?,?,?)", (u, pw, is_admin))
        db.commit()
        row = db.execute("SELECT id,username,is_admin,created_at FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
        return jsonify(dict(row)), 201
    rows = db.execute("SELECT id,username,is_admin,created_at FROM users ORDER BY username").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/users/<int:uid>", methods=["PUT","DELETE"])
@admin_required
def user_modify(uid):
    db = get_db()
    if request.method == "DELETE":
        db.execute("DELETE FROM users WHERE id=?", (uid,))
        db.commit()
        return jsonify({"ok": True})
    d = request.json or {}
    is_admin = 1 if d.get("is_admin") else 0
    pw = d.get("password")
    if pw:
        pw_hash = pbkdf2_sha256.hash(pw)
        db.execute("UPDATE users SET password=?, is_admin=? WHERE id=?", (pw_hash, is_admin, uid))
    else:
        db.execute("UPDATE users SET is_admin=? WHERE id=?", (is_admin, uid))
    db.commit()
    row = db.execute("SELECT id,username,is_admin,created_at FROM users WHERE id=?", (uid,)).fetchone()
    return jsonify(dict(row))

# ---------- settings (notifications) ----------
@app.route("/api/settings", methods=["GET","PUT"])
@admin_required
def settings():
    db = get_db()
    if request.method == "PUT":
        data = request.json or {}
        for k, v in data.items():
            db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (k, v if v is not None else ""))
        db.commit()
    rows = db.execute("SELECT key,value FROM settings").fetchall()
    return jsonify({r["key"]: r["value"] for r in rows})

# ---------- cards & payments ----------
def r2card(r):
    return {
        "id": r["id"], "name": r["name"], "last4": r["last4"],
        "due_day": r["due_day"], "notes": r["notes"],
        "paid": bool(r["paid"]), "payment_date": r["payment_date"]
    }

@app.route("/api/cards", methods=["GET","POST"])
def cards():
    if not session.get("user_id"):
        return jsonify({"error":"unauthenticated"}), 401
    db = get_db()
    if request.method == "POST":
        d = request.json or {}
        name, last4, due_day = d.get("name"), d.get("last4"), int(d.get("due_day") or 0)
        notes = d.get("notes","")
        if not (name and last4 and 1 <= due_day <= 31):
            return jsonify({"error":"invalid"}), 400
        cur = db.execute("INSERT INTO cards (name,last4,due_day,notes) VALUES (?,?,?,?)", (name,last4,due_day,notes))
        db.commit()
        r = db.execute("SELECT * FROM cards WHERE id=?", (cur.lastrowid,)).fetchone()
        return jsonify(r2card(r)), 201
    rows = db.execute("SELECT * FROM cards ORDER BY name").fetchall()
    return jsonify([r2card(r) for r in rows])

@app.route("/api/cards/<int:cid>", methods=["PUT","DELETE"])
def card_modify(cid):
    if not session.get("user_id"):
        return jsonify({"error":"unauthenticated"}), 401
    db = get_db()
    if request.method == "DELETE":
        db.execute("DELETE FROM cards WHERE id=?", (cid,))
        db.commit()
        return jsonify({"ok": True})
    d = request.json or {}
    if "paid" in d:
        paid = 1 if d.get("paid") else 0
        payment_date = date.today().isoformat() if paid else None
        db.execute("UPDATE cards SET paid=?, payment_date=? WHERE id=?", (paid, payment_date, cid))
        if paid:
            db.execute("INSERT INTO payments (card_id,payment_date,method,note) VALUES (?,?,?,?)",
                       (cid, payment_date, d.get("method","manual"), d.get("note","")))
        db.commit()
        r = db.execute("SELECT * FROM cards WHERE id=?", (cid,)).fetchone()
        return jsonify(r2card(r))
    db.execute("UPDATE cards SET name=?, last4=?, due_day=?, notes=? WHERE id=?",
               (d.get("name"), d.get("last4"), d.get("due_day"), d.get("notes",""), cid))
    db.commit()
    r = db.execute("SELECT * FROM cards WHERE id=?", (cid,)).fetchone()
    return jsonify(r2card(r))

@app.route("/api/statuses")
def statuses():
    if not session.get("user_id"):
        return jsonify({"error":"unauthenticated"}), 401
    db = get_db()
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz).date()
    rows = db.execute("SELECT * FROM cards").fetchall()
    out = []
    for r in rows:
        y, m = today.year, today.month
        due_day = r["due_day"]
        try:
            due_date = date(y, m, due_day)
        except ValueError:
            if m == 12:
                due_date = date(y, m, 31)
            else:
                nxt = date(y, m+1, 1)
                due_date = nxt - timedelta(days=1)
        if r["paid"]:
            color = "green"
        else:
            delta = (due_date - today).days
            color = "red" if today >= due_date else ("yellow" if delta <= 5 else "white")
        out.append({
            "id": r["id"], "name": r["name"], "last4": r["last4"],
            "due_day": r["due_day"], "due_date": due_date.isoformat(),
            "notes": r["notes"], "paid": bool(r["paid"]), "payment_date": r["payment_date"],
            "color": color
        })
    return jsonify(out)

@app.route("/api/report")
def report():
    if not session.get("user_id"):
        return jsonify({"error":"unauthenticated"}), 401
    month = request.args.get("month")
    if not month:
        return jsonify({"error":"month YYYY-MM required"}), 400
    start = datetime.strptime(month + "-01", "%Y-%m-%d").date()
    end = date(start.year + int(start.month == 12), (start.month % 12)+1, 1)
    db = get_db()
    rows = db.execute("""
        SELECT p.*, c.name, c.last4 FROM payments p
        JOIN cards c ON c.id=p.card_id
        WHERE p.payment_date >= ? AND p.payment_date < ?
        ORDER BY p.payment_date
    """, (start.isoformat(), end.isoformat())).fetchall()
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["name","last4","payment_date","method","note"])
    for r in rows:
        w.writerow([r["name"], r["last4"], r["payment_date"], r["method"] or "", r["note"] or ""])
    buf.seek(0)
    return send_file(io.BytesIO(buf.getvalue().encode()), as_attachment=True,
                     download_name=f"payments-{month}.csv", mimetype="text/csv")

# ---------- notifications & monthly reset ----------
def get_setting(key, default=""):
    db = get_db()
    r = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return (r["value"] if r else default) or ""

def send_alert_email(missed):
    host = get_setting("SMTP_HOST"); port = int(get_setting("SMTP_PORT","587") or 587)
    user = get_setting("SMTP_USER"); pwd = get_setting("SMTP_PASS")
    to = get_setting("ALERT_EMAIL")
    if not host or not to:
        app.logger.info("SMTP not configured; skipping email")
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = "CC Tracker: Missed payments"
        msg["From"] = user or to; msg["To"] = to
        body = ["The following cards were not paid last month:"] + [f"- {c['name']} ****{c['last4']} (due {c['due_day']})" for c in missed]
        msg.set_content("\n".join(body))
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            if user and pwd: s.login(user, pwd)
            s.send_message(msg)
        return True
    except Exception as e:
        app.logger.exception("Email failed: %s", e)
        return False

def post_webhook(payload):
    url = get_setting("WEBHOOK_URL")
    if not url: return False
    try:
        requests.post(url, json=payload, timeout=6); return True
    except Exception as e:
        app.logger.warning("Webhook failed: %s", e); return False

def send_sms(body):
    sid = get_setting("TWILIO_SID"); token = get_setting("TWILIO_TOKEN"); from_ = get_setting("TWILIO_FROM"); to = get_setting("TWILIO_TO")
    if not (sid and token and from_ and to): return False
    try:
        from twilio.rest import Client
        Client(sid, token).messages.create(body=body, from_=from_, to=to); return True
    except Exception as e:
        app.logger.exception("SMS failed: %s", e); return False

def monthly_reset_job():
    db = sqlite3.connect(APP_DB); db.row_factory = sqlite3.Row
    rows = db.execute("SELECT * FROM cards").fetchall()
    missed = []
    for r in rows:
        if r["paid"]:
            db.execute("UPDATE cards SET paid=0, payment_date=NULL WHERE id=?", (r["id"],))
        else:
            missed.append(dict(r))
    db.commit(); db.close()
    if missed:
        send_alert_email(missed)
        post_webhook({"type":"missed_payments","cards":[{"name":c["name"],"last4":c["last4"],"due_day":c["due_day"]} for c in missed]})
        send_sms(f"CC Tracker: {len(missed)} card(s) unpaid last month.")

@app.route('/icon.png')
def icon_png():
    # The Dockerfile copies an icon to /app/icon.png
    return send_from_directory('.', 'icon.png')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

with app.app_context():
    init_db()
scheduler = BackgroundScheduler(timezone=TIMEZONE)
scheduler.add_job(monthly_reset_job, CronTrigger(day='1', hour='0', minute='5', timezone=TIMEZONE))
scheduler.start()
