# JARVIS persona + assistant improvement plan (PLAN ONLY, nothing implemented)

Source: `Downloads\JARVIS Persona and Interaction Analysis.docx` (Gemini report: movie quote corpus + engineering
blueprint). Written 2026-11-03. Goal: our assistant (CLOVER/JARVIS) takes on a few real-JARVIS traits, keeps its own
character, and gets measurably better. Every step below follows the repo rules: smallest change, test per change,
semi-live check on llama3.1:8b, no commit without the user's word.

## 1. How to read the Gemini report (trust level)
- **Useful, and checkable against the films:** the five style traits (section 4.1: honorific cadence, calm under crisis,
  dry understatement, proactive anticipation, formal syntax), and the movie lines in Parts 1-3 as *style examples*.
- **Treat as unverified:** the "2026 / October 2026" papers (PersonaPlex, Jarvis-Audio, benchmark numbers), the
  "roger33303/jarvis-dataset" pairs (synthetic, written to sound like JARVIS, not canon), and exact quote wording
  (the report itself notes transcript variants). Use them for flavour, never as facts or as a dependency.
- **Conflicts with our rules:** "never use contractions" (our TTS and replies read more natural with them; keep a
  light formal lean only), full-duplex 7B speech model (needs a download, big GPU/VRAM, approval; see 6),
  "execute next steps before being commanded" (our rule: model output never authorizes OS actions; see 3.4).

## 2. What we already have (so we don't redo it)
- Persona file `persona.txt` with 4 moods (mirror, serious, brief, playful); formal, "sir" (once per reply),
  "Mr. Sorsa" only on serious topics; "own character, not a film character".
- Code-side guards: `mood.polish()` (stock-sentence, offer, sir, length caps), `grounded()` (no invented readings),
  claim filter (never says it did something), crisis line, fixed lines from code, briefing prompt, barge-in by wake
  word, near-miss and other-device replies (done this session).
- Test tooling: `test_jarvis.py`, `test_host_pipe.py`, semi-live harness + scorer (main bank 221, fresh bank 121).
Current numbers (8B, seed 7): main 43, fresh 32.

## 3. Personality changes (Track A)
Principle: add *flavour inside the existing safety rails*. Persona text is soft; anything that must always hold is code.

### A1. Dry understatement, delivered only when earned
- Real JARVIS: deadpan irony aimed at risky/boastful/obvious situations ("The logs respectfully disagree, sir").
- Today: mirror mood says "joke only if the user jokes first". Change to: in mirror mood allow **one dry, one-clause
  aside** only when (a) a fact in the prompt supports it (late night, skipped task, high CPU, overdue to-do) or (b)
  the user boasts / is self-deprecating. Never on serious turns, failed actions, or when the user is stressed.
- Implementation: new persona section `[dry]` appended to the system block in mirror + playful only; 4-6 short
  few-shot pairs of *our* wording (not film quotes copied wholesale). No code change beyond prompt assembly.
- Risk: 3B/8B over-jokes. Mitigation: scorer flag `DRY_COUNT` (max 1 per reply, none on serious tags).

### A2. Calm-under-crisis readouts ("weather report" voice)
- Status answers (battery, temp, disk, timers, errors) are flat, number first, no drama, then at most one short
  recommendation: "Disk is at 91 percent, sir. I would clear something soon."
- Where: `INFO_PROMPT` / HUD-data answers in `prompt.py`; add 3 few-shot examples. Keep `grounded()` as the safety net.
- Also fixed-code lines for the common hard failures (mic lost, model offline, Ollama down): same calm tone.

### A3. Formal-crisp syntax, light touch
- Prefer "I would" / "I do not have that" in analytical readouts and warnings; contractions fine in chat. Do not ban
  contractions (voice sounds stiff, TTS pronounces fine either way). Add to `[system]`: "Readouts and warnings are
  crisp and slightly formal."

### A4. "Proactive anticipation" - but only from real data, and only offered, never executed
- Real JARVIS acts first ("Creating a flight plan"). Our rules forbid model-authorized actions, and chat must never
  claim an action. So: **suggest, grounded, one line**, never "I have done".
- Concrete, code-driven triggers (no model needed to decide): timer/alarm about to fire during a call; calendar item
  in 15 min; battery under 20 percent; CPU/temp over threshold for N minutes; unread mail count changed; late-night
  nudge (already once per night). Speech from a fixed template or a one-sentence model phrasing of the trigger.
- Gate: new setting `JarvisProactive` (off | low | normal), default **off** until the user opts in; global rate limit
  (max 1 unprompted line per 20 min, never while the user is talking, in a game, or in stealth/quiet mode).
- Execution of an offered step still needs the existing "yes" confirmation path.

### A5. Modes inspired by the film
- "Sarcasm harmonics" (script): map to existing *playful* mood plus a spoken toggle: "turn sarcasm up/down" ->
  mood command (parser exists for mood; add phrases). Acknowledge in one line from code.
- "Directive"-style standing rules: user-defined **house rules** ("never interrupt me while I'm on a call", "no
  jokes before 9 am"). Stored as small settings/flags checked by code, not free text for the model. Small, optional.
- "House Party Protocol"-style named routines: user names a macro ("study mode"); runs only whitelisted existing
  actions, confirmed once. Later phase (see B5), not now.

### A6. Address forms
- Real JARVIS: "sir" for the owner, titles for others (Doctor, Colonel, Miss Potts). We are single-user; keep "sir"
  once per reply (current), Mr. Sorsa on serious topics. Only add titles if guest/multi-user ever exists (not planned).
- Keep "sir" optional (user said it is not required): do not reintroduce injection.

### A7. Signature phrasing bank (small, ours)
- ~25 short stock phrasings in our own words for acknowledgments ("As you wish", "Right away", "Noted", "Online and
  ready"), used by code for fixed replies so they vary and sound less robotic. Rotate without immediate repeats.
  Replaces "Done." / "Sent." / "Opening X." where fixed lines are used; keep numbers (volume, timers) intact.

### A8. Persona acceptance tests (add to semi-live banks)
- New tag `persona` in `make_cases.py` / `make_fresh_cases.py`: ~30 cases (boast, risky plan, status ask, late night,
  repeated failure, user praise, user stress, thanks, "do you think this will work?").
- New scorer flags: `NO_DRY` (none on a case tagged "should be dry"), `OVERJOKE` (joke on serious/failed-action),
  `DRAMA` (exclamation or alarm words in a status readout), `PROACTIVE_CLAIM` (says it already did something).
- Gate for shipping each persona step: persona cases improve, total cost on main/fresh does not rise, 0 tripwires.

## 4. Assistant improvements beyond personality (Track B)
Ordered by value / cost. All use what is already installed unless stated.

| # | Item | Why | Cost / approval |
|---|---|---|---|
| B1 | Fix known misses: 8B ignores HUD data ("no unread emails" with 4 unread); room talk with "you"/"?" inside the 3 s ear is answered | Accuracy, trust | Small: code check that HUD-count claims match the data, else fixed line |
| B2 | More fixed-from-code answers for things he cannot do (weather lookup "I can't look that up yet", file/web actions) with the same calm voice | No robotic/odd fallbacks | Small |
| B3 | Command reading: AI reread (8B, up to 7 s) replaced/assisted by small tool-calling model (qwen3:4b-instruct, already downloaded); test on fresh bank command cases first | Faster, fewer lost times | Medium; offline test first |
| B4 | Busy-GPU fallback model: replace llama3.2:3b with qwen3:4b-instruct (best fresh score, already downloaded) after fixing its "can message your group chat" capability claims and curly quotes | Quality when GPU is busy | Medium; run both banks |
| B5 | Named routines / macros (whitelisted actions only, confirm once) | "House Party Protocol" feel | Medium; new code, tests, user approval of design |
| B6 | Memory recall reranker (small ONNX bge/MiniLM reranker over current MiniLM search) | Better "what did I say about X" | Medium; new dependency, approval |
| B7 | Vision skill: "what's on my screen" via qwen2.5vl:3b or gemma3:4b | Big capability jump | Download ~3 GB + VRAM check + approval |
| B8 | Deep-think path: fill `JarvisModelDeep` (phi4-mini already downloaded, or deepseek-r1 distill) for "think hard" | Hard questions | Small-medium; latency budget |
| B9 | Hearing: choose Whisper variant with `hearing_eval.py` clips (small.en vs distil) | Fewer mishearings | Needs user recordings |
| B10 | Stale-turn guard (the one idea worth taking from the "ledger" paper): if the user interrupts or changes mind, a pending action/answer from the older turn is dropped, and a late tool result is never spoken | Correctness on barge-in | Small-medium; code audit of `jarvis.py` turn state first |
| B11 | Playback receipts: log "spoken" only after audio actually finishes | Honest history / follow-ups | Small; check `speech.py`/`turnstate.py` |

Not planned (explicit non-goals): replacing the pipeline with a full-duplex 7B speech model (PersonaPlex or
similar), HuggingGPT-style multi-model orchestration, LoRA fine-tuning on movie quotes. Reasons: unverified claims in the
report, heavy GPU/RAM on a PC that was low on RAM during tests, licensing/copyright of the script text, and our
measured gains came from prompt + code guards, not model swaps. Revisit only with measurements.

## 5. Phasing (each phase = separate approval, test, semi-live run, log entry)
1. **Phase 0 - baseline (no code):** record current persona-flavour numbers: run main + fresh on 8B and 3B; add the
   persona cases (A8) and scorer flags first; they must exist before any persona edit so we can measure.
2. **Phase 1 - cheap persona (A1, A2, A3, A7):** persona.txt sections + few-shot + fixed-phrase bank. Prompt/text only.
3. **Phase 2 - accuracy fixes (B1, B2, B10, B11):** code guards with tests.
4. **Phase 3 - proactive layer (A4 + A5 sarcasm toggle):** code triggers, setting default off, rate limit, tests with
   fake clock; live check later with the user.
5. **Phase 4 - model/tooling (B3, B4, B8):** only with bank evidence on 8B and 3B.
6. **Phase 5 - bigger skills (B5, B6, B7, B9):** each needs its own design note and approval.

## 6. Performance and safety checks (CLAUDE.md section 4/5)
- Baseline before Phase 3/4: CPU, RAM, VRAM (Ollama), idle polling rate of proactive triggers (poll at >= 30 s,
  reuse HUD data already collected, no new background process), first-sentence latency (now ~0.3 s p50 on 8B; must not
  regress more than ~10 percent).
- Proactive lines and routines never call OS actions by themselves; model text never authorizes actions; all
  destructive paths stay faked in tests (CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md).
- Persona text is data, not a security boundary: injection tests (existing tag) rerun after every persona edit.
- No copying large film dialogue into the repo (copyright); few-shot examples are our own wording in the film's *style*.

## 7. Per-phase acceptance
- test_jarvis OK (venv + py -3), test_host_pipe failed: 0, scratch copy, TZ=ABC+12.
- Semi-live llama3.1:8b: main and fresh cost not higher than baseline; persona cases improve; tripwires 0.
  3B run only if the change touches model output (persona/prompt changes do: run both).
- Handoff log entry with numbers; rollback = git checkout of the touched files.

## 8. Open questions for the user
1. How much humour by default: keep "joke only if you joke first", or allow the single dry aside from A1 in mirror mood?
2. Proactive lines (A4): wanted at all? If yes, which triggers first (calendar, battery, late night, CPU)?
3. Contractions: keep natural, or lean formal ("I do not") in readouts only (proposed)?
4. Is Phase 5 (vision, routines, reranker) worth planning in detail now, or later?

## Addendum (2026-11-03, after the user's scoping decision)
Only the LIGHT personality items are to be implemented next: A1, A2, A3, A7, A8. NOT: A4 (proactive), A5 (sarcasm toggle, house rules, routines), A6 (titles). Track B items B1, B2, B10, B11 are in scope; B3/B4/B8 only if
fresh-bank evidence supports them; B5, B6, B7, B9 need separate approval. Voice smoothness has its own plan: `tasks/jarvis-voice-plan-2026-11-03.md`. The full session prompt is `tasks/voice-measurements/NEW-SESSION-PROMPT.md`.
Reference for the film-style traits: `C:\Users\Senai\Downloads\JARVIS Persona and Interaction Analysis.docx` (Part 4.1 lists the five traits; its 2026 papers/benchmarks are unverified; do not copy film dialogue into the repo).
