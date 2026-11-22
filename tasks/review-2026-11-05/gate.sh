#!/bin/bash
# gate for the finish worktree: scratch mirror of $W + live Settings/Data copies; tests x2, host_pipe, run_all, goldens
G=/c/Users/Senai/AppData/Local/Temp/claude/360eef7110f46b5a/847a2b1f-3a44-4fb4-b241-883d505d5d6e/scratchpad; L=/c/Users/Senai/RainmeterSpaceship; W=$L
S=$G/mirror; JD="Skins/Spaceship/@Resources/Jarvis"; PY="$LOCALAPPDATA/SpaceshipHUD/venv/Scripts/python.exe"; export TZ=ABC+12
rm -rf "$S"; mkdir -p "$S/$JD"; cp -r "$W/contract" "$S/"
R="$L/Skins/Spaceship/@Resources"
cp -r "$R/Settings.inc" "$R/Data" "$R/Sounds" "$R/Scripts" "$R/Bin" "$S/Skins/Spaceship/@Resources/" 2>/dev/null
cp -r "$R/Jarvis/Data" "$S/$JD/" 2>/dev/null
for f in "$W/$JD/"*; do case "$(basename "$f")" in kokoro|voices|vosk) ;; tools) mkdir -p "$S/$JD/tools"; cp "$f"/*.py "$f"/*.jsonl "$f"/*.txt "$S/$JD/tools/" 2>/dev/null;; *) cp -r "$f" "$S/$JD/";; esac; done
cd "$S/$JD" || exit 9; rc=0
"$PY" -B tests/guarded_run.py test_jarvis.py > "$G/h_venv.txt" 2>&1; echo "venv test_jarvis exit $?: $(tail -1 "$G/h_venv.txt" | cut -c1-200)"; grep -q "^test_jarvis: OK" "$G/h_venv.txt" && grep -q "tripwires hit: 0" "$G/h_venv.txt" || rc=1
py -3 -B tests/guarded_run.py test_jarvis.py > "$G/h_py3.txt" 2>&1; echo "py3 test_jarvis exit $?: $(tail -1 "$G/h_py3.txt" | cut -c1-200)"; grep -q "^test_jarvis: OK" "$G/h_py3.txt" && grep -q "tripwires hit: 0" "$G/h_py3.txt" || rc=1
"$PY" -B test_host_pipe.py > "$G/h_pipe.txt" 2>&1; echo "host_pipe: $(grep failed: "$G/h_pipe.txt")"; grep -q "failed: 0" "$G/h_pipe.txt" || rc=1
"$PY" -B tests/run_all.py > "$G/h_new.txt" 2>&1 || rc=1; tail -3 "$G/h_new.txt"
"$PY" -B tools/golden_routes.py --check > "$G/h_routes.txt" 2>&1 || rc=1; tail -2 "$G/h_routes.txt"
"$PY" -B tools/golden_replies.py --check > "$G/h_replies.txt" 2>&1 || rc=1; tail -2 "$G/h_replies.txt"
echo "GATE ${1:-} rc=$rc"; exit $rc
