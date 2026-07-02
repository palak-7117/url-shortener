# ⚡ SwiftURL | URL Shortener & QR Code Generator

A responsive full-stack web application built with Flask and SQLite. SwiftURL lets users shorten long URLs, create custom aliases, and generate QR codes instantly. Deployed live on Render with an automated backend test suite.

🎯 **Live Demo:** https://swifturls.onrender.com/

---

## ✨ Features

- **🔗 URL Shortening:** Automatically validates and sanitizes input URLs, appends missing `https://` protocol, and generates a unique 6-character short code.
- **🏷️ Custom Aliases:** Users can define a personalized short code. Duplicate aliases pointing to different URLs are blocked with a clear error response.
- **📱 QR Code Generation:** Instantly generates a scannable QR code for any shortened link.
- **📊 Click Tracking:** Records the number of redirects per short code in the database.
- **🪐 Custom 404 Page:** Invalid short codes serve a themed error page instead of a raw browser error.
- **🌌 Interactive UI:** Slate-blue interface with a Canvas API cursor physics effect built in Vanilla JS.

---

## 🛠️ Tech Stack

| Layer      | Technology                                    |
|------------|-----------------------------------------------|
| Frontend   | HTML5, CSS3, JavaScript (ES6), Canvas API     |
| Backend    | Python 3, Flask, Gunicorn (WSGI)              |
| Database   | SQLite3                                       |
| Testing    | Python `unittest`                             |
| Deployment | Render (Cloud Container)                      |

---

## 🚀 Local Setup

1. **Clone the repository:**
```bash
   git clone https://github.com/palak-7117/url-shortener.git
   cd url-shortener
```

2. **Install dependencies:**
```bash
   pip install -r requirements.txt
```

3. **Run the app:**
```bash
   python app.py
```

4. **Open in your browser:** http://localhost:5000
---

## 🧪 Running Tests

```bash
python test_app.py
```

The test suite covers 5 cases: homepage load, URL shortening, custom alias creation, duplicate alias rejection, and 404 handling. Each test runs against an isolated temporary database.

---

## 📁 Project Structure
url-shortener/

├── app.py              # Flask application & API routes

├── test_app.py         # Automated unit test suite

├── requirements.txt    # Python dependencies

├── templates/          # HTML templates (index, 404)

└── .gitignore
---

## ⚙️ Deployment Notes

- SQLite database path is resolved using `os.path.abspath(__file__)` to prevent routing failures in Linux container environments on Render.
- All database connections use Python context managers (`with sqlite3.connect()`) for safe, automatic connection handling.
- App is served via **Gunicorn** in production instead of Flask's built-in dev server.