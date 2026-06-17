import os
import unittest
import sqlite3
from app import app, DB_NAME

class SwiftURLTestCase(unittest.TestCase):

    def setUp(self):
        """Runs BEFORE every single test. Sets up a temporary clean test database."""
        app.config['TESTING'] = True
        self.app = app.test_client()
        
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)
            
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

    def tearDown(self):
        """Runs AFTER every single test. Cleans up the test database file."""
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)

    # --- TEST 1: Check if Homepage Loads ---
    def test_home_page_loads(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SwiftURL', response.data)

    # --- TEST 2: Check standard URL shortening ---
    def test_url_shortening_success(self):
        response = self.app.post('/shorten', json={
            "long_url": "google.com"
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn("display_url", data)
        self.assertIn("real_url", data)
        self.assertEqual(data["long_url"], "https://google.com")

    # --- TEST 3: Check custom alias creation ---
    def test_custom_alias_success(self):
        response = self.app.post('/shorten', json={
            "long_url": "github.com",
            "custom_alias": "mygit"
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        # Updated to check the display_url values we actually return now
        self.assertEqual(data["display_url"], "swifturl.com/mygit")

    # --- TEST 4: Check duplicate custom alias protection ---
    def test_duplicate_alias_error(self):
        self.app.post('/shorten', json={"long_url": "site1.com", "custom_alias": "portfolio"})
        response = self.app.post('/shorten', json={"long_url": "site2.com", "custom_alias": "portfolio"})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)

    # --- TEST 5: Check 404 behavior for invalid links ---
    def test_invalid_short_code_404(self):
        response = self.app.get('/thisCodeDoesNotExist')
        self.assertEqual(response.status_code, 404)
        # Fixed case sensitivity to look for lower-case 'vanished' matching our template!
        self.assertIn(b'vanished into cyber space', response.data)

if __name__ == '__main__':
    unittest.main()