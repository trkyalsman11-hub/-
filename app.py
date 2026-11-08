"""منصة «بناء وتأثيث» — تطبيق الويب (Flask)

تشغيل محلي:
    pip install -r requirements.txt
    python app.py                      # SQLite محلي على http://127.0.0.1:5000

الإنتاج (Render): يقرأ DATABASE_URL ويعمل على PostgreSQL تلقائيًا.
"""
import os
from datetime import datetime
from functools import wraps
from zoneinfo import ZoneInfo

from flask import (Flask, g, redirect, render_template, request, session,
                   url_for, flash, abort)
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash

import database
import notifications

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE, "platform.db"))
PRODUCTION = database.IS_PG
TZ = ZoneInfo("Asia/Riyadh")

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = os.environ.get("SECRET_KEY") or "dev-only-change-me"
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=PRODUCTION and os.environ.get("INSECURE_COOKIES") != "1")

# ───────────────────────── الأدوار والصلاحيات ─────────────────────────
ROLES = {
    "admin": "مدير النظام",
    "owner": "المالك",
    "developer": "المطور العقاري",
    "office": "المكتب الهندسي",
    "client": "العميل",
}

PERMISSIONS = {
    "admin":     {"view_all", "create", "assign", "update_status", "comment", "manage_users", "dashboard"},
    "owner":     {"create", "comment", "choose_office"},
    "client":    {"create", "comment", "choose_office"},
    "developer": {"update_status", "comment", "assign"},
    "office":    {"update_status", "comment"},
}

STATUSES = ["جديد", "قيد الدراسة", "بانتظار المكتب الهندسي", "تم تقديم عرض السعر",
            "معتمد", "قيد التنفيذ", "مكتمل", "ملغي"]
REQUEST_TYPES = ["تصميم هندسي", "إشراف هندسي", "مقاولات", "تأثيث وديكور", "تطوير عقاري"]
STYLES = ["حديث", "نجدي", "كلاسيكي", "مودرن كلاسيك", "غير محدد"]

# بيانات المكاتب الأولية (تُستخدم إذا لم يوجد ملف data/offices_data.xlsx)
SEED_OFFICES = [
    ("المباركية للاستشارات الهندسية", "0553948576", "الرياض", 320, 5),
    ("مكتب مشعل للخدمات الهندسية", "0546378921", "الرياض", 330, 4.5),
    ("مكتب المنصور للهندسة والعمران", "0546783920", "شقراء", 280, 5),
    ("الفهيد للخدمات الهندسية", "0567384950", "شقراء", 260, 4.3),
    ("الاعمار والبناء للخدمات الهندسية", "0546773645", "الرياض", 400, 4.4),
    ("مشرف المشرف للاشراف الهندسي", "0566477838", "شقراء", 325, 4.2),
    ("ميم صاد للخدمات الهندسية", "0555434367", "الرياض", 380, 4),
    ("حاء قاف للاشراف الهندسي", "0555554637", "الرياض", 450, 3.9),
    ("ميم نون للاشراف الهندسي", "0554433676", "شقراء", 220, 3.7),
    ("الغالية للخدمات الهندسية", "0556789876", "الرياض", 410, 4.8),
]


def can(perm):
    return perm in PERMISSIONS.get(session.get("role"), set())


def status_class(s):
    if s in ("مكتمل", "معتمد"):
        return "s-done"
    if s == "ملغي":
        return "s-bad"
    if s.startswith("بانتظار") or s.startswith("تم تقديم"):
        return "s-wait"
    return ""


FLOW = STATUSES[:7]  # مراحل مؤشر التقدم (بدون «ملغي»)

# رسمة الدور الثلاثية الأبعاد المناسبة لكل نوع خدمة (templates/illus/*.svg)
ILLUS_BY_TYPE = {"تصميم هندسي": "office", "إشراف هندسي": "office", "مقاولات": "contractor",
                 "تأثيث وديكور": "furnish", "تطوير عقاري": "developer"}


def status_step(s):
    """رقم المرحلة من 1 إلى 7، و0 للطلب الملغي."""
    return FLOW.index(s) + 1 if s in FLOW else 0


app.jinja_env.globals.update(can=can, ROLES=ROLES, STATUSES=STATUSES, FLOW=FLOW, status_class=status_class,
                             status_step=status_step, ILLUS_BY_TYPE=ILLUS_BY_TYPE)


# ───────────────────────── قاعدة البيانات ─────────────────────────
def db():
    if "db" not in g:
        g.db = database.Conn(DB_PATH)
    return g.db


@app.teardown_appcontext
def close_db(exc):
    conn = g.pop("db", None)
    if conn:
        if exc:
            conn.rollback()
        conn.close()


def now():
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M")


def init_db():
    conn = database.Conn(DB_PATH)
    conn.executescript(database.SCHEMA)
    conn.commit()
    if conn.execute("SELECT COUNT(*) FROM offices").fetchone()[0] == 0:
        xlsx = os.path.join(BASE, "data", "offices_data.xlsx")
        rows = read_offices_xlsx(xlsx) if os.path.exists(xlsx) else SEED_OFFICES
        for r in rows:
            conn.execute("INSERT INTO offices (name,phone,city,price_per_m2,rating) VALUES (?,?,?,?,?)", r)
    if conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0] == 0:
        admin_pw = os.environ.get("ADMIN_PASSWORD") or ("" if PRODUCTION else "123456")
        if admin_pw:
            conn.execute(
                "INSERT INTO users (username,password,full_name,role,phone,office_id,created_at) VALUES (?,?,?,?,?,?,?)",
                (os.environ.get("ADMIN_USERNAME", "admin"), generate_password_hash(admin_pw),
                 "مدير النظام", "admin", os.environ.get("ADMIN_PHONE", ""), None, now()))
    # حسابات تجريبية: محليًا دائمًا، وفي الإنتاج فقط إذا DEMO_USERS=1
    if (not PRODUCTION or os.environ.get("DEMO_USERS") == "1") and \
            conn.execute("SELECT COUNT(*) FROM users WHERE username='owner'").fetchone()[0] == 0:
        pw = generate_password_hash("123456")
        first_office = conn.execute("SELECT MIN(id) FROM offices").fetchone()[0]
        for u, n, r, p, o in [
            ("owner", "مالك تجريبي", "owner", "0500000002", None),
            ("developer", "مطور تجريبي", "developer", "0500000003", None),
            ("office", "المباركية للاستشارات الهندسية", "office", "0553948576", first_office),
            ("client", "عميل تجريبي", "client", "0500000005", None),
        ]:
            conn.execute(
                "INSERT INTO users (username,password,full_name,role,phone,office_id,created_at) VALUES (?,?,?,?,?,?,?)",
                (u, pw, n, r, p, o, now()))
    conn.commit()
    conn.close()


def read_offices_xlsx(path):
    """يقرأ المكاتب من Excel: اسم المكتب، رقم التواصل، المدينة، السعر للمتر، التقييم."""
    import openpyxl
    ws = openpyxl.load_workbook(path, data_only=True).active
    out = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        name, phone, city, price, rating = row[:5]
        phone = str(phone or "")
        if phone and not phone.startswith("0"):
            phone = "0" + phone
        out.append((str(name).strip(), phone, str(city).strip(), float(price or 0), float(rating or 0)))
    return out


def next_req_no():
    """رقم طلب تسلسلي بالصيغة BT-2026-00001"""
    year = datetime.now(TZ).year
    prefix = f"BT-{year}-"
    last = db().execute("SELECT req_no FROM requests WHERE req_no LIKE ? ORDER BY id DESC LIMIT 1",
                        (prefix + "%",)).fetchone()
    seq = int(last["req_no"].split("-")[-1]) + 1 if last else 1
    return f"{prefix}{seq:05d}"


# ───────────────────────── محرك الترشيح ─────────────────────────
def match_offices(req, limit=3):
    """المدينة 40% + التقييم 35% + السعر 25%."""
    offices = db().execute("SELECT * FROM offices").fetchall()
    if not offices:
        return []
    prices = [o["price_per_m2"] for o in offices]
    pmin, pmax = min(prices), max(prices)
    results = []
    for o in offices:
        reasons = []
        city_score = 40 if (req["city"] or "").strip() == o["city"] else 10
        if city_score == 40:
            reasons.append(f"في نفس المدينة ({o['city']})")
        rating_score = (o["rating"] / 5) * 35
        if o["rating"] >= 4.5:
            reasons.append(f"تقييم مرتفع {o['rating']} من 5")
        price_score = 25 * (1 - (o["price_per_m2"] - pmin) / (pmax - pmin)) if pmax > pmin else 25
        if price_score >= 15:
            reasons.append(f"سعر تنافسي {o['price_per_m2']:.0f} ريال/م²")
        est = (o["price_per_m2"] * req["area_m2"]) if req["area_m2"] else None
        if est and req["budget"] and est > req["budget"] * 0.1:
            price_score *= 0.7
        results.append({"office": o, "score": round(city_score + rating_score + price_score),
                        "reasons": reasons or ["خيار متوازن"], "estimate": est})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


# ───────────────────────── الإشعارات ─────────────────────────
def notify_requester(req, new_status, note=""):
    """يرسل واتساب/SMS للمستفيد صاحب الطلب ويسجّل النتيجة."""
    phone = req["contact_phone"]
    track = url_for("track", _external=True) + f"?no={req['req_no']}"
    msg = notifications.build_message(req["req_no"], new_status, note, track)
    channel = os.environ.get("NOTIFY_CHANNEL", "whatsapp")
    ok, detail = notifications.send(phone, msg, channel)
    db().execute(
        "INSERT INTO notifications (request_id,phone,channel,message,success,detail,created_at) VALUES (?,?,?,?,?,?,?)",
        (req["id"], phone, channel, msg, int(ok), detail, now()))


# ───────────────────────── المصادقة ─────────────────────────
def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return f(*a, **kw)
    return wrapper


def require(perm):
    def deco(f):
        @wraps(f)
        def wrapper(*a, **kw):
            if not can(perm):
                abort(403)
            return f(*a, **kw)
        return login_required(wrapper)
    return deco


def current_user():
    if "user_id" not in session:
        return None
    if "user" not in g:
        g.user = db().execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    return g.user


app.jinja_env.globals.update(current_user=current_user)


def safe_next(target):
    return target if target and target.startswith("/") and not target.startswith("//") else None


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = db().execute("SELECT * FROM users WHERE username=?", (request.form["username"].strip(),)).fetchone()
        if u and check_password_hash(u["password"], request.form["password"]):
            session.clear()
            session.update(user_id=u["id"], role=u["role"])
            return redirect(safe_next(request.args.get("next")) or url_for("home"))
        flash("اسم المستخدم أو كلمة المرور غير صحيحة", "error")
    return render_template("login.html", demo=not PRODUCTION or os.environ.get("DEMO_USERS") == "1")


@app.route("/register", methods=["GET", "POST"])
def register():
    offices_list = db().execute("SELECT id, name, city FROM offices ORDER BY name").fetchall()
    if request.method == "POST":
        f = request.form
        role = f.get("role")
        if role not in ("owner", "client", "developer", "office"):
            abort(400)
        office_id = int(f["office_id"]) if role == "office" and f.get("office_id") else None
        if role == "office" and not office_id:
            flash("اختر مكتبك من القائمة", "error")
            return render_template("register.html", offices=offices_list)
        try:
            db().execute(
                "INSERT INTO users (username,password,full_name,role,phone,office_id,created_at) VALUES (?,?,?,?,?,?,?)",
                (f["username"].strip(), generate_password_hash(f["password"]), f["full_name"].strip(),
                 role, f["phone"].strip(), office_id, now()))
            db().commit()
            flash("تم إنشاء الحساب، سجّل دخولك", "ok")
            return redirect(url_for("login"))
        except database.IntegrityError:
            db().rollback()
            flash("اسم المستخدم مستخدم مسبقًا، اختر اسمًا آخر", "error")
    return render_template("register.html", offices=offices_list)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ───────────────────────── الصفحات ─────────────────────────
@app.route("/healthz")
def healthz():
    db().execute("SELECT 1").fetchone()
    return "ok"


@app.route("/")
def index():
    one = lambda q: db().execute(q).fetchone()[0]
    stats = {
        "offices": one("SELECT COUNT(*) FROM offices"),
        "requests": one("SELECT COUNT(*) FROM requests"),
        "active": one("SELECT COUNT(*) FROM requests WHERE status IN ('معتمد','قيد التنفيذ','مكتمل')"),
    }
    top = db().execute("SELECT * FROM offices ORDER BY rating DESC, price_per_m2 ASC LIMIT 3").fetchall()
    # مثال الترشيح يُحسب من بيانات المكاتب الفعلية (لا نسب مخترعة)
    example = {"city": "شقراء", "area_m2": 600, "budget": 0}
    return render_template("index.html", stats=stats, top=top, example=example, example_matches=match_offices(example))


def visible_requests_query():
    """شرط SQL حسب صلاحية المستخدم — كل دور يرى ما يخصه فقط."""
    role, uid = session.get("role"), session.get("user_id")
    if role == "admin":
        return "1=1", ()
    if role in ("owner", "client"):
        return "r.created_by=?", (uid,)
    if role == "developer":
        return "(r.developer_id=? OR r.developer_id IS NULL)", (uid,)
    if role == "office":
        return "r.office_id=?", (current_user()["office_id"],)
    return "1=0", ()


@app.route("/home")
@login_required
def home():
    where, params = visible_requests_query()
    status = request.args.get("status")
    q = f"""SELECT r.*, o.name AS office_name, u.full_name AS owner_name
            FROM requests r LEFT JOIN offices o ON o.id=r.office_id
            LEFT JOIN users u ON u.id=r.created_by WHERE {where}"""
    if status:
        q += " AND r.status=?"
        params = params + (status,)
    rows = db().execute(q + " ORDER BY r.id DESC", params).fetchall()
    return render_template("home.html", rows=rows, status=status)


@app.route("/requests/new", methods=["GET", "POST"])
@require("create")
def new_request():
    if request.method == "POST":
        f = request.form
        user = current_user()
        for attempt in range(3):  # حماية من تكرار الرقم عند إرسال طلبين بنفس اللحظة
            req_no = next_req_no()
            try:
                db().execute(
                    """INSERT INTO requests (req_no,title,req_type,city,area_m2,budget,style,description,status,
                       created_by,contact_phone,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (req_no, f["title"].strip(), f["req_type"], f["city"].strip(), float(f.get("area_m2") or 0),
                     float(f.get("budget") or 0), f.get("style"), f.get("description", "").strip(), STATUSES[0],
                     user["id"], (f.get("contact_phone") or user["phone"] or "").strip(), now(), now()))
                break
            except database.IntegrityError:
                db().rollback()
        req = db().execute("SELECT * FROM requests WHERE req_no=?", (req_no,)).fetchone()
        db().execute("INSERT INTO request_updates (request_id,user_id,new_status,note,created_at) VALUES (?,?,?,?,?)",
                     (req["id"], user["id"], STATUSES[0], "تم إنشاء الطلب", now()))
        notify_requester(req, STATUSES[0], "تم استلام طلبك بنجاح")
        db().commit()
        flash(f"تم إنشاء الطلب رقم {req_no}", "ok")
        return redirect(url_for("request_detail", req_no=req_no))
    cities = [r[0] for r in db().execute("SELECT DISTINCT city FROM offices").fetchall()]
    return render_template("new_request.html", types=REQUEST_TYPES, styles=STYLES, cities=cities)


def load_visible_request(req_no):
    where, params = visible_requests_query()
    req = db().execute(f"SELECT r.* FROM requests r WHERE r.req_no=? AND {where}", (req_no,) + params).fetchone()
    if not req:
        abort(404)
    return req


@app.route("/requests/<req_no>")
@login_required
def request_detail(req_no):
    req = load_visible_request(req_no)
    updates = db().execute(
        """SELECT ru.*, u.full_name, u.role FROM request_updates ru JOIN users u ON u.id=ru.user_id
           WHERE request_id=? ORDER BY ru.id DESC""", (req["id"],)).fetchall()
    office = db().execute("SELECT * FROM offices WHERE id=?", (req["office_id"],)).fetchone() if req["office_id"] else None
    matches = match_offices(req) if not req["office_id"] else []
    developers = db().execute("SELECT id, full_name FROM users WHERE role='developer'").fetchall()
    offices_list = db().execute("SELECT id, name, city FROM offices ORDER BY name").fetchall()
    notes = db().execute("SELECT * FROM notifications WHERE request_id=? ORDER BY id DESC LIMIT 10",
                         (req["id"],)).fetchall() if can("view_all") else []
    return render_template("request_detail.html", req=req, updates=updates, office=office, matches=matches,
                           developers=developers, offices=offices_list, notes=notes, step=status_step(req["status"]))


@app.route("/requests/<req_no>/update", methods=["POST"])
@login_required
def update_request(req_no):
    req = load_visible_request(req_no)
    f = request.form
    user = current_user()
    new_status = f.get("status") or req["status"]
    note = f.get("note", "").strip()
    office_id, developer_id = req["office_id"], req["developer_id"]

    if new_status != req["status"] and not can("update_status"):
        abort(403)
    if new_status not in STATUSES:
        abort(400)
    if f.get("office_id") and (can("assign") or can("choose_office")):
        new_office = int(f["office_id"])
        if new_office != office_id:
            office_id = new_office
            o = db().execute("SELECT name FROM offices WHERE id=?", (office_id,)).fetchone()
            if not o:
                abort(400)
            note = (note + " — " if note else "") + f"تم إسناد الطلب إلى {o['name']}"
            if new_status == STATUSES[0]:
                new_status = "بانتظار المكتب الهندسي"
    if f.get("developer_id") and can("assign"):
        developer_id = int(f["developer_id"])
    if not note and new_status == req["status"] and office_id == req["office_id"] and developer_id == req["developer_id"]:
        flash("لا يوجد تغيير للحفظ", "error")
        return redirect(url_for("request_detail", req_no=req_no))

    db().execute("UPDATE requests SET status=?, office_id=?, developer_id=?, updated_at=? WHERE id=?",
                 (new_status, office_id, developer_id, now(), req["id"]))
    db().execute("INSERT INTO request_updates (request_id,user_id,old_status,new_status,note,created_at) VALUES (?,?,?,?,?,?)",
                 (req["id"], user["id"], req["status"], new_status, note, now()))
    notify_requester(req, new_status, note)   # ← الربط التلقائي مع المستفيد
    db().commit()
    flash("تم التحديث وإشعار المستفيد", "ok")
    return redirect(url_for("request_detail", req_no=req_no))


@app.route("/offices")
def offices():
    city = request.args.get("city", "")
    sort = request.args.get("sort", "rating")
    order = {"rating": "rating DESC", "price": "price_per_m2 ASC"}.get(sort, "rating DESC")
    q, params = "SELECT * FROM offices", ()
    if city:
        q, params = q + " WHERE city=?", (city,)
    rows = db().execute(f"{q} ORDER BY {order}", params).fetchall()
    cities = [r[0] for r in db().execute("SELECT DISTINCT city FROM offices").fetchall()]
    return render_template("offices.html", rows=rows, cities=cities, city=city, sort=sort)


@app.route("/track")
def track():
    """متابعة عامة برقم الطلب + آخر 4 أرقام من الجوال (بدون تسجيل دخول)."""
    no, digits = request.args.get("no", "").strip().upper(), request.args.get("phone4", "").strip()
    req, updates = None, []
    if no and digits:
        r = db().execute("SELECT * FROM requests WHERE req_no=?", (no,)).fetchone()
        if r and len(digits) == 4 and (r["contact_phone"] or "").endswith(digits):
            req = r
            updates = db().execute(
                "SELECT new_status, note, created_at FROM request_updates WHERE request_id=? ORDER BY id DESC",
                (r["id"],)).fetchall()
        else:
            flash("لم نجد طلبًا بهذا الرقم، أو آخر 4 أرقام من الجوال غير مطابقة", "error")
    return render_template("track.html", req=req, updates=updates, no=no, searched=bool(no and digits))


@app.route("/dashboard")
@require("dashboard")
def dashboard():
    one = lambda q: db().execute(q).fetchone()[0]
    owners = one("SELECT COUNT(*) FROM users WHERE role IN ('owner','client')")
    total = one("SELECT COUNT(*) FROM requests")
    by_status = {r["status"]: r["c"] for r in
                 db().execute("SELECT status, COUNT(*) AS c FROM requests GROUP BY status").fetchall()}
    kpi = {
        "owners": owners, "requests": total,
        "contracts": one("SELECT COUNT(*) FROM requests WHERE status IN ('معتمد','قيد التنفيذ','مكتمل')"),
        "assigned": one("SELECT COUNT(*) FROM requests WHERE office_id IS NOT NULL"),
        "conversion": round(total / owners * 100) if owners else 0,
        "notify_ok": one("SELECT COUNT(*) FROM notifications WHERE success=1"),
        "notify_fail": one("SELECT COUNT(*) FROM notifications WHERE success=0"),
    }
    mx = max([1] + list(by_status.values()))
    return render_template("dashboard.html", kpi=kpi, by_status=by_status, mx=mx)


@app.route("/users")
@require("manage_users")
def users():
    rows = db().execute("""SELECT u.*, o.name AS office_name FROM users u
                           LEFT JOIN offices o ON o.id=u.office_id ORDER BY u.id""").fetchall()
    return render_template("users.html", rows=rows)


@app.errorhandler(403)
def forbidden(_):
    return render_template("message.html", title="غير مصرح", text="ليس لديك صلاحية لهذه الصفحة"), 403


@app.errorhandler(404)
def not_found(_):
    return render_template("message.html", title="غير موجود", text="الصفحة أو الطلب غير موجود"), 404


init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
