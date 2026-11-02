# GOD mode plan (2026-10-30) - DRAFT, awaiting the user's approval

Nothing here is built. Work starts only after the JARVIS live test (J plan) and the wallpaper-slice live test.
Labels: **[M]** measured, **[C]** confirmed in code, **[V]** verified in a primary source, **[S]** secondary source only, **[E]** estimate, **[?]** unknown / must be tested on this laptop.

## 0. Names (one display constant each, `GodNames.cs`)

| Slot | Display name | Role | Tools |
|---|---|---|---|
| fast | **Jarvis Advanced** | Daily GOD work, verifier, quick answers | all allowed by the mode |
| big | **Jarvis Ascendent** | Long reasoning | all allowed by the mode |
| huge | **VISION** | Hours-long answers, overnight jobs | all allowed by the mode |
| abliterated | **ULTRON** | Conversation only | **none, ever** (no files, no settings, no network, no RAG) |

- "Ascendent" is the user's spelling. Correct English is "Ascendant". Both names live in one constant, so a later fix is a one-line change.
- ULTRON always has a purple border, a lock icon and the line "Unfiltered model. Conversation only." Its slot cannot be given tools, in code, in config or by any message (tested, section 6).

## 1. Hardware the plan is built for [M]
- Ryzen AI 9 465 (10C/20T), 31.3 GB RAM, RTX 5070 Laptop 8 GB VRAM + Radeon 880M, one 1 TB NVMe (C: 422 GB free).
- So every model above ~22 GB **cannot sit in RAM**. It is memory-mapped from the NVMe and pages in on use. Speed is set by NVMe reads, not compute. Every speed below is [E] until G0.

## 2. Gemini report: what applies (checked)

### Kept
- Separate `llama-server` process for GOD mode. Ollama stays for JARVIS (`keep_alive:0` frees its VRAM when GOD loads).
- Native `llama-server --jinja --chat-template-file <pinned file>`, plus a GGUF header check. Chat templates are executable Jinja and a known backdoor route (arXiv 2602.04653, 18 models / 4 engines) [V]. The old llama-cpp-python template RCE is CVE-2024-34359 [V].
- Job Object, loopback-only firewall rules, path canonicalisation (no reparse points, no `:` streams), a hash-chained `audit.jsonl`, a secrets blocklist.
- Skip cloud placeholders: attribute mask `0x00441000` (RECALL_ON_DATA_ACCESS 0x400000 | RECALL_ON_OPEN 0x40000 | OFFLINE 0x1000). This stops Google Drive (G:) and OneDrive downloading everything.
- Thermal stops: GPU 80 °C pause / 85 °C stop, NVMe 66 °C pause.
- Qwen3.6-35B-A3B Q4_K_M ~21.5 GB for the fast slot.

### Corrected
- **gpt-oss-120b Q2_K is pointless.** The experts are MXFP4 in every quant, so Q2_K ≈ 62.6 GB vs ≈ 63.4 GB for Q8_0. Use the ggml-org MXFP4 build (~1 GiB smaller, faster in one test) [S].
- The flag is `--load-mode none|mmap|mlock|mmap+mlock|dio`, not `-lm` [S]. Sources disagree whether `--mmap/--no-mmap` still exist, so G0 reads `--help` of the pinned build.
- USN journal needs admin. Use **Everything** (its service reads the journal) through its pipe `\\.\PIPE\Everything IPC` [S].
- Sandbox = a **low-integrity token of the user's own account** (or AppContainer if CUDA works there). A separate user account cannot read the user's profile, which defeats "read every file".
- Data folder: `%LOCALAPPDATA%\CSpace\GodMode\` (audit, config; worker cannot write) + `%USERPROFILE%\AppData\LocalLow\CSpace\GodMode\` (the only place the low-integrity worker can write: checkpoints, staging). Not ProgramData.
- Broker logic lives in **Core** (pure, testable) and runs **in the CSpace App process**. The worker never loads the broker.
- **DeepSeek-V4.1-Flash** exists (2026-09-10, -1017 variant 2026-10-17) [V], but it is ~763B total (552B + 196B Engram tables), Q2_K ~246 GiB [V]. It does not fit this laptop. Not used.
- DSpark (DeepSeek speculative decoding) is real, shown in vLLM with 7 speculative tokens [V]. llama.cpp support is unconfirmed [?]. Not planned; community gain ~1.15-1.25x over MTP [S], press claims 60-85% [S].

### Cut from v1
- CaMeL. The paper is real (77% of AgentDojo tasks with provable security vs 84% undefended) [V], but it needs a custom interpreter. Our design gets the key property more cheaply: **the model never authorises anything**. Code checks and a native human click do.
- DiagService Windows service (needs admin, new attack surface).
- LanceDB + embedding/reranker (no C# SDK). v1 = Everything + ripgrep + SQLite FTS5. Vectors come later (add-on A9).
- NPU offload (no llama.cpp path [?]).
- A separate gpt-oss-20b verifier. Jarvis Advanced with a verifier prompt does it with no extra download.

### Not verified (treated as unknown)
- DeepSeek-V4-Flash-0731 "discussion #58 repetition loops": not found. Size given as 284B and 304B in different places.
- arXiv 2512.13655 abliteration numbers (GSM8K −18.81 pts worst case): secondary only. Takeaway kept: abliteration costs some reasoning, so ULTRON is chat-only anyway.
- CUDA inside AppContainer or a low-IL token: no source. **Must test (G2).**
- MpCmdRun exit codes for a single-file scan: not documented. One old source guesses "always 0". We parse its text output and treat anything unexpected as "unknown", never as "clean".

## 3. Model lineup and disk budget

| Slot | Model (pinned by HF revision + SHA-256) | Size | Fits RAM? | Speed [E] |
|---|---|---|---|---|
| Jarvis Advanced | Qwen3.6-35B-A3B Q4_K_M (35B / 3B active, 262k ctx) | ~21.5 GB | yes (with 8 GB VRAM via `--n-cpu-moe`) | 15-30 tok/s |
| Jarvis Ascendent | gpt-oss-120b ggml-org MXFP4 (needs its harmony template) | ~61 GB | no, mmap | 2-6 tok/s |
| VISION | **G0 decides:** DeepSeek-V4-Flash-0731 (284B / 13B active, MIT, 1M ctx) smallest sane quant (Unsloth UD-IQ1_S is ~83 GB for V4-Flash [S]), or Qwen3-235B-A22B-2507 IQ2_XS ~71 GB [S] | 71-104 GB | no, mmap | 0.3-1.5 tok/s |
| ULTRON | huihui-ai Huihui-Qwen3.6-35B-A3B-abliterated, Q4_K_S ~20 GB (mradermacher) | ~20 GB | yes | 15-30 tok/s |

- Total ≈ 175-205 GB of 422 GB free. The model manager refuses a download if free space after it would drop below 100 GB.
- VISION at ~1 tok/s means a 3,000-token answer takes ~50 min, and prefill of a large file set is slower. This is the "hours" model. Quality at 1-2 bit is degraded; G0 checks it on a fixed question set before VISION is accepted.
- Avoid the "Claude 4.7 Opus" community fine-tunes and any repo without a clear author. TrevorJS gemma-4-31B-it-uncensored [S] is a fallback for ULTRON if the Huihui build tests badly.
- Mainline llama.cpp: V4-Flash runs with `llama-server -hf unsloth/...` per Unsloth, who also warn that older builds produce gibberish after turn 2 [S]. Some other V4 GGUFs need a fork. **We only use GGUFs that load on the pinned mainline build.**

## 4. Architecture

```
 CSpace.exe  (medium integrity, existing App)                       [trusted, deterministic]
 ├─ Control Center → Advanced → "Open GOD mode"  (existing WebView2 UI)
 ├─ GodWindow (new top-level Form, WebView2 ?panel=god, same hardened env)
 ├─ GodHost: starts/stops the two child processes in ONE Job Object (KILL_ON_JOB_CLOSE)
 ├─ GodBroker (Core logic): mode gate, path policy, settings proposals, staging copy,
 │     Everything queries, Defender, audit writer, guards (RAM/thermal/battery/game)
 ├─ Native approval dialogs (TaskDialog) — the ONLY thing that can approve a change
 │
 ├──pipe (per-run name, CurrentUserOnly, nonce like PipeGate)──┐
 │                                                              ▼
 │   ShipCore.God.exe  (LOW integrity, own token, no network but 127.0.0.1)   [untrusted-adjacent]
 │   ├─ agent loop: prompt → model → tool call → broker/ReadTools → model …
 │   ├─ ReadTools: list/stat/read/grep (ripgrep) with the SAME Core PathPolicy
 │   └─ checkpoints → LocalLow\CSpace\GodMode\jobs\
 │                         │ HTTP 127.0.0.1:<random port>, API key per run
 │                         ▼
 │   llama-server.exe  (LOW integrity or AppContainer; reads models folder only; loopback only)
 │
 └─ Ollama + JARVIS (unchanged) ← GPU lease message over the existing host pipe
```

Why this split:
- **Low integrity blocks writes by the OS**, not by our code. A low-IL process cannot write medium-IL files (the user's files, the repo, CSpace's install folder, the registry under HKCU except the Low key). It can still read almost everything, which is what "reads every file" needs. So even a bug in our tool code cannot modify files.
- The model only talks to the worker. The worker only has read tools. Everything that changes anything (settings, staging copy, scans, downloads) is in the App, behind code checks **and** a native dialog click. Model text never authorises an OS action (project rule).
- Approvals use a **native** dialog, not the web page, because model output is rendered in the web page. If a crafted file ever caused script injection in the GOD page, it still could not click "Apply".
- One Job Object owns both children: closing CSpace, the kill chord (Ctrl+Alt+Shift+1) or a crash kills them. Job limits: CPU rate hard cap, process count 4, `BELOW_NORMAL` priority, low memory priority (its pages are evicted before the user's apps), low I/O priority.

## 5. Permission modes

| Mode | Colour | Can read | Can change | Who approves |
|---|---|---|---|---|
| Chat | grey | nothing | nothing | - |
| Read (default) | cyan | files via PathPolicy, system info, Everything, ripgrep | nothing | - |
| Settings | amber | as Read | **CSpace settings only**, through ConfigSchema, never code | native dialog per batch, undo kept |
| Staging | orange | as Read | new files in `LocalLow\...\staging\` only; a copy out needs a native dialog per file | native dialog per file |
| ULTRON | purple | nothing | nothing | - (mode is fixed, cannot switch) |

Rules enforced in Core (`GodModeGate`) and tested:
1. Tool calls are checked against a per-mode allowlist. Unknown tool, wrong mode, bad argument → **tripwire** (section 7).
2. GOD can never change GOD's own settings: no `God*` key is writable in Settings mode, and switching modes is a UI click only, never a tool.
3. Settings mode allows only `toggle`, `slider`, `color`, `select` keys plus safe text keys (fonts, `AssistantLabel`, `HomeSize`). **Denied** [C, from `contract/config-keys.json`, 36 text keys]: every path, command, network or model key: `JarvisProfile`, `JarvisVault`, `JarvisVoice`, `JarvisMic`, `JarvisModel`, `JarvisModelFast`, `JarvisWakeModel`, `ObsidianTodo`, `ObsidianVault`, `WallpaperFile`, `PingHost`, `Drive1/2`, `HomeMonitor`, all `Llt*`. **No actions** (`apps.scan`, `defaults.all`, `setup.reset`, ...) are callable.
4. Each value goes through the existing `ConfigSchema.Problem(key, value)`. The proposal is shown as a diff (old → new). Apply writes through `IConfigStore` and keeps an undo snapshot. Undo is one click in the GOD window and in Control Center.
5. Staging: worker writes only inside the staging folder (OS-enforced by the LocalLow label). A copy out happens in the App after `PathPolicy.CanWriteOut(dest)`, which **always denies**: the repo, the CSpace install folder, `%LOCALAPPDATA%\Spaceship`, `%LOCALAPPDATA%\CSpace`, Windows, Program Files, ProgramData, Startup folders, any `.exe .dll .ps1 .bat .cmd .vbs .js .lnk .reg .msi` destination, and any existing file (no overwrite in v1). The dialog shows the destination and the full text diff.

PathPolicy (read side), all in Core with tests:
- `Path.GetFullPath` + `\\?\` normalisation, reject `:` after the drive (ADS), reject device paths (`\\.\`, `CON`, `NUL`...), reject UNC unless allowlisted, reject paths that resolve through a reparse point (checked per segment), skip cloud placeholders (mask above).
- Secrets blocklist (never read, never listed in output): browser profile folders (Login Data, Cookies, Local State), `.ssh`, `.gnupg`, `*.kdbx`, `.env*`, `*credentials*`, `*.pem/*.pfx/*.key`, Windows `Credentials` and `Protect` folders, the Jarvis vault keys, password-manager folders. A read of a blocked path is **not** a tripwire (the model can't know), it returns "blocked by privacy rule" and is logged.
- Size caps: 2 MB per text read, binary files return metadata + hash only; docx/pdf text extraction is a later add-on (needs a NuGet package, approval).

## 6. What the tests must prove (written before the code, xUnit in `ShipCore.Core.Tests`)
- `GodModeGateTests`: every tool × every mode matrix; ULTRON gets zero tools even if a message claims a different mode; unknown tool → Violation.
- `GodPathPolicyTests`: `..` escape, mixed slashes, `\\?\`, ADS, device names, 8.3 short names, trailing dots/spaces, reparse points (fake attribute source), placeholders mask, secrets list (case-insensitive), long paths.
- `GodSettingsProposalTests`: denied keys, `God*` keys, actions, values outside the schema, duplicate keys in one batch, oversized batches (cap 50).
- `GodStagingTests`: every denied destination class; overwrite refused; extension list; destination with a reparse point.
- `GodAuditLogTests`: hash chain detects an edited line, a removed line and a truncation; a new log starts from a stored anchor.
- `ProtocolTests` + `contract/fixtures/ui-to-host.json`: new `god.*` messages accepted/rejected.
- Worker tests (`ShipCore.God.Tests` or same project): tool-call JSON parsing never throws on malformed output; loop stops at the step cap; a `write` tool name never reaches the broker.
- No test calls a real model, real Defender, real file write outside a temp dir, or a real settings change (project test rules: fakes first).

## 7. Tripwire and incident explainer
- Trigger: any Violation from the mode gate, a staging write outside staging (should be impossible at low IL, so it means a bug), a worker that tries to open a non-loopback socket (firewall log or failed connect counted by the worker), or the worker/llama-server exiting with an access-denied in a write path.
- Action, in this order: (1) kill the job (Job Object terminate), (2) write the audit record (tool, args, mode, model, last 2 prompts hashed, time), (3) lock GOD mode until the user clicks "I've read this", (4) show the red incident panel.
- Explainer: **qwen3:4b via the existing Ollama**, given only the deterministic audit record. Its text is labelled "AI explanation, may be wrong". The raw record is always shown under it. The explainer has no tools and its output triggers nothing.

## 8. Long jobs, limits and guards
- Every job has a step cap (default 60 tool calls), a token cap and a wall-clock cap (default 6 h, VISION 12 h).
- Checkpoint after every tool result to `LocalLow\...\jobs\<id>.json` (transcript + tool results). Prompt cache via llama-server `--slot-save-path` and `/slots/<id>?action=save` [?, check on pinned build]. Resume after a pause, crash or reboot.
- Guards (checked every 5 s by the App, reusing existing sensors):
  - RAM: pause if available physical memory < 3 GB for 10 s (GlobalMemoryStatusEx). Never use `mlock` (would commit RAM and push the system into the pagefile).
  - Thermal: GPU 80 °C pause / 85 °C stop (existing GPU counters); NVMe 66 °C pause if HWiNFO exposes it [?], otherwise no NVMe guard and the UI says so.
  - Battery: Ascendent and VISION refuse to start on battery; a running job pauses when AC is unplugged (existing `PowerPolicy`).
  - Gaming / exam browser / fullscreen app: pause (existing `VisibilityPolicy`, `ExamBrowserList`).
  - Kill chord: already kills helper trees; GodHost also closes the job handle.
- Threads: `-t` = physical cores − 2. CPU job cap 70% by default, slider 30-90% (God setting, not GOD-writable).
- Pause = cancel the current generation, save the slot, keep the process; Stop = kill the job.

## 9. GPU / VRAM lease with JARVIS
- GOD start sends `god.gpu` over the existing host pipe. JARVIS unloads Ollama models (`keep_alive:0`), keeps Whisper/Kokoro (~1.27 GB VRAM [M]) and keeps working for **commands** (they skip the LLM [C]).
- JARVIS chat while GOD holds the GPU: **open decision D2.** Recommendation: a short busy line ("GOD mode is using the GPU, I can still run commands"), with a setting to allow CPU chat instead.
- GOD stop releases the lease. If CSpace crashes, the lease expires after 30 s without a heartbeat.
- `--fit` [S] is not trusted alone (mixed reports, ignores mmproj); G0 finds a manual `--n-cpu-moe` per model and stores it in the model profile.

## 10. Code changes, file by file

### Core (`SpaceshipApp/ShipCore.Core/God/`, pure, no OS calls, no new packages)
- `GodNames.cs` - display names and slot ids.
- `GodModeGate.cs` - modes, per-mode tool allowlist, argument rules (same style as `ActionGate`).
- `GodPathPolicy.cs` - read/write-out rules; OS facts come through a small `IFileFacts` interface (attributes, reparse, exists) so tests use fakes (same pattern as `IHwinfoRegistry`).
- `GodSettingsProposal.cs` - wraps `ConfigSchema.Problem`, adds the GOD deny list.
- `GodAudit.cs` - hash-chained JSONL record + verifier.
- `GodGuards.cs` - RAM/thermal/battery/game decisions from sampled values (like `PowerPolicy`).
- `GodJob.cs` - job state machine (Queued, Loading, Running, Paused, Done, Failed, Tripped) + checkpoint shape.
- `GodModelProfile.cs` - pinned model table (repo, revision, file, SHA-256, size, template hash, `n-cpu-moe`, ctx).
- `Protocol.cs` - new UI→host types: `god.open`, `god.send`, `god.pause`, `god.resume`, `god.stop`, `god.mode`, `god.model`, `god.undo`, `god.ack-incident`, `god.download`. Shapes checked by `Protocol.Problem`. **No** `god.approve` message: approval is native only.
- `MessageRouter.cs` - one more optional delegate (`God`), unchanged for existing callers.

### New worker (`SpaceshipApp/ShipCore.God/`, net10.0 console, references Core)
- `Program.cs` - read pipe name + nonce from args, connect, hello (like `JarvisPipe`), run.
- `AgentLoop.cs` - OpenAI-style `/v1/chat/completions` with tools to llama-server, step cap, checkpoint.
- `ReadTools.cs` - `fs.list`, `fs.stat`, `fs.read`, `fs.grep` (bundled `rg.exe`, args built from validated parts, no shell), `fs.hash`.
- No write API is linked into this exe except the LocalLow checkpoint/staging writer.

### App (`SpaceshipApp/ShipCore.App/`)
- `GodWindow.cs` - top-level Form, WebView2 at `https://spaceship.local/?panel=god`, same hardened settings and source check as `Overlay`, separate user-data subfolder not needed (same env).
- `GodHost.cs` - Job Object, low-IL token (`CreateRestrictedToken` + `SetTokenInformation(TokenIntegrityLevel)`) or AppContainer, random port + API key, health check, exit-code checks.
- `GodBroker.cs` - pipe server; runs Everything queries, Defender, system read tools, settings proposals, staging copy; writes the audit log; shows native dialogs.
- `GodSystemTools.cs` - read-only system facts (processes via existing snapshots, services, startup entries, scheduled tasks list, TCP table, event log System/Application, Defender status via WMI `MSFT_MpComputerStatus`, Authenticode check via `WinVerifyTrust`).
- `Program.cs` - add `llama-server.exe` and `CSpace.God.exe` to `Helpers`; tray item "GOD mode" (only when enabled); kill chord also calls `GodHost.Kill()`.
- `ShipCore.App.csproj` - copy the worker exe, `rg.exe` and the pinned `llama-server` build into output (not committed binaries: fetched by `Build-Installer.ps1` with pinned hashes).

### UI (`SpaceshipApp/SpaceshipUI/src/`)
- `main.tsx` - route `?panel=god`.
- `god/GodApp.tsx`, `god/Transcript.tsx`, `god/ActivityPanel.tsx`, `god/ModelPicker.tsx`, `god/IncidentPanel.tsx`, built from the existing `ui/kit` (HUD kit).
- `host/contract.ts` - mirror of the new types.
- `settings/registry.ts` - assistant category, new **Advanced** group "GOD mode": `act('god.open')`, toggle `GodEnabled` (default off), slider `GodCpuCap`, select `GodDefaultModel`, toggle `GodJarvisCpuChat`. The `God*` keys are added to `contract/config-keys.json` by the existing generator.
- Model text is rendered as **plain text** (markdown subset rendered to DOM nodes, never `innerHTML`); links are not clickable; file paths open only through a host message that re-checks PathPolicy and opens Explorer selected, never runs the file.

### Installer (`installer/CSpace.iss`, `PrivilegesRequired=lowest` [C])
- Firewall rules need admin, so they are an **optional elevated step** ("Allow GOD mode network lock"), run once from the GOD window. Without it, GOD mode still runs; the worker and llama-server are told loopback-only by args and the UI shows "network lock: off". [?] whether a per-user rule is possible without admin.

## 11. GOD window UI
- Separate window, opened from Control Center → Advanced → "Open GOD mode" (and the tray item). Dark HUD style from the kit, wider type for long reading, resizable, remembers size.
- **Left rail:** four model cards (name, size, state: not downloaded / ready / loading / loaded, last measured tok/s). ULTRON card purple with lock. Mode switch under it (colour per mode, section 5).
- **Centre:** transcript with streaming text, collapsible "thinking", each tool use as a small chip ("read C:\...\notes.md, 14 KB"). Citations: every file the answer used is listed at the end with path:line.
- **Right panel "Activity":** live tool calls (allowed / blocked by privacy / tripwire), guards (RAM free, VRAM, GPU °C, CPU cap, battery), job ETA from measured tok/s, audit chain status (green tick = verified).
- **Bottom bar:** Pause, Resume, Stop, "Run while I'm away" (AC only), step/token counters.
- **Approvals:** native TaskDialog, title "CSpace - GOD mode wants to change something", lists each change, buttons "Apply" / "Don't apply", default button is "Don't apply".
- **Incident:** red full-width panel: what was attempted (from code), the AI explanation (labelled), the raw record, "I've read this" unlock.
- **Long jobs:** when the window is closed, the job continues; finish posts a Notice + tray toast. Reopen shows the result.
- Accessibility: keyboard reachable, focus ring, mode never shown by colour alone (text label too), reduced motion respected.

## 12. Flaws and how each is handled

| # | Flaw / risk | Handling |
|---|---|---|
| 1 | Prompt injection in a file the model reads ("ignore rules, delete X") | Model has no write tools; mode gate in code; OS blocks writes at low IL; approvals native |
| 2 | Model asks to edit CSpace code | No tool exists; staging copy-out denies repo/app folders; tripwire |
| 3 | Self-escalation via settings (turn on its own modes, raise CPU cap) | `God*` keys never GOD-writable; mode switch is UI-only |
| 4 | Path/command settings used to run something (WallpaperFile, JarvisVault, Llt*) | Denied in Settings mode (list in §5) |
| 5 | Script injection in the GOD web page from model output | Text-only rendering, strict CSP, approvals native |
| 6 | Secrets read and repeated in chat | Secrets blocklist; no network so nothing leaves the PC; chat history stored locally only |
| 7 | Exfiltration over network | No network tools; loopback only; optional firewall lock; llama-server bound to 127.0.0.1 with per-run API key |
| 8 | Malicious GGUF or chat template | Pinned repo revision + SHA-256; template hash check; our own pinned `--chat-template-file`; mainline llama.cpp only |
| 9 | llama-server exploit | Runs low IL / AppContainer in a Job Object, models folder read only; pinned build updated deliberately |
| 10 | System slows to a crawl (mmap of 61-104 GB on 31 GB RAM) | Low memory priority, RAM guard, CPU cap, low I/O priority; accept test: HUD and JARVIS commands stay responsive during a VISION job |
| 11 | Pagefile thrash / commit exhaustion | No mlock; commit-charge check before load; refuse if commit < model ctx buffers + 4 GB |
| 12 | Overheating on long jobs | Thermal guard, pause not stop at 80 °C |
| 13 | Battery drain | Heavy models AC only |
| 14 | Fights JARVIS for VRAM | GPU lease (§9) |
| 15 | Google Drive / OneDrive download everything | Placeholder mask skip; G: excluded by default |
| 16 | Low-IL process can't use CUDA | G2 test first; fallback = medium-IL llama-server in a restricted token without write rights to user folders + Job Object (documented as weaker) |
| 17 | Low-IL worker can't talk to Everything (UIPI on window messages) | Broker (medium) queries Everything over the named pipe |
| 18 | Low-IL can't read some files (Security log, other users, protected folders) | Reported as "not readable", never escalated |
| 19 | Infinite tool loops / repetition loops | Step cap, repeat-call detector (same tool+args 3x stops), token cap |
| 20 | Hours-long job lost on crash or reboot | Checkpoint per step, resume |
| 21 | Wrong answers presented as fact | Citations required; optional verifier pass with Jarvis Advanced; VISION quality gate in G0 |
| 22 | Defender scan result misread (undocumented exit codes) | Parse output; unknown = "couldn't confirm", never "clean"; `-DisableRemediation` so nothing is quarantined by our request |
| 23 | Huge downloads fill the disk or are corrupt | Size shown before download, 100 GB floor, resumable, SHA-256 verify, approval per download |
| 24 | Audit log tampered | Lives in medium-IL folder the worker can't write; hash chain; anchor hash stored in settings |
| 25 | Kill chord or crash leaves orphans | Job Object KILL_ON_JOB_CLOSE + Helpers set |
| 26 | Two CSpace instances fighting over GOD | Existing single-instance mutex; GOD host mutex too |
| 27 | Abliterated model misused as a tool user | ULTRON hard-wired chat-only, tested; separate system prompt; no RAG |
| 28 | Model name confusion ("Ascendent") | One constant |
| 29 | Long contexts exceed VRAM (KV cache) | Per-model ctx in profile; q8 KV cache if supported [?]; context trimming with summary |
| 30 | Model output triggers JARVIS speech of secrets | GOD answers are never spoken unless the user clicks "read aloud" |
| 31 | Breaking existing CSpace | New code in new files; only additive changes to `Program.cs`, `Protocol.cs`, `MessageRouter.cs`, `registry.ts`, `main.tsx`; all existing tests must stay green; GOD disabled by default |
| 32 | 8.3 names / case tricks bypass deny lists | Compare on full canonical long path, case-insensitive; tests |

## 13. Slices (one at a time, failing test first, commit per slice on the user's word)

Gates for every slice: all `ShipCore.Core.Tests` green, UI `vitest` + `tsc` green, existing JARVIS tests untouched, RAM/CPU pass at the end, nothing staged blind, no weights/logs/secrets.

- **G0 - Benchmark and spec (no product code).** Scratch scripts outside the repo. Download Jarvis Advanced first (~21.5 GB, needs the user's OK), then the others one by one. Measure tok/s (prefill + decode), RAM working set, VRAM, GPU/NVMe temps, system responsiveness, for 2-3 `--n-cpu-moe` values each. Fixed 10-question quality set. **Output: final model table, VISION choice, pinned build + hashes.** Rollback: delete the models folder.
- **G1 - Core logic.** `GodNames`, `GodModeGate`, `GodPathPolicy`, `GodSettingsProposal`, `GodAudit`, `GodGuards`, `GodJob`, `GodModelProfile` + all tests from §6. No OS calls. Rollback: remove `God/` folder.
- **G2 - Sandbox spike.** Tiny exe: start under low IL and under AppContainer, run `cuInit` + a 1-token llama-server load, try a write to `Documents` (must fail), connect to a non-loopback address (must fail with firewall lock). Decides the sandbox. Rollback: delete spike.
- **G3 - GodHost.** Job Object, token, port + key, health check, Helpers, kill chord. Fake child process in tests.
- **G4 - Worker + Read mode.** Pipe, agent loop, read tools, ripgrep, checkpoints. Fake llama-server (canned responses) in tests.
- **G5 - GOD window UI + protocol.** `?panel=god`, registry rows, contract mirror, fixtures. Chat and Read only.
- **G6 - Tripwire + incident explainer.**
- **G7 - Long jobs + guards + GPU lease** (JARVIS side: handle `god.gpu` in the existing host pipe code).
- **G8 - ULTRON slot** (chat-only, tests that no tool path exists).
- **G9 - Settings mode** with native approval + undo.
- **G10 - Staging mode** with native approval per file.
- **G11 - PC tools** (system facts, Defender status + scan, signatures, Everything).
- **G12 - Model manager** (download with approval, verify, delete model).
- **G13 - Efficiency pass + one combined live test** (with the user present, fake-first rules apply: Defender scan only on a test file, settings change only on a cosmetic key, staging copy to a temp folder).

## 14. Useful add-ons (after v1, each its own approval)
- A1 "Run overnight": queue jobs, AC only, start after idle, report in the morning.
- A2 PC health report: startup impact, big files, duplicates, old drivers, disk SMART, failing services (read-only).
- A3 Privacy audit: which apps used mic/camera/location (CapabilityAccessManager registry, read-only).
- A4 CSpace integrity watch: hash manifest of CSpace + repo files; a change outside a known build trips an alert (also catches outside tampering).
- A5 Compare answers: same question to two models side by side.
- A6 Export an answer to Markdown in staging (Staging mode rules).
- A7 "Explain this folder / this crash dump / this log" quick actions.
- A8 Docx/PDF text extraction (needs OpenXml/PdfPig NuGet approval).
- A9 Local semantic search: llama-server `--embedding` + flat int8 vector file (no LanceDB).
- A10 Voice hand-off: "Jarvis, ask VISION ..." opens the GOD window with the question; the answer stays on screen (no auto-speak).
- A11 Speed history per model, to give honest ETAs.

## 15. Open decisions (the user's call)
- D1 Storage: `%LOCALAPPDATA%\CSpace\GodMode\` + `LocalLow\CSpace\GodMode\` (recommended) vs ProgramData.
- D2 JARVIS chat during a GOD job: busy line (recommended) vs CPU fallback.
- D3 VISION: DeepSeek-V4-Flash-0731 vs Qwen3-235B-A22B, decided by G0 numbers.
- D4 Spelling: keep "Ascendent" or use "Ascendant".
- D5 Firewall lock: run the one-time elevated step or not.
- D6 New packages for later add-ons (Microsoft.Data.Sqlite for FTS5 in G11, OpenXml/PdfPig for A8).

## 16. Sources
- Chat template backdoors: https://arxiv.org/abs/2602.04653v2 , https://www.pillar.security/blog/from-discovery-to-large-scale-validation-chat-template-backdoors-across-18-models-and-4-engines
- CaMeL: https://arxiv.org/abs/2503.18813
- DeepSeek V4.1-Flash: https://api-docs.deepseek.com/news/news261017/ , https://huggingface.co/nvidia/DeepSeek-V4.1-Flash-NVFP4 , https://huggingface.co/ISTA-DASLab/DeepSeek-V4.1-Flash-1017-GSQ-RCO-GGUF , https://unsloth.ai/docs/models/deepseek-v4.1-flash
- DeepSeek V4-Flash GGUF: https://huggingface.co/unsloth/DeepSeek-V4-Flash-GGUF , https://huggingface.co/unsloth/DeepSeek-V4-Flash-0731-GGUF , https://github.com/unslothai/unsloth/releases/tag/v0.1.52-beta
- DSpark: https://huggingface.co/fraserprice/DeepSeek-V4-Flash-DSpark , https://letsdatascience.com/blog/deepseek-dspark-85-percent-faster-open-source
- gpt-oss MXFP4 sizes: https://huggingface.co/unsloth/gpt-oss-120b-BF16
- Qwen3.6-35B-A3B: https://recipes.vllm.ai/Qwen/Qwen3.6-35B-A3B
- Abliterated: https://huggingface.co/huihui-ai/Huihui-Qwen3.6-35B-A3B-abliterated-MTP-GGUF , https://huggingface.co/mradermacher/Huihui-Qwen3.6-35B-A3B-abliterated-GGUF , https://featherless.ai/models/TrevorJS/gemma-4-31B-it-uncensored
- Qwen3-235B sizes: https://llmrun.dev/model/qwen-qwen3-235b-a22b-instruct-2507
- MpCmdRun: https://brianreiter.org/2010/07/21/mse-v2-command-line-scanning/ , https://learn.microsoft.com/en-us/answers/questions/1164115/windows-defender-command-line-tool-(mpcmdrun-exe)
