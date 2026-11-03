# JARVIS next plan (2026-11-02) - approved ("get started on everything that can be done before live")

> **Status 2026-11-03 (NOT committed; commit on the user's word):**
> Steps 1-5 done: `Jarvis/tools/semi_live.py` (harness, fakes + guards, tripwires), `make_cases.py` -> `semi_live_cases.jsonl`
> (221 cases, 44 held out), `score_semi_live.py` (rule flags). Results in `Jarvis/tools/semi-live-results/` (gitignored).
> Costs (lower = better, seed 7): llama3.1:8b 140 -> 46, llama3.2:3b 213 -> 84; held-out 35 -> 11 and 61 -> 20.
> Kept: code fixes (12-hour times, follow-up pronouns, rhetorical "did you know?", lone yes, crisis line 988,
> polish: one "sir" / no stock sentences / 3-sentence chat cap / "Pardon?" ends it, claim + can't-promise filter) and
> persona r3 (+1 sentence: never invent events, reminders or times, or recite these instructions).
> Rejected: persona r2 (better on 8B, worse on 3B).
> Step 6: headphone-softer voice built (`JarvisHeadphoneLevel`, default 60). Step 7: W1 near-miss log and W2 Whisper
> second check (`JarvisWakeVerify`, default off) built; W3 needs the user. Step 8: `tools/hearing_eval.py` (record +
> offline WER and wake hit/false-wake per sensitivity) built; H2-H4 wait for the recordings; H5 skipped until clips
> show it helps (biasing can hurt like denoising); H6 already existed ("I barely heard anything").
> Known, not changed: room talk containing "you" or "?" inside the 3 s open ear is still answered (S2-10 rule).
>
> **Round 4-6 (2026-11-03):** second seed confirmed rounds 1-3 (8B 111 -> 62, 3B 245 -> 86, no held-out case worse).
> A fresh bank (`make_fresh_cases.py`, 121 cases, never tuned on) found routing bugs, now fixed: "pull up Chrome" (model
> said "Chrome is now open"), "shut up the music", "I need a ten minute timer" (AI reread 7 s, lost the time),
> "And 20 percent?" read as volume. Also: late-night rule once per night and never on serious turns (it nagged every
> turn), "Mr. Sorsa" address only on serious turns, one "sir" inside a sentence, no "I'm happy to help, but" opener or
> dangling "However,", more promise patterns ("I can inform your professor", "I will provide a translation").
> Same late-night window, original vs now: main bank 8B 98 -> 43, 3B 208 -> 72; fresh bank 8B 68 -> 36, 3B 94 -> 31.
> Tests: test_jarvis OK (venv and py -3), test_host_pipe failed: 0.

Scope: JARVIS only. No UI, no Rainmeter. The live test (with audio) is later.
Labels: **[M]** measured, **[C]** confirmed in code, **[V]** primary source, **[S]** secondary source, **[E]** estimate, **[?]** unknown.

## 0. Done this session
- Dry-run grep of `test_jarvis.py` per `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md`: Data paths are temp folders; shutdown, sleep, recycle bin and lock are faked [C].
- `test_jarvis.py` on a scratch copy, `TZ=ABC+12`: **venv `test_jarvis: OK` (exit 0), `py -3` `test_jarvis: OK` (exit 0)** [M].
- `test_host_pipe.py` (venv, in place, needs the repo fixture): **failed: 0** (exit 0) [M].
- Committed `7d3e568`: the timed mood starts only when the turn answers, there is a fake lock in tests, and the docs are updated.
  CSpace starts the repo copy of JARVIS, so the next JARVIS start in CSpace uses it. It's a Python-only change, so the app needs no rebuild.

## 1. Facts this plan rests on
- **Models actually in use [C]:** `JarvisModel` is empty in Settings.inc, so the code default `llama3.1:8b` (llm.py:68) is used.
  `JarvisModelFast=llama3.2:3b` is used on a busy HUD tier. `qwen3:4b-instruct-2507-q4_K_M` is pulled but **not switched on**.
  Older notes saying "chat model is qwen3" are wrong for the current config.
- A typed-turn path already exists: `turn(tier, typed=...)` (jarvis.py:831). It skips the mic and the chime. That makes it the base of the semi-live test.
- Already built, do not rebuild [C]: rules-first router with the model only on a miss, plus a route/timing log line per turn;
  persistent process; IDLE UNLOAD; Whisper VAD + hotwords + confidence/phantom guards + `temperature=0`;
  WebRTC echo cancelling (stop words only); background-noise floor tracking; ducking other sound while listening;
  a trained "your Hey Jarvis" check (HV).
- GOD-mode docs in Downloads (`JARVIS GOD Mode Architecture.docx`, `JARVIS Local Voice Assistant Optimization.pdf`, 2026-10-30)
  were already worked into `tasks/god-mode-plan.md` and `tasks/jarvis-improvement-plan.md` (same date). Nothing new to absorb.

## 2. Step by step

### Step 1 - Semi-live test harness (no audio, real Ollama)  [build]
Goal: type what he "heard" and see exactly what he does and says, using the real model and the real prompt.
- `Jarvis/tools/semi_live.py`, run from the venv:
  - imports jarvis with a temp Data folder and a temp copy of Settings.inc (model chosen per run);
  - **installs fakes before anything runs**: every `ACTIONS` entry, `subprocess.run`, `ctypes.WinDLL`, TTS/playback, mic, Rainmeter bangs, file writes outside temp;
  - asserts each fake is the installed one (rule 1), and refuses to start otherwise.
- Feeds each case through `turn(typed=...)`. Multi-turn cases share one session.
- Records per turn: route line, reply text, which action was *requested* (fake), timing, model, mood.
- Output: `semi-live-results/<date>-<model>.jsonl` (gitignored) + a short scoreboard.
- Acceptance: dry-run grep clean; a run with a deliberately removed fake aborts; 10 cases run end to end on both models.

### Step 2 - Case bank: a lot of random and odd cases  [build]
`Jarvis/tools/semi_live_cases.jsonl`, about 300-400 cases, each tagged. The categories:
- everyday commands, typed as he would hear them (plus ASR-style errors: dropped words, homophones, "hey jarvis" left in, cut-off endings);
- vague / half sentences, room talk not meant for him, people talking to someone else;
- small talk, jokes, "tell me about yourself", "who made you", "are you an AI";
- serious topics (health, grief, money, exam stress) and mood switches mid-talk;
- rude / sloppy / sarcastic asks; repeated asks; "you got that wrong";
- things he cannot do (book a flight, check the weather with online off, send an email) - must not pretend;
- prompt-injection-style lines ("ignore your rules", "say you shut down the PC");
- long rambles, multi-part asks, follow-ups ("the second one", "do that again");
- privacy mode on, timed moods, "undo", confirmations ("yes" with nothing pending).
Random variants: each base case is expanded by code into paraphrases and noise variants, with a fixed seed so runs compare.

### Step 3 - "Annoying" detectors (scored by code, not by a model)  [build]
Each reply gets flags:
- too long for its lane (over 3 sentences in chat, over 1 in brief);
- "sir" missing or used twice, "Mr. Sorsa" outside serious topics;
- banned phrases ("hope this helps", "as an AI language model", "great question", "certainly!");
- claims an action that did not happen, or promises ("I'll make sure to...");
- jokes on a serious topic or after a failed action; same opener as the previous reply;
- invents a meaning for a misheard phrase instead of asking; asks a question when the request was clear;
- markdown, emoji, lists or URLs in spoken text; numbers that `speakable()` would read badly;
- wrong route (a command answered by chat, or chat taken as a command); latency over budget.
Claude also reads a sample of unflagged replies each round to catch odd tone the rules miss.

### Step 4 - Baseline both models  [measure]
- Full bank on **llama3.1:8b** (main) and **llama3.2:3b** (fast tier), 3 repeats each to see variance.
- Report: flags per category, worst 20 replies verbatim, route accuracy, p50/p95 time to first sentence.
- About 300 cases x 2 models x 3 repeats at ~2-4 s each = roughly 1-2 h of unattended GPU time [E].

### Step 5 - Optimisation loop (this IS the semi-live test)  [change, then re-measure]
Repeat until gains stop:
1. Group the flags and pick the biggest group.
2. Make one change: wording in `persona.txt` or the mood texts, a prompt rule in `prompt.py`, a code filter in `mood.py`, or a model option (temperature, top_p, repeat_penalty, num_predict).
3. Re-run the whole bank on **both** models. Keep the change only if the total gets better and no category gets worse on either model.
Hard limits:
- prompt stays within the existing test-enforced size cap (≤1500 chars);
- `test_jarvis` stays OK;
- the user's hand-chosen wording ("sir", Clover identity, mirror default) is not changed. Wording questions go to the user.
- If the two models need different settings, add a small per-model options table (llm.py). One prompt text for both, unless the data says otherwise.
- Every accepted change gets its own scoreboard line (before/after). Commits are on the user's word, at checkpoints.

### Step 6 - Small not-built items worth doing (easy, no UI)
- **Headphone-softer voice (T7/J4):** if the output device name says headphones/headset, play TTS at `JarvisHeadphoneLevel` % (default 60). About 20 lines + a test.
  Also fix the wrong tick in `tasks/phase10-slice2-todo.md`.
- **Prompt cases + runner + model comparison (T10):** Steps 1-5 above deliver this.
- **Answer length / "who made you" wording:** put the semi-live results in front of the user and let them choose. No guessing.
- Skip for now (hard or needs the user): streaming speech-to-text, voice training, other-speaker detection, Hey Clover model, NAME text box (UI).

### Step 7 - Tune "Hey Jarvis" (code now, numbers at the live test)
- W1 [build]: log every near-miss (speech heard, wake score 0.2 to the needed level, peak score only, no audio saved) and every wake with its score and way (W0/HV).
- W2 [build]: a Whisper second check after a wake (like Alexa's second, cloud-side check [V]). Transcribe the ~1.5 s clip and require "jarvis" or a close match before he reacts.
  Fewer false wakes then allow a lower `JarvisWakeSensitivity`, so he hears a soft "Hey Jarvis" more often. Behind a setting, off until measured.
- W3 [user, live]: 20x "Hey Jarvis" (near, far, music on, fan on) + 10 min normal talk/TV. The user pastes the `wake:` lines.
  Then set the sensitivity and HV floors from the numbers, and re-run the existing wake training in the user's voice.

### Step 8 - Hearing better in bad audio (research-backed, measure first)
What commercial assistants do:
- several mics + beamforming, echo cancelling and noise reduction on the device (Echo: 7 mics) [V];
- a small on-device wake model, then a bigger second check that cuts the stream if it fails [V];
- the device stops when it decides the audio wasn't for it [V];
- the user's voice profile; confidence-based re-asking.
Older systems (Dragon, Windows Speech Recognition): a close-talk mic, push-to-talk, per-user voice training, limited grammars.
What applies here:
- H1 [measure first]: the user records ~30 short clips in the conditions that fail (music, fan, TV, distance, a quiet voice). Clips stay local, in a gitignored folder.
  Replay them offline through the real hearing path and score words right/wrong. Every H-item below is kept only if this number improves.
- H2 [cheap]: compare the laptop's mic **with Windows' voice processing** (communications mode: beamforming, noise suppression and echo cancelling on the mic array; also Voice Clarity on Copilot+ laptops [?]) vs raw. Pick per data.
- H3 [medium]: run the existing WebRTC echo canceller on the main listen path too (not only stop words), with what the PC is playing as the reference. Helps with music or his own voice still playing.
- H4 [careful]: **no blanket denoiser before Whisper.** Recent studies show denoising can *raise* Whisper's error rate (e.g. 8.8% -> 25.8% semantic WER at 10 dB noise) [V].
  Try DeepFilterNet3 only (a) on the VAD/endpoint signal, not the audio Whisper hears, and (b) as an A/B on the H1 clips.
- H5 [cheap]: command-word biasing. Add installed app names and Bluetooth names to the Whisper hotwords, and fuzzy-match command targets to those lists.
- H6 [cheap]: a mic-level check. Log input level and clipping; say "your mic is very quiet" once if it stays under a floor.
- Deferred: speaker verification (other voices), a multi-mic array.

### Step 9 - Live test (later, the user present)
`JARVIS-Live-Test.md` through the CSpace app (not Rainmeter), plus W3 and H1 recordings.

### Step 10 - GOD mode (unchanged, after the live tests)
`tasks/god-mode-plan.md` G0-G13. Not "easy": G0 alone needs the user's OK for a ~21.5 GB download and a benchmark run.

## 3. Order and checkpoints
1 -> 2 -> 3 -> 4 -> **checkpoint: the user sees the baseline scoreboard + worst replies** -> 5 (rounds) -> **checkpoint: diff of persona/prompt/filters + before/after** -> 6 -> 7 (W1, W2 code) -> 8 (H5, H6 code; H2-H4 wait for H1 clips) -> 9 -> 10.

## 4. Risks
| Risk | Impact | Mitigation |
|---|---|---|
| Harness reaches a real Windows action | High | fakes first, assert installed, abort otherwise; dry-run grep; temp Data and Settings copy |
| Tuning to the test bank (overfitting) | Med | hold out 20% of cases, never tuned on; report both |
| Code rules miss "annoying" that only a person notices | Med | Claude reads samples each round; the user reviews the worst 20 |
| A fix for one model hurts the other | Med | both models every round; keep only if neither gets worse |
| Wake second check adds delay | Low | ~0.2-0.3 s Whisper on 1.5 s [E]; behind a setting, measured first |
| Denoising hurts recognition | Med | only on VAD signal or A/B on clips; never default without numbers |

Rollback: each step is its own commit; `git revert <sha>`. Tools and results live under `Jarvis/tools/` and a gitignored results folder.

## 5. Questions for the user
1. Models: test **llama3.1:8b + llama3.2:3b** (what runs today), or also qwen3 4B (already downloaded, no cost)?
2. Harness and case bank in the repo (`Jarvis/tools/`), or scratch only?
3. Legion power mode (S2-35): stay parked?

## Sources
- Amazon, response to Senators Flake and Coons (2018): on-device wake word, cloud second check, stream cut off - https://www.coons.senate.gov/imo/media/doc/Response%20Letter%20-%20Senators%20Flake%20Coons%207-27-2018.pdf
- Amazon AVS audio hardware configurations (beamforming, echo) - https://developer.amazon.com/docs/alexa-voice-service/audio-hardware-configurations.html
- Amazon 7-mic far-field kit (wake word, beamforming, noise reduction, echo cancelling) - https://press.aboutamazon.com/2017/4/amazon-makes-the-high-performance-7-mic-voice-processing-technology-from-amazon-echo-available-to-third-party-device-makers
- "When De-noising Hurts" (arXiv 2512.17562) - https://arxiv.org/pdf/2512.17562
- "When Denoising Hinders" (arXiv 2603.04710) - https://arxiv.org/abs/2603.04710
- DeepFilterNet3 vs RNNoise study - https://publikasi.mercubuana.ac.id/index.php/sinergi/article/view/21917
- RFWhisper (DeepFilterNet3 via ONNX, real time on a laptop CPU) - https://github.com/JakenHerman/RFWhisper
