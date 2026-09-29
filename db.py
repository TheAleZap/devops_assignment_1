import os
import sqlite3
import config


def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON") #Ignore foreign keys unless turned on
    return conn

def init_db():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    conn = get_connection()
    conn.close()