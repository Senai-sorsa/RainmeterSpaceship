#!/usr/bin/env python3
"""Step animated modules frame by frame and audit every Nth frame: every shape and text must stay inside its
zone (the zones themselves are checked against the windows / each other by check_layout.py).

    python tools/anim_audit.py                      # Target, HUD, Sphere, Category panels, 40 s each
    python tools/anim_audit.py --only Target --seconds 60 --every 5
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import rmsim  # noqa: E402
from layoutlib import load, shape  # noqa: E402

ANIMATED = ["Center\\Target", "Center\\HUD", "Center\\Sphere", "Left\\Category", "Right\\Category"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--seconds", type=float, default=40)
    ap.add_argument("--every", type=int, default=5, help="audit every Nth frame (frames are 50 ms)")
    args = ap.parse_args()
    layout = load()
    zones = {z["id"]: shape(z, layout["curves"]) for z in layout["zones"]}
    start_file = rmsim.RES / "Data" / "StartApps.txt"
    mock = not start_file.exists()
    if mock:
        start_file.write_text(rmsim.MOCK_START)
    total, bad = 0, 0
    try:
        for config, ini in rmsim.discover():
            short = config.split("Spaceship\\", 1)[-1]
            if short not in ANIMATED or (args.only and args.only.lower() not in short.lower()):
                continue
            probs = rmsim.Problems()
            sk = rmsim.Skin(ini, config, "full", probs, {})
            sk.measure_values()
            sk.run_lua(1)
            frames = int(args.seconds * 20)
            seen = 0
            for f in range(frames):
                sk.call("Update()")
                if f % args.every == 0:
                    rmsim.render_skin(sk, Image.new("RGBA", (2560, 1600)), zones, probs)
                    seen += 1
            issues = [p for p in probs.items if p[1] in ("align", "lua", "shape")]
            total += seen
            bad += len(issues)
            print(f"{short:18s} {frames} frames, {seen} audited: {len(issues)} problems")
            for p in issues[:8]:
                print("   ", p[2])
    finally:
        if mock:
            start_file.unlink()
    print(f"audited {total} frames, {bad} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
