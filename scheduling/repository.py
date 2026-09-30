import db

SCHEMA = """
CREATE TABLE IF NOT EXISTS date_polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    range_start TEXT NOT NULL,
    range_end TEXT NOT NULL,
    trip_length INTEGER NOT NULL CHECK (trip_length >= 1),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_poll_id INTEGER NOT NULL REFERENCES date_polls(id) ON DELETE CASCADE,
    participant TEXT NOT NULL,
    day TEXT NOT NULL,
    UNIQUE (date_poll_id, participant, day)
);
"""


def create_tables():
    conn = db.get_connection()
    conn.executescript(SCHEMA)
    conn.close()


def insert_poll(title, range_start, range_end, trip_length):
    conn = db.get_connection()
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO date_polls (title, range_start, range_end, trip_length) "
                "VALUES (?, ?, ?, ?)",
                (title, range_start, range_end, trip_length),
            )
        return cursor.lastrowid
    finally:
        conn.close()


def get_poll(poll_id):
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT id, title, range_start, range_end, trip_length "
            "FROM date_polls WHERE id = ?",
            (poll_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_availability(poll_id):
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT participant, day FROM availability "
            "WHERE date_poll_id = ? ORDER BY participant, day",
            (poll_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def replace_availability(poll_id, participant, days):
    conn = db.get_connection()
    try:
        with conn:
            conn.execute(
                "DELETE FROM availability WHERE date_poll_id = ? AND participant = ?",
                (poll_id, participant),
            )
            conn.executemany(
                "INSERT INTO availability (date_poll_id, participant, day) VALUES (?, ?, ?)",
                [(poll_id, participant, day) for day in days],
            )
    finally:
        conn.close()
