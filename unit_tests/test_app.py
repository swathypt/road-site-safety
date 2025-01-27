import unittest
import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.app.test_client()
        self.app.testing = True

    def test_home(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Flask API is running", response.data)

    def test_get_violations(self):
        response = self.app.get('/violations')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json, list))

if __name__ == '__main__':
    unittest.main()
