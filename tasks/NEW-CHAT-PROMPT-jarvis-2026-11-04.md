You are picking up the JARVIS live-test feedback loop. Read these first, in order, and run nothing until you have:
1. CLAUDE.md and CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md (repo root)
2. tasks/HANDOFF-jarvis-semi-live.md, section 6, top entry "2026-11-04 n" (state, evidence, what is applied, what is not)
3. tasks/HANDOFF-jarvis-refactor-and-live-test-2026-11-04.md (how to investigate, traps, the gate) and Skins/Spaceship/@Resources/Jarvis/ARCHITECTURE.md
4. tasks/jarvis-chat-quality-plan-2026-11-04.md (the plan for F3)
Use Grep to jump into big files (jarvis.py, routing.py), do not read them whole. Work only in Skins/Spaceship/@Resources/Jarvis/ and tasks/.
Do not touch SpaceshipApp/, GodMode/, Refrences-Art/, tools/blender/, tools/contract_check.py, Settings.inc, or any process that is not yours.
No commit, merge or push unless I say so. Fix in the worktree C:\Users\Senai\RainmeterSpaceship-refactor (branch refactor/jarvis-pipeline) or a scratch
copy, ship as a patch in tasks/, apply to the live checkout only after my yes. Report real command output only.

STATE (verify with git log -1 and git status): live checkout C:\Users\Senai\RainmeterSpaceship, main at adda63f, plus UNCOMMITTED, already applied:
- F1 patch tasks/jarvis-f1-wasapi-buffer.patch (WASAPI buffer 0.1 s, setting JarvisPlayerLatency, 0 = old "low")
- F2 patch tasks/jarvis-f2-typed-text-only.patch (typed chat text is answered in the chat only, never spoken)
The running JARVIS needs a restart to use them. The worktree has the same changes plus the old uncommitted refactor phase 6f.
Not verified: the live checkout got only a syntax check after the patches (full gate was green on the worktree). F1/F2 mutation checks were not completed.
TRAP: a mutated test_jarvis run can HANG instead of failing: always use `timeout 300`. Unload Ollama after runs (keep_alive 0). RAM is tight.

OPEN ITEMS, in this order:
1. F1 "cracked speech on speakers": still small glitches, but smaller after the 0.1 s buffer. Blind A/B by ear (user, one listen each): own 48 kHz resample
   glitched, the current Windows-converted path was clean, the 100 ms buffer smoothest. Silent sandbox tests found no clipping, no GPU/CPU difference, no
   underflow. Next: more blind A/B rounds (first slot a throwaway, try 0.2 s), Windows audio enhancements/spatial sound on the Realtek device, the mic stream
   in the same process, and log the device underflow count and per-reply peak (diagnostic only). The A/B scripts are in the old session scratchpad and are gone: rewrite.
2. F2: ask the user to confirm typed replies now stay in the chat after a restart (and that alarms still speak).
3. F3 wake word too hard, "assumes misunderstandings", no jesting: follow the plan file. First ask the user for 10-20 real example lines and a yes to
   record wake clips with tools/hearing_eval.py. Then baselines on both models (llama3.1:8b and the 3B), same hour, seed 7, before changing anything.
4. "Blocked" messages: explained in the log entry (Windows Application Control policy blocks unsigned DLLs: CSpace.dll, ShipCore.Core.dll, cublas64_12.dll,
   scipy .pyd; Windhawk). The fix (sign them, or a supplemental policy) is the user's decision; do not change system policy.

For each note the user sends: number it (F4, F5, ...), restate it in one line, find evidence in Data\jarvis.log (route:, timing:, voice gaps:, player:, ear:),
say what is confirmed / likely / unknown, propose the smallest fix BEFORE changing anything and wait for my yes when it changes what he says, a setting
default or timing. Every fix gets a test that fails without it, then the full gate in the handoff, and a log entry at the top of section 6.
Start by reading the files, then tell me what is applied and what is verified, and ask me for my first note.
