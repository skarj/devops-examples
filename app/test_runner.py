from unittest import TestLoader
from xmlrunner import XMLTestRunner

start_dir = 'tests'
reports_dir = 'test-reports'

loader = TestLoader()
suite = loader.discover(start_dir)

runner = XMLTestRunner(output=reports_dir)
runner.run(suite)
