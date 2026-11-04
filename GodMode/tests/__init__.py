"""All temp files made by the tests go under one folder that is removed when the run ends."""
import atexit
import shutil
import tempfile

_ROOT = tempfile.mkdtemp(prefix="godmode-tests-")
tempfile.tempdir = _ROOT
atexit.register(shutil.rmtree, _ROOT, True)
