from __future__ import annotations

import re
import sqlite3
import os
from pathlib import Path

from flask import Flask, redirect, render_template, url_for, request, jsonify
import db

app = Flask(__name__)

# Usar /tmp en Vercel, directorio actual en local
DB_PATH = os.environ.get('DB_PATH', 'mothers_day.db')
if os.environ.get('VERCEL'):
    DB_PATH = '/tmp/mothers_day.db'

db.init_db()

def get_gallery_photos():
    image_dir = Path(app.static_folder) / 'photo-galery'
    if not image_dir.exists():
        return []

    allowed = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    photos = []
    for image_path in sorted(image_dir.iterdir()):
        if image_path.suffix.lower() in allowed:
            photos.append({
                'src': url_for('static', filename=f'photo-galery/{image_path.name}'),
                'alt': image_path.stem.replace('_', ' ').replace('-', ' ').title()
            })
    return photos

def get_music_tracks():
    audio_dir = Path(app.static_folder) / 'audio'
    if not audio_dir.exists():
        return []

    covers_dir = audio_dir / 'covers'
    allowed_audio = {'.mp3', '.m4a', '.ogg', '.wav', '.opus', '.webm'}
    image_exts = ('.jpg', '.jpeg', '.png', '.webp')

    def collect_audio_paths():
        by_key = {}
        for base in (audio_dir, covers_dir):
            if not base.exists():
                continue
            for p in sorted(base.iterdir()):
                if not p.is_file() or p.suffix.lower() not in allowed_audio:
                    continue
                key = p.name.lower()
                if key not in by_key:
                    by_key[key] = p
        return sorted(by_key.values(), key=lambda x: x.name.lower())

    def cover_for_stem(stem: str):
        if not covers_dir.exists():
            return None
        for ext in image_exts:
            cap = covers_dir / f'{stem}{ext}'
            if cap.is_file():
                return url_for('static', filename=f'audio/covers/{cap.name}')
        return None

    def static_src_for_audio(audio_path: Path) -> str:
        rel = audio_path.relative_to(Path(app.static_folder))
        return url_for('static', filename=str(rel.as_posix()))

    tracks = []
    for audio_path in collect_audio_paths():
        stem = audio_path.stem.replace('_', ' ')
        title = stem
        artist = 'Para mamá'
        m = re.match(r'^\s*(.+?)\s+-\s+(.+?)\s*$', stem)
        if m:
            artist, title = m.group(1).strip(), m.group(2).strip()
        tracks.append({
            'id': audio_path.name,
            'title': title,
            'artist': artist,
            'src': static_src_for_audio(audio_path),
            'cover': cover_for_stem(audio_path.stem),
        })
    return tracks

@app.route('/')
def home():
    messages = db.get_messages()
    return render_template('index.html', messages=messages, show_intro=True)

@app.route('/about')
def about():
    return redirect('/carta')

@app.route('/carta')
def carta():
    return render_template('carta.html')

@app.route('/gallery')
def gallery():
    return redirect('/galeria')

@app.route('/galeria')
def galeria():
    return render_template('galeria.html', photos=get_gallery_photos())

@app.route('/cancion')
def cancion():
    return render_template('cancion.html', tracks=get_music_tracks())

@app.route('/messages')
def messages():
    return redirect('/cancion')

def save_message(message):
    conn = sqlite3.connect(db.DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO messages (message) VALUES (?)", (message,))
    conn.commit()
    conn.close()

@app.route('/contact')
def contact():
    return redirect('/')

@app.route('/escribeme')
def escribeme():
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        if message:
            save_message(message)
            return jsonify({'success': True, 'message': 'Tu mensaje ha sido guardado con éxito'})
        else:
            return jsonify({'success': False, 'message': 'Por favor escribe un mensaje'})
    
    messages = db.get_messages()
    return render_template('escribeme.html', messages=messages)

if __name__ == '__main__':
    app.run(debug=True)
