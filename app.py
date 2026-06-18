import os
import sqlite3
import random
import string
from flask import Flask, request, jsonify, redirect, render_template

app = Flask(__name__)

# --- FIX: FORCE ABSOLUTE PATH FOR THE DATABASE ON CLOUD SERVERS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "urls.db")

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                long_url TEXT NOT NULL,
                short_code TEXT UNIQUE NOT NULL,
                clicks INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Automatically initialize database structures
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON request"}), 400
        
    long_url = data.get('long_url', '').strip()
    custom_alias = data.get('custom_alias')

    if not long_url:
        return jsonify({"error": "URL is required"}), 400

    # --- PROTOCOL VALIDATION ---
    if not (long_url.startswith('http://') or long_url.startswith('https://')):
        if '.' not in long_url:
            long_url = long_url + '.com'
        long_url = 'https://' + long_url
    elif '.' not in long_url:
        long_url = long_url + '.com'

    if custom_alias:
        short_code = "".join(x for x in custom_alias if x.isalnum())
        if not short_code:
            return jsonify({"error": "Alias can only contain letters and numbers"}), 400
        
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            existing = cursor.execute("SELECT long_url FROM urls WHERE short_code = ?", (short_code,)).fetchone()
        
        if existing:
            if existing['long_url'] == long_url:
                base_url = request.host_url.rstrip('/')
                return jsonify({
                    "message": "Hey! I already have this mapping.",
                    "long_url": long_url,
                    "display_url": f"swifturl.com/{short_code}",
                    "real_url": f"{base_url}/{short_code}"
                }), 200
            else:
                return jsonify({"error": f"The alias '{short_code}' is already taken!"}), 400
    else:
        short_code = generate_short_code()
    
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO urls (long_url, short_code) VALUES (?, ?)", (long_url, short_code))
            conn.commit()
        
        base_url = request.host_url.rstrip('/')
        return jsonify({
            "long_url": long_url,
            "display_url": f"swifturl.com/{short_code}",
            "real_url": f"{base_url}/{short_code}"
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "A conflict occurred, please try again."}), 500

@app.route('/<short_code>')
def redirect_to_url(short_code):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        row = cursor.execute("SELECT long_url FROM urls WHERE short_code = ?", (short_code,)).fetchone()
        
        if row:
            cursor.execute("UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?", (short_code,))
            conn.commit()
            return redirect(row['long_url'], code=302)
    
    return render_template('404.html'), 404

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run()