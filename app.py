import sqlite3
import random
import string
from flask import Flask, request, jsonify, redirect, render_template

app = Flask(__name__)
DB_NAME = "urls.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
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
    conn.close()

def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

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

    # --- FIX 1: STRICT URL VALIDATION ---
    # Force prefix protocol
    if not (long_url.startswith('http://') or long_url.startswith('https://')):
        # If it doesn't even have a dot (e.g., "apple"), append .com safely
        if '.' not in long_url:
            long_url = long_url + '.com'
        long_url = 'https://' + long_url
    elif '.' not in long_url:
        # If they typed http://apple, add .com
        long_url = long_url + '.com'

    if custom_alias:
        short_code = "".join(x for x in custom_alias if x.isalnum())
        if not short_code:
            return jsonify({"error": "Alias can only contain letters and numbers"}), 400
            
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        existing = cursor.execute("SELECT long_url FROM urls WHERE short_code = ?", (short_code,)).fetchone()
        conn.close()
        
        if existing:
            if existing['long_url'] == long_url:
                return jsonify({
                    "message": "Hey! I already have this mapping.",
                    "long_url": long_url,
                    "display_url": f"swifturl.com/{short_code}",
                    "real_url": f"http://localhost:5000/{short_code}"
                }), 200
            else:
                return jsonify({"error": f"The alias '{short_code}' is already taken!"}), 400
    else:
        short_code = generate_short_code()
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO urls (long_url, short_code) VALUES (?, ?)", (long_url, short_code))
        conn.commit()
        conn.close()
        
        return jsonify({
            "long_url": long_url,
            "display_url": f"swifturl.com/{short_code}",
            "real_url": f"http://localhost:5000/{short_code}"
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "A conflict occurred, please try again."}), 500

@app.route('/<short_code>')
def redirect_to_url(short_code):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    row = cursor.execute("SELECT long_url FROM urls WHERE short_code = ?", (short_code,)).fetchone()
    
    if row:
        cursor.execute("UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?", (short_code,))
        conn.commit()
        conn.close()
        return redirect(row['long_url'], code=302)
    
    conn.close()
    return render_template('404.html'), 404

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404