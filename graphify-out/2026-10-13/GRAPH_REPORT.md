# Graph Report - RainmeterSpaceship  (2026-10-13)

## Corpus Check
- 26 files · ~810,424 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1195 nodes · 2448 edges · 153 communities (54 shown, 99 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 317 edges (avg confidence: 0.85)
- Token cost: 67,885 input · 7,365 output

## Community Hubs (Navigation)
- ShipCore Native Helper
- Ship Frame Art Builder
- ShipCore Audio Endpoints
- Frame Render Tools
- App Launcher Slots
- Control Center Rows
- Lua Drawing Library
- Jarvis Tests
- HUD Helper Init and Alerts
- Jarvis Prompt and HUD Context
- Skin Simulator Core
- HUD Text and Hit Areas
- Rainmeter Simulator Render
- Jarvis Daemon Main and Alarm
- Jarvis Hologram Skin
- Layout Checks
- Systems Dial
- Packaging and Audits
- Jarvis Chat and Context Fit
- Performance Tier Controller
- Jarvis Speech Output
- Jarvis Turn and Routing
- Jarvis Settings and Voice Synthesis
- Console Skin
- Category Panel
- Reminders and Timers
- Jarvis Docs and Guardrails
- Target Reticle and To-dos
- Ollama Model Handling
- Volume and Mute Actions
- Audio Visualizer Skin
- Location Skin
- HUD Guide and Settings
- Boot Sequence
- HUD Ladder
- Panels Skin
- Setup Guide and Tiers
- Reminder Time Parsing
- Sphere Skin
- README Overview
- Jarvis Conversation Log
- Status Block
- Strip Skin
- System Info Skin
- Storage Skin
- Layout Build Tool
- Preset Slots
- Font Licences
- Graph Skin
- Status Callbacks
- Position Guard
- INI and Lua Parsing
- Guide Hardware Concepts
- Microphone Listening
- Data Sources
- Streaming Reply Chunks
- Jarvis skills (actions, readings, timers

## God Nodes (most connected - your core abstractions)
1. `ShipCore` - 79 edges
2. `turn()` - 40 edges
3. `build()` - 38 edges
4. `log()` - 27 edges
5. `fmt()` - 25 edges
6. `H.text()` - 25 edges
7. `H.init()` - 24 edges
8. `setting()` - 24 edges
9. `H.hit()` - 22 edges
10. `H.canvas()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Safe development and audit rules` --semantically_similar_to--> `Jarvis action guardrails (confirm destructive, allowlist)`  [INFERRED] [semantically similar]
  CLAUDE.md → Skins/Spaceship/@Resources/Docs/Spaceship-HUD-Guide.md
- `OnWan()` --calls--> `H.sval()`  [INFERRED]
  Skins/Spaceship/@Resources/Scripts/sysinfo.lua → Skins/Spaceship/@Resources/Scripts/lib.lua
- `Initialize()` --calls--> `H.init()`  [INFERRED]
  Skins/Spaceship/@Resources/Scripts/sphere.lua → Skins/Spaceship/@Resources/Scripts/lib.lua
- `Initialize()` --calls--> `H.init()`  [INFERRED]
  Skins/Spaceship/@Resources/Scripts/hud.lua → Skins/Spaceship/@Resources/Scripts/lib.lua
- `Initialize()` --calls--> `H.init()`  [INFERRED]
  Skins/Spaceship/@Resources/Scripts/jarvislog.lua → Skins/Spaceship/@Resources/Scripts/lib.lua

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Layout to frame build pipeline** — tools_ref_layout, layout_layout, tools_build, tools_ship_frame, tools_frame_render, tools_package [EXTRACTED 1.00]
- **Performance tier system** — concept_perf_tiers, concept_controller, concept_dgpu_hygiene [INFERRED 0.85]
- **Jarvis voice pipeline** — skins_spaceship__resources_docs_spaceship_hud_guide_wakeword, skins_spaceship__resources_docs_spaceship_hud_guide_whisper, skins_spaceship__resources_docs_spaceship_hud_guide_ollama, skins_spaceship__resources_docs_spaceship_hud_guide_jarvisskills [EXTRACTED 0.95]
- **HUD modules fed by ShipCore data files** — skins_spaceship__resources_docs_spaceship_hud_guide_shipcore, skins_spaceship__resources_docs_spaceship_hud_guide_missionclock, skins_spaceship__resources_docs_spaceship_hud_guide_systemsdial, skins_spaceship__resources_docs_spaceship_hud_guide_secretsstorage [INFERRED 0.85]

## Communities (153 total, 99 thin omitted)

### Community 0 - "ShipCore Native Helper"
Cohesion: 0.05
Nodes (8): CalendarForm, CalEvent, CalSource, COPYDATASTRUCT, GmailForm, Prop, ShipCore, Vevent

### Community 1 - "Ship Frame Art Builder"
Cohesion: 0.06
Nodes (34): at(), build(), beam(), H_ellipse(), hose(), lamp(), P(), ring() (+26 more)

### Community 2 - "ShipCore Audio Endpoints"
Cohesion: 0.06
Nodes (5): IAudioEndpointVolume, IMMDevice, IMMDeviceEnumerator, MicVolume, MMDeviceEnumeratorCom

### Community 3 - "Frame Render Tools"
Cohesion: 0.09
Nodes (25): blur(), _box(), _busy(), corners_png(), glass_fx_png(), highlights(), hull_png(), mist_png() (+17 more)

### Community 4 - "App Launcher Slots"
Cohesion: 0.09
Nodes (38): A.entry(), A.getState(), A.launch(), A.load(), A.loadAll(), A.loadStart(), A.notFound(), A.parseIni() (+30 more)

### Community 5 - "Control Center Rows"
Cohesion: 0.12
Nodes (40): applyTheme(), arm(), bump(), colorRow(), copyFile(), core(), cycle(), cycleSlot() (+32 more)

### Community 6 - "Lua Drawing Library"
Cohesion: 0.17
Nodes (35): Canvas:arc(), Canvas:brackets(), Canvas:chamfer(), Canvas:circle(), Canvas:dashArc(), Canvas:dot(), Canvas:fillCircle(), Canvas:fillPoly() (+27 more)

### Community 7 - "Jarvis Tests"
Cohesion: 0.06
Nodes (11): ahead(), cmd(), _Col, _Done, FakeWhisper, hm(), _Resp, _run() (+3 more)

### Community 8 - "HUD Helper Init and Alerts"
Cohesion: 0.07
Nodes (22): alerts(), Initialize(), OnClick(), Initialize(), OnClick(), timeToLimit(), Initialize(), Initialize() (+14 more)

### Community 9 - "Jarvis Prompt and HUD Context"
Cohesion: 0.08
Nodes (13): about_me(), act_close(), context(), MEMORYSTATUSEX, open_windows(), press_key(), read_kv(), run_ok() (+5 more)

### Community 10 - "Skin Simulator Core"
Cohesion: 0.10
Nodes (7): main(), discover(), mock_value(), Problems, Skin, parseformula(), rep()

### Community 11 - "HUD Text and Hit Areas"
Cohesion: 0.20
Nodes (27): Update(), Update(), draw(), Update(), Update(), H.canvas(), H.ellipsePts(), H.hideHit() (+19 more)

### Community 12 - "Rainmeter Simulator Render"
Cohesion: 0.14
Nodes (19): draw_shape(), draw_text(), eval_formula(), font_for(), inside_grown(), main(), make_mock_icons(), num() (+11 more)

### Community 13 - "Jarvis Daemon Main and Alarm"
Cohesion: 0.13
Nodes (17): alarm(), chroma_index(), _chunks(), ding(), due_reminders(), hud_tier(), index_loop(), log() (+9 more)

### Community 14 - "Jarvis Hologram Skin"
Cohesion: 0.16
Nodes (20): buildPlexus(), colorSetting(), command(), drawScene(), exists(), Forget(), frameFile(), hidden() (+12 more)

### Community 15 - "Layout Checks"
Cohesion: 0.16
Nodes (10): Spaceship HUD Master Plan, layout.json, skin_geometry(), check(), main(), render(), convex_overlap(), in_safe_area() (+2 more)

### Community 16 - "Systems Dial"
Cohesion: 0.16
Nodes (18): apply(), buildControls(), ctl(), frac(), Initialize(), label(), now(), OnClick() (+10 more)

### Community 17 - "Packaging and Audits"
Cohesion: 0.17
Nodes (6): cover(), main(), window_mask(), load(), layout_ini(), main()

### Community 18 - "Jarvis Chat and Context Fit"
Cohesion: 0.10
Nodes (11): chat_stream(), cpu_times(), ctx_tokens(), fit_context(), gpu(), hw_value(), sensors(), card() (+3 more)

### Community 19 - "Performance Tier Controller"
Cohesion: 0.20
Nodes (19): A.writeIconQueue(), checkMonitor(), DetectSensors(), findHome(), fitTo(), Initialize(), Master(), OnHwScan() (+11 more)

### Community 20 - "Jarvis Speech Output"
Cohesion: 0.15
Nodes (12): convo_add(), filler(), filler_done(), go(), live(), play_samples(), reply_line(), say_text_only() (+4 more)

### Community 21 - "Jarvis Turn and Routing"
Cohesion: 0.14
Nodes (11): best_app(), chime(), confirmed(), missing_packages(), route(), search_notes(), start_apps(), turn() (+3 more)

### Community 22 - "Jarvis Settings and Voice Synthesis"
Cohesion: 0.19
Nodes (13): cpu_in_use(), cpu_threads(), _kokoro(), _piper(), prepare_fillers(), resolve_voice(), setting(), synth_audio() (+5 more)

### Community 23 - "Console Skin"
Cohesion: 0.25
Nodes (13): buttons(), cycle(), hybridIndex(), OnClick(), OnLltDone(), OnRightClick(), runLlt(), RX() (+5 more)

### Community 24 - "Category Panel"
Cohesion: 0.25
Nodes (12): catIndex(), choose(), current(), drawPager(), drawScan(), drawSchematic(), drawTabs(), OnClick() (+4 more)

### Community 25 - "Reminders and Timers"
Cohesion: 0.18
Nodes (9): clock(), describe(), load_reminders(), remind_reply(), ring_line(), save_reminders(), pending(), span() (+1 more)

### Community 26 - "Jarvis Docs and Guardrails"
Cohesion: 0.19
Nodes (12): Project instructions (CLAUDE.md), Jarvis voice assistant, Obsidian to-do note, Ollama local model, Smart note search (ChromaDB), Target reticle, Wake word (openWakeWord), Whisper speech recognition (+4 more)

### Community 27 - "Target Reticle and To-dos"
Cohesion: 0.25
Nodes (12): countdown(), inside(), OnClick(), OnRightClick(), OnScroll(), parseTodos(), pickNext(), refreshTodos() (+4 more)

### Community 28 - "Ollama Model Handling"
Cohesion: 0.18
Nodes (9): ensure_ollama(), http_json(), installed_models(), keep_alive(), ollama_on_cpu(), pick_model(), preload_ollama(), warm() (+1 more)

### Community 29 - "Volume and Mute Actions"
Cohesion: 0.17
Nodes (7): act_volume(), _com(), done_line(), muted(), sound(), speakers(), speakers_mute()

### Community 30 - "Audio Visualizer Skin"
Cohesion: 0.24
Nodes (6): glyph(), media(), OnClick(), P(), placeHits(), Update()

### Community 31 - "Location Skin"
Cohesion: 0.23
Nodes (8): set(), value(), H.clamp(), countdown(), load(), OnClick(), Update(), when()

### Community 32 - "HUD Guide and Settings"
Cohesion: 0.24
Nodes (9): Spaceship HUD Complete Guide, Apps.ini app catalog, Control Center, HWiNFO sensor data, Startup boot sequence, Update installer (Apply-SpaceshipUpdate), Sounds guide, Settings update snippet (network, captions, data links) (+1 more)

### Community 33 - "Boot Sequence"
Cohesion: 0.35
Nodes (9): bang(), buildOrder(), color(), finish(), Initialize(), num(), readings(), rel() (+1 more)

### Community 34 - "HUD Ladder"
Cohesion: 0.29
Nodes (7): ease(), Initialize(), ladder(), OnClick(), Update(), X(), Y()

### Community 35 - "Panels Skin"
Cohesion: 0.24
Nodes (8): H.llt(), Initialize(), OnClick(), OnRightClick(), span(), Update(), utcOffset(), week()

### Community 36 - "Setup Guide and Tiers"
Cohesion: 0.20
Nodes (7): Controller skin (tiers, app scan, helper), HWiNFO sensor integration, Lenovo Legion Toolkit CLI (GPU modes), MASTER kill switch, DPAPI-encrypted secrets storage, ShipCore helper (compiled C#), Spaceship HUD Setup Guide

### Community 37 - "Reminder Time Parsing"
Cohesion: 0.22
Nodes (5): duration(), _num(), reminder_cmd(), split_time(), when()

### Community 38 - "Sphere Skin"
Cohesion: 0.20
Nodes (4): Initialize(), OnClick(), X(), Y()

### Community 39 - "README Overview"
Cohesion: 0.25
Nodes (9): App launcher slots and category panels, Cockpit Frame (hull, glass, accents), Control Center (Aurum-style settings), Home monitor / AutoFit handling, Layout guard (overlap checker), Presets with undo, Spaceship HUD README, Apps.ini app catalog (+1 more)

### Community 40 - "Jarvis Conversation Log"
Cohesion: 0.25
Nodes (6): build(), Initialize(), OnClick(), OnRightClick(), OnScroll(), readAll()

### Community 41 - "Status Block"
Cohesion: 0.25
Nodes (6): Initialize(), n(), OnClick(), OnRightClick(), readMail(), rows()

### Community 42 - "Strip Skin"
Cohesion: 0.25
Nodes (4): Initialize(), OnClick(), short(), Update()

### Community 43 - "System Info Skin"
Cohesion: 0.22
Nodes (6): Initialize(), mask(), OnClick(), OnRightClick(), OnWan(), readSpeed()

### Community 44 - "Storage Skin"
Cohesion: 0.36
Nodes (5): OnClick(), short(), Update(), X(), Y()

### Community 45 - "Layout Build Tool"
Cohesion: 0.54
Nodes (6): fnum(), geometry_inc(), key_of(), main(), meters_inc(), zones_lua()

### Community 46 - "Preset Slots"
Cohesion: 0.29
Nodes (7): Presets (save/load/undo), Preset slot 2 README, Preset slot 3 README, Preset slot 4 README, Preset slot 5 README, Preset slot 6 README, Preset undo README

### Community 47 - "Font Licences"
Cohesion: 0.29
Nodes (7): OFL licence B612 Mono, OFL licence Michroma, OFL licence Orbitron, OFL licence Oxanium, OFL licence Rajdhani, OFL licence Share Tech Mono, SIL Open Font License

### Community 48 - "Graph Skin"
Cohesion: 0.57
Nodes (5): OnClick(), OnRightClick(), OnScroll(), setSource(), Update()

### Community 49 - "Status Callbacks"
Cohesion: 0.33
Nodes (6): OnStatus(), OnCore(), OnSPX(), H.sval(), OnISS(), OnRun()

### Community 50 - "Position Guard"
Cohesion: 0.60
Nodes (5): G.check(), G.checkAll(), inSafe(), moved(), sep()

### Community 51 - "INI and Lua Parsing"
Cohesion: 0.33
Nodes (3): lua_syntax_check(), parse_ini(), read_text()

### Community 52 - "Guide Hardware Concepts"
Cohesion: 0.40
Nodes (4): Lenovo Legion Toolkit, Mission clock (calendar), ShipCore helper, Systems dial

### Community 53 - "Microphone Listening"
Cohesion: 0.40
Nodes (3): hear(), listen(), _listen()

## Ambiguous Edges - Review These
- `Settings update snippet (network, captions, data links)` → `UPDATE.txt (update part marker)`  [AMBIGUOUS]
  Skins/Spaceship/UPDATE.txt · relation: conceptually_related_to

## Knowledge Gaps
- **27 isolated node(s):** `HWiNFO sensor integration`, `Lenovo Legion Toolkit CLI (GPU modes)`, `Preset slots (1-6, _undo)`, `UPDATE.txt (update part marker)`, `Jarvis hologram frames guide` (+22 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 388 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **99 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Skin` connect `Skin Simulator Core` to `INI and Lua Parsing`, `Rainmeter Simulator Render`, `Console Skin`?**
  _High betweenness centrality (0.334) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `turn()` (e.g. with `main()` and `prepare_fillers()`) actually correct?**
  _`turn()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `HWiNFO sensor integration`, `Lenovo Legion Toolkit CLI (GPU modes)`, `Preset slots (1-6, _undo)` to the rest of the system?**
  _27 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ShipCore Native Helper` be split into smaller, more focused modules?**
  _Cohesion score 0.053211351755041075 - nodes in this community are weakly interconnected._
- **Why does `ShipCore` connect `ShipCore Native Helper` to `ShipCore Audio Endpoints`?**
  _High betweenness centrality (0.160) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `build()` (e.g. with `.ellipse()` and `.line()`) actually correct?**
  _`build()` has 5 INFERRED edges - model-reasoned connections that need verification._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Settings update snippet (network, captions, data links)` and `UPDATE.txt (update part marker)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._