#!/usr/bin/env python3
"""Validate layout/layout.json and render a preview.

Checks:
  * every zone stays inside the canvas safe area (inset + rounded corners)
  * no two zones overlap, and every pair keeps at least `min_gap` px apart
  * no zone touches a frame keep-out polygon (struts / beams), with the same gap
  * overlays stay inside the canvas (they are transient, so they may cover zones)

Usage: python tools/check_layout.py [--preview out.png] [--ref reference.png]
"""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def rect_poly(z, grow=0):
    x, y, w, h = z["x"] - grow, z["y"] - grow, z["w"] + 2 * grow, z["h"] + 2 * grow
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def convex_overlap(a, b):
    """Separating axis test for two convex polygons."""
    for poly in (a, b):
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            nx, ny = y2 - y1, x1 - x2
            pa = [nx * px + ny * py for px, py in a]
            pb = [nx * px + ny * py for px, py in b]
            if max(pa) <= min(pb) or max(pb) <= min(pa):
                return False
    return True


def in_safe_area(z, canvas, safe):
    inset, r = safe["inset"], safe["corner_radius"]
    left, top = inset, inset
    right, bottom = canvas["w"] - inset, canvas["h"] - inset
    for px, py in rect_poly(z):
        if not (left <= px <= right and top <= py <= bottom):
            return False
        cx = left + r if px < left + r else right - r if px > right - r else None
        cy = top + r if py < top + r else bottom - r if py > bottom - r else None
        if cx is not None and cy is not None and math.hypot(px - cx, py - cy) > r:
            return False
    return True


def check(layout):
    errors = []
    canvas, safe, gap = layout["canvas"], layout["safe_area"], layout["min_gap"]
    zones = layout["zones"]
    ids = [z["id"] for z in zones]
    if len(ids) != len(set(ids)):
        errors.append("duplicate zone ids")
    for z in zones:
        if not in_safe_area(z, canvas, safe):
            errors.append(f"{z['id']}: outside safe area")
        for k in layout["keepouts"]:
            if convex_overlap(rect_poly(z, gap), k["poly"]):
                errors.append(f"{z['id']}: within {gap}px of frame keep-out {k['id']}")
    for i, a in enumerate(zones):
        for b in zones[i + 1:]:
            # growing both by gap/2 means edges closer than `gap` count as overlap
            if convex_overlap(rect_poly(a, gap / 2), rect_poly(b, gap / 2)):
                errors.append(f"{a['id']} and {b['id']}: overlap or closer than {gap}px")
    for o in layout.get("overlays", []):
        if o["x"] < 0 or o["y"] < 0 or o["x"] + o["w"] > canvas["w"] or o["y"] + o["h"] > canvas["h"]:
            errors.append(f"overlay {o['id']}: outside canvas")
    return errors


GROUP_COLORS = {
    "top": (0, 230, 255), "graphs": (0, 200, 160), "left": (80, 170, 255),
    "right": (80, 170, 255), "center": (255, 140, 40), "bottom": (170, 120, 255),
}


def render(layout, out, ref=None):
    from PIL import Image, ImageDraw
    W, H = layout["canvas"]["w"], layout["canvas"]["h"]
    img = Image.new("RGBA", (W, H), (6, 10, 20, 255))
    if ref:
        bg = Image.open(ref).convert("RGBA").resize((W, H))
        bg.putalpha(90)
        img.alpha_composite(bg)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    s = layout["safe_area"]
    d.rounded_rectangle([s["inset"], s["inset"], W - s["inset"], H - s["inset"]],
                        radius=s["corner_radius"], outline=(90, 110, 130, 255), width=3)
    for k in layout["keepouts"]:
        d.polygon([tuple(p) for p in k["poly"]], fill=(60, 70, 85, 170), outline=(120, 130, 150, 255))
    for z in layout["zones"]:
        c = GROUP_COLORS.get(z["group"], (255, 255, 255))
        box = [z["x"], z["y"], z["x"] + z["w"], z["y"] + z["h"]]
        d.rectangle(box, fill=c + (40,), outline=c + (255,), width=3)
        d.text((z["x"] + 6, z["y"] + 4), z["id"], fill=(255, 255, 255, 255), font_size=22)
    for o in layout.get("overlays", []):
        box = [o["x"], o["y"], o["x"] + o["w"], o["y"] + o["h"]]
        for i in range(o["x"], o["x"] + o["w"], 30):
            d.line([(i, o["y"]), (min(i + 15, box[2]), o["y"])], fill=(255, 80, 80, 255), width=3)
            d.line([(i, box[3]), (min(i + 15, box[2]), box[3])], fill=(255, 80, 80, 255), width=3)
        d.text((o["x"] + 6, box[3] - 30), o["id"] + " (transient)", fill=(255, 120, 120, 255), font_size=22)
    img.alpha_composite(layer)
    img.convert("RGB").save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", default=ROOT / "layout" / "layout.json")
    ap.add_argument("--preview")
    ap.add_argument("--ref")
    args = ap.parse_args()
    layout = json.loads(Path(args.layout).read_text())
    errors = check(layout)
    for e in errors:
        print("FAIL", e)
    if args.preview:
        render(layout, args.preview, args.ref)
        print("preview written to", args.preview)
    print(f"{len(layout['zones'])} zones, {len(errors)} problems")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
