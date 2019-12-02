from app import application
import unittest

class TestConfig(unittest.TestCase):

    def setUp(self):
        application.testing = True
        self.app = application.test_client()

    def test_list(self):
        rv = self.app.get('/api/v1/config')
        self.assertEqual(rv.status, '200 OK')
        self.assertIn(b'"dynamodb_endpoint" :null', rv.data)

if __name__ == '__main__':
    unittest.main()
