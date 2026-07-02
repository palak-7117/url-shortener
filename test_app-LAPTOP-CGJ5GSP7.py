import os
import unittest
import sqlite3
from app import app, DB_NAME

import app as app_module

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_urls.db")

class SwiftURLTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Runs ONCE before all tests. Creates the test database."""
        app_module.DB_NAME = TEST_DB
        app.config['TESTING'] = True

        with sqlite3.connect(TEST_DB) as conn:
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

    def setUp(self):
        """Runs BEFORE every single test. Wipes table data for a clean slate."""
        self.app = app.test_client()
        with sqlite3.connect(TEST_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM urls")
            conn.commit()

    @classmethod
    def tearDownClass(cls):
        """Runs ONCE after all tests. Restores original DB and deletes test DB."""
        app_module.DB_NAME = DB_NAME
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except PermissionError:
                pass

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
        self.assertIn(b'vanished into cyber space', response.data)

if __name__ == '__main__':
    unittest.main()