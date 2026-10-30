# Implementation Plan: CSpace features round (2026-10-29)

`tasks/plan.md` and `tasks/todo.md` hold the JARVIS Phase 6 plan, and its 13 to-dos are still open, so this plan has its own files: this one and `tasks/cspace-features-todo.md`.

## Overview

The user asked for six things: all the clicks ("clocks"), the slots, the daily app-icon refresh, a check that CARGO is ported, the JARVIS orb animation and voice echo, and `JarvisPython` from Settings.inc. Before planning I read the skin's scripts and the app's code. What I found:

| Ask | What is there now | Work left |
|---|---|---|
| Clicks | **All ported.** Strip (Task Manager /7, drive), alert and power (open the Control Center), graph click, right-click and scroll, drawer, slots, dial and calendar. My last reply listed some of these as missing. I took that from old file-header comments that were never updated after the clicks were added. | Fix the out-of-date comments (Task 5). |
| Mission clock | Ported (`MissionClock.tsx`). It is the only clock in the skin. | None, unless "clocks" means something else (see Open Questions). |
| Slots | All eight skin slots use `Style=row` (`Left/Slot1-4`, `Right/Slot5-8`), and the app has row. The skin's other styles (compact, ship, card, rcompact) are not used by any of its slots. | None by default (see Open Questions). |
| CARGO | **Ported.** `DrawerModule.tsx` has the clicks, launch, folder focus, scroll, idle close, the app pictures (`c.appIcon`) and the tray item. The header comment in `drawer.ts` is out of date. | Comment only (Task 5). |
| JARVIS orb animation | **Ported.** The 210 Idle frames play in `JarvisModule.tsx` `Orb`. | None. |
| Voice echo | Not ported (`S1_2`). The level isn't smoothed either. | Task 2. |
| Daily app-icon refresh | Not ported, for two reasons. (1) The app has no host-side queue writer (`apps.lua A.writeIconQueue`) and never runs `Scripts\app-icons.ps1`. (2) Icons are bundled into `dist` at **build** time (`draw/appIcons.ts`, `import.meta.glob`, about 3.7 MB), so a new icon would not show until a rebuild. | Tasks 3 and 4. |
| JarvisPython | Not read (`Program.cs` shortcut). | Task 1. |

## Architecture Decisions

- **JarvisPython is read by the host only.** It is not added to the page's schema. A value the page could write would let the page choose which program the host launches, so the host reads the line from Settings.inc itself. The path is accepted only when it is fully qualified, on a local drive (no UNC), ends in `pythonw.exe` or `pyw.exe`, and exists. If it is set but fails any of these checks, the result is NO PYTHON, as jarvis.lua does when the setting is set but the file is missing. Empty means the current default places.
- **Voice echo** follows jarvis.lua lines 317-350 exactly:
  - smoothed `lvl` (attack 0.55, release 0.18)
  - `act` toward 0.55+0.45·lvl while speaking, 0.25 while thinking, else 0
  - a second `<image>` drawn only when act·255 ≥ 3, so there is no extra cost when quiet
  - frames: the Active folder if it exists, else Idle half a loop ahead
  - size ORB_D·size·(1.12+0.28·lvl), colour mix(col, white, 0.4), alpha act·150
  - The Active frames are bundled like the Idle ones (+5 MB in dist, the user's own frames, already in git). Only the frame on screen is decoded, as Orb does now.
- **Icons are served at run time, not at build time.** The host maps `@Resources\Icons` to a second WebView2 virtual host. The pattern is the same as the UI's existing `SetVirtualHostNameToFolderMapping`, read-only and DenyCors. The host sends `icons.list`: the ids that have a png, with a version stamp. `appIconUrls` builds URLs from that list, and the build-time glob is removed. This takes about 3.7 MB out of `dist`, and new icons show without a rebuild.
- **The icon queue is built in the host**, from the same catalog feed the page uses. It does not trust a list from the page. Each id must match `^[A-Za-z0-9_.-]{1,64}$` (the script writes `Icons\<id>.png`, so this blocks path traversal). Each path must be either `shell:AppsFolder\<AUMID>` with no control characters, or a fully qualified existing `.exe`/`.lnk`. The host writes `Data\IconQueue.txt` and runs `app-icons.ps1` through `StatusRunner.RunScript`. The run is single and off the UI thread, and the exit code is logged.
- **When the icons refresh** (controller.lua lines 134-137 and 171-176): after each Start-menu scan, plus a rescan every hour while the app runs, as the skin's `tick % 3600`. The app currently scans only at start.

## Dependency graph

```
Task 1 JarvisPython ── independent
Task 2 voice echo ──── independent
Task 3 icons served at run time ──> Task 4 icon queue + app-icons.ps1 + daily/hourly
Task 5 out-of-date comments ── after 1-4 (touches the same headers)
```

## Task List

### Phase 1: JARVIS
- [x] Task 1: Host reads and checks JarvisPython (S)
- [x] Task 2: Voice echo and level smoothing on the orb (M)

### Checkpoint A
- [x] dotnet build 0 errors, dotnet test, tsc, vitest, vite build, playwright hud spec all pass
- [x] Preview: `?jarvis=speaking` shows the echo layer, and idle shows no second image
- [x] Efficiency note: frame timer count unchanged, one extra `<image>` only while speaking or thinking

### Phase 2: App icons
- [x] Task 3: Icons served at run time from the host (M)
- [x] Task 4: Icon queue, app-icons.ps1 after each scan, and the hourly rescan (M)

### Checkpoint B
- [x] All checks pass. `dist` is about 3.7 MB smaller.
- [x] app-icons.ps1 was read in full and dry-run grepped (done: no delete, kill, registry or process-start calls). Its first run goes against a **scratch copy** of `@Resources`, never the repo's Icons folder, until the output is checked.
- [x] Preview with no host: line icons as before (no broken images)

### Phase 3: Clean-up
- [x] Task 5: Fix the out-of-date "not ported" comments, and log the round in `tasks/cspace-pm-log.md` (XS)

### Checkpoint: Complete
- [x] Every acceptance criterion met; one commit per task, explicit paths; not pushed
- [x] Live checks listed as unverified (CSpace stays closed unless the user starts it)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| A path from settings or the catalog launches or reads the wrong file | High | Host-side checks on file name, fully qualified local path and existence. The page can't write JarvisPython, and ids are limited to a safe pattern. |
| app-icons.ps1 overwrites the user's existing icons badly | Med | Its first run is on a scratch copy and the output is compared; the repo's Icons folder is gitignored, so it can't be committed by mistake |
| A second orb image costs GPU while JARVIS speaks | Low | Drawn only when act ≥ 3/255; on the same frame tick; measured in the preview |
| The virtual host for Icons leaks other files | Med | Mapped to the Icons folder only, read-only, DenyCors, same as the UI mapping |
| The hourly rescan adds CPU | Low | One Get-StartApps run an hour (as the skin does), single-run guard |

## Open Questions (defaults are used if no answer)

1. "Add the clocks": the only clock in the skin, the mission clock, is in the app. If you meant something else (a time-of-day clock, a stopwatch), say which. **Default:** it meant "clicks", which are all in.
2. "The slots": all eight are in, in the style the skin uses. Porting the four styles no skin slot uses would add code nobody can see. **Default:** skip them.
