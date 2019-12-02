import unittest
import xmlrunner

tests_dir = 'tests'
reports_dir = 'test-reports'

loader = unittest.TestLoader()
suite = loader.discover(tests_dir)

runner = xmlrunner.XMLTestRunner(output=reports_dir)
runner.run(suite)
