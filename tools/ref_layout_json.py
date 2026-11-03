"""Write tools/frame_src/layout_polys.json for the Blender scene (canvas units, y down).
Run: py -3 -I tools/ref_layout_json.py"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import ref_layout as R  # noqa: E402


def trim_paths():
    """Unique Decor core paths (the P<n>= lines), as point lists."""
    seen, out = set(), []
    for m in re.finditer(r"^P\d+=(.+)$", (ROOT / "Skins/Spaceship/Frame/Parts/Decor.inc").read_text(), re.M):
        pts = [tuple(float(v) for v in s.replace("LineTo", "").split(",")) for s in m.group(1).split("|") if "ClosePath" not in s]
        if tuple(pts) not in seen:
            seen.add(tuple(pts))
            out.append([list(p) for p in pts])
    return out


def spill():
    t = (ROOT / "SpaceshipApp/SpaceshipUI/src/ui/spill.ts").read_text()
    body = re.search(r"SPILL[^{]*\{(.*?)\};", t, re.S).group(1)
    return {k: int(v) for k, v in re.findall(r"(\w+):\s*(\d+)", body)}


def main():
    zones = json.loads((ROOT / "layout/layout.json").read_text())["zones"]
    data = {
        "canvas": {"w": R.CW, "h": R.CH},
        "windows": [R.scale(w) for w in R.WINDOWS],
        "bezels": [R.scale(b) for b in R.BEZELS],
        "struts": [R.scale(p) for p in (R.PILLAR_L, R.PILLAR_R, R.STRUT_L, R.STRUT_R)],
        "zones": {z["id"]: [z["x"], z["y"], z["w"], z["h"]] for z in zones},
        "spill": spill(),
        "trim": trim_paths(),
    }
    out = ROOT / "tools/frame_src/layout_polys.json"
    out.write_text(json.dumps(data, indent=1))
    print("wrote", out.name, len(data["zones"]), "zones", len(data["trim"]), "trim paths")


if __name__ == "__main__":
    main()
