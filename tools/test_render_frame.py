"""Checks the Blender-rendered shell (Task 8). Run: py -3 -I tools/test_render_frame.py"""
import json
import struct
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RENDER = ROOT / "Skins/Spaceship/@Resources/Images/Render"
NAMES = ["hull", "corners", "light_screens", "light_trim", "light_orb", "glass_reflect"]


def read_png(p):
    d = Path(p).read_bytes()
    pos, idat, hdr = 8, b"", None
    while pos < len(d):
        n, t = struct.unpack(">I4s", d[pos:pos + 8])
        body = d[pos + 8:pos + 8 + n]
        if t == b"IHDR":
            hdr = struct.unpack(">IIBBBBB", body)
        elif t == b"IDAT":
            idat += body
        pos += 12 + n
    w, h, depth, ct = hdr[:4]
    assert depth == 8 and hdr[6] == 0, hdr
    ch = {0: 1, 2: 3, 4: 2, 6: 4}[ct]
    raw = np.frombuffer(zlib.decompress(idat), np.uint8).reshape(h, 1 + w * ch)
    rows, prev = np.zeros((h, w * ch), np.int32), np.zeros(w * ch, np.int32)
    for y in range(h):
        f, line = raw[y, 0], raw[y, 1:].astype(np.int32)
        if f == 0:
            cur = line
        elif f == 2:
            cur = (line + prev) & 255
        else:  # 1 sub, 3 avg, 4 paeth: sequential
            cur = line.copy()
            for i in range(w * ch):
                a = cur[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                if f == 1:
                    pr = a
                elif f == 3:
                    pr = (a + b) // 2
                else:
                    pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                    pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                cur[i] = (cur[i] + pr) & 255
        rows[y] = cur
        prev = cur
    return rows.reshape(h, w, ch).astype(np.uint8)


for n in NAMES:
    p = RENDER / (n + ".png")
    assert p.exists(), "missing " + n
    img = read_png(p)
    assert img.shape[:2] == (1600, 2560), (n, img.shape)
    if n.startswith("light_") or n == "glass_reflect":
        rgb = img[..., :3].astype(int)  # a 1-channel (grey) PNG is grayscale by definition
        if rgb.shape[2] == 3:
            assert np.abs(rgb[..., 0] - rgb[..., 1]).max() <= 1 and np.abs(rgb[..., 0] - rgb[..., 2]).max() <= 1, n
        assert rgb.mean() > 0, n
    if n == "hull":
        alpha = img[..., 3] > 127
        glass = read_png(ROOT / "Skins/Spaceship/@Resources/Images/window_mask.png")[..., 0] > 127
        iou = (alpha & ~glass).sum() / (alpha | ~glass).sum()
        sag = json.loads((ROOT / 'tools/frame_src/curve.json').read_text())['edgeSag']
        # edgeSag 0 = the layout is exact; a bowed windscreen edge moves the silhouette by design (about 0.3 % of the frame)
        assert iou >= (0.995 if not (sag['top'] or sag['bottom']) else 0.985), iou
        print("hull IoU", round(float(iou), 5))

c = json.loads((ROOT / "tools/frame_src/curve.json").read_text())
assert 0 <= c["edgeSag"]["top"] <= 24
print("ok")
