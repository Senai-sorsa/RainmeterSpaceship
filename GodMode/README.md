# GodMode (standalone, not wired into CSpace or JARVIS yet)

The plan is in `GOD-MODE-plan.md`. Python 3.12, standard library only. Run everything from this folder.

| Command | What it does |
|---|---|
| `py -3 -B -m unittest discover -s tests -t .` | unit tests (fakes only) |
| `py -3 -I spikes/<name>.py` | on-machine proofs: lowil, memcap, label, appcontainer, private_ollama, freeze, wiring, chat_smoke (see HANDOFF.md §2) |
| `py -3 -B -m godmode doctor` | read-only check: RAM/VRAM budgets, placements, Ollama, folders, audit |
| `py -3 -B -m godmode plan [slot]` | comfortable-RAM placement for a model slot |
| `py -3 -B -m godmode gguf --ollama gpt-oss:120b` | real sizes/layers from an installed model (after G0 download) |
| `py -3 -B -m godmode tweak-check patch.json` | static gate only |
| `py -3 -B -m godmode tweak-run patch.json` | full gate: copy, sandboxed tests before/after, proposal bundle |
| `py -3 -B -m godmode proposal-show <id>` | diff + the git commands to apply it by hand (from the repo root) |
| `py -3 -B -m godmode chat --slot advanced --mode read` | console session (needs the model installed) |
| `py -3 -B -m godmode audit-verify` / `incident-ack` | audit chain check / unlock after an incident |
| `py -3 -B -m godmode sandbox-setup [--venv] [--undo]` | AppContainer for tweak tests (`--venv` needs the user's OK) |
| `py -3 -B -m godmode protect-secrets [--apply\|--undo]` | dry run by default; label secret folders so sandboxed processes can't read them |

| Module | Role |
|---|---|
| `godmode/memory.py` | measure RAM/VRAM, comfortable budget, placement (gpu/split/stream/refuse), watchdog |
| `godmode/sandbox_win.py` | low-IL token + Job Object + working-set cap + low memory priority |
| `godmode/tweak.py`, `surfaces.json` | what may be edited, structure lock, banned content |
| `godmode/testgate.py`, `testgate.json` | disposable copy, forced tests, protected-file hashes |
| `godmode/gate.py`, `paths.py`, `tools.py` | modes, path policy, read tools + apply_patch |
| `godmode/agent.py`, `runtime.py`, `incident.py` | agent loop, Ollama/llama-server clients, incident explainer |
| `godmode/gguf.py` | GGUF header reader + chat-template red-flag scan |
| `godmode/servers.py`, `guard.py` | private capped Ollama; freeze/thaw memory guard during generation |
| `godmode/reader.py` | low-IL reader process for file tools (broker keeps gate/audit/apply_patch) |
| `godmode/hardening.py`, `pyruntime.py` | opt-in permission steps (AppContainer grants, secret labels); private runtime |
| `godmode/audit.py` | hash-chained audit log |

Data: `%LOCALAPPDATA%\CSpace\GodMode\` (audit, work copies, proposals) and `%USERPROFILE%\AppData\LocalLow\CSpace\GodMode\` (sandbox-writable: jobs, tmp).
Rollback: see `HANDOFF.md` §9. Status, measurements and next steps: `HANDOFF.md`.
