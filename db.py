import sqlite3
import os
from pathlib import Path

# Usar /tmp en Vercel, directorio actual en local
DB_PATH = os.environ.get('DB_PATH', 'mothers_day.db')
if os.environ.get('VERCEL'):
    DB_PATH = '/tmp/mothers_day.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    message TEXT NOT NULL
                )''')
    # Insert some sample messages
    messages = [
        "¡Feliz Día de la Madre! Eres la mejor.",
        "Gracias por todo lo que haces, mamá.",
        "Te quiero mucho, feliz Día de la Madre.",
        "Eres mi inspiración, mamá.",
        "¡Feliz Día de la Madre! Disfruta tu día."
    ]
    for msg in messages:
        c.execute("INSERT OR IGNORE INTO messages (message) VALUES (?)", (msg,))
    conn.commit()
    conn.close()

def get_messages():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT message FROM messages")
    messages = [row[0] for row in c.fetchall()]
    conn.close()
    return messages