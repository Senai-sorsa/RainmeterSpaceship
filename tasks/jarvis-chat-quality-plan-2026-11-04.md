# JARVIS chat-quality plan: wake word, "assumes misunderstandings", no jesting (PLAN ONLY, nothing implemented)

Written 2026-11-04 after the first live test. Rules that apply: `CLAUDE.md` (smallest change, real command output, no commit/push without
the user's yes), `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md`, work in `Skins/Spaceship/@Resources/Jarvis/` and `tasks/` only, fixes in the
refactor worktree or a scratch copy, then a patch (as with F1/F2). Method = the semi-live loop: type what he "heard" into the real
pipeline (real model, real prompt, real routing), score every reply, fix one thing, re-run the SAME cases plus never-tuned ones.

## 0. The three complaints, restated (the user corrects these)
- **W** The wake word is too hard to trigger (has to be said several times, or loudly, or close).
- **M** He assumes he misunderstood too often: asks "did you mean...", refuses, says "nothing close", or ignores a line he should have taken.
- **J** He can't hold a jesting conversation: takes jokes literally, answers flat, lectures, or drops the thread.
Also in scope ("and more possible chatting issues"): follow-ups ("and in Paris?"), callbacks to an earlier turn, short or fragmentary
replies ("yeah", "nah", "the second one"), self-corrections ("no wait"), filler ("um, so"), sarcasm, insults meant as teasing,
hypotheticals, repeated questions, emotional lines, long rambles, and chat-only replies when typing (F2).

## 1. What is known today (evidence, not guesses)
- `jarvis.log` has only 6 chat turns since the voice work (all `chat.chat via model`, answered), 5 `help: nothing close`, 3 `wake word heard`
  (score 0.92 on the one I could read), 4 `wake: best N this minute`. Far too little to measure W or M: the log never holds your words, by design.
- Wake settings now: `JarvisWakeModel=hey_jarvis`, `JarvisWakeSensitivity=0.5`, `JarvisWakeVerify=0` (config.py). Numbers to choose a
  sensitivity have never been measured on your voice: `tools/hearing_eval.py` exists for this and has never been run with real clips.
- Joke handling today: persona mood "mirror" says to joke only if the user jokes first; replies are capped at 3 sentences and passed through
  `mood.polish()` (stock-sentence, offer, "sir" filters). Whether that kills banter is UNKNOWN until measured (that is step 3).
- Misunderstanding paths that can fire: `understand()` (routing rules), the AI reread (`ai-reread`), `NEAR_MISS`/`CANT` fixed lines, `directed()`
  and room-talk gating in the open ear, `help: nothing close`, autocorrect and interpreter lines. Which one fires on which phrase is UNKNOWN
  until the cases run (every case logs its route).

## 2. New test banks (typed cases, same JSONL format as `tools/semi_live_*.jsonl`; written into `tools/`)
Each bank has a TUNING half and a HELD-OUT half (never looked at while fixing), like the existing 221/121 banks.
| Bank | What it holds | Size |
|---|---|---|
| J1 banter | teasing him ("you're slow today"), absurd hypotheticals, wordplay, one-liners, a running gag over 3-5 turns, being complimented/insulted playfully, sarcasm ("great, another timer"), requests to roast/joke on purpose | 60 |
| M1 misread | clear intent in awkward form: fragments, fillers, self-corrections, homophone/ASR errors injected by script (there/their, "to do" list vs "todo"), missing words, polite padding | 80 |
| M2 should-ask | genuinely ambiguous lines where ONE short question is right (so we do not just make him never ask) | 25 |
| C1 continuity | follow-ups and callbacks ("and that one?", "what did I just ask?", "go back to the joke") across 2-6 turns | 40 |
| E1 emotion/edge | tired, annoyed, sad, praise, "shut up", "never mind"; crisis lines are NOT tested casually (existing rule) | 25 |
| T1 typed | the same lines typed: reply must be text only, never spoken (checked by the tripwire that no audio call happens) | 20 |
| W1 wake clips | `tools/hearing_eval.py record` with YOU at the microphone: "Hey Jarvis" + a command, in conditions quiet / music / fan / tv / far / soft, plus `--talk` clips of normal speech with no wake word to count false wakes | about 15 min of your time |
I write J1/M1/M2/C1/E1 from the examples YOU give me (send 10-20 real lines that went wrong, any format) plus variations; I never invent
your private details. Anything with personal data stays out of the banks.

## 3. Scoring (extend `tools/score_semi_live.py`, rule-based first, same style as today)
New flags, each a plain rule so runs are repeatable: `MISREAD` (asked or refused when the intent was clear and the case is tagged clear),
`OVERASK` (more than one clarifying question, or a question when none was needed), `LITERAL_JOKE` (joke tag, reply is a flat refusal, a fact,
or a lecture), `NO_PLAYBACK` (joke tag, reply neither jokes nor acknowledges it; proxy: a stock sentence or a pure status), `DROPPED_THREAD`
(callback case, reply ignores the thread), `SPOKEN_WHEN_TYPED`, plus the existing CLAIM/PROMISE/TOO_LONG/STOCK/OFFER flags as guard rails.
Rule flags cannot judge whether a joke is FUNNY. So add a blind human rating: after each round I print 20 replies in random order,
unlabelled by version (old / new), and you rate each 1 to 5 (about 5 minutes). That is the real score for J; flags are the early warning.
Baselines: run the whole set on the CURRENT code on BOTH models (llama3.1:8b and the 3B), same hour, seed 7, 2 repeats, because run noise is
about +-5 per bank. Record the numbers in the HANDOFF log before any change.

## 4. Diagnose before fixing (per failing case, no guessing)
For each flagged case record: the route line (lane, kind, via rule/context/ai-reread/model), which gate or filter acted (`directed`,
`polish`, `grounded`, near-miss), and the prompt mood chosen. Group failures by cause. Likely levers, in the order I would test them, one at a time:
1. Persona text: let "mirror" and "playful" play along with a joke (dry one-liner allowed when the user jokes or teases), keep serious turns serious (this is persona plan A1).
2. Mood selection: how a joke or tease is detected so the playful mood is chosen at all.
3. `understand()` / AI reread thresholds and the near-miss refusal: prefer answering the likeliest meaning over asking, for low-risk intents only; risky actions keep asking (action table risk "ask").
4. `directed()` / room-talk gating in the open ear (the user's S2-10 design): count of wrongly ignored lines vs wrongly accepted ones, measured on M1.
5. Reply filters (`polish`, caps, "sir" frequency) when they flatten a joke.
6. Wake word: choose `JarvisWakeSensitivity` and `JarvisWakeVerify` from the W1 numbers (hit rate vs false wakes per hour of talk), not by feel.
   If no setting reaches a good hit rate, the next options need your approval: another wake model, or a custom "Hey Jarvis" model trained on your voice.
Nothing that changes what he says, a setting default, or timing is applied without your yes (fixes ship as a patch, like F1/F2).

## 5. The fix loop (each lever)
1. Write the failing case(s) first. 2. One small change. 3. Test that fails without it (mutation-check it). 4. Full gate: test_jarvis (venv python and
`py -3`), test_host_pipe, tests/run_all.py, golden routes and golden replies (commands must not change: 0 diffs unless the diff is the point and
I show it). 5. Semi-live old vs new on both models, same hour, the tuning bank AND the held-out bank, plus the command banks as a regression
check (route + action decisions equal). 6. Blind rating for J. 7. Patch to you; live only after your yes. Log in HANDOFF section 6.
Stop a lever that helps the tuning half but not the held-out half (that is overfitting; it is dropped).

## 6. Acceptance (numbers are set after the baseline, shown to you, and agreed before fixing starts)
- M: MISREAD+OVERASK rate on M1 at most half of baseline on both models; M2 still asks (no regression there).
- J: LITERAL_JOKE+NO_PLAYBACK on J1 near zero on the held-out half; your blind rating of new above old on at least 80 % of the pairs and averaging 4 or more.
- C: DROPPED_THREAD at most half of baseline.
- W: hit rate and false-wake rate on W1 at a setting we pick together (target: you can say it once, at normal volume, from your desk, and it hears you).
- No regression: golden routes 0 diffs, golden replies 0 diffs (or each diff approved), tripwires 0, command banks' decisions equal, first-sentence time unchanged.
- Then YOUR live test: you talk to him, send notes as before (F3, F4...), and any miss becomes a new case in the banks.

## 7. Costs and cautions
RAM is tight: one model at a time, unload after every run (`keep_alive:0`). 8B runs take minutes per bank. W1 needs you at the microphone and the room's
noise conditions; clips stay local in a gitignored folder. Persona changes risk the 3B model over-joking: the guard is the scorer (max one aside per reply,
none on serious tags). Wake changes risk false wakes from TV/music: the guard is W1's `--talk` and tv clips.

## 8. What I need from you to start
(a) 10-20 real lines (what you said, what he said, what you wanted) for jokes and misunderstandings, any format; (b) a yes to record the W1 clips
(15 min, you at the mic, quiet room first); (c) a yes on the plan order: baseline first, then M, then J, then W, then the rest.
