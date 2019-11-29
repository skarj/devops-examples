from app.app import application
import unittest

class TestEndpoints(unittest.TestCase):

    def setUp(self):
        application.testing = True
        self.app = application.test_client()

    def test_404(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status, '404 NOT FOUND')

if __name__ == '__main__':
    unittest.main()
