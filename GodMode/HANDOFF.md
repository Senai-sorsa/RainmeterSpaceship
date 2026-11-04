# GOD mode handoff (updated 2026-11-03, after the gap fixes)

Read with `GOD-MODE-plan.md` (design + sources) and `README.md` (commands). Labels: **[M]** measured here, **[E]** estimate, **[?]** not tested yet.

## 1. State in one paragraph
GOD mode is a standalone Python 3.12 package (standard library only) in `GodMode/`. **Nothing is wired into CSpace, JARVIS or the UI, no GOD models are downloaded, nothing is committed.** The full chat stack works end to end on this laptop with a stand-in model:
- GOD mode's **own private Ollama** runs at low integrity in our Job Object, with every process RAM-capped.
- A **memory guard** freezes the model mid-answer when RAM gets tight and resumes it without losing work.
- File reads run in a **separate low-integrity reader process**; the gate, audit and tweak proposals stay in the broker.
- **Self-tweaks** are gated and tested on a throwaway copy. The tests can run in an **AppContainer** (no network at all, no user files).
- Secret folders can be **OS-blocked** from every sandboxed process (opt-in).

## 2. Verified [M] (all run on this laptop, 2026-11-03)
| Check | Command (from the repo root) | Result |
|---|---|---|
| Unit tests (fakes only) | `py -3 -B -m unittest discover -s GodMode/tests -t GodMode` | **111 OK** |
| Low-IL sandbox | `py -3 -I GodMode/spikes/lowil_spike.py` | 4/4: can't write user folders, can write LocalLow, timeout kill, commit cap |
| Memory caps | `py -3 -I GodMode/spikes/memcap_spike.py` | 4/4: the hard working-set cap holds private memory **and memory-mapped model pages** (200 MB vs 600 MB uncapped); grandchildren are capped the instant they start (job events) |
| Secret labels | `py -3 -I GodMode/spikes/label_spike.py` | 5/5: NO_READ_UP (no admin) blocks low-IL reads; normal apps unaffected; undo works |
| AppContainer | `py -3 -I GodMode/spikes/appcontainer_spike.py` | 7/7: no localhost, no internet, no user files; private 29 MB Python runtime |
| Private Ollama | `py -3 -I GodMode/spikes/private_ollama_spike.py` | 6/6: low IL, **CUDA works** (29/29 layers on the RTX 5070), runner ≤ cap, model store unchanged, JARVIS Ollama unaffected |
| **Pause without losing work** | `py -3 -I GodMode/spikes/freeze_spike.py` | **6/6**: froze mid-generation, server RAM **924 MB → 0 MB** while frozen, the request waited, then the **same answer completed 8 s after thaw**; RunGuard drove pause/resume on the real server |
| **Wiring** | `py -3 -I GodMode/spikes/wiring_spike.py` | **7/7**: the real low-IL reader reads/lists; the **OS** refused it a labelled folder; a tricky path trips in the broker; **GOD mode's 111 unit tests pass inside the AppContainer** through `testgate.run_suite` |
| **Full chat stack** | `py -3 -I GodMode/spikes/chat_smoke.py` | **4/4** with llama3.2:3b: private Ollama + guard + reader + gate + audit; the model called `fs_read` through the reader and answered correctly; audit chain OK |
| Tweak pipeline | `godmode tweak-run` (1-line `quiet.py` edit, earlier today) | passed; real `test_jarvis.py` ran at low IL on the copy (62.7 s / 74.5 s); real repo untouched (proposal deleted in cleanup) |
| Secrets dry run | `godmode protect-secrets` | would label `C:\Users\Senai\.ssh` (nothing changed) |

Findings that changed the design [M]:
- The job-wide working-set limit needs an admin privilege (error 1314), so caps are applied per process on job "new process" events.
- Inside an AppContainer, Windows forces TEMP to the container's `AC\Temp`, and Python 3.12's `mkdtemp()` creates owner-only folders the container can't write. The AppContainer test boot fixes this inside the sandboxed process only (`testgate.AC_BOOT`).
- Low-IL console children get a console host (conhost) in their job, so the reader's job allows 2 processes.
- Real KV costs (from the HF configs): Qwen3.6 is 20,480 B/token; gpt-oss-120b is 36,864 B/token.
- The GPU has 12 GB of VRAM.

## 3. Gaps: status
| Gap | Status |
|---|---|
| Ollama shared with JARVIS, can't be capped | **Fixed.** `servers.PrivateOllama`; `godmode chat` uses it (cap = comfortable RAM budget, min 2 GiB). |
| Watchdog only between model calls | **Fixed.** `guard.RunGuard`: every 2 s; pause = `Proc.freeze()` (suspend + hand RAM back), resume = `thaw()`, stop = `kill()`. Wired into `godmode chat`. Note: after a thaw the server pulls its pages back, so under real pressure it may pause again; the hysteresis (3 low / 5 high samples) keeps it from flapping fast. |
| Worker and broker in one process | **Fixed for reads.** `reader.RemoteTools`: fs_list/stat/read/grep run in a low-IL child (JSON lines over pipes); sys_memory and apply_patch stay in the broker; the broker re-checks paths and trips early. The agent loop itself still runs in the broker (it is our own code, not untrusted input). |
| Tests can reach the network / user files | **Fixed, opt-in.** `godmode sandbox-setup` (done; GOD mode folders only). JARVIS tests switch to the AppContainer only after `godmode sandbox-setup --venv`, which **needs your OK** (adds read access for the container on `%LOCALAPPDATA%\SpaceshipHUD\venv\Lib\site-packages`; `--undo` removes it). Until then tweak tests run at low IL (proven). |
| Low-IL processes can read secrets | **Fixed, opt-in.** `godmode protect-secrets --apply` labels `.ssh` (+ `.gnupg`, `.aws`, `.azure`, `.kube`, `.docker`, password managers if present). **Needs your OK.** `--undo` reverses it. Browser profiles stay code-blocked only (labelling them might break a browser). |
| Network for the low-IL reader / model servers | Accepted residual: servers bind 127.0.0.1 + key; the reader has no network code. A full block needs the admin firewall step (D5). |
| Model sizes are estimates | Open until G0 (downloads). `gguf.summarize` still computes KV for every layer; correct it for hybrid/sliding layers then. |
| Ascendent (llama-server split) | Not started: binary not downloaded (G0). `runtime.llama_server_argv` and the placement planner are ready; start it through `sandbox_win.spawn` + `watch_new_processes` + RunGuard exactly like PrivateOllama. |

## 4. Files
- `godmode/memory.py`: comfortable-RAM rule (budget, placement gpu/split/stream/refuse, Ollama check, watchdog).
- `godmode/sandbox_win.py`: `spawn()`/`run()`; sandbox = `lowil` | `appcontainer` | `none`; Job Object; inherited-handle allowlist; `enforce_caps`, `watch_new_processes`, `working_sets`, `freeze`/`thaw`; `set_label`; `grant_appcontainer`/`revoke_appcontainer`.
- `godmode/servers.py`: PrivateOllama. · `godmode/guard.py`: RunGuard. · `godmode/reader.py`: reader child + RemoteTools.
- `godmode/hardening.py`: `sandbox-setup` / `protect-secrets` state, in `%LOCALAPPDATA%\CSpace\GodMode\hardening.json`.
- `godmode/pyruntime.py`: private stdlib-only Python for the AppContainer.
- `godmode/tweak.py` + `surfaces.json`, `godmode/testgate.py` + `testgate.json` (AppContainer boot: `AC_BOOT`, `ac_argv`).
- `godmode/agent.py`, `tools.py`, `gate.py`, `paths.py`, `runtime.py`, `incident.py`, `audit.py`, `gguf.py`, `profiles.py` + `models.json`, `cli.py`.
- `spikes/`: the 9 on-machine proofs above (each touches only its own scratch folders and kills only its own job).

## 5. What exists on disk outside the repo (after cleanup, 2026-11-03)
- `%LOCALAPPDATA%\CSpace\GodMode\`: `audit.jsonl` (hash chain; it still records the deleted smoke-test proposal), `hardening.json`, `runtime\python` (29 MB private runtime), empty `work\` and `ac-tmp\`.
- `%USERPROFILE%\AppData\LocalLow\CSpace\GodMode\`: empty (subfolders are recreated on use).
- AppContainer profile `CSpace.GodMode.Tests` (folder `%LOCALAPPDATA%\Packages\cspace.godmode.tests`, temp emptied). Its ACL grants exist **only** on `runtime\python`, `work` and `ac-tmp`.
- No labels anywhere. No GOD models downloaded. JARVIS's Ollama and its models are unchanged.
- Cleaned: spike scratch folders, the smoke-test proposal, and about 300 temp folders left in `%TEMP%` by earlier unit-test runs (identified by their test fixtures). Tests now keep all temp files under one folder that is removed at the end of each run (`tests/__init__.py`).

## 6. Next steps, in order
1. **Your OKs:** `godmode sandbox-setup --venv` (JARVIS tests with no network) and `godmode protect-secrets --apply`. After the venv grant, run one `tweak-run` and check that the JARVIS tests pass inside the AppContainer; they might touch paths outside the copy, which would show up as failures.
2. **G0 (needs OK, ~88 GB):** pull `qwen3.6:35b-a3b` and `gpt-oss:120b`, plus a pinned llama-server build. Fill `models.json` from `godmode gguf --ollama <tag>`. Benchmark tok/s and RAM at 2-3 `--n-cpu-moe` values. Check whether llama-server loads the Ollama blob directly. Then add a `LlamaServer` class next to PrivateOllama.
3. A live `godmode chat --slot advanced` session once the model exists. Try a memory squeeze: open apps until the guard freezes, close them, and check that it resumes.
4. Wire into CSpace (GOD window, native approval dialog, GPU lease with JARVIS). Touches UI/JARVIS: needs approval.

## 7. Decisions waiting for you
D1 apply-by-hand vs native dialog · D2 editable files list · D3 reserve size (6 GiB / 20%) · D4 Ascendent runtime after G0 · D5 one-time admin firewall/sandbox user · the venv grant (`sandbox-setup --venv`) · `protect-secrets --apply`.

## 8. Rules to keep
- Read `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` before running anything.
- GOD mode never writes the real repo; proposals are applied by a person.
- No `--no-mmap`/`--mlock`; servers only on loopback (enforced in `runtime.py`).
- Unit tests must not depend on real folders (the AppContainer run caught two that did; both fixed).
- Another session is editing UI files (`SpaceshipApp/SpaceshipUI/...`, e.g. `settings/registry.ts`). None of those changes are from GOD mode.

## 9. Rollback
1. `py -3 -B -m godmode sandbox-setup --undo` and `py -3 -B -m godmode protect-secrets --undo` (if applied).
2. Delete `GodMode/`, `%LOCALAPPDATA%\CSpace\GodMode` and `%USERPROFILE%\AppData\LocalLow\CSpace\GodMode`.
3. Optionally delete `%LOCALAPPDATA%\Packages\cspace.godmode.tests` (the AppContainer profile folder).
