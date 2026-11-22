# review-2026-11-05: scripts and raw output

Everything here is read-only with respect to the repo. All scripts run inside a **scratch mirror** with `TZ=ABC+12`, a temp `RES` (so the real `Data\jarvis.log` is never written),
tripwires on every destructive call, and no model unless a script says so. Read `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` first.

| File | What | How it was run (from a mirror of the repo depth, venv python) |
|---|---|---|
| `gate.sh` | baseline gate: `test_jarvis` x2 through `tests/guarded_run.py`, `test_host_pipe`, `tests/run_all.py`, both goldens. Builds the mirror itself. **Edit the `G=` (output folder) and `L=` (repo) lines first**: they point at this session's scratch folder. | `bash gate.sh baseline` |
| `probe_routes.py` | 245 phrases through `understand()`; prints misses, false positives, and which ones would ask the model | `TZ=ABC+12 python -B probe_routes.py <mirror Jarvis dir>` |
| `probe_misc.py` | `crisis`, `directed`, `is_yes`, `level_fix`, `takes`, `mode_after`, `strip_name` | same |
| `probe3.py` | 41 phrases (negations, ranges, power words, compounds) through `understand()` | same |
| `probe4.py` | `ask_ai` on negations; crisis typed with Ollama down / model missing | same |
| `probe5.py` | watchdog, busy lock, second turn while busy | same |
| `probe6.py` | numeric settings with odd values; invalid UTF-8 in the facts file | same |
| `rv_cases.jsonl` | 35 typed multi-turn cases (`ear` / `ear_mode` for follow-ups) | `python -B tools/semi_live.py --model llama3.1:8b --cases rv_cases.jsonl --seed 7 --out out.jsonl` then `curl -s localhost:11434/api/generate -d "{\"model\":\"llama3.1:8b\",\"keep_alive\":0}"` |
| `mutate.py` | 38 one-line mutants of the decision code; each runs `test_jarvis.py` through the tripwire runner in the scratch mirror (restores the file from the repo every time) | `python -B mutate.py <mirror Jarvis dir> <repo Jarvis dir> [M07 M27 ...]` |
| `out_*.txt`, `out_semi_live_*.jsonl` | raw output of the above | |

The semi-live harness uses a made-up profile and vault, never your real ones; results contain no personal data.
Note: the repo files use CRLF line endings; multi-line mutant snippets need `\r\n`.
