from xmlrunner import XMLTestRunner
from unittest import TestLoader

tests_dir = 'tests'
reports_dir = 'test-reports'

loader = TestLoader()
suite = loader.discover(tests_dir)

runner = XMLTestRunner(output=reports_dir)
runner.run(suite)
