"""#74 wake.start_training starts one wake-training thread at a time. Fakes only: no microphone, no real training."""
import os
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.argv[1:] = [tempfile.mkdtemp()]                            # temp RES: no real Settings.inc, no real jarvis.log

from jarvislib import wake  # noqa: E402

started, release, ran = [], threading.Event(), []


def fake_train():
    ran.append(1)
    release.wait(5)


real_thread = threading.Thread


def spy(*a, **k):
    started.append(1)
    return real_thread(*a, **k)


wake.threading.Thread = spy
try:
    assert wake.start_training(fake_train) is True
    assert wake.start_training(fake_train) is False, "second start while the first runs"
    wake.TRAINING.set()
    assert wake.start_training(fake_train) is False, "TRAINING set"
    wake.TRAINING.clear()
    assert len(started) == 1, started
    release.set()
    for _ in range(100):                                       # the lock is released when the thread ends
        if wake.start_training(lambda: None):
            break
        threading.Event().wait(0.05)
    else:
        raise AssertionError("lock never released")
finally:
    wake.threading.Thread = real_thread
    wake.TRAINING.clear()
assert ran == [1]
print("one wake training at a time: OK")
