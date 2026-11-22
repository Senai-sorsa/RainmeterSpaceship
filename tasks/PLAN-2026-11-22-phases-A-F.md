# Plan, 2026-11-22: phases A to F

This is a planning document only. No code has changed. Each phase needs your approval before it starts.
Every item lists its goal, scope, non-goals, how we know it is done, how it gets checked, the risks and how to undo it.

**Rules for every phase:**
- Work on a branch, with one commit per item, so `git revert <sha>` undoes exactly one change.
- Run the full gate after each item:
  - `npx tsc --noEmit -p .`
  - `npx vitest run`
  - `dotnet test ShipCore.Core.Tests`
  - the JARVIS gate: test_jarvis on venv and on py3, host_pipe, run_all and the goldens.
- Fake first, and do a dry run first. Nothing may touch the recycle bin, shutdown, sleep or file deletion.
- Measure CPU, RAM, GPU and VRAM before and after any visual or host change. Use PresentMon or Task Manager GPU columns, plus `Get-Counter` for the CSpace and msedgewebview2 processes, 60 s idle and 60 s with animation.

**Baseline at the start (2026-11-22, all run):**
- tsc: exit 0.
- vitest: 536 passed.
- dotnet: 322 passed.
- test_jarvis: exit 0 on both runs, with 0 tripwires.
- host_pipe: 0 failed.
- replies: 0 diffs.
- routes: **5 diffs, all intended:**
  - The crisis line gets `directed=yes`.
  - "schedule a meeting" now gets "can't do that yet".
  - "be serious for ten minutes" now gets `mood_for`.

---

## A. Bug fixes (small, one commit each)

| # | Where | Bug | Fix | Test |
|---|---|---|---|---|
| A1 | `Program.cs:618` | `new FileInfo(file).Length` throws if the wallpaper file is gone, so `wallpaper.src` is never posted. | Guard it with `File.Exists` or try/catch, log `len=?`, and still post. | A HostLogic test that uses a missing path. |
| A2 | `Program.cs:626` | `WallLog` has one cap of 80 lines for the whole process. Console errors use it up, and later SYNC/SHOW lines are lost. | Give console errors their own cap, separate from wallpaper events. | A unit test on the counter. |
| A3 | `turnstate.py:32` | `DID_WHAT` matches small talk such as "what did you do last weekend". | Match only when nothing time- or social-related follows, or when the last turn ran an action. | Add a golden pair: "what did you do last weekend" goes to chat; "what did you just do" goes to recap. |
| A4 | `routing.py:423` | The `fixed_num` rewrite turns "set volume to 30, no, mute" into "set volume to mute". | When the correction is not a number, keep the corrected clause whole. | A route test. |
| A5 | `jarvis.py:992` | The `if line:` "no words" branch is dead, because `missed_line` never returns "". | Delete the dead branch, or make `missed_line` return "" for empty input, whichever matches the intent in the git blame. | Existing tests. |
| A6 | `jarvis.py:686` | The "turn is stuck" error stays on screen until the next turn. | Clear it when the stuck turn finishes or after a timeout. | A test using a fake clock. |
| A7 | `Program.cs:1099` | The PickFile dialog can open twice, because it is re-entrant. | Add a `_picking` flag and ignore a second pick while one is open. | Manual double-click. |
| A8 | `boot.ts:65` | NETWORK shows ONLINE for any reading, even 0. | Show ONLINE only when connected; show 0 or no reading as OFFLINE. | A vitest case. |
| A9 | `Program.cs:640` | `GetProperty("entry")` has no guard. | Use `TryGetProperty`. | A malformed-message test. |
| A10 | `confirm.py:11` | `format (my\|the\|c)` asks for confirmation on "format the paragraph". This was already there before this branch. | Require a drive or disk word. Keep the false-positive side safe. | Confirm tests. |
| A11 | `routing.py:497` | "make it 50" after a timer changes the timer, but the comment says it should not. | **You chose: follow the context.** Keep the behaviour (it changes whatever we were just talking about) and fix the comment. Add tests for both orders: after a timer it changes the timer, after a volume change it changes the volume. Phase E replaces this with a proper topic tracker. | Route tests for both orders. |
| A12 | goldens | `routes.jsonl` had 5 intended diffs. | **Done 2026-11-22, with your approval.** I regenerated it with `golden_routes.py`: exactly 5 lines changed. `--check` now finds 0 diffs over 834 lines (rc=0). Not committed yet. | Done. |

**Non-goals:** refactors, and any change to how the personality answers.

**Rollback:** revert the commit for that item.

---

## B. Silver corner and edge pieces for fitted picture mode

**What ship.png shows:**
- The cockpit is dark navy gunmetal.
- Metal edges catch cool blue-white highlights in thin streaks along the bevels.
- There are blue LED pods on the pillars.
- The screen corners are cut off by the frame: top-left at about (0,0) to (50,100), and the bottom corners at about (0,1400) to (100,1512).
- Plain bright silver would look pasted on. It needs to be **cool chrome**, a silver with a slight blue tint. Its darkest tone should match the navy of the art and its brightest the blue-white highlights, so it looks lit by the same light.

**Shape reference:** the Rainmeter visor corners in `@Resources/Images/corners.png`.
- The top corners are curved cuts, from about x 0-95 down to y ~270.
- The bottom corners are stepped chamfers, about 215 px wide over y 1290-1600.

**Approach (reuses code that already exists):**
1. Add a new `CornerPieces` layer. It sits beside `PictureTrim.tsx` and draws only when picture mode is **fitted**. It uses the same seat maths as `pictureSlots.ts`, so the corners line up with the art's cut-outs at any screen size.
2. Draw it as SVG, one path per corner, with these layers:
   - A linear gradient made of 5 to 7 stops for the chrome look: dark, mid, bright band, mid, dark. Its angle follows the light direction in ship.png, roughly from the top-left.
   - A brushed-metal texture from `feTurbulence` stretched along one axis, used once as a pattern and kept out of the animation path.
   - A thin, nearly white edge line on the side that faces the light, and a dark edge line on the far side.
   - Small details: 2 or 3 rivets or panel seams per piece, copied from the groove style in `corners.png`.
   - A glow. The edge that faces the screen gets a soft blur in the HUD accent colour, the same accent `PictureTrim` uses. It is drawn into a cached layer, so there is no live blur on every frame.
3. Add settings: `CornerPieces` on/off, glow strength, and a tint between silver and the accent colour. The default is on, but only in fitted mode.

**Done when:**
- The pieces line up with the art's corners at 1920x1080, 2560x1600 and 3840x2160 (screenshots).
- They do not cover any HUD hit areas.
- They do not appear in other picture modes.
- Idle CPU and GPU stay within 1 percentage point of the baseline.

**Checks:**
- A vitest geometry test for the corner positions against the seat.
- Screenshot review.
- A before-and-after perf measurement.

**Risks:**
- An SVG filter can be expensive on a full-screen transparent WebView. Cache it as an image (a one-time render to a canvas, then a data URL) if the measurement shows a cost.

**Rollback:** set the setting to off, or revert the commit.

---

## C. Host and UI

### C1. Remove the flicker when the app first shows (an unusual workaround)

**What the last attempt did (2026-11-08, snapshot in `publish/snapshot-before-revert-20261108/`):**
- It changed three things at once:
  - Chromium flags (`--disable-features=CalculateNativeWinOcclusion` and others).
  - GPU counters in the background.
  - A deferred show.
- `gpuprefs.reg` also forced the GPU preference for Rainmeter, CSpace and msedgewebview2.
- The deferred show and the 4 s showGuard are still in the code today. The flags and the GPU counters were removed.
- **My strong suspicion is that the flags or the GPU preference caused the breakage, not the deferred show.** This is not proven.

**What you saw on 11-08:** everything froze. The same change also made the HUD keep running and animating when something on the taskbar was clicked. Those flags are the most likely cause of the freeze:
- `--disable-backgrounding-occluded-windows`
- `--disable-renderer-backgrounding`
- `--disable-background-timer-throttling`
- `--disable-features=CalculateNativeWinOcclusion`

Two more things went in alongside them: GPU counters polled in the background, and `gpuprefs.reg`. Together they make the renderer draw full-screen at full rate all the time, with nothing slowing it down. That likely ties up the GPU and the shell.

So C1 is split into two separate problems, each fixed on its own.

**C1a. The flicker: show a picture first.** It needs no Chromium flags and no GPU registry changes.
1. When the HUD closes, and every few minutes while it runs, the host saves the current frame as `Data/lastframe.png` (WebView2 `CapturePreviewAsync`).
2. At the next start, the window first paints that image itself, as a WinForms background or a DirectComposition visual underneath the WebView. The window is then shown normally and really visible, so Chromium does not throttle anything.
3. The page posts `{type:'ui.painted'}` after its first real frame (two `requestAnimationFrame` calls after mount). Then the WebView fades in over the image, which is identical or nearly so, and the image is released.
4. If there is no image (first run, or a different screen size), the host does what it does today. The 4 s showGuard stays.

- **Rejected idea:** cloaking the window with DWM until it has painted. Chromium's occlusion check probably treats a cloaked window as hidden and stops drawing, which would leave it waiting forever. I'd only try it with a timeout, and only if C1a falls short.
- **Done when:** a 240 fps screen recording of 10 cold starts shows no blank, white or black frame, and hover, click-through and tray still work.

**C1b. Keep animating while the taskbar has focus (this is what froze last time).**
1. First, add a **freeze watchdog**. The page sends a heartbeat every second. If it misses 5 s, the host logs the freeze and reloads the page instead of hanging. If it misses 15 s, the host restarts the WebView. This goes in before any flag experiment, so another freeze recovers by itself.
2. Look for a fix with no flags first:
   - `ApplyVisibility` or the visibility policy may treat the taskbar (`Shell_TrayWnd`) as something covering the HUD. If so, add a rule that taskbar focus leaves the HUD visible and drawing.
   - Also set `CoreWebView2Controller.IsVisible = true` explicitly when that happens. Check the WebView2 docs through Context7 first.
3. Only if that fails, try **one flag at a time**, starting with `CalculateNativeWinOcclusion` alone:
   - Measure GPU and CPU for 10 minutes and watch the watchdog.
   - Never use the three backgrounding flags together. Never use `gpuprefs.reg`.
   - Cap the frame rate while the taskbar has focus (for example 30 fps), so "keep animating" never means "draw as fast as possible".

**Steps to keep it from breaking things:**
- One change per commit, each behind a setting (`HostSnapshotShow`, `HostAnimateOnTaskbar`).
- A live test needs your yes, because it restarts the HUD.
- Before the live test, you get a one-line way to undo it: turn the setting off in the tray, or delete the setting.

**Rollback:** turn the setting off, or revert the commit.

### C2. Show at startup and after unlock

**Startup:**
- `AutoStart.cs` already uses the HKCU Run key with `--autostart`. It needs no admin rights. Today it is opt-in from the tray.
- **You chose: on by default.**
  - On first run, the host enables the Run key unless you have explicitly turned it off. A `HostAutoStartOff=1` marker records that choice, so the app never switches itself back on after you disable it.
  - The settings panel gets a "Start with Windows" switch next to `JarvisAutoStart`.
- To make it appear faster, measure the time from logon to the HUD showing first, then decide. The Run key starts the app late in logon. A scheduled task at logon is faster but heavier, and needs your approval.

**Unlock:**
- `SessionSwitch` already sets `_locked` and calls `ApplyVisibility()`.
- Plan: on `SessionUnlock`, tell the page `session.unlock` so it can replay its intro later.
- Check that the window really comes back after Win+L, after sleep and resume, and after a remote session reconnects. `SessionUnlock` might not fire after resume from hibernate, so also listen for `PowerModeChanged`.

**Notes only, do not build yet: the door animation**
- Sequence: unlock, then the doors open (two blast-door halves slide out from the centre, about 900 ms, with sound), then the existing boot sequence.
- Hook: the page shows a `DoorIntro` overlay when it gets `session.unlock`, then hands over to `BootModule`.
- It needs the C1 cloak, so the doors are the first frame you see.
- Add a setting to skip it. Respect reduced motion.

### C3. Drag panels by the top strip, and resize the chat from its corners

- **The model is Chrome tabs.** There is no drag code in the HUD today. What Chrome does:
  - Press on the top strip and the panel lifts: a slight scale-up and a stronger glow.
  - It follows the cursor directly, with no lag.
  - Other panels in the same row **slide aside smoothly** (about 150 ms) to show where it will land.
  - On release it settles into the gap, or into a free spot.
  - Pressing Esc while dragging sends it back where it was.
- Plan:
  - Add one shared `useDragHandle` hook built on pointer capture. It handles pointerdown, pointermove and pointerup on a panel's top strip, about 36 px high.
  - A small move (under 4 px) still counts as a click, so the buttons in the strip keep working.
  - Layout is kept as an order of panels within each zone (left, right, bottom), plus an optional free offset. Moving a panel reorders that zone, like tabs in a strip. The other panels animate with a CSS transform.
  - Positions are saved per panel through the settings store, so they survive restarts.
  - The host needs no change, as long as the hit areas move with the panel. Check `regionsOf`, so click-through follows the panel.
- **Chat panel resize:**
  - `JarvisModule` draws a fixed 1200x616 SVG (`JarvisModule.tsx:104`).
  - Add corner handles of 16 px that change `W` and `H` within set minimum and maximum sizes, and reflow the log lines.
  - Save the size.
- Add "Reset layout" to the tray and settings.

**Done when:**
- You can drag any panel and resize the chat, and both survive a restart.
- Click-through still works everywhere else.

**Checks:**
- vitest for the snap and clamp maths.
- The e2e frame spec.

**Rollback:** revert the commit, and "Reset layout" clears the saved offsets.

---

## D. JARVIS fixes only

### D1. Long speech dismissed as room talk

- **Cause:** `jarvis.py:742` `room_talk()` drops anything of 25 words or more that has no "?", no "you" and neither name. Talking at length to JARVIS triggers it.
- **Fix:**
  - Treat speech as room talk only with **positive evidence**: other voices or a turn change, speech not aimed at him right after a wake, or a third-person mention such as "he" or "him" referring to JARVIS.
  - **Never** treat it as room talk inside an open follow-up window, or right after a wake word.
  - Raise the length to 60 or more words and log every drop with a `room?` tag, so we can tune it from real logs.
- **Done when:**
  - Your long monologues in the replay bank get answers.
  - Real room talk recorded in `tests` still gets dropped.
  - Both are added to the goldens.

### D2. Wake works about 1 in 4 times; the old version was better

**Likely causes, the commits that made it stricter:**
- `4061766`: stricter default for slice G.
- `2ded86c`: the HV check needs a plain score of 0.3 or more.
- `9ee8f5e`, `bae539b`, `bdfb8fb`, `34fdeb3`, `7f1f18e`.
- The rule that needs 2 scores in a row (`held`).
- The VAD gate at 0.5 on `prediction_buffer[-7:-4]`.
- The check that the transcript contains his name.

**Plan, measure first:**
1. Record a test set of about 30 "Hey Jarvis" from you, at desk distance and across the room, plus about 30 minutes of normal room audio, as wav files under `tests/wake_bank/`.
2. Write an offline scorer that runs the current `wake_way` and the old setup from before the stricter commits (around `da8e8ec`) over the same audio. It reports hits and false wakes for each.
3. Choose with numbers. The likely result is to bring back the single-moment rule above the old threshold, lower or remove the HV floor, and only *log* the name-check result instead of blocking on it.
4. Keep the near-miss logging (`NEAR_FLOOR=0.15`) for live tuning.

- **Done when:** at least 90% of wakes are caught at desk distance, with at most 1 false wake per hour of room audio.

### D3. Ultron mode (panel and button)

**What exists:**
- The pi coding agent, with these extensions in `~/.pi/agent/extensions`:
  - `destroy.ts` for `/destroy [n|all]`.
  - `loop.ts` for `/loop`.
  - `background.ts` for `/jobs` and the bash_background, bash_output and bash_kill tools.
  - `safety.ts`.
- A llama.cpp server running the Cyber-Tiel-Coder-35B model, per `~/.pi/ultron-server.log`.

- `ultron` is your PowerShell command: it starts the llama server and opens pi. It is set up already. **We use it exactly as it is: no new models and no changes to pi.**

**Plan:**
1. Add an ULTRON button and section in the HUD next to JARVIS. It opens an `UltronModule` panel styled like the chat log: the same frame kit, a red/amber theme, and the same resize and drag from C3.
2. The host runs **your existing `ultron` command**, via `pwsh -NoLogo -Command ultron`, inside a hidden pseudo-console (ConPTY). The panel shows pi's output and sends what you type back.
   - ConPTY works with any program that runs in a terminal, so `ultron` stays untouched.
   - If the pi docs (checked via Context7) show a JSON/RPC mode that `ultron` could pass through, that gives a cleaner chat view. That is optional, and it would need a small change to `ultron`, which needs your OK.
   - Closing the panel leaves Ultron running. **Stop** ends pi and the server cleanly, and HUD exit asks first.
   - **What `ultron` does** (from the definition you pasted, 2026-11-22):
     - It checks `http://127.0.0.1:9931/props`.
     - If the server is running with too small a context, it restarts it, but only if the process is llama.cpp.
     - Otherwise it starts a hidden `llama-server`: `-hf peculiar-ragdoll/Cyber-Tiel-Coder-35B-A3B-GGUF:UD-IQ4_XS --offline --host 127.0.0.1 --port 9931`, with a 64k context and `--n-cpu-moe 22`.
     - It waits up to 5 min for `/health`.
     - Then it runs `pi --provider llama-cpp --model <model> @args`.
   - **What that means for the panel:**
     - pi is an interactive terminal app, so ConPTY is the right choice.
     - The panel's status light can read `/health` and `/props` on port 9931, with no need to parse the terminal.
     - "Kill server" stops only the llama process listening on port 9931, using the same safety check `ultron` uses.
     - Loading takes up to a minute, so the panel shows "loading model" until `/health` returns 200.
   - The server is bound to 127.0.0.1, which is good. But with no `--api-key`, and CORS allowing every origin, any web page open in your browser can still send it requests. Recommended: add `--api-key` to `ultron` and the same key to pi's models.json. That is your change to make; I won't touch either file.
3. Buttons:
   - **Stop** interrupts the current pi turn.
   - **Jobs** runs `/jobs`.
   - **Loop** runs `/loop`.
   - **Destroy** runs `/destroy`, with confirmation in the panel. pi's own confirmation is still the real gate, so a click in the HUD alone never deletes anything.
   - **Kill server** stops llama-server.
4. **Security:**
   - The llama server warns: "no API key is set and CORS allows all origins". Bind it to 127.0.0.1 and set `--api-key`, otherwise any web page you visit can call it.
   - `GOD-MODE-plan.md` says the GodMode ultron slot is chat only. The pi version **does** have tools, so keep `safety.ts` on and make no auto-approval from the HUD.
- **Non-goals:** changing how pi behaves, downloading or switching models, or editing `ultron`.

---

## E. Rebuild JARVIS on proven open-source parts (the largest phase). Planning only for now.

**Idea:** stop writing our own versions of solved problems. Keep the **personality** and swap the plumbing for well-tested patterns:
- what to keep: `reply/`, `mood.py`, the persona text in `prompt.py`, `voice/fillers.py`, `voice/pacing.py`;
- what to take from elsewhere: the proven pattern from a reference project, ported or pulled in.

**Rules for this phase:**
- **No new AI models** without a separate yes from you. That includes Ollama pulls, Hugging Face weights and new wake models.
- Everything below runs on the models already installed:
  - Ollama: qwen3:4b-instruct, llama3.1:8b, llama3.2:3b, phi4-mini, nomic-embed-text.
  - faster-whisper, Kokoro and Piper, which are already used in `hearing.py` and `voice/synth.py`.
  - The openWakeWord models.
- This builds on `PLAN-jarvis-from-openjarvis-2026-11-05.md` and its file index, which are reused, not repeated.
- The Gemini deep-research results pick the exact projects to copy. The parts below are named by pattern, and the candidates are the ones to verify.

**What is wrong today, by area:**
- `jarvis.py` is 1726 lines, and `exchange()` is one big function with stages 6d-6f.
- `routing.py` is 861 lines of regex rules, where the rule order decides the meaning.
- Wake, room-talk and follow-up are stacked filters that each veto a turn and are tuned by hand.
- There is no explicit conversation state, so "make it 50" has to guess.

**The target architecture (as in Pipecat or LiveKit Agents):**
```
mic frames -> VAD -> wake / follow-up gate -> streaming STT (faster-whisper)
   -> turn-end detector -> Understanding (fast-path rules + LLM tool call) -> Dialogue state
   -> Action gate (schema check -> policy -> confirm) -> executor -> reply composer (personality) -> TTS (Kokoro/Piper) -> speaker
   barge-in (you start talking) cancels everything downstream
```

### E0. Foundation (before any swap)
1. **An event pipeline.** Split `exchange()` into stages that pass typed frames, as Pipecat's processors do: `AudioFrame`, `SpeechStarted`, `Transcript(partial/final)`, `TurnEnded`, `Intent`, `ActionResult`, `ReplyText`, `ReplyAudio` and `Cancel`.
   - At first each stage wraps the existing code with no change in behaviour, so the goldens stay byte-for-byte the same.
   - Files: a new `jarvislib/pipeline.py`; `jarvis.py` gets much smaller.
2. **Tracing.** Every turn gets an id and a timestamp for each stage, written to `Data/jarvis_trace.jsonl`, which git ignores.
   - It records: wake score, VAD, STT text and confidence, each gate's decision with the reason, the intent, the action, and latency per stage.
   - All tuning after this point is based on these numbers.
3. **A replay bank built from real audio.** `tests/wake_bank/`, plus your logged misses, replayed offline through the whole pipeline. This becomes the test for everything else in E.

### E1. Listening: wake, voice detection, room talk, follow-up
- Replace the stacked vetoes (the two-moments-in-a-row rule, the HV floor, the name check, `room_talk`, the follow-up window) with **one scoring decision**: wake score + transcript name match + direction cues + follow-up context, compared to one threshold.
  - This is the "multi-signal endpointing" pattern from the LiveKit turn detector and Picovoice.
  - Each signal is logged, so a miss shows *which* signal lost.
- Wake rules come from the D2 measurements. Room talk needs positive evidence (D1).
- Follow-up: after JARVIS speaks, keep the mic open for N seconds with no wake word needed, the way Alexa and Home Assistant Assist handle follow-ups.
- **Barge-in:** speech during TTS stops playback and starts a new turn, as in Pipecat's interruption handling.

### E2. Hearing: speech to text
- Stream faster-whisper with partial results and word timestamps, following whisper_streaming / WhisperLive. This allows an early intent guess and a faster first reply.
- Add an end-of-turn check: a pause together with "this sentence looks finished" (a check on the transcript text), instead of a fixed silence timer.
- Pass a hotword prompt (`initial_prompt` with "Jarvis", app names, your contacts) to cut mishearings, so that sound-alike fixes like "time her" are no longer needed.

### E3. Understanding: routing becomes tool calling
- **Two-tier router:**
  1. A **fast path** of deterministic rules, kept for the top ~20 commands where speed and exactness matter: volume, timers, stop, mute, brightness and similar. These are the existing rules, trimmed down.
  2. Anything else goes to an **LLM tool call** on qwen3:4b-instruct (already installed, supports tools). It uses a JSON schema for each tool, built from the registry in `actions.py`.
- **Dialogue state** (`jarvislib/state.py`), as in Rasa slots or Home Assistant Assist's context:
  - It tracks the current topic, such as the timer, the volume or a note, plus the last thing acted on, its value and when.
  - "make it 50", "louder", "cancel that", "the other one" are resolved against it. This replaces the guessing in A11.
- If the model returns invalid JSON or an unknown tool, JARVIS asks you instead of guessing.
- Validation: the goldens become "what was understood" (intent + arguments), with any intended diffs approved by you one batch at a time.

### E4. Acting: the action gate
- Every action takes this path: the tool and its arguments are checked against the schema, then a **policy** check (allow, confirm or deny, by tool and argument), then the executor. The result goes back into the dialogue state.
- **The model never authorizes an action on its own.** Dangerous actions (delete, close windows, shutdown, sleep, anything in the recycle bin) always need confirmation from you, by voice or a click. The confirmation is matched to the exact pending action.
  - This is the pattern from Claude Code's permissions, the OpenAI Agents SDK guardrails and Open Interpreter's approval step.
- The regex in `confirm.py` becomes one input to the policy, not the gate itself.
- Tests: fake executors, plus the tripwires that already exist in `golden_common`.

### E5. Memory
- Short term: the last N turns plus the dialogue state.
- Long term: facts and notes embedded with **nomic-embed-text, which is already installed**, kept in a local store (sqlite + numpy, or the existing `notes_index`). Retrieval happens only when a turn asks for it.
  - Pattern: mem0 / Letta "memory blocks".
- You can see what is stored, and "forget X" deletes it.

### E6. Speaking
- Keep Kokoro and Piper.
- Stream the reply: send the first sentence to TTS while the LLM is still writing. `voice/chunker.py` already does part of this.
- Measure the time from the end of your speech to the first sound, with a target under 1.2 s for a fast-path command.

### E7. Clean up
- Remove the code each swap replaced: old gates, unused regex, dead branches such as A5.
- Keep `diag.py` and the doctor tool, rewired to read the trace.

**Order:** E0, E1 (fixes the biggest pain: wake and being ignored), E3, E4, E2, E6, E5, E7.

**For each step:**
- Done when: there is a measured gain on the replay bank, `replies.jsonl` shows no personality regression, and the gate is green.
- Validation: the replay bank, the goldens, latency from the trace, CPU and RAM before and after.
- Risks:
  - Tool calling on a 4B model can be flaky. The fast path and the ask-back on invalid output keep it safe.
  - The pipeline split touches everything. E0 changes no behaviour and is checked byte-for-byte.
- Rollback: one branch per step, and the old path stays selectable by a setting until the new one has been through your live test.
- Licences: only MIT, Apache or BSD code gets copied in, and it keeps its licence header.

---

## F. Stage 2: vision, control, avatar

- **Screen vision:**
  - The user triggers it ("look at my screen"). A capture is taken with Windows.Graphics.Capture in the host.
  - **No vision model is installed.** Using one means a download, which needs your yes. The "find what's free" survey proposes one first.
  - Until then, the cheaper path is UI Automation text, which needs no model and is often enough: window titles, focused control, selected text.
  - Nothing is kept unless you say so, and capture always shows a visible indicator.
- **Window and tab control:**
  - Use UI Automation and Win32 (move, snap, focus, close a tab with Ctrl+W through UIA) as tools behind the E4 action gate.
  - Each action is listed and checked. Destructive ones need confirmation, and model output alone never runs an action.
- **On-screen avatar:**
  - A small, separate transparent click-through host window, or a layer of the HUD, that drifts with spring physics, reacts to listening, thinking and speaking, and follows the cursor gently.
  - Right-click opens a popup panel with mute, type, Ultron, hide, settings, and "look at screen".
  - It reuses the orb art and filters from `JarvisModule`.
  - The commands "hide yourself" and "come back" toggle it.
  - Perf budget: at most 1% CPU idle, a capped frame rate when it is still, and it pauses when hidden.
- **"Find what's free":**
  - A short survey document comparing licences, VRAM and quality for free local tools.
  - It is done before F is built.
  - Downloads only after you approve.

---


## Research adopted (Gemini deep research, 2026-11-22)

Source: `Local Voice Assistant Architecture Research.docx` (Downloads). Only MIT, Apache-2.0 or BSD code is copied, with its licence header kept. Claims in it were checked against this repo where possible; unchecked claims are marked.

| Plan step | What we take | From (licence) |
|---|---|---|
| D2 / E1 wake | One gate: feed exact 1280-sample int16 chunks at 16 kHz, openWakeWord's own `vad_threshold=0.5`, one-frame threshold near 0.25 plus a cooldown, a pre-roll ring buffer so the first word is not cut. Drop the transcript name veto. Tune offline with `openwakeword.utils.bulk_predict` on the replay bank (false accepts per hour, recall). Issue #350: 0.5 caught 48% of wakes, 0.25 caught 83%. | openWakeWord (Apache-2.0 code; the `hey_jarvis` weights are CC BY-NC-SA, fine for personal use) |
| D1 room talk | Remove the 25-word filter for wake-started turns. Room-talk check only in follow-up mode: qwen3 with `think=False` and a one-boolean JSON schema, plus exit phrases ("never mind", "not you"). | pattern only |
| E0 pipeline | Typed frames: system frames (cancel, interruption) jump the queue, data frames keep order. A per-stage watchdog. Per-stage latency spans like Pipecat's `UserBotLatencyObserver`. | Pipecat `frames.py`, `task.py` (BSD-2) |
| E2 hearing | Streaming policy from `whisper_online.py` (`OnlineASRProcessor`) ported onto faster-whisper; sliding-window segment confirmation from WhisperLive. Settings: `int8`, `beam_size=1`, `temperature=0`, `condition_on_previous_text=False`, `cpu_threads<=4`, a warm-up clip. Test `hotwords` vs `initial_prompt` on the replay bank (research says `initial_prompt` can cause name hallucinations). | ufal/whisper_streaming, collabora/WhisperLive (MIT) |
| E3 understanding | Tier 1: hassil-style templates with `requires_context` ("make it 50" only matches when the topic is a timer or volume). Tier 2: semantic-router over **nomic-embed-text** with a top-1 vs top-2 margin. Tier 3: Ollama native `/api/chat` with a JSON schema in `format`, `temperature=0`, `think=False`. Dialogue state as an event log of slot sets (Rasa tracker idea, under 100 lines). | hassil (Apache-2.0), semantic-router (MIT), Rasa (pattern) |
| E4 action gate | Order: deny tools / deny argument patterns, then confirm tools, then allow tools with bounds checks, else fail closed to confirm. One pending action, bound to a sha256 of its exact arguments, with a TTL; consumed once; the policy is re-checked after approval. Only a HUD click or a deterministic voice "yes" can approve; the LLM can never call approve. | OpenHands `confirmation_policy.py`, OpenAI Agents SDK `needs_approval` (MIT) |
| E5 memory | One SQLite file: numpy cosine over float32 blobs (under ~10k facts) plus FTS5, merged by reciprocal rank fusion; retrieval only when the turn refers to the past. A tiny pinned core-facts list in the static prompt. Not mem0 (an extra LLM call per turn). | sqlite-vec (MIT) optional; pattern |
| E6 speaking | Start TTS on the first stable clause (`stream2sentence` settings `quick_yield_single_sentence_fragment`, `minimum_first_fragment_length`). On barge-in, flush the resampler so old audio does not leak into the next reply (pipecat#6806). | stream2sentence (Apache-2.0), RealtimeTTS (MIT) |
| Latency | Keep the system prompt byte-identical across turns so Ollama reuses its cache; always send `keep_alive` (one request without it resets the timer to 5 min). Never use `/v1/chat/completions` (drops `keep_alive` and `think`). | ollama issues #5272, #9577 |
| F stage 2 | UI Automation first, vision only as a fallback (UFO²). pywinauto (BSD-3) for windows and tabs; Windows-MCP (MIT) as the reference for consent countdown and takeover hotkey. Avatar as a separate small WPF layered window, not a click-through WebView2. | UFO (MIT), Windows-MCP (MIT), pywinauto (BSD-3) |

**Checked against this repo today:**
- `llm.py` already uses native `/api/chat` and `/api/generate` and sends `keep_alive` on each call. Good.
- `hearing.py:31` already uses `int8` and `cpu_threads()`. `hearing.py:144` passes both `hotwords` and `initial_prompt` with `vad_filter=True`. E2 tests which helps.
- `JarvisPipe.cs:39` already uses `PipeOptions.Asynchronous`, so the named-pipe deadlock in the research does not apply.
- Only `onnxruntime-gpu` 1.23.2 is installed (not both), as the research advises.
- `av` 19.0.1 is installed with faster-whisper 1.2.1. The research says that pair fails when faster-whisper decodes a file. JARVIS passes numpy audio, so it is probably not hit; E0 adds a test that decodes a wav through `decode_audio` to confirm. **Not yet verified.**
- Research says `vad_filter=True` zeroes the last 64 samples of the buffer in place (#1688). E2 checks whether any buffer is reused after transcribe. **Not yet verified.**

**Needs your yes (new models, nothing downloaded):**
- Pipecat Smart Turn v3.2 (BSD-2, 8 MB int8 ONNX): an end-of-turn detector for long pauses. Recommended by the research; it would replace the fixed silence timer in E2.
- Silero VAD v6 (MIT, about 2 MB): only if the bundled one is older. Check first which version openWakeWord ships.
- OmniParser v2 (1.4 GB): stage 2 only, and only if UI Automation is not enough. Not recommended now.
- Skip: the LiveKit turn detector (its licence forbids use outside LiveKit), Open Interpreter 01 (AGPL).

**Licensing note:** piper is GPL (piper1-gpl). Keep it as a separate process or keep Kokoro as the main voice, and copy none of its code.

## Order and gates

A, then B, then C1, then C2, then C3, then D1, then D2, then D3, then E (the most time), then F.

Each phase ends with:
- the full gate,
- a perf comparison for B, C and F,
- your live test.

Nothing is deployed until you say so.

## Answers so far (2026-11-22)

- **Ultron:** it is your `ultron` PowerShell command; use it as it is. I still need its definition pasted.
- **Dragging:** like Chrome tabs.
- **New models:** none.
- **Autostart:** on by default.
- **11-08:** it froze. It is tied to the keep-animating-on-taskbar change.
- **A11:** use the context.
- **Routes:** approved and regenerated.
- **Review branch:** `review/cspace-code`, code-only.

## Still open
1. Paste the output of `(Get-Command ultron).Definition`, so the panel launches it correctly.
2. D2: roughly when the old, better wake setup was in use. If you don't know, I'll compare against the setup from before `4061766`.
