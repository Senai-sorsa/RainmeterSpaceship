# Comprehensive Repository Audit, Comparable Assistant Complaint Analysis & Master Fix Plan (`RainmeterSpaceship` / JARVIS)

## Executive Summary & Validation Baseline

This master report presents a full-repository forensic audit of `RainmeterSpaceship` (`chore/jarvis-baseline-and-performance`, 26,825 lines across Python, Lua, C#, PowerShell, and Rainmeter `.ini`/`.inc` skin configurations), covering:
1. **Phases 7, 8, and 9** of `JARVIS-Repair-Plan.txt` (`BUG-P7-01`..`08`, `BUG-P8-01`..`05`, `BUG-P9-01`..`05`).
2. **AI Industry Benchmark Edge-Case Testing** (`BUG-EDGE-01`..`07`), drawing on evaluation methodologies from the [Berkeley Function-Calling Leaderboard (BFCL)](https://www.google.com/search?q=https%3A%2F%2Fwww.emergentmind.com%2Ftopics%2Fberkeley-function-calling-benchmark-bfcl), [Apple ToolSandbox](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2408.04682), [Sierra τ-bench](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2406.12045), [Apple Spoken Language Understanding (SLU) Disfluency Research](https://www.google.com/search?q=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F370156965_From_User_Perceptions_to_Technical_Improvement_Enabling_People_Who_Stutter_to_Better_Use_Speech_Recognition), and [OpenAI Instruction Hierarchy](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2404.13208).
3. **Comparable Voice Assistant & Model Complaint Audit** (`BUG-COMP-01`..`07` + Guarded Feature Matrix), auditing customer and developer complaints across voice assistants that share JARVIS's exact components ([openWakeWord](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fdscripka%2FopenWakeWord%2Fblob%2Fmain%2Fdocs%2Fmodels%2Fhey_jarvis.md), [faster-whisper](https://www.google.com/search?q=https%3A%2F%2Flocalaimaster.com%2Fblog%2Fwhisper-hallucination-fix), [RealtimeVoiceChat / RealtimeSTT + RealtimeTTS](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FKoljaB%2FRealtimeVoiceChat), [Open-LLM-VTuber](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FSnowfork%2FOpen-LLM-VTuber%2Fblob%2Faidan_fixes%2FREADME.md), [Home Assistant Assist + Ollama](https://www.google.com/search?q=https%3A%2F%2Fwww.home-assistant.io%2Fblog%2F2025%2F09%2F11%2Fai-in-home-assistant%2F), [OpenVoiceOS / Mycroft Alerts](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FOpenVoiceOS%2Fovos-skill-alerts), and consumer assistants [Amazon Alexa](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Falexa%2Fcomments%2F1h8gau9%2Fis_there_anyway_to_make_alexa_assume_the_nearest%2F), [Apple Siri](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2FSiri%2Fcomments%2F1wsewt6%2Fi_asked_siri_for_a_740_pm_alarm_four_different%2F), and [Google Assistant](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fgooglehome%2Fcomments%2F6uvbnj%2Fsetting_an_alarm_for_midday%2F)).
4. **Core Bugs, Repetitive Hardware Pipelines (7 Subsystems), Dead Code, Stale Skins, Test Infrastructure Gaps & HUD Scroll Audit** (`BUG-CORE-01`..`03`, `BUG-INFRA-01`, `BUG-SCROLL-01`..`03`).
5. **Complete Step-by-Step Fix Plan with Pseudocode** (`Fixes 1–29`), **Possible Recommendations (`REC-01`..`REC-05`)**, and **Architectural Recommendation (`Part 4`): WebView2 / Tauri v2 Migration & Intro Animation Blueprint for Lenovo Legion (`BLACK-CLOVER`)**.

### Automated Validation Baseline

| Validation Check | Command Executed | Outcome | Notes |
| :--- | :--- | :--- | :--- |
| **Python Bytecode Compilation** | `python3 -m py_compile` across all 41 `.py` files | **PASS (0 errors)** | All `Jarvis/*.py`, `jarvislib/*.py`, and `tools/*.py` compile cleanly |
| **HUD Geometry & Overlap Audit** | `python3 tools/check_layout.py` | **PASS (0 problems)** | Verified `35 zones, 6 decor, 0 problems` against 1920x1080 bounds |
| **Rainmeter Skin & Lua Wiring** | Static `.ini`, `.inc`, and `dofile()` path check | **PASS (0 broken paths)** | All `@Include` and `ScriptFile` references resolve; 2 Lua scripts and 1 PS1 script are dead code |
| **JARVIS Unit Test Suite** | `python3 test_jarvis.py` (3,569 lines) | **1 Date-Dependent Failure** | Fails at `test_jarvis.py:2449` on Fridays between 09:00 and 21:00; 100% pass once clock-pinned |
| **Phase 7–9 Targeted Bug Probes** | `python3 verify_phase7_to_9_bugs.py` | **Confirmed 22 Bugs / Glitches** | Reproduced all Phase 7–9 functional bugs, confirmation bypasses, and pipeline redundancies |
| **AI Benchmark Edge-Case Suite** | `python3 test_industry_edge_cases.py` | **Confirmed 7 Benchmark Bugs** | Reproduced SLU disfluency, multi-intent drop, negation inversion, and homophone bugs (`BUG-EDGE-01`..`07`) |
| **Comparable Assistant Complaint Suite** | `python3 test_similar_system_complaints.py` | **Confirmed 7 Shared-Stack Bugs + 5 Recs** | Reproduced noise-floor lock-in, TTS abbreviation splitting, named timer drop, OWW VAD persistence, and alarm ducking (`BUG-COMP-01`..`07`) |
| **HUD Scroll Edit Audit** | `rmsim.static_checks()` + Lua scroll inspection | **Confirmed 3 Scroll/Encoding Issues** | Reproduced `drawer.lua` unclamped overscroll in `focus` mode (`BUG-SCROLL-01`..`03`) |

### Master Index of All 39 Confirmed Bugs & 5 Architectural Recommendations

| ID | Category / Phase | Severity | File & Line Numbers | Summary of Issue |
| :--- | :--- | :--- | :--- | :--- |
| **BUG-P7-01** | Phase 7 (`7-0`..`7d`) | **High** | `jarvis.py:1070-1071`, `actions.py:320-355` | Confirmed `"ask"`-risk actions say `"Done."` instead of calling `done_line()`, bypassing Windows state read-back for `mic_mute`, `bluetooth_off`, `btlink`, `power`, `recycle`, and `micdev` |
| **BUG-P7-02** | Phase 7 (`7-0`, `7a`..`7c`) | **High** | `jarvislib/routing.py:206-219, 643-646` | Stale `UNBUILT_CAPS` still lists `"brightness"`, `"bluetooth"`, and `"microphone"`, causing natural phrasings (`"dim the screen to 40"`, `"toggle bluetooth"`, `"open microphone settings"`) to return `"I can't do that yet."` |
| **BUG-P7-03** | Phase 7 (`7a`, `7c`) | **Medium** | `jarvislib/routing.py:553-563, 571-580` | Brightness and microphone step regexes lack `"by N"` support (unlike volume), so `"increase brightness by 20"` and `"turn the mic up by 20"` hit `UNBUILT_CAPS` and fail |
| **BUG-P7-04** | Phase 7 (`7a` Undo) | **High** | `jarvis.py:220-227` | `undo_last()` for `mic_unmute` ignores `was_muted` (`before[0]`), unconditionally muting an already-unmuted microphone while falsely speaking `"Microphone unmuted."` |
| **BUG-P7-05** | Phase 7 (`7-A8` App Focus) | **High** | `jarvislib/actions.py:44-53, 370-377`, `routing.py:618-624` | `act_open()` fails to focus running apps when `.exe` path has uppercase letters (`Notepad.exe` vs lowercase `windows.txt`) or when display names are multi-word (`"Google Chrome"`, `"Visual Studio Code"`, `"Microsoft Edge"`); `close <MultiWordApp>` also fails |
| **BUG-P7-06** | Phase 7 (`7b` Bluetooth) | **High** | `jarvislib/routing.py:494-509`, `actions.py:209-227`, `jarvis.py:130` | `bt_devices()` compiles C# via PowerShell synchronously inside pure `route()`, is called up to 3x per turn (`directed` -> `route` -> `run_action`), and raises uncaught `subprocess.TimeoutExpired` |
| **BUG-P7-07** | Phase 7 (`7-A6` Stealth) | **Medium** | `jarvis.py:920, 1068-1071`, `routing.py:472-473` | Entering `stealth` mode by voice speaks `"Done."` out loud instead of in the pop-up (`1b-13`), opens a 10s follow-up ear in STEALTH, and lacks a voice refusal rule for `"exit stealth mode"` |
| **BUG-P7-08** | Phase 7 (`7-0`, `7c` Undo) | **Low** | `jarvis.py:130, 194-233`, `actions.py:88-101` | `undo_last()` for hardware/setting actions logs the reverse command in `did` instead of `did_add("undo")`, and undoing a theme change when Windows was in `"mixed"` mode fails with `"That didn't work."` |
| **BUG-P8-01** | Phase 8 (`8-A1`, `8d`, `9e`) | **High** | `jarvis.py:938-954, 1003, 1154, 1157` | Offer confirmations (`room`, `closing`, `fact`) only check `is_yes(text)` across a 33s window — bypassing `heard_score[0] >= -1.0`, channel matching (`typed_turn[0]`), and the 15s confirmation timeout |
| **BUG-P8-02** | Phase 8 (`8d` Typed `ASK`) | **High** | `jarvis.py:780-785, 1616-1623` | Typed `ASK` turns cannot confirm any `"ask"`-risk command (`ask_yes` immediately returns `False` and prints `"Cancelled."`), `busy.locked()` calls `reply_line()` on the main thread (corrupting active turns), and `turn()` hardcodes `tier=0` |
| **BUG-P8-03** | Phase 8 (`8a` Dim Standby) | **Medium** | `jarvislib/mic.py:171-174`, `Scripts/jarvis.lua:415` | `_listen()` sets `S.set(state="idle")` after `dim_after` (3s) while holding `busy` and recording until 10s; clicking the orb during seconds 3–10 sends `WAKE` (dropped) instead of waking/cancelling |
| **BUG-P8-04** | Phase 8 (`8-A3` / Slice D) | **Medium** | `jarvis.py:700-702, 874, 900, 936` | Command replies open a full 10s open-ear follow-up instead of Slice D's 5s undo/remove window; `ear_wait()` is evaluated twice and can shrink from 8s to 3s mid-turn if an `offer` expires during transcription |
| **BUG-P8-05** | Phase 8 (`8c` Quiet Class) | **Low** | `jarvislib/quiet.py:15-46`, `jarvis.py:977` | Saying `"you can talk"` outside a class event falls through to the LLM (`chat`) instead of giving a fixed reply; overlapping class events return the first regex match instead of the latest `end` time |
| **BUG-P9-01** | Phase 9 (`9-5` Protected) | **High** | `jarvislib/diag.py:192-200`, `routing.py:620`, `actions.py:382` | `is_protected()` omits `OWN_MODEL` (`python`, `pythonw`, `ollama`) and `shipcore`, allowing `"close python"`, `"kill ollama"`, or `"close shipcore"` to terminate JARVIS, Ollama, or `ShipCore.exe` |
| **BUG-P9-02** | Phase 9 (`9-2` `diag.ps1`) | **High** | `Jarvis/diag.ps1:22-37`, `jarvislib/diag.py:153-165` | `diag.ps1` keys `$by` by `$x.InstanceName` (which omits `#1`, `#2` in PowerShell `Get-Counter`), overwriting multi-process PIDs/metrics and breaking per-app GPU attribution in `gpu_apps()` |
| **BUG-P9-03** | Phase 9 (`9-3` Boot Logs) | **Medium** | `jarvislib/diag.py:345-348, 374-380` | `diagnose(..., span="boot")` runs `snapshot("logs", 720)` twice (spawning two sequential PowerShell `Get-WinEvent` processes) because `gather()` discards raw event timestamps |
| **BUG-P9-04** | Phase 9 (`9-7` Silent Watch) | **Medium** | `jarvislib/diag.py:455-498` | `watch()` `name_it()` always runs `gather("cpu", 24, False)` (spawning a 3.5s PowerShell counter sample) even when the trip was disk space or temperature, and drops ctypes findings if PowerShell fails |
| **BUG-P9-05** | Phase 9 (`9-4` Summary) | **Low** | `jarvislib/diag.py:263-269` | `summary(snap)` reports `"disk fine"` whenever `snap.get("disks")` is non-empty without checking whether any disk violates free-space thresholds |
| **BUG-EDGE-01** | AI Benchmark (Apple SLU) | **High** | `jarvislib/routing.py:658-669`, `reminders.py:65-72` | Mid-utterance self-repair (`"set volume to 40 no wait 60"`, `"set a timer for 10 minutes actually 5 minutes"`) executes the **aborted first number** (`40`, `10 min`) instead of the corrected target |
| **BUG-EDGE-02** | AI Benchmark (BFCL Multi) | **High** | `jarvislib/routing.py:663-678` | `understand()` only splits compound `"and"` commands when the **entire** string fails `route()`; if any regex swallows `"and ..."` (`"set a timer for 5 minutes and mute"`, `"add milk to my todo list and open calculator"`), the second action is silently dropped or corrupted |
| **BUG-EDGE-03** | AI Benchmark (BFCL Negation) | **High** | `jarvislib/routing.py:25-33, 661`, `jarvis.py:772-799` | `clean_cmd()` strips `"please"` before `DONT_DO` checks (`"just don't lock my computer"` bypasses `DONT_DO` -> `fix_route` strips `"don't"` and **locks PC**!); in `ask_yes()`, `"yes don't do it"` / `"sure never mind"` evaluates `is_yes() == True` and executes destructive actions |
| **BUG-EDGE-04** | AI Benchmark (ToolSandbox) | **High** | `jarvislib/reminders.py:49-108` | Out-of-bounds calendar dates (`"remind me on February 30 at 9am to pay rent"`) raise uncaught `ValueError: day is out of range for month` inside `reminders.when()`, crashing the turn thread |
| **BUG-EDGE-05** | AI Benchmark (τ-bench) | **Medium** | `jarvislib/routing.py:553-609`, `reminders.py:65-72` | Relative adjustment phrases (`"increase volume from 30 to 50"`, `"change brightness from 80 to 40"`) lock onto the **first** number (`30`, `80` — the current state!) instead of the target; `"half an hour"` / `"a quarter of an hour"` timers fail |
| **BUG-EDGE-06** | AI Benchmark (STT ASR) | **Medium** | `jarvislib/routing.py:25-44` | Common Whisper homophones (`"set volume to to"`, `"turn on blue tooth"`, `"screen shot"`, `"bright ness"`, `"un mute"`, `"fourty"`) fail rule routing |
| **BUG-EDGE-07** | AI Benchmark (BFCL Guard) | **Medium** | `jarvislib/routing.py:345-391` | `interpret()` (Stage-3 LLM JSON fallback) accepts hallucinated parameter values (e.g., `brightness=80` or `volume=50` when the user uttered **no number** in `"make it brighter"` / `"adjust the volume"`) |
| **BUG-COMP-01** | Shared Stack (`RealtimeSTT` / `SpeechRecognition` VAD) | **High** | `jarvislib/mic.py:150-161` | Adaptive noise floor (`floor`) initializes to frame 0's RMS (`floor = rms`) and updates even during speech; if the user speaks immediately after clicking or waking (`rms = 0.10`), `thresh` becomes `0.30` (`3 * rms`) and **drops the entire utterance as silence** |
| **BUG-COMP-02** | Shared Stack (`RealtimeTTS` / `Kokoro` Streaming) | **Medium** | `jarvislib/speech.py:153-163` | `sentences_from()` splits on any `[.!?]\s+`, breaking mid-sentence on titles and abbreviations (`"Mr."`, `"Mrs."`, `"Dr."`, `"St."`, `"vs."`, `"e.g."`, `"i.e."`) and causing unnatural TTS pauses |
| **BUG-COMP-03** | Shared Stack (`Alexa` / `OVOS` Named Timers) | **High** | `jarvislib/reminders.py:214-218` | Asking `"how much time is left on my <name> timer"` (`"pasta timer"`, `"laundry timer"`) or `"how much time is left"` fails the rigid regex in `reminders.py:214` and falls through to the LLM (`chat`), which hallucinates or denies having timers |
| **BUG-COMP-04** | Shared Stack (`openWakeWord` + Silero VAD `#219`) | **High** | `jarvis.py:1234, 1420, 1449, 1495` | `wake_loop()` calls `model.reset()` 3 times without clearing `model.vad.prediction_buffer` (unlike `speech_feats()` at line 1235), leaving stale `>0.5` Silero VAD scores that trigger false `barge == "voice"` or `heard_speech()` on the next frame |
| **BUG-COMP-05** | Shared Stack (`Alexa` / Smart Speaker Alarm Ducking) | **Medium** | `jarvis.py:521-530`, `jarvislib/mic.py:15-19, 184-199` | While an alarm rings (`alarm()` loop), `hear(patience=1.5)` calls `duck()` and `unduck()` every 2 seconds — pumping the master Windows volume between 30% and 100% and thrashing `Data\jarvis_duck.txt` |
| **BUG-COMP-06** | Shared Stack (`ChatGPT Memory` / `MemGPT` Drift) | **Medium** | `jarvis.py:311-325, 951-954`, `jarvislib/memory.py:114-129` | Accepting an auto-learned memory offer (`learnable()` -> `"Want me to remember that?"` -> `"yes"`) calls `memory_reply("save", fact)` directly, bypassing `fact_save()`'s `_fact_head` conflict check and storing contradictory facts (`"I live in Austin"` + `"I live in Chicago"`) |
| **BUG-COMP-07** | Shared Stack (`sounddevice` PortAudio Hot-Plug `#173`) | **Medium** | `jarvis.py:1572`, `jarvislib/mic.py:25-68` | `list_mics()` runs only once at daemon startup and PortAudio caches device tables at `Pa_Initialize()`, so USB/Bluetooth headsets connected after startup cannot be selected by `"use the headset microphone"` and stale indices raise `PortAudioError` |
| **BUG-CORE-01** | Core Reminders (`when()`) | **High** | `jarvislib/reminders.py:54-92`, `test_jarvis.py:2446-2451` | `"next <weekday>"` spoken on the same weekday before the target hour schedules for **today (0 days)** instead of **+7 days**; unpinned clock in `test_jarvis.py:2447` fails every Friday between 09:00 and 21:00 |
| **BUG-CORE-02** | Core Log Commands (`exchange`) | **Medium** | `jarvis.py:983-997` | `SHOW_LOG` / `HIDE_LOG` sets `way["kind"] = "log"` unconditionally before matching and returns early without `fixed()`, skipping `filler_done()`, `recent["me"]`, `history`, and follow-up listening |
| **BUG-CORE-03** | Core Prompt Safety (`INFO-01`) | **Medium** | `jarvislib/prompt.py:45-93` | `context()` injects untrusted calendar titles, to-do items, and note snippets directly into the `system` prompt without `<hud_data>` delimiters |
| **BUG-INFRA-01** | Pipelines, Skins & Test Infra | **Medium** | `actions.py`, `ShipCore.cs`, `Scripts/*.ps1`, `Settings.inc`, `test_jarvis.py` | 7 duplicated hardware pipelines across Python/PS1/C#; `Everywhere` test proxy misses `ACTION_TABLE` function references; dirty `Settings.inc`; unused `sphere.lua`, `storage.lua`, `location.ps1`, and 20 dead `[G1_1]`..`[I1_20]` meters |
| **BUG-SCROLL-01** | HUD Scroll Edit (`drawer.lua`) | **High** | `Scripts/drawer.lua:27-31, 40-41, 95-99, 115` | `build()` returns early at line 30 when `focus` is set (`"ALL INSTALLED APPS"` or a side-slot folder) before clamping `scroll <= maxScroll`, causing infinite overscroll into blank space, hidden hit boxes that block scrolling back up, and scrollbar thumb overflow (`frac > 1.0`) |
| **BUG-SCROLL-02** | HUD Scroll Edit (`rmsim.py`) | **Medium** | `Scripts/lib.lua:490`, `Scripts/target.lua:5, 35, 36` | Non-ASCII Unicode characters in Lua comments (`▸` on `lib.lua:490`, `📅`/`⏰` in `target.lua`) cause `tools/rmsim.py` (`lua_syntax_check`, line 873) to fail with 2 `encoding` errors |
| **BUG-SCROLL-03** | HUD Scroll Edit (`Bounds` / `Meters.inc`) | **Low** | `Scripts/drawer.lua:11-16`, `Overlay/Jarvis/Meters.inc` | `drawer.lua` lacks `Bounds` scroll actions (`Fill Color 0,0,0,1`), leaving dead scroll zones in the header, margins, and scrollbar track; `Overlay\Jarvis\Meters.inc` carries 40 unused image meters and 38 unused hit meters copied from `Drawer` |
| **REC-01** | Recommendation (`Alexa`/`Siri` Alarms) | **Advisory** | `jarvislib/reminders.py:54, 100-106` | Post-midnight (`00:00–03:59 AM`) `"set an alarm for 8 AM tomorrow"` schedules 31.5 hours ahead (next calendar day) instead of warning or clarifying upcoming morning vs. next day |
| **REC-02** | Recommendation (`faster-whisper` ASR) | **Advisory** | `jarvislib/hearing.py:13, 88-111` | Whisper `initial_prompt=HINT` echo on noise bursts and YouTube training hallucinations (`"Please subscribe"`, `"Amara.org"`) not covered by `PHANTOM` |
| **REC-03** | Recommendation (`RealtimeVoiceChat` EOU) | **Advisory** | `jarvislib/mic.py:134-170` | Static `JarvisSilence` endpointing cuts off users who pause after `"remind me to..."` while adding unnecessary latency after 1-word confirmations (`"yes"`, `"stop"`) |
| **REC-04** | Recommendation (`Home Assistant` + `Ollama`) | **Advisory** | `jarvislib/llm.py:66-132` | Switching between `JarvisModel` (8B) and `JarvisModelFast` (3B) when `PerfTier` changes leaves both models resident in VRAM (`keep_alive=10m`), risking VRAM exhaustion and CPU fallback |
| **REC-05** | Recommendation (Windows Core Audio) | **Advisory** | `jarvislib/mic.py:71-104`, `jarvislib/audio.py` | Master endpoint volume ducking (`IAudioEndpointVolume`) visibly shifts the Windows system volume slider; per-session `ISimpleAudioVolume` ducking avoids touching master volume |

## Part 1: Comprehensive Report on Everything That Needs to Be Fixed

### Section 1.1 — Phase 7 Bugs (`MORE SETTINGS BY VOICE`: `7-0`..`7e`, `7-A1`..`7-A10`)

#### BUG-P7-01 (High): Confirmed `"ask"`-Risk Actions Say `"Done."` Instead of Calling `done_line(action, target)`
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:1065-1071` and `jarvislib/actions.py:320-355`.
* **What happens**:
  In `actions.py:320-355`, `done_line(action, target)` implements dedicated read-back replies for Phase 7's `"ask"`-risk actions so JARVIS reports what Windows actually did (`JARVIS-Repair-Plan.txt` lines 3073–3074, 3108, and Live Tests `1b-3`, `1b-8`, `1b-9`, `1b-10`, `1b-14`, `1b-15`). However, in `jarvis.py:1070-1071`:
  ```python
  unsure = prompt.startswith("Did you say: ")    # then say what really happened, as an unasked command does
  fixed(("Added." if action == "todo" else done_line(action, target) if unsure or action == "sleep" else "Done.") if ok else "That didn't work.")
  ```
  Because `"micdev"`, `"bluetooth_off"`, `"btlink"`, `"power"`, `"recycle"`, and `"mic_mute"` all have `risk="ask"` with their own confirmation prompt (`"You want me to ... Confirm with yes."`), `unsure` (`prompt.startswith("Did you say: ")`) is always `False`! Consequently, `done_line(action, target)` is **never called** after the user says `"yes"` — JARVIS just says `"Done."`, rendering all 6 branches in `done_line()` dead code in normal turns.

#### BUG-P7-02 (High): Stale `UNBUILT_CAPS` Falsely Refuses Built Phase 7 Capabilities
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py:206-219, 643-646`.
* **What happens**:
  `UNBUILT_CAPS` at `routing.py:206-214` still lists `"brightness"`, `"bluetooth"`, and `"microphone"`. Any natural command phrasing for brightness, Bluetooth, or microphone that misses the rigid regexes at lines 475–580 (`"dim the screen to 40"`, `"change the brightness"`, `"toggle bluetooth"`, `"open microphone settings"`) matches `UNBUILT_CAPS` and returns `"I can't do that yet."`.

#### BUG-P7-03 (Medium): Brightness and Microphone Step Regexes Reject `"by N"` Step Amounts and `"dim/brighten to N"`
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py:551-580`.
* **What happens**:
  Unlike speaker volume (`routing.py:598-608`), brightness (`routing.py:558-561`) and microphone level (`routing.py:576-580`) only accept `{bit}$` (`"a bit"`, `"a little"`, `"slightly"`), rejecting `"by 20"` / `"by 20%"` and `"dim the screen to 40"`.

#### BUG-P7-04 (High): `undo_last()` Mutes an Already-Unmuted Microphone While Saying `"Microphone unmuted."`
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:220-227`.
* **What happens**:
  `undo_last()` for `mic_unmute` ignores `was_muted` (`before[0]`), unconditionally running `mic_mute` even if the microphone was already unmuted before `"unmute the microphone"`, while formatting the spoken confirmation from `was_muted` (`"Microphone unmuted."`).

#### BUG-P7-05 (High): `7-A8` (`act_open` Focus Running App) and `close <App>` Fail on MixedCase `.exe` Paths and Multi-Word App Names
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/actions.py:44-53, 370-377`, `jarvislib/routing.py:618-624`, and `Scripts/ShipCore.cs:219`.
* **What happens**:
  `ShipCore.cs:219` writes lowercase `.exe` names (`notepad.exe`, `code.exe`) to `Data\windows.txt`, whereas `act_open()` checks `os.path.basename(app[1]) in open_windows()` case-sensitively (`"Notepad.exe"` -> `False`). For multi-word Start Menu display names (`"Google Chrome"`, `"Microsoft Edge"`, `"Visual Studio Code"`), `running_window()` compares `"googlechrome"` against `"chrome"` using only `s == want`, `s.startswith(want)`, and `want in s`, which all fail when `want` is longer than `stem`.

#### BUG-P7-06 (High): Synchronous `bt_devices()` PowerShell C# Compilation Inside `route()` + Uncaught `TimeoutExpired`
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py:494-517`, `jarvislib/actions.py:209-227`, and `jarvis.py:130, 688`.
* **What happens**:
  `bt_devices()` spawns `powershell.exe` with `Add-Type` C# compilation synchronously inside `route()`, is called up to 3x per turn (`directed` -> `understand` -> `run_action`), and `except OSError:` misses `subprocess.TimeoutExpired`.

#### BUG-P7-07 (Medium): Voice Stealth Activation Speaks `"Done."` Out Loud and Opens a Follow-Up Window
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:920, 1068-1071` and `jarvislib/routing.py:472-473`.
* **What happens**:
  `quiet = muted()` is evaluated before `ask_yes()` (`jarvis.py:920`), so when `run_action("stealth")` succeeds, `fixed("Done.")` speaks `"Done."` out loud instead of in the pop-up (`LIVE TEST 1b-13`) and opens a 10s follow-up ear. Leaving stealth mode by voice falls through to `chat`.

#### BUG-P7-08 (Low): `undo_last()` Pollutes `did` History with Reverse Actions and Fails on Windows `"mixed"` Theme
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:130, 194-233` and `jarvislib/actions.py:88-101`.
* **What happens**:
  Undoing hardware/setting actions calls `run_action()` without `_is_undo=True` (logging a forward action instead of `"undo"` in `did`), and undoing a theme change when Windows was in `"mixed"` mode returns `"That didn't work."`.

### Section 1.2 — Phase 8 Bugs (`FOLLOW-UP TIMING AND SOUNDS`: `8a`..`8d`, `8-A1`..`8-A6`)

#### BUG-P8-01 (High): Conversational Offer Confirmations (`room`, `closing`, `fact`) Bypass Whisper Confidence, Channel, and Timeout Guards
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:938-954, 1003, 1055, 1154, 1157`.
* **What happens**:
  In `exchange()` (`jarvis.py:938-954`), `if closing and is_yes(text):`, `if room and is_yes(text):`, and `if fact and is_yes(text):` do not check `heard_score[0] >= -1.0` or `offer.get("typed") == typed_turn[0]`, allowing a low-confidence noise transcribed as `"Okay."` to kill a running app (`closing`) or save a memory fact.

#### BUG-P8-02 (High): Three Defects in `8d` (`TYPE TO HIM` / `ASK` Command Handling)
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:780-785, 1616-1623`.
* **What happens**:
  1. `ask_yes()` immediately returns `False` when `typed_turn[0]` is `True`, so typed `"ask"`-risk commands print `"Confirm with yes."` followed immediately by `"Cancelled."` in the same turn and can never be confirmed.
  2. When `busy.locked()`, `main()` calls `reply_line("One moment, I'm busy.", muted())` on the main loop thread, mutating `recent["me"]`, `live("")`, and audio state while an active turn is running.
  3. `main()` hardcodes `args=(0,)` instead of `hud_tier()` when spawning `turn()` for `ASK`.

#### BUG-P8-03 (Medium): Dimmed Follow-Up Window Sets `state="idle"` While Holding `busy`, Breaking Orb Click-to-Cancel
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/mic.py:171-174` and `Skins/Spaceship/@Resources/Scripts/jarvis.lua:414-416`.
* **What happens**:
  After `dim_after` (3s), `_listen()` sets `S.set(state="idle")` while continuing to hold `busy` until 10s. Clicking the orb during seconds 3–10 sends `WAKE` (which is ignored because `busy` is locked) instead of waking or cancelling the dimmed follow-up listen.

#### BUG-P8-04 (Medium): `8-A3` Follow-Up Mode Violation After Command Replies + `ear_wait()` Re-Evaluation Race
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:700-702, 874, 900, 936`.
* **What happens**:
  `fixed()` sets `left["again"] = "ear"` (10s window) after command replies instead of Slice D's 5s `"undo"` window (`8-A3`), and `ear_wait()` is evaluated twice (lines 874 and 900), shrinking from `8.0s` to `3.0s` if `offer["expires"]` elapses during transcription.

#### BUG-P8-05 (Low): `8c` `"you can talk"` Falls Through to LLM Outside Class Events & Overlapping Event Edge Case
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/quiet.py:15-46` and `jarvis.py:977`.
* **What happens**:
  Saying `"you can talk"` when no class event is active falls through to `chat`, and `quiet._current()` returns the first matching event's end time instead of `max()`.

### Section 1.3 — Phase 9 Bugs (`ASK HIM WHAT IS WRONG / DIAGNOSIS`: `9-1`..`9-8`)

#### BUG-P9-01 (High): `is_protected()` Omits `OWN_MODEL` (`python`, `pythonw`, `ollama`) and `shipcore`
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/diag.py:192-200`, `jarvislib/routing.py:620`, and `jarvislib/actions.py:381-383`.
* **What happens**:
  `is_protected()` checks `PROTECTED` but omits `OWN_MODEL` (`python`, `pythonw`, `ollama`) and `shipcore`, allowing `"close python"`, `"kill ollama"`, or `"close shipcore"` to terminate JARVIS, Ollama, or `ShipCore.exe`.

#### BUG-P9-02 (High): `diag.ps1` Overwrites Multi-Process Instances Because `$x.InstanceName` Lacks `#N` Disambiguators
* **Where**: `Skins/Spaceship/@Resources/Jarvis/diag.ps1:21-37` and `jarvislib/diag.py:141-165`.
* **What happens**:
  `diag.ps1` keys `$by` by `$x.InstanceName` (`"chrome"` for all 30 Chrome processes), overwriting PIDs and metrics so `top_apps()` undercounts multi-process apps and `gpu_apps()` loses child GPU PIDs.

#### BUG-P9-03 (Medium): `diagnose()` Spawns `diag.ps1 -Part logs -Hours 720` Twice When `span == "boot"`
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/diag.py:345-348, 374-380`.
* **What happens**:
  `gather()` discards raw event timestamps, forcing `diagnose(..., span="boot")` to run `snapshot("logs", 720)` a second time.

#### BUG-P9-04 (Medium): Silent `watch()` Always Spawns a 3.5s PowerShell `processes` Snapshot Even for Disk/Temp Trips
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/diag.py:455-498`.
* **What happens**:
  `watch()` `name_it()` unconditionally calls `gather("cpu", 24, False)` even when the trip was disk space or temperature.

#### BUG-P9-05 (Low): `summary(snap)` Reports `"disk fine"` Without Checking Disk Thresholds
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/diag.py:263-269`.
* **What happens**:
  `summary(snap)` appends `"disk fine"` whenever `snap.get("disks")` is non-empty without checking free-space thresholds.

### Section 1.4 — AI Industry Benchmark Edge-Case Evaluation Findings (`BUG-EDGE-01`..`07`)

#### BUG-EDGE-01 (High): Mid-Utterance Self-Repair Executes the Aborted First Value (`routing.py:658-669`, `reminders.py:65-72`)
* **Benchmark Source**: [Apple SLU Disfluency \& Self-Repair](https://www.google.com/search?q=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F370156965_From_User_Perceptions_to_Technical_Improvement_Enabling_People_Who_Stutter_to_Better_Use_Speech_Recognition).
* **What happens**:
  Utterances with mid-sentence self-repairs (`"set the volume to 40 no wait 60"`, `"set brightness to 80 actually 30"`, `"set a timer for 10 minutes no wait 5 minutes"`, `"open calculator no wait notepad"`) execute the **aborted first number** (`40`, `80`, `10 minutes`) or fail lookup because `_num()` and `reminders.when()` extract the first match left-to-right.

#### BUG-EDGE-02 (High): Compound Multi-Action Commands Silently Drop or Corrupt the Second Action (`routing.py:663-678`)
* **Benchmark Source**: [BFCL Multi-Function / Parallel Calling](https://www.google.com/search?q=https%3A%2F%2Fwww.emergentmind.com%2Ftopics%2Fberkeley-function-calling-benchmark-bfcl).
* **What happens**:
  `understand()` only splits on `" and "` / `" then "` if `fix_route(text)` returns `"chat"`. Greedy regexes (`"set a timer for 5 minutes and mute"`, `"add buy milk to my todo list and open calculator"`, `"mute the volume and turn on dark mode"`) match on the unsplit string and drop or corrupt the second command.

#### BUG-EDGE-03 (High): Negated Commands Bypass `DONT_DO` When Prefixed, and Contradictory Confirmations (`"yes don't"`) Execute Destructive Actions (`routing.py:25-33, 275-279`, `jarvis.py:772-799`)
* **Benchmark Source**: [BFCL Irrelevance / Abstention](https://www.google.com/search?q=https%3A%2F%2Fopenreview.net%2Fpdf%3Fid%3D2GmDdhBdDk) & [Sierra τ-bench Policy Safety](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2406.12045).
* **What happens**:
  `"just don't lock my computer"` or `"hey don't lock my computer"` misses `^` in `DONT_DO`, and `fix_route()` strips the leading two words (`"just don't"`), routing `"lock my computer"` to `('act', 'lock', ...)`! In `ask_yes()`, `YES_WORD` ends with `\b.*`, so `"yes wait no"`, `"yes don't do it"`, and `"sure never mind"` evaluate `is_yes() == True` and execute `"ask"`-risk commands.

#### BUG-EDGE-04 (High): Out-of-Bounds Calendar Dates Raise Uncaught `ValueError` in `reminders.when()` (`reminders.py:49-108`)
* **Benchmark Source**: [Apple ToolSandbox](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2408.04682).
* **What happens**:
  `"remind me on February 30 at 9am to pay rent"` or `"April 31"` raises an uncaught `ValueError: day is out of range for month` in `base.replace(month=mon, day=day)`.

#### BUG-EDGE-05 (Medium): `"from X to Y"` Numeric Commands Set the Old Value `X`, and Fractional Hour Timers Fail (`routing.py:553-609`, `reminders.py:65-72`)
* **Benchmark Source**: [Sierra τ-bench](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2406.12045).
* **What happens**:
  `"change volume from 30 to 50"` sets volume to `30`, and `"set a timer for half an hour"` / `"a quarter of an hour"` fails `reminders.when()`.

#### BUG-EDGE-06 (Medium): Whisper ASR Split-Word & Homophone Artifacts Fail Rule Routing (`routing.py:25-44`)
* **Benchmark Source**: [Apple SLU ASR Robustness](https://www.google.com/search?q=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F370156965_From_User_Perceptions_to_Technical_Improvement_Enabling_People_Who_Stutter_to_Better_Use_Speech_Recognition).
* **What happens**:
  Whisper split compounds (`"blue tooth"`, `"screen shot"`, `"un mute"`, `"bright ness"`, `"fourty"`) fail rule matching; `"un mute"` matches `"mute"` and inverts the user's intent.

#### BUG-EDGE-07 (Medium): Stage-3 LLM `interpret()` Accepts Hallucinated Numeric Arguments When User Uttered None (`routing.py:345-391`)
* **Benchmark Source**: [BFCL Hallucination Detection](https://www.google.com/search?q=https%3A%2F%2Fwww.emergentmind.com%2Ftopics%2Fberkeley-function-calling-benchmark-bfcl) & [ADC Adversarial Function Calling](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fhtml%2F2412.17754v2).
* **What happens**:
  `interpret()` accepts integer targets (`volume=50`, `brightness=80`) from LLM JSON even when `_num(text) is None`.

### Section 1.5 — Comparable Voice Assistant & Model Complaint Audit (`BUG-COMP-01`..`07`)

| JARVIS Subsystem | JARVIS Implementation | Comparable Models & Assistants Audited | Customer / Developer Complaint Audited | Status in JARVIS |
| :--- | :--- | :--- | :--- | :--- |
| **Wake Word & Barge-In** | `openWakeWord` (`hey_jarvis_v0.1.onnx`) + Silero VAD (`vad_threshold=0.5`) in `jarvis.py:1218-1510` | [dscripka/openWakeWord (hey\_jarvis)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fdscripka%2FopenWakeWord%2Fblob%2Fmain%2Fdocs%2Fmodels%2Fhey_jarvis.md), [ESPHome / Home Assistant (#219)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fesphome%2Ffirmware%2Fissues%2F219), [M5 Atom Echo Wake Word](https://www.google.com/search?q=https%3A%2F%2Fcommunity.home-assistant.io%2Ft%2Fm5-atom-echo-wake-word-not-working%2F625957), [Raspberry Pi 5 openWakeWord](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FCarbonRaven%2Ftele-ai%2Fblob%2Fmain%2Fdocumentation%2Fraspberry-pi-5-openwakeword.md) | 1. Continuous speech (`"Hey Jarvis what time is it"`) loses first word.<br>2. `model.reset()` does **not** clear `model.vad.prediction_buffer`, causing stale Silero VAD triggers on next listen. | 1. **Guarded** (`pre` ring buffer).<br>2. **VULNERABLE (`BUG-COMP-04`)**. |
| **Microphone Capture & Energy VAD** | `sounddevice.InputStream` + dynamic RMS noise floor (`floor`) in `jarvislib/mic.py:123-199` | [Python SpeechRecognition (adjust\_for\_ambient\_noise)](https://www.google.com/search?q=https%3A%2F%2Fstackoverflow.com%2Fquestions%2F66070703%2Fwhy-is-my-python-speechrecognition-listen-not-stopping-to-record), [RealtimeSTT (KoljaB/RealtimeVoiceChat)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FKoljaB%2FRealtimeVoiceChat), [python-sounddevice (#173)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fspatialaudio%2Fpython-sounddevice%2Fissues%2F173) | 1. Speaking immediately on frame 0 locks `floor = rms` (`thresh = 3 * rms`), dropping the whole utterance.<br>2. USB/Bluetooth headset hot-plug fails until PortAudio re-initializes (`#173`). | 1. **VULNERABLE (`BUG-COMP-01`)**.<br>2. **VULNERABLE (`BUG-COMP-07`)**. |
| **STT (`faster-whisper`)** | `faster-whisper` (`base.en`, `int8`, `vad_filter=True`, `condition_on_previous_text=False`, `initial_prompt=HINT`) in `jarvislib/hearing.py` | [faster-whisper Hallucination Analysis](https://www.google.com/search?q=https%3A%2F%2Flocalaimaster.com%2Fblog%2Fwhisper-hallucination-fix), [Open-LLM-VTuber](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FSnowfork%2FOpen-LLM-VTuber%2Fblob%2Faidan_fixes%2FREADME.md), [myOfflineAi-VoiceAssistant](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fvbookshelf%2FmyOfflineAi-VoiceAssistant) | 1. Whisper loops repeating phrases when `condition_on_previous_text=True`.<br>2. Whisper echoes `initial_prompt` (`HINT`) or YouTube outros (`"Please subscribe"`, `"Amara.org"`) on short noise bursts. | 1. **Guarded** (`condition_on_previous_text=False`).<br>2. **Partially Guarded -> `REC-02`**. |
| **TTS (`kokoro-onnx` + Sentence Streamer)** | `kokoro-onnx` + `sentences_from()` regex splitter in `jarvislib/speech.py:150-245` | [RealtimeTTS (KoljaB/RealtimeVoiceChat HN Thread)](https://www.google.com/search?q=https%3A%2F%2Fnews.ycombinator.com%2Fitem%3Fid%3D43899028), [Kokoro-FastAPI Local TTS](https://www.google.com/search?q=https%3A%2F%2Flocalaimaster.com%2Fblog%2Flocal-tts-api-server-kokoro-fastapi), [Open-LLM-VTuber](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FSnowfork%2FOpen-LLM-VTuber%2Fblob%2Faidan_fixes%2FREADME.md) | 1. Sentence streamer splits on `"Mr."`, `"Dr."`, `"St."`, `"vs."`, `"e.g."`, causing awkward mid-sentence pauses.<br>2. Markdown symbols read aloud literally. | 1. **VULNERABLE (`BUG-COMP-02`)**.<br>2. **Guarded** (`clean_for_speech()`). |
| **Hybrid Rule + Local LLM Routing (`Ollama`)** | 3-stage router (`route()` -> `fix_route()` -> `interpret()` / `ask_llm()`) in `routing.py` & `llm.py` | [Home Assistant Assist + Ollama](https://www.google.com/search?q=https%3A%2F%2Fcommunity.home-assistant.io%2Ft%2Fprefer-handling-commands-locally-during-continued-conversation%2F883012), [HA Ollama Latency Spike (#947662)](https://www.google.com/search?q=https%3A%2F%2Fcommunity.home-assistant.io%2Ft%2Fwhy-prefer-handling-commands-locally-increases-the-time-from-2-5s-to-52s%2F947662), [HA Core (#169315)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fhome-assistant%2Fcore%2Fissues%2F169315), [HA Local AI Blog](https://www.google.com/search?q=https%3A%2F%2Fwww.home-assistant.io%2Fblog%2F2025%2F09%2F11%2Fai-in-home-assistant%2F) | 1. Unrecognized command phrasing falls through to slow LLM or `UNBUILT_CAPS`.<br>2. Switching between heavy (8B) and fast (3B) Ollama models keeps both in VRAM (`keep_alive`). | 1. **VULNERABLE (`BUG-P7-02`, `BUG-COMP-03`)**.<br>2. **VRAM Contention -> `REC-04`**. |
| **Alarms, Timers & Reminders** | `jarvislib/reminders.py` + `alarm()` loop in `jarvis.py:497-554` + `mic.duck()` | [OpenVoiceOS ovos-skill-alerts](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FOpenVoiceOS%2Fovos-skill-alerts), [Mycroft skill-alarm](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FMycroftAI%2Fskill-alarm), [Amazon Alexa Nearest-Time](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Falexa%2Fcomments%2F1h8gau9%2Fis_there_anyway_to_make_alexa_assume_the_nearest%2F), [Alexa Next-Day](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Falexa%2Fcomments%2F1rmgujx%2Ftried_to_set_an_alarm_for_the_next_day%2F), [Apple Siri Alarms](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2FSiri%2Fcomments%2F1wsewt6%2Fi_asked_siri_for_a_740_pm_alarm_four_different%2F), [Google Home Midday](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fgooglehome%2Fcomments%2F6uvbnj%2Fsetting_an_alarm_for_midday%2F) | 1. Asking `"how much time is left on my <name> timer"` fails to match named timers.<br>2. Alarm loop ducks/unducks master system volume every 2s.<br>3. Post-midnight `"tomorrow"` sets alarm 31.5h ahead. | 1. **VULNERABLE (`BUG-COMP-03`)**.<br>2. **VULNERABLE (`BUG-COMP-05`)**.<br>3. **UX Edge Case -> `REC-01`**. |
| **Conversational Auto-Memory** | `learnable()` in `jarvis.py:311-325` + `jarvislib/memory.py` | OpenAI ChatGPT Memory & MemGPT / Letta local memory agents | Auto-learned facts (`"Want me to remember that?"` -> `"yes"`) append contradictory facts (`"I live in Austin"` + `"I live in Chicago"`). | **VULNERABLE (`BUG-COMP-06`)**. |

* **BUG-COMP-01 (High — `mic.py:150-161`)**: `if floor is None: floor = rms` initializes the noise floor to frame 0's RMS. If the user speaks immediately (`rms = 0.10`), `thresh = 0.30` (`3 * rms`) and the entire utterance is dropped as silence.
* **BUG-COMP-02 (Medium — `speech.py:153`)**: `sentences_from()` splits on any `[.!?]\s+`, breaking mid-sentence on `"Mr."`, `"Mrs."`, `"Dr."`, `"St."`, `"vs."`, `"e.g."`, and `"i.e."`.
* **BUG-COMP-03 (High — `reminders.py:214-218`)**: `how (?:much time|long) ... left on (?:my |the )?(reminder|timer)s?$` rejects timer labels (`"my pasta timer"`) and standalone `"how much time is left"`, sending them to `chat`.
* **BUG-COMP-04 (High — `jarvis.py:1420, 1449, 1495`)**: `wake_loop()` calls `model.reset()` 3 times without clearing `model.vad.prediction_buffer` (unlike `speech_feats()` at line 1235), leaving stale Silero VAD scores `>0.5`.
* **BUG-COMP-05 (Medium — `jarvis.py:521-530`, `mic.py:184-199`)**: `alarm()` calls `hear(patience=1.5)` every 2 seconds, which calls `duck()` and `unduck()` in a loop, oscillating Windows master volume between 30% and 100%.
* **BUG-COMP-06 (Medium — `jarvis.py:953`, `memory.py:166-176`)**: Confirming a `learnable()` fact offer calls `memory_reply("save", fact)` directly, bypassing `fact_save()`'s `_fact_head` conflict replacement.
* **BUG-COMP-07 (Medium — `jarvis.py:1572`, `mic.py:25-68`)**: `list_mics()` runs only once at boot and PortAudio caches devices at `Pa_Initialize()`, so USB/Bluetooth headsets connected later are invisible to `pick_mic()`.

### Section 1.6 — Core Bugs, Repetitive Hardware Pipelines (7 Subsystems), Dead Code, Stale Skins & Test Infrastructure Gaps

* **BUG-CORE-01 (High — `reminders.py:54-92`, `test_jarvis.py:2446-2451`)**: `"next <weekday>"` spoken on the same weekday before the target hour schedules for today (`0 days`) instead of `+7 days`; unpinned clock at `test_jarvis.py:2447` fails on Fridays between 09:00 and 21:00.
* **BUG-CORE-02 (Medium — `jarvis.py:983-997`)**: `SHOW_LOG` / `HIDE_LOG` sets `way["kind"] = "log"` unconditionally before matching and returns without calling `fixed()`.
* **BUG-CORE-03 (Medium — `prompt.py:45-93`)**: Untrusted calendar, to-do, and note text is injected into the LLM system prompt without `<hud_data>` delimiters.
* **BUG-INFRA-01 (Medium)**:
  1. **7 Duplicated Pipelines**: Brightness (`ShipCore.cs` vs `actions.py` PowerShell WMI), Media keys (`actions.py` `keybd_event` vs `Scripts/media.ps1`), Audio COM (`audio.py` vs `ShipCore.cs` vs `audio_switch.ps1`), Sleep/Monitor-off (`actions.py` vs `Main.ini`), GPU/Process telemetry (`ShipCore.cs` vs `diag.ps1` vs `diag.py`), Weather/Location (`ShipCore.cs` vs dead `location.ps1`), and KV parsers (`state.py`, `core_bridge.lua`, `jarvis.lua`).
  2. **Dead Scripts & Unused Meters**: `Scripts/sphere.lua`, `Scripts/storage.lua`, `Scripts/location.ps1`, and 20 unused `[G1_1]`..`[I1_20]` meters in `Overlay/Jarvis/Meters.inc`.
  3. **`Settings.inc` Pollution**: 5x duplicated comment blocks, `JarvisCallMe=Senai`, `BootSound=1`, leading spaces after `=`, and dead `ObsidianVault=`.
  4. **`Everywhere` Test Proxy Blind Spot (`test_jarvis.py:25-32`)**: Patching `j.act_*` does not update `ACTION_TABLE[key].run` or `ACTIONS[key]`.

### Section 1.7 — HUD Scroll Edit Audit (`BUG-SCROLL-01`..`03`)

* **BUG-SCROLL-01 (High — `Scripts/drawer.lua:27-31, 40-41, 95-99, 115`)**: `build()` returns early at line 30 when `focus` is set (`"ALL INSTALLED APPS"` or any folder opened from a side slot) **before** clamping `scroll <= maxScroll` at lines 40–41. Scrolling down in `focus` mode overscrolls past the list into blank space, hides all row hit boxes (`H1_2`..`H1_20`) so scrolling back up with the wheel stops working, and pushes the scrollbar thumb (`frac > 1.0`) outside the bottom of the panel.
* **BUG-SCROLL-02 (Medium — `Scripts/lib.lua:490`, `Scripts/target.lua:5, 35, 36`)**: Non-ASCII Unicode characters in Lua comments (`▸` on `lib.lua:490` from the scroll caption example, and `📅`/`⏰` in `target.lua`) cause `tools/rmsim.py` (`lua_syntax_check`, line 873) to fail with 2 `encoding` errors.
* **BUG-SCROLL-03 (Low — `Scripts/drawer.lua:11-16`, `Overlay/Jarvis/Meters.inc`)**: Unlike `control.lua:39-41` (which binds `MouseScrollUpAction`/`MouseScrollDownAction` on `Bounds` with `Fill Color 0,0,0,1`), `drawer.lua` only binds scroll on individual row hits (`H1_2`..`H1_20`), leaving dead scroll zones in the header, margins, and scrollbar track.

## Part 2: Complete Step-by-Step Fix Plan with Pseudocode (`Fixes 1–29`)

### Fix 1: Restore Windows Read-Back Replies (`done_line`) for Confirmed `"ask"`-Risk Actions (`BUG-P7-01`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/actions.py (top of done_line):
def done_line(action, target):
    if action == "todo":
        return "Added."
    ...
# In Skins/Spaceship/@Resources/Jarvis/jarvis.py (exchange, lines 1065-1072):
if kind == "act":
    if ask_yes(prompt, quiet):
        ok = run_action(action, target, pending=(action, target))
        way["result"] = "done" if ok else "failed"
        if action in ("mute", "unmute", "volume", "stealth"):
            quiet = True if action == "stealth" else muted()
        fixed(done_line(action, target) if ok else "That didn't work.")
```

### Fix 2: Prune Built Capabilities from `UNBUILT_CAPS` & Expand Brightness / Mic / Settings Routing (`BUG-P7-02`, `BUG-P7-03`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py:
UNBUILT_CAPS = {
    "bluetooth": r"unpair\b.*\b(?:bluetooth|headphones|earbuds|airpods|device)",
    "wifi": r"wi-?fi|airplane mode|flight mode|hotspot",
    "display": r"wallpaper|(?:desktop )?background|resolution|screen ?saver|refresh rate",
    "account": r"hibernat\w*|sign (?:me )?out|log (?:me )?(?:off|out)",
    "keyboard light": r"keyboard (?:light|backlight)",
}
# Add "microphone"/"mic" to ("sound", ...) and "brightness" to ("display", ...) in `names`,
# and use `bit_or_by = r"(?: (?:a )?(?:bit|little|tad)| slightly| by (.+?)(?: ?%| percent)?)?"` on brightness and mic step rules.
```

### Fix 3: Fix `undo_last()` for `mic_unmute`, Mixed Themes, and `did_add("undo")` (`BUG-P7-04`, `BUG-P7-08`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvis.py (undo_last, lines 220-227):
if what.startswith("mic_"):
    was_muted, percent = before
    ok = (run_action("mic_level", ("set", percent), _is_undo=True) if what == "mic_level"
          else run_action("mic_mute", None, ("mic_mute", None), _is_undo=True) if was_muted
          else run_action("mic_unmute", None, _is_undo=True))
    undo.clear()
    if not ok:
        return "That didn't work."
    now_muted, now_pct = mic_volume()
    return (f"Microphone back at {now_pct} percent." if what == "mic_level"
            else "Microphone muted." if now_muted else "Microphone unmuted.")
```

### Fix 4: Case-Insensitive & Multi-Word Window Matching in `running_window()`, `act_open()`, and `close` (`BUG-P7-05`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/actions.py:
def running_window(name):
    raw_words = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in name.split()]
    raw_words = [w for w in raw_words if w]
    if not raw_words:
        return None
    want = "".join(raw_words)
    tail = raw_words[-1] if len(raw_words) > 1 else ""
    stems = [(exe, re.sub(r"[^a-z0-9]", "", os.path.splitext(exe)[0].lower())) for exe in open_windows()]
    checks = (
        lambda s: s == want or (len(tail) >= 3 and s == tail),
        lambda s: (len(want) >= 3 and s.startswith(want)) or (len(tail) >= 3 and s.startswith(tail)),
        lambda s: (len(want) >= 4 and want in s) or (len(s) >= 4 and s in want),
    )
    for ok in checks:
        for exe, stem in stems:
            if stem and ok(stem):
                return exe
    return None
```

### Fix 5: Cache `bt_devices()` with a 5s TTL and Catch `subprocess.TimeoutExpired` (`BUG-P7-06`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/actions.py:
_bt_cache = [0.0, None]
def _bt_ps(call, timeout=40):
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", BT_DEV_SCRIPT % call],
                             creationflags=NO_WINDOW, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise OSError("Windows timed out listing or changing Bluetooth devices") from e
    if out.returncode:
        raise OSError("Windows would not list or change Bluetooth devices")
    return out.stdout
```

### Fix 6: Stealth Mode Pop-Up Reply, No Follow-Up Ear, and Leave-Stealth Refusal (`BUG-P7-07`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py (after line 473):
if re.fullmatch(r"(?:leave|exit|turn off|disable|end|quit|stop) (?:the )?stealth(?: mode)?|stealth(?: mode)? off", cmd):
    return ("say", None, None, "I can't leave stealth mode by voice; switch it off in the Control Center.")
```

### Fix 7: Enforce Confidence, Same-Channel, and Expiry Guards on Offer Confirmations (`BUG-P8-01`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvis.py (lines 938-954):
now_t = time.time()
same_chan = offer.get("typed", False) == typed_turn[0]
valid_offer = now_t < offer.get("expires", 0) and same_chan
fact = offer.pop("fact", None) if valid_offer else None
room = offer.pop("room", None) if valid_offer else None
closing = offer.pop("close", None) if valid_offer else None
offer.clear()
sure_yes = typed_turn[0] or heard_score[0] >= -1.0
```

### Fix 8: Safe Non-Blocking `ASK` Handling and Same-Channel Typed Confirmation (`BUG-P8-02`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvis.py (main, lines 1616-1623):
elif parts[0] == "ASK":
    text = ask_text(raw)
    if not text:
        pass
    elif busy.locked():
        convo_add("J", "One moment, I'm busy.")
        S.set(pop="open")
    else:
        threading.Thread(target=turn, args=(min(hud_tier(), 2),), kwargs={"typed": text}, daemon=True).start()
```

### Fix 9: Fix Dimmed Follow-Up Orb Click (`8a`), Command Follow-Up Mode (`8-A3`), and `ear_wait()` Snapshot (`BUG-P8-03`, `BUG-P8-04`, `BUG-P8-05`)
```python
# Snapshot `wait_direct = ear_wait()` once before `listen()` in `exchange()`, set `left["again"] = "undo"` after command replies,
# and reply `fixed("I'm not in quiet mode right now.")` when `quiet_talk.TALK` is spoken outside class hours.
```

### Fix 10: Protect `python`, `pythonw`, `ollama`, and `shipcore` in `is_protected()` (`BUG-P9-01`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/diag.py:
PROTECTED = frozenset({
    "explorer", "svchost", "csrss", "wininit", "winlogon", "lsass", "services", "smss", "dwm", "system",
    "registry", "fontdrvhost", "sihost", "ctfmon", "audiodg", "msmpeng", "searchhost", "taskhostw",
    "rainmeter", "jarvis", "shipcore",
})
OWN_MODEL = frozenset({"ollama", "python", "pythonw"})
def is_protected(name):
    stem = re.sub(r"\.exe$", "", str(name or "").lower())
    return stem in PROTECTED or stem in OWN_MODEL
```

### Fix 11: Preserve Multi-Process Instances in `diag.ps1` and Eliminate Duplicate Event Log Reads (`BUG-P9-02`, `BUG-P9-03`, `BUG-P9-04`, `BUG-P9-05`)
```powershell
# In Skins/Spaceship/@Resources/Jarvis/diag.ps1 (lines 21-32):
$inst = if ($p -match '\\process\(([^)]+)\)\\') { $Matches[1] } else { $i }
if (-not $by.ContainsKey($inst)) {
    $by[$inst] = @{ name = ($inst -replace '#\d+$', ''); pid = 0; cpu = 0; mem = 0; io = 0 }
}
```

### Fix 12: Fix `"next <weekday>"` Same-Day Scheduling & Pin Clock in `test_jarvis.py:2446` (`BUG-CORE-01`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py:
wd = re.search(rf",? (?:on )?(next |this |coming )?({'|'.join(WEEKDAYS)})(?: at)? ", s)
...
if wd:
    days = (WEEKDAYS.index(wd.group(2)) - datetime.fromtimestamp(now).weekday()) % 7
    if days == 0 and (wd.group(1) or "").strip() == "next":
        days = 7
```

### Fix 13: Route `SHOW_LOG` / `HIDE_LOG` Through `fixed()` and Wrap Prompt HUD Data in `<hud_data>` (`BUG-CORE-02`, `BUG-CORE-03`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvis.py:
if HIDE_LOG.search(text):
    way.update(kind="log", via="rule")
    S.set(pop="close")
    fixed("Closing the log.")
    return
if SHOW_LOG.search(text):
    way.update(kind="log", via="rule")
    S.set(pop="open")
    fixed("Here's everything we've said.")
    return
```

### Fix 14: Unify Hardware Helpers (`ShipCore.exe`), Update `Everywhere` Proxy, and Clean Up Dead Files (`BUG-INFRA-01`)
```python
# Sync ACTION_TABLE and ACTIONS in test_jarvis.py Everywhere.__setattr__; use ShipCore.exe brightness in actions.py;
# clean Settings.inc duplicates; remove dead sphere.lua, storage.lua, and location.ps1.
```

### Fix 15: Mid-Utterance Self-Repair Normalization (`"no wait"`, `"actually"`, `"I mean"`) (`BUG-EDGE-01`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py:
REPAIR_SPLIT = re.compile(r"\b(?:no wait|wait no|actually no|sorry i meant|i meant|i mean|or rather|actually)\b\s*(.+)$")
```

### Fix 16: Pre-Route Compound Command Splitting & Anchor `turn on (dark|light) mode` (`BUG-EDGE-02`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py (understand):
# Split on `\b(?:and(?: then)?|then)\b` before `fix_route(text)` when both clauses independently route to non-chat commands.
```

### Fix 17: Polite Negation Guard (`DONT_DO` Anywhere Before Verb) & Contradictory Confirmation Guard (`BUG-EDGE-03`)
```python
# In jarvis.py:
YES_ABORT = re.compile(r"\b(?:no|not|don'?t|dont|wait|stop|cancel|never ?mind|hold on)\b")
def is_yes(text):
    s = strip_name(text).lower().strip(" .,!?")
    return not YES_ABORT.search(s) and bool(YES_WORD.fullmatch(s))
```

### Fix 18: Catch Invalid Calendar Dates in `reminders.when()` (`BUG-EDGE-04`)
```python
# Wrap `base.replace(month=mon, day=day, hour=hour, minute=minute)` in `try ... except ValueError: return None, s`.
```

### Fix 19: Support `"from X to Y"` Numeric Targets & Fractional Hour Timers (`"half an hour"`) (`BUG-EDGE-05`)
```python
# Allow optional `(?:from \d+(?: ?%| percent)? )?` before `(?:to|at) (.+)` in volume/brightness/mic_level,
# and normalize "half an hour" -> "30 minutes", "a quarter of an hour" -> "15 minutes" in reminders._words_to_ints().
```

### Fix 20: Normalize Whisper Split-Word Compounds & Homophones in `clean_cmd()` (`BUG-EDGE-06`)
```python
# Collapse "blue tooth" -> "bluetooth", "screen shot" -> "screenshot", "un mute" -> "unmute", "bright ness" -> "brightness", "fourty" -> "forty".
```

### Fix 21: Guard Stage-3 `interpret()` Against Hallucinated Numbers (`BUG-EDGE-07`)
```python
# In interpret(), require `_num(text) is not None` before accepting an integer target for volume, brightness, or mic_level.
```

### Fix 22: Fix Adaptive Noise Floor Lock-In When User Speaks Immediately on Frame 0 (`BUG-COMP-01`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/mic.py (_listen, lines 150-161):
rms = float(np.sqrt(np.mean(block * block)))
if floor is None:
    floor = min(rms, 0.015)
thresh = max(floor * 3.0, 0.012)
if rms > thresh:
    if not started:
        onset[0] = round(waited * 0.03, 2)
    started = True
    quiet = 0
elif not started:
    floor = 0.95 * floor + 0.05 * min(rms, 0.025)
```

### Fix 23: Prevent TTS Sentence Streamer (`sentences_from`) from Splitting on Abbreviations & Titles (`BUG-COMP-02`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/speech.py:
SENT_SPLIT = re.compile(
    r"(.+?(?<!\bMr)(?<!\bMrs)(?<!\bMs)(?<!\bDr)(?<!\bProf)(?<!\bSr)(?<!\bJr)"
    r"(?<!\bSt)(?<!\bMt)(?<!\bvs)(?<!\betc)(?<!\be\.g)(?<!\bi\.e)[.!?])(\s+|$)",
    re.IGNORECASE,
)
```

### Fix 24: Support Named Timer Queries (`"how much time is left on my pasta timer"`) & Standalone Time-Left Queries (`BUG-COMP-03`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py (lines 214-219):
m = re.match(
    r"(?:what (?:are|is) my (reminder|timer|alarm)s?|do i have (?:any )?(reminder|timer|alarm)s?"
    r"|list (?:my )?(reminder|timer|alarm)s?|check (?:my )?(reminder|timer|alarm)s?"
    r"|how (?:much time|long) (?:is |do i have )?left(?: on (?:my |the )?(?:[a-z0-9 ]+? )?(reminder|timer)s?| on it)?)$",
    cmd
)
```

### Fix 25: Clear `model.vad.prediction_buffer` Whenever `model.reset()` Is Called in `wake_loop()` (`BUG-COMP-04`)
```python
# In Skins/Spaceship/@Resources/Jarvis/jarvis.py:
def reset_oww(m):
    if m is not None:
        m.reset()
        if hasattr(m, "vad") and hasattr(m.vad, "prediction_buffer"):
            m.vad.prediction_buffer.clear()
```

### Fix 26: Prevent Alarm Ring Loop (`alarm()`) from Pumping System Volume via `duck()` / `unduck()` (`BUG-COMP-05`)
```python
# Add `duck_audio=True` to `listen()` and `hear()`, and call `hear(patience=1.5, duck_audio=False)` inside `alarm()`.
```

### Fix 27: Deduplicate Contradictory Slot Prefix (`_fact_head`) When Saving Auto-Learned Memory Facts (`BUG-COMP-06`)
```python
# In memory_reply("save", target), replace any existing fact with the same singular `_fact_head(target)` prefix ("i live in", "my job is", etc.).
```

### Fix 28: Refresh PortAudio Device List on Microphone Hot-Plug / Selection Miss (`BUG-COMP-07`)
```python
# In pick_mic(), call list_mics(refresh=True) on miss; in list_mics(refresh=True), call sd._terminate(); sd._initialize() when mic lock is free.
```

### Fix 29: Clamp `drawer.lua` Scroll in `focus` Mode, Bind Scroll to `Bounds`, and Strip Non-ASCII Lua Comment Glyphs (`BUG-SCROLL-01`..`03`)
```lua
-- In Skins/Spaceship/@Resources/Scripts/drawer.lua:
function Initialize()
  H = dofile(SKIN:GetVariable('@') .. 'Scripts\\lib.lua')
  A = dofile(SKIN:GetVariable('@') .. 'Scripts\\apps.lua')
  H.init()
  A.load()
  SKIN:Bang('!SetOption', 'Bounds', 'Shape', 'Rectangle 0,0,(#WW#*#Scale#),(#WH#*#Scale#) | Fill Color 0,0,0,1 | StrokeWidth 0')
  SKIN:Bang('!SetOption', 'Bounds', 'MouseScrollUpAction', '[!CommandMeasure mScript "OnScroll(1,0,-1)"]')
  SKIN:Bang('!SetOption', 'Bounds', 'MouseScrollDownAction', '[!CommandMeasure mScript "OnScroll(1,0,1)"]')
end

local function build()
  rows = {}
  if focus then
    for _, app in ipairs(A.cats[focus].apps) do rows[#rows + 1] = { kind = 'app', app = app } end
    rows[#rows + 1] = { kind = 'all' }
  else
    rows[#rows + 1] = { kind = 'cat', cat = A.cats.all, jump = true }
    for _, id in ipairs(A.catOrder) do
      local cat = A.cats[id]
      rows[#rows + 1] = { kind = 'cat', cat = cat }
      if open[id] then
        for _, app in ipairs(cat.apps) do rows[#rows + 1] = { kind = 'app', app = app } end
      end
    end
  end
  local maxScroll = math.max(0, #rows - ROWS)
  scroll = H.clamp(scroll, 0, maxScroll)
end
```

## Part 3: Possible Recommendations — Low-Probability or Complex Cross-Industry Issues & Architectural Solutions (`REC-01`..`REC-05`)

* **`REC-01` — Early-Morning (`00:00–03:59 AM`) `"Set an alarm for 8 AM tomorrow"` Disambiguation (`reminders.py:54, 165-179`)**:
  Explicitly state the weekday name when `"tomorrow"` is spoken between midnight and 4:00 AM (`"Set alarm for Sunday at 8:00 AM. Say 'this morning' if you meant today."`) and support a 1-turn `FLIP_TODAY` (`"this morning"` / `"today"`) handler alongside `flip_ampm()`.
* **`REC-02` — Whisper `initial_prompt` (`HINT`) Vocabulary Replacement & Expanded `PHANTOM` Filter (`hearing.py:13, 88-111`)**:
  Replace full-sentence `HINT` with comma-separated domain vocabulary (`"Jarvis, timer, alarm, reminder, volume, mute, Bluetooth, brightness, screenshot, stealth."`) and expand `PHANTOM` to block `"please subscribe"`, `"like and subscribe"`, and `"amara.org"`.
* **`REC-03` — Context-Aware Dynamic End-of-Turn Endpointing (`mic.py:134-170`)**:
  Use a crisp `0.65s` silence window during short confirmation/alarm listens (`patience <= 5`) and `1.0s` (with a hesitation allowance on `<0.7s` speech) on standard turns.
* **`REC-04` — Explicit VRAM Eviction (`keep_alive: 0`) When Switching Between `JarvisModel` (8B) and `JarvisModelFast` (3B) (`llm.py:66-132`)**:
  Track `_loaded_model` in `llm.py` and send a background `keep_alive: 0` request to `/api/generate` whenever `pick_model(tier)` switches models so both models never sit in VRAM simultaneously.
* **`REC-05` — Per-Application Audio Session Ducking (`ISimpleAudioVolume`) (`mic.py:71-104`, `ShipCore.cs`)**:
  Duck third-party audio sessions via Windows `IAudioSessionManager2` / `ISimpleAudioVolume` instead of lowering the master Windows volume slider.

## Part 4: Architectural Recommendation — WebView2 / Tauri v2 Migration & Intro Animation Blueprint for Lenovo Legion (`BLACK-CLOVER`)

### 1. Is WebView2 / Tauri v2 + `ShipCore` & `jarvis.py` a Good Idea on Your Specific Lenovo Legion (`BLACK-CLOVER`)?

Your machine (`Hardware.inc` & `Docs/SETUP.txt`) is a **Lenovo Legion (`BLACK-CLOVER`)** equipped with:
* **CPU / iGPU**: **AMD Ryzen AI 9 465** (10 cores / 20 threads) + **AMD Radeon 880M iGPU** (RDNA 3.5, 12 Compute Units)
* **dGPU**: **NVIDIA GeForce RTX 5070 Laptop GPU (12 GB GDDR7)** with NVIDIA Advanced Optimus / MUX & **Lenovo Legion Toolkit (`llt.exe`)** (`ECO`, `HYBRID`, `AUTO`, `dGPU`)
* **Display**: **2560x1600 165Hz OLED**

**Verdict for `BLACK-CLOVER`**: **Yes — your hardware is an ideal match for a WebView2 / [Tauri v2](https://www.google.com/search?q=https%3A%2F%2Fv2.tauri.app%2Flearn%2Fwindow-customization%2F) HUD**, provided you enforce **three Lenovo Legion / OLED-specific engineering rules** (all of which can be automated inside `ShipCore.exe`):

1. **Rule 1 — Pin the HUD Process to the Radeon 880M iGPU (Never Wake the RTX 5070 in `HYBRID` / `ECO` Mode)**:
   * On a Lenovo Legion in `HYBRID` or `AUTO` mode, if any desktop app opens a Direct3D context on the NVIDIA dGPU, the RTX 5070 stays awake drawing 15–25W of idle battery power ([NVIDIA Optimus / Hybrid GPU Power Guide](https://www.google.com/search?q=https%3A%2F%2Fsupport.genymotion.com%2Fhc%2Fen-us%2Farticles%2F360020501537-How-to-fix-issues-on-Windows-with-laptops-using-hybrid-graphics-dual-GPU)).
   * Your **Radeon 880M iGPU** is more than powerful enough to render a 2560x1600 165Hz 2D/WebGL HUD at `<2%` iGPU load while the RTX 5070 sleeps at `0W` (or stays 100% dedicated to `Ollama` / games).
   * In `ShipCore.exe` (or Tauri), you can automatically write the Windows `GpuPreference=1;` registry key (`HKCU\Software\Microsoft\DirectX\UserGpuPreferences`) for `ShipCore.exe` and `msedgewebview2.exe` on first launch so the user never even has to open Windows Graphics Settings manually (unlike `SETUP.txt` step 2 today!).
2. **Rule 2 — Zero-GPU Suspension During Fullscreen Games (`TrySuspend` / `Visibility` Throttling)**:
   * When `ShipCore.exe` detects a fullscreen game or `PerfTier == 3` (`STEALTH`), calling `CoreWebView2.TrySuspendAsync()` (or hiding the window via `ShowWindow(SW_HIDE)`) causes [Microsoft Edge WebView2](https://www.google.com/search?q=https%3A%2F%2Flearn.microsoft.com%2Fen-us%2Fmicrosoft-edge%2Fwebview2%2Fconcepts%2Fperformance) to drop its GPU composition surfaces and enter `0.0% CPU / 0.0% GPU` suspended mode in under 10 ms.
3. **Rule 3 — OLED Burn-In Protection on Your 2560x1600 OLED Panel**:
   * Because `BLACK-CLOVER` has a **2560x1600 OLED** display, static cyan HUD lines at 100% brightness pose a long-term OLED subpixel wear risk.
   * In WebView2/CSS, you can add a subtle, imperceptible **2-pixel Lissajous pixel-orbit shift** (`transform: translate(dx, dy)` over a 120-second cycle) and automatic idle dimming (`opacity: 0.35` after 3 minutes of mouse/voice inactivity) in **5 lines of CSS** — something that would require refreshing all 25 skin windows in Rainmeter!

### 2. Would It Let You Easily Add Animations & a Cinematic Intro Sequence?

**Yes — this is the single biggest advantage of moving from Rainmeter to WebView2 / [Tauri v2](https://www.google.com/search?q=https%3A%2F%2Fv2.tauri.app%2Flearn%2Fwindow-customization%2F).**

Compare what `Overlay\Boot\Boot.ini` + `Scripts/boot.lua` (149 lines of Lua + 257 lines of `.ini`) can do today vs. what you can do in WebView2 with [GSAP Timeline](https://www.google.com/search?q=https%3A%2F%2Fgsap.com%2Fdocs%2Fv3%2FGSAP%2FTimeline%2F), CSS/SVG, and WebGL:

| Animation Capability | Current Rainmeter (`boot.lua` + `lib.lua`) | WebView2 / Tauri v2 ([GSAP](https://www.google.com/search?q=https%3A%2F%2Fgsap.com%2Fdocs%2Fv3%2FGSAP%2FTimeline%2F) + SVG + Canvas/Three.js) |
| :--- | :--- | :--- |
| **Drawing Vector Borders On-Screen ("Laser Trace" Intro)** | **Impossible across modules**: `boot.lua:113` can only fade each module window's flat rectangle opacity (`!SetTransparency`), because Rainmeter cannot animate `stroke-dashoffset` across path segments without rebuilding string options every frame | **Trivial (1 line of CSS/GSAP)**: Every cockpit strut and panel border is an `<svg><path>` where `stroke-dashoffset` animates from `pathLength -> 0`, tracing the entire spaceship cockpit with glowing laser lines at **165 fps** |
| **3D Cockpit / Hologram Camera Fly-In** | **Impossible**: Rainmeter only supports 2D affine `TransformationMatrix` (`a;b;c;d;tx;ty`) — no 3D perspective (`perspective`, `rotateX/Y/Z`) and no shaders | **Native**: CSS 3D transforms (`perspective: 1200px; transform: rotateX(...) scale(...)`) let the side wing panels unfold from the edges in 3D space while the Three.js 3D JARVIS core coalesces from a particle cloud |
| **Synchronized Audio + Visual Sequencing** | **Hardcoded frame counting**: `boot.lua:12-15` counts `Update=16` ticks (`SCAN0=2, P0=22, C0=last+4`) and can only play a single `.wav` file (`[Play "..."]`) with no timeline scrubbing | **Declarative Timeline**: A single `gsap.timeline()` sequences the audio cues, laser grid sweep, wireframe trace, text scramble/typewriter decoder, dial spin-ups, and JARVIS voice greeting (`"All systems nominal, sir"`) with millisecond precision |
| **Chromatic Aberration, Glitch & Bloom Shaders** | **None**: Bloom is faked by drawing every line 3 times (`lib.lua:168`); no RGB split, lens flare, or CRT/hologram distortion | **Real GPU Shaders**: WebGL post-processing (`UnrealBloomPass`, RGB shift, scanline distortion) and CSS `backdrop-filter: blur(12px)` run natively on your Radeon 880M at 165Hz |
| **Interactive Hover / Click Micro-Animations** | **None**: Buttons jump instantaneously between states on `Update()` | **Automatic**: `transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1)` gives every button, tab, and dial smooth spring physics, hover glow expansion, and ripple feedback |

### 3. Concrete Example: How a 165Hz Cinematic Intro Sequence Looks in Code (~25 Lines of GSAP vs. 400 Lines of `Boot.ini` + `boot.lua`)

Because `layout/layout.json` already contains the exact polygon coordinates of all 35 zones on your `2560x1600` canvas, your WebView2 app can render every zone directly from `layout.json` and run a full Iron-Man / Spaceship cockpit power-on sequence in ~25 lines of [GSAP](https://www.google.com/search?q=https%3A%2F%2Fgsap.com%2Fdocs%2Fv3%2FGSAP%2Fgsap.timeline%28%29%2F):

```javascript
// Complete 3.2-second 165Hz Spaceship Cockpit Intro Sequence in WebView2 / Tauri v2
function playIntroSequence(systemReadings) {
  const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

  tl.set(".hud-zone", { opacity: 0, scale: 0.92, transformOrigin: "center center" })
    // 1. 0.00s: Top-to-bottom laser scanner beam + cockpit hull fade-in
    .fromTo("#scanner-beam", { y: -40, opacity: 1 }, { y: 1600, duration: 0.55, ease: "power2.inOut" }, 0)
    .fromTo("#cockpit-hull", { opacity: 0, filter: "brightness(2.5)" }, { opacity: 1, filter: "brightness(1)", duration: 0.7 }, 0.05)

    // 2. 0.30s: Laser-trace every panel's chamfered SVG border from center outward
    .set(".hud-zone", { opacity: 1 }, 0.30)
    .fromTo(".zone-border-path",
      { strokeDasharray: 2000, strokeDashoffset: 2000 },
      { strokeDashoffset: 0, duration: 0.65, stagger: { from: "center", amount: 0.35 } },
      0.30
    )

    // 3. 0.45s: Unfold left/right wing panels in 3D perspective & spin up bottom dials + 3D Jarvis Orb
    .fromTo(".hud-zone",
      { scale: 0.92, rotationY: (i, el) => el.dataset.side === "left" ? 18 : el.dataset.side === "right" ? -18 : 0 },
      { scale: 1, rotationY: 0, duration: 0.6, stagger: { from: "center", amount: 0.3 } },
      0.45
    )
    .fromTo(jarvisOrbUniforms.uImplode, { value: 0.0 }, { value: 1.0, duration: 0.9, ease: "elastic.out(1, 0.6)" }, 0.50)
    .fromTo(".dial-progress", { "--sweep": 0 }, { "--sweep": (i, el) => el.dataset.target, duration: 0.8 }, 0.60)

    // 4. 0.90s: Typewriter/scramble decode of system check readouts (CPU, RTX 5070, RAM, Storage, Network)
    .fromTo("#boot-readout-card", { clipPath: "inset(50% 0 50% 0)", opacity: 0 }, { clipPath: "inset(0% 0 0% 0)", opacity: 1, duration: 0.35 }, 0.90)
    .to(".boot-row-value", { duration: 0.5, stagger: 0.07, scrambleText: { text: "{original}", chars: "0123456789%OK" } }, 1.05)
    .to("#boot-readout-card", { opacity: 0, y: -12, duration: 0.35, delay: 0.9 });

  return tl;
}
```