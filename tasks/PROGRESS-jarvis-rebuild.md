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

## Safety checks
- (none yet) last checked commit: 8da8683
