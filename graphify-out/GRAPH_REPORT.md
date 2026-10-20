# Graph Report - RainmeterSpaceship  (2026-10-14)

## Corpus Check
- 9 files · ~894,056 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1621 nodes · 3313 edges · 187 communities (65 shown, 122 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 440 edges (avg confidence: 0.86)
- Token cost: 108,309 input · 0 output

## Community Hubs (Navigation)
- ShipCore C# Helper
- Cockpit Frame Builder
- Jarvis Core Turn Helpers
- Jarvis Imports and Main
- App Launcher (apps.lua)
- Notes Index and Reminders
- Command Parsing (amounts, times)
- Control Center (control.lua)
- Canvas Drawing Library
- Ollama Chat and GPU
- Memory Facts and Gists
- Context Building
- Jarvis Test Harness
- HUD Update Hooks
- Rainmeter Simulator
- Frame Render (numpy)
- Audio Endpoint COM
- Dial Widgets
- Simulator INI Parsing
- Barge-in and Speech Loop
- Controller Skin
- Systems Dial
- Command Replies and Undo
- Sphere and Sysinfo
- Jarvis Hologram
- Phase 6 Task Checkpoints
- Repair Plan Overview
- Repair Plan Features
- Reference Layout
- Animation Audit Tool
- HUD Guide and Rules
- Console Skin
- Fix Rounds 5-6 and Redesign
- GPU and Voice Phase
- Master Plan and Voice Check
- Phase 5-7 Live Tests
- Target Reticle
- Phase 6 Memory Plan
- README Feature List
- Memory Design Sources
- Layout Build Script
- Hearing and Follow-up Design
- Boot Sequence
- Panels Skin
- HUD Infrastructure Docs
- HWiNFO Readings
- Test Clock and Threads
- HUD Tier Skin
- Jarvis Log Skin
- Location Skin
- Status Block
- Audio Skin
- Drawer Skin
- Storage Skin
- Phase 1 Truth Design
- Image Frame Tool
- HUD Guide Topics
- Fix Rounds 1-4
- Presets
- Font Licences
- Vosk Stop Words
- Graph Skin
- Barge Test Fakes
- Fake Kokoro Output
- Alert Skin
- Layout Guard
- Power Skin
- HUD Guide Integrations
- BargeMic
- FakeKokoro
- _Proc
- _U32
- Sensor Sources
- BargeModel
- Fake Vosk Recognizer
- TrainOww
- cockpit-trace.svg (VTracer trace of cock
- State
- ahead()
- _BS
- CardWhisper
- FakeSess
- talk()
- OptWhisper
- Stop
- _Col
- FakeWhisper
- WakeModel
- Hologram shows status only

## God Nodes (most connected - your core abstractions)
1. `ShipCore` - 79 edges
2. `log()` - 54 edges
3. `exchange()` - 54 edges
4. `build()` - 38 edges
5. `setting()` - 37 edges
6. `H.text()` - 29 edges
7. `route()` - 29 edges
8. `H.init()` - 27 edges
9. `H.hit()` - 27 edges
10. `H.canvas()` - 26 edges

## Surprising Connections (you probably didn't know these)
- `Gates for every task (not repeated below)` --references--> `http_json()`  [INFERRED]
  tasks/plan.md → Skins/Spaceship/@Resources/Jarvis/jarvis.py
- `Risks` --references--> `related()`  [INFERRED]
  tasks/plan.md → Skins/Spaceship/@Resources/Jarvis/jarvis.py
- `Task 4: M4a-1, only matching facts in the prompt (S; about 15 lines)` --references--> `related()`  [INFERRED]
  tasks/plan.md → Skins/Spaceship/@Resources/Jarvis/jarvis.py
- `Task 5: M4a-2, save, replace, forget, "what do you know" (S–M; about 25 lines)` --references--> `route()`  [INFERRED]
  tasks/plan.md → Skins/Spaceship/@Resources/Jarvis/jarvis.py
- `Task 8: M3a, daily compaction into checked facts (M; about 35 lines)` --references--> `http_json()`  [INFERRED]
  tasks/plan.md → Skins/Spaceship/@Resources/Jarvis/jarvis.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Jarvis voice pipeline** — skins_spaceship__resources_docs_spaceship_hud_guide_wakeword, skins_spaceship__resources_docs_spaceship_hud_guide_whisper, skins_spaceship__resources_docs_spaceship_hud_guide_ollama, skins_spaceship__resources_docs_spaceship_hud_guide_jarvisskills [EXTRACTED 0.95]
- **Layout to frame build pipeline** — tools_ref_layout, layout_layout, tools_build, tools_ship_frame, tools_frame_render, tools_package [EXTRACTED 1.00]
- **Performance tier system** — concept_perf_tiers, concept_controller, concept_dgpu_hygiene [INFERRED 0.85]
- **HUD modules fed by ShipCore data files** — skins_spaceship__resources_docs_spaceship_hud_guide_shipcore, skins_spaceship__resources_docs_spaceship_hud_guide_missionclock, skins_spaceship__resources_docs_spaceship_hud_guide_systemsdial, skins_spaceship__resources_docs_spaceship_hud_guide_secretsstorage [INFERRED 0.85]
- **Redesign pipeline slices A-H (front door to output)** — jarvis_repair_plan_hearing_gate, jarvis_repair_plan_understand_decision, jarvis_repair_plan_lanes_info_no_data, jarvis_repair_plan_follow_up_gate, jarvis_repair_plan_output_sink_typing, jarvis_repair_plan_stop_while_speaking, jarvis_repair_plan_slice_g_wake_rows, jarvis_repair_plan_slice_h_cleanup [EXTRACTED 1.00]
- **Phase 6b memory layers L1-L4** — tasks_plan_m1_active_window, tasks_plan_m2_topic_memory, tasks_plan_m3_compaction, tasks_plan_m4a_user_facts, tasks_plan_m4b_action_list [EXTRACTED 1.00]
- **Prior art the memory design draws on** — tasks_plan_memgpt_letta, tasks_plan_generative_agents, tasks_plan_mem0, tasks_plan_chatgpt_memory [EXTRACTED 1.00]

## Communities (187 total, 122 thin omitted)

### Community 0 - "ShipCore C# Helper"
Cohesion: 0.05
Nodes (8): CalendarForm, CalEvent, CalSource, COPYDATASTRUCT, GmailForm, Prop, ShipCore, Vevent

### Community 1 - "Cockpit Frame Builder"
Cohesion: 0.06
Nodes (34): at(), build(), beam(), H_ellipse(), hose(), lamp(), P(), ring() (+26 more)

### Community 2 - "Jarvis Core Turn Helpers"
Cohesion: 0.06
Nodes (36): active(), alarm(), ask_yes(), clock(), convo_add(), describe(), ding(), exchange() (+28 more)

### Community 3 - "Jarvis Imports and Main"
Cohesion: 0.05
Nodes (27): act_close(), act_todo(), confirmed(), context(), _decode(), far_add(), first_words(), info_blocks() (+19 more)

### Community 4 - "App Launcher (apps.lua)"
Cohesion: 0.09
Nodes (46): A.entry(), A.getState(), A.launch(), A.load(), A.loadAll(), A.loadStart(), A.notFound(), A.parseIni() (+38 more)

### Community 5 - "Notes Index and Reminders"
Cohesion: 0.07
Nodes (30): chroma_index(), _chunks(), closeness(), due_reminders(), index_loop(), list_mics(), load_meaning(), log() (+22 more)

### Community 6 - "Command Parsing (amounts, times)"
Cohesion: 0.06
Nodes (24): amount(), as_said(), best_app(), calc(), convert(), duration(), fact_answer(), for_ear() (+16 more)

### Community 7 - "Control Center (control.lua)"
Cohesion: 0.12
Nodes (40): applyTheme(), arm(), bump(), colorRow(), copyFile(), core(), cycle(), cycleSlot() (+32 more)

### Community 8 - "Canvas Drawing Library"
Cohesion: 0.15
Nodes (39): Canvas:arc(), Canvas:brackets(), Canvas:chamfer(), Canvas:circle(), Canvas:dashArc(), Canvas:dot(), Canvas:fillCircle(), Canvas:fillPoly() (+31 more)

### Community 9 - "Ollama Chat and GPU"
Cohesion: 0.08
Nodes (26): ask_gist(), chat_stream(), chat_to_gpu(), go(), cpu_in_use(), cpu_threads(), _cuda_dlls(), ensure_ollama() (+18 more)

### Community 10 - "Memory Facts and Gists"
Cohesion: 0.08
Nodes (20): compact(), fact_save(), facts_about(), file_talk(), gist_for(), gist_ok(), keywords(), load_gist() (+12 more)

### Community 11 - "Context Building"
Cohesion: 0.08
Nodes (21): about_me(), ask_ai(), chime(), ctx_tokens(), file_active(), fit_context(), fix_route(), follow_wait() (+13 more)

### Community 12 - "Jarvis Test Harness"
Cohesion: 0.06
Nodes (9): blocks(), do(), _Done, _Resp, _run(), run_wake(), _S, _Smi (+1 more)

### Community 13 - "HUD Update Hooks"
Cohesion: 0.18
Nodes (34): alerts(), Update(), P(), placeHits(), Update(), Update(), drawSchematic(), drawTabs() (+26 more)

### Community 14 - "Rainmeter Simulator"
Cohesion: 0.11
Nodes (24): discover(), draw_shape(), draw_text(), eval_formula(), font_for(), inside_grown(), lua_syntax_check(), main() (+16 more)

### Community 15 - "Frame Render (numpy)"
Cohesion: 0.17
Nodes (16): blur(), _box(), _busy(), corners_png(), glass_fx_png(), highlights(), hull_png(), mist_png() (+8 more)

### Community 16 - "Audio Endpoint COM"
Cohesion: 0.11
Nodes (5): IAudioEndpointVolume, IMMDevice, IMMDeviceEnumerator, MicVolume, MMDeviceEnumeratorCom

### Community 17 - "Dial Widgets"
Cohesion: 0.09
Nodes (18): Initialize(), OnClick(), timeToLimit(), Initialize(), Initialize(), H.guard(), H.hw(), H.init() (+10 more)

### Community 18 - "Simulator INI Parsing"
Cohesion: 0.10
Nodes (4): mock_value(), parse_ini(), Skin, rep()

### Community 19 - "Barge-in and Speech Loop"
Cohesion: 0.09
Nodes (12): barge_in(), barge_turn(), compact_due(), daily_memory(), heard_speech(), hud_tier(), mic_device(), record() (+4 more)

### Community 20 - "Controller Skin"
Cohesion: 0.22
Nodes (21): OnStatus(), checkMonitor(), DetectSensors(), findHome(), fitTo(), Initialize(), Master(), OnCore() (+13 more)

### Community 21 - "Systems Dial"
Cohesion: 0.16
Nodes (20): apply(), buildControls(), ctl(), frac(), Initialize(), label(), now(), OnClick() (+12 more)

### Community 22 - "Command Replies and Undo"
Cohesion: 0.13
Nodes (12): act_volume(), can_undo(), _com(), command_reply(), did_add(), done_line(), duck(), run_action() (+4 more)

### Community 23 - "Sphere and Sysinfo"
Cohesion: 0.10
Nodes (12): OnSPX(), H.sval(), Initialize(), OnClick(), OnISS(), X(), Y(), Initialize() (+4 more)

### Community 24 - "Jarvis Hologram"
Cohesion: 0.16
Nodes (18): buildPlexus(), colorSetting(), command(), drawScene(), exists(), Forget(), frameFile(), hidden() (+10 more)

### Community 25 - "Phase 6 Task Checkpoints"
Cohesion: 0.11
Nodes (19): Checkpoint A: commit on the user's word (live checks saved for the end of Phase 6), Checkpoint B: commit on the user's word (live checks saved for the end of Phase 6), Dependency graph, Gates for every task (not repeated below), Live tests: all at the end of Phase 6 (the user, 2026-10-14), Open questions, Risks (added for this breakdown), Task 11: 6j, route + timing log (XS; about 10 lines) (+11 more)

### Community 26 - "Repair Plan Overview"
Cohesion: 0.15
Nodes (16): JARVIS Repair Plan (master copy), The 26 reported issues, Checks after every phase (Part E), Current State / Handover, GPU Measurement (C2), HUD-daemon command/state files (jarvis_cmd.txt / jarvis.txt), The 28 Reported Issues, Research sources (Part H) (+8 more)

### Community 27 - "Repair Plan Features"
Cohesion: 0.14
Nodes (16): ACTIONS fixed entries (only things that can run), Barge-in levels off, wake, voice, aec, Continuous alarm ring with gap listening, Answers by code: time, date, sums, conversions, Phase 0: Measure First, Phase 1: He Tells The Truth And Commands Really Run, Phase 5: Alarms That Behave Like Alarms, Snooze (Phase 5b) (+8 more)

### Community 29 - "Reference Layout"
Cohesion: 0.18
Nodes (9): _arc(), main(), mquad(), P(), persp(), quad(), rect(), scale() (+1 more)

### Community 30 - "Animation Audit Tool"
Cohesion: 0.23
Nodes (4): main(), load(), layout_ini(), main()

### Community 31 - "HUD Guide and Rules"
Cohesion: 0.13
Nodes (13): Project instructions (CLAUDE.md), Audio reactor, Jarvis voice assistant, Jarvis skills (actions, readings, timers), Obsidian to-do note, Ollama local model, Smart note search (ChromaDB), Target reticle (+5 more)

### Community 32 - "Console Skin"
Cohesion: 0.23
Nodes (13): buttons(), cycle(), hybridIndex(), OnClick(), OnLltDone(), OnRightClick(), runLlt(), RX() (+5 more)

### Community 33 - "Fix Rounds 5-6 and Redesign"
Cohesion: 0.14
Nodes (14): COURTESY fixed-reply table, Fix Round 5: He Wakes On Noise (N0-N3), Fix Round 6: Live Findings L1-L10, Hearing gate + control check (Slice A), Model check: qwen3 4B vs llama3.2 3B, Pop-up typing at speaking pace (Slice E), Wake rows and stricter default (Slice G), Clean-up scan (Slice H) (+6 more)

### Community 34 - "GPU and Voice Phase"
Cohesion: 0.16
Nodes (14): GPU measurements (RTX 5070 and Radeon 880M), GPU watch (sticky fallback fix), Shorter conversation history (4 messages, 2 minutes), Kokoro voice on GPU (2e, onnxruntime-gpu 1.23.2), Memory relook and JarvisLearn offer, Phase 2: GPU First, Phase 6: Relevance, Memory, Sounding Human, Smoother voice (6g) (+6 more)

### Community 35 - "Master Plan and Voice Check"
Cohesion: 0.21
Nodes (7): Spaceship HUD Master Plan, layout.json, check(), main(), render(), convex_overlap(), in_safe_area()

### Community 36 - "Phase 5-7 Live Tests"
Cohesion: 0.19
Nodes (11): Airplane mode via Wi-Fi and Bluetooth radios, Bluetooth and connect-to by voice, Part E: Checks After Every Phase, Lanes + info no-data fixed reply (Slice C), Phase 10: Personality And Voice, Phase 6 Live Test Checklist, Phase 7: More Settings By Voice, M1b last results ("the second one") (+3 more)

### Community 37 - "Target Reticle"
Cohesion: 0.25
Nodes (12): countdown(), inside(), OnClick(), OnRightClick(), OnScroll(), parseTodos(), pickNext(), refreshTodos() (+4 more)

### Community 38 - "Phase 6 Memory Plan"
Cohesion: 0.15
Nodes (13): 6a in detail, 6b. The memory design: four layers, one path, After approval, Context, Order and checkpoints, Phase 10: Personality and voice (parked, not built now), Phase 6 after the change, Phase 6 plan (revised 2026-10-14) (+5 more)

### Community 39 - "README Feature List"
Cohesion: 0.20
Nodes (11): App launcher slots and category panels, Cockpit Frame (hull, glass, accents), Control Center (Aurum-style settings), Home monitor / AutoFit handling, Layout guard (overlap checker), Presets with undo, Spaceship HUD README, Apps.ini app catalog (+3 more)

### Community 40 - "Memory Design Sources"
Cohesion: 0.23
Nodes (10): chromadb 1.5.9, ChatGPT memory (saved memories + chat history), Generative Agents (Park et al., 2023), keywords() / related() / meaning() matching, M1 active window (last 2 exchanges, 120 s), M2 topic memory (jarvis_topics.json), M3 compaction into code-checked gist facts, M4a user facts (matching only, Replace?, offer to remember) (+2 more)

### Community 41 - "Layout Build Script"
Cohesion: 0.36
Nodes (9): fnum(), geometry_inc(), key_of(), main(), meters_inc(), skin_geometry(), zones_lua(), matrix() (+1 more)

### Community 42 - "Hearing and Follow-up Design"
Cohesion: 0.18
Nodes (11): Autocorrect layer and Whisper settings, Follow-up gate + undo window (Slice D), Follow-up windows (3 s / 10 s with name), JarvisMic microphone selection, Music ducking while listening, Name normalisation (Travis, droves aliases), New settings this plan adds (Part F), Phase 3: Hearing You Correctly (+3 more)

### Community 43 - "Boot Sequence"
Cohesion: 0.35
Nodes (9): bang(), buildOrder(), color(), finish(), Initialize(), num(), readings(), rel() (+1 more)

### Community 44 - "Panels Skin"
Cohesion: 0.25
Nodes (8): H.llt(), OnClick(), OnRightClick(), rows(), span(), Update(), utcOffset(), week()

### Community 45 - "HUD Infrastructure Docs"
Cohesion: 0.20
Nodes (7): Controller skin (tiers, app scan, helper), HWiNFO sensor integration, Lenovo Legion Toolkit CLI (GPU modes), MASTER kill switch, DPAPI-encrypted secrets storage, ShipCore helper (compiled C#), Spaceship HUD Setup Guide

### Community 46 - "HWiNFO Readings"
Cohesion: 0.20
Nodes (6): cpu_times(), hw_value(), sensors(), cpu(), hw(), sound()

### Community 47 - "Test Clock and Threads"
Cohesion: 0.24
Nodes (3): _Clock, ring_alarm(), within()

### Community 48 - "HUD Tier Skin"
Cohesion: 0.24
Nodes (6): ease(), Initialize(), ladder(), OnClick(), X(), Y()

### Community 49 - "Jarvis Log Skin"
Cohesion: 0.29
Nodes (7): build(), Initialize(), OnClick(), OnRightClick(), OnScroll(), readAll(), Update()

### Community 50 - "Location Skin"
Cohesion: 0.27
Nodes (6): countdown(), Initialize(), load(), OnClick(), Update(), when()

### Community 51 - "Status Block"
Cohesion: 0.29
Nodes (7): n(), OnClick(), OnRightClick(), OnRun(), readMail(), rows(), Update()

### Community 52 - "Audio Skin"
Cohesion: 0.25
Nodes (6): glyph(), Initialize(), media(), OnClick(), OnRightClick(), OnScroll()

### Community 53 - "Drawer Skin"
Cohesion: 0.33
Nodes (6): build(), Focus(), OnClick(), OnScroll(), Update(), H.hideHit()

### Community 54 - "Storage Skin"
Cohesion: 0.31
Nodes (6): Initialize(), OnClick(), short(), Update(), X(), Y()

### Community 55 - "Phase 1 Truth Design"
Cohesion: 0.25
Nodes (5): AI fallback interpret (checked, never first reader), Phase 9: Ask Him What Is Wrong (Diagnosis), JarvisWatch silent pop-up warnings, System snapshot (diag.ps1) and event log findings, Daily briefing

### Community 56 - "Image Frame Tool"
Cohesion: 0.32
Nodes (3): cover(), main(), window_mask()

### Community 57 - "HUD Guide Topics"
Cohesion: 0.32
Nodes (7): Spaceship HUD Complete Guide, Apps.ini app catalog, Control Center, HWiNFO sensor data, Startup boot sequence, Update installer (Apply-SpaceshipUpdate), Sounds guide

### Community 58 - "Fix Rounds 1-4"
Cohesion: 0.38
Nodes (7): BEFORE PHASE 5 live test (sections S, A-F) and Q1-Q15, Fix rounds 1-4 (AI fallback interpret, one schedule, round 4 complaints), Found while building N1-N12, N7 timer rounding test flake, Phase 4: Interrupting Him, Stop key End (RegisterHotKey while busy), Instant stop (stop_now)

### Community 59 - "Presets"
Cohesion: 0.29
Nodes (7): Presets (save/load/undo), Preset slot 2 README, Preset slot 3 README, Preset slot 4 README, Preset slot 5 README, Preset slot 6 README, Preset undo README

### Community 60 - "Font Licences"
Cohesion: 0.29
Nodes (7): OFL licence B612 Mono, OFL licence Michroma, OFL licence Orbitron, OFL licence Oxanium, OFL licence Rajdhani, OFL licence Share Tech Mono, SIL Open Font License

### Community 62 - "Graph Skin"
Cohesion: 0.57
Nodes (5): OnClick(), OnRightClick(), OnScroll(), setSource(), Update()

### Community 63 - "Barge Test Fakes"
Cohesion: 0.33
Nodes (3): barge(), run_key(), sleep()

### Community 66 - "Layout Guard"
Cohesion: 0.60
Nodes (5): G.check(), G.checkAll(), inSafe(), moved(), sep()

### Community 68 - "HUD Guide Integrations"
Cohesion: 0.40
Nodes (4): Lenovo Legion Toolkit, Mission clock (calendar), ShipCore helper, Systems dial

### Community 78 - "cockpit-trace.svg (VTracer trace of cock"
Cohesion: 0.67
Nodes (3): cockpit-posterized.svg (VTracer trace of cockpit artwork), cockpit-trace.svg (VTracer trace of cockpit artwork, 1260x709, dark navy base), reference-simplified.svg (simplified VTracer trace of cockpit reference)

## Ambiguous Edges - Review These
- `Settings update snippet (network, captions, data links)` → `UPDATE.txt (update part marker)`  [AMBIGUOUS]
  Skins/Spaceship/UPDATE.txt · relation: conceptually_related_to

## Knowledge Gaps
- **60 isolated node(s):** `Preset slots (1-6, _undo)`, `UPDATE.txt (update part marker)`, `jarvis.py voice service`, `Audio reactor`, `Ollama local model` (+55 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 575 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **122 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Skin` connect `Simulator INI Parsing` to `Controller Skin`, `Animation Audit Tool`, `Rainmeter Simulator`?**
  _High betweenness centrality (0.315) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `exchange()` (e.g. with `prepare_fillers()` and `watchdog()`) actually correct?**
  _`exchange()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Preset slots (1-6, _undo)`, `UPDATE.txt (update part marker)`, `jarvis.py voice service` to the rest of the system?**
  _60 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ShipCore C# Helper` be split into smaller, more focused modules?**
  _Cohesion score 0.053211351755041075 - nodes in this community are weakly interconnected._
- **Why does `ShipCore` connect `ShipCore C# Helper` to `ShipCore .NET Imports`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `build()` (e.g. with `.ellipse()` and `.line()`) actually correct?**
  _`build()` has 5 INFERRED edges - model-reasoned connections that need verification._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Settings update snippet (network, captions, data links)` and `UPDATE.txt (update part marker)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._