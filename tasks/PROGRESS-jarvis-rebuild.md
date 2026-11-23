# JARVIS rebuild: progress log

Plan: `tasks/PLAN-2026-11-22-phases-A-F.md`. Each entry lists what was done, the gate result, and what still needs a live test.
Loops this session: 30 min work loop, 2 h safety check.

## Waiting on a yes from you
- Smart Turn v3.2 model (download), livekit-rtc for echo cancelling (install): not done until you say yes.
- Live microphone runs for D1/D2 (replay bank recording), and launching the real app for B/C screenshots and perf.

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

## Safety checks
- (none yet) last checked commit: 8da8683
