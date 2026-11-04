#!/usr/bin/env python3
"""CSpace's picture-frame shade: the skin's shade.png, made for the PICTURE's windows.

shade.png (tools/frame_render.shade_png) is made from the rendered hull's windows, whose side windows are split by a diagonal strut.
The picture's side windows are one pane, so over the picture shade.png left an unshaded diagonal band across each side window
(task 13, measured ~170 px tall at 1707x1067). This runs the same shade_png() with the picture's own glass, window_mask_pic.png
(written by tools/image_frame.py), the way image_frame.py makes glass_fx_pic / scan_pic.

Writes SpaceshipApp/SpaceshipUI/src/assets/shade_pic.png (a CSpace-only asset; the skin's Images/ are not touched).
Re-run after tools/image_frame.py makes a new picture:  py -3 tools/shade_pic.py   (needs numpy and Pillow, as frame_render.py does)
"""
from pathlib import Path

import numpy as np
from PIL import Image

import frame_render as FR

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "Skins" / "Spaceship" / "@Resources" / "Images" / "window_mask_pic.png"
OUT = ROOT / "SpaceshipApp" / "SpaceshipUI" / "src" / "assets" / "shade_pic.png"


def main():
    glass = np.asarray(Image.open(SRC).convert("L"), dtype=np.float32) / 255
    if glass.shape != (FR.CH, FR.CW):
        raise SystemExit(f"{SRC.name} is {glass.shape[1]}x{glass.shape[0]}, expected {FR.CW}x{FR.CH}")
    FR.shade_png(glass).save(OUT, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
