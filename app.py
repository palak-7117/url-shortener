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

# --- ROUTE 2: SHORTEN A LINK (API) ---
@app.route('/shorten', methods=['POST'])
def shorten_url():
    # Get the long URL from the client request
    data = request.get_json()
    
    # Simple safety check if data is empty
    if not data:
        return jsonify({"error": "Invalid JSON request"}), 400
        
    long_url = data.get('long_url')
    
    if not long_url:
        return jsonify({"error": "URL is required"}), 400

    # Generate a unique short code
    short_code = generate_short_code()
    
    # Save to SQLite
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO urls (long_url, short_code) VALUES (?, ?)", 
            (long_url, short_code)
        )
        conn.commit()
        conn.close()
        
        # Return the new short link details back to the user
        return jsonify({
            "long_url": long_url,
            "short_url": f"http://localhost:5000/{short_code}",
            "short_code": short_code
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Collision occurred, try again."}), 500

# --- ROUTE 3: REDIRECT FROM SHORT TO LONG ---
@app.route('/<short_code>')
def redirect_to_url(short_code):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Fetch the long URL
    row = cursor.execute(
        "SELECT long_url FROM urls WHERE short_code = ?", 
        (short_code,)
    ).fetchone()
    
    if row:
        # 2. Basic Click Counter: Increment the click count by +1
        cursor.execute(
            "UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?", 
            (short_code,)
        )
        conn.commit()
        conn.close()
        
        # 3. Redirect the browser
        return redirect(row['long_url'], code=302)
    
    conn.close()
    return "<h1>404: Link Not Found</h1>", 404