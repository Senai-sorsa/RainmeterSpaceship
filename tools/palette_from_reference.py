"""Sample RefrenceImage.png and print HUD palette as hex.

Method (1260x709 view, RGBA flattened onto black, whole image, pixels quantised to 16 levels/channel):
  background = most common colour among pixels with luma < 40 (the dark field)
  line       = most common colour among bright (luma>90), saturated (>0.5), blue-cyan hue (170-215 deg) pixels
  glow       = most common colour among dim-ish (luma 40-90) saturated cyan-hue pixels (halo around lines)
  accent     = most common colour among saturated (>0.5), luma>60 red-orange hue (0-30 or >345 deg) pixels
Each bucket's mean actual colour is reported (not the quantised key).
"""
import colorsys
import sys
from collections import Counter
from PIL import Image

path = sys.argv[1] if len(sys.argv) > 1 else "RefrenceImage.png"
im = Image.open(path).convert("RGBA")
bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
im = Image.alpha_composite(bg, im).convert("RGB")
buckets = {k: {} for k in ("background", "line", "glow", "accent")}
for r, g, b in im.getdata():
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h *= 360
    name = None
    if luma < 40:
        name = "background"
    elif s > 0.5 and luma > 60 and (h < 30 or h > 345):
        name = "accent"
    elif s > 0.5 and 170 <= h <= 215:
        name = "line" if luma > 90 else ("glow" if luma >= 40 else None)
    if name:
        k = (r >> 4, g >> 4, b >> 4)
        c = buckets[name].setdefault(k, [0, 0, 0, 0])
        c[0] += 1; c[1] += r; c[2] += g; c[3] += b
for name, d in buckets.items():
    if not d:
        print(f"{name}: none found"); continue
    n, r, g, b = max(d.values(), key=lambda c: c[0])
    print(f"{name}: #{round(r/n):02x}{round(g/n):02x}{round(b/n):02x}  ({n} px of {im.width*im.height})")
