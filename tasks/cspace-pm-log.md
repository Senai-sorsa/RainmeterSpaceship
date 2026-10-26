# CSpace PM log (autonomous run started 2026-10-25)

Standing order: memory `autonomous-pm-directive.md` (verbatim). Loop per slice: plan -> code -> unit/static checks
(no live runs of the app until everything is built) -> compare with similar apps (Wallpaper Engine, Lively,
Rainmeter, Seelen UI, Windhawk, BeWidgets...) -> queue improvements -> next slice. Ask the user only before
actions that could damage the PC. No push (public repo).

Sources read: docs/HANDOFF-2026-10-21-cspace.md (plan Steps 0-6), claude_spaceship_migration_phases.md (spec;
gap list in tasks/cspace-gap-analysis.md), JARVIS-Repair-Plan.txt (CURRENT STATE + PHASE 10B).

## Done this run
- Step 0: old app closed; `dotnet build ShipCore.App` exit 0, CSpace.exe exists (1 MSB3277 WindowsBase warning from WebView2.Wpf, harmless).
- d647f8e scheduler carries remainder (rates right on 60/144/165 Hz) + test.
- 96b2ff3 ?module= list/all, test icons hidden when modules on, Center skips sphere when Jarvis on, Center reticle stale-readings fix.
- Host opens index.html?module=all (decision: full HUD by default; user delegated the call).
- d5ab992 docs name the real kill chord; f83655e desktop layer by z-order (S2-S4).
- 6066979 S1 click-through outside the page's hit regions (hit.regions message, WS_EX_LAYERED + TRANSPARENT toggle).
- 8489368 tray never writes autostart; WM_DISPLAYCHANGE re-homes; hang restarts the page; idempotent teardown.
- 3cc9543 S7 foreground WinEvent hides at once for fullscreen apps / exam browsers.
- 643fa37 S5 JARVIS state into the core: host reads Data\jarvis.txt read-only (share delete), posts jarvis.update.

## Queue (app)
1. Docs: Ctrl+Alt+1 -> Ctrl+Alt+Shift+1 in docs/HANDOFF-2026-10-20-standalone-app.md; ShipCore.App(.exe) -> CSpace in docs/tools.
2. Gap-analysis slices (tasks/cspace-gap-analysis.md).
3. Handoff Step 3 host robustness (hit regions, TaskbarCreated, WM_DISPLAYCHANGE, WM_QUERYENDSESSION, graceful quit).
4. Step 4 packaging (publish, installer decision). Autostart stays unbuilt (user's word).
5. Live go needed later for: first run, baseline (Step 2), dial on hardware.

## Queue (JARVIS track, fakes-only fixes from PHASE 10B)
W1 bare "Jarvis" wakes, T1 silent never-mind, T3 listen 1 s after stop, U2 count after tidy, U4 voices path, X1 persona path log line.
Need the user: W2 (training off-PC), T4 (measure live), G1 (measure), U5 wording (Phase 10 hand review).

## Decisions made (PM)
- Full HUD by default in the host (handoff 1c).
- Desktop layer = Rainmeter's "On Desktop" model (top-level, HWND_BOTTOM, held there on WM_WINDOWPOSCHANGING), not a
  WorkerW child. Why: a WorkerW child sits under the icon view (no clicks), and 24H2+ (this PC is 26300) changed the tree
  (0x052C needs 0xD/1, WorkerW is a Progman child). Sources: rainmeter/Library/System.cpp + Skin.cpp (ChangeZPos),
  kirie PR #11, VibingWrapper PR #7. Follow-up queued: Show Desktop (Win+D) lift like Rainmeter's CheckDesktopState.
- Win+D (Show Desktop) lift: deferred to after the live run (lifting on desktop focus would also cover apps; Explorer's
  behaviour can't be checked without a live run).
- TaskbarCreated: no code - WinForms NotifyIcon re-adds itself.
- S5 reads the file JARVIS already writes instead of the pipe: no JARVIS change, no live risk. POP/HUD lines are not acted
  on (they change settings / stealth). Pipe line-JSON postponed.
- Known S1 limits: layered + NOREDIRECTIONBITMAP render unverified (fallback: drop WS_EX_LAYERED); drag leaving a region
  loses moves; cursor shape not forwarded; DPI SystemAware.
- Dial stays live (volume/brightness direct, power/refresh confirm) - same as the skin; announce before first live run.
