import os
import unittest

from schrodinger.profile import Profiler


class TestProfiler(Profiler):
    def upload_file(self, filename):
        with open(filename, 'rb') as rfile:
            self.uploaded_filedata = rfile.read()


class ProfileTestCase(unittest.TestCase):
    def test_profiler_run(self):
        os.environ.setdefault("SCHRODINGER_BUCKET", "-fakebucket-")
        profiler = TestProfiler('testfunction', probability=1)

        @profiler
        def testfunction():
            return "ProfiledFunction"

        self.assertEqual(testfunction(), "ProfiledFunction")

        self.assertTrue(hasattr(profiler, 'uploaded_filedata'))
