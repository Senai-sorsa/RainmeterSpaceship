# JARVIS combined live test (condensed)

One run, in order. Built on branch `fix/phase7-9-audit`; **nothing here has had a live run**. Only fakes have passed (`test_jarvis: OK`).
Source of each step is in brackets. Mark each step PASS / FAIL. For a FAIL, paste: what you said, what he said, roughly when, plus the `route:` and `timing:` log lines of that turn.

**Before:** copy to live on your word (PART D "COPY TO LIVE" in `JARVIS-Repair-Plan.txt`; backs up the live folder first), refresh Rainmeter, restart JARVIS, wait for STANDBY. Settings.inc is never copied.
**Rules:** you paste log lines (Claude never reads `jarvis.log` or `Data\`). Tone/wording problems are only noted, not fixed on the spot. Have a wired keyboard and speakers (not headphones) for step 2.

---

## 0. Setup (5 min, once)
- Control Center > JARVIS: WAKE WORD STRICTER to 0.50; WAKE TRAINING > TRAIN (~2 min: "Hey Jarvis", "Hey", bare "Jarvis", 15 s quiet). Paste the `train:` lines and `wake: your checks:` line. WHISPER = small.en. MODEL: your choice (qwen3:4b-instruct-2507-q4_K_M or current); restart JARVIS after a change.
- Live `Settings.inc` by hand: `JarvisCallMe=Sir`, `JarvisQuietCalendar=<class calendar label>` (for step 9).
- Control Center check: every old JARVIS row still there, scroll works, three headings (1b-17). New rows listed in step 12.

## 1. Wake word and noise (about 10 min, run while doing other steps)
- "Hey Jarvis" 10x normal voice (9+ wake), 10x softly (count). Paste `wake word heard (score, way)` lines. [F1]
- "Hey" ... 2 s ... "Jarvis" wakes; ... 7 s ... does NOT. Bare "Jarvis" 5x: no wake. [F2, F3]
- 30 min of room talk or a video near the mic, no wake word: 0 wakes. Check log for `route: false_wake` / `silence` lines and that each turn has exactly one `route:` line. [F4, C1, C2]
- Click the orb: it wakes and cancels; REINDEX and TRAINWAKE still work. [0d]

## 2. Stop words on speakers (5 min)
- Ask 10 things containing "stop", "quiet", "enough" (e.g. "what does a stop sign mean?"): 0 false stops.
- Say "stop" 10x mid long answer: 9+ stop him. Paste `stop words` lines. [T5]

## 3. One long conversation (the main test, ~15 min)
Do this as one flowing talk; tick each item as it happens.
- **Memory window (new):** ask about topic A, then 4-5 follow-ups with no wake word between (within 20 min): he stays on A and knows the earlier points. Say something unrelated: window clears. "New topic." -> "Okay." Come back after 21+ min: he does not carry the old talk.
- **Follow-up timing:** answer within 3 s without his name: taken. Wait 5 s, talk without name: ignored (`ear: started late without his name - dropped`). Wait 5 s, "Jarvis, and tomorrow?": taken. Wait 12 s, "Jarvis, hello": nothing. [8a]
- **Room talk:** right after a reply say "Mom, the pasta is boiling over." Default is now silent (`ear: unsure` logged, no question). "uh huh": nothing. A 25-word ramble: silent too. A real question after a wake: answered. [A3, F5, F6, D6]
- Short quiet "Thank you." after a wake: dropped; a real thanks gets **"You're welcome, sir."** [L4, I3]
- "About 20%." right after a volume exchange sets the volume. "Hello": "Hello, Sir." and ear stays open ~3 s. [L2, B4]
- Calendar question with an empty calendar: fixed "nothing" reply. [L10]
- Ask something while not muted and talk over a long reply: log/history keep only what he said aloud. [8-A2]
- Pop-up text types at his speaking pace (muted: reading pace). [L8]

## 4. Personality and honesty (Phase 10, tone is for your review)
- Default stays **playful**; answers 1-3 sentences; "sir" in nearly every reply; contractions fine; "Mr. Sorsa" only on serious topics.
- Name: he calls himself **Clover**; Control Center says CLOVER. "Who made you?" -> Senai Sorsa made him, runs locally. "Are you an AI?" -> allowed to say so. "Hope this helps" never appears.
- Serious topic (health, money trouble, grief, stress about an exam): tone switches to serious and "Mr. Sorsa" may appear; playful again afterwards.
- Mood commands: "be serious" / "be brief" / "be playful" / "be natural" -> short confirmation; Control Center buttons match; "undo" or "back to before" returns the old mood. [mood.py]
- Rude or sloppy ask -> calm reply; a real mistake by him -> "I apologize, sir," then the specific mistake (and not otherwise).
- Mis-heard phrase: he says he didn't catch it instead of inventing a meaning. Unclear input: he asks, doesn't joke. He never promises something he cannot do ("I'll make sure to get that to you"). [evidence a-e]
- Late-night and "talk less" hints behave (set TALK LESS on in step 12).
- Paste 5-10 replies you didn't like; Claude notes them for Phase 10 review.

## 5. Memory (facts, promises, privacy)
- "Remember that ..." in three wordings ("hey Jarvis, remember ...", "..., remember that", "I want you to remember that ..."): saved. Next day he knows them. [M4a]
- Contradicting fact: "Replace it?" (yes replaces, otherwise both kept).
- Say "my favourite colour is green" in chat: with LEARN FACTS = **AUTO** (default) it saves silently, no offer, and "undo" removes it; with ASK it says "Want me to remember that?"; OFF does nothing.
- Ask him to do something later and let him say "I'll remind you...": a `I promised: ...` note is saved (AUTO only).
- "What do you know about me?" / "What do you remember about me?": lists facts and your note. "What do you remember about A?" lists topic A. "Forget what we said about A": reads back, waits for yes; gist `#month` header stays. [0c]
- "What did you do?" after setting a timer and opening an app: lists exactly those. Right after a restart: ran nothing. [M4b]
- **Privacy** (Control Center PRIVACY on): "which apps are open", "what's on my calendar", "my to-dos" -> he gives counts/limited info, no names or titles. Turn off: details return. (Known: the privacy path is only checked with fakes.)

## 6. Alarms, timers, undo, volume (one pass)
- "Set a timer for 1 minute", then "Never mind Jarvis, undo." within 3 s -> "Removed that timer." immediately. [A2]
- Alarm for an hour already gone today -> "... tomorrow". "No, PM" after an alarm moves it 12 h; "undo" brings it back. "An alarm for 7 and a timer for 10 minutes" sets both; undo takes back both. "Snooze for 10", "5 minutes more". [0f, 0h]
- "Can you tell me if I have any alarms tomorrow?" -> alarm list only, no calendar events. "What alarms do I have", "cancel the second one" (confirm), "the fifth one" -> "Which one?". [A4, M1b]
- Volume: "the music is too loud" -> down; "knock the volume down by 20"; "louder and quieter" refused; confirmed volume says the real level. [0g]
- Mumble an alarm / "remember that ..." so Whisper is unsure: "Did you say ...?"; "no" -> "Cancelled.". [0i]
- Wallpaper / Wi-Fi off / hotspot: "I can't do that yet." (no fake "done"). "Make the screen dimmer" works as brightness. "Why is my screen dim?" is answered, not refused. [A1, D]

## 7. Windows actions (Phase 7 writes; all untested live)
Do these with ask-first rows, answering "yes" where asked. A bare "yes" with nothing pending does nothing.
- **Mic:** "mute the microphone" (asks) -> check Windows; click orb unmutes; "mic up a bit", "set the mic to 40"; "undo". "Which microphone are you using", "use the headset microphone" -> asks, applies next listen, Control Center row updates; "use the webcam microphone" -> can't find it; "use the default mic". [1b-3, 1b-14]
- **Brightness:** "brightness 50", "a bit brighter", "0", "above 100" answered, "undo"; level matches Windows. [1b-4, step 6]
- **Dark/light mode:** apps and Windows change, read back, undo. [1b-5]
- **Settings pages:** sound settings, night light/focus (opens page, says no switch), "what starts with windows", "are there updates". [1b-6]
- **Screenshot** appears in Pictures\Screenshots; "show the desktop"; "extend the screen" with a second monitor. [1b-7]
- **Recycle bin:** asks, says cannot be undone, empties. [1b-8]
- **Power mode:** "balanced mode" (asks, reads back, undo); "best performance" says no such plan if only Balanced; "power saver" refused. [1b-9]
- **Bluetooth:** off (asks) / on; "which bluetooth devices are connected"; "connect my headphones" -> asks, connects, "undo" disconnects; "connect to banana" -> no such device; radio off -> "turn it on first"; "pair a new device" opens page. Have the wired keyboard ready. [1b-10, 1b-15, steps 3-5]
- **Airplane mode** on (asks) then off: Wi-Fi/Bluetooth go off and return. [step 7]
- **Stealth:** "stealth mode" -> asks -> HUD STEALTH, pop-up only; leave via Control Center. "Mute yourself" = sound mute. [1b-13]
- **Open Chrome** (already running): existing window comes front, no second copy. Weather/news/prices: "I can't look that up yet." [1b-11, 1b-12]
- **Sleep:** "put my PC in sleep mode" -> asks, "Yes, Jarvis." -> screen off, standby (log `sleep: suspend refused ... screen off for Modern Standby` is normal), wake with a key. "Restart" -> asks; say "no" -> `left - no yes` (optional real restart with `shutdown /a` ready). SYSTEM > SLEEP does the same. "Go to sleep" with sleep off says the screen was turned off. [A5, A6, B6, 1b-2]
- **Confirmations:** "lock my computer": silence for 15 s does nothing; "yes" at once works; his own prompt echoing from the speakers is not taken as yes. [8-A1]

## 8. Diagnosis (Phase 9; start something heavy first)
- "Why is my PC slow?" names the app; "what's using my memory / graphics card" vs Task Manager; "why is the fan loud?"; "did anything crash today?" vs Event Viewer; router off: "is my internet working?"; nothing wrong: "is anything wrong?" gives numbers. [P9 1-7]
- "What's using my CPU" (heavy app): one sentence, "Want me to close it?"; "yes" closes only that app. "Kill explorer" / "close explorer": refused. [9-6, 9-5]
- Leave something heavy 5-15 min unasked: a silent pop-up appears. ERR pop-up clears in ~60 s; "what went wrong" still answers. DIAGNOSIS ASK OFF -> "Diagnosis is off." [P9 8, 9-1, 9-8]
- Time end-of-question to first word: target under 4 s (also measure in step 3 on a long conversation, since the memory window is now larger).

## 9. Typed input and quiet in class
- Control Center > TYPE TO HIM > TYPE "what time is it": reply in log, spoken unless muted. Type "lock my computer": he asks, and a **spoken** yes does NOT run it. Type while he is busy: "One moment, I'm busy." 600 characters cut to 500. [8d]
- During a class event on the quiet calendar: replies pop-up only, no chime, alarms silent. "You can talk" -> normal until the next class. [8c]
- Chime and start-up sound quiet (CHIME VOLUME); restart both: no "Jarvis online". [8b, Phase 8 step 5]

## 10. Voice and sound (by ear; Phase 10 slice 2)
- Times, percents, units: ask the time ("3 oh 5 PM"), battery percent, GB of memory, a temperature in degrees: said naturally. A reply with `chrome.exe` says "Chrome". Ellipsis/dashes make short pauses.
- Pronunciation file: add one test line to `Jarvis\pronounce.txt` (e.g. `Rainmeter=rain meter`), save, ask for it: new sound next turn, no restart. Remove it after.
- VOICE SPEED -/+ (0.8-1.2) with RESET: audibly faster/slower, both Kokoro and the Windows voice. Voice vector name mapping (slice 1): voice sounds as intended; report if it falls back.
- Replies on headphones vs speakers: the softer-voice item was **not built**; just note the difference.

## 11. Logs and data
- `Data\jarvis_log-YYYY-MM.txt` exists and grows each exchange; "forget" clears only `jarvis_log.txt`. [1b-16]
- One memory compaction: ask Claude for the short-test-age steps, paste the `compaction:` line (counts only). A game or LITE must not start it. [M3]
- Apply-SpaceshipUpdate with comments in a settings-add file: comments not appended. Fresh install: Setup-Jarvis.ps1 leaves JarvisPython blank, relative JarvisVoice, voice bm_lewis. Task Manager > GPU during a few turns. [0j, 1b-18, 6i]
- Alarm file unwritable: he says it was not saved. [0b] Memory offer: "Yes, Jarvis" saves; "carry on" counts as yes. [0e]

## 12. Control Center JARVIS tab (new and existing rows)
- New this phase: LEARN FACTS AUTO/ASK/OFF (default AUTO), SERIOUS TOPICS on, TALK LESS off, PRIVACY off, ROOM TALK QUIET/ASK (default QUIET), VOICE SPEED + RESET, NAME (EDIT opens Settings.inc; no text box yet). Each toggle changes, survives RELOAD, and the matching behaviour changes (steps 3-5, 10). Mouse wheel = 1 row per notch; click on the scroll track jumps; drag follows (note whether while moving or only on release). [B1-B3]
- CALL ME: type a name, Enter -> row shows it; "Hey Jarvis, hello." uses it; CLEAR -> NO NAME; `O'Neil` saves as ONeil. [B4, B5]
- AI ROUTER / GPU / LEARN / RECALL toggles, FIRST WORDS, IDLE UNLOAD, WAKE STRICT stay in limits; BLUETOOTH NAMES lists paired names; REMEMBERED FACTS count, OPEN shows file, FORGET ALL needs second click. NAME WINDOW, CHIME VOLUME, QUIET IN CLASS rows. [1b-19, Phase 8]
- **First real run of `control.lua` and `jarvis.lua` changes** (no Lua parser here): any blank row, wrong button or Rainmeter log error counts as a FAIL.
- WAKE TRAINING log after training: `train: Hey from N word samples`. [C3]

---

## Known gaps before you start (so you don't chase them)
- **Not built:** prompt-cases file + runner + model comparison (T10), headphone-softer voice (T7/J4, ticked in `tasks/phase10-slice2-todo.md` by mistake), temporary moods, streaming voice, voice training, speaker detection, Hey Clover wake model, NAME text input. Wake word stays "Hey Jarvis".
- **Unverified:** all Lua, real-model behaviour of the new prompt rules, every real Windows write, the voices, privacy mode beyond fakes.
- Privacy mode was tested with a fake only: if it leaks names, note it, don't stop the run.
- Memory window now keeps up to 40 messages for 20 min; if replies feel slow late in a long talk, report the `timing:` lines.

## Afterwards
Claude lists every finding with a proposed fix or "park"; you pick. Then update CURRENT STATE and the plan. Rollback: PART D "UNDO" with this copy's backup folder; in git, `git revert f63ada6 a542262 5b8b66c` for the latest Phase 10 and memory changes.

## Paste back
`route:`, `timing:`, `ear:`, `wake word heard`, `train:`, `stop words`, `transcript: dropped`, `sleep:`, `compaction:`, and any `Rainmeter` log error. Leave out `you:` lines if you prefer.
