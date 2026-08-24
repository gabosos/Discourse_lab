import sqlite3
import os
from pathlib import Path

# Usar /tmp en Vercel, directorio actual en local
DB_PATH = os.environ.get('DB_PATH', 'educational_platform.db')
if os.environ.get('VERCEL'):
    DB_PATH = '/tmp/educational_platform.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    message TEXT NOT NULL
                )''')
    # No holiday-specific sample messages are inserted by default.
    # Keep the `messages` table empty unless the application explicitly adds records.
    conn.commit()
    conn.close()

def get_messages():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT message FROM messages")
    messages = [row[0] for row in c.fetchall()]
    conn.close()
    return messages