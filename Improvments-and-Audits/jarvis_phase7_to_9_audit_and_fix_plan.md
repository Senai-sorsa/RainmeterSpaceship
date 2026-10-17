# Comprehensive Repository Audit, Comparable Assistant Complaint Analysis & Master Fix Plan (`RainmeterSpaceship` / JARVIS)

## Executive Summary & Validation Baseline

This master report presents a full-repository forensic audit of `RainmeterSpaceship` (`chore/jarvis-baseline-and-performance`, 26,825 lines across Python, Lua, C#, PowerShell, and Rainmeter `.ini`/`.inc` skin configurations), covering:
1. **Phases 7, 8, and 9** of `JARVIS-Repair-Plan.txt` (`BUG-P7-01`..`08`, `BUG-P8-01`..`05`, `BUG-P9-01`..`05`).
2. **AI Industry Benchmark Edge-Case Testing** (`BUG-EDGE-01`..`07`), drawing on evaluation methodologies from the [Berkeley Function-Calling Leaderboard (BFCL)](https://www.google.com/search?q=https%3A%2F%2Fwww.emergentmind.com%2Ftopics%2Fberkeley-function-calling-benchmark-bfcl), [Apple ToolSandbox](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2408.04682), [Sierra τ-bench](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2406.12045), [Apple Spoken Language Understanding (SLU) Disfluency Research](https://www.google.com/search?q=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F370156965_From_User_Perceptions_to_Technical_Improvement_Enabling_People_Who_Stutter_to_Better_Use_Speech_Recognition), and [OpenAI Instruction Hierarchy](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2404.13208).
3. **Comparable Voice Assistant & Model Complaint Audit** (`BUG-COMP-01`..`07` + Guarded Feature Matrix), auditing customer and developer complaints across voice assistants that share JARVIS's exact components ([openWakeWord](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fdscripka%2FopenWakeWord%2Fblob%2Fmain%2Fdocs%2Fmodels%2Fhey_jarvis.md), [faster-whisper](https://www.google.com/search?q=https%3A%2F%2Flocalaimaster.com%2Fblog%2Fwhisper-hallucination-fix), [RealtimeVoiceChat / RealtimeSTT + RealtimeTTS](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FKoljaB%2FRealtimeVoiceChat), [Open-LLM-VTuber](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FSnowfork%2FOpen-LLM-VTuber%2Fblob%2Faidan_fixes%2FREADME.md), [Home Assistant Assist + Ollama](https://www.google.com/search?q=https%3A%2F%2Fwww.home-assistant.io%2Fblog%2F2025%2F09%2F11%2Fai-in-home-assistant%2F), [OpenVoiceOS / Mycroft Alerts](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FOpenVoiceOS%2Fovos-skill-alerts), and consumer assistants [Amazon Alexa](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Falexa%2Fcomments%2F1h8gau9%2Fis_there_anyway_to_make_alexa_assume_the_nearest%2F), [Apple Siri](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2FSiri%2Fcomments%2F1wsewt6%2Fi_asked_siri_for_a_740_pm_alarm_four_different%2F), and [Google Assistant](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fgooglehome%2Fcomments%2F6uvbnj%2Fsetting_an_alarm_for_midday%2F)).
4. **Core Bugs, Repetitive Hardware Pipelines (7 Subsystems), Dead Code, Stale Skins & Test Infrastructure Gaps** (`BUG-CORE-01`..`03`, `BUG-INFRA-01`).
5. **Complete Step-by-Step Fix Plan with Pseudocode** (`Fixes 1–28`) and a new **Possible Recommendations (`REC-01`..`REC-05`)** section for lower-probability or complex architectural edge cases.
6. Note: Stop key should also work when JARVIS is still in listening mode. Also let user select in in command center by clicking "select" and prompting the user to type it in.
 
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

### Master Index of All 36 Confirmed Bugs & 5 Architectural Recommendations

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
  In `actions.py:320-355`, `done_line(action, target)` implements dedicated read-back replies for Phase 7's `"ask"`-risk actions so JARVIS reports what Windows actually did (`JARVIS-Repair-Plan.txt` lines 3073–3074, 3108, and Live Tests `1b-3`, `1b-8`, `1b-9`, `1b-10`, `1b-14`, `1b-15`):
  * `"micdev"` -> `"Listening through {target}. It applies the next time I listen."`
  * `"bluetooth_off"` -> `"Bluetooth is {bluetooth_radio()}."`
  * `"btlink"` -> `"Connected to {target[2]}."` / `"Disconnected from {target[2]}."`
  * `"power"` -> `"Power mode is {POWER_NAMES.get(power_key(power_plans()[0]), ...)}."`
  * `"recycle"` -> `"Recycle bin emptied."`
  * `"mic_mute"` -> `"Microphone muted."`
  However, in `jarvis.py:1070-1071`:
  ```python
  unsure = prompt.startswith("Did you say: ")    # then say what really happened, as an unasked command does
  fixed(("Added." if action == "todo" else done_line(action, target) if unsure or action == "sleep" else "Done.") if ok else "That didn't work.")
  ```
  Because `"micdev"`, `"bluetooth_off"`, `"btlink"`, `"power"`, `"recycle"`, and `"mic_mute"` all have `risk="ask"` with their own confirmation prompt (`"You want me to ... Confirm with yes."`), `unsure` (`prompt.startswith("Did you say: ")`) is always `False`! Consequently, `done_line(action, target)` is **never called** after the user says `"yes"` — JARVIS just says `"Done."`, rendering all 6 branches in `done_line()` dead code in normal turns and failing Live Tests `1b-3`, `1b-8`, `1b-9`, `1b-10`, `1b-14`, and `1b-15`.
* **Why `test_jarvis.py` missed it**: The unit tests in `test_jarvis.py` (lines 261, 309, 354, 415, 460, 519) called `j.run_action(...)` and `j.done_line(...)` directly as separate function calls instead of running a full `j.turn()` with `"yes"`.

#### BUG-P7-02 (High): Stale `UNBUILT_CAPS` Falsely Refuses Built Phase 7 Capabilities
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py:206-219, 643-646`.
* **What happens**:
  `JARVIS-Repair-Plan.txt` (`7-A2`, line 3034 and `PHASE 7 MUST KNOW`, line 298) explicitly required removing `"brightness"`, `"bluetooth"`, and `"microphone"` from `UNBUILT_CAPS` (or folding `UNBUILT_CAPS` into `ACTION_TABLE`) once Phase 7 built those capabilities. Instead, `UNBUILT_CAPS` at `routing.py:206-214` still contains:
  ```python
  UNBUILT_CAPS = {
      "brightness": r"brightness|brighter|dimmer|dim|darker",
      "bluetooth": r"bluetooth|headphones|earbuds|airpods",
      "wifi": r"wi-?fi|airplane mode|flight mode|hotspot",
      "display": r"wallpaper|(?:desktop )?background|resolution|screen ?saver",
      "microphone": r"microphone|mic",
      "account": r"hibernat\w*|sign (?:me )?out|log (?:me )?(?:off|out)",
      "keyboard light": r"keyboard (?:light|backlight)",
  }
  ```
  Any natural command phrasing for brightness, Bluetooth, or microphone that misses the rigid regexes at lines 475–580 falls through to lines 643–646 (`cap = UNBUILT.search(cmd) if UNBUILT_ASK.match(cmd) else None`), where it logs `capability: <cap> not built yet - said so` and returns `("say", None, None, "I can't do that yet.")` (`CANT`) instead of returning `NEAR_MISS` or reaching `fix_route()` / `interpret()`:
  * `route("dim the screen to 40")` -> `("say", None, None, "I can't do that yet.")`
  * `route("change the brightness")` -> `("say", None, None, "I can't do that yet.")`
  * `route("toggle bluetooth")` / `route("switch bluetooth")` -> `("say", None, None, "I can't do that yet.")`
  * `route("open microphone settings")` / `route("open brightness settings")` (when `StartApps.txt` exists) -> `("say", None, None, "I can't do that yet.")` (because `"open"` is in `UNBUILT_ASK` and `"microphone"`/`"brightness"` are missing from `names` at lines 519–523!).

#### BUG-P7-03 (Medium): Brightness and Microphone Step Regexes Reject `"by N"` Step Amounts and `"dim/brighten to N"`
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py:551-580`.
* **What happens**:
  Speaker volume (`routing.py:598-608`) supports stepping by an explicit number (`"turn it up by 20"`, `"lower the volume by 5 percent"`). However:
  1. Brightness (`routing.py:553-563`) only accepts `set|turn|change|put|bring ... brightness ... to N` (rejecting `"dim the screen to 40"` or `"brighten the screen to 80"`), and its step regex (`lines 558-561`) only accepts `{bit}$` (`"a bit"`, `"a little"`, `"slightly"`), rejecting `"by 20"` / `"by 20%"`.
  2. Microphone level (`routing.py:576-580`) also only accepts `(?: (?:a )?(?:bit|little|tad)| slightly)?$`, rejecting `"turn the microphone up by 20"` or `"lower the mic volume by 15%"`.
  Combined with **BUG-P7-02**, all of those phrases return `"I can't do that yet."`.

#### BUG-P7-04 (High): `undo_last()` Mutes an Already-Unmuted Microphone While Saying `"Microphone unmuted."`
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:220-227`.
* **What happens**:
  Compare `undo_last()` for `mic_*` (`lines 220-227`) against `volume`/`mute`/`unmute` (`lines 228-233`):
  ```python
  if what.startswith("mic_"):                                # 7a: put the microphone back as it was read before
      was_muted, percent = before
      ok = (run_action("mic_level", ("set", percent)) if what == "mic_level"
            else run_action("mic_mute", None, ("mic_mute", None)) if what == "mic_unmute" else run_action("mic_unmute", None))
      undo.clear()
      if not ok:
          return "That didn't work."
      return f"Microphone back at {mic_volume()[1]} percent." if what == "mic_level" else "Microphone muted." if was_muted else "Microphone unmuted."
  ```
  When `what` is `"mic_mute"` or `"mic_unmute"`, `before` is `(was_muted, percent)` read from Windows before the action ran.
  * Line 223 ignores `was_muted` and dispatches `run_action("mic_mute", ...)` whenever `what == "mic_unmute"`, even if the microphone was already unmuted (`was_muted == False`) before the user said `"unmute the microphone"`.
  * Then line 227 formats the spoken response using `was_muted` (`"Microphone muted." if was_muted else "Microphone unmuted."`) instead of reading back `mic_volume()[0]`!
  * Result: If the mic was unmuted (`was_muted = False`), and the user says `"unmute the microphone"` followed by `"undo"`, JARVIS **mutes the microphone** (cutting off the user's voice input without confirmation!) while telling the user **`"Microphone unmuted."`**.

#### BUG-P7-05 (High): `7-A8` (`act_open` Focus Running App) and `close <App>` Fail on MixedCase `.exe` Paths and Multi-Word App Names
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/actions.py:44-53, 370-377`, `jarvislib/routing.py:618-624`, and `Scripts/ShipCore.cs:219`.
* **What happens**:
  1. **Case-sensitivity mismatch (`actions.py:372-374` vs `ShipCore.cs:219`)**:
     In `ShipCore.cs:219`, `ExeOf()` writes all window executable names to `Data\windows.txt` in lowercase (`Path.GetFileName(sb.ToString()).ToLowerInvariant()`, e.g. `W notepad.exe`, `W code.exe`).
     In `actions.py:372-374`:
     ```python
     exe = os.path.basename(app[1]) if app[1].lower().endswith(".exe") else running_window(app[0])
     core = os.path.join(RES, "Bin", "ShipCore.exe")
     if exe and exe in open_windows() and os.path.exists(core):
     ```
     Because `os.path.basename(app[1])` preserves the case from `StartApps.txt` (e.g. `"Notepad.exe"`, `"Code.exe"`, `"Spotify.exe"`), `exe in open_windows()` performs a case-sensitive check against lowercase `["notepad.exe", "code.exe"]`, evaluates to `False`, and launches a duplicate instance instead of focusing the running window.
  2. **Multi-word Start Menu display names fail in `running_window()` (`actions.py:44-53`)**:
     For apps whose `StartApps.txt` AppID does not end in `.exe` (such as `Google Chrome|Chrome`, `Microsoft Edge|MSEdge`, `Visual Studio Code|Microsoft.VisualStudioCode`), `act_open()` calls `running_window(app[0])` with the full display name (`"Google Chrome"`, `"Microsoft Edge"`, `"Visual Studio Code"`).
     In `running_window(name)`, `want` is `"googlechrome"`, `"microsoftedge"`, or `"visualstudiocode"`, which is compared against `stem` (`"chrome"`, `"msedge"`, `"code"`) using only `s == want`, `s.startswith(want)`, and `want in s`. None of those match when `want` is longer than `stem`!
     Thus, `act_open(("Google Chrome", "Chrome"))` never focuses an already-open Chrome window (`LIVE TEST 1b-12`), and saying `"close Google Chrome"` or `"close Visual Studio Code"` (`routing.py:619`) fails with `"I don't see google chrome open."`.

#### BUG-P7-06 (High): Synchronous `bt_devices()` PowerShell C# Compilation Inside `route()` + Uncaught `TimeoutExpired`
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py:494-517`, `jarvislib/actions.py:209-227`, and `jarvis.py:130, 688`.
* **What happens**:
  1. `bt_devices()` (`actions.py:217`) calls `_bt_ps("[Bt]::List()", timeout=40)`, which spawns `powershell.exe` and compiles 30 lines of inline C# (`Add-Type`) against `bthprops.cpl`.
  2. `route()` calls `bt_devices()` synchronously (`routing.py:496, 506`). Because `route()` is treated as a pure, zero-cost matcher across the codebase, a single utterance like `"connect my headphones"` in a follow-up window triggers `directed()` (`jarvis.py:688` -> calls `route()`), `understand()` (`jarvis.py:736` -> calls `route()`), `fix_route()` (`routing.py:264` -> calls `route()` up to 15 times in a loop if `route()` returned `chat`/`NEAR_MISS`), and then `run_action()` (`jarvis.py:130` -> calls `bt_devices()` again to record `before`)!
  3. In `routing.py:497, 507`, `try: devs = bt_devices() except OSError:` only catches `OSError`. In Python, `subprocess.TimeoutExpired` inherits from `SubprocessError(Exception)`, **not** `OSError`, so a PowerShell timeout crashes `route()` and aborts the turn with a raw traceback.

#### BUG-P7-07 (Medium): Voice Stealth Activation Speaks `"Done."` Out Loud and Opens a Follow-Up Window
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:920, 1068-1071` and `jarvislib/routing.py:472-473`.
* **What happens**:
  * `JARVIS-Repair-Plan.txt` (`LIVE TEST 1b-13`, line 3333) specifies:
    `1b-13. Stealth: "stealth mode" -> he asks -> "yes" -> the HUD goes to STEALTH and he answers in the pop-up only. He cannot undo it by voice; leave it in the Control Center.`
  * In `exchange()` (`jarvis.py:920`), `quiet = muted()` is evaluated before `ask_yes()`. When `run_action("stealth", None, pending=("stealth", None))` succeeds at line 1068, `quiet` is still `False`.
  * Line 1071 calls `fixed("Done.")` with `quiet = False`, so JARVIS **speaks `"Done."` out loud** after entering stealth mode and sets `left["again"] = "ear"` (opening the microphone for a 10s follow-up turn while in stealth mode, which then immediately aborts at `if tier >= 3: return` once `PerfTier` updates).
  * Furthermore, if the user says `"turn off stealth mode"`, `"exit stealth mode"`, or `"disable stealth mode"`, `routing.py:472` only matches entering stealth mode, so leaving stealth mode falls through to `chat` (the LLM) instead of returning a fixed explanation (`"I can't leave stealth mode by voice; turn it off in the Control Center."`).

#### BUG-P7-08 (Low): `undo_last()` Pollutes `did` History with Reverse Actions and Fails on Windows `"mixed"` Theme
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:130, 194-233` and `jarvislib/actions.py:88-101`.
* **What happens**:
  1. In `undo_last()`, undoing reminders or memory facts (`lines 235-298`) calls `did_add("undo")` (`"undid the last change"`). Undoing any `ACTION_TABLE` action (`lines 194-233`: `bluetooth`, `btlink`, `power`, `theme`, `brightness`, `micdev`, `mic_*`, `volume`, `mute`, `unmute`) calls `run_action(...)`, which calls `did_add(action, target)` (recording a new forward action instead of `"undo"` in `did`, and calling `problem()` on failure in addition to returning `"That didn't work."`).
  2. Windows 10/11 defaults to a `"mixed"` theme on many installations (Dark system taskbar `SystemUsesLightTheme = 0`, Light app windows `AppsUseLightTheme = 1`). When `theme_mode()` reads `{0, 1}`, it returns `"mixed"`. If the user switches to `"dark"` mode and then says `"undo"`, `undo_last()` (`jarvis.py:209`) checks `ok = before != "mixed" and run_action("theme", before)`, returning `"That didn't work."` instead of restoring the `(AppsUseLightTheme, SystemUsesLightTheme)` pair.

### Section 1.2 — Phase 8 Bugs (`FOLLOW-UP TIMING AND SOUNDS`: `8a`..`8d`, `8-A1`..`8-A6`)

#### BUG-P8-01 (High): Conversational Offer Confirmations (`room`, `closing`, `fact`) Bypass Whisper Confidence, Channel, and Timeout Guards
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:938-954, 1003, 1055, 1154, 1157`.
* **What happens**:
  In `ask_yes()` (`jarvis.py:780-799`), every direct command confirmation enforces three safety invariants:
  1. `heard_score[0] >= -1.0` (`P0-02` / `INV-7`: a low-confidence cough or mumble transcribed by Whisper as `"Okay."` never confirms).
  2. Same-channel confirmation (`8d` / `8-A6`: a voice ask cannot be confirmed by a typed turn and vice versa).
  3. A 15-second expiration window (`expires = time.time() + 15`).
  However, in `exchange()` (`jarvis.py:938-954`), the three offer handlers:
  ```python
  fact = offer.pop("fact", None) if time.time() < offer.get("expires", 0) else None
  room = offer.pop("room", None) if time.time() < offer.get("expires", 0) else None
  closing = offer.pop("close", None) if time.time() < offer.get("expires", 0) else None
  offer.clear()
  plain = " ".join(re.sub(r"[^a-z]+", " ", strip_name(text).lower()).split())
  if room and is_yes(text):                              # "Are you talking to me, sir?" "Yes": answer what was said
      text = room
  if closing and is_yes(text):                           # 9e: the yes to "Want me to close it?" is the confirmation
      way.update(kind="act", action="close", via="rule", lane="command")
      ok = run_action("close", closing, pending=("close", closing))
  ```
  check **only `is_yes(text)`**!
  * If JARVIS asks `"chrome is using 80% of the CPU. Want me to close it?"` and the user coughs 4 seconds later (`transcribe()` outputs `"Okay."` with `heard_score[0] = -1.6`), `closing and is_yes(text)` is `True` and **JARVIS kills `chrome.exe` without asking `"Did you say: Okay.?"`**.
  * Likewise, if a low-confidence noise is transcribed as `"Okay."` after `"Are you talking to me, sir?"` or `"Want me to remember that?"`, JARVIS executes the room speech or saves the unverified memory fact.
  * Additionally, `offer` does not record `typed=typed_turn[0]`, allowing cross-channel confirmation between voice and `TYPE TO HIM`.

#### BUG-P8-02 (High): Three Defects in `8d` (`TYPE TO HIM` / `ASK` Command Handling)
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:780-785, 1616-1623`.
* **What happens**:
  1. **Typed `"ask"`-risk commands immediately self-cancel (`jarvis.py:782-785, 1067-1075`)**:
     `JARVIS-Repair-Plan.txt` (`8d`, line 3517) states: *"a 'yes' for a confirmation must come from the same channel (typed question -> typed yes, or a click)."*
     However, when the user types `"lock my computer"` or `"close chrome"` or `"empty the recycle bin"` in Control Center > `TYPE TO HIM`, `exchange()` calls `ask_yes(prompt, quiet)`:
     ```python
     def ask_yes(prompt, quiet):
         reply_line(prompt, quiet)
         if typed_turn[0]:                                          # 8d: a typed ask is never confirmed by the microphone (other channel)
             log("confirm: typed turn - not confirmed, ask out loud")
             return False
     ```
     `ask_yes()` outputs `"You want me to lock the PC. Confirm with yes."`, immediately returns `False`, and `exchange()` (`line 1075`) immediately outputs `"Cancelled."` in the same turn! Because `pending` is not saved for a subsequent typed `"yes"`, **no `"ask"`-risk command can ever be confirmed via `TYPE TO HIM`**.
  2. **`busy.locked()` calls `reply_line()` on the `main()` loop thread (`jarvis.py:1620-1621`)**:
     ```python
     elif busy.locked():
         reply_line("One moment, I'm busy.", muted())
     ```
     Calling `reply_line()` on the `main()` loop thread while an active turn holds `busy` mutates `recent["me"]`, calls `filler_done()`, fights over `sounddevice.OutputStream` and `S.set(state="speaking")` if unmuted, or blocks the `main()` event loop for up to 3.0 seconds (`time.sleep`) and wipes `LIVE_FILE` (`live("")`) while the active turn is streaming its answer!
  3. **Hardcoded `tier=0` (`jarvis.py:1623`)**:
     `threading.Thread(target=turn, args=(0,), kwargs={"typed": text}, daemon=True).start()` passes `0` instead of `hud_tier()`, forcing `pick_model(0)` (the heavy model) even when the HUD is in `LITE` (`1`) or `LOW` (`2`) gaming tiers.

#### BUG-P8-03 (Medium): Dimmed Follow-Up Window Sets `state="idle"` While Holding `busy`, Breaking Orb Click-to-Cancel
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/mic.py:171-174` and `Skins/Spaceship/@Resources/Scripts/jarvis.lua:414-416`.
* **What happens**:
  In `_listen(patience=10, dim_after=3)` (`mic.py:171-173`):
  ```python
  if dim_after and not started and not dim and waited * 0.03 > dim_after:
      dim = True
      S.set(state="idle")                     # 8a: past the direct window the hologram shows STANDBY (name needed)
  ```
  During seconds 3–10 of the follow-up window, `jarvis.py` is still inside `listen()` holding the `busy` and `mic` locks, but `Data\jarvis.txt` now reports `STATE idle`.
  If the user clicks the HUD orb during seconds 3–10 (either to wake JARVIS without saying `"Jarvis"` or to stop him from listening), `jarvis.lua:415` checks:
  ```lua
  if js.state == 'idle' then command('WAKE ' .. os.time() .. ' ' .. H.tier); js.state = 'listening'
  else command('CANCEL ' .. os.time()) end
  ```
  Because `js.state == 'idle'`, `jarvis.lua` writes `WAKE` instead of `CANCEL`. `jarvis.py` receives `WAKE`, spawns `turn()`, and `turn()` immediately exits at `if not busy.acquire(blocking=False): return` (`jarvis.py:828`)! Meanwhile, the old follow-up `_listen()` is still in `dim = True` mode requiring `"Jarvis"` in front of whatever the user says next — even though the user just clicked the orb (`js.state = 'listening'` on screen)!

#### BUG-P8-04 (Medium): `8-A3` Follow-Up Mode Violation After Command Replies + `ear_wait()` Re-Evaluation Race
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:700-702, 874, 900, 936`.
* **What happens**:
  1. **Slice D / `8-A3` violation (`jarvis.py:936`)**:
     `JARVIS-Repair-Plan.txt` (`8-A3`, line 3468) states: *"8-A3 (P1-04) = 8a, but it OBEYS SLICE D: follow-ups after chat / info replies only, no cap, and after a command reply only the 5 s 'undo / remove' window. 8a's 3 s direct / 3-10 s name-prefixed timing stays."*
     In `jarvis.py:936`, `fixed()` sets `left["again"] = not quiet and not cancel.is_set() and not NO_FOLLOW.match(reply) and "ear"` for **all** command replies (unless the reply was `"Cancelled."` / `"Okay, never mind."`), keeping the mic open for the full 10s open-ear window after every command instead of distinguishing `"undo"` (5s undo/flip/correction window after commands) from `"ear"` (3s/10s open follow-up after chat/info/questions).
  2. **`ear_wait()` double-evaluation race (`jarvis.py:700-702, 874, 900`)**:
     `ear_wait()` returns `8.0` if `time.time() < offer.get("expires", 0)` or `recent["me"].endswith("?")`, else `follow_wait()` (`3.0`).
     In `exchange()`, `ear_wait()` is called at line 874 (`dim_after=ear_wait()`) and called **again** at line 900 (`if follow and onset[0] > ear_wait() and strip_name(text) == text:`) *after* `listen()` and `transcribe()` have finished (which takes 2–6 seconds). If `offer["expires"]` elapsed while the user was speaking or while Whisper was transcribing, `ear_wait()` was `8.0` when the user started speaking at `onset = 4.5s`, but evaluates to `3.0` at line 900 — falsely dropping the user's speech (`"ear: started late without his name - dropped"`).

#### BUG-P8-05 (Low): `8c` `"you can talk"` Falls Through to LLM Outside Class Events & Overlapping Event Edge Case
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/quiet.py:15-46` and `jarvis.py:977`.
* **What happens**:
  1. In `jarvis.py:977`:
     ```python
     if quiet_talk.TALK.fullmatch(said) and quiet_talk.talk():   # 8c: "you can talk" ends QUIET for this class only
         way.update(kind="quiet", via="rule")
         quiet = muted()
         fixed("Okay, I can talk." if not quiet else "Okay.")
         return
     ```
     If the user says `"you can talk"` or `"end quiet mode"` when no class event is currently running (`quiet_talk.talk()` returns `False`), line 977 does not match and sends `"you can talk"` to the LLM (`chat`).
  2. In `quiet.py:21-24`, `_current()` returns the `end` timestamp of the **first** matching event in `calendar.txt`. If two events on the quiet calendar overlap (e.g. a 09:00–10:00 lab and a 09:00–11:00 block), `_current()` returns the first one (`10:00`), so `_off[0]` is set to `10:00` instead of the latest running event's end time (`max`).

### Section 1.3 — Phase 9 Bugs (`ASK HIM WHAT IS WRONG / DIAGNOSIS`: `9-1`..`9-8`)

#### BUG-P9-01 (High): `is_protected()` Omits `OWN_MODEL` (`python`, `pythonw`, `ollama`) and `shipcore`
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/diag.py:192-200`, `jarvislib/routing.py:620`, and `jarvislib/actions.py:381-383`.
* **What happens**:
  In `diag.py:192-200`:
  ```python
  PROTECTED = frozenset({"explorer", "svchost", "csrss", "wininit", "winlogon", "lsass", "services", "smss", "dwm", "system",
                         "registry", "fontdrvhost", "sihost", "ctfmon", "audiodg", "msmpeng", "searchhost", "taskhostw",
                         "rainmeter", "jarvis"})
  OWN_MODEL = frozenset({"ollama", "python"})

  def is_protected(name):
      return re.sub(r"\.exe$", "", str(name or "").lower()) in PROTECTED
  ```
  While `findings()` (`diag.py:208`) checks `not is_protected(app) and app not in OWN_MODEL`, both `route()` (`routing.py:620`) and `act_close()` (`actions.py:382`) check **only `is_protected(exe)`**!
  Because `python`, `pythonw`, `ollama`, `ollama app`, and `shipcore` are **not** in `PROTECTED`, saying `"close python"`, `"kill ollama"`, or `"close shipcore"` runs `taskkill /IM python.exe` / `ollama.exe` / `ShipCore.exe`, terminating JARVIS, Ollama, or the HUD's background service!

#### BUG-P9-02 (High): `diag.ps1` Overwrites Multi-Process Instances Because `$x.InstanceName` Lacks `#N` Disambiguators
* **Where**: `Skins/Spaceship/@Resources/Jarvis/diag.ps1:21-37` and `jarvislib/diag.py:141-165`.
* **What happens**:
  In Windows PowerShell 5.1 `Get-Counter`, when multiple processes share a name (e.g. 30 `chrome.exe` or `svchost.exe` processes), PDH formats the instance index `#1`, `#2` inside `$x.Path` (`\\machine\process(chrome#1)\id process`), whereas `$x.InstanceName` is just `"chrome"` for **every single instance**!
  Because `diag.ps1` keys `$by` by `$i` (`$x.InstanceName`), all 30 `chrome` processes collide on `$by['chrome']`, overwriting `cpu`, `mem`, `io`, and `pid` so only the **last** Chrome process's metrics and PID survive in `procs`!
  Consequently:
  1. `top_apps()` (`diag.py:141`) sees 1 `chrome` process instead of summing all 30 Chrome processes.
  2. `gpu_apps()` (`diag.py:155`) maps GPU usage (`\GPU Engine(pid_1234_...)\Utilization Percentage`) to app names by looking up `pid` in `procs`. Because 29 of the 30 Chrome PIDs (including Chrome's GPU sub-process!) were overwritten in `$by['chrome']`, `names.get(x.get("pid"))` returns `None` and **Chrome's GPU utilization is invisible to `gpu_apps()`**!

#### BUG-P9-03 (Medium): `diagnose()` Spawns `diag.ps1 -Part logs -Hours 720` Twice When `span == "boot"`
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/diag.py:345-348, 374-380`.
* **What happens**:
  When the user asks `"what crashed since the last restart"` (`span == "boot"`), `gather("crash", 720, own_cpu)` runs `snapshot("logs", 720)` (`powershell.exe -File diag.ps1 -Part logs -Hours 720`), groups events without `since=lg.get("boot")`, and discards raw timestamps. Immediately afterward, `diagnose()` (`line 379`) calls `lg = snapshot("logs", 720)` **a second time**, spawning a second PowerShell `Get-WinEvent` process over 30 days of logs just to pass `since=snap["boot"]`.

#### BUG-P9-04 (Medium): Silent `watch()` Always Spawns a 3.5s PowerShell `processes` Snapshot Even for Disk/Temp Trips
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/diag.py:455-498`.
* **What happens**:
  When any trip in `watch_trips()` persists for 3 checks (`WATCH_NEED = 3`), `watch()` spawns `name_it()`, which unconditionally runs `gather("cpu", 24, False)` (a 3.5s PowerShell `Get-Counter` sample) even when the trip was `"drive C is nearly full"` or `"the GPU is hot"`.

#### BUG-P9-05 (Low): `summary(snap)` Reports `"disk fine"` Without Checking Disk Thresholds
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/diag.py:263-269`.
* **What happens**:
  `summary(snap)` appends `"disk fine"` whenever `snap.get("disks")` is non-empty, without verifying that no drive in `snap["disks"]` has `free_gb < T["disk_gb"]` or `100 * free_gb / total_gb < T["disk_pct"]`.

### Section 1.4 — AI Industry Benchmark Edge-Case Evaluation Findings (`BUG-EDGE-01`..`07`)

To stress-test JARVIS against the edge cases used by frontier AI teams, we modeled an evaluation suite (`test_industry_edge_cases.py`) on five industry benchmarks:
1. **[Berkeley Function-Calling Leaderboard (BFCL v3/v4)](https://www.google.com/search?q=https%3A%2F%2Fwww.emergentmind.com%2Ftopics%2Fberkeley-function-calling-benchmark-bfcl)** ([OpenReview Paper](https://www.google.com/search?q=https%3A%2F%2Fopenreview.net%2Fpdf%3Fid%3D2GmDdhBdDk)) and **[Adversarial Function Calling (ADC)](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fhtml%2F2412.17754v2)**: Tests parallel/multi-intent utterances, negation/refusal traps, and parameter hallucination when arguments are omitted.
2. **[Apple ToolSandbox](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2408.04682)**: Tests stateful tool invariants, impossible/out-of-bounds parameter values, and implicit state dependencies.
3. **[Apple Spoken Language Understanding (SLU) Disfluency \& Self-Repair Benchmarks](https://www.google.com/search?q=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F370156965_From_User_Perceptions_to_Technical_Improvement_Enabling_People_Who_Stutter_to_Better_Use_Speech_Recognition)**: Tests mid-sentence corrections (`"no wait"`, `"actually"`, `"I mean"`), repetitions, and Whisper ASR homophones.
4. **[Sierra τ-bench (Tau-Bench)](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2406.12045)** ([HTML Paper](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fhtml%2F2406.12045v1)): Tests multi-turn policy compliance, confirmation flow reversals (`"yes wait no"`), and relative vs. absolute numeric updates (`"from X to Y"`).
5. **[OpenAI Instruction Hierarchy](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2404.13208)** & **[OWASP Top 10 for LLM (LLM01 Prompt Injection)](https://www.google.com/search?q=https%3A%2F%2Fmedium.com%2F%40shivayadav2820%2Fowasp-top-10-for-ai-blog-1-prompt-injection-the-mother-of-all-ai-attacks-3af23412ff6d)**: Tests indirect prompt injections via calendar/todo/note data.

#### BUG-EDGE-01 (High): Mid-Utterance Self-Repair Executes the Aborted First Value (`routing.py:658-669`, `reminders.py:65-72`)
* **Benchmark Source**: [Apple SLU Disfluency \& Self-Repair](https://www.google.com/search?q=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F370156965_From_User_Perceptions_to_Technical_Improvement_Enabling_People_Who_Stutter_to_Better_Use_Speech_Recognition).
* **What happens**:
  In voice interfaces, users frequently correct themselves mid-breath without pausing long enough to end the recording:
  * `understand("set the volume to 40 no wait 60")` -> returns `('act', 'volume', ('set', 40), None)` (sets volume to **40** instead of **60**!).
  * `understand("set brightness to 80 actually 30")` -> returns `('act', 'brightness', ('set', 80), None)` (sets brightness to **80** instead of **30**!).
  * `understand("set a timer for 10 minutes no wait 5 minutes")` -> returns `('remind', 'set', ('timer', 600, ...))` (sets a **10-minute** timer instead of **5 minutes**!).
  * `understand("open calculator no wait notepad")` -> returns `NEAR_MISS` (`"I couldn't find calculator no wait notepad installed."`).
  **Root Cause**: `_num()` (`routing.py:130`) scans tokens left-to-right and returns the **first** number (`40`, `80`) while ignoring `"no wait 60"` or `"actually 30"`. Similarly, `reminders.when()` (`reminders.py:65`) matches the first `in (\d+) minutes` (`10`) and leaves `"no wait"` inside the timer's label!

#### BUG-EDGE-02 (High): Compound Multi-Action Commands Silently Drop or Corrupt the Second Action (`routing.py:663-678`)
* **Benchmark Source**: [BFCL Multi-Function / Parallel Calling](https://www.google.com/search?q=https%3A%2F%2Fwww.emergentmind.com%2Ftopics%2Fberkeley-function-calling-benchmark-bfcl).
* **What happens**:
  In `understand()` (`routing.py:661-678`), `res = fix_route(text)` is called **before** the `" and "` / `" then "` splitter (`lines 664-678`). The splitter only runs if `res[0] == "chat"`!
  Whenever the first command's regex uses a greedy `(.+)` capture that matches across `" and ..."`, `route()` succeeds on the whole string and the second command is either silently dropped or stuffed into the first command's text argument:
  * `understand("set a timer for 5 minutes and mute")` -> `reminders.when()` strips `"for 5 minutes"` and treats `"set a timer and mute"` as the timer label (`label = "and mute"`), **never muting the speakers**!
  * `understand("add buy milk to my todo list and open calculator")` -> `routing.py:424` matches `add (.+?) to my to-do list` or `add (.+)`, adding `"buy milk to my todo list and open calculator"` as a to-do item and **never opening Calculator**!
  * `understand("mute the volume and turn on dark mode")` -> `routing.py:482` (`turn on (dark|light) mode`) uses `re.search` instead of `re.match`, so it matches `"turn on dark mode"` inside the whole string and **silently drops `"mute the volume"`**!

#### BUG-EDGE-03 (High): Negated Commands Bypass `DONT_DO` When Prefixed, and Contradictory Confirmations (`"yes don't"`) Execute Destructive Actions (`routing.py:25-33, 275-279`, `jarvis.py:772-799`)
* **Benchmark Source**: [BFCL Irrelevance / Abstention](https://www.google.com/search?q=https%3A%2F%2Fopenreview.net%2Fpdf%3Fid%3D2GmDdhBdDk) & [Sierra τ-bench Policy Safety](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2406.12045).
* **What happens**:
  1. **Prefixed Negation Trap (`"just don't lock my computer"`)**:
     In `routing.py:25`:
     `DONT_DO = re.compile(r"^(?:do not|don t|dont|never|stop)\b")`
     If the user says `"just don't lock my computer"` or `"hey don't lock my computer"` or `"actually don't mute the mic"`, `DONT_DO` fails because `"don't"` is not at index 0 (`^`)! Worse still, `fix_route()` (`routing.py:276`) then strips two leading words (`w[1:]` / `w[2:]`), stripping `"just don't"` and leaving `"lock my computer"`, which **routes to `('act', 'lock', None, ...)` and locks the PC**!
  2. **Contradictory Confirmation Trap (`"yes wait no"`, `"yes don't"`, `"sure never mind"`)**:
     In `jarvis.py:772-774`:
     `YES_WORD = re.compile(r"(?:yes|yeah|yep|yup|sure|ok|okay|do it|go ahead|confirm|affirmative|please)\b.*")`
     Because `YES_WORD` ends with `\b.*` and `is_yes()` never checks for negation/cancellation words (`no`, `not`, `don't`, `wait`, `stop`, `cancel`, `never mind`), saying `"yes wait no"`, `"yes don't do it"`, or `"sure never mind"` during `ask_yes()` returns **`is_yes() == True`** and immediately executes `"ask"`-risk actions (`shutdown`, `restart`, `recycle`, `close`, `forget_all`)!

#### BUG-EDGE-04 (High): Out-of-Bounds Calendar Dates Raise Uncaught `ValueError` in `reminders.when()` (`reminders.py:49-108`)
* **Benchmark Source**: [Apple ToolSandbox](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2408.04682).
* **What happens**:
  In `reminders.py:57-58, 93-95`:
  ```python
  md = re.search(rf",? (?:on )?(?:({'|'.join(MONTHS)}) (\d{{1,2}})(?:st|nd|rd|th)?|(\d{{1,2}})/(\d{{1,2}}))(?: at)? ", s)
  ...
  due = base.replace(month=mon, day=day, hour=hour, minute=minute)
  ```
  If the user (or Whisper ASR) says an invalid date such as `"remind me on February 30 at 9am to pay rent"`, `"remind me on April 31 at 5pm"`, or `"remind me on 2/29 at 9am"` in a non-leap year, `base.replace(month=mon, day=day)` raises an uncaught `ValueError: day is out of range for month`, crashing `route()` and aborting the turn!

#### BUG-EDGE-05 (Medium): `"from X to Y"` Numeric Commands Set the Old Value `X`, and Fractional Hour Timers Fail (`routing.py:553-609`, `reminders.py:65-72`)
* **Benchmark Source**: [Sierra τ-bench](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2406.12045).
* **What happens**:
  1. When a user says `"change volume from 30 to 50"` or `"set brightness from 80 to 40"`, the regex `set|turn|change ... (?:to|at) (.+)` matches the first `"to"` or `_num()` extracts the **first** number in the capture group (`30` or `80`), setting the volume/brightness to the value it was already at (`30` / `80`) instead of the target (`50` / `40`)!
  2. When a user says `"set a timer for half an hour"` or `"remind me in a quarter of an hour to check the oven"`, `reminders.when()` (`reminders.py:65`) fails because it only matches integers/number words before `hours?|minutes?|seconds?`, sending `"set a timer for half an hour"` to `chat`.

#### BUG-EDGE-06 (Medium): Whisper ASR Split-Word & Homophone Artifacts Fail Rule Routing (`routing.py:25-44`)
* **Benchmark Source**: [Apple SLU ASR Robustness](https://www.google.com/search?q=https%3A%2F%2Fwww.researchgate.net%2Fpublication%2F370156965_From_User_Perceptions_to_Technical_Improvement_Enabling_People_Who_Stutter_to_Better_Use_Speech_Recognition).
* **What happens**:
  `faster-whisper` (`base.en` / `small.en`) frequently produces split compound words or homophones on fast speech:
  * `"turn on blue tooth"` / `"disconnect blue tooth"` (`blue tooth` with a space instead of `bluetooth`) -> misses Bluetooth rules and falls through to `chat`.
  * `"take a screen shot"` (`screen shot` with a space) -> misses `screenshot` in `routing.py:528` (`take a screenshot`).
  * `"un mute the microphone"` / `"un mute"` (`un mute` with a space) -> misses `unmute` and matches `mute` instead (inverting the user's command!).
  * `"set volume to fourty"` (`fourty` spelling) or `"set volume to to"` / `"set volume to too"` (homophone for `2`) -> fails `_num()`.

#### BUG-EDGE-07 (Medium): Stage-3 LLM `interpret()` Accepts Hallucinated Numeric Arguments When User Uttered None (`routing.py:345-391`)
* **Benchmark Source**: [BFCL Hallucination Detection](https://www.google.com/search?q=https%3A%2F%2Fwww.emergentmind.com%2Ftopics%2Fberkeley-function-calling-benchmark-bfcl) & [ADC Adversarial Function Calling](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fhtml%2F2412.17754v2).
* **What happens**:
  In `interpret()` (`routing.py:372-383`), when the local LLM classifies a fuzzy command into JSON (`{"action": "volume", "target": 50}` or `{"action": "brightness", "target": 80}`), `interpret()` checks `0 <= int(target) <= 100`, but **never checks whether the user's utterance actually contained a number**! Small 3B/8B models under `format="json"` frequently hallucinate a default integer (`50` or `80`) when the user says `"adjust the volume"` or `"change the brightness"`, causing JARVIS to jump to a random volume/brightness level instead of stepping by 10 or asking.

### Section 1.5 — Comparable Voice Assistant & Model Complaint Audit (`BUG-COMP-01`..`07`)

To identify real-world failure modes in production systems that share JARVIS's exact software stack and feature designs, we audited user and developer complaints across **7 comparable voice assistant architectures** and tested each complaint against JARVIS (`test_similar_system_complaints.py`).

#### Comparable Systems & Shared Feature Matrix

| JARVIS Subsystem | JARVIS Implementation | Comparable Models & Assistants Audited | Customer / Developer Complaint Audited | Status in JARVIS |
| :--- | :--- | :--- | :--- | :--- |
| **Wake Word & Barge-In** | `openWakeWord` (`hey_jarvis_v0.1.onnx`) + Silero VAD (`vad_threshold=0.5`) in `jarvis.py:1218-1510` | [dscripka/openWakeWord (hey\_jarvis)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fdscripka%2FopenWakeWord%2Fblob%2Fmain%2Fdocs%2Fmodels%2Fhey_jarvis.md), [ESPHome / Home Assistant Voice PE (#219)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fesphome%2Ffirmware%2Fissues%2F219), [M5 Atom Echo Wake Word](https://www.google.com/search?q=https%3A%2F%2Fcommunity.home-assistant.io%2Ft%2Fm5-atom-echo-wake-word-not-working%2F625957), [Raspberry Pi 5 openWakeWord](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FCarbonRaven%2Ftele-ai%2Fblob%2Fmain%2Fdocumentation%2Fraspberry-pi-5-openwakeword.md) | 1. Wake word stops working after first turn if audio stream isn't reset.<br>2. `model.reset()` does **not** clear `model.vad.prediction_buffer`, causing stale Silero VAD state on next listen.<br>3. Continuous speech with zero gap (`"Hey Jarvis what time is it"`) loses first word after wake word. | 1. **Guarded** (stream reopened per turn).<br>2. **VULNERABLE (`BUG-COMP-04`)**.<br>3. **Guarded** (`pre` ring buffer in `wake_loop` passes 10 chunks into `turn`). |
| **Microphone Capture & Energy VAD** | `sounddevice.InputStream` + dynamic RMS noise floor (`floor`) in `jarvislib/mic.py:123-199` | [Python SpeechRecognition (adjust\_for\_ambient\_noise)](https://www.google.com/search?q=https%3A%2F%2Fstackoverflow.com%2Fquestions%2F66070703%2Fwhy-is-my-python-speechrecognition-listen-not-stopping-to-record), [RealtimeSTT (KoljaB/RealtimeVoiceChat)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FKoljaB%2FRealtimeVoiceChat), [python-sounddevice (#173)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fspatialaudio%2Fpython-sounddevice%2Fissues%2F173) | 1. Speaking immediately on frame 0 locks the noise floor to the user's voice (`thresh = 3 * rms`), dropping the whole sentence.<br>2. HVAC/fan noise spike raises `floor` permanently during a listen.<br>3. USB/Bluetooth headset hot-plug fails until PortAudio re-initializes (`#173`). | 1. **VULNERABLE (`BUG-COMP-01`)**.<br>2. **VULNERABLE (`BUG-COMP-01`)**.<br>3. **VULNERABLE (`BUG-COMP-07`)**. |
| **STT (`faster-whisper`)** | `faster-whisper` (`base.en`, `int8`, `vad_filter=True`, `condition_on_previous_text=False`, `initial_prompt=HINT`) in `jarvislib/hearing.py` | [faster-whisper Hallucination Analysis](https://www.google.com/search?q=https%3A%2F%2Flocalaimaster.com%2Fblog%2Fwhisper-hallucination-fix), [Open-LLM-VTuber](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FSnowfork%2FOpen-LLM-VTuber%2Fblob%2Faidan_fixes%2FREADME.md), [myOfflineAi-VoiceAssistant](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fvbookshelf%2FmyOfflineAi-VoiceAssistant) | 1. Whisper loops repeating phrases when `condition_on_previous_text=True`.<br>2. Whisper echoes `initial_prompt` (`HINT`) or YouTube outros (`"Please subscribe"`, `"Amara.org"`) on short noise bursts. | 1. **Guarded** (`condition_on_previous_text=False` at `hearing.py:102`).<br>2. **Partially Guarded -> `REC-02`** (`PHANTOM` catches `"thanks for watching"`, misses `HINT` echo & `"please subscribe"`). |
| **TTS (`kokoro-onnx` + Sentence Streamer)** | `kokoro-onnx` + `sentences_from()` regex splitter in `jarvislib/speech.py:150-245` | [RealtimeTTS (KoljaB/RealtimeVoiceChat HN Thread)](https://www.google.com/search?q=https%3A%2F%2Fnews.ycombinator.com%2Fitem%3Fid%3D43899028), [Kokoro-FastAPI Local TTS](https://www.google.com/search?q=https%3A%2F%2Flocalaimaster.com%2Fblog%2Flocal-tts-api-server-kokoro-fastapi), [Open-LLM-VTuber](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FSnowfork%2FOpen-LLM-VTuber%2Fblob%2Faidan_fixes%2FREADME.md) | 1. Sentence streamer splits on `"Mr."`, `"Dr."`, `"St."`, `"vs."`, `"e.g."`, causing awkward mid-sentence pauses.<br>2. Markdown asterisks (`**bold**`), backticks, or URLs read aloud literally. | 1. **VULNERABLE (`BUG-COMP-02`)**.<br>2. **Guarded** (`clean_for_speech()` in `speech.py:72-95` strips markdown/symbols). |
| **Hybrid Rule + Local LLM Routing (`Ollama`)** | 3-stage router (`route()` -> `fix_route()` -> `interpret()` / `ask_llm()`) in `routing.py` & `llm.py` | [Home Assistant Assist ("Prefer handling commands locally" + Ollama)](https://www.google.com/search?q=https%3A%2F%2Fcommunity.home-assistant.io%2Ft%2Fprefer-handling-commands-locally-during-continued-conversation%2F883012), [HA Ollama Latency Spike (#169315)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fhome-assistant%2Fcore%2Fissues%2F169315), [HA Local AI Blog](https://www.google.com/search?q=https%3A%2F%2Fwww.home-assistant.io%2Fblog%2F2025%2F09%2F11%2Fai-in-home-assistant%2F) | 1. Unrecognized command phrasing falls through to slow LLM or `UNBUILT_CAPS`.<br>2. Switching between heavy (8B) and fast (3B) Ollama models keeps both in VRAM (`keep_alive`), causing CPU fallback (`#947662`). | 1. **VULNERABLE (`BUG-P7-02`, `BUG-COMP-03`)**.<br>2. **Potential VRAM Contention -> `REC-04`**. |
| **Alarms, Timers & Reminders** | `jarvislib/reminders.py` + `alarm()` loop in `jarvis.py:497-554` + `mic.duck()` | [OpenVoiceOS ovos-skill-alerts](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FOpenVoiceOS%2Fovos-skill-alerts), [Mycroft skill-alarm](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FMycroftAI%2Fskill-alarm), [Amazon Alexa Nearest-Time / Post-Midnight Complaints](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Falexa%2Fcomments%2F1h8gau9%2Fis_there_anyway_to_make_alexa_assume_the_nearest%2F), [Alexa Next-Day Alarm](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Falexa%2Fcomments%2F1rmgujx%2Ftried_to_set_an_alarm_for_the_next_day%2F), [Apple Siri Alarm Complaints](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2FSiri%2Fcomments%2F1wsewt6%2Fi_asked_siri_for_a_740_pm_alarm_four_different%2F), [Google Home Midday/Midnight](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fgooglehome%2Fcomments%2F6uvbnj%2Fsetting_an_alarm_for_midday%2F) | 1. Asking `"how much time is left on my <name> timer"` fails to match named timers.<br>2. Alarm loop ducks/unducks master system volume every 2s.<br>3. `"12pm"` / `"12am"` noon/midnight confusion.<br>4. Saying `"set an alarm for 8am"` at 9am without AM/PM.<br>5. Saying `"set an alarm for 8am tomorrow"` at 12:30 AM sets it 31.5h away. | 1. **VULNERABLE (`BUG-COMP-03`)**.<br>2. **VULNERABLE (`BUG-COMP-05`)**.<br>3. **Guarded** (`12pm` -> `12:00`, `12am` -> `00:00`, `"noon"`/`"midnight"` work).<br>4. **Guarded** (`when()` advances `<= now` by `+1 day` and speaks `"tomorrow"`).<br>5. **Complex UX Edge Case -> `REC-01`**. |
| **Conversational Auto-Memory** | `learnable()` in `jarvis.py:311-325` + `jarvislib/memory.py` | OpenAI ChatGPT Memory & MemGPT / Letta local memory agents | Auto-learned facts (`"Want me to remember that?"` -> `"yes"`) append duplicate/contradictory facts (`"I live in Austin"` + `"I live in Chicago"`) instead of updating the existing slot. | **VULNERABLE (`BUG-COMP-06`)**. |

#### Detailed Breakdown of the 7 New Confirmed Bugs from Comparable Systems (`BUG-COMP-01`..`07`)

#### BUG-COMP-01 (High): Adaptive Noise Floor Lock-In When Speaking Immediately (`jarvislib/mic.py:150-161`)
* **Comparable Systems**: [Python SpeechRecognition (adjust\_for\_ambient\_noise)](https://www.google.com/search?q=https%3A%2F%2Fstackoverflow.com%2Fquestions%2F66070703%2Fwhy-is-my-python-speechrecognition-listen-not-stopping-to-record) and [RealtimeSTT (KoljaB/RealtimeVoiceChat)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FKoljaB%2FRealtimeVoiceChat). One of the most common complaints across Python energy-threshold voice assistants is that if a user starts speaking immediately after clicking the mic button or during a follow-up window (so frame 0 already contains the user's voice), the dynamic noise floor calibrates itself to the user's speech level and refuses to trigger speech onset.
* **Where in JARVIS**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/mic.py:150-161`:
  ```python
  rms = float(np.sqrt(np.mean(block * block)))
  if floor is None:
      floor = rms
  if not started:
      floor = 0.95 * floor + 0.05 * rms
  thresh = max(floor * 3.0, 0.012)
  if rms > thresh:
      if not started:
          onset[0] = round(waited * 0.03, 2)
      started = True
  ```
* **What happens (Verified in `test_similar_system_complaints.py`)**:
  If the user is already speaking in frame 0 (`rms = 0.10`):
  1. `floor` is initialized to `0.10`.
  2. `thresh = max(0.10 * 3.0, 0.012) = 0.30` (3x the user's voice RMS!).
  3. `if rms > thresh:` (`0.10 > 0.30`) evaluates to `False`!
  4. On every subsequent frame of the user's speech (`rms ≈ 0.10`), `started` remains `False` and `floor` remains `0.10`, so **the user's entire sentence is discarded as silence (`return None`)**!
  Even if the user starts speaking 100 ms later, if a transient noise (like setting down a mug or a cough in frame 0 with `rms = 0.08`) occurs on frame 0, `floor` starts at `0.08` (`thresh = 0.24`), making JARVIS deaf to normal speech (`rms = 0.06–0.12`) for several seconds until `0.95 ** N` decays!

#### BUG-COMP-02 (Medium): TTS Sentence Streamer Splits Mid-Sentence on Abbreviations and Titles (`jarvislib/speech.py:153`)
* **Comparable Systems**: [RealtimeTTS (KoljaB/RealtimeVoiceChat)](https://www.google.com/search?q=https%3A%2F%2Fnews.ycombinator.com%2Fitem%3Fid%3D43899028), [Kokoro-FastAPI](https://www.google.com/search?q=https%3A%2F%2Flocalaimaster.com%2Fblog%2Flocal-tts-api-server-kokoro-fastapi), and [Open-LLM-VTuber](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FSnowfork%2FOpen-LLM-VTuber%2Fblob%2Faidan_fixes%2FREADME.md). Users of sentence-streaming TTS wrappers around `kokoro-onnx` and `Piper` frequently complain that LLM outputs containing `"Mr."`, `"Dr."`, `"Mrs."`, `"Ms."`, `"St."`, `"vs."`, `"e.g."`, or `"i.e."` cause the TTS engine to treat the period after the abbreviation as the end of a sentence — synthesizing `"Hello Mister."` with a falling terminal cadence and a 300 ms gap before speaking `"Smith"`.
* **Where in JARVIS**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/speech.py:150-158`:
  ```python
  def sentences_from(pieces):
      buf = ""
      for piece in pieces:
          buf += piece
          while True:
              m = re.search(r"(.+?[.!?])(\s+|$)", buf)
              if not m or (m.group(2) == "" and len(buf) < 160):
                  break
  ```
* **What happens (Verified in `test_similar_system_complaints.py`)**:
  Passing `["Hello Mr. Smith, your meeting with Dr. Jones on Main St. is at 3:00 PM."]` into `sentences_from()` yields **four separate TTS chunks**:
  `['Hello Mr.', 'Smith, your meeting with Dr.', 'Jones on Main St.', 'is at 3:00 PM.']`
  Each chunk is synthesized as an isolated `kokoro.create()` call, producing choppy prosody and unnatural pauses.

#### BUG-COMP-03 (High): Named Timer Status Queries (`"how much time is left on my pasta timer"`) Fall Through to LLM (`jarvislib/reminders.py:214-218`)
* **Comparable Systems**: [OpenVoiceOS ovos-skill-alerts](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FOpenVoiceOS%2Fovos-skill-alerts), [Mycroft skill-alarm](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FMycroftAI%2Fskill-alarm), and Amazon Alexa. Users routinely label multiple timers (`"set a timer for 10 minutes for pasta"`, which JARVIS supports via `reminders.py:66`) and then ask `"how much time is left on my pasta timer"`, `"how long is left on the laundry timer"`, or simply `"how much time is left"`.
* **Where in JARVIS**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py:214-218`:
  ```python
  m = re.match(
      r"(?:what (?:are|is) my (reminder|timer|alarm)s?|do i have (?:any )?(reminder|timer|alarm)s?"
      r"|list (?:my )?(reminder|timer|alarm)s?|how (?:much time|long) (?:is |do i have )?left on (?:my |the )?(reminder|timer)s?)$",
      cmd
  )
  ```
* **What happens (Verified in `test_similar_system_complaints.py`)**:
  Because `left on (?:my |the )?(reminder|timer)s?$` allows **no label words** between `my/the` and `timer`, and requires `on my timer` at the end:
  * `route("how much time is left on my pasta timer")` -> `('chat', None, None, None)`!
  * `route("how long is left on the laundry timer")` -> `('chat', None, None, None)`!
  * `route("how much time is left")` -> `('chat', None, None, None)`!
  All three fall through to the LLM (`chat`), which has no tool access to read timers and either guesses a time from `prompt.py` or says it cannot check timers.

#### BUG-COMP-04 (High): `wake_loop()` Calls `model.reset()` Without Clearing `model.vad.prediction_buffer` (`jarvis.py:1420, 1449, 1495`)
* **Comparable Systems**: [dscripka/openWakeWord (hey\_jarvis)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fdscripka%2FopenWakeWord%2Fblob%2Fmain%2Fdocs%2Fmodels%2Fhey_jarvis.md) and [ESPHome / Home Assistant openWakeWord Issues (#219)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fesphome%2Ffirmware%2Fissues%2F219). A known quirk of `openWakeWord` when initialized with `vad_threshold=0.5` is that `Model.reset()` clears wake-word prediction buffers, **but does NOT clear `model.vad.prediction_buffer`** (the Silero VAD ring buffer).
* **Where in JARVIS**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:1234-1235` vs `1420, 1449, 1495`:
  In `speech_feats()` (`jarvis.py:1234-1235`), the author discovered this exact `openWakeWord` bug and wrote:
  ```python
  oww.reset()
  if hasattr(oww, "vad"):
      oww.vad.prediction_buffer.clear()                  # reset() keeps it: the last clip's speech would count here
  ```
  However, in `wake_loop()` (`jarvis.py:1420, 1449, 1495`), `model.reset()` is called in three places **without** clearing `model.vad.prediction_buffer`:
  * Line 1420: when entering `busy.locked() or S.state != "idle"`
  * Line 1449: after speaker echo / cooldown
  * Line 1495: after wake-word activation
* **What happens**:
  When a turn finishes or when `barge == "voice"` is active while JARVIS speaks, `model.vad.prediction_buffer` still contains `[0.85, 0.92, ...]` from the user's or speaker's last frame before `model.reset()`. On the very next frame in `wake_loop()`, `heard_speech(model)` (`jarvis.py:1225`, which checks `max(list(model.vad.prediction_buffer)[-5:]) > 0.5`) returns `True` from the **stale** buffer before any new speech occurs!

#### BUG-COMP-05 (Medium): Ringing Alarm Loop (`alarm()`) Pumps Master Windows Volume Up and Down Every 2 Seconds (`jarvis.py:521-530`, `mic.py:15-19`)
* **Comparable Systems**: Smart speaker / Windows voice assistant audio ducking complaints.
* **Where in JARVIS**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:521-530` and `jarvislib/mic.py:15-19, 184-199`.
* **What happens**:
  When a timer or alarm fires, `alarm()` (`jarvis.py:521-530`) loops for up to 45 seconds:
  ```python
  while time.time() < end and not cancel.is_set():
      ding()
      ...
      said = hear(patience=1.5) if not cancel.is_set() else ""
  ```
  Inside each 2-second iteration:
  1. `ding()` plays the chime at normal volume.
  2. `hear(patience=1.5)` calls `listen(patience=1.5)`.
  3. `listen()` calls `duck()` (`mic.py:189`), which drops the **master Windows speaker volume** to 30% (`JarvisDuckLevel`) and writes `Data\jarvis_duck.txt`.
  4. 1.5 seconds later, `listen()` exits and calls `unduck()` (`mic.py:199`), restoring the master Windows speaker volume to 100% and deleting `Data\jarvis_duck.txt`.
  5. 50 ms later, the loop repeats!
  For the entire 45 seconds that an alarm rings, JARVIS **oscillates the PC's master volume between 30% and 100% every 2 seconds**, causing any background music, game, or video to violently swell and dip 20+ times in a row.

#### BUG-COMP-06 (Medium): Conversational Auto-Memory (`learnable()`) Saves Contradictory Facts Without Replacing (`jarvis.py:311-325, 951-954`)
* **Comparable Systems**: OpenAI ChatGPT Memory & MemGPT / Letta local memory assistants, where users complain that telling the assistant an updated personal fact in conversation (`"I moved — I live in Chicago now"`) leaves the old fact (`"I live in Austin"`) in memory alongside the new one, confusing the LLM on future turns.
* **Where in JARVIS**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:311-325, 951-954` vs `jarvislib/memory.py:114-129`.
* **What happens (Verified in `test_similar_system_complaints.py`)**:
  When a user explicitly commands `"remember that I live in Chicago"`, `fact_save()` (`memory.py:114-129`) checks `_fact_head("I live in Chicago")` (`"i live in"`) against existing facts (`"I live in Austin"`) and routes to `replace_fact`.
  However, when the user states `"I live in Chicago."` in conversation, `learnable()` (`jarvis.py:311-325`) sets `offer["fact"] = "I live in Chicago"` and asks `"Want me to remember that?"`. When the user replies `"yes"`, `exchange()` (`jarvis.py:953`) calls `memory_reply("save", fact)` directly — **bypassing `fact_save()`'s `_fact_head` replacement check** and appending `"I live in Chicago"` so `jarvis_memory.txt` now contains both `"I live in Austin"` and `"I live in Chicago"`!

#### BUG-COMP-07 (Medium): USB / Bluetooth Microphone Hot-Plug Blindness (`jarvis.py:1572`, `jarvislib/mic.py:25-68`)
* **Comparable Systems**: [python-sounddevice (PortAudioError -9985 Issue #173)](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fspatialaudio%2Fpython-sounddevice%2Fissues%2F173) and `RealtimeSTT`. Users who turn on Bluetooth headphones or plug in a USB microphone *after* JARVIS has booted complain that the assistant cannot see the new microphone or crashes with `PortAudioError: Error opening InputStream: Device unavailable [PaErrorCode -9985]`.
* **Where in JARVIS**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:1572` and `jarvislib/mic.py:25-68`.
* **What happens**:
  1. `list_mics()` is called only once at daemon startup (`jarvis.py:1572`). When the user turns on a Bluetooth headset later and says `"use the headset microphone"`, `pick_mic()` (`mic.py:55-68`) only calls `list_mics()` if `MICS_FILE` does not exist on disk (`os.path.exists(MICS_FILE)` is `True` from boot!), so it reads the stale startup list and replies `"I don't see a microphone matching headset."`.
  2. Furthermore, PortAudio (`sounddevice`) caches the Windows audio device table inside `Pa_Initialize()`. Even if `list_mics()` is called again later, `sd.query_devices()` returns the **boot-time device list** unless PortAudio is re-initialized (`sd._terminate(); sd._initialize()`) while no audio stream is open!

### Section 1.6 — Core Bugs, Repetitive Hardware Pipelines (7 Subsystems), Dead Code, Stale Skins & Test Infrastructure Gaps

#### BUG-CORE-01 (High): `"next <weekday>"` Same-Day Scheduling Bug in `reminders.py` & Friday Test Failure in `test_jarvis.py`
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py:54-92` and `test_jarvis.py:2446-2451`.
* **What happens**:
  1. In `reminders.py:54-56, 88-92`, `(?:next |this |coming )?` is non-capturing, so `when()` discards whether `"next"` was spoken. Saying `"remind me next Friday at 9 pm"` on a Friday at 10:00 AM computes `days = (4 - 4) % 7 = 0` and schedules the reminder for **tonight (0 days)** instead of **next Friday (+7 days)**.
  2. In `test_jarvis.py:2446-2451`, `j.route("remind me on Friday at 9 to pay rent")` runs after `j.time.time` was restored to `real_time` at line 2354, failing every Friday between 09:00 and 21:00 local time.

#### BUG-CORE-02 (Medium): `SHOW_LOG` / `HIDE_LOG` Early Returns Bypass `fixed()` and Corrupt `way["kind"]`
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py:983-997`.
* **What happens**:
  `way["kind"] = "log"` is assigned unconditionally at line 983 before checking `HIDE_LOG` or `SHOW_LOG`, and both branches return manually without calling `fixed(reply)`, skipping `filler_done()`, `recent["me"]`, `history`, and follow-up listening.

#### BUG-CORE-03 (Medium): Untrusted External Data Injected into LLM System Prompt Without `<hud_data>` Delimiters (`INFO-01`)
* **Where**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/prompt.py:45-93` and `jarvis.py:1086-1122`.
* **What happens**:
  `prompt.context()` and `exchange()` concatenate raw calendar event titles (`calendar.txt`), open to-do lines (`ObsidianTodo`), note snippets (`notes.py`), and `about_me()` directly into the `system` role message without `<hud_data>...</hud_data>` tags or an instruction hierarchy rule ([OpenAI Instruction Hierarchy](https://www.google.com/search?q=https%3A%2F%2Farxiv.org%2Fabs%2F2404.13208), [OWASP LLM01](https://www.google.com/search?q=https%3A%2F%2Fmedium.com%2F%40shivayadav2820%2Fowasp-top-10-for-ai-blog-1-prompt-injection-the-mother-of-all-ai-attacks-3af23412ff6d)).

#### BUG-INFRA-01 (Medium): Complete Inventory of Repetitive Pipelines (7 Subsystems), Dead Code, Stale Skins, `Settings.inc` Pollution & Test Gaps

##### 1. All 7 Repetitive / Duplicated Hardware & System Pipelines
| Subsystem | Implementation A | Implementation B | Implementation C | Latency / Maintenance Impact & Consolidation Target |
| :--- | :--- | :--- | :--- | :--- |
| **1. Screen Brightness** | `ShipCore.cs:834-850` (`WmiMonitorBrightness` polled every 3s into `Data\sys.txt` + `ShipCore.exe brightness <0-100>`) | `jarvislib/actions.py:63-83` (`screen_brightness()` spawns cold `powershell.exe Get-CimInstance` on every read/write — 2x on `"step"`) | — | **1.5–3.0s wasted per voice brightness step**. Consolidate `actions.py:screen_brightness()` to read `Data\sys.txt` (`BRIGHT`) and invoke `ShipCore.exe brightness <n>`, keeping PowerShell only as a fallback. |
| **2. Media Transport Keys** | `jarvislib/actions.py:390-405` (`ctypes.windll.user32.keybd_event` in <1 ms) | `Scripts/media.ps1` + `Scripts/audio.lua:30-34` (spawns `powershell.exe` + `Add-Type` C# compiler on every HUD media button click) | — | **500–900 ms lag on HUD play/next/prev clicks**. Add `ShipCore.exe media <play\|next\|prev>` (or call `keybd_event` in `ShipCore.cs`) and retire `Scripts/media.ps1`. |
| **3. Audio Endpoint COM (`IAudioEndpointVolume`)** | `jarvislib/audio.py` (134 lines: `IMMDeviceEnumerator` + `IAudioEndpointVolume` vtable for render `0` + capture `1`) | `ShipCore.cs:870-935` (C# `IMMDeviceEnumerator` + `IAudioEndpointVolume` + `IAudioMeterInformation` polling speaker volume/peak) | `Scripts/audio_switch.ps1` (72 lines: C# `PolicyConfigClient` default audio device switcher) | Keep `audio.py` as the single Python COM layer for speaker + mic volume/mute, and optionally expose mic read/write in `ShipCore.exe` for HUD meter parity. |
| **4. Sleep / Display Off** | `jarvislib/actions.py:303-317` (`powercfg /a` + `SetSuspendState` + `SendMessageW(0xFFFF, 0x0112, 0xF170, 2)`) | `Main/Main.ini:213` (spawns `powershell.exe (Add-Type ...)::SendMessage(-1, 0x0112, 0xF170, 2)` on HUD button click) | — | Add `ShipCore.exe monitor_off` so `Main.ini` and `actions.py` use a single native binary instead of inline PowerShell `Add-Type`. |
| **5. GPU & Process Telemetry** | `ShipCore.cs:450-610` (`LibreHardwareMonitor` + PDH counters polling GPU load, VRAM, temps every 3s into `Data\gpu.txt` & `sys.txt`) | `Jarvis/diag.ps1` (`Get-Counter '\Process(*)\*'`, `'\GPU Engine(*)\*'`, `'\GPU Adapter Memory(*)\*'`) | `jarvislib/diag.py:67-115` (`ctypes` `GlobalMemoryStatusEx`, `GetSystemTimes`, plus reads `sys.txt` / `gpu.txt`) | Fix `diag.ps1` multi-instance key collision (`BUG-P9-02`) and avoid spawning `diag.ps1` in `watch()` when `ctypes` / `sys.txt` / `gpu.txt` already have the answer (`BUG-P9-04`). |
| **6. Weather / Location Fetching** | `ShipCore.cs:620-740` (native HTTP poller writing `Data\weather.txt` and `Data\net.txt`) | `Scripts/location.ps1` (66 lines: legacy PowerShell IP-geolocation + Open-Meteo poller writing `LocationVars.inc`) | — | `Scripts/location.ps1` is completely superseded by `ShipCore.exe` and is never referenced by any `.ini` or `.lua` file. Delete/archive `Scripts/location.ps1`. |
| **7. Key=Value State File Parsers** | `jarvislib/state.py` (`StateFile` + `read_kv()`) | `Scripts/core_bridge.lua` (`read_kv()`) | `Scripts/jarvis.lua` (`parse_kv()`) | Standardize on `core_bridge.lua`'s shared KV reader or keep `jarvis.lua` self-contained with identical escaping rules. |

##### 2. Dead Code, Stale Scripts & Unused Skin Meters
* **`Skins/Spaceship/@Resources/Scripts/sphere.lua` (151 lines)**: Legacy 3D sphere projection script; zero `.ini` or `.inc` files reference `sphere.lua` (replaced by `Overlay/Jarvis` and `holo.lua`).
* **`Skins/Spaceship/@Resources/Scripts/storage.lua` (67 lines)**: Legacy disk bar script; zero `.ini` or `.inc` files reference `storage.lua` (replaced by `ShipCore.exe` -> `Data\disks.txt` -> `core_bridge.lua`).
* **`Skins/Spaceship/@Resources/Scripts/location.ps1` (66 lines)**: Legacy geolocation PowerShell script; completely unreferenced.
* **`Skins/Spaceship/Overlay/Jarvis/Meters.inc` lines 56–68 (`[G1_1]`..`[G1_5]`, `[G2_1]`..`[G2_5]`, `[I1_1]`..`[I1_20]`)**: 20 shape meters defined in `Overlay/Jarvis/Meters.inc` that `Scripts/jarvis.lua` never updates or positions (leftover from an older ring-segment design; `jarvis.lua` only drives `O1..O5`, `R1..R14`, `P1..P16`, `SW1..SW3`, `CoreGlow`, `Core`, and `Prompt`).

##### 3. `Settings.inc` Pollution (`Phase 11 / 11c`)
* **`Skins/Spaceship/@Resources/Settings.inc` (lines 126–168)**:
  * Contains **5x duplicated** `; ---- update: network, captions, data links` comment blocks (27 redundant lines).
  * Hardcodes personal `JarvisCallMe=Senai` and `BootSound=1` (Phase 8b / 11c requires `BootSound=0` and empty `JarvisCallMe=` in the tracked repository default).
  * Contains leading whitespace after `=` on `JarvisKokoroVoice= bm_fable`, `JarvisSilence= 2.0`, and `JarvisWakeWord= hey_jarvis_v0.1.onnx`.
  * Retains unused `ObsidianVault=` alongside `ObsidianFolder=` and `ObsidianTodo=`.

##### 4. Test Infrastructure Gaps (`test_jarvis.py`)
* **`Everywhere.__setattr__` Blind Spot (`test_jarvis.py:25-32`)**: `ACTION_TABLE` and `ACTIONS` bind function references (`Action(act_lock, ...)`) at module import time. When a test sets `j.act_lock = fake`, `Everywhere.__setattr__` updates `_jarvis.act_lock` and `actions.act_lock`, but **does not update `ACTION_TABLE["lock"].run` or `ACTIONS["lock"]`** (it only had a special case for `open_target`)!
* **Direct `done_line()` Calls Masking `exchange()` Bugs**: Phase 7 tests called `j.run_action(...)` and `j.done_line(...)` separately rather than testing confirmed `"ask"`-risk actions through `j.turn()`, which masked `BUG-P7-01`.
* **Unpinned Wall-Clock Time (`test_jarvis.py:2446`)**: Restoring `j.time.time = real_time` at line 2354 left lines 2446–2451 dependent on the host machine's day of week and hour (`BUG-CORE-01`).

## Part 2: Complete Step-by-Step Fix Plan with Pseudocode (`Fixes 1–28`)

### Fix 1: Restore Windows Read-Back Replies (`done_line`) for Confirmed `"ask"`-Risk Actions (`BUG-P7-01`)
* **Target Files**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py` (`exchange()`, lines 1065–1076) and `Skins/Spaceship/@Resources/Jarvis/jarvislib/actions.py` (`done_line()`, lines 320–355).
* **What It Does & How It Works**:
  Adds `"todo": "Added."` into `done_line()` and updates `exchange()` (`jarvis.py:1071`) to call `done_line(action, target)` unconditionally whenever `run_action(action, target, pending=(action, target))` succeeds. Because `done_line()` already returns `"Done."` as its default fallback (`line 354`) for `lock`, `restart`, `shutdown`, `close`, `forget_*`, and `replace_fact`, calling `done_line(action, target)` for all confirmed actions restores live Windows read-back replies for `mic_mute`, `bluetooth_off`, `btlink`, `power`, `recycle`, `micdev`, and `sleep`.
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/actions.py (done_line):
  def done_line(action, target):
      if action == "todo":
          return "Added."
      if action == "micdev":
          return (f"Listening through {target}. It applies the next time I listen."
                  if target else "Back to the Windows default microphone.")
      if action == "open":
          return f"Opening {target[0]}."
      if action == "volume":
          return f"Volume at {speakers()[1]} percent."
      if action in ("bluetooth", "bluetooth_off"):
          return f"Bluetooth is {bluetooth_radio()}."
      if action == "btlink":
          return f"{'Connected to' if target[1] else 'Disconnected from'} {target[2]}."
      if action == "power":
          return f"Power mode is {POWER_NAMES.get(power_key(power_plans()[0]), 'a plan I do not switch')}."
      if action == "page":
          key, note = target
          title = PAGES[key][1]
          return (f"Windows has no switch for that, so I opened the {title} settings." if note == "noswitch" else
                  f"I can't read that list yet, so I opened the {title} settings." if note == "nolist" else
                  f"I can't connect devices by voice yet, so I opened the {title} settings. Pick it there." if note == "noconnect" else
                  f"Opening the {title} settings.")
      if action == "screenshot":
          return "Screenshot saved in Pictures, Screenshots."
      if action == "recycle":
          return "Recycle bin emptied."
      if action == "desktop":
          return "Sent."
      if action == "theme":
          return f"{theme_mode().capitalize()} mode is on."
      if action == "brightness":
          return f"Brightness is at {screen_brightness()} percent."
      if action in ("mic_mute", "mic_unmute", "mic_level"):
          is_muted, percent = mic_volume()
          return ("Microphone muted." if is_muted else
                  "Microphone unmuted." if action == "mic_unmute" else
                  f"Microphone at {percent} percent.")
      if action == "sleep" and screen_only[0]:
          return "This PC can't sleep that way, so I turned the screen off."
      return "Sent." if action == "media" else "Done."

  # In Skins/Spaceship/@Resources/Jarvis/jarvis.py (exchange, lines 1065-1076):
  if kind == "act":
      if ask_yes(prompt, quiet):
          ok = run_action(action, target, pending=(action, target))
          way["result"] = "done" if ok else "failed"
          if action in ("mute", "unmute", "volume", "stealth"):
              quiet = True if action == "stealth" else muted()
          fixed(done_line(action, target) if ok else "That didn't work.")
      else:
          way["result"] = "left - no yes"
          log(f"action {action} not confirmed")
          fixed(memory_reply("save", target[1]) + " I kept the old one too." if action == "replace_fact" else "Cancelled.")
      return
  ```

### Fix 2: Prune Built Capabilities from `UNBUILT_CAPS` & Expand Brightness / Mic / Settings Routing (`BUG-P7-02`, `BUG-P7-03`)
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py` (lines 206–219, 519–580, 643–653).
* **What It Does & How It Works**:
  1. Removes built Phase 7 capabilities (`"brightness"`, `"microphone"`, and general `"bluetooth"`) from `UNBUILT_CAPS`, retaining only genuinely unbuilt capabilities (`"bluetooth"` unpair, `"wifi"`, `"display"` wallpaper/resolution/screensaver, `"account"` hibernate/sign out, `"keyboard light"`).
  2. Adds `"microphone"` (`"sound"`) and `"brightness"` (`"display"`) to the settings `names` table (`routing.py:519-523`) so `"open microphone settings"` opens `ms-settings:sound` and `"open brightness settings"` opens `ms-settings:display`.
  3. Adds `"dim/darken/brighten (the screen) to N"` and `"by N (percent)"` step support to both brightness (`routing.py:553-563`) and microphone level (`routing.py:571-580`).
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py:
  UNBUILT_CAPS = {
      "bluetooth": r"unpair\b.*\b(?:bluetooth|headphones|earbuds|airpods|device)",
      "wifi": r"wi-?fi|airplane mode|flight mode|hotspot",
      "display": r"wallpaper|(?:desktop )?background|resolution|screen ?saver|refresh rate",
      "account": r"hibernat\w*|sign (?:me )?out|log (?:me )?(?:off|out)",
      "keyboard light": r"keyboard (?:light|backlight)",
  }

  names = (
      ("night light", r"night ?light", 1),
      ("focus", r"focus(?: assist)?|do not disturb", 1),
      ("battery saver", r"battery saver", 1),
      ("startup", r"start-?up apps|startup programs", 1),
      ("apps", r"installed apps|apps and features", 1),
      ("update", r"windows updates?", 1),
      ("bluetooth", r"bluetooth", 1),
      ("wifi", r"wi-?fi", 1),
      ("sound", r"sound|audio|microphone|mic", 0),
      ("display", r"display|screen|brightness", 0),
      ("storage", r"storage|disk space", 0),
      ("power", r"power(?: and sleep| settings)?|sleep", 0),
      ("update", r"updates", 0),
      ("apps", r"apps", 0),
  )

  bright = r"(?:the |my )?(?:screen |display )?brightness"
  screen_target = rf"(?:{bright}|(?:the |my )?(?:screen|display))"
  bit_or_by = r"(?: (?:a )?(?:bit|little|tad)| slightly| by (.+?)(?: ?%| percent)?)?"

  m = (re.match(rf"(?:set|turn|change|put|bring) {bright}(?: up| down)? (?:from \d+(?: ?%| percent)? )?(?:to|at) (.+?)(?: ?%| percent)?$", cmd)
       or re.match(rf"(?:dim|darken|brighten) {screen_target} (?:from \d+(?: ?%| percent)? )?(?:to|at) (.+?)(?: ?%| percent)?$", cmd)
       or re.match(rf"{bright} (?:to|at) (.+?)(?: ?%| percent)?$", cmd))
  if m and _num(m.group(1)) is not None:
      n = _num(m.group(1))
      return (("act", "brightness", ("set", int(n)), None)
              if 0 <= n <= 100 else ("say", None, None, "I can set it between 0 and 100."))

  m = (re.match(rf"(dim|darken|brighten) (?:the |my )?(?:screen|display){bit_or_by}$", cmd)
       or re.match(rf"make (?:the |my )?(?:screen|display) (brighter|dimmer|darker){bit_or_by}$", cmd)
       or re.match(rf"turn (up|down) {bright}{bit_or_by}$", cmd)
       or re.match(rf"turn {bright} (up|down){bit_or_by}$", cmd)
       or re.match(rf"(raise|increase|boost|lower|decrease|reduce) {bright}{bit_or_by}$", cmd))
  if m:
      step_n = _num(m.group(2)) if m.group(2) else 10
      if step_n is not None and 1 <= step_n <= 100:
          up_words = ("brighten", "brighter", "up", "raise", "increase", "boost")
          delta = int(step_n) if m.group(1) in up_words else -int(step_n)
          return ("act", "brightness", ("step", delta), None)

  m = (re.match(rf"turn (up|down) {mic_word}(?: volume| level)?{bit_or_by}$", cmd)
       or re.match(rf"turn {mic_word}(?: volume| level)? (up|down){bit_or_by}$", cmd)
       or re.match(rf"(raise|increase|boost|lower|decrease|reduce) {mic_word}(?: volume| level)?{bit_or_by}$", cmd))
  if m:
      step_n = _num(m.group(2)) if m.group(2) else 10
      if step_n is not None and 1 <= step_n <= 100:
          delta = int(step_n) if m.group(1) in ("up", "raise", "increase", "boost") else -int(step_n)
          return ("act", "mic_level", ("step", delta), None)
  ```

### Fix 3: Fix `undo_last()` for `mic_unmute`, Mixed Themes, and `did_add("undo")` (`BUG-P7-04`, `BUG-P7-08`)
* **Target Files**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py` (`run_action`, `undo_last`, lines 123–234) and `Skins/Spaceship/@Resources/Jarvis/jarvislib/actions.py` (`theme_mode`, `act_theme`, lines 88–102).
* **What It Does & How It Works**:
  1. In `undo_last()` (`jarvis.py:220-227`), inspects `was_muted` (`before[0]`) to decide whether to run `"mic_mute"` (`if was_muted`) or `"mic_unmute"` (`if not was_muted`), and reads back `mic_volume()[0]` from Windows for the spoken confirmation.
  2. Adds `_is_undo=False` to `run_action()` so undoing an `ACTION_TABLE` command logs `did_add("undo")` instead of polluting `did` with a fake forward command.
* **Pseudocode**:
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
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/actions.py` (lines 44–53, 370–377).
* **What It Does & How It Works**:
  1. In `running_window(name)`, checks both the full normalized string `want` (`"googlechrome"`) and the final token `tail` (`"chrome"` from `"Google Chrome"`, `"code"` from `"Visual Studio Code"`), plus 4+ character stem suffix matching (`"msedge"` in `"microsoftedge"`).
  2. In `act_open(app)`, lowercases `os.path.basename(app[1]).lower()` when checking `open_windows()` so `"Notepad.exe"` matches `"notepad.exe"` in `Data\windows.txt`.
* **Pseudocode**:
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

  def act_open(app):
      target = app[1] if os.path.isabs(app[1]) else "shell:AppsFolder\\" + app[1]
      win_map = {w.lower(): w for w in open_windows()}
      if app[1].lower().endswith(".exe"):
          bname = os.path.basename(app[1]).lower()
          exe = win_map.get(bname) or running_window(app[0])
      else:
          exe = running_window(app[0]) or running_window(app[1])
      core = os.path.join(RES, "Bin", "ShipCore.exe")
      if exe and exe.lower() in win_map and os.path.exists(core):
          run_ok([core, "focus", win_map[exe.lower()], target])
          return
      os.startfile(target)
  ```

### Fix 5: Cache `bt_devices()` with a 5s TTL and Catch `subprocess.TimeoutExpired` (`BUG-P7-06`)
* **Target Files**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/actions.py` (lines 209–227) and `jarvis.py` (line 130).
* **What It Does & How It Works**:
  Converts `subprocess.TimeoutExpired` into `OSError` inside `_bt_ps()`, caches `bt_devices()` for 5.0 seconds (invalidated on `bt_link()` / `act_bluetooth()`), and uses `(target[0], target[2], not target[1])` for `before` in `run_action("btlink")` so a single turn never spawns PowerShell C# compilation 3 times.
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/actions.py:
  _bt_cache = [0.0, None]

  def _bt_ps(call, timeout=40):
      try:
          out = subprocess.run(
              ["powershell", "-NoProfile", "-NonInteractive", "-Command", BT_DEV_SCRIPT % call],
              creationflags=NO_WINDOW, capture_output=True, text=True, timeout=timeout
          )
      except subprocess.TimeoutExpired as e:
          raise OSError("Windows timed out listing or changing Bluetooth devices") from e
      if out.returncode:
          raise OSError("Windows would not list or change Bluetooth devices")
      return out.stdout

  def bt_devices(max_age=5.0):
      now = time.time()
      if _bt_cache[1] is not None and now - _bt_cache[0] < max_age:
          return list(_bt_cache[1])
      rows = [ln.split("|", 2) for ln in _bt_ps("[Bt]::List()").splitlines() if ln.count("|") >= 2]
      devs = [(a, n.strip(), c == "1") for a, c, n in rows if re.fullmatch(r"[0-9A-F]{12}", a)]
      _bt_cache[:] = [now, devs]
      return list(devs)
  ```

### Fix 6: Stealth Mode Pop-Up Reply, No Follow-Up Ear, and Leave-Stealth Refusal (`BUG-P7-07`)
* **Target Files**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py` (lines 1068–1072) and `jarvislib/routing.py` (lines 472–474).
* **What It Does & How It Works**:
  Sets `quiet = True` when `action == "stealth"` succeeds so `"Done."` is shown in the pop-up only (`1b-13`) and `left["again"]` stays `False`. Adds a fixed refusal in `routing.py` for `"leave/exit/turn off stealth mode"`.
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py (after line 473):
  if re.fullmatch(r"(?:leave|exit|turn off|disable|end|quit|stop) (?:the )?stealth(?: mode)?|stealth(?: mode)? off", cmd):
      return ("say", None, None, "I can't leave stealth mode by voice; switch it off in the Control Center.")
  ```

### Fix 7: Enforce Confidence, Same-Channel, and Expiry Guards on Offer Confirmations (`BUG-P8-01`)
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py` (lines 938–954).
* **What It Does & How It Works**:
  Checks `offer.get("typed", False) == typed_turn[0]` and `typed_turn[0] or heard_score[0] >= -1.0` before accepting `is_yes(text)` on `room`, `closing`, or `fact`. If a low-confidence noise (`heard_score[0] < -1.0`) is transcribed as `"Okay."` after `"Want me to close it?"`, JARVIS asks `ask_yes(f"Did you say: {text}?", quiet)` instead of killing the process.
* **Pseudocode**:
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
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py` (lines 938–954, 1065–1076, 1616–1623).
* **What It Does & How It Works**:
  1. Stages `"ask"`-risk commands triggered from `TYPE TO HIM` (`typed_turn[0] == True`) into `offer["act"] = (action, target)` with `typed=True, expires=time.time() + 15` so the user can type `"yes"` in the next `ASK` turn (while rejecting any voice `"yes"`).
  2. Replaces the unsafe `reply_line("One moment, I'm busy.", muted())` call on the main thread when `busy.locked()` with `convo_add("J", "One moment, I'm busy."); S.set(pop="open")`.
  3. Passes `min(hud_tier(), 2)` instead of `0` when spawning `turn()` from `ASK`.
* **Pseudocode**:
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
* **Target Files**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py`, `jarvislib/mic.py`, and `jarvislib/quiet.py`.
* **What It Does & How It Works**:
  1. Tracks `dim_listening` in `mic.py` so clicking the orb during the dimmed 3–10s standby window (`WAKE`) immediately promotes the dimmed follow-up listen back to active listening (`dim = False`, `waited = 0`, `S.set(state="listening")`).
  2. Snapshots `wait_direct = ear_wait()` once before `listen()` in `exchange()` so `offer` expiry during Whisper transcription cannot retroactively drop speech.
  3. Sets `left["again"] = "undo"` (5s window) after command replies that do not end in `"?"`, and `"ear"` after chat/info/question replies (`8-A3`).
  4. Handles `"you can talk"` when not in quiet mode with `fixed("I'm not in quiet mode right now.")`, and uses `max(ends, default=0)` in `quiet._current()`.

### Fix 10: Protect `python`, `pythonw`, `ollama`, and `shipcore` in `is_protected()` (`BUG-P9-01`)
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/diag.py` (lines 192–200).
* **Pseudocode**:
  ```python
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
* **Target Files**: `Skins/Spaceship/@Resources/Jarvis/diag.ps1` (lines 21–32) and `jarvislib/diag.py` (lines 263–270, 317–385, 488–498).
* **Pseudocode**:
  ```powershell
  # In Skins/Spaceship/@Resources/Jarvis/diag.ps1 (lines 21-32):
  foreach ($x in $s) {
      $p = $x.Path; $i = $x.InstanceName
      if ($p -like '*\process(*') {
          if ($i -eq '_total' -or $i -eq 'idle') { continue }
          $inst = if ($p -match '\\process\(([^)]+)\)\\') { $Matches[1] } else { $i }
          if (-not $by.ContainsKey($inst)) {
              $by[$inst] = @{ name = ($inst -replace '#\d+$', ''); pid = 0; cpu = 0; mem = 0; io = 0 }
          }
          $v = $x.CookedValue
          if ($p -like '*% processor time') { $by[$inst].cpu = [math]::Round($v, 1) }
          elseif ($p -like '*working set - private') { $by[$inst].mem = [int64]$v }
          elseif ($p -like '*io data bytes/sec') { $by[$inst].io = [int64]$v }
          elseif ($p -like '*id process') { $by[$inst].pid = [int]$v }
      }
  ```

### Fix 12: Fix `"next <weekday>"` Same-Day Scheduling & Pin Clock in `test_jarvis.py:2446` (`BUG-CORE-01`)
* **Target Files**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py` (lines 54–92) and `test_jarvis.py` (lines 2445–2452).
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py:
  wd = re.search(rf",? (?:on )?(next |this |coming )?({'|'.join(WEEKDAYS)})(?: at)? ", s)
  if wd:
      s = s[:wd.start()] + " " + s[wd.end():]
  ...
  if wd:
      days = (WEEKDAYS.index(wd.group(2)) - datetime.fromtimestamp(now).weekday()) % 7
      if days == 0 and (wd.group(1) or "").strip() == "next":
          days = 7
  ```

### Fix 13: Route `SHOW_LOG` / `HIDE_LOG` Through `fixed()` and Wrap Prompt HUD Data in `<hud_data>` (`BUG-CORE-02`, `BUG-CORE-03`)
* **Target Files**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py` (lines 983–997) and `jarvislib/prompt.py` (lines 45–93).
* **Pseudocode**:
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
* **Target Files**: `jarvislib/actions.py`, `test_jarvis.py`, `Settings.inc`, `Scripts/`.
* **What It Does**: Reads `BRIGHT` from `Data\sys.txt` and uses `ShipCore.exe brightness <n>` when available; updates `Everywhere.__setattr__` to sync `ACTION_TABLE` and `ACTIONS`; removes duplicate comment blocks and leading spaces in `Settings.inc`; archives dead `sphere.lua`, `storage.lua`, `location.ps1`, and unused `[G1_1]`..`[I1_20]` meters.

### Fix 15: Mid-Utterance Self-Repair Normalization (`"no wait"`, `"actually"`, `"I mean"`) (`BUG-EDGE-01`)
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py` (`clean_cmd()`, lines 25–44).
* **What It Does & How It Works**:
  In `clean_cmd()`, detects mid-utterance self-repair markers (`no wait`, `wait no`, `actually no`, `actually`, `i mean`, `sorry i meant`, `or rather`) and resolves them before regex matching:
  1. If the text after the repair marker is itself a complete command (`route(after)[0] != "chat"`), replaces the utterance with `after`.
  2. If the text after the repair marker is a replacement argument (e.g. `"set volume to 40 no wait 60"` -> `after = "60"`, or `"set a timer for 10 minutes actually 5 minutes"` -> `after = "5 minutes"`, or `"open calculator no wait notepad"` -> `after = "notepad"`), substitutes the aborted trailing argument before the marker with `after`!
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py:
  REPAIR_SPLIT = re.compile(
      r"\b(?:no wait|wait no|actually no|sorry i meant|i meant|i mean|or rather|actually)\b\s*(.+)$"
  )

  def apply_self_repair(s):
      m = REPAIR_SPLIT.search(s)
      if not m:
          return s
      head = s[:m.start()].strip(" ,;-")
      tail = m.group(1).strip()
      if not head or not tail:
          return s
      # Case 1: tail is a standalone duration ("5 minutes", "10 seconds") -> replace trailing duration in head
      dur_pat = r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|fifteen|twenty|thirty|forty|fifty|sixty)\s*(?:seconds?|secs?|minutes?|mins?|hours?|hrs?)\b"
      if re.fullmatch(dur_pat, tail) and re.search(dur_pat, head):
          return re.sub(dur_pat + r"(?!.*" + dur_pat + r")", tail, head)
      # Case 2: tail is a number ("60", "30 percent") -> replace the last number in head
      num_pat = r"\b(?:\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)(?: ?%| percent)?\b"
      if re.fullmatch(num_pat, tail) and re.search(num_pat, head):
          return re.sub(num_pat + r"(?!.*" + num_pat + r")", tail, head)
      # Case 3: head starts with a verb prefix ("open X", "close X", "launch X") and tail is a noun target
      verb_m = re.match(r"^((?:open|launch|start|run|close|quit|kill|connect|disconnect|switch to|use)\s+(?:the\s+)?)(.+)$", head)
      if verb_m and not re.match(r"^(?:open|launch|start|run|close|quit|kill)\b", tail):
          return verb_m.group(1) + tail
      return s
  ```

### Fix 16: Pre-Route Compound Command Splitting & Anchor `turn on (dark|light) mode` (`BUG-EDGE-02`)
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py` (lines 482, 660–678).
* **What It Does & How It Works**:
  1. Changes `re.search(r"turn on (dark|light) mode", cmd)` at line 482 to `re.fullmatch(r"(?:turn on|enable) (dark|light) mode", cmd)` so it never matches a substring inside a compound command.
  2. In `understand()`, checks if `text` contains `" and "` or `" then "` where **both** sides independently route as valid non-chat commands (`a[0] not in ("chat", "diag")` and `b[0] not in ("chat", "diag")`) *before* letting a greedy single-command regex swallow the second clause into a reminder label or todo item!
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py (understand, lines 660-678):
  norm = clean_cmd(text)
  if re.search(r"\b(?:and(?: then)?|then)\b", norm):
      parts = [p.strip() for p in re.split(r"\b(?:and(?: then)?|then)\b", norm, maxsplit=1) if p.strip()]
      if len(parts) == 2:
          a, b = fix_route(parts[0]), fix_route(parts[1])
          ok_lane = lambda r: r[0] not in ("chat", "diag") and r != NEAR_MISS and r[3] != CANT
          if ok_lane(a) and ok_lane(b):
              if (a[0], b[0]) == ("remind", "remind") and a[1] == b[1] == "set":
                  return ("remind", "both", [a[2], b[2]], None)
              return ("multi", None, [a, b], None)
  ```

### Fix 17: Polite Negation Guard (`DONT_DO` Anywhere Before Verb) & Contradictory Confirmation Guard (`BUG-EDGE-03`)
* **Target Files**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py` (lines 25–33, 275–279, 661) and `jarvis.py` (lines 772–778).
* **What It Does & How It Works**:
  1. Expands `DONT_DO` to match negation words (`do not`, `don't`, `dont`, `never`, `please don't`, `just don't`, `better not`, `do me a favor and don't`) and prevents `fix_route()` from ever stripping negation tokens (`don`, `dont`, `not`, `never`) when trimming leading words (`w[1:]`, `w[2:]`).
  2. In `is_yes(text)` (`jarvis.py:776`), rejects any response that also contains a cancellation/negation word (`no`, `not`, `don't`, `dont`, `wait`, `stop`, `cancel`, `never mind`, `hold on`, `actually no`), so `"yes wait no"` or `"yes don't do it"` safely cancels instead of confirming!
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvis.py (lines 772-778):
  YES_ABORT = re.compile(r"\b(?:no|not|don'?t|dont|wait|stop|cancel|never ?mind|hold on)\b")

  def is_yes(text):
      s = strip_name(text).lower().strip(" .,!?")
      if YES_ABORT.search(s):
          return False
      return bool(YES_WORD.fullmatch(s))

  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py:
  DONT_DO = re.compile(r"^(?:(?:please|just|actually|hey|wait|um|uh)\s+)*(?:do not|don ?t|never|stop|better not)\b")
  NEG_TOKENS = frozenset({"not", "dont", "don", "never"})
  # Inside fix_route() step 2 (line 276):
  for trimmed in (w[1:], w[2:]):
      if trimmed and not (set(w[:len(w)-len(trimmed)]) & NEG_TOKENS):
          ...
  ```

### Fix 18: Catch Invalid Calendar Dates in `reminders.when()` (`BUG-EDGE-04`)
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py` (lines 93–98).
* **What It Does & How It Works**:
  Wraps `base.replace(month=mon, day=day, ...)` in `try ... except ValueError:` so impossible dates like `"February 30"` or `"April 31"` return `(None, s)` (or a clear spoken error `"That date doesn't exist on the calendar."`) instead of crashing the turn thread with an unhandled `ValueError`.
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py (lines 93-99):
  if md:
      mon = MONTHS.index(md.group(1)) + 1 if md.group(1) else int(md.group(3))
      day = int(md.group(2) or md.group(4))
      try:
          due = base.replace(month=mon, day=day, hour=hour, minute=minute)
          if due.timestamp() <= now:
              due = due.replace(year=base.year + 1)
      except ValueError:
          return None, s
  ```

### Fix 19: Support `"from X to Y"` Numeric Targets & Fractional Hour Timers (`"half an hour"`) (`BUG-EDGE-05`)
* **Target Files**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py` (lines 553–609) and `jarvislib/reminders.py` (lines 50–72).
* **What It Does & How It Works**:
  1. In `routing.py`, allows an optional `from \d+(?: ?%| percent)? ` before `(?:to|at) (.+)` in volume, brightness, and mic level rules so `"change volume from 30 to 50"` captures `50`.
  2. In `reminders.py:_words_to_ints(s)`, normalizes `"half an hour"` / `"a half hour"` -> `"30 minutes"`, `"a quarter of an hour"` / `"quarter hour"` -> `"15 minutes"`, and `"an hour and a half"` -> `"90 minutes"`.
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py (_words_to_ints):
  def _words_to_ints(s):
      s = re.sub(r"\b(?:an|one) hour and a half\b", "90 minutes", s)
      s = re.sub(r"\b(?:half an hour|a half hour)\b", "30 minutes", s)
      s = re.sub(r"\b(?:a )?quarter (?:of an )?hour\b", "15 minutes", s)
      ...
  ```

### Fix 20: Normalize Whisper Split-Word Compounds & Homophones in `clean_cmd()` (`BUG-EDGE-06`)
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py` (`clean_cmd()`, lines 25–44, and `NUM_WORDS`, lines 113–122).
* **What It Does & How It Works**:
  Collapses common Whisper ASR split compounds (`"blue tooth"` -> `"bluetooth"`, `"screen shot"` -> `"screenshot"`, `"un mute"` -> `"unmute"`, `"bright ness"` -> `"brightness"`, `"micro phone"` -> `"microphone"`) and adds `"fourty": 40` plus contextual `"to"`/`"too"` -> `2` after numeric prepositions.
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py (clean_cmd):
  ASR_COMPOUNDS = (
      (r"\bblue\s+tooth\b", "bluetooth"),
      (r"\bscreen\s+shot\b", "screenshot"),
      (r"\bun\s+mute\b", "unmute"),
      (r"\bbright\s+ness\b", "brightness"),
      (r"\bmicro\s+phone\b", "microphone"),
      (r"\bfourty\b", "forty"),
  )
  for pat, rep in ASR_COMPOUNDS:
      s = re.sub(pat, rep, s)
  ```

### Fix 21: Guard Stage-3 `interpret()` Against Hallucinated Numbers (`BUG-EDGE-07`)
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py` (`interpret()`, lines 370–385).
* **What It Does & How It Works**:
  When `interpret()` receives `action in ("volume", "brightness", "mic_level")` with an integer `target`, verifies that `_num(text) is not None` (i.e. the user actually spoke a number in `text`)! If the user said `"make the screen brighter"` or `"adjust the volume"` with no number, `interpret()` rejects the hallucinated integer or converts directional words into `("step", ±10)`.
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/routing.py (interpret, lines 372-383):
  if action == "volume" and isinstance(target, (int, float)) and not isinstance(target, bool):
      if _num(text) is None:
          return ("chat", None, None, None)
      return ("act", "volume", ("set", max(0, min(100, int(target)))), None)
  ```

### Fix 22: Fix Adaptive Noise Floor Lock-In When User Speaks Immediately on Frame 0 (`BUG-COMP-01`)
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/mic.py` (`_listen()`, lines 150–162).
* **What It Does & How It Works**:
  Fixes the #1 `SpeechRecognition` / `RealtimeSTT` energy-VAD complaint:
  1. Caps the initial noise floor `floor = min(rms, 0.015)` on frame 0 so that if the user is already speaking (`rms = 0.08–0.15`) or a transient click occurs on frame 0, `thresh = max(floor * 3.0, 0.012)` starts at `<= 0.045` instead of `3.0 * rms`, immediately triggering `started = True` on frame 0!
  2. Only adapts `floor = 0.95 * floor + 0.05 * rms` on quiet ambient frames (`if not started and rms < thresh:`) so transient noise spikes never ratchet `floor` above the speech threshold.
* **Pseudocode**:
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
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/speech.py` (`sentences_from()`, lines 150–163).
* **What It Does & How It Works**:
  Updates the sentence-boundary regex in `sentences_from()` so a period immediately following common titles, abbreviations, or initials (`Mr.`, `Mrs.`, `Ms.`, `Dr.`, `Prof.`, `Sr.`, `Jr.`, `St.`, `Mt.`, `vs.`, `etc.`, `e.g.`, `i.e.`, `Fig.`, `No.`) is not treated as the end of a sentence.
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/speech.py (lines 150-163):
  SENT_SPLIT = re.compile(
      r"(.+?(?<!\bMr)(?<!\bMrs)(?<!\bMs)(?<!\bDr)(?<!\bProf)(?<!\bSr)(?<!\bJr)"
      r"(?<!\bSt)(?<!\bMt)(?<!\bvs)(?<!\betc)(?<!\be\.g)(?<!\bi\.e)[.!?])(\s+|$)",
      re.IGNORECASE,
  )

  def sentences_from(pieces):
      buf = ""
      for piece in pieces:
          buf += piece
          while True:
              m = SENT_SPLIT.search(buf)
              if not m or (m.group(2) == "" and len(buf) < 160):
                  break
              sent, buf = buf[:m.end(1)].strip(), buf[m.end():]
              if sent:
                  yield sent
      if buf.strip():
          yield buf.strip()
  ```

### Fix 24: Support Named Timer Queries (`"how much time is left on my pasta timer"`) & Standalone Time-Left Queries (`BUG-COMP-03`)
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py` (lines 214–218, 250–266).
* **What It Does & How It Works**:
  Expands the timer/reminder query regex in `reminders.py:214` to match:
  * `"how much time is left on my <name> timer"` / `"how long is left on the <name> timer"`
  * `"how much time is left"` / `"how much time is left on it"` / `"check my timers"`
  And if a specific label word (`"pasta"`) is captured, filters or highlights the matching timer in `remind_reply("list", ...)`.
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py (lines 214-219):
  m = re.match(
      r"(?:what (?:are|is) my (reminder|timer|alarm)s?|do i have (?:any )?(reminder|timer|alarm)s?"
      r"|list (?:my )?(reminder|timer|alarm)s?|check (?:my )?(reminder|timer|alarm)s?"
      r"|how (?:much time|long) (?:is |do i have )?left(?: on (?:my |the )?(?:[a-z0-9 ]+? )?(reminder|timer)s?| on it)?)$",
      cmd
  )
  if m:
      kind = next((g for g in m.groups() if g), "timer" if "left" in cmd else None)
      return ("remind", "list", kind, None)
  ```

### Fix 25: Clear `model.vad.prediction_buffer` Whenever `model.reset()` Is Called in `wake_loop()` (`BUG-COMP-04`)
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvis.py` (lines 1233–1236, 1420, 1449, 1495).
* **What It Does & How It Works**:
  Extracts a helper `reset_oww(m)` that calls `m.reset()` and clears `m.vad.prediction_buffer` (matching `speech_feats()` at line 1235), and calls `reset_oww(model)` at all three reset points inside `wake_loop()` (`lines 1420, 1449, 1495`).
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvis.py:
  def reset_oww(m):
      if m is not None:
          m.reset()
          if hasattr(m, "vad") and hasattr(m.vad, "prediction_buffer"):
              m.vad.prediction_buffer.clear()
  ```

### Fix 26: Prevent Alarm Ring Loop (`alarm()`) from Pumping System Volume via `duck()` / `unduck()` (`BUG-COMP-05`)
* **Target Files**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/mic.py` (`listen()`, lines 184–199) and `jarvis.py` (`hear()`, line 15, and `alarm()`, line 529).
* **What It Does & How It Works**:
  Adds `duck_audio=True` to `listen(..., duck_audio=True)` and `hear(..., duck_audio=True)`. In `alarm()`, calls `hear(patience=1.5, duck_audio=False)` so the 45-second alarm loop does not oscillate Windows master volume between 30% and 100% every 2 seconds.
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/mic.py:
  def listen(patience=10, silence=None, prior=None, dim_after=None, duck_audio=True):
      if not mic.acquire(blocking=False):
          log("mic: already listening, skipped second open")
          return None
      if duck_audio:
          duck()
      try:
          return _listen(patience, silence, prior, dim_after)
      finally:
          if duck_audio:
              unduck()
          mic.release()
  ```

### Fix 27: Deduplicate Contradictory Slot Prefix (`_fact_head`) When Saving Auto-Learned Memory Facts (`BUG-COMP-06`)
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/memory.py` (`memory_reply()`, lines 166–179).
* **What It Does & How It Works**:
  In `memory_reply("save", target)`, before appending `target` to `items`, removes any existing fact whose `_fact_head(k)` matches `_fact_head(target)` (when `_fact_head(target)` is a singular slot prefix like `"i live in"`, `"my name is"`, `"my job is"`, `"i work at"`, `"my birthday is"`), ensuring auto-learned conversational facts update the slot cleanly instead of accumulating contradictory entries.
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/memory.py (memory_reply, lines 166-176):
  if op == "save":
      head = _fact_head(target)
      singular = head.startswith(("i live in", "my name is", "my job is", "i work at", "i am a ", "my birthday is"))
      if singular:
          items = [x for x in items if _fact_head(x[0]) != head or x[0].lower() == target.lower()]
      if not any(k.lower() == target.lower() for k, _ in items):
          if len(items) >= MAX_FACTS:
              return f"My memory list is full ({MAX_FACTS} items) — ask me to forget one first."
          items.append((target, today))
          save_memory(items)
      return f"Got it — I'll remember that {you_form(target)}."
  ```

### Fix 28: Refresh PortAudio Device List on Microphone Hot-Plug / Selection Miss (`BUG-COMP-07`)
* **Target File**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/mic.py` (`list_mics()`, `pick_mic()`, lines 25–68).
* **What It Does & How It Works**:
  1. When `pick_mic(spoken)` does not find a match in the cached `MICS_FILE`, it calls `list_mics(refresh=True)` to re-enumerate hardware devices before giving up.
  2. In `list_mics(refresh=False)`, when `refresh=True` and the `mic` lock is free (no active `InputStream`), calls `sd._terminate(); sd._initialize()` so PortAudio picks up newly connected USB or Bluetooth microphones without restarting `jarvis.py` ([python-sounddevice #173](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2Fspatialaudio%2Fpython-sounddevice%2Fissues%2F173)).
* **Pseudocode**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/mic.py:
  def list_mics(refresh=False):
      try:
          if refresh and mic.acquire(blocking=False):
              try:
                  sd._terminate()
                  sd._initialize()
              finally:
                  mic.release()
          seen = []
          for d in sd.query_devices():
              ...
  ```

## Part 3: Possible Recommendations — Low-Probability or Complex Cross-Industry Issues & Architectural Solutions (`REC-01`..`REC-05`)

The following five issues represent subtle human-factors dilemmas or multi-component architectural trade-offs that surface in customer complaints across [Amazon Alexa](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Falexa%2Fcomments%2F1h8gau9%2Fis_there_anyway_to_make_alexa_assume_the_nearest%2F), [Apple Siri](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2FSiri%2Fcomments%2F1wsewt6%2Fi_asked_siri_for_a_740_pm_alarm_four_different%2F), [Google Assistant](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Fgooglehome%2Fcomments%2F6uvbnj%2Fsetting_an_alarm_for_midday%2F), [faster-whisper](https://www.google.com/search?q=https%3A%2F%2Flocalaimaster.com%2Fblog%2Fwhisper-hallucination-fix), [KoljaB/RealtimeVoiceChat](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FKoljaB%2FRealtimeVoiceChat), and [Home Assistant Assist + Ollama](https://www.google.com/search?q=https%3A%2F%2Fcommunity.home-assistant.io%2Ft%2Fwhy-prefer-handling-commands-locally-increases-the-time-from-2-5s-to-52s%2F947662). While they either have a lower probability of occurring on a typical turn or involve deeper UX/architectural trade-offs, planning for them now provides a clear roadmap for hardening JARVIS beyond standard desktop assistants.

### REC-01: Early-Morning (`00:00–03:59 AM`) `"Set an alarm for 8 AM tomorrow"` Ambiguity
* **Where in JARVIS**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py:54, 100-106`.
* **The Cross-Industry Complaint**:
  On [r/alexa](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Falexa%2Fcomments%2F1h8gau9%2Fis_there_anyway_to_make_alexa_assume_the_nearest%2F), [r/alexa (next-day alarm)](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2Falexa%2Fcomments%2F1rmgujx%2Ftried_to_set_an_alarm_for_the_next_day%2F), and [r/Siri](https://www.google.com/search?q=https%3A%2F%2Fwww.reddit.com%2Fr%2FSiri%2Fcomments%2F1wsewt6%2Fi_asked_siri_for_a_740_pm_alarm_four_different%2F), one of the most upvoted user frustrations happens late at night (between `12:00 AM` and `3:59 AM`):
  * A user goes to bed at **12:30 AM on Saturday** and says: *"Set an alarm for 8 AM tomorrow."*
  * Mentally, the user has not gone to sleep yet, so `"tomorrow"` means *"when I wake up at 8:00 AM"* (7.5 hours away, Saturday at 8:00 AM).
  * However, because the system clock crossed `00:00`, `reminders.when()` (`reminders.py:54`) sees `tom = "tomorrow"`, sets `days = 1`, and schedules the alarm for **Sunday at 8:00 AM (31.5 hours away)** — causing the user to oversleep on Saturday morning!
* **How Other Assistants & Later Versions Resolved It**:
  1. **Apple Siri / iOS Clock**: Siri states the explicit weekday or relative hours when confirming a post-midnight `"tomorrow"` alarm, or treats alarms within the next 12 hours as Nearest-Time unless the user explicitly names a weekday (`"Sunday"`).
  2. **Home Assistant / Custom OVOS Skills**: Define a `"waking day rollover"` (`04:00 AM`) for `"tomorrow morning"` alarms spoken between `00:00` and `03:59 AM`, or append a spoken disambiguation notice (`"Set for Sunday at 8:00 AM — say 'this morning' if you meant today."`) with a 5-second flip handler (just like JARVIS's existing `flip_ampm` handler in `reminders.py:165-179`!).
* **Recommended Resolution Plan & Pseudocode for JARVIS**:
  Keep calendar accuracy predictable while adding a **late-night spoken heads-up + 1-turn `"no, this morning"` / `"no, today"` flip** (extending `reminders.flip_ampm()` in `reminders.py:165-179`):
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/reminders.py:
  FLIP_TODAY = re.compile(r"(?:no |actually |wait |i meant )?(?:today|this morning|in a few hours)$")

  def remind_reply(op, target):
      if op == "set":
          kind, due, label, said = target
          ...
          now_dt = datetime.now()
          due_dt = datetime.fromtimestamp(due)
          # If it is 00:00-03:59 AM and the user said "tomorrow" for a morning alarm (04:00-11:59 AM) >24h away:
          if 0 <= now_dt.hour < 4 and "tomorrow" in (said or "").lower() and (due - time.time()) > 86400 and 4 <= due_dt.hour < 12:
              day_name = due_dt.strftime("%A")
              return f"Set {what} for {day_name} at {clock}{ask}. Say 'this morning' if you meant today."
          return f"Set {what} for {day_word}{clock}{ask}."
  ```

### REC-02: Whisper `initial_prompt` (`HINT`) Continuation Echo & YouTube Outro Hallucinations
* **Where in JARVIS**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/hearing.py:13, 88-111`.
* **The Cross-Industry Complaint**:
  In [faster-whisper](https://www.google.com/search?q=https%3A%2F%2Flocalaimaster.com%2Fblog%2Fwhisper-hallucination-fix), Home Assistant Wyoming Whisper, and [Open-LLM-VTuber](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FSnowfork%2FOpen-LLM-VTuber%2Fblob%2Faidan_fixes%2FREADME.md), two Whisper failure modes occur even when `vad_filter=True` and `condition_on_previous_text=False`:
  1. **Prompt Continuation Echo**: Whisper's `initial_prompt` parameter is designed as *preceding transcript text*, not a system instruction. When given a full sentence like `HINT = "Hey Jarvis, set a timer for ten minutes. Jarvis, turn the volume down."` (`hearing.py:13`), a 0.4s throat-clear or desk bump that passes Silero VAD can cause `faster-whisper` (`base.en`) to output a continuation or fragment of `HINT` (e.g., `"Jarvis, turn the volume down."` or `"Set a timer for ten minutes."`)!
  2. **Expanded YouTube Training Artifacts**: `PHANTOM` (`hearing.py:88`) blocks `"thanks for watching"`, `"subtitles by"`, and `"you"`, but misses `"please subscribe"`, `"like and subscribe"`, `"thank you for watching."`, `"amara.org"`, and `"mbc news"`.
* **How Later `faster-whisper` Versions & Industry Resolved It**:
  1. **Switch from Sentence `initial_prompt` to `hotwords` (or Comma-Separated Vocabulary)**: `faster-whisper` added native `hotwords` support (`hotwords="Jarvis, Kokoro, Rainmeter, Bluetooth, Spotify, Obsidian"`) which boosts token probabilities during beam search *without* priming the decoder to hallucinate full command sentences!
  2. **Guard Against `HINT` Echoes & Expand `PHANTOM`**: Reject any low-confidence transcript (`avg_logprob < -0.65` or `no_speech_prob > 0.5`) that matches a clause of `HINT`, and expand `PHANTOM`.
* **Recommended Resolution Plan & Pseudocode for JARVIS**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/hearing.py:
  HINT = "Jarvis, timer, alarm, reminder, volume, mute, Bluetooth, brightness, screenshot, stealth."
  PHANTOM = re.compile(
      r"(?:thanks?(?: you)? for watching|subtitles by|transcribed by|please subscribe|like and subscribe"
      r"|amara\.org|mbc news|you|thank you|bye)\.?$",
      re.I,
  )
  ```

### REC-03: Context-Aware Dynamic End-of-Turn Endpointing (`JarvisSilence` Scaling)
* **Where in JARVIS**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/mic.py:134-170`.
* **The Cross-Industry Complaint**:
  In [KoljaB/RealtimeVoiceChat](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FKoljaB%2FRealtimeVoiceChat) ([HN Technical Discussion](https://www.google.com/search?q=https%3A%2F%2Fnews.ycombinator.com%2Fitem%3Fid%3D43899028)), Amazon Alexa ("Adaptive Listening"), and Apple Siri, users complain that a fixed silence timeout (`JarvisSilence = 1.0s`, or `2.0s` in `Settings.inc`) creates a painful trade-off:
  * If `JarvisSilence` is `2.0s` (as currently set in `Settings.inc:141`!), every command including `"mute"`, `"pause"`, and `"yes"` has a sluggish **2-second dead pause** after the user finishes speaking before JARVIS even starts transcribing!
  * Conversely, if `JarvisSilence` is lowered to `0.8s`, a user who pauses for 0.9s after saying `"Remind me to..."` or `"Add..."` while thinking of the task is cut off mid-sentence!
* **How `RealtimeVoiceChat`, LiveKit EOU, and Alexa Adaptive Listening Resolved It**:
  Scale the silence patience dynamically based on **turn context** and **utterance length so far**:
  1. **Confirmation / Alarm Stop Listen (`patience <= 5`)**: Use a crisp `0.6s` silence window because the user is only saying `"yes"`, `"no"`, or `"stop"`.
  2. **Normal Turns**: Cap default endpointing at `1.0s`, and if the user has only spoken `< 0.7s` of audio (`speech_frames < 24`, e.g., `"Remind me to..."`), grant an extra `+0.5s` hesitation allowance before cutting off the recording.
* **Recommended Resolution Plan & Pseudocode for JARVIS**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/mic.py (_listen):
  base_sil = silence if silence is not None else float(setting("JarvisSilence", "1.0") or 1.0)
  eff_sil = min(base_sil, 0.65) if patience <= 5 else min(base_sil, 1.1)
  limit = max(1, int(eff_sil / 0.03))
  ```

### REC-04: Explicit VRAM Unload When Switching Between `JarvisModel` (8B) and `JarvisModelFast` (3B)
* **Where in JARVIS**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/llm.py:66-132`.
* **The Cross-Industry Complaint**:
  In [Home Assistant Assist + Ollama (#947662)](https://www.google.com/search?q=https%3A%2F%2Fcommunity.home-assistant.io%2Ft%2Fwhy-prefer-handling-commands-locally-increases-the-time-from-2-5s-to-52s%2F947662) and [Open-LLM-VTuber](https://www.google.com/search?q=https%3A%2F%2Fgithub.com%2FSnowfork%2FOpen-LLM-VTuber%2Fblob%2Faidan_fixes%2FREADME.md), users who configure two local Ollama models (a primary 8B chat model and a fast 3B model for low-resource or routing tasks) report massive latency spikes (2.5s jumping to 30–50s) and GPU VRAM exhaustion when switching tiers.
  **Why**: Ollama's `keep_alive` (`10m` by default in `JarvisKeepAlive`) is tracked **per model name**. When the user launches a game (`PerfTier` moves from `0` to `1` or `2`), `pick_model(tier)` (`llm.py:66-70`) switches from `llama3.1:8b` (~5.5 GB VRAM) to `JarvisModelFast` (`llama3.2:3b`, ~2.2 GB VRAM). Because `llama3.1:8b` still has 9 minutes left on its `keep_alive` timer, **Ollama keeps both models loaded in VRAM simultaneously (~7.7 GB)** right when the user's game needs VRAM — forcing Ollama to spill layers onto system RAM (`ollama_on_cpu` triggers!) and causing game stutter!
* **How Industry Resolved It**:
  Track `_loaded_model = [None]` in `llm.py`. Whenever `pick_model(tier)` selects a model different from `_loaded_model[0]`, fire a non-blocking `keep_alive: 0` request for `_loaded_model[0]` so Ollama immediately evicts the old model from VRAM before loading the new one.
* **Recommended Resolution Plan & Pseudocode for JARVIS**:
  ```python
  # In Skins/Spaceship/@Resources/Jarvis/jarvislib/llm.py:
  _loaded_model = [None]

  def _evict_if_switched(new_model):
      old = _loaded_model[0]
      _loaded_model[0] = new_model
      if old and old != new_model:
          def _unload():
              try:
                  body = json.dumps({"model": old, "prompt": "", "keep_alive": 0}).encode("utf-8")
                  req = urllib.request.Request(OLLAMA_GENERATE, data=body, headers={"Content-Type": "application/json"})
                  urllib.request.urlopen(req, timeout=5).read()
                  log(f"llm: evicted {old} from VRAM after switching to {new_model}")
              except Exception:
                  pass
          threading.Thread(target=_unload, daemon=True).start()
  ```

### REC-05: Per-Application Audio Session Ducking (`ISimpleAudioVolume`) vs. Master Volume Slider Ducking
* **Where in JARVIS**: `Skins/Spaceship/@Resources/Jarvis/jarvislib/mic.py:71-104` and `jarvislib/audio.py`.
* **The Cross-Industry Complaint**:
  On Windows desktop assistants, lowering the master `IAudioEndpointVolume` scalar (`mic.py:85`: `audio.speaker_volume(target)`) reduces the global Windows system volume slider (`Volume` on the HUD and taskbar). While `unduck()` checks `abs(now - to) <= 2` (`mic.py:100`), the HUD's own volume readout (`Data\audio.txt` / speaker meter) visibly drops to `30%` every time the user speaks to JARVIS and jumps back to `100%` afterward.
* **How Windows Native Assistants & Discord Resolved It**:
  Windows Core Audio provides `IAudioSessionManager2::GetSessionEnumerator` and `ISimpleAudioVolume` per process ID, allowing an assistant (or `ShipCore.exe`) to duck only third-party multimedia sessions (Spotify, browsers, media players) to 30% while leaving the master Windows endpoint volume slider and JARVIS's own `python.exe` TTS output at 100%.
* **Recommended Resolution Plan & Pseudocode for JARVIS**:
  Add a `ShipCore.exe duck <0-100|restore>` command in `ShipCore.cs` using `IAudioSessionManager2` (skipping `Process.GetCurrentProcess().Id` and `python.exe`), or pass `duck_audio=False` during short confirmation (`ask_yes`) and alarm (`alarm`) listens so master volume only ducks on full command/chat listens.