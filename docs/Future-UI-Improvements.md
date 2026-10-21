# Future UI improvements (full detail)

Written 2026-10-20 for a later session. Read `docs/UI-IMPROVEMENTS.md` for the short version and the phase order; this file has the detail needed to start building. Nothing here is built. Every item still needs its own goal / scope / non-goals / acceptance / rollback (CLAUDE.md section 3) and your word before it starts.

## 0. Your original notes (kept word for word)

> Improving scrollability and control center view
> Why does GPU usage spike whenever I actively
> Make the various noises easier to control and adjust
> Making the music/noise ball more like a accurate visual
> The current calendar outlook cuts of important info - text should be smaller, remove the timer, and Give more room for the text. Once there is less than 24hrs till a task it shouldnt say "TMRW" but rather give a time which the task is at ( something like 10:24AM )
> There are many different popups that occur when you hover over a button. Remove a lot of them - such as the ones for the app groups (not individual apps), and various random HUD information (only when it shows the same information again, not when it tells what the information is about). Then from the remaining tags remove what is unnecessary or shows redundant or useless information (things like click to open or click to scroll should be removed) and only keep what shows useful information (like JARVIS inactive). This is mainly just to remove unnecessary information and make the HUD cleaner.
> We will do a complete control center overhaul together - already done
> We need to redo the frame - note for later
> We need to use a video to animate a opening into the intended frame from the lock screen - note for later

Note: the second line stops after "actively". Ask which action.

## 1. Where the work goes

Standing ruling: new UI work goes in the standalone UI (`SpaceshipApp/SpaceshipUI`), not the Rainmeter skin. These items are about Rainmeter modules that are not ported yet (migration phase P-F). **Open decision** (asked, not answered): make the small Phase 1 fixes in the skin now and port them later, or wait for P-F. The skin files that matter are listed per item below. Only the Control Center items (1.1, 1.3 settings part, 2.9 to 2.13) can be built and fully tested in the standalone UI today.

## 2. Phase 1: your requests

### 1.1 Scrolling and the Control Center view
- **Today:** the Control Center is `src/ui/ControlCenter.tsx` with `CategoryRail`, `GroupSection`, `SettingRow` and `SettingsPanel`; styles in `ui.css`. Level (Normal/Advanced), search and undo exist.
- **Changes:**
  1. Visible scroll bar plus top/bottom edge fades when more content is hidden.
  2. Remember the scroll position per category (kept in memory for the session; `localStorage` only as a convenience, always inside try/catch, because it can be blocked).
  3. Mouse wheel, PgUp/PgDn/Home/End, and Space work when the panel has focus.
  4. The category rail and the search box stay pinned; only the settings list scrolls.
  5. Tighter row height so more rows fit at 1280x800 (the size every screenshot test uses).
  6. Known leftovers from earlier reviews to fix at the same time: the reset-group strip wraps to two lines at 1280 px; the search view is sparse; sliders and selects do not take row-navigation arrows.
- **Acceptance:** every setting reachable without losing your place; Playwright tests for scroll memory, keyboard scrolling and the pinned rail; screenshots still fit 1280x800 with no page-level scroll.
- **Risks:** nested scroll areas fighting each other (wheel events). Test by hand with the wheel over a slider.

### 1.2 GPU spike "whenever I actively ..."
- **Blocked on:** the rest of your sentence (what action) and a Windows measurement.
- **Method:** (1) reproduce the action; (2) record GPU and CPU before, during and after with Task Manager and `tools/gpu_baseline.ps1`; (3) turn off one module at a time (or use the PERF tier switch) to find which meter redraws; (4) smallest fix the numbers support (for example: pause or slow that meter while the action runs, or lower its redraw rate); (5) measure again.
- **Existing mechanism:** the PERF tiers (FULL under 50% GPU, LITE at 50% and above, about 10 fps, then LOW and STEALTH), checked every second with hysteresis, in the Controller. The spike may be a reaction to the action that the tier logic is too slow to catch.
- **Acceptance:** two numbers, before and after, from the same test. No estimate.

### 1.3 Make the noises easier to control and adjust
- **Today:** sound settings are spread across the Control Center (assistant voice, volume, alerts) and the audio dial (scroll for volume, click to mute). I have not listed every sound the HUD makes: **first step is an inventory** (grep `Sounds/`, `PlaySound` and the alarm/alert code) written as a table: sound, what triggers it, where its volume comes from.
- **Changes:** one "Sound" group in the Control Center with a master volume; separate sliders for the JARVIS voice, alerts and UI clicks; a mute toggle for each; a "play sample" button beside every slider (an action row, sent as an `action` message; the host plays the sample). A mute toggle on the HUD itself.
- **Contract impact:** new setting keys must be added to `registry.ts`, then `UPDATE_CONTRACT=1 npx vitest run` regenerates `contract/config-keys.json`; the C# and Python tests then check the same list. New actions need adding to the host's action allowlist.
- **Acceptance:** each sound type can be changed and tested without leaving the page.
- **Needs from you:** whether you want your own sound files (Phase 3, item 3.3).

### 1.4 Make the music/noise ball a more accurate visual
- **Today (read in `Scripts/audio.lua`):** it already uses 96 analyser bands (`mBand0..mBand95`), a smoothed band array, RMS, a peak meter (red top ticks), a "pulse ring" of 96 spokes that breathes with loudness, and a core that pulses and mutes on click. So the data is not the weak point; **first find out what looks inaccurate to you** (examples to ask: it moves with no sound? it ignores bass? it is too jumpy? it does not match the music's rhythm?).
- **Candidate changes, after that answer:** map bands on a log frequency scale so bass and treble get fair space; separate attack (fast) and release (slow) smoothing per band; peak-hold dots; scale by decibels, not raw level; a calm resting state at silence (no random motion); match the redraw rate to the PERF tier.
- **Verification:** needs sound. Test with a pure tone (for example 100 Hz, 1 kHz, 8 kHz) and with silence, and check which spokes move. Windows only.

### 1.5 Calendar: fix the cut-off text
- **Today (read in `Scripts/location.lua`):** the left panel has a ring that shows a countdown to the next event (`countdown()`, labels "T-MINUS" / "ENDS IN", lines 74 to 90) and three rows of `when(e, now)` plus the title. Rows use size 6.4 text; the title is uppercased and clipped to the width between `X(158)` and `X(228)`, which is only about 70 layout units. `when()` returns `TODAY` / `TMRW` only for all-day events; timed events today show `HH:MM` only when the day is today, else the weekday or `MM/DD`.
- **Interpretation to confirm:** "remove the timer" = remove the countdown ring (the T-MINUS / ENDS IN number and its label). If you meant something else, say so.
- **Changes:**
  1. Remove the countdown ring and use its space for the rows.
  2. Smaller text (about 5.2 to 5.6) and widen the title area by moving the date column left and shrinking it.
  3. Let a long title wrap onto two lines before it is cut; add a full-text hint only if it is still cut (this is a useful hint, so it stays under the hint rules in 1.6).
  4. New `when()` rule: an event less than 24 hours away shows its clock time as `10:24AM` (12-hour with AM/PM, or follow the system setting; ask which). All-day events inside 24 hours show `ALL DAY` or `TODAY`, never `TMRW`. Beyond 24 hours keep the weekday, then `MM/DD`.
  5. Take care with time zones and daylight saving: compute "less than 24 hours" from timestamps, not from calendar days (the current code compares days).
- **Acceptance:** no title cut at the default size on a test calendar with long titles; a test event 5 hours away shows its time; one at 23h59m shows its time; one at 24h01m shows the weekday.
- **Tests:** the Lua can be exercised with `lupa` through the existing simulator tools (`tools/run_rmsim_safe.py`). Never run `tools/rmsim.py` directly.

### 1.6 Clean up the hover hints
- **Today:** the hints are "HUD captions" drawn by `Scripts/lib.lua` (about line 492 to 628); the text comes from about 29 `tip =` sites: `console.lua` 13, `jarvis.lua` 4, `location.lua` 3, `slot.lua` 3, `target.lua` 2, `lib.lua` 2, `audio.lua` 1, `dial.lua` 1. `CaptionStyle=0` in `Settings.inc` switches back to Windows tooltips.
- **Rules (remove a hint when):** it is on an app group (not an individual app); it only repeats information already on screen; it only says how to use the thing ("click to open", "click to scroll", "drag to move"); or it describes something obvious from its icon. **Keep** a hint only if it shows information you cannot see (for example "JARVIS inactive", why something is greyed out, what a colour means, the full text of a cut title).
- **Method:** (1) I print a table of all ~29 hint sites: file, line, current text, keep or remove, reason. (2) You strike out the ones you disagree with. (3) I change them: either delete the `tip` value or shorten it. (4) Update the Quick Guide text that describes hints.
- **Acceptance:** the count drops, every remaining hint passes the rule, and nothing else on the HUD changed.

## 3. Phase 2: additional suggestions (detail)

Source of the ideas: how CAD tools (SolidWorks/Fusion), aircraft glass cockpits, game and monitoring overlays, and dashboards (Grafana, Task Manager) handle the same problems. This is my general knowledge, not a lookup.

| # | Change | Detail | Where | Size |
|---|---|---|---|---|
| 2.1 | Declutter levels | FULL → ESSENTIAL (alerts, clock, calendar, JARVIS state) → QUIET. One hotkey or tray item cycles them; the choice is saved. Each module declares its minimum level | Core: a `declutter` setting; host: tray item; modules: a level tag in `layout.json` | M |
| 2.2 | Hint delay and learn mode | Hint appears after about 600 ms; each hint is shown at most N times (default 3) then stays quiet; counters stored in State | `lib.lua` caption code | S |
| 2.3 | One status line | JARVIS state, mic, mute, mode in a fixed place | Top or bottom strip | S |
| 2.4 | Alert levels | Three levels (advisory, caution, warning). Only caution/warning get colour change or motion; normal stays calm | Theme + each alert source | M |
| 2.5 | Fixed-width numerals and number formats | No jumping digits; one unit per reading | `fontNum` already exists; add a rule per module | S |
| 2.6 | Relative calendar times | "in 2h 10m", overdue in a warning colour, a "now" line in the day view | `location.lua` after 1.5 | S |
| 2.7 | Contrast check and a high-contrast option | Warn when the accent colour is hard to read on the glass; one switch for a high-contrast palette | Control Center colour rows + `theme.ts` | S |
| 2.8 | Reduced-motion toggle | Turns off decorative animation; also saves GPU | One setting read by all animated modules | S |
| 2.9 | "Changed from default" filter and compare view | `store.isChanged` already exists; add a filter chip and a two-column current/default view | `ControlCenter.tsx` | S |
| 2.10 | Jump list per category | Clickable group names at the top | `CategoryRail`/`GroupSection` | S |
| 2.11 | Test buttons | Next to voice, wake word and alert settings | Action rows (see 1.3) | S |
| 2.12 | Pending marker per row | A small marker while a write is unacknowledged; the store already tracks in-flight writes | `SettingRow.tsx` | S |
| 2.13 | Keyboard-only use | Visible focus ring, `/` focuses search, `Esc` clears it | `ui.css`, `ControlCenter.tsx` | S |
| 2.14 | Snap-to-grid and guides in edit mode | Modules snap to a grid; alignment lines | Edit mode (needs the ported layout) | M |
| 2.15 | "HUD cost" readout | Own CPU/GPU share and frame time over the last 60 s, shown in PERF | Host sampler + PERF page | M |
| 2.16 | Quiet hours / focus schedule | Hide or mute at set times and while a process from `contract/exam-browsers.json` runs (the suspend policy already exists and is tested) | Host + a settings group | M |
| 2.17 | Undo toast | A visible "Undo" for 5 seconds after any change including resets (the store has undo) | `ControlCenter.tsx` | S |

Size: S = under a day of focused work, M = a few days, including tests. These are estimates, not measurements.

## 4. Phase 3: things only you can supply

| # | What | Spec |
|---|---|---|
| 3.1 | Lock-screen-to-frame video | MP4 (H.264) or WebM; no audio; 3 to 8 seconds; your monitor's resolution; first frame = your real lock screen; last frame = the finished frame exactly; say whether it plays at every sign-in or only the first. WebView2 can play it. It costs GPU while it plays, so measure it against the "not more than Rainmeter" rule before keeping it. A fallback for slow starts (skip button or an automatic cut after N seconds) is needed |
| 3.2 | Frame redo | Layered PNGs with alpha (hull, glass, corners, glow) or a reference image and your notes on what to change. `Pasted image.png` has not been read; it is a secondary reference for ideas for redrawing small parts. Read it only when you say so. Frame modes (rendered, picture, none) must keep working |
| 3.3 | Sounds | Optional: short WAV files per event (alert, click, wake, error) |
| 3.4 | The GPU sentence | What you do when it spikes, plus a screen recording or description |
| 3.5 | Windows measurements | Prototype run, Rainmeter baseline, baseline with each change |
| 3.6 | Hint table decisions | Strike out hints you want to keep (from 1.6) |
| 3.7 | Lockdown-browser process names | From Task Manager > Details while it runs; the repo list is unverified |

## 5. Checks every UI item must pass before it counts as done

1. `git status --porcelain -- Skins` is empty unless the item is a deliberate skin edit you approved.
2. From `SpaceshipApp/SpaceshipUI`: `npx tsc --noEmit`, `npm test`, `npm run test:e2e` (one heavy command at a time, in the foreground, with `timeout`; check for a leftover `chrome`/`vite` process first).
3. If the contract changed: `UPDATE_CONTRACT=1 npx vitest run`, then `dotnet test` in `SpaceshipApp/ShipCore.Core.Tests` and `python3 -I tools/test_contract_check.py`.
4. Screenshots at 1280x800 fit without scrolling for wizard steps.
5. Performance claims come with measurements from Windows or are labelled as not measured.
