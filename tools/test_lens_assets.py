"""Self-check for lens_assets.py (tasks/hyperrealism-plan.md Task 5): the blue-noise tile and the lens-dirt map.  Run:
  py -3 -I tools/test_lens_assets.py"""
import os
import struct
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lens_assets as L

# blue noise: every level used equally (a ranking), little low-frequency energy, deterministic
t = L.blue_noise(32)
assert t.shape == (32, 32) and t.dtype == np.uint8, (t.shape, t.dtype)
hist, _ = np.histogram(t, bins=8, range=(0, 256))
assert all(abs(h - 128) <= 1 for h in hist), hist
f = t.astype(float)
box = sum(np.roll(np.roll(f, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9
assert box.std() < 0.25 * f.std(), (box.std(), f.std())  # white noise gives ~0.33
assert np.array_equal(L.blue_noise(32), L.blue_noise(32))
assert not np.array_equal(L.blue_noise(32, seed=1), L.blue_noise(32, seed=2))

# dirt: faint on average, a few stronger smudges, deterministic
d = L.dirt()
assert d.shape == (400, 640) and d.dtype == np.uint8, (d.shape, d.dtype)
assert 4 <= d.mean() <= 20, d.mean()
assert d.max() >= 60, d.max()
assert np.array_equal(d, L.dirt())

# png writer: signature and IHDR size
with tempfile.TemporaryDirectory() as tmp:
    p = os.path.join(tmp, "x.png")
    L.write_png(p, np.zeros((3, 5), np.uint8))
    b = open(p, "rb").read()
    assert b[:8] == b"\x89PNG\r\n\x1a\n"
    w, h = struct.unpack(">II", b[16:24])
    assert (w, h) == (5, 3), (w, h)
    L.write_png(p, np.zeros((3, 5, 4), np.uint8))
    assert open(p, "rb").read()[25] == 6  # colour type RGBA

print("lens_assets ok")
