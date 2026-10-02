import db

SCHEMA = """
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    destination TEXT,
    start_date TEXT,
    end_date TEXT,
    date_poll_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    UNIQUE (trip_id, name)
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    claimed_by INTEGER REFERENCES members(id) ON DELETE SET NULL,
    done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1))
);
"""


def create_tables():
    conn = db.get_connection()
    conn.executescript(SCHEMA)
    conn.close()

def insert_trip_with_members(name, destination, member_names):
    conn = db.get_connection()
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO trips (name, destination) VALUES (?, ?)",
                (name, destination),
            )
            trip_id = cursor.lastrowid
            conn.executemany(
                "INSERT INTO members (trip_id, name) VALUES (?, ?)",
                [(trip_id, member_name) for member_name in member_names],
            )
        return trip_id
    finally:
        conn.close()


def get_trip(trip_id):
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT id, name, destination, start_date, end_date, date_poll_id "
            "FROM trips WHERE id = ?",
            (trip_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def insert_member(trip_id, name):
    conn = db.get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO members (trip_id, name) VALUES (?, ?)",
                (trip_id, name),
            )
    finally:
        conn.close()


def get_members(trip_id):
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name FROM members WHERE trip_id = ? ORDER BY id",
            (trip_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def insert_task(trip_id, title):
    conn = db.get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO tasks (trip_id, title) VALUES (?, ?)",
                (trip_id, title),
            )
    finally:
        conn.close()


def get_tasks(trip_id):
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT tasks.id, tasks.title, tasks.done, members.name AS claimed_by "
            "FROM tasks LEFT JOIN members ON members.id = tasks.claimed_by "
            "WHERE tasks.trip_id = ? ORDER BY tasks.id",
            (trip_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def set_task_claim(task_id, member_id):
    conn = db.get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE tasks SET claimed_by = ? WHERE id = ?",
                (member_id, task_id),
            )
    finally:
        conn.close()


def set_task_done(task_id):
    conn = db.get_connection()
    try:
        with conn:
            conn.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
    finally:
        conn.close()
