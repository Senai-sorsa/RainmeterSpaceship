# GOD-MODE plan (2026-11-03)

Supersedes the model and runtime parts of `tasks/god-mode-plan.md` (2026-10-30). The safety sections there (§5 path policy, §7 tripwire, §12 flaw table) still hold unless this file says otherwise.
Labels: **[M]** measured on this laptop, **[C]** confirmed in code, **[V]** primary source, **[S]** secondary source, **[E]** estimate, **[?]** unknown, must be tested.

## 0. What changed since 10-30 (the user's rulings, 2026-11-03)
1. **Two models for now**, the two weaker tool-using ones: **Jarvis Advanced** (Qwen3.6-35B-A3B) and **Jarvis Ascendent** (gpt-oss-120b). VISION stays out. **ULTRON (abliterated) has a reserved slot**: chat only, no tools ever.
2. **Ascendent runs "split"**: it must work even though it is bigger than RAM, slowly if needed (an hour is fine), without pushing the system.
3. **Self-tweaks are allowed** (this reverses the 10-30 "no code edits" rule): small changes to features, never to the main structure, never to GOD mode's own code, and tests are forced.
4. **Every high-RAM model measures free RAM and uses only a comfortable amount.**
5. **Built separately**: everything lives in `GodMode/`. No JARVIS code, no UI code, no CSpace code touched. No model downloads yet.

## 1. Hardware [M, 2026-11-03]
- RAM 31.3 GB. **GPU: RTX 5070 Laptop reports 12,231 MiB VRAM** (`nvidia-smi`). The 10-30 plan said 8 GB; that was wrong. 12 GB changes the placement maths for the better.
- C: 410 GB free. Ollama 0.40.13 installed. Models already on disk: llama3.1:8b, llama3.2:3b, qwen3:4b-instruct-2507, phi4-mini, nomic-embed-text.
- Python 3.12 (only interpreter). GOD mode code uses the **standard library only**, so it needs no install.

## 2. Models (registry checked 2026-11-03, read-only manifest query) [M]

| Slot | Name | Runtime | Tag / file | Size | Fits? |
|---|---|---|---|---|---|
| advanced | Jarvis Advanced | **Ollama** | `qwen3.6:35b-a3b` (same digest as `qwen3.6:35b`) | 22.6 GB | yes: 12 GB VRAM + RAM |
| ascendent | Jarvis Ascendent | **llama-server (split)**, Ollama as the fallback test | `gpt-oss:120b` | 65.4 GB | **no**: > 31 GB RAM + 12 GB VRAM → streamed |
| ultron | ULTRON | Ollama | reserved: huihui-ai Qwen3.6-35B-A3B abliterated (~20 GB) | - | slot only |
| vision | VISION | - | not planned now | - | - |

### Why Ascendent needs llama-server, not plain Ollama
- What the user described ("split up the processing so it's slower but comfortable") exists. It is **MoE expert offload plus memory-mapped streaming**. gpt-oss-120b is a mixture-of-experts model (117B total, ~5.1B active per token) [V]. Each token only touches a few experts. So:
  - attention and shared weights plus the KV cache go to **VRAM** (they are used on every token);
  - expert weights stay in a **memory-mapped file**. The OS keeps the hot experts in RAM and reads the rest from the NVMe on demand.
  - llama.cpp flags: `-ngl 99 --n-cpu-moe N` (or `-ot ".ffn_.*_exps.=CPU"`). **Never** `--no-mmap` (it loads everything into RAM, then gets killed when the model is bigger than RAM) or `--mlock` (it locks every page and fails) [S: dev.to guide; carteakey].
  - Reported: ~8 tok/s on a 32 GB laptop for a >100B MoE [S, anecdotal]; 18-28 tok/s with 12 GB VRAM **and 64 GB RAM** [S]. Our case is RAM < model, so expect **~1-8 tok/s [E]**. G0 measures it.
  - Rule of thumb [S]: RAM for experts ≥ 70% of the expert size gives near full speed; 40-70% works with variable speed; **< 40% is not worth it**. Ours: ~20-23 GB comfortable RAM vs ~58 GB of experts ≈ 35-40% [E]. Borderline, so G0 decides. The placement planner (§4) computes it live and refuses below the floor.
- **Ollama does not expose expert offload.** Feature request ollama#11772 is still open (comments up to 2026-10-25) [V]. One user reports `LLAMA_ARG_CPU_MOE=1` working on Windows with Ollama 0.30 [S, unverified, global to all models, so it would also hit JARVIS]. Ollama also has no per-process memory caps we can apply without affecting JARVIS (both share one `ollama.exe`).
- **Plan:** Advanced on Ollama, as the user asked. Ascendent on a dedicated, pinned `llama-server.exe` (official ggml-org release, SHA-256 pinned) in our own Job Object with a hard working-set cap. **Fallback test in G0**: `ollama pull gpt-oss:120b` and see whether Ollama loads it at all. If it does and it stays comfortable, use Ollama for both.
- Disk saver [?]: Ollama stores gpt-oss as a GGUF blob. If `llama-server` loads that blob path directly, we keep one 65 GB copy, not two. G0 checks this with `godmode gguf <blob>` (header reader, already built).
- **CUDA gotcha** [S]: with experts on CPU, set `GGML_CUDA_NO_PINNED=1`, or the load can fail with "CUDA error: out of memory" (ollama#11772, 2026-06-05).
- gpt-oss needs its **harmony** format. Tool calls break if the template is wrong. It also has a strong prior for an `apply_patch` tool (arXiv 2604.00362 [V]: an undefined `apply_patch` was called 860 times, and defining it fixed that). **So our tweak tool is named `apply_patch`** and takes search/replace edits.

## 3. Comfortable-RAM rule (the user's note) — built: `godmode/memory.py`
Measured, not guessed. Every model load and every 2 s while running:
1. **Measure**: `GlobalMemoryStatusEx` (available physical, commit used/limit) and `nvidia-smi --query-gpu=memory.total,memory.used` (fixed args, exit code checked). Unknown VRAM is not treated as zero: GPU placement is then refused.
2. **Comfortable budget** = available RAM − reserve, where reserve = max(**6 GiB**, **20% of total**) [E, tunable]. On this laptop that leaves ~6.3 GiB for Windows, CSpace, JARVIS, the browser and Discord on top of what is already in use. VRAM budget = free VRAM − **1.5 GiB** for JARVIS Whisper + Kokoro (1.27 GB [M, J plan]).
3. **Placement planner** (pure, tested): from the GGUF's own tensor table (expert bytes vs the rest, layer count) and the KV cost per token, it picks the context size, `--n-cpu-moe`, threads (physical cores − 2) and mode:
   - `gpu`: everything fits in VRAM;
   - `split`: CPU experts fit inside the RAM budget (full speed);
   - `stream`: CPU experts > the RAM budget but ≥ 40% fits → mmap streaming, slower;
   - `refuse`: below 40%, or the non-expert part + KV doesn't fit in VRAM even at the minimum context. The reason is shown in plain words.
4. **Enforce (llama-server, own process)**:
   - **Hard working-set cap** = the RAM budget (`SetProcessWorkingSetSizeEx` with `QUOTA_LIMITS_HARDWS_MAX_ENABLE`) [V, API]. Resident pages beyond the cap get pushed out instead of taking the user's RAM. [?] whether mapped-file pages count fully against the cap is checked in G2 with the spike.
   - **Low memory priority** (`SetProcessInformation(ProcessMemoryPriority, MEMORY_PRIORITY_LOW)`): its pages are dropped first when the user needs RAM.
   - **Job Object**: commit cap for *private* memory (buffers, not the mapped model), kill-on-close, BELOW_NORMAL priority, CPU hard cap (default 70%), max 4 processes.
5. **Enforce (Ollama, shared with JARVIS)**: a pre-load check (the model must fit the budget at the chosen `num_ctx`). While it runs, the same watchdog; under pressure, abort the request and unload with `keep_alive: 0`.
6. **Watchdog** (pure, tested), with hysteresis so it doesn't flap: available < **4 GiB** for 3 samples → **pause** (cancel the generation, keep the checkpoint); available > 5.5 GiB for 5 samples → **resume**; available < **2.5 GiB** once → **stop** (kill the job; the checkpoint survives). Commit > 90% of the limit → pause.

## 4. Self-tweak lane ("small changes, tests forced") — built: `godmode/tweak.py`, `godmode/testgate.py`
Research that shaped it:
- **Darwin Gödel Machine** (arXiv 2505.22954 [V]): the self-modifying agent *removed the logging the hallucination checker relied on* and scored well without fixing anything ("objective hacking"), even though the checker itself was hidden. **Lesson: the agent must not be able to touch anything on the path to the score**: tests, the test runner, logging used by checks, the gate.
- open-dgm / SuperQode / Self-Harness (arXiv 2606.09498) [S/V]: fixed **edit surfaces**; protected evaluator, checks, approvals and sandbox; candidate generation is separate from acceptance; regression tests on every candidate.
- Self-evolving agent survey (arXiv 2608.03392) [S]: 170 of 1,030 patches passed the tests while dropping protections. **Passing tests is not enough**, so we add a static gate and a human review.
- Diff-XYZ (arXiv 2510.12487) [V]: **search/replace** edits beat unified diffs, and small models struggle with any format. So: search/replace with an exact, unique match, plus a tight size cap.
- OpenAI Codex on Windows [V]: unelevated mode = restricted token + ACLs; elevated mode = a dedicated sandbox user + firewall rules (admin). Our v1 = low-integrity token + Job Object (no admin); the dedicated user is a later upgrade (D5).

Pipeline (each step is code, never the model's say-so):
1. The model calls `apply_patch` with ≤ 3 files, ≤ 60 changed lines, ≤ 6,000 chars, plus a one-line reason.
2. **Surface check**: the path must be on the editable list (`surfaces.json`) and on **no** protected list. Protected always wins: `GodMode/**` (its own code), every test file and test folder, test runners, `CLAUDE*.md`, `.git`, `.claude`, installer, contract, the safety modules (JARVIS `actions.py`, `launch.py`, `host_pipe.py`, `confirm.py`, `stopkey.py`; CSpace `ActionGate`, `KillSwitch`, `PipeGate`, `ConfigSchema`...). Paths are canonicalised; `..`, ADS, device names, absolute paths and reparse points are rejected. A protected hit is a **tripwire**, not just a refusal.
3. **Content check on the new text**: no new imports outside a small allowlist; no `subprocess`, `ctypes`, `winreg`, `socket`, `os.system/remove/unlink/rmdir`, `shutil.rmtree/move`, `eval/exec/compile/__import__`, `importlib`, `pickle`, `open(..., "w")`, network libraries; no mention of godmode/audit/tripwire.
4. **Structure check (Python AST)**: the same top-level functions and classes with the **same signatures**, the same class methods, no new or removed top-level definitions, no new imports, `ACTIONS`-style top-level tables keep their keys. Only *bodies and literals* may change. That is "tweaks, not the main structure", checked by code.
5. **Disposable copy**: the broker copies the target tree into `%LOCALAPPDATA%\CSpace\GodMode\work\<id>\` (medium integrity, so neither the low-IL worker nor the low-IL test run can change the copy's tests between runs). No `.git`, `Data`, `kokoro`, `voices` or weights; links are skipped. The test run's TEMP points to `LocalLow\...\tmp\<id>`. The real repo is never written. The copy is deleted afterwards.
6. **Forced tests** (the broker runs them, not the model): a baseline run on the untouched copy, then the patched copy. Same commands (`testgate.json`), low-IL sandbox, no network variables, timeout, Job limits. Accept only if: exit code 0 on both, the pass line is present, **test count ≥ baseline**, and the **protected-file hash manifest is unchanged** after the run (catches a patch that edits tests at runtime). The repo rule "fakes first" holds: the test suites run are the existing vetted ones, and the content check bans new OS calls.
7. **Output**: a proposal bundle (diff, reasons, test logs, gate results, audit hash) in `%LOCALAPPDATA%\CSpace\GodMode\proposals\<id>\` (medium, so the worker can't edit a proposal after it passed). **Applying it to the real repo is a human step**: `godmode proposal show <id>` prints the diff and the exact `git switch -c god/tweak-<id>` + `git apply` commands. Nothing auto-merges.
8. Rate limit: 1 active proposal, max 10 per day (config). A failed gate goes back to the model as text once; the second failure stops the attempt.

## 5. Sandbox — built: `godmode/sandbox_win.py` (+ `spikes/lowil_spike.py`)
- Worker and llama-server start under a **low-integrity copy of the user's token** (`DuplicateTokenEx` → `SetTokenInformation(TokenIntegrityLevel, S-1-16-4096)` → `CreateProcessAsUserW`) [V, MSDN bb625960]. The OS then blocks writes to the user's files, the repo, CSpace and HKCU (except LocalLow / AppDataLow). Reads still work. So: **it cannot touch its own code even if our Python has a bug.**
- Started suspended, put in the Job Object, then resumed (no escape window).
- Honest gaps: (a) low IL alone does not block **reads** of secrets → `PathPolicy` blocks them in code (the dedicated-user design would fix this with deny ACLs, D5); (b) low IL does not block **network** → the worker has no network code, llama-server binds 127.0.0.1 with a per-run API key, and the clients refuse non-loopback URLs; a firewall rule needs admin (D5); (c) CUDA at low IL is unverified → G2.
- Data folders: `%LOCALAPPDATA%\CSpace\GodMode\` (audit, config: medium, so the worker can't write) and `%USERPROFILE%\AppData\LocalLow\CSpace\GodMode\` (work, proposals, jobs, checkpoints: worker-writable).

## 6. Modes and tools — built: `godmode/gate.py`, `godmode/tools.py`
| Mode | Tools |
|---|---|
| chat | none |
| read (default) | `fs_list`, `fs_stat`, `fs_read`, `fs_grep`, `sys_memory` |
| tweak | read tools + `apply_patch` (proposal only, §4) |
| ultron | **none, fixed at construction; it can't be switched** |
- The mode is set by the person (constructor/CLI flag), never by a tool. An unknown tool, a tool not allowed in the mode or a bad argument → **tripwire**: stop the job, write a hash-chained audit record, lock until acknowledged, and explain the incident using qwen3:4b fed **only the audit record**, labelled "AI explanation, may be wrong".
- Read side: `PathPolicy` (canonical paths, no ADS/device/UNC, no reparse points, skips cloud placeholders with mask `0x00441000`, skips G:, secrets blocklist, 2 MB cap).

## 7. Agent loop — built: `godmode/agent.py`
Ollama `/api/chat` (Advanced) or OpenAI-style `/v1/chat/completions` (llama-server) behind one interface. Loopback-only URLs. Step cap 60, repeat detector (same tool + args 3× → stop), wall-clock cap, a checkpoint after every tool result (`jobs/<id>.json`), resume from a checkpoint. File contents go back to the model as quoted, labelled data; they can't change the mode or the tools.

## 8. What is built now (this session) vs later
**Now, in `GodMode/` only**: profiles + names, memory probe/budget/planner/watchdog, GGUF header reader (sizes + chat-template safety scan), path policy, mode gate, audit chain, tweak gates, test gate, runtime clients and llama-server command builder, low-IL + Job Object launcher, agent loop, tools, `doctor` (read-only health check), unit tests (fakes only), the low-IL spike.
**Later (each needs the user):**
- **G0** download + benchmark (qwen3.6:35b-a3b 22.6 GB; gpt-oss:120b 65.4 GB via Ollama, then try llama-server on the same blob). Fill in `models.json` from `godmode gguf` (layers, expert bytes). Measure tok/s, RAM, VRAM, temperatures, desktop responsiveness at 2-3 `--n-cpu-moe` values.
- **G2** run the low-IL spike with llama-server + CUDA; confirm how the working-set cap treats mapped pages.
- Wire into CSpace (GOD window, native approval dialog, GPU lease with JARVIS): UI/JARVIS changes, so only after the user approves.
- Download the pinned `llama-server` build (needs approval).

### 8a. Built and checked on 2026-11-03 [M]
Commands run from `GodMode/`. Python 3.12, standard library only.
- `py -3 -B -m unittest discover -s tests -t .` → **Ran 92 tests, OK**. Fakes only: no model, no OS action, no repo write. A dry-run grep of `tests/` for subprocess/ctypes/delete/shutdown/registry found nothing.
- `py -3 -I spikes/lowil_spike.py` → **4/4 PASS**: a low-IL child was **denied** a write to a medium folder (PermissionError), **could** write LocalLow, was killed by the job on timeout, and a 1.5 GB allocation was stopped by a 512 MB private-commit cap.
- `py -3 -B -m godmode doctor` → RAM 31.3 GiB total, **13.7 GiB free, reserve 6.3, comfortable 7.5 GiB**; commit 47.1/80.1 GiB; VRAM 11.9 GiB, comfortable 10.4; 10 physical cores; C: 439 GB free; Ollama 0.40.13 reachable; neither GOD model installed.
  - With what was open at that moment, **both models were refused** by the comfortable-RAM rule. Ascendent: only 14% of its CPU experts fit (floor 40%). Advanced: about 14 GiB of RAM needed vs 7.5 GiB comfortable (a later change added Ollama "stream" mode at ≥ 40% coverage, so Advanced would now stream at ~50% [E]). So the rule works, and **Ascendent needs ~23 GiB free before it starts** [E, re-measure in G0].
- `tweak-check` on a protected file (`test_jarvis.py`) → **VIOLATION**, exit 2. On a one-string log-wording edit to `jarvislib/quiet.py` → OK.
- `tweak-run` on that edit → **proposal 20261103-28a7faa8 passed**: real `test_jarvis.py` ran at low integrity on the copy, baseline exit 0 in 62.7 s, patched exit 0 in 74.5 s, protected hashes unchanged, 2 changed lines, 2 m 17 s in total. The real `quiet.py` was not modified (`git status`). `audit-verify` → OK. (It is a pipeline smoke test; it doesn't need applying.)

> **Update 2026-11-03 (later):** five spikes answered most of 8b/8c on this laptop: CUDA works at low IL, the hard cap holds mapped model pages, a private capped Ollama works, an AppContainer blocks all network, and NO_READ_UP labels block secret reads without admin. Later the same day the gap fixes were built and verified (private capped Ollama, freeze/thaw guard, low-IL reader, AppContainer tests, secret labels). Status and next steps: `HANDOFF.md` §3 and §6.

### 8b. Known gaps (honest list)
- **Worker and broker are still one process** in the CLI (`godmode chat`). The model's read tools run at medium IL; apply_patch already runs the tests sandboxed. Next: G4 runs the agent loop in a low-IL child talking to the broker over a pipe, as §5 describes.
- The watchdog checks between model calls. A single long llama-server generation needs the runner-level thread (G7) that pauses or kills the job mid-generation.
- Ollama's runner is shared with JARVIS, so it has no hard working-set cap. Only the pre-load check, the watchdog and `keep_alive: 0` unload apply.
- Model sizes in `models.json` are estimates until `godmode gguf --ollama <tag>` reads the real files (G0).
- Network and secret-read gaps of low IL (§5) stay until the D5 admin step.

### 8c. Research to do at each next step
- **G0**: does Ollama 0.40 load gpt-oss:120b on 31 GB at all (memory check)? Does llama-server load the Ollama blob directly? Measure tok/s at 2-3 `--n-cpu-moe` values with mmap streaming on **Windows** (sources are Linux-only). Does `LLAMA_ARG_CPU_MOE` really change Ollama?
- **G2**: CUDA inside a low-IL process; whether the hard working-set cap trims mapped model pages (measure the working set with `--n-cpu-moe` in stream mode); whether file-backed mapped pages count against the job commit cap.
- **G4**: pipe protocol between the low-IL worker and the broker (reuse the CSpace `PipeGate` nonce pattern); CaMeL-style quarantined reader as a later option.
- **Tweak quality**: run the JARVIS semi-live harness (`tools/semi_live.py`) on the copy as a second, behaviour-level gate (score must not get worse), using the held-out cases so the model can't tune to them.

## 9. Open decisions (the user's)
- D1 Approval for a tweak: CLI print-and-apply by hand (now) vs a native dialog in CSpace (later).
- D2 Editable surfaces v1: `persona.txt`, `pronounce.txt` and non-safety `jarvislib/*.py`. Add UI CSS/theme files later?
- D3 Reserve size: 6 GiB / 20% default. More cautious = slower Ascendent.
- D4 Ascendent runtime after G0: llama-server split (recommended) vs Ollama if it loads comfortably.
- D5 One-time admin step: firewall lock + a dedicated sandbox user (closes the read-secrets and network gaps, like Codex "elevated").

## 10. Risks
| Risk | Handling |
|---|---|
| Ascendent too slow at < 40% RAM coverage | planner refuses with the numbers; G0 data; smaller ctx; the user may close apps first |
| Windows page cache behaves unlike Linux under mmap streaming | G0 measures; working-set cap + low memory priority; watchdog stop |
| Objective hacking (DGM) | tests, runners, gates and GodMode are protected; hash manifest before/after; human applies |
| Tests pass but behaviour is worse | AST structure lock, content ban list, size caps, human diff review, JARVIS semi-live harness can be run on the copy later |
| Prompt injection from read files | no write tool except the gated proposal; mode fixed by the person; OS low IL |
| gpt-oss tool-format drift | harmony via the runtime's template; the `apply_patch` name matches its prior; malformed calls are tolerated (never crash) |
| Breaking CSpace/JARVIS | nothing outside `GodMode/` is touched; JARVIS keeps its models; GOD is not wired in yet |

## 11. Sources
- DGM: https://arxiv.org/abs/2505.22954 · Self-Harness: https://arxiv.org/abs/2606.09498 · Self-evolving coding agents: https://arxiv.org/abs/2608.03392
- Diff-XYZ: https://arxiv.org/abs/2510.12487 · gpt-oss harmony: https://arxiv.org/abs/2604.00362
- Codex Windows sandbox: https://developers.openai.com/codex/windows
- Low integrity: https://msdn.microsoft.com/en-us/library/bb625960 · SetProcessWorkingSetSizeEx: https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-setprocessworkingsetsizeex · Job limits: https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information
- MoE > RAM: https://dev.to/eme_gug_0821b41b948be6516/running-moe-llms-larger-than-your-ram-a-practical-guide-to-mmap-expert-offloading-and-ssd-2f88 · https://carteakey.dev/blog/local-inference/optimizing-gpt-oss-120b-local-inference/
- Ollama: https://github.com/ollama/ollama/issues/11772 · https://github.com/ollama/ollama/issues/16637 · docs v0.40.13 (Context7: KV cache type, flash attention, use_mmap, tool calling)
