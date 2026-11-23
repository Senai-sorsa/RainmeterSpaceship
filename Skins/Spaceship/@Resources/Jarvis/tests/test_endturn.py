"""Smart Turn end-of-turn (E1/E2): a fake microphone (40 blocks of speech, then quiet) shows that "finished" ends the
listen at the 0.27 s pause, "not finished" holds it up to 3 s of quiet, and off / unavailable keeps the old 0.7 s timer.
With the downloaded model present, it also runs once on silence (CPU, no side effects)."""
import os
import sys
import tempfile
import types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.argv[1:] = [tempfile.mkdtemp()]                            # temp RES: no real Settings.inc, no real jarvis.log

reads = [0]


class FakeStream:
    def __init__(self, **kw):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def close(self):
        pass

    def read(self, n):
        reads[0] += 1
        return np.full((n, 1), 0.1 if reads[0] <= 40 else 0.0, np.float32), False


sys.modules["sounddevice"] = types.SimpleNamespace(InputStream=FakeStream)
from jarvislib import endturn, mic  # noqa: E402

mic.mic_device = lambda: None
asked = []


def run(on, p):
    reads[0] = 0
    asked.clear()
    endturn.enabled = lambda: on
    endturn.complete = lambda a: asked.append(len(a)) or p
    audio = mic._listen(patience=6)
    assert audio is not None
    return reads[0]


assert run(False, 0.9) == 40 + 24 and not asked                 # off: the 0.7 s fast end, never asks
assert run(True, 0.9) == 40 + mic.TURN_GAP                      # finished: stops at the first pause
assert asked == [(40 + mic.TURN_GAP) * 480]                     # all the speech so far, with the pause
assert run(True, 0.2) == 40 + mic.TURN_CAP + 1                  # not finished: waits the 3 s cap
assert run(True, None) == 40 + 24                               # model unavailable: the plain timer

import importlib  # noqa: E402
real = importlib.reload(endturn)
if os.path.exists(real.MODEL):
    try:
        import faster_whisper  # noqa: F401
        import onnxruntime  # noqa: F401
    except ImportError:
        print("test_endturn: OK (model check skipped: no onnxruntime/faster_whisper here)")
        sys.exit(0)
    p = real.complete(np.zeros(16000, np.float32))
    assert p is not None and 0.0 <= p <= 1.0, p
print("test_endturn: OK")
