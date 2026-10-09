#!/usr/bin/env python3
"""Generate layout/layout.json from coordinates traced off the reference image (1260 x 709).

Every zone, window and hull outline below is written in REFERENCE pixels, measured from zoomed,
gridded crops of the original cockpit image, and mapped onto the 2560 x 1600 canvas
(x * 2560/1260, y * 1600/709). Slanted panels are quads [TL, TR, BR, BL]; the build turns each quad
into a Rainmeter TransformationMatrix so text and graphics lean exactly like the reference.

Deviations from the reference are deliberate and listed in DEVIATIONS.
Run:  python tools/ref_layout.py && python tools/build.py && python tools/ship_frame.py
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RW, RH = 1260, 709
CW, CH = 2560, 1600
SX, SY = CW / RW, CH / RH

DEVIATIONS = [
    "Widgets stay above the Windows taskbar band (72 px); the bottom info strip sits 6 ref px higher.",
    "Left column slot 4 shares its block with the upkeep counters (the reference's small 3 / 4 counters).",
    "Right column gets a matching dev-status counter block left of ship 4.",
    "Right category page selector uses the reference's small triangle-and-number glyph.",
]


def P(x, y):
    return [round(x * SX, 2), round(y * SY, 2)]


def rect(x0, y0, x1, y1):
    return [P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)]


def quad(*pts):
    return [P(x, y) for x, y in pts]


def zone(zid, group, q, content):
    tl, tr, br, bl = q
    w = math.hypot(tr[0] - tl[0], tr[1] - tl[1])
    h = math.hypot(bl[0] - tl[0], bl[1] - tl[1])
    return {"id": zid, "group": group, "x": tl[0], "y": tl[1], "w": round(w, 2), "h": round(h, 2), "quad": q,
            "content": content}


ZONES = [
    # ---------------------------------------------------------------- top console
    zone("T_power", "top", quad((335, 24), (432, 32), (432, 44), (335, 36)), "H ---- C bar -> power draw"),
    zone("T_battery", "top", quad((826, 33), (956, 21), (956, 33), (826, 45)), "PWR ---- bar -> battery"),
    zone("T_settings", "top", rect(470, 10, 805, 57), "COMBAT STARMAP... tabs -> GPU modes; RADR/IFCS + MISL..GFRC -> quick settings"),
    zone("T_alert", "top", rect(289, 53, 318, 72), "warning triangle + count"),
    zone("G1_cpu", "top", rect(333, 62, 447, 95), "OXYGEN LEVEL plate -> CPU (fixed)"),
    zone("G2_select", "top", rect(493, 62, 607, 95), "INTERNAL PRESSURE plate -> selectable"),
    zone("G3_select", "top", rect(663, 62, 787, 95), "HULL INTEGRITY plate -> selectable"),
    zone("G4_ram", "top", rect(828, 62, 940, 95), "FUEL LEVEL plate -> RAM (fixed)"),
    # ---------------------------------------------------------------- left column
    zone("L_tabs", "left", quad((74, 39), (256, 70), (256, 91), (74, 60)), "OVR WEAP AVI... -> category app tabs"),
    zone("L_category", "left", rect(62, 95, 232, 218), "ship schematic -> app wireframe"),
    zone("L_location", "left", quad((34, 222), (230, 232), (230, 306), (34, 296)), "LAT / LON / VRT block"),
    zone("L_dots", "left", rect(92, 307, 164, 321), "page dots -> category pages"),
    zone("L_app1", "left", rect(34, 325, 230, 387), "weapon 1 -> slot 1"),
    zone("L_app2", "left", rect(40, 390, 230, 450), "weapon 2 -> slot 2"),
    zone("L_app3", "left", rect(52, 455, 158, 510), "weapon 3 -> slot 3"),
    zone("L_app4", "left", rect(68, 516, 136, 574), "ship 4 -> slot 4"),
    zone("L_upkeep", "left", rect(140, 518, 180, 552), "3 / 4 counters -> updates / upgrades"),
    # ---------------------------------------------------------------- right column
    zone("R_tabs", "right", quad((1004, 72), (1182, 42), (1182, 63), (1004, 93)), "SUBSYS CARGO MAIL -> category app tabs"),
    zone("R_category", "right", rect(1030, 98, 1202, 212), "ship -> app wireframe"),
    zone("R_dots", "right", rect(1210, 186, 1240, 216), "triangle + 4 glyph -> category page"),
    zone("R_sysinfo", "right", rect(1028, 226, 1228, 302), "VANDUUL SCYTHE card -> BLACK-CLOVER"),
    zone("R_app1", "right", rect(1028, 324, 1228, 388), "card 1 -> slot 5"),
    zone("R_app2", "right", rect(1124, 394, 1226, 452), "card 2 -> slot 6"),
    zone("R_app3", "right", rect(1124, 456, 1226, 512), "card 3 -> slot 7"),
    zone("R_app4", "right", rect(1128, 516, 1200, 574), "ship 4 -> slot 8"),
    zone("R_dev", "right", rect(1084, 518, 1124, 552), "dev counters"),
    # ---------------------------------------------------------------- centre
    zone("C_target", "center", rect(583, 155, 709, 251), "orange target lock"),
    zone("C_hud", "center", rect(486, 256, 778, 401), "speed ladders, pipper, M/S THR"),
    zone("C_sphere", "center", rect(535, 407, 768, 582), "holographic sphere + DSP RNGE label"),
    # ---------------------------------------------------------------- dash
    zone("B_storage", "bottom", rect(395, 565, 488, 638), "ENG / ATMOS / DMG screen -> storage"),
    zone("B_audio", "bottom", rect(778, 568, 872, 638), "TARGET SNR screen -> audio"),
    zone("B_stripL", "bottom", rect(425, 650, 604, 676), "1500 / 7 / 0% / 443 boxed cells"),
    zone("B_stripR", "bottom", rect(742, 654, 822, 676), "20 / 20 open cells"),
]

# ---------------------------------------------------------------- the ship (reference pixels)
# Windows from the owner's line drawing (art/window-lines-right.png: the right half, mirrored for the left).
# Drawing px -> reference px: x = 630 + gx * 630/597.7, y = (gy - 2.6) * 709/674.9
WIN_CENTER = [(333.9, 90.2), (926.1, 90.2), (759.2, 365.5), (500.8, 365.5)]
WIN_RIGHT = [(1043.1, 89.9), (1260, 303.4), (1260, 554.7), (819.4, 420.2), (782.8, 377.4)]
WIN_TOP_R = [(1116.5, 36.7), (1197.2, 0), (1260, 104.2), (1260, 181.5)]


def mirror(pts):
    return [(RW - x, y) for x, y in pts][::-1]


WIN_LEFT = mirror(WIN_RIGHT)
WIN_TOP_L = mirror(WIN_TOP_R)
WINDOWS = [WIN_CENTER, WIN_LEFT, WIN_RIGHT, WIN_TOP_L, WIN_TOP_R]


def _arc(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


# structure between the windows (left side; the right side is mirrored)
PILLAR_L = [(216.9, 89.9), (333.9, 90.2), (500.8, 365.5), (477.2, 377.4)]       # A-pillar: windscreen | side window
STRUT_L = [(143.5, 36.7), (216.9, 89.9), (0, 303.4), (0, 181.5)]                # roof strut: side window | top window
SILL_EDGE_L = [(0, 554.7), (440.6, 420.2), (477.2, 377.4)]                      # side-window sill
PILLAR_R, STRUT_R = mirror(PILLAR_L), mirror(STRUT_L)
LIGHTS = [(358, 200), (902, 200), (232, 498), (1028, 498)]
PLATES = [(330, 52, 450, 93), (490, 52, 610, 93), (660, 52, 790, 93), (825, 52, 943, 93)]
SCREENS = [(392, 562, 491, 641), (775, 565, 875, 641)]
TILTED = [[(305, 648), (348, 632), (360, 694), (318, 709)], [(955, 648), (912, 632), (900, 694), (942, 709)]]
ARCH = [(382, 706), (420, 668), (520, 650), (640, 645), (760, 650), (838, 668), (876, 706)]

# HUD lines that are part of the cockpit glass (decor layer, tinted with the theme colour)
CONSOLE_LINES = [
    [(482, 0), (510, 29), (750, 29), (778, 0)],
    [(280, 30), (445, 50), (462, 37), (602, 42), (620, 59)],
    [(642, 59), (660, 44), (800, 37), (817, 50), (980, 30)],
]
GLYPHS = [(118, 598), (148, 655), (1142, 598), (1112, 655)]
CIRCLE_GLYPH = (315, 372)
COWL_DOTS = (635, 700, 372)


def scale(pts):
    return [P(x, y) for x, y in pts]


def main():
    layout = {
        "_comment": "GENERATED by tools/ref_layout.py from the reference image (1260x709) - edit that file, not this one.",
        "deviations": DEVIATIONS,
        "reference": {"w": RW, "h": RH, "sx": SX, "sy": SY},
        "canvas": {"w": CW, "h": CH},
        "safe_area": {"inset": 10, "corner_radius": 110},
        "taskbar": {"height": 72},
        "min_gap": 6,
        "decor_gap": 1,
        "curves": {g: {"type": "flat"} for g in ("top", "left", "right", "center", "bottom")},
        "keepouts": [],
        "zones": ZONES,
        "decor": [
            {"id": f"D_glyph{i + 1}", "group": "center", "x": P(x - 7, y - 7)[0], "y": P(x - 7, y - 7)[1],
             "w": round(14 * SX, 2), "h": round(14 * SY, 2)} for i, (x, y) in enumerate(GLYPHS)
        ] + [
            {"id": "D_circle", "group": "center", "x": P(CIRCLE_GLYPH[0] - 9, 0)[0], "y": P(0, CIRCLE_GLYPH[1] - 9)[1],
             "w": round(18 * SX, 2), "h": round(18 * SY, 2)},
            {"id": "D_tiltL", "poly": scale(TILTED[0])},
            {"id": "D_tiltR", "poly": scale(TILTED[1])},
        ],
        "overlays": [
            {"id": "O_drawer", "x": 1000, "y": 240, "w": 560, "h": 560, "content": "CARGO drawer (transient)"},
            {"id": "O_control", "x": 760, "y": 300, "w": 1040, "h": 900, "content": "Control Center (transient)"},
        ],
        "frame": {
            "windows": [scale(w) for w in WINDOWS],
            "pillars": [scale(PILLAR_L), scale(PILLAR_R)],
            "struts": [scale(STRUT_L), scale(STRUT_R)],
            "lights": scale(LIGHTS),
            "screens": [P(a, b) + P(c, d) for a, b, c, d in SCREENS],
            "tilted": [scale(t) for t in TILTED],
            "arch": scale(ARCH),
            "console_lines": [scale(l) for l in CONSOLE_LINES],
            "glyphs": scale(GLYPHS),
            "circle_glyph": P(*CIRCLE_GLYPH),
            "cowl_dots": [P(COWL_DOTS[0], COWL_DOTS[2]), P(COWL_DOTS[1], COWL_DOTS[2])],
        },
    }
    # keep the module list from the existing layout, updated for the new zones
    old = json.loads((ROOT / "layout" / "layout.json").read_text())
    skins = old["skins"]
    skins["Left\\Category"] = {"zones": ["L_tabs", "L_category", "L_dots"]}
    skins["Right\\Category"] = {"zones": ["R_tabs", "R_category", "R_dots"]}
    skins["Bottom\\Strip"] = {"zones": ["B_stripL", "B_stripR"]}
    layout["skins"] = skins
    (ROOT / "layout" / "layout.json").write_text(json.dumps(layout, indent=1))
    print(f"wrote layout.json: {len(ZONES)} zones")


if __name__ == "__main__":
    main()
