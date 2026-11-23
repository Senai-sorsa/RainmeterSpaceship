"""E6: play_samples stamps the turn's first sound once (later clips keep it), with the smooth-mode lead added. Fake
speakers: no audio device is opened."""
import os
import sys
import tempfile
import time
import types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.argv[1:] = [tempfile.mkdtemp()]                            # temp RES: no real Settings.inc, no real jarvis.log


class FakeOut:
    def __init__(self, **kw):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def write(self, chunk):
        pass


sys.modules["sounddevice"] = types.SimpleNamespace(OutputStream=FakeOut, query_devices=lambda **k: {"name": "Speakers"})
from jarvislib.voice import output  # noqa: E402

output.S.set = lambda **k: None                                # no HUD state file written
output.far_add = lambda *a: None
output.smooth_on = lambda: False
clip = np.zeros(1600, np.float32)

output.first_sound[0] = None
t = time.time()
output.play_samples(clip, 16000)
first = output.first_sound[0]
assert first is not None and t <= first <= time.time(), first
output.play_samples(clip, 16000)
assert output.first_sound[0] == first, "a later clip must not move the first sound"
output.first_sound[0] = None
t = time.time()
output.play_samples(clip, 16000, None, 200)                    # smooth off: the lead is ignored, the clip plays now
assert t <= output.first_sound[0] < t + 0.2, output.first_sound[0] - t
output.first_sound[0] = None
output.smooth_on = lambda: True
output.player.play = lambda *a: None                           # the persistent stream, faked
t = time.time()
output.play_samples(clip, 16000, None, 200)                    # smooth: the sound starts after its 200 ms lead
assert output.first_sound[0] >= t + 0.2, output.first_sound[0] - t
print("test_first_sound: OK")
