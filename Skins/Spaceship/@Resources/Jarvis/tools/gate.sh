#!/bin/bash
# The JARVIS gate, in the repo (it used to live in %TEMP%). HEAVY: about 10 minutes of one CPU core, no GPU, no model.
# Do not run it while the machine is busy. Everything happens on a scratch COPY (never the live folder), with TZ=ABC+12.
#   bash tools/gate.sh [label]            env: GATE_OUT=<scratch folder>   PY=<venv python>
# Prints one line per stage and "GATE <label> rc=0" when all of them pass:
#   test_jarvis (venv python and py -3, through the tripwire runner), test_host_pipe, tests/run_all.py, golden routes, golden replies.
HERE="$(cd "$(dirname "$0")/.." && pwd)"            # .../@Resources/Jarvis
L="$(cd "$HERE/../../../.." && pwd)"                # repo root
G="${GATE_OUT:-${TMPDIR:-${TEMP:-/tmp}}/jarvis-gate}"
JD="Skins/Spaceship/@Resources/Jarvis"; R="$L/Skins/Spaceship/@Resources"
PY="${PY:-$LOCALAPPDATA/SpaceshipHUD/venv/Scripts/python.exe}"; export TZ=ABC+12
S="$G/mirror"; mkdir -p "$G"
rm -rf "$S"; mkdir -p "$S/$JD"; cp -r "$L/contract" "$S/" 2>/dev/null
mkdir -p "$S/Skins/Spaceship/@Resources"
cp -r "$R/Settings.inc" "$R/Data" "$R/Sounds" "$R/Scripts" "$R/Bin" "$S/Skins/Spaceship/@Resources/" 2>/dev/null
cp -r "$HERE/Data" "$S/$JD/" 2>/dev/null
for f in "$HERE/"*; do case "$(basename "$f")" in kokoro|voices|vosk|__pycache__) ;; tools) mkdir -p "$S/$JD/tools"; cp "$f"/*.py "$f"/*.jsonl "$f"/*.txt "$S/$JD/tools/" 2>/dev/null;; *) cp -r "$f" "$S/$JD/";; esac; done
cd "$S/$JD" || exit 9; rc=0
"$PY" -B tests/guarded_run.py test_jarvis.py > "$G/h_venv.txt" 2>&1; echo "venv test_jarvis exit $?: $(tail -1 "$G/h_venv.txt" | cut -c1-200)"
grep -q "^test_jarvis: OK" "$G/h_venv.txt" && grep -q "tripwires hit: 0" "$G/h_venv.txt" || rc=1
py -3 -B tests/guarded_run.py test_jarvis.py > "$G/h_py3.txt" 2>&1; echo "py3 test_jarvis exit $?: $(tail -1 "$G/h_py3.txt" | cut -c1-200)"
grep -q "^test_jarvis: OK" "$G/h_py3.txt" && grep -q "tripwires hit: 0" "$G/h_py3.txt" || rc=1
"$PY" -B test_host_pipe.py > "$G/h_pipe.txt" 2>&1; echo "host_pipe: $(grep failed: "$G/h_pipe.txt")"; grep -q "failed: 0" "$G/h_pipe.txt" || rc=1
"$PY" -B tests/run_all.py > "$G/h_new.txt" 2>&1 || rc=1; tail -3 "$G/h_new.txt"
"$PY" -B tools/golden_routes.py --check > "$G/h_routes.txt" 2>&1 || rc=1; tail -2 "$G/h_routes.txt"
"$PY" -B tools/golden_replies.py --check > "$G/h_replies.txt" 2>&1 || rc=1; tail -2 "$G/h_replies.txt"
echo "GATE ${1:-} rc=$rc"; exit $rc
