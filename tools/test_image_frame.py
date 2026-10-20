"""Self-check for image_frame.py's alpha cleaning and speck removal (synthetic data, no repo images).  Run:
  ~/.venvs/rmsim/bin/python tools/test_image_frame.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import image_frame as F

a = np.array([0, 5, 64, 132, 200, 252, 255], np.uint8)
assert F.clean_alpha(a, 64, 200).tolist() == [0, 0, 0, 128, 255, 255, 255], F.clean_alpha(a, 64, 200)
g = np.zeros((40, 40), bool)
g[2:30, 2:30] = True          # big area
g[35:37, 35:37] = True        # speck
out, kept, dropped = F.drop_specks(g, 50)
assert kept == [784] and dropped == [4] and out[10, 10] and not out[35, 35]
print("ok")
