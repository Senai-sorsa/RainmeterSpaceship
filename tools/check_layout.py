#!/usr/bin/env python3
"""Validate layout/layout.json and render a preview.

Zones are authored as flat rectangles, then bent by their group's curve into the
affine shape Rainmeter will draw (TransformationMatrix). All checks run on the
bent shapes:
  * every zone stays inside the canvas safe area (inset + rounded corners)
  * no two zones overlap, and every pair keeps at least `min_gap` px apart
  * no zone comes within `min_gap` of a frame keep-out (struts / beams)
  * decor (frame-baked bars, rails, glyphs) never intrudes into a zone
  * overlays stay on the canvas (they are transient, so they may cover zones)

Usage: python tools/check_layout.py [--preview out.png] [--ref reference.png] [--matrices]
"""
import argparse
import json
import sys
from pathlib import Path

from layoutlib import ROOT, convex_overlap, in_safe_area, matrix, shape


def check(layout):
    errors = []
    canvas, safe, curves = layout["canvas"], layout["safe_area"], layout["curves"]
    gap, dgap = layout["min_gap"], layout["decor_gap"]
    zones, decor = layout["zones"], layout.get("decor", [])
    ids = [i["id"] for i in zones + decor + layout.get("overlays", [])]
    if len(ids) != len(set(ids)):
        errors.append("duplicate ids")
    tb = canvas["h"] - layout.get("taskbar", {}).get("height", 0) - 2
    for z in zones:
        if max(p[1] for p in shape(z, curves)) > tb:
            errors.append(f"{z['id']}: reaches into the taskbar band")
        if not in_safe_area(shape(z, curves), canvas, safe):
            errors.append(f"{z['id']}: outside safe area")
        for k in layout["keepouts"]:
            if convex_overlap(shape(z, curves, gap), k["poly"]):
                errors.append(f"{z['id']}: within {gap}px of frame keep-out {k['id']}")
        for dc in decor:
            if convex_overlap(shape(z, curves, dgap), shape(dc, curves)):
                errors.append(f"{z['id']}: decor {dc['id']} intrudes")
    for i, a in enumerate(zones):
        for b in zones[i + 1:]:
            if convex_overlap(shape(a, curves, gap / 2), shape(b, curves, gap / 2)):
                errors.append(f"{a['id']} and {b['id']}: overlap or closer than {gap}px")
    for o in layout.get("overlays", []):
        if o["x"] < 0 or o["y"] < 0 or o["x"] + o["w"] > canvas["w"] or o["y"] + o["h"] > canvas["h"]:
            errors.append(f"overlay {o['id']}: outside canvas")
    return errors


GROUP_COLORS = {
    "top": (0, 230, 255), "left": (80, 170, 255), "right": (80, 170, 255),
    "center": (255, 140, 40), "bottom": (170, 120, 255),
}


def render(layout, out, ref=None):
    from PIL import Image, ImageDraw
    curves = layout["curves"]
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
    for dc in layout.get("decor", []):
        d.polygon(shape(dc, curves), fill=(0, 255, 200, 110), outline=(0, 255, 200, 255))
    for z in layout["zones"]:
        c = GROUP_COLORS.get(z["group"], (255, 255, 255))
        poly = shape(z, curves)
        d.polygon(poly, fill=c + (40,), outline=c + (255,), width=3)
        d.text((poly[0][0] + 6, poly[0][1] + 4), z["id"], fill=(255, 255, 255, 255), font_size=22)
    for o in layout.get("overlays", []):
        x0, y0, x1, y1 = o["x"], o["y"], o["x"] + o["w"], o["y"] + o["h"]
        for i in range(x0, x1, 30):
            d.line([(i, y0), (min(i + 15, x1), y0)], fill=(255, 80, 80, 200), width=2)
            d.line([(i, y1), (min(i + 15, x1), y1)], fill=(255, 80, 80, 200), width=2)
        d.text((x0 + 6, y1 - 28), o["id"] + " (transient)", fill=(255, 120, 120, 255), font_size=20)
    img.alpha_composite(layer)
    img.convert("RGB").save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", default=ROOT / "layout" / "layout.json")
    ap.add_argument("--preview")
    ap.add_argument("--ref")
    ap.add_argument("--matrices", action="store_true", help="print each zone's TransformationMatrix")
    args = ap.parse_args()
    layout = json.loads(Path(args.layout).read_text())
    errors = check(layout)
    for e in errors:
        print("FAIL", e)
    if args.matrices:
        for z in layout["zones"]:
            print(f"{z['id']:<12} TransformationMatrix=" + ";".join(f"{v:.4f}" for v in matrix(z, layout["curves"])))
    if args.preview:
        render(layout, args.preview, args.ref)
        print("preview written to", args.preview)
    print(f"{len(layout['zones'])} zones, {len(layout.get('decor', []))} decor, {len(errors)} problems")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
