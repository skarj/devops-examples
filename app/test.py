#!/usr/bin/env python

import unittest
import app

class TestHello(unittest.TestCase):

    def setUp(self):
        app.application.testing = True
        self.app = app.application.test_client()

    def test_404(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status, '404 NOT FOUND')

    def test_list(self):
        rv = self.app.get('/api/v1/images')
        self.assertEqual(rv.status, '200 OK')
        self.assertEqual(rv.data, b'[]\n')

if __name__ == '__main__':
    unittest.main()
