"""Procedural detail for the cockpit frame, layered over the traced hull by tools/vector_frame.py.

The trace gives the ship's silhouette and its flat colour regions. This module adds the surface work a
render has and a posterized trace loses, all as Shape meters in canvas pixels (2560x1600):

  Sheen.inc     brushed-metal sheen down the struts and beams, specular edge highlights, rim light where
                the hull meets the glass (silver core + faint theme-colour bloom)
  Greebles.inc  panel insets, cross seams, rivets, vent grilles, hazard bands
  Lights.inc    strut lights with spill, anamorphic flare and star glints; status LEDs with halos
  Spill.inc     theme-coloured light the HUD throws onto the dash (sphere, screens, console)
  Glare.inc     faint diagonal reflections on the glass
  Scan.inc      optional scanlines over the windows (Settings.inc: ScanLines, ScanAlpha)

Nothing is placed under a widget zone, so live instruments always sit on clean metal.
"""
import math
import random

from shapely.affinity import scale as shp_scale
from shapely.geometry import LineString, MultiLineString, Point, Polygon, box
from shapely.ops import substring, unary_union

import ref_layout as R

CW, CH = R.CW, R.CH
PER_METER = 150


def C(pts):
    """reference px -> canvas px"""
    return [(x * R.SX, y * R.SY) for x, y in pts]


def cpoly(pts):
    return Polygon(C(pts)).buffer(0)


def lines_of(geom):
    if geom.is_empty:
        return []
    if isinstance(geom, LineString):
        return [geom]
    if isinstance(geom, MultiLineString):
        return list(geom.geoms)
    out = []
    for g in getattr(geom, "geoms", []):
        out += lines_of(g)
    return out


def norm(vx, vy):
    l = math.hypot(vx, vy) or 1.0
    return vx / l, vy / l


class Layer:
    """Collects shapes for one part file; splits them over several meters of PER_METER shapes."""

    def __init__(self, name, hidden=None):
        self.name, self.hidden, self.items = name, hidden, []

    def path(self, pts, spec, closed=False, grad=None):
        if len(pts) < 2:
            return
        d = " | ".join(("%.1f,%.1f" if i == 0 else "LineTo %.1f,%.1f") % p for i, p in enumerate(pts))
        self.items.append(("path", d + (" | ClosePath 1" if closed else ""), spec, grad))

    def raw(self, spec):
        self.items.append(("raw", None, spec, None))

    def ellipse(self, x, y, rx, ry, spec):
        self.raw(f"Ellipse {x:.1f},{y:.1f},{rx:.1f},{ry:.1f} | {spec}")

    def line(self, geom, spec):
        for ln in lines_of(geom):
            self.path(list(ln.coords), spec)

    def text(self):
        out, chunks = [], [self.items[i:i + PER_METER] for i in range(0, len(self.items), PER_METER)] or [[]]
        for n, chunk in enumerate(chunks, 1):
            name = self.name if len(chunks) == 1 else f"{self.name}{n:02d}"
            lines = [f"[{name}]", "Meter=Shape", "X=0", "Y=0"]
            if not chunk:
                lines.append("Shape=Rectangle 0,0,0,0 | Fill Color 0,0,0,0 | StrokeWidth 0")
            for k, (kind, d, spec, grad) in enumerate(chunk, 1):
                key = "Shape" if k == 1 else f"Shape{k}"
                if grad:
                    lines.append(f"G{k}={grad}")
                if kind == "path":
                    lines.append(f"P{k}={d}")
                    lines.append(f"{key}=Path P{k} | {spec}")
                else:
                    lines.append(f"{key}={spec}")
            lines.append("TransformationMatrix=#Scale#;0;0;#Scale#;0;0")
            if self.hidden:
                lines.append(f"Hidden={self.hidden}")
            lines.append("DynamicVariables=0")
            out.append("\n".join(lines) + "\n")
        return "\n".join(out) + "\n", len(chunks)

    def __len__(self):
        return len(self.items)


# ------------------------------------------------------------------ geometry of the structure
# (polygon, axis start, axis end) in reference px; the axis runs down the middle of each member
MEMBERS = {
    "pillar_l": (R.PILLAR_L, (293.5, 63), (478, 370)),
    "pillar_r": (R.PILLAR_R, (964, 63), (786, 372)),
    "beam_l": (R.BEAM_L, (487, 377), (0, 597)),
    "beam_r": (R.BEAM_R, (782, 380), (1260, 599)),
}
# per member: cross seams, vent grille span, LED positions (axis t, side offset as a fraction of half width)
PLAN = {
    "pillar_l": {"seams": (0.16, 0.6, 0.9), "vents": [(0.68, 0.8)], "leds": [(0.12, -0.45), (0.12, 0.45), (0.56, 0.5), (0.86, -0.4)]},
    "pillar_r": {"seams": (0.16, 0.6, 0.9), "vents": [(0.68, 0.8)], "leds": [(0.12, -0.45), (0.12, 0.45), (0.56, -0.5), (0.86, 0.4)]},
    "beam_l": {"seams": (0.3, 0.7), "vents": [(0.34, 0.46)], "leds": [(0.27, 0.0), (0.74, 0.3)], "hazard": (0.62, 0.68)},
    "beam_r": {"seams": (0.3, 0.7), "vents": [(0.34, 0.46)], "leds": [(0.27, 0.0), (0.74, -0.3)], "hazard": (0.62, 0.68)},
}
# lower dash areas beside the console (left side; the right is mirrored) and the rail direction there
DASH_L = [(505, 380), (535, 600), (392, 650), (300, 700), (140, 709), (0, 640), (0, 610), (250, 500)]
RIB_DIR = {"l": ((505, 395), (0, 625)), "r": ((755, 395), (1260, 625))}
LED_COLS = ["#ColorAccent#", "#ColorGood#", "#ColorWarn#", "#ColorAlert#", "#ColorAccent#"]


def busy_region():
    """every widget zone (canvas quads) plus a margin, and the strut lights - detail stays off these"""
    polys = [Polygon(z["quad"]) for z in R.ZONES]
    polys += [Point(x * R.SX, y * R.SY).buffer(70) for x, y in R.LIGHTS]
    return unary_union(polys).buffer(10)


def member_geom(key):
    pts, a, b = MEMBERS[key]
    poly = cpoly(pts)
    A, B = (a[0] * R.SX, a[1] * R.SY), (b[0] * R.SX, b[1] * R.SY)
    ax, ay = norm(B[0] - A[0], B[1] - A[1])
    return poly, A, B, (ax, ay), (-ay, ax)


def at(A, B, t):
    return (A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t)


def cross(poly, P, n, inset=4):
    """segment across the member through P along n, clipped inside the member"""
    ln = LineString([(P[0] - n[0] * 400, P[1] - n[1] * 400), (P[0] + n[0] * 400, P[1] + n[1] * 400)])
    seg = ln.intersection(poly.buffer(-inset))
    segs = lines_of(seg)
    if not segs:
        return None
    return min(segs, key=lambda s: s.distance(Point(P)))


def build_layers(hull, windows, scan_spacing=5):
    hull_c = shp_scale(hull, R.SX, R.SY, origin=(0, 0))
    win_c = shp_scale(windows, R.SX, R.SY, origin=(0, 0))
    screen = box(1, 1, CW - 1, CH - 1)
    busy = busy_region()
    free = hull_c.difference(busy)

    sheen = Layer("Sheen", hidden="#UseShipImage#")
    greeb = Layer("Greebles", hidden="#UseShipImage#")
    lights = Layer("Lights", hidden="#UseShipImage#")
    spill = Layer("Spill")
    glare = Layer("Glare")
    scan = Layer("Scan", hidden="(1-#ScanLines#)")

    # ---------------------------------------------------------------- struts and beams
    for key in MEMBERS:
        poly, A, B, ax, n = member_geom(key)
        plan = PLAN[key]
        width = poly.area / max(1.0, math.dist(A, B))
        # brushed sheen: a soft bright band down the middle, gradient across the member
        band = poly.intersection(LineString([A, B]).buffer(width * 0.22, cap_style=2)).difference(busy)
        ang = math.degrees(math.atan2(n[1], n[0]))
        for g in getattr(band, "geoms", [band]):
            if g.geom_type == "Polygon" and g.area > 60:
                sheen.path(list(g.exterior.coords)[:-1], "Fill LinearGradient G{k} | StrokeWidth 0", True,
                           f"{ang:.0f} | 200,225,245,0 ; 0.0 | 200,225,245,15 ; 0.5 | 200,225,245,0 ; 1.0")
        # specular edge highlight on both long sides
        for side in (-1, 1):
            edge = poly.difference(poly.buffer(-13)).intersection(
                LineString([A, B]).parallel_offset(width * 0.42, "left" if side < 0 else "right").buffer(width * 0.12, cap_style=2))
            edge = edge.difference(busy)
            gang = math.degrees(math.atan2(-n[1] * side, -n[0] * side))
            lit = 22 if side < 0 else 12
            for g in getattr(edge, "geoms", [edge]):
                if g.geom_type == "Polygon" and g.area > 40:
                    sheen.path(list(g.exterior.coords)[:-1], "Fill LinearGradient G{k} | StrokeWidth 0", True,
                               f"{gang:.0f} | 215,235,255,{lit} ; 0.0 | 215,235,255,0 ; 1.0")
        # panel inset: dark groove with a light lip
        for off, spec in ((-8, "Stroke Color 0,0,0,120 | StrokeWidth 1.8"), (-9.6, "Stroke Color 150,185,210,34 | StrokeWidth 1")):
            ring = poly.buffer(off, join_style=2).exterior
            greeb.line(ring.difference(busy).intersection(screen), "Fill Color 0,0,0,0 | " + spec)
        # cross seams with rivets at the ends
        for t in plan["seams"]:
            seg = cross(poly, at(A, B, t), n, inset=9)
            if seg is None or seg.intersects(busy):
                continue
            p0, p1 = seg.coords[0], seg.coords[-1]
            greeb.path([p0, p1], "Stroke Color 0,0,0,170 | StrokeWidth 2.2")
            greeb.path([(p0[0] + ax[0] * 2, p0[1] + ax[1] * 2), (p1[0] + ax[0] * 2, p1[1] + ax[1] * 2)],
                       "Stroke Color 140,175,200,48 | StrokeWidth 1")
        # rivets along the inset, skipping widget zones and lights
        ring = poly.buffer(-14, join_style=2).exterior
        step, d = 34.0, 10.0
        while d < ring.length:
            p = ring.interpolate(d)
            d += step
            if busy.contains(p) or not screen.contains(p):
                continue
            greeb.ellipse(p.x, p.y, 2.4, 2.4, "Fill Color 12,18,24,235 | Stroke Color 110,140,165,90 | StrokeWidth 0.8")
            greeb.ellipse(p.x - 0.7, p.y - 0.8, 1.0, 1.0, "Fill Color 200,225,240,120 | StrokeWidth 0")
        # vent grilles: a recessed plate with slots across the member
        for t0, t1 in plan["vents"]:
            c0, c1 = at(A, B, t0), at(A, B, t1)
            plate = poly.buffer(-16).intersection(LineString([c0, c1]).buffer(width * 0.3, cap_style=2))
            if plate.is_empty or plate.intersects(busy) or plate.geom_type != "Polygon":
                continue
            greeb.path(list(plate.exterior.coords)[:-1], "Fill Color 0,0,0,70 | Stroke Color 0,0,0,150 | StrokeWidth 1.4", True)
            greeb.line(plate.buffer(-1.6).exterior, "Fill Color 0,0,0,0 | Stroke Color 140,170,195,30 | StrokeWidth 1")
            nslots = max(4, int(math.dist(c0, c1) / 9))
            for i in range(nslots):
                P = at(c0, c1, (i + 0.5) / nslots)
                seg = cross(plate, P, n, inset=5)
                if seg is None:
                    continue
                p0, p1 = seg.coords[0], seg.coords[-1]
                greeb.path([p0, p1], "Stroke Color 0,0,0,220 | StrokeWidth 3.2 | StrokeStartCap Round | StrokeEndCap Round")
                greeb.path([(p0[0] + ax[0] * 2.2, p0[1] + ax[1] * 2.2), (p1[0] + ax[0] * 2.2, p1[1] + ax[1] * 2.2)],
                           "Stroke Color 130,165,190,40 | StrokeWidth 1")
        # hazard band: amber chevrons near the cockpit end of each beam
        if "hazard" in plan:
            t0, t1 = plan["hazard"]
            c0, c1 = at(A, B, t0), at(A, B, t1)
            strip = poly.buffer(-12).intersection(LineString([c0, c1]).buffer(width * 0.24, cap_style=2))
            if not strip.is_empty and not strip.intersects(busy) and strip.geom_type == "Polygon":
                greeb.path(list(strip.exterior.coords)[:-1], "Fill Color 10,10,8,150 | Stroke Color 0,0,0,160 | StrokeWidth 1.2", True)
                L = math.dist(c0, c1)
                for i in range(int(L / 11)):
                    P = at(c0, c1, (i + 0.5) / int(L / 11))
                    q = [(P[0] - n[0] * 40 - ax[0] * 4, P[1] - n[1] * 40 - ax[1] * 4), (P[0] - n[0] * 40 + ax[0] * 1, P[1] - n[1] * 40 + ax[1] * 1),
                         (P[0] + n[0] * 40 + ax[0] * 9, P[1] + n[1] * 40 + ax[1] * 9), (P[0] + n[0] * 40 + ax[0] * 4, P[1] + n[1] * 40 + ax[1] * 4)]
                    s = Polygon(q).intersection(strip.buffer(-1.5))
                    if s.geom_type == "Polygon" and s.area > 4:
                        greeb.path(list(s.exterior.coords)[:-1], "Fill Color #ColorWarn#,95 | StrokeWidth 0", True)
        # status LEDs with halos
        for i, (t, side) in enumerate(plan["leds"]):
            P = at(A, B, t)
            P = (P[0] + n[0] * side * width * 0.5, P[1] + n[1] * side * width * 0.5)
            if busy.contains(Point(P)) or not poly.buffer(-8).contains(Point(P)):
                continue
            col = LED_COLS[(i + len(key)) % len(LED_COLS)]
            for r, a in ((16, 10), (10, 22), (6, 50)):
                lights.ellipse(P[0], P[1], r, r, f"Fill Color {col},{a} | StrokeWidth 0")
            lights.ellipse(P[0], P[1], 3.0, 3.0, f"Fill Color {col},255 | Stroke Color 0,0,0,160 | StrokeWidth 1")
            lights.ellipse(P[0] - 0.6, P[1] - 0.6, 1.1, 1.1, "Fill Color 255,255,255,200 | StrokeWidth 0")

    # ---------------------------------------------------------------- dash ribs: long machined rails below the beams
    rng = random.Random(7)
    blocked = busy.union(unary_union([Polygon(C([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])) for x0, y0, x1, y1 in R.SCREENS]
                                      + [cpoly(t) for t in R.TILTED]).buffer(14))
    for side, dash in (("l", DASH_L), ("r", [(R.RW - x, y) for x, y in DASH_L])):
        region = cpoly(dash).intersection(hull_c).difference(blocked)
        (bx0, by0), (bx1, by1) = C([RIB_DIR[side][0], RIB_DIR[side][1]])
        dx, dy = norm(bx1 - bx0, by1 - by0)
        nx, ny = -dy, dx
        if ny < 0:
            nx, ny = -nx, -ny
        for i in range(-3, 24):
            off = i * 28 + rng.uniform(-5, 5)
            ox, oy = bx0 + nx * off, by0 + ny * off
            ln = LineString([(ox - dx * 2000, oy - dy * 2000), (ox + dx * 2000, oy + dy * 2000)]).intersection(region)
            for seg in lines_of(ln):
                if seg.length < 60:
                    continue
                # break long rails into machined sections
                L, d = seg.length, 0.0
                while d < L:
                    run = rng.uniform(160, 520)
                    piece = substring(seg, d, min(L, d + run))
                    d += run + rng.uniform(10, 60)
                    if piece.length < 40:
                        continue
                    pts = list(piece.coords)
                    hi = rng.choice((22, 34, 48, 70))
                    greeb.path(pts, "Stroke Color 0,0,0,150 | StrokeWidth 2.6")
                    greeb.path([(x + nx * 2.2, y + ny * 2.2) for x, y in pts], f"Stroke Color 150,190,215,{hi} | StrokeWidth 1.1")
                    if rng.random() < 0.3:
                        greeb.path([(x + nx * 7, y + ny * 7) for x, y in pts], f"Stroke Color 150,190,215,{hi // 2} | StrokeWidth 1")
                    if rng.random() < 0.18:
                        greeb.path([(x - nx * 1.6, y - ny * 1.6) for x, y in pts], "Stroke Color #ColorAccent#,26 | StrokeWidth 3")

    # ---------------------------------------------------------------- rim light where hull meets glass
    light_dir = norm(-0.35, -1.0)        # space light falls from above, slightly from the left
    for w in getattr(win_c, "geoms", [win_c]):
        ring = w.buffer(1.8, join_style=2).exterior
        pts = list(ring.coords)
        groups, cur, cur_b = [], [], None
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            ex, ey = norm(x1 - x0, y1 - y0)
            nx, ny = ey, -ex                  # outward from the window = into the hull
            lit = max(0.0, -(nx * light_dir[0] + ny * light_dir[1]))
            b = min(3, int(lit * 4))
            if b != cur_b and cur:
                groups.append((cur_b, cur))
                cur = [cur[-1]]
            cur_b = b
            if not cur:
                cur = [(x0, y0)]
            cur.append((x1, y1))
        if cur:
            groups.append((cur_b, cur))
        for b, gp in groups:
            seg = LineString(gp).intersection(screen).intersection(hull_c.buffer(3))
            I = 0.3 + 0.7 * b / 3
            sheen.line(seg, f"Stroke Color #ColorAccent#,{int(16 * I)} | StrokeWidth 7 | StrokeLineJoin Round")
            sheen.line(seg, f"Stroke Color 205,230,250,{int(35 + 120 * I)} | StrokeWidth {1.0 + 0.8 * I:.1f} | StrokeLineJoin Round")

    # ---------------------------------------------------------------- strut lights: spill, flare, glints
    for (x, y) in R.LIGHTS:
        X, Y = x * R.SX, y * R.SY
        for r, a in ((190, 4), (130, 7), (85, 12)):
            lights.ellipse(X, Y, r, r, f"Fill Color 50,135,255,{a} | StrokeWidth 0")
        for r, a in ((46, 20), (34, 34), (24, 60), (15, 110)):
            lights.ellipse(X, Y, r, r, f"Fill Color 40,130,255,{a} | StrokeWidth 0")
        lights.ellipse(X, Y, 230, 2.2, "Fill Color 120,190,255,30 | StrokeWidth 0")
        lights.ellipse(X, Y, 120, 3.5, "Fill Color 140,200,255,55 | StrokeWidth 0")
        lights.ellipse(X, Y, 2.0, 55, "Fill Color 140,200,255,30 | StrokeWidth 0")
        lights.path([(X - 26, Y - 26), (X + 26, Y + 26)], "Stroke Color 170,215,255,40 | StrokeWidth 1.2")
        lights.path([(X - 26, Y + 26), (X + 26, Y - 26)], "Stroke Color 170,215,255,40 | StrokeWidth 1.2")
        lights.ellipse(X, Y, 7, 7, "Fill Color 190,230,255,255 | StrokeWidth 0")
        lights.ellipse(X, Y, 3.2, 3.2, "Fill Color 255,255,255,255 | StrokeWidth 0")

    # ---------------------------------------------------------------- HUD light thrown onto the dash
    # many faint layers rather than a few strong ones, so the falloff has no visible rings
    for i in range(7):
        k = 1 - i / 7
        spill.ellipse(651 * R.SX, 592 * R.SY, 120 + 230 * k, 34 + 86 * k, "Fill Color #ColorAccent#,3 | StrokeWidth 0")
    for (x0, y0, x1, y1) in R.SCREENS:
        cx, cy = (x0 + x1) / 2 * R.SX, (y0 + y1) / 2 * R.SY
        hw, hh = (x1 - x0) / 2 * R.SX, (y1 - y0) / 2 * R.SY
        for i in range(5):
            k = 1.08 + 0.12 * i
            spill.ellipse(cx, cy, hw * k, hh * k, "Fill Color #ColorAccent#,3 | StrokeWidth 0")
    arch = [(x * R.SX, y * R.SY) for x, y in R.ARCH]
    spill.path(arch, "Stroke Color #ColorAccent#,10 | StrokeWidth 26 | StrokeLineJoin Round")
    spill.path([(x, y + 6) for x, y in arch], "Stroke Color #ColorAccent#,8 | StrokeWidth 40 | StrokeLineJoin Round")
    for l in R.CONSOLE_LINES:
        spill.path(C(l), "Stroke Color #ColorAccent#,9 | StrokeWidth 22 | StrokeLineJoin Round")

    # ---------------------------------------------------------------- reflections on the glass
    bands = [((-0.15, 0.0), (0.55, 1.0), 0.07, 1.0), ((0.25, 0.0), (0.95, 1.0), 0.035, 0.6), ((0.6, 0.0), (1.2, 0.9), 0.05, 0.8)]
    for w in getattr(win_c, "geoms", [win_c]):
        minx, miny, maxx, maxy = w.bounds
        W, H = maxx - minx, maxy - miny
        for (u0, v0), (u1, v1), half, k in bands:
            p0 = (minx + W * u0, miny + H * v0)
            p1 = (minx + W * u1, miny + H * v1)
            strip = LineString([p0, p1]).buffer(max(W, H) * half, cap_style=2).intersection(w.buffer(-2))
            dx, dy = norm(p1[0] - p0[0], p1[1] - p0[1])
            ang = math.degrees(math.atan2(dx, -dy))
            for g in getattr(strip, "geoms", [strip]):
                if g.geom_type == "Polygon" and g.area > 400:
                    glare.path(list(g.exterior.coords)[:-1], "Fill LinearGradient G{k} | StrokeWidth 0", True,
                               f"{ang:.0f} | 220,240,255,0 ; 0.0 | 220,240,255,(#GlassGlare#*{k}) ; 0.5 | 220,240,255,0 ; 1.0")

    # ---------------------------------------------------------------- scanlines over the windows
    y = scan_spacing / 2
    while y < CH:
        seg = LineString([(0, y), (CW, y)]).intersection(win_c.buffer(-1))
        scan.line(seg, "Stroke Color 0,0,0,#ScanAlpha# | StrokeWidth 1.6")
        y += scan_spacing

    # fill in per-shape gradient ids (G{k} must match the shape's index inside its own meter)
    for layer in (sheen, glare):
        fixed = []
        for idx, (kind, d, spec, grad) in enumerate(layer.items):
            k = idx % PER_METER + 1
            fixed.append((kind, d, spec.replace("G{k}", f"G{k}"), grad))
        layer.items = fixed
    return [sheen, greeb, lights, spill, glare, scan]
