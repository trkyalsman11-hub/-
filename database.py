"""طبقة قاعدة البيانات — تعمل على PostgreSQL في الإنتاج وعلى SQLite محليًا.

- إذا وُجد متغير البيئة DATABASE_URL (تضيفه Render تلقائيًا) نستخدم PostgreSQL.
- غير ذلك نستخدم ملف SQLite محلي (platform.db) للتجربة على الجهاز.
الكود في app.py يكتب الاستعلامات بعلامة ? في الحالتين، وهذه الطبقة تحوّلها.
"""
import os
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]
IS_PG = DATABASE_URL.startswith("postgresql://")

if IS_PG:
    import psycopg
    IntegrityError = psycopg.IntegrityError
else:
    IntegrityError = sqlite3.IntegrityError

PK = "SERIAL PRIMARY KEY" if IS_PG else "INTEGER PRIMARY KEY AUTOINCREMENT"

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS offices (
    id {PK},
    name TEXT NOT NULL,
    phone TEXT,
    city TEXT,
    price_per_m2 REAL,
    rating REAL
);
CREATE TABLE IF NOT EXISTS users (
    id {PK},
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    phone TEXT,
    office_id INTEGER REFERENCES offices(id),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS requests (
    id {PK},
    req_no TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    req_type TEXT,
    city TEXT,
    area_m2 REAL,
    budget REAL,
    style TEXT,
    description TEXT,
    status TEXT NOT NULL,
    created_by INTEGER NOT NULL REFERENCES users(id),
    contact_phone TEXT,
    office_id INTEGER REFERENCES offices(id),
    developer_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS request_updates (
    id {PK},
    request_id INTEGER NOT NULL REFERENCES requests(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    old_status TEXT,
    new_status TEXT,
    note TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications (
    id {PK},
    request_id INTEGER REFERENCES requests(id),
    phone TEXT,
    channel TEXT,
    message TEXT,
    success INTEGER,
    detail TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_requests_created_by ON requests(created_by);
CREATE INDEX IF NOT EXISTS idx_requests_office ON requests(office_id);
CREATE INDEX IF NOT EXISTS idx_updates_request ON request_updates(request_id);
"""


class Row(dict):
    """صف يُقرأ بالاسم row["name"] أو بالترتيب row[0] أو row.name في القوالب."""
    __slots__ = ("_vals",)

    def __init__(self, names, values):
        super().__init__(zip(names, values))
        self._vals = list(values)

    def __getitem__(self, k):
        return self._vals[k] if isinstance(k, int) else super().__getitem__(k)

    def keys(self):
        return super().keys()


def _pg_row_factory(cursor):
    names = [d.name for d in (cursor.description or [])]
    return lambda values: Row(names, values)


def _sqlite_row_factory(cursor, values):
    return Row([d[0] for d in cursor.description], values)


class Conn:
    """غلاف موحّد: execute / commit / close بنفس الشكل للقاعدتين."""

    def __init__(self, sqlite_path=None):
        if IS_PG:
            self.raw = psycopg.connect(DATABASE_URL, row_factory=_pg_row_factory)
        else:
            self.raw = sqlite3.connect(sqlite_path)
            self.raw.row_factory = _sqlite_row_factory
            self.raw.execute("PRAGMA foreign_keys=ON")

    def execute(self, sql, params=()):
        if IS_PG:
            sql = sql.replace("?", "%s")
        return self.raw.execute(sql, params)

    def executescript(self, script):
        if IS_PG:
            for stmt in [s.strip() for s in script.split(";") if s.strip()]:
                self.raw.execute(stmt)
        else:
            self.raw.executescript(script)

    def commit(self):
        self.raw.commit()

    def rollback(self):
        self.raw.rollback()

    def close(self):
        self.raw.close()
