# Graph Report - RainmeterSpaceship  (2026-10-14)

## Corpus Check
- 148 files · ~878,884 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 56 file(s) not represented in the graph (top: .ini 37, .ttf 12, (none) 3)

## Summary
- 1526 nodes · 3193 edges · 184 communities (64 shown, 120 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 453 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `aa3a48de`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ShipCore C# Helper
- Cockpit Frame Builder
- apps.lua
- jarvis.py
- log
- control.lua
- alarm
- lib.lua
- H.text
- turn
- rmsim.py
- frame_render.py
- http_json
- H.init
- test_jarvis.py
- IAudioEndpointVolume
- Skin
- dial.lua
- layoutlib.py
- route
- jarvis.lua
- ref_layout.py
- .bang
- Spaceship HUD README
- Tasks
- console.lua
- Jarvis voice assistant
- check_layout.py
- gpu
- keywords
- Update
- hud.lua
- Spaceship HUD Complete Guide
- audio.lua
- build.py
- BEFORE PHASE 5 live test (sections S, A-F) and Q1-Q15
- Phase 2 GPU first
- boot.lua
- status_block.lua
- Context blocks sent only when the question needs them
- Update
- Update
- sphere.lua
- strip.lua
- JARVIS Assumed Settings and Guide
- H.set
- Update
- Update
- H.sval
- Phase 3 Hearing you correctly
- Presets (save/load/undo)
- SIL Open Font License
- Update
- ACTIONS fixed entries (only things that can run)
- Phase 1 He tells the truth and commands really run
- Follow-up windows (3 s / 10 s with name)
- barge
- _Out
- wake_loop
- G.check
- category.lua
- ShipCore helper
- BargeMic
- FakeKokoro
- _Proc
- _U32
- sources.lua
- BargeModel
- cockpit-trace.svg (VTracer trace of cockpit artwork, 1260x709, dark navy base)
- ShipCore helper (compiled C#)
- Jarvis skills (actions, readings, timers)
- State
- ahead
- _BS
- CardWhisper
- FakeSess
- talk
- OptWhisper
- ring_alarm
- Stop
- _Col
- FakeWhisper
- WakeModel
- Hologram shows status only
- _Resp
- sensors
- TrainOww

## God Nodes (most connected - your core abstractions)
1. `ShipCore` - 79 edges
2. `turn()` - 62 edges
3. `log()` - 52 edges
4. `build()` - 38 edges
5. `setting()` - 36 edges
6. `H.text()` - 30 edges
7. `route()` - 28 edges
8. `H.init()` - 28 edges
9. `H.hit()` - 28 edges
10. `H.canvas()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `Gates for every task (not repeated below)` --references--> `http_json()`  [INFERRED]
  tasks/plan.md → Skins/Spaceship/@Resources/Jarvis/jarvis.py
- `Task 8: M3a, daily compaction into checked facts (M; about 35 lines)` --references--> `http_json()`  [INFERRED]
  tasks/plan.md → Skins/Spaceship/@Resources/Jarvis/jarvis.py
- `Task 5: M4a-2, save, replace, forget, "what do you know" (S–M; about 25 lines)` --references--> `route()`  [INFERRED]
  tasks/plan.md → Skins/Spaceship/@Resources/Jarvis/jarvis.py
- `Risks` --references--> `related()`  [INFERRED]
  tasks/plan.md → Skins/Spaceship/@Resources/Jarvis/jarvis.py
- `Task 4: M4a-1, only matching facts in the prompt (S; about 15 lines)` --references--> `related()`  [INFERRED]
  tasks/plan.md → Skins/Spaceship/@Resources/Jarvis/jarvis.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ways to stop JARVIS: click, End key, barge-in via wake word or voice** — jarvis_repair_plan_stop_now, jarvis_repair_plan_stop_key_end, jarvis_repair_plan_barge_in, jarvis_repair_plan_wake_word [EXTRACTED 0.95]
- **Jarvis voice pipeline** — skins_spaceship__resources_docs_spaceship_hud_guide_wakeword, skins_spaceship__resources_docs_spaceship_hud_guide_whisper, skins_spaceship__resources_docs_spaceship_hud_guide_ollama, skins_spaceship__resources_docs_spaceship_hud_guide_jarvisskills [EXTRACTED 0.95]
- **Phases 2-4 built together and live-tested before Phase 5** — jarvis_repair_plan_phase_2, jarvis_repair_plan_phase_3, jarvis_repair_plan_phase_4, jarvis_repair_plan_before_phase_5_test [EXTRACTED 0.95]
- **Layout to frame build pipeline** — tools_ref_layout, layout_layout, tools_build, tools_ship_frame, tools_frame_render, tools_package [EXTRACTED 1.00]
- **GPU stack: Whisper small.en, Kokoro on onnxruntime-gpu, llama3.1:8b on one RTX** — jarvis_repair_plan_stronger_models, jarvis_repair_plan_kokoro_on_gpu, jarvis_repair_plan_gpu_watch, skins_spaceship__resources_jarvis_requirements_gpu_onnxruntime_gpu [INFERRED 0.85]
- **Performance tier system** — concept_perf_tiers, concept_controller, concept_dgpu_hygiene [INFERRED 0.85]
- **HUD modules fed by ShipCore data files** — skins_spaceship__resources_docs_spaceship_hud_guide_shipcore, skins_spaceship__resources_docs_spaceship_hud_guide_missionclock, skins_spaceship__resources_docs_spaceship_hud_guide_systemsdial, skins_spaceship__resources_docs_spaceship_hud_guide_secretsstorage [INFERRED 0.85]

## Communities (184 total, 120 thin omitted)

### Community 0 - "ShipCore C# Helper"
Cohesion: 0.05
Nodes (8): CalendarForm, CalEvent, CalSource, COPYDATASTRUCT, GmailForm, Prop, ShipCore, Vevent

### Community 1 - "Cockpit Frame Builder"
Cohesion: 0.06
Nodes (34): at(), build(), beam(), H_ellipse(), hose(), lamp(), P(), ring() (+26 more)

### Community 2 - "apps.lua"
Cohesion: 0.12
Nodes (31): A.launch(), A.load(), A.loadAll(), A.loadStart(), A.notFound(), A.parseIni(), A.resolve(), A.writeIconQueue() (+23 more)

### Community 3 - "jarvis.py"
Cohesion: 0.05
Nodes (25): act_close(), act_todo(), act_volume(), _com(), confirmed(), context(), _decode(), done_line() (+17 more)

### Community 4 - "log"
Cohesion: 0.08
Nodes (26): chroma_index(), _chunks(), due_reminders(), index_loop(), _kokoro(), list_mics(), load_meaning(), log() (+18 more)

### Community 5 - "control.lua"
Cohesion: 0.12
Nodes (40): applyTheme(), arm(), bump(), colorRow(), copyFile(), core(), cycle(), cycleSlot() (+32 more)

### Community 6 - "alarm"
Cohesion: 0.06
Nodes (35): alarm(), can_undo(), clock(), command_reply(), convo_add(), describe(), did_add(), ding() (+27 more)

### Community 7 - "lib.lua"
Cohesion: 0.16
Nodes (37): Canvas:arc(), Canvas:brackets(), Canvas:chamfer(), Canvas:circle(), Canvas:dashArc(), Canvas:dot(), Canvas:fillCircle(), Canvas:fillPoly() (+29 more)

### Community 8 - "H.text"
Cohesion: 0.27
Nodes (26): alerts(), Update(), P(), placeHits(), Update(), Update(), drawSchematic(), drawTabs() (+18 more)

### Community 9 - "turn"
Cohesion: 0.08
Nodes (26): about_me(), active(), ask_ai(), chat_stream(), chime(), ctx_tokens(), file_active(), first_words() (+18 more)

### Community 10 - "rmsim.py"
Cohesion: 0.11
Nodes (24): discover(), draw_shape(), draw_text(), eval_formula(), font_for(), inside_grown(), lua_syntax_check(), main() (+16 more)

### Community 11 - "frame_render.py"
Cohesion: 0.17
Nodes (16): blur(), _box(), _busy(), corners_png(), glass_fx_png(), highlights(), hull_png(), mist_png() (+8 more)

### Community 12 - "http_json"
Cohesion: 0.14
Nodes (12): chat_to_gpu(), go(), ensure_ollama(), filler(), go(), http_json(), installed_models(), ollama_on_cpu() (+4 more)

### Community 13 - "H.init"
Cohesion: 0.12
Nodes (14): Initialize(), OnClick(), A.entry(), A.getState(), Initialize(), Initialize(), Initialize(), Initialize() (+6 more)

### Community 14 - "test_jarvis.py"
Cohesion: 0.06
Nodes (9): blocks(), do(), _Done, hm(), _run(), run_wake(), _S, _Smi (+1 more)

### Community 15 - "IAudioEndpointVolume"
Cohesion: 0.11
Nodes (5): IAudioEndpointVolume, IMMDevice, IMMDeviceEnumerator, MicVolume, MMDeviceEnumeratorCom

### Community 16 - "Skin"
Cohesion: 0.10
Nodes (4): mock_value(), parse_ini(), Skin, rep()

### Community 17 - "dial.lua"
Cohesion: 0.15
Nodes (22): apply(), buildControls(), ctl(), draw(), frac(), Initialize(), label(), now() (+14 more)

### Community 18 - "layoutlib.py"
Cohesion: 0.15
Nodes (7): main(), cover(), main(), window_mask(), load(), layout_ini(), main()

### Community 19 - "route"
Cohesion: 0.06
Nodes (22): as_said(), best_app(), calc(), duration(), fact_answer(), fact_save(), facts_about(), fix_route() (+14 more)

### Community 20 - "jarvis.lua"
Cohesion: 0.16
Nodes (18): buildPlexus(), colorSetting(), command(), drawScene(), exists(), Forget(), frameFile(), hidden() (+10 more)

### Community 22 - "ref_layout.py"
Cohesion: 0.18
Nodes (9): _arc(), main(), mquad(), P(), persp(), quad(), rect(), scale() (+1 more)

### Community 23 - ".bang"
Cohesion: 0.23
Nodes (20): OnStatus(), checkMonitor(), DetectSensors(), findHome(), fitTo(), Initialize(), Master(), OnHwScan() (+12 more)

### Community 24 - "Spaceship HUD README"
Cohesion: 0.15
Nodes (13): App launcher slots and category panels, Cockpit Frame (hull, glass, accents), Control Center (Aurum-style settings), Controller skin (tiers, app scan, helper), HWiNFO sensor integration, Layout guard (overlap checker), Lenovo Legion Toolkit CLI (GPU modes), MASTER kill switch (+5 more)

### Community 25 - "Tasks"
Cohesion: 0.05
Nodes (34): amount(), convert(), for_ear(), unit(), 6b. The memory design: four layers, one path, After approval, Checkpoint A: commit on the user's word (live checks saved for the end of Phase 6), Checkpoint B: commit on the user's word (live checks saved for the end of Phase 6) (+26 more)

### Community 26 - "console.lua"
Cohesion: 0.19
Nodes (13): buttons(), cycle(), hybridIndex(), Initialize(), OnClick(), OnLltDone(), OnRightClick(), runLlt() (+5 more)

### Community 27 - "Jarvis voice assistant"
Cohesion: 0.19
Nodes (12): Project instructions (CLAUDE.md), Jarvis voice assistant, Obsidian to-do note, Ollama local model, Smart note search (ChromaDB), Target reticle, Wake word (openWakeWord), Whisper speech recognition (+4 more)

### Community 28 - "check_layout.py"
Cohesion: 0.21
Nodes (7): Spaceship HUD Master Plan, layout.json, check(), main(), render(), convex_overlap(), in_safe_area()

### Community 29 - "gpu"
Cohesion: 0.15
Nodes (11): ask_gist(), cpu_in_use(), cpu_threads(), _cuda_dlls(), gpu(), gpu_watch(), _load_whisper(), card() (+3 more)

### Community 30 - "keywords"
Cohesion: 0.08
Nodes (21): compact(), file_talk(), gist_for(), gist_ok(), keywords(), load_gist(), load_topics(), meaning() (+13 more)

### Community 31 - "Update"
Cohesion: 0.25
Nodes (12): countdown(), inside(), OnClick(), OnRightClick(), OnScroll(), parseTodos(), pickNext(), refreshTodos() (+4 more)

### Community 32 - "hud.lua"
Cohesion: 0.24
Nodes (6): ease(), Initialize(), ladder(), OnClick(), X(), Y()

### Community 33 - "Spaceship HUD Complete Guide"
Cohesion: 0.21
Nodes (10): Home monitor / AutoFit handling, Spaceship HUD Complete Guide, Apps.ini app catalog, Control Center, HWiNFO sensor data, Startup boot sequence, Update installer (Apply-SpaceshipUpdate), Sounds guide (+2 more)

### Community 34 - "audio.lua"
Cohesion: 0.25
Nodes (6): glyph(), Initialize(), media(), OnClick(), OnRightClick(), OnScroll()

### Community 35 - "build.py"
Cohesion: 0.36
Nodes (9): fnum(), geometry_inc(), key_of(), main(), meters_inc(), skin_geometry(), zones_lua(), matrix() (+1 more)

### Community 36 - "BEFORE PHASE 5 live test (sections S, A-F) and Q1-Q15"
Cohesion: 0.24
Nodes (11): Barge-in levels off, wake, voice, aec, BEFORE PHASE 5 live test (sections S, A-F) and Q1-Q15, Continuous alarm ring with gap listening, Fix rounds 1-4 (AI fallback interpret, one schedule, round 4 complaints), Found while building N1-N12, N7 timer rounding test flake, Phase 4 Interrupting him, Phase 5 Alarms that behave like alarms (+3 more)

### Community 37 - "Phase 2 GPU first"
Cohesion: 0.24
Nodes (10): GPU measurements (RTX 5070 and Radeon 880M), GPU watch (sticky fallback fix), Shorter conversation history (4 messages, 2 minutes), Kokoro voice on GPU (2e, onnxruntime-gpu 1.23.2), Phase 2 GPU first, Phase 6 Relevance, tone, memory, sounding human, Smoother voice (6g), small.en and llama3.1:8b choice (2f) (+2 more)

### Community 38 - "boot.lua"
Cohesion: 0.35
Nodes (9): bang(), buildOrder(), color(), finish(), Initialize(), num(), readings(), rel() (+1 more)

### Community 39 - "status_block.lua"
Cohesion: 0.29
Nodes (7): Initialize(), n(), OnClick(), OnRightClick(), readMail(), rows(), Update()

### Community 40 - "Context blocks sent only when the question needs them"
Cohesion: 0.20
Nodes (8): JARVIS Repair Plan (master copy), The 26 reported issues, Checks after every phase (Part E), Phase 9 Ask him what is wrong (diagnosis), Research sources (Part H), JarvisWatch silent pop-up warnings, System snapshot (diag.ps1) and event log findings, Daily briefing

### Community 41 - "Update"
Cohesion: 0.27
Nodes (6): countdown(), Initialize(), load(), OnClick(), Update(), when()

### Community 42 - "Update"
Cohesion: 0.29
Nodes (7): OnClick(), OnRightClick(), rows(), span(), Update(), utcOffset(), week()

### Community 43 - "sphere.lua"
Cohesion: 0.11
Nodes (7): Initialize(), OnClick(), Initialize(), OnClick(), OnISS(), X(), Y()

### Community 44 - "strip.lua"
Cohesion: 0.24
Nodes (5): cells(), Initialize(), OnClick(), short(), Update()

### Community 45 - "JARVIS Assumed Settings and Guide"
Cohesion: 0.28
Nodes (9): Memory relook and JarvisLearn offer, Natural tone and serious-topic override, JARVIS Assumed Settings and Guide, Alarms (RINGS=10, stop words), Personality setting (proper, playful, brief), Remembered facts (50 max, jarvis_memory.txt), Repeating reminders, Snooze (1 minute default, 1 min to 2 h) (+1 more)

### Community 46 - "H.set"
Cohesion: 0.16
Nodes (16): build(), Focus(), OnClick(), OnScroll(), Update(), matrix(), sprite(), capFormat() (+8 more)

### Community 47 - "Update"
Cohesion: 0.33
Nodes (7): build(), OnClick(), OnRightClick(), OnScroll(), readAll(), Update(), wrap()

### Community 48 - "Update"
Cohesion: 0.13
Nodes (11): Initialize(), OnClick(), timeToLimit(), H.hw(), num(), Initialize(), OnClick(), short() (+3 more)

### Community 49 - "H.sval"
Cohesion: 0.17
Nodes (9): OnCore(), OnSPX(), H.sval(), OnRun(), Initialize(), mask(), OnRightClick(), OnWan() (+1 more)

### Community 50 - "Phase 3 Hearing you correctly"
Cohesion: 0.29
Nodes (7): JarvisMic microphone selection, Music ducking while listening, New settings this plan adds (Part F), Phase 0 Measure first (read-only), Phase 3 Hearing you correctly, Voice crash and start-up import race, Wake word (openWakeWord hey_jarvis)

### Community 51 - "Presets (save/load/undo)"
Cohesion: 0.29
Nodes (7): Presets (save/load/undo), Preset slot 2 README, Preset slot 3 README, Preset slot 4 README, Preset slot 5 README, Preset slot 6 README, Preset undo README

### Community 52 - "SIL Open Font License"
Cohesion: 0.29
Nodes (7): OFL licence B612 Mono, OFL licence Michroma, OFL licence Orbitron, OFL licence Oxanium, OFL licence Rajdhani, OFL licence Share Tech Mono, SIL Open Font License

### Community 53 - "Update"
Cohesion: 0.57
Nodes (5): OnClick(), OnRightClick(), OnScroll(), setSource(), Update()

### Community 54 - "ACTIONS fixed entries (only things that can run)"
Cohesion: 0.40
Nodes (4): ACTIONS fixed entries (only things that can run), Airplane mode via Wi-Fi and Bluetooth radios, Bluetooth and connect-to by voice, Phase 7 More settings by voice

### Community 55 - "Phase 1 He tells the truth and commands really run"
Cohesion: 0.33
Nodes (4): AI fallback interpret (checked, never first reader), Answers by code: time, date, sums, conversions, Phase 1 He tells the truth and commands really run, Undo that and what did you hear

### Community 56 - "Follow-up windows (3 s / 10 s with name)"
Cohesion: 0.33
Nodes (6): Autocorrect layer and Whisper settings, Follow-up windows (3 s / 10 s with name), Name normalisation (Travis, droves aliases), Phase 8 Follow-up timing and sounds, Quieter startup sounds and chime volume, Follow-up without the wake word

### Community 57 - "barge"
Cohesion: 0.33
Nodes (3): barge(), run_key(), sleep()

### Community 59 - "wake_loop"
Cohesion: 0.14
Nodes (8): barge_in(), barge_turn(), compact_due(), daily_memory(), hud_tier(), mic_device(), record(), wake_loop()

### Community 60 - "G.check"
Cohesion: 0.60
Nodes (5): G.check(), G.checkAll(), inSafe(), moved(), sep()

### Community 61 - "category.lua"
Cohesion: 0.33
Nodes (11): A.setState(), catIndex(), choose(), current(), drawPager(), drawScan(), OnClick(), OnScroll() (+3 more)

### Community 62 - "ShipCore helper"
Cohesion: 0.40
Nodes (4): Lenovo Legion Toolkit, Mission clock (calendar), ShipCore helper, Systems dial

### Community 70 - "cockpit-trace.svg (VTracer trace of cockpit artwork, 1260x709, dark navy base)"
Cohesion: 0.67
Nodes (3): cockpit-posterized.svg (VTracer trace of cockpit artwork), cockpit-trace.svg (VTracer trace of cockpit artwork, 1260x709, dark navy base), reference-simplified.svg (simplified VTracer trace of cockpit reference)

### Community 81 - "ring_alarm"
Cohesion: 0.24
Nodes (3): _Clock, ring_alarm(), within()

### Community 182 - "sensors"
Cohesion: 0.17
Nodes (8): cpu_times(), hw_value(), sensors(), cpu(), hw(), sound(), 6a in detail, S1. Only send what the question needs (6a, about 40 lines)

## Ambiguous Edges - Review These
- `Settings update snippet (network, captions, data links)` → `UPDATE.txt (update part marker)`  [AMBIGUOUS]
  Skins/Spaceship/UPDATE.txt · relation: conceptually_related_to

## Knowledge Gaps
- **44 isolated node(s):** `HWiNFO sensor integration`, `Lenovo Legion Toolkit CLI (GPU modes)`, `MASTER kill switch`, `Preset slots (1-6, _undo)`, `jarvis.py voice service` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 532 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **120 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Skin` connect `Skin` to `layoutlib.py`, `rmsim.py`, `.bang`?**
  _High betweenness centrality (0.327) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `turn()` (e.g. with `main()` and `prepare_fillers()`) actually correct?**
  _`turn()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `HWiNFO sensor integration`, `Lenovo Legion Toolkit CLI (GPU modes)`, `MASTER kill switch` to the rest of the system?**
  _44 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ShipCore C# Helper` be split into smaller, more focused modules?**
  _Cohesion score 0.053211351755041075 - nodes in this community are weakly interconnected._
- **Why does `ShipCore` connect `ShipCore C# Helper` to `ShipCore.cs`?**
  _High betweenness centrality (0.154) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `build()` (e.g. with `.ellipse()` and `.line()`) actually correct?**
  _`build()` has 5 INFERRED edges - model-reasoned connections that need verification._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Settings update snippet (network, captions, data links)` and `UPDATE.txt (update part marker)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._