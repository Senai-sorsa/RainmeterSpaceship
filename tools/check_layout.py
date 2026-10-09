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
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def matrix(item, curves):
    """Return Rainmeter TransformationMatrix (a, b, c, d, tx, ty) for an item:
    x' = a*x + c*y + tx,  y' = b*x + d*y + ty."""
    cv = curves.get(item.get("group", "center"), {"type": "flat"})
    zcx, zcy = item["x"] + item["w"] / 2, item["y"] + item["h"] / 2
    if cv["type"] == "arc_x":
        u = zcx - cv["center_x"]
        dy = cv["depth"] * (u / cv["half_span"]) ** 2
        s = 2 * cv["depth"] * u / cv["half_span"] ** 2
        return (1, s, 0, 1, 0, dy - s * zcx)
    if cv["type"] == "wrap_y":
        v = zcy - cv["center_y"]
        dx = cv["dir"] * cv["depth"] * (v / cv["half_span"]) ** 2
        sx = cv["dir"] * 2 * cv["depth"] * v / cv["half_span"] ** 2
        return (1, cv["tilt"], sx, 1, dx - sx * zcy, -cv["tilt"] * cv["pivot_x"])
    return (1, 0, 0, 1, 0, 0)


def shape(item, curves, grow=0):
    if "poly" in item:
        pts = item["poly"]
        if grow:
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            pts = [(px + math.copysign(grow, px - cx), py + math.copysign(grow, py - cy)) for px, py in pts]
        return [tuple(p) for p in pts]
    a, b, c, d, tx, ty = matrix(item, curves)
    x, y, w, h = item["x"] - grow, item["y"] - grow, item["w"] + 2 * grow, item["h"] + 2 * grow
    return [(a * px + c * py + tx, b * px + d * py + ty)
            for px, py in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]


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


def in_safe_area(poly, canvas, safe):
    inset, r = safe["inset"], safe["corner_radius"]
    left, top = inset, inset
    right, bottom = canvas["w"] - inset, canvas["h"] - inset
    for px, py in poly:
        if not (left <= px <= right and top <= py <= bottom):
            return False
        cx = left + r if px < left + r else right - r if px > right - r else None
        cy = top + r if py < top + r else bottom - r if py > bottom - r else None
        if cx is not None and cy is not None and math.hypot(px - cx, py - cy) > r:
            return False
    return True


def check(layout):
    errors = []
    canvas, safe, curves = layout["canvas"], layout["safe_area"], layout["curves"]
    gap, dgap = layout["min_gap"], layout["decor_gap"]
    zones, decor = layout["zones"], layout.get("decor", [])
    ids = [i["id"] for i in zones + decor + layout.get("overlays", [])]
    if len(ids) != len(set(ids)):
        errors.append("duplicate ids")
    for z in zones:
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
