"""Shared geometry for the Spaceship HUD layout (used by check_layout, vector_frame, build, rmsim)."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = ROOT / "layout" / "layout.json"


def load(path=LAYOUT):
    return json.loads(Path(path).read_text())


def by_id(layout):
    return {i["id"]: i for i in layout["zones"] + layout.get("decor", []) + layout.get("overlays", [])}


def matrix(item, curves):
    """Return Rainmeter TransformationMatrix (a, b, c, d, tx, ty) for an item:
    x' = a*x + c*y + tx,  y' = b*x + d*y + ty."""
    if "quad" in item:
        (x0, y0), (x1, y1), _, (x3, y3) = item["quad"]
        w, h = item["w"], item["h"]
        a, b = (x1 - x0) / w, (y1 - y0) / w
        c, d = (x3 - x0) / h, (y3 - y0) / h
        return (a, b, c, d, x0 - a * item["x"] - c * item["y"], y0 - b * item["x"] - d * item["y"])
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


