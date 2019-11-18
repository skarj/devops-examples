#!/usr/bin/env python

import unittest
import app

class TestConfig(unittest.TestCase):

    def setUp(self):
        app.application.testing = True
        self.app = app.application.test_client()

    def test_404(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status, '404 NOT FOUND')

    def test_list(self):
        rv = self.app.get('/api/v1/config')
        self.assertEqual(rv.status, '200 OK')
        self.assertIn(b'"dynamodb_endpoint": null, \n', rv.data)

if __name__ == '__main__':
    import xmlrunner
    runner = xmlrunner.XMLTestRunner(output='test-reports')
    unittest.main(testRunner=runner)
