"""Self-check for parity_diff.py: plain asserts.  Run:  ~/.venvs/rmsim/bin/python -I tools/test_parity_diff.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import parity_diff as pd

with tempfile.TemporaryDirectory() as d:
    p = lambda n: os.path.join(d, n)  # noqa: E731
    Image.new("RGB", (40, 20), (10, 20, 30)).save(p("a.png"))
    Image.new("RGB", (80, 40), (10, 20, 30)).save(p("same_bigger.png"))   # resized to match -> identical
    mad, pct = pd.compare(p("a.png"), p("same_bigger.png"), p("d0.png"))
    assert mad == 0 and pct == 0, (mad, pct)
    Image.new("RGB", (40, 20), (110, 20, 30)).save(p("b.png"))            # red channel +100 everywhere
    mad, pct = pd.compare(p("a.png"), p("b.png"), p("d1.png"))
    assert abs(mad - 100 / 3) < 1e-6 and pct == 100.0, (mad, pct)
    assert pd.compare(p("a.png"), p("b.png"), p("d2.png"), threshold=100)[1] == 0.0  # not strictly over
    assert Image.open(p("d1.png")).size == (40, 20)
print("ok")
