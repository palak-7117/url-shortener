import sqlite3
import random
import string
from flask import Flask, request, jsonify, redirect, render_template

app = Flask(__name__)
DB_NAME = "urls.db"

def init_db():
    """Creates the database table if it doesn't exist yet."""
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
    """Generates a random 6-character string (letters and numbers)."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Initialize the database immediately when the app starts
init_db()

# --- ROUTE 1: THE HOMEPAGE ---
@app.route('/')
def home():
    return render_template('index.html')

# --- ROUTE 2: SMART SHORTEN A LINK (API) ---
@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid JSON request"}), 400
        
    long_url = data.get('long_url')
    custom_alias = data.get('custom_alias')

    if not long_url:
        return jsonify({"error": "URL is required"}), 400

    # Determine the short code to use
    if custom_alias:
        # Clean the input to keep the URL safe
        short_code = "".join(x for x in custom_alias if x.isalnum())
        
        if not short_code:
            return jsonify({"error": "Alias can only contain letters and numbers"}), 400
            
        # Check SQLite to see if this exact alias already exists
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        existing = cursor.execute("SELECT long_url FROM urls WHERE short_code = ?", (short_code,)).fetchone()
        conn.close()
        
        if existing:
            # If the alias exists AND points to the exact same website, return it gracefully!
            if existing['long_url'] == long_url:
                return jsonify({
                    "message": "Hey! I already have this mapping. Here is your link:",
                    "long_url": long_url,
                    "short_url": f"http://swifturl.com/{short_code}", # <-- Updated Domain
                    "short_code": short_code
                }), 200
            else:
                # The alias exists but belongs to a completely different web address
                return jsonify({"error": f"The alias '{short_code}' is already taken by a different URL!"}), 400
    else:
        # If no custom alias was given, generate a random one
        short_code = generate_short_code()
    
    # Save a brand new entry to SQLite
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO urls (long_url, short_code) VALUES (?, ?)", 
            (long_url, short_code)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "long_url": long_url,
            "short_url": f"http://swifturl.com/{short_code}", # <-- Updated Domain
            "short_code": short_code
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "A conflict occurred, please try again."}), 500

# --- ROUTE 3: REDIRECT FROM SHORT TO LONG ---
@app.route('/<short_code>')
def redirect_to_url(short_code):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    row = cursor.execute(
        "SELECT long_url FROM urls WHERE short_code = ?", 
        (short_code,)
    ).fetchone()
    
    if row:
        cursor.execute(
            "UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?", 
            (short_code,)
        )
        conn.commit()
        conn.close()
        return redirect(row['long_url'], code=302)
    
    conn.close()
    return "<h1>404: Link Not Found</h1>", 404