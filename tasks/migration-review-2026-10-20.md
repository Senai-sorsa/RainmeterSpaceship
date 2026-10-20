# Review of claude_spaceship_migration_phases.md (Gemini plan) - 2026-10-20

Status: REVIEW ONLY. Nothing from the plan has been applied. Sources: Sonnet repo fact-check, Opus design review, both read-only. Nothing was compiled or run (sandbox is Linux: no .NET, no Windows, no WebView2).

## A. Repo facts the plan gets wrong
- Repo/branch name: real one is RainmeterSpaceship on main, not "RainmeterSpaceship-fix-phase7-9-audit".
- Module counts (22 / 25) match nothing: 35 skin .ini, 33 `_DX` keys in Offsets.inc, 35 zones in layout/layout.json.
- `jarvis.lua` "R=203..237" is not a constant (values at jarvis.lua:19, 234, 382).
- `tools/export_ui_assets.py` does not exist yet; the plan assumes it.
- Almost every line number is off. Re-grep before using one. Real: base.py:197 rainmeter_running; jarvis.py:1502-1505 the 30 s exit; audio.lua:19; dial.lua:16; lib.lua:507 H.caption; Settings.inc:205.
- Confirmed right: BUG-01..06, 09, 10 (DPAPI entropy "SpaceshipHUD" must be UTF-8 bytes; ShipCore.cs:164,173).
- Unchecked: BUG-07/08, Part 3.1 numbers, Part 5.1 vs the Lua sources.

## B. Design errors (must be fixed in the plan before any C# is written)
Critical
1. Transparent window never specified. Windowed WebView2 + DefaultBackgroundColor=Transparent does not show the desktop; a layered parent cannot host the GPU child. Needs WS_EX_NOREDIRECTIONBITMAP + CoreWebView2CompositionController (DirectComposition). PROTOTYPE FIRST; every phase depends on it.
2. Named pipes: default DACL, no first-instance flag, snapshot sent before auth, SID in name is not security, Local\ mutex vs global pipe names. Use CurrentUserOnly/PipeSecurity, FIRST_PIPE_INSTANCE, send nothing until hello verified, PID check, session id in names.
3. WebMessage -> OS actions with no origin check (sys.powerAction, shell.open); pipe config.set lets model output write any Settings.inc key (violates CLAUDE.md s5). Allowlist keys, origin-lock, user confirmation for power actions.
4. Every start deactivates Rainmeter skins and force-kills ShipCore; rollback never re-activates. Only on explicit Switch-HudHost, graceful close, record and restore active configs.
5. Startup task installed automatically, exit code unchecked. Ask first, check exit code, fall back to HKCU Run.
High
6. Occlusion gate 5 precedence bug (Progman/WorkerW flagged as fullscreen); 7. z-order inverted; 8. Win+D guard defeats emergency hide; 9. WM_QUERYENDSESSION must just return TRUE, tear down on WM_ENDSESSION(TRUE); 10. ProcessFailed checks wrong enum, no try/catch; 11. SharedBuffer: ReadOnly + JS write = renderer crash, torn reads, float32 frame counter stops at 2^24, modal never gets Bounds; 12. region leak on SetWindowRgn failure, leases never expire, HTTRANSPARENT claim half-wrong; 13. icon extractor flag 0x8 = THUMBNAILONLY (ICONONLY=0x4), FromHbitmap drops alpha; 14. ReadyToRun is not AOT, IncludeNativeLibrariesForSelfExtract extracts to %TEMP%.
Medium: impossible numbers (<25 ms Stage 0, <15 ms wake vs 35/50 ms debounce, 165 Hz P99, <22 MB VRAM is really ~43 MB, <500 ms recovery); intro barrier never resolves at 60 Hz; FFT per packet in double, INFINITE wait freezes on silence; three different generated-JSON paths; SpaceshipHudHostClass never registered; blocking pipe write in JARVIS main path; unverified `--gpu-preference` flag; WDA return value unchecked, "screen-share detected" not reliable.

## C. What can be verified here vs. only on Windows
Verifiable on Linux: tools/export_ui_assets.py, tools/build_orb_atlas.py (Python + Pillow), Preact/TS UI with mocked chrome.webview, vitest, headless-Chromium screenshots vs RefrenceImage.png.
Windows only: all C#, transparency, regions, hit-testing, DwmFlush, schtasks, shutdown, pipes C#<->Python, WASAPI, test_jarvis.py with real ctypes, the Rainmeter switch, every performance number.

## D. Proposed first slice (needs approval)
1. Commit/checkpoint Phase 10B first (WIP patch saved in the job tmp dir; nothing committed).
2. export_ui_assets.py + build_orb_atlas.py into a scratch dir.
3. Preact/TS UI in a new SpaceshipApp/SpaceshipUI with a mock host, static HUD vs RefrenceImage.png. Needs npm + Playwright installs.
4. C# host written only after a Windows prototype of finding B1 passes.
Rainmeter skin stays untouched and remains the default throughout.
