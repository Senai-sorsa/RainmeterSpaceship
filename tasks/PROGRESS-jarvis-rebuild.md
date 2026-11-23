# JARVIS rebuild: progress log

Plan: `tasks/PLAN-2026-11-22-phases-A-F.md`. Each entry lists what was done, the gate result, and what still needs a live test.
Loops this session: 30 min work loop, 2 h safety check.

## Approvals
- 2026-11-22: you said yes to all of it: Smart Turn v3.2 download, livekit-rtc install, the wake bank recording,
  launching the real app for B/C screenshots and perf, and pushing.

## Log

### 2026-11-22: D1 long speech dismissed as room talk (code part)
- `room_talk()` needs 60 words (was 25), and `understand()` only applies it to open-ear speech when he asked nothing
  (never right after the wake word, a click, or typed text). Each drop logs a `room?` line with the word count.
- Tests: `test_jarvis.py` room-talk block rewritten (a click turn is answered at once; 40 words is not room talk).
  Route golden: 1 intended change (a 48-word story is now `chat` in `understand()`; in the open ear `directed()` still keeps quiet).
- Gate: rc=0, 0 tripwires, 0 golden diffs after regenerating `routes.jsonl`.
- Not done: the 25 s cap check after a wake (`for_me`) is false-wake protection and is unchanged.
  Needs live: your long monologues in the replay bank (D2 bank not recorded yet).

### 2026-11-22: wake refractory (second report): already covered, no change
- After a wake the loop closes the stream, resets the model and sleeps 1 s, and the turn holds `busy` until it ends,
  so a second wake cannot start a turn. Adding a timer would change nothing.

### 2026-11-22: E4 confirmation binding: already in place, no change
- `run_action` runs an "ask" row only with the exact `(action, target)` you said yes to; `ask_yes` decides the yes
  in code with a 15 s expiry; the model never approves. The shell-surrogate deny waits until a tool takes arguments.

### 2026-11-22: E0 tracing (part 2 of E0)
- `base.trace()` appends one JSON line per turn to `Data/jarvis_trace.jsonl` (git-ignored, rotated at 512 KB like the log):
  turn id, follow/woke/typed, kind/action/lane/via/result (code names), total ms and stage ms
  (`open`, `listen`, `stt`, `reply_start`, `reply_done`). Never the words.
- Test: the D1 click turn leaves a trace line with the stage times and without the spoken words.
- Gate: rc=0, 0 tripwires, 0 golden diffs.
- Not yet: wake score / VAD per turn in the trace (needs the wake loop to pass them to the turn).

### 2026-11-22: E0 tracing: wake score and way per woken turn
- The wake loop keeps the last wake's score and way (`W0`/`HV`) in `wake_info`; the trace adds `"wake": [score, way]`
  on the first exchange of a woken turn (null for clicks, typing and follow-ups).
- Test: a click turn has `wake: null`; a woken turn carries `[0.61, "W0"]`. Gate: rc=0, 0 tripwires, 0 golden diffs.
- Still not traced: the VAD value and near-miss peaks (near misses are already logged as `wake: near miss`).

### 2026-11-22: E0 Ollama stream timeout: already in place, no change
- `llm.chat_stream` reads in its own thread with a 120 s socket timeout, polls cancel every 0.2 s, retries once before
  the first piece, and the 91 s turn watchdog sits on top. Nothing to add.

### 2026-11-22: E3 "cancel that" family
- Probed the cancel phrases by context. "cancel that" / "undo that" / "take that back" are undo; "cancel it" points at the
  item just set or listed (`pick_last`, tested at `test_jarvis.py:2689`); "never mind" ends quietly. Gap: "scratch that"
  went to the model. It is now undo too (`routing._rules_undo`); "forget that" is left to memory/chat on purpose.
- Test: `tests/test_phase_a.py` (scratch that / no, scratch that = undo; "scratch that off my list" is not).
- Gate: rc=0, 0 tripwires, 0 golden diffs (the phrase was not in the corpus).

### 2026-11-22: E1/E2 Smart Turn v3.2 end-of-turn (behind JarvisSmartTurn, default 0)
- Downloaded `smart-turn-v3.2-cpu.onnx` (8,679,182 B, the size on HF; sha256 2bb02631...7e4f) from `pipecat-ai/smart-turn-v3`
  into `Jarvis/turn/` (git-ignored by `**/*.onnx`). Licence BSD-2-Clause, copied to `turn/LICENSE-smart-turn.txt`.
- `jarvislib/endturn.py` follows Daily's `inference.py` (last 8 s, zero-padded in front, normalised, Whisper log-mel
  80x800) but uses faster_whisper's FeatureExtractor, so no transformers/torch. One CPU thread; ~26 ms per call warm, ~70 ms first.
- `mic._listen`: with the setting on, each 0.27 s pause is judged once: >= 0.5 ends the listen there; below it, the
  listen waits up to 3 s of quiet (the research report's numbers). Any load/run error logs `smart turn off` and the old timers stay.
- Test: `tests/test_endturn.py` (fake mic: off = 0.7 s timer, finished = stops at the pause, unfinished = 3 s cap,
  unavailable = timer; plus one real model run on silence). Gate: rc=0, 0 tripwires, 0 golden diffs.
- Needs live: turn on `JarvisSmartTurn=1` and check you are not cut off and short commands end faster. Setup-Jarvis.ps1
  does not download the model yet (a fresh install has the setting but not the file; enabled() then stays off).

### 2026-11-22: livekit-rtc installed; not wired in (echo cancelling already exists)
- `pip install livekit` in the venv: exit 0, livekit 1.3.0 (Apache-2.0) plus aiofiles and types-protobuf; numpy unchanged.
- Finding: `stopwords.StopWords` already runs WebRTC AEC (`pywebrtc-audio` 0.2.0, Apache-2.0, in requirements.txt) with
  what the player is playing (`far_add`) as the reference. livekit's `AudioProcessingModule` is the same WebRTC code, so
  swapping would add a dependency for no gain. livekit stays installed but unused; `pip uninstall livekit` removes it.
- The gap that is left: while he speaks, the **wake model** still gets the raw microphone (it only raises the threshold
  by 0.2). Feeding it the echo-cancelled block is the next AEC step; it changes barge-in, so it waits for a live test.

### 2026-11-22: D2 wake bank recorder
- `tools/record_wake_bank.py` writes 16 kHz mono int16 wav to `Jarvis/tests/wake_bank/{wake,room}/` (git-ignored twice:
  `**/*.wav` and the folder). Checked with a fake mic (names, numbering, wav format). Not run on your mic.
- Your part (from the Jarvis folder):
  `! "%LOCALAPPDATA%/SpaceshipHUD/venv/Scripts/python.exe" tools/record_wake_bank.py wake 15 desk`, then `wake 15 room`,
  then `room 30`. After that the offline scorer (current wake rules vs the older setup) can run.

## Safety checks
- 2026-11-22 (1st, 2 h loop): checked b97e0c7, 9ed5316. Gate rc=0 (test_jarvis venv + py3 exit 0, 0 tripwires; host_pipe 0 failed;
  run_all OK; route and reply goldens 0 diffs). Added lines: no subprocess/ctypes/delete/power/shell calls, no secrets, no new
  dependency or model. The trace holds code strings only (no `result` built from your words). The only file overwrite is the
  trace's own `.old` rotation, the same as `jarvis.log`. Nothing reverted. **Last checked commit: 9ed5316**
