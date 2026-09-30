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
