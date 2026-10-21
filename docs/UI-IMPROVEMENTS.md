# UI improvements

Written 2026-10-20. Full detail for each item is in `docs/Future-UI-Improvements.md`. Small feature changes, not redesigns. Three phases:

- **Phase 1**: exactly what you asked for.
- **Phase 2**: extra changes I suggest, taken from how engineering tools and HUDs handle the same problems.
- **Phase 3**: work that needs something from you first (videos, art, sounds, Windows measurements).

Where things live today (checked in the repo): hover hints are the "HUD captions" drawn by `Scripts/lib.lua` (about 29 `tip =` sites across `console`, `jarvis`, `location`, `slot`, `target`, `audio`, `dial`); the calendar text is built in `Scripts/location.lua` (`when()` makes "TMRW"/"TODAY"); the audio visual is `Scripts/audio.lua` (Bottom/Audio); the graphics tiers are in the PERF section of the guide. Nothing below has been built yet.

**Decision needed (one):** these items are about the Rainmeter modules, which are not ported to the standalone UI yet (phase P-F). Your ruling says new UI work goes in the standalone UI. My proposal: make the Phase 1 text and hint fixes in the Rainmeter skin now (it is still the app you use every day, and they are small), and build the same behaviour into each module when it is ported. If you want the skin left alone, Phase 1 waits for P-F.

## Already done or noted

| Item | State |
|---|---|
| Complete Control Center overhaul | Done in the standalone UI (categories, Normal/Advanced, search, undo, setup wizard) |
| Redo the frame | Later. Phase 3 (needs art from you) |
| Video that opens from the lock screen into the frame | Later. Phase 3 (needs the video from you) |

## Phase 1: your requests

| # | Change | How I would do it | Done when |
|---|---|---|---|
| 1.1 | **Scrolling and the Control Center view** | Show a scroll bar and fade edges so you can see there is more; remember the scroll position per category; mouse wheel and PgUp/PgDn/Home/End work; the category rail stays pinned while the settings scroll; fit more rows per screen at 1280x800 | You can reach every setting without losing your place; Playwright test for scroll memory and keyboard scrolling |
| 1.2 | **GPU spikes when you actively ...** | **Your sentence stopped after "actively". Tell me the action** (moving the mouse? hovering? talking to JARVIS? dragging a window?). Then: reproduce it and measure GPU before and after (Windows only), find which meter redraws, and cap or pause it while the action runs | A before/after GPU number from Task Manager or `tools/gpu_baseline.ps1`; no estimate |
| 1.3 | **Make the noises easier to control and adjust** | One "Sound" group in the Control Center: master volume, separate sliders for the JARVIS voice, alerts and UI clicks, a mute for each, and a "play sample" button next to every slider; a mute toggle on the HUD itself | Each sound type can be changed and tested without leaving the page |
| 1.4 | **Make the music/noise ball a more accurate visual** | (`audio.lua` already uses 96 analyser bands plus RMS and peak, so first find out what looks wrong to you; see `docs/Future-UI-Improvements.md` 1.4.) Candidate changes: real frequency bands (low / mid / high on a log scale), smooth the rise fast and the fall slowly, show silence as a calm resting ring instead of random motion, and make the size follow loudness in decibels, not raw level | With a test tone the bands line up with the pitch; with silence the ball is still |
| 1.5 | **Calendar: fix the cut-off text** | Smaller font; remove the countdown timer; give the text more width (shorter date column, wrap the title to two lines before cutting it); inside 24 hours show the clock time (`10:24AM`) instead of "TMRW"/"TODAY"; keep a day name beyond 24 hours | No event title is cut at the default size; an event 5 hours away shows its time |
| 1.6 | **Clean up the hover hints** | Rules below | Hint count drops; every remaining hint passes the rule |

### 1.6 Hint rules

Remove a hint when any of these is true:

1. It is on an **app group** (not an individual app).
2. It only **repeats** what is already on screen (the same number, name or status shown again).
3. It only **says how to use** the thing ("click to open", "click to scroll", "drag to move").
4. It describes something obvious from its icon.

Keep a hint only if it adds **information you cannot see**: for example "JARVIS inactive", why something is greyed out, what a coloured warning means, or the full text of a shortened title.

Method: I list all ~29 hint sites with their current text and my keep/remove call in a table, you strike out the ones you disagree with, then I change them. Hint wording also gets shorter (no sentences).

## Phase 2: additional suggestions

These come from general design practice in tools like SolidWorks and Fusion (CAD property managers, snap, shortcut bars), aircraft glass cockpits (declutter, caution levels), game and monitoring overlays (RTSS-style cost readouts, frame-time graphs) and dashboards (Grafana, Task Manager). I did not look any of them up for this list; it is my knowledge of their conventions.

### Less clutter
| # | Change | Why |
|---|---|---|
| 2.1 | **Declutter levels**: a hotkey or tray switch cycles FULL → ESSENTIAL (only alerts, clock, calendar, JARVIS state) → QUIET | Cockpits and CAD let you hide detail without turning the display off |
| 2.2 | **Hint delay and "learn mode"**: hints appear after about 600 ms, and each hint shows only its first few times, then stays quiet | Fusion and VS Code do this; it removes the flicker of passing over things |
| 2.3 | **One status line** (JARVIS state, mic, mute, mode) in a fixed place instead of scattered hints | Keeps the useful "JARVIS inactive" visible without hovering |
| 2.4 | **Alert levels**: colour and motion only for real alerts (advisory / caution / warning); everything normal stays calm | Aviation caution-panel convention; stops the HUD from always looking busy |

### Readability
| # | Change | Why |
|---|---|---|
| 2.5 | **Fixed-width numerals and fixed number formats** (no jumping digits, no changing units) | Dashboards and Task Manager keep numbers from jittering |
| 2.6 | **Relative times in the calendar**: "in 2h 10m", overdue in a warning colour, a thin "now" line in the day view | Calendar apps show urgency this way |
| 2.7 | **Contrast check and a high-contrast option** for the accent colour | The accent is user-chosen; a bad choice makes text unreadable |
| 2.8 | **Reduced-motion toggle** | One switch for all decorative animation; also saves GPU |

### Control Center
| # | Change | Why |
|---|---|---|
| 2.9 | **"Changed from default" filter** and a compare view (current vs default) | Property managers show modified values; helps you find what you changed |
| 2.10 | **Jump list** of groups at the top of each category | Faster than scrolling, same idea as an outline panel |
| 2.11 | **Test button next to risky or audible settings** (voice, wake word, alerts) | Try before you commit |
| 2.12 | **Unsaved/pending marker per row** while a write is waiting for the host | The store already knows; the row does not show it |
| 2.13 | **Keyboard-only use**: visible focus ring everywhere, `/` focuses search, `Esc` clears it | Engineering tools are keyboard-first |

### Layout and cost
| # | Change | Why |
|---|---|---|
| 2.14 | **Snap-to-grid and alignment guides in edit mode** | CAD snap; stops modules from being a few pixels off |
| 2.15 | **"HUD cost" readout** in PERF (its own CPU/GPU share and frame time, last 60 s) | Game overlays show their own cost; backs the "no more than Rainmeter" requirement with a number |
| 2.16 | **Quiet hours / focus schedule**: the HUD hides or mutes itself at set times and while any process on `contract/exam-browsers.json` runs | Builds on the exam-browser list already in the repo |
| 2.17 | **Confirm-free undo toast for every Control Center change**, including resets | The store already has undo; a visible "Undo" for 5 seconds is faster than reaching for it |

## Phase 3: needs something from you

| # | What I need | For |
|---|---|---|
| 3.1 | **The opening video** (lock screen to frame). Please give: the file (MP4 H.264, or WebM), no audio, 3-8 seconds, the same resolution as your monitor, the first frame matching your actual lock screen, the last frame matching the finished frame exactly so it can hand over without a jump. Say whether you want it to play at every sign-in or only the first | The lock-screen-to-frame opening. Note: WebView2 can play it, but playing a video costs GPU, so I would measure it against the "no more than Rainmeter" rule |
| 3.2 | **Frame art** for the redo: layered PNGs with transparency (hull, glass, corners, glow), or a reference image plus your say on what to change. Tell me whether `Pasted image.png` should now be read for ideas (the memory note says I have not read it) | Redoing the frame |
| 3.3 | **Sound files**, if you want your own: WAV, short, one per event (alert, click, wake, error) | Phase 1.3 samples and the Phase 2 sound set |
| 3.4 | **The sentence for 1.2** and a short screen recording or description of when the GPU spikes | Finding the cause |
| 3.5 | **Windows measurements**: the prototype run (`docs/P-D-PROTOTYPE.md`), a 5-minute Task Manager capture with Rainmeter, and one with the change | Every performance claim; nothing here is promised until measured |
| 3.6 | **Your call on the hint table** (strike out hints you want kept) | Phase 1.6 |
| 3.7 | **Confirmed lockdown-browser process names** from Task Manager | Phase 2.16 |

## Suggested order

1. Phase 1.5 (calendar) and 1.6 (hints): small, visible, no measurement needed.
2. Phase 1.1 and 1.3: Control Center and sound controls (can be built and tested in the standalone UI now).
3. Phase 1.4 (audio ball), after I read `audio.lua` to see what data it gets.
4. Phase 1.2 once I have your sentence and a Windows measurement.
5. Phase 2 in the order of your choice; 2.2, 2.3 and 2.4 pair well with 1.6.
6. Phase 3 items as you hand things over.
