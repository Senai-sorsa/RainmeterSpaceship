# UI handoff (CSpace HUD visuals), updated 2026-11-03

This handoff covers the visual work only (the HUD, frame and pop-ups). JARVIS is a separate session's work; see §1.
A new session should read this file, then `tasks/hyperrealism-plan.md` (the live plan) and, for history,
`tasks/line-art-realism-plan.md` (slices R0-R12). Everything in §2-§7 was checked against the code and git on
2026-11-03. The older notes in §8 were written from the earlier session's memory; check them against the code before
you rely on a detail.

---

## 1. Rules (read first, every session)
- Read `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` every session, and again before you run any test or script:
  - Fakes first and a dry run first.
  - Grep each script for recycle-bin, power, shutdown, registry, process-kill and file-deletion calls before running it.
  - No real destructive calls in tests.
- Root `CLAUDE.md`: "Dont break anything".
- Project `CLAUDE.md` (scope, safe development, performance evidence, reporting).
- **Do not touch anything JARVIS** (user, 2026-11-03: "dont interfere with stuff related to JARVIS"):
  - `Skins/Spaceship/@Resources/Jarvis/**`
  - `Skins/Spaceship/@Resources/Docs/Jarvis-*`
  - `tasks/jarvis-*`
  - `tasks/phase10-slice2-todo.md`
  - the `.gitignore` edits
  - **Why:** another session owns these files and usually has them uncommitted in the working tree. Never stage them, never stash them, and never run a checkout that would rewrite them.
- **Blender shell render built 2026-11-03 on branch `feature/hull-render`** (see §2c). Task 10 skipped (straight bezel).
- **Permission (user, 2026-11-03):** "Run anything and everything you want - just dont interfere with stuff related to JARVIS." This covers tests, the dev server, headless browsers and the measurement scripts. A live run of the real app and the GPU script `tools/gpu_baseline.ps1` were not done in that session. Running them is now allowed, but the GPU is busy, so measure when it is idle, or ask first.
- Keep the base frame and the layout; do not move features. The goal is realism and finish, not a redesign (memory `visual-overhaul-direction`).
- Make one commit per slice and stage explicit paths. Never use `git add .`. End commit messages with:
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
- Do not push or deploy without the user's word. (Merging into local `main` was asked for and done on 2026-11-03.)
- Keep the tier system:

  | Tier | What it gets |
  |---|---|
  | FULL (0) | The effects |
  | LITE (1) | A cheaper subset |
  | LOW (2) | Stays as it is |
  | STEALTH (3) | Stays as it is |

  `PerfOverride` forces a tier (Settings.inc default 0 = forced FULL). The user does not want GPU spikes.
- Keep `Refrences-Art/` out of git (the user's reference images). Keep secrets out of git.
- User preferences (memory):
  - Refine the small features, all the pop-ups and the frame finish.
  - The music ball "moves weirdly": research real visualizers before changing it.
  - Keep most hints, but condense them.
  - Assets come later.
- What the user wants overall (2026-11-02): **hyperrealism** like `Refrences-Art/` (above all
  `MAIN-REFRENCE-try_to_capture_curvness.jpg`: curvature and lit MFD screens; `images (5).jpg`: materials and light),
  with their layout and **minimal GPU**.

## 2. Repo state (2026-11-03)
- `main` was fast-forwarded to the end of `feature/hyperreal`, so it now holds `feature/visual-overhaul` (R1-R12) plus
  `feature/hyperreal` (H0-H5). Not pushed: `origin/main` is behind.
- Both branches still exist: `feature/visual-overhaul` stops at 296c8ed, and `feature/hyperreal` equals `main`.
- The working tree has uncommitted **JARVIS** changes from the other session (`jarvis.py`, `jarvislib/*`,
  `persona.txt`, `test_jarvis.py`, Docs, `.gitignore`, `tasks/phase10-slice2-todo.md`). Leave them alone.
- Untracked: `Refrences-Art/`, `Skins/Spaceship/@Resources/Jarvis/tools/`, `tasks/jarvis-next-plan-2026-11-02.md`.
- Gates at the last commit (8fac91b), run from `SpaceshipApp/SpaceshipUI`:

  | Gate | Result |
  |---|---|
  | `npx tsc --noEmit -p .` | clean |
  | `npx vitest run` | 428/428 |
  | `npx playwright test` | 57/57 |
  | `npx vite build` | ok (only the usual chunk-size warning) |
  | `py -3 -I tools/test_lens_assets.py` | ok |
  | `py -3 -I tools/lens_assets.py --check` | exit 0 |

- Known flaky e2e tests (each failed once, then passed on rerun):
  - Control Center scroll memory.
  - Wizard Launch below 1100 px.
  - The `control-center.spec.ts:95` "failed write" test prints a progress line that looks like a failure; it is not one.

## 2b. Session 2 (2026-11-03, autonomous run): what was added
Commits on `main`, oldest first (all gates green after each: tsc clean, vitest, playwright, vite build):

| Commit | §12 item | What | Switch |
|---|---|---|---|
| d98b87c | #30 | Light canvas draws rounded rects with `roundRect` | — |
| 64958b7 | #19 | **Music ring motion fixed.** Cause: smoothing was per redraw, and after the host's one quiet frame the ring fell one step per metrics tick (~10 s of visible jumps); metrics ticks also added an extra step during music. Now: time-based attack/release (same values at 20 Hz), one step per spectrum frame, 20 Hz release ticks until rest (~1.6 s, then 0 Hz), peak meter holds 400 ms then falls with gravity, idle ripple cross-fades in. | git revert |
| e0c461f | #7 (K8) | Depth haze: the centre hologram (sphere/target/hud) light tile uses `HAZE_STACK` (same radii, weight moved to wide passes, fainter core): no extra blur cost. With JARVIS on, the orb takes the centre and stays near (it is the focus), so haze shows only with JARVIS off. | `DepthHaze` |
| ad75c7a | #11 | Screen bezels: dark recess + faint lip round every `Canvas.screen()` (graphs, strip cells, sysinfo box), FULL+LITE | `ScreenBezel` |
| a634db6 | #34 | Scroll-memory e2e waits for state (End scrolls smoothly) | — |
| a4fdec8 | #29 | Anchors re-read `getScreenCTM` only when `placeKey()` (viewport, viewBox, ancestor transforms) changes or on resize: 65 reads/s idle -> ~0. Assumes no anchor under a CSS transform animation (e2e guards `.scan`). | git revert |
| f7a7bd8 | #9 | Orb light: a static pool on the hull at C_sphere fades in (0.25 s) while JARVIS listens/speaks; state only, no blur; FULL | `StateLight` |
| 7c5d3e1 | #21 | Lens settles last: grain + glass off during the boot, fade in over 0.9 s after it (instant hide, fade reveal); none under reduced motion | `BootAnim=0` |
| 8abb325 | #22 | Pop-ups (log, drawer, boot check) share the bezel via `Canvas.bezel()` | `ScreenBezel` |
| 80443ec | #24 | Hint audit: only `WallpaperQuality` was over 100 chars; condensed. Hover tips already terse. | — |

New settings (Settings.inc + registry, Display > Theme, advanced; contract regenerated): `DepthHaze`, `ScreenBezel`, `StateLight` (all default 1).
Headless CPU vs 3d13728 (3 interleaved rounds, medians): idle +2.6 %, music +0.1 % (plan §D). Live GPU still not measured.

Tried and dropped: **glare streak (#10)** on the orb. Inside the orb it is invisible; strong enough to see beside it, it read as a flat grey bar, not optics. Reverted, nothing committed.
Audited, no change needed: **motion language (#20)**: all UI transitions are 120-250 ms ease-out/steps, scans linear, no bounce, all in both reduced-motion blocks; the 0.5 s Control Center sweep and the 0.9 s lens settle are deliberate.
Findings for the user (ASK, colour change): **contrast (#27)**: ColorDim (0,110,150) on the darkest panel is 3.27:1, under WCAG AA 4.5:1 for small text; (0,138,188) gives 4.77:1. Text/Accent/White pass (10-16:1).
Not built: Blender Tasks 8-10 (the user allowed Blender, then asked to finish up; only inputs were read: `ref_layout.py` windows/bezels, Decor core paths as `P<n>` LineTo strings in `Skins/Spaceship/Frame/Parts/Decor.inc`), #12 pixel grid (HUD_SCAN already covers it), #13/#15/#17 (low value or need real data), #16 hologram breathe (measure first).
Known flaky (not reproduced in 15 repeats): wizard "stacks below 1100px".

## 3. What the hyperreal work built (commits on `main`, oldest first)
| Commit | Plan task | What |
|---|---|---|
| d0bef9c | — | `tasks/hyperrealism-plan.md`: research, design, tasks |
| 1591b8d | T1 / H0 | Baseline row in plan §D; live GPU not run |
| 1dbc09d | T2 / H1a | `src/draw/bloomBus.ts`, `bloomPaint.ts` (paintOps, stackBlur), `bloomMode.ts`; `tests/bloom.test.ts` |
| b7e8600 | T3 / H1b | Light canvas: `OpsView` canvas mode + `BloomAnchor` (`src/draw/ops.tsx`), `src/ui/BloomLayer.tsx`, Hud mount, setting `BloomEngine`; `e2e/bloom.spec.ts` |
| 37efe46 | T4 | Perf: per-anchor tile cache (`TileCache`, `entryBounds`), equal-ops skip in `BloomAnchor`, normal blending (not screen) |
| b2e8615 | T5 / H2a | `tools/lens_assets.py` (+ test): `src/assets/lens/bluenoise.png` (128² void-and-cluster), `dirt.png` (640×400 alpha smudges) |
| b16982e | T6 / H2b | Lens layer: `paintGlass` (wide-spread light × dirt + soft ghost), `.glass-layer` canvas, setting `LensFx` |
| 96d0880 | T7 / H2c | Hull grain: FrameLayers `grain` layer (blue noise, soft-light 7 %, not on glass, tier < 2) |
| e2760f0 | T11 / H5 | `e2e/hot-budget.spec.ts`: at most 2 hot highlights per module, 3 per side column |
| 2aa5856 | T13 (headless) | Per-tier e2e; glass at half size and at most 4 repaints a second; tiles re-blurred at most 10 times a second |
| 8fac91b | final review | Canvas glow clips clipped text; dashed glow stays dashed |

Rollback, at runtime or in git:
- `BloomEngine=svg` brings back the old per-group SVG blur.
- `LensFx=0` turns off the lens layer.
- Each commit can be `git revert`ed on its own; revert newest first if you revert several.

## 4. How the light canvas works (read before you touch glow)
- **Mode:** `bloomMode(tier, values)` in `src/draw/bloomMode.ts` returns:
  - `'canvas'` on FULL (default);
  - `'svg'` when `BloomEngine=svg`;
  - `'off'` when the tier is 1 or higher (only FULL ever bloomed).

  `Hud.tsx` sets `currentBloomMode.value` (in `ops.tsx`) on every render, before the modules render. Every
  `OpsView` reads it unless it is given a `mode` prop, so the 27 `OpsView` call sites needed no edits.
- **OpsView in canvas mode:**
  - It routes every op with `bloom`, and every text op with `shape.blur > 0` (the text glow copies on the `top` layer), into one `<BloomAnchor id={name} ops={light}/>` placed where the first such op was.
  - Everything else is drawn as SVG, exactly as before.
  - On LITE (mode `'off'`), the SVG text glow (CSS blur per text) still exists, unchanged from before.
- **BloomAnchor:**
  - It renders `<g data-bloom-anchor data-bloom-key>`.
  - In `useLayoutEffect`, and on every `resize`, it posts `{ops, ctm: getScreenCTM()}` to the bus under a unique key `name#n`. On unmount it drops the key.
  - It keeps the previous ops array when the ops are the same objects **or** have equal JSON. Some modules rebuild equal ops on every timer tick: the console, the power rail and the tabs.
- **Bus** (`bloomBus.ts`): `bloomEntries` is a signal map. `postBloom` is a no-op for the same ops array and the same CTM numbers; a change replaces the map.
- **BloomLayer** (`src/ui/BloomLayer.tsx`):
  - **Size:** the canvas is `ceil(innerWidth / 4) × ceil(innerHeight / 4)`, CSS-stretched to the viewport, with `pointer-events: none` and normal blending (`ui.css .bloom-layer`).
  - **Mounting:** it is always mounted. When it was gated on the console OFF tab, the light went stale.
  - **Tiles:** each anchor gets a cached tile (`TileCache` in `bloomPaint.ts`). The tile box comes from `entryBounds()`, padded by `ceil(baseRadius × 9 × 2.5)`.
  - **Building a tile:** `paintOps` → `stackBlur` (three passes, `BLOOM_STACK` = [[1, 0.6], [3, 0.3], [9, 0.15]]) → plus the unblurred core at alpha 0.5.
  - **When tiles rebuild:** only when the entry object changes, and at most every `TILE_MS` = 100 ms. A trailing `setTimeout` catches the last change.
  - **A frame** is `clearRect` plus one `drawImage` per tile.
  - **Radius:** `baseRadius = max(0.5, 1.6 × GlowWidth × 0.45 × Scale × 0.25)`, today's FULL bloom in light-canvas px.
  - **When it draws:** redraws are rAF-coalesced and happen only on a bus change, a resize, or `document.fonts.ready` (which rebuilds all tiles once).
- **Lens / glass** (`.glass-layer`, FULL and `LensFx` ≠ 0 and `Off_Frame` ≠ 1):
  - Painted at `GLASS_SCALE` = 0.5 of the light canvas size, at most every `GLASS_MS` = 250 ms.
  - `paintGlass`:
    - the light canvas drawn twice with `blur(LENS_SPREAD = 7px)`;
    - `destination-in` the dirt PNG, which gives light × dirt (the smudges show only near bright parts);
    - a ghost of the light at `GHOST_ALPHA` 0.07, `GHOST_SCALE` 1.035, `blur(GHOST_BLUR = 2px)`.
  - It covers the whole view, not only the windows. Masked to the windows, it showed almost nothing, because little HUD light falls on the glass; lens dirt is a camera-lens effect.
- **Grain** (`FrameLayers.tsx`, the `Grain` component and `GRAIN` = 0.07):
  - The blue-noise tile at 128 px, `soft-light`, `notGlassMask`.
  - Rendered style only, and only when `PerfTier` < 2.
  - `e2e/frame.spec.ts` expects the layer list `… 'vignette', 'trimspill', 'grain'`.
- **Dev-only hooks** (`import.meta.env.DEV`; the e2e tests use them):
  - `window.__bloomLast` (key → ctm, as of the last draw)
  - `__bloomDraws`
  - `__bloomTileBuilds`
  - `__bloomBuiltBy` (key → number of rebuilds)
  - `__glassDraws`
- **Tuning knobs** (all in `src/draw/bloomPaint.ts`):
  - `BLOOM_STACK`
  - `TILE_MS`
  - `GHOST_ALPHA`, `GHOST_SCALE`, `GHOST_BLUR`
  - `LENS_SPREAD`
  - `GLASS_SCALE`, `GLASS_MS`
  - Grain: `GRAIN` in `FrameLayers.tsx`.
  - The lens effect is deliberately faint (glass canvas alpha max about 14/255). If the user wants it stronger, raise `LENS_SPREAD` or draw the spread a third time; for the reflection, raise `GHOST_ALPHA`.
- **Settings added** (in both `Skins/Spaceship/@Resources/Settings.inc` and `src/settings/registry.ts`, Display > Theme, advanced; contract regenerated):

  | Setting | Values | Default |
  |---|---|---|
  | `BloomEngine` | canvas \| svg | canvas |
  | `LensFx` | 0 / 1 | 1 |

  After any registry change, run `npm run gen` and `UPDATE_CONTRACT=1 npx vitest run tests/contract.test.ts`.

## 5. Measurements (headless Chromium, software rendering, % of one core; NOT WebView2)
- **Method:**
  1. Start the dev server: `cd SpaceshipApp/SpaceshipUI && npx vite --port 5199 --strictPort`. One was already running on 5199 during the session; it serves the working tree.
  2. Hold the HUD open with a config: a variant of `tools/visual-check/hold.cjs` that passes the config into `addInitScript((c) => localStorage.setItem('mockhost.v1', JSON.stringify({config: JSON.parse(c), setupDone: true, aboutMe: ''})), cfg)` and appends an optional query such as `&audio=demo`. The stock `hold.cjs` has no config argument; the variant lived in the session scratchpad and is gone, so re-create it (about 10 lines).
  3. Wait 7 s, then run `powershell -File tools/visual-check/cpu.ps1 15`.
  4. **Interleave** the conditions and repeat them 3 times. Between rounds the machine drifts by ±20 points, so only interleaved medians mean anything.
- **Results:**

  | When | Condition | Old SVG glow | New layers | Change |
  |---|---|---|---|---|
  | Final (2aa5856 / 8fac91b) | Idle | 134.7 | 139.3 | +3.4 % |
  | Final (2aa5856 / 8fac91b) | Music (`&audio=demo`) | 133.0 | 145.8 | +9.6 % |
  | H1 tuned, before the lens layer | Idle | 152 | 127 (canvas only) | −16 % |

  The final numbers are medians of 3 interleaved rounds. The budget is +10 % headless, so music is at the edge.
- **Live WebView2 GPU / VRAM: never measured.** `tools/gpu_baseline.ps1 -Seconds 30 -Label "..."` is read-only.
  - **Why it matters:** headless uses software rasterisation, which overstates canvas filter costs. The live number decides.
  - **How:** measure FULL idle, FULL with music and LITE idle, each with `BloomEngine=svg` and with `canvas`, and record them in `tasks/hyperrealism-plan.md` §D.

## 6. Decisions made (rulings), with the cost if wrong
- **Glass covers the whole view, not just the windows:** smudges may also appear faintly over the hull.
- **Ghost blurred:** none.
- **Normal blend instead of screen:** glow over bright text is very slightly less additive. A side-by-side crop showed no visible difference.
- **Glow rebuild cap of 10 a second:** the glow trails the audio ring by up to 100 ms.
- **Glass repaint cap of 4 a second:** the smudge glow lags up to 250 ms.
- **K7 fringe copies (R11) kept:** they are blur-0 SVG text and not routed to the canvas. Removing them needs the user's OK.
- **Hot budget is an e2e count (svg engine) rather than `Canvas.hotCount()`:** a hot op with the normal radius would not be counted.
- **Task 12 (WebGL2 dual-Kawase compositor) skipped:** the headless budget was met. Revisit if the live GPU number is bad.
- **No git worktree used:** the branch was cut in place.
- **Final review was a self-review:** the session rules allow subagents only when the user asks. If you want an independent review of `296c8ed..8fac91b`, ask the user.
- **Deferred minors:**
  - Rounded rects (`rect.r`) glow with square corners.
  - `getScreenCTM` is read by every anchor on every Hud render (33 reads); it could be cached per resize.
- **Warm colour (`st.warn`) used for things that may not be warnings, for the user to decide (unchanged):**
  - `console.ts:124` status message
  - `dial.ts:124` sub-label
  - `jarvis.ts:331` and `jarvis.ts:335` system lines
  - `sysinfo.ts:54` speed-test box
  - `sphere.ts:42` orange

## 7. What to work on next (priority order)
1. **Live check, when the user's GPU is free:** measure as in §5, and have the user look at the real HUD over their wallpaper and tune the lens strength.
2. **Hyperreal plan Tasks 8-10 (Blender), only on the user's go (GPU busy on 2026-11-03).** This is the biggest remaining realism gain, at zero runtime cost.
   - Blender 5.2 is installed at `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`; numpy is in `py -3`; PIL is not (use the PNG writer in `tools/lens_assets.py`).
   - **Task 8:** `tools/blender/cockpit_scene.py` with an orthographic camera, so the layout cannot move. Outputs go to `Skins/Spaceship/@Resources/Images/Render/`. Rainmeter's own images must not change.
   - **Task 9:** `HullRender` setting, live-tinted light passes.
   - **Task 10:** `curve.json`, so the strip, console and rails bend with the shell.
   - Full specs, tests and commands are in the plan.
3. **Other UI improvements that do not need Blender** (candidates; check each with the user before building):
   - **Depth haze (K8)** on the light canvas: far or decor layers get a little extra blur in their tile only (cheap now that tiles are cached). This needs a per-anchor "far" flag on `OpsView`.
   - **Music ball motion:** the user says it "moves weirdly". Research per-band attack/decay smoothing first (see the sources in `line-art-realism-plan.md` §9), then change `src/modules/audio.ts`.
   - **Curvature without Blender:** bend the long elements (bottom strip, console line, rails) along the existing frame's bezel lines. Plan Task 10's `bendFor`/warp design works without the render if `curve.json` is measured from today's frame. Today's frame lines are straight, so this only makes sense together with a curved frame.
   - **Hologram breathe (K11)** throttled to the light canvas's 10 Hz tile cap, FULL only. Measure first.
   - **Control Center outer glow** (needs a wrapper element) and **JARVIS log row bands** (were noisy on wrapped text).
     - **Note:** the JARVIS log *pop-up* is HUD UI (`src/modules/jarvis.ts`), not JARVIS Python. It is OK to style; do not touch the Python side.
   - **LOW/STEALTH gradients:** decide whether they should go back to flat fills (about two lines in `canvas.ts` `push()`/`scaledGrad()`).
   - **The deferred minors in §6:** rounded glow corners, CTM caching.
   - **K7 fringe:** decide with the user whether to keep it now that the light canvas exists.
4. **Push:** only on the user's word. `origin/main` is 200+ commits behind local `main`.

## 8. Older notes (from the earlier session's memory; verify against the code)
### Where things live (`SpaceshipApp/SpaceshipUI/`)
- Preact + SVG HUD in WebView2 (transparent page; the desktop wallpaper shows through the windows).
- Canvas engine: `src/draw/canvas.ts`, rendered by `src/draw/ops.tsx` (`OpsView`, `OpEl`, `HudDefs`). Ops go on four layers: base, glow, core, top.
- Visual checks: `tools/visual-check` (README). `?panel=kit` shows the RealismKit demo. Before/after crops are in `C:\Users\Senai\cspace-visual-baseline\R0..R11`.
- Whole-frame pixel diffs are noise (about 130k px between two captures of the same code): use DOM counts and per-zone crops.
- Preview switches: `?preview=1&module=all`, `?jarvis=<state>`, `?audio=demo`, `?jarvislog=demo`, `?drawer=1`, `?bootat=<frame>`, `?panel=control|kit|demo`, `?debug=1`.

### Realism kit (R1, `src/draw/canvas.ts`)
- **`Op` fields:** `grad?`, `pattern?` and `shimmer?`, kept separate from `fill`, which stays RGBA. Gradients use `userSpaceOnUse`, so they skew with the zone matrix.
- **Exports:**
  - `Grad` and `GradStop`.
  - `HUD_SCAN` (a 3×3 pattern at 0.045 opacity).
  - `ScreenOpts`.
  - `heat(st, col, k)`: mixes towards white by 0.55 + 0.2k and returns the colour unchanged when `CoreWhite` ≤ 0.
- **Methods:**
  - `gradRect`, `gradPoly`.
  - `texture()`: FULL and LITE.
  - `screen()` by tier:

    | Tier | `screen()` draws |
    |---|---|
    | FULL | Gradient, texture, glow, edge and inner border |
    | LITE | The same without the glow |
    | LOW and up | Flat body and the inner border |

  - `hot()` / `hotDot()`: FULL only. They go to `hotOps`, which `flush()` emits first with `bloom × 3`. In canvas mode they become part of the anchor's light, like the other glow.
- **`TextOpts`:**
  - `fringe`: FULL only, on by default for size 13 and up; red and blue copies at ±0.6/s, 17 % alpha.
  - `shimmer`: FULL only. `OpsView` wraps the op in `<g key="i~value" class="shimmer">`. Canvas mode keeps that wrapper for non-glow ops.
- **`OpEl` quirk:** it calls `Shape()` as a plain function, so a plain op is a bare SVG element. A test depends on this.
- **Helpers:**
  - `src/draw/plate.ts`: `litPlate`, `rowBand`, `litKey`.
  - `src/draw/gauge.ts`: `railTrack`, `railFill`.
  - `src/draw/popup.ts`: `popupFrame`, `popupRowBand`.
- **CSS keyframes:** `.power-on` (180 ms) and `.shimmer` (120 ms) in `src/ui/ui.css`, off under reduced motion.
- **Hull light:**
  - `src/ui/spill.ts`: `SPILL`, `spillBackground()`.
  - `FrameLayers.tsx`: `Finish` (sheen, bounce, spill, vignette), `notGlassMask()`, `TrimSpill` (Decor core paths, 26-wide stroke, `blur(14px)`, screen, tier < 2).

### Slices R1-R12 (`feature/visual-overhaul`, now in `main`)

| Slice | Commit | Content |
|---|---|---|
| R1 | f05087e | The kit |
| R2 | 7806677 | Telemetry chips and rails |
| R3 | 8b841a4 | Slot plates, clock and sysinfo plates, Wi-Fi bars |
| R4 | 7145d26 | Dial face, audio ring, strip chips, panels |
| R5 | 2cb4575 | Hot bloom and spill |
| R6 | 87973f0 | Hologram emitter and beam; orb dial gradients |
| R7 | 8bb942e | `litKey` tabs and console; `TrimSpill` |
| R8 | a9aec77 | Pop-ups as powered screens (`.power-on`) |
| R9 | aebe8b4 | DOM glass in `finish.css` |
| R10 | ab7621e | Boot ring |
| R11 | 932e18b | Fringe and shimmer |
| R12 | 296c8ed | Docs: tier pass |

Deliberately not built in R1-R12:
- K8 depth haze
- Hologram breathe
- Control Center outer glow
- JARVIS log row bands

### Tier DOM counts after R11 (before the light canvas; with canvas mode FULL now has 0 `g.bloom` groups)

| Tier | Gradients | Textures | Bloom groups | Shimmer | Spill / trimspill |
|---|---|---|---|---|---|
| FULL | 65 | 29 | 45 | 4 | yes / yes |
| LITE | 65 | 29 | 0 | 0 | yes / yes |
| LOW | 52 | 0 | 0 | 0 | no / no |
| STEALTH | 50 | 0 | 0 | 0 | no / no |

## 9. Execution ledger (copy of `.superpowers/sdd/hyperrealism-plan/progress.md`, which is local scratch)
- Tasks complete: 1-7, 11. Task 12 was skipped (budget met). Task 13 is done headless; the live run and the user's check are still open.
- Tasks 8-10 wait for Blender (user: not yet).
- To resume the plan: read `tasks/hyperrealism-plan.md` Task 8. The plan's §0 start condition is satisfied. Work on a new branch off `main`.

---

## 10. Research summary (2026-11-02/03; the full version with sources is in `tasks/hyperrealism-plan.md` §A and §E)
**Why the references look real.** Five things, in order of how much they matter:
1. **Lit materials and geometry.** Bevels catch light, there is ambient occlusion in seams, panels are curved and glossy, there are contact shadows (`images (5).jpg`, MAIN). Our hull is a procedural 2D numpy texture (`tools/frame_render.py`). This is the biggest gap. Plan Task 8 fixes it with Blender, at zero runtime cost.
2. **Light behaves physically.**
   - Bright cores burn white and fall off through the hue (`heat()` does this).
   - Bloom is several radii stacked, not one blur (Kawase GDC 2004; Jimenez SIGGRAPH 2014). The light canvas does this.
   - Screens spill light onto the surfaces around them. Today that is radial CSS pools; Task 9 makes it physically rendered.
3. **The camera lens.**
   - Every reference is "filmed": soft bloom, grain, lens dirt lit only near bright sources, a faint reflection, slight chromatic aberration (CA) at the edges, vignette, and optics compensation (barrel curvature) for a first-person look.
   - Values from PremiumBeat's HUD compositing tips: overall softening blur of 2-4 px; CA about 100.3 % scale; ghost reflection at 15-30 % in film. We use 7 %, because a desktop must stay readable.
4. **Curvature.** The main reference is named for it. Nothing in our HUD curves yet: zone matrices are 2D affine. See Tasks 8 and 10.
5. **Composition.** Dark by default, 1-3 hot things per cluster, one warm accent for focus or warnings, dense micro-detail only in the periphery. Readability first: players complained about CRT-style MFDs in Star Citizen.

**What costs GPU in a web page** (Chrome "Animating a blur"; FrostKiwi "Video Game Blurs"):
- Blur cost is texture taps and memory traffic. A Gaussian grows with radius². Downsampling first makes wide blurs cheap. Dual Kawase / mip-chain bloom is the cheap, motion-stable option (ARM 2015; KDE uses it).
- A blurred element that changes is re-blurred by the GPU on every update. A blurred element that does not change is rasterised once and reused. So: blur things that change at low resolution, and cache everything else. The tile cache does this.
- `mix-blend-mode` and `backdrop-filter` make the browser read back what is behind the element. Keep only a few full-screen blended layers. Normal blending measured cheaper than screen blending for the light canvas.

**Dither.** Add about ±2/255 noise before 8-bit quantisation (Zed GPUI). Blue noise is the best pattern (Bart Wronski). For Blender's 8-bit output, use `dither_intensity`.

**Page lifecycle** (Chrome docs; WebView2 reports):
- Chrome does not call `requestAnimationFrame` for background or hidden pages. Background timers are throttled after about 10 s.
- WebView2 may pause rAF and timers when Windows reports the window as occluded. That is good for power, but check that the HUD wakes up correctly. A third-party app needed a watchdog for this; see the crew v0.12.9 link below.
- Our `host/scheduler.ts` already sleeps between jobs and pauses when the host reports a fullscreen window.

**Desktop-overlay norms.**
- No official overhead figure exists for Wallpaper Engine or Rainmeter. Community reports range from about 4 % to about 50 % GPU depending on the wallpaper; a Steam moderator says it "depends on the particular wallpaper", and badly optimised ones use a lot.
- Task Manager and GPU-Z disagree on GPU %, so always measure with the same tool (`tools/gpu_baseline.ps1`).
- **Lesson:** an always-on overlay has to be judged against "almost nothing", not against a game.

Additional sources from this round:
- Wallpaper Engine performance threads: https://steamcommunity.com/app/431960/discussions/1/135512931353453239 and https://steamcommunity.com/app/431960/discussions/2/1696045708644625403
- Chrome background tabs (rAF paused, timer budget): https://developer.chrome.com/blog/background_tabs
- WebView2 timer throttling proposal: https://github.com/MicrosoftEdge/WebView2Announcements/issues/80
- WebView2 occlusion pausing rAF (third-party report): https://github.com/ArdaDDemir/crew/releases/tag/v0.12.9

## 11. Performance budgets: what is acceptable
These are **recommendations** (engineering targets), not measurements. They are based on the machine and on the HUD's own tier thresholds.
- **Machine** (read 2026-11-03):
  - CPU: AMD Ryzen AI 9 465, 20 logical cores.
  - GPU: hybrid. Radeon 880M (integrated) plus RTX 5070 Laptop (discrete; ECO mode turns it off).
  - RAM: 31 GB.
- **The HUD's own auto tiers** step down at a *whole-GPU* load of 50 % (LITE), 75 % (LOW) and 85 % (STEALTH) (`TierLite`/`TierLow`/`TierStealth` in Settings.inc). The HUD itself must sit far below these, or it will push itself into lower tiers and make them flap.
- **How to read the numbers:**
  - Headless "% of one core" ÷ 20 = % of the whole CPU. For example, 140 % of one core ≈ 7 % of the CPU in Task Manager.
  - Headless includes software rasterisation, which the GPU does in the live app, so headless overstates CPU and says nothing about GPU. Use it only for relative A/B checks.

| Condition (live WebView2, FULL) | CPU, whole machine (Task Manager) | GPU 3D engine, the adapter the HUD runs on | VRAM / RAM (HUD processes) | Spikes |
|---|---|---|---|---|
| Idle, nothing changing | target ≤ 2 %, max 3 % | target ≤ 3 %, max 5 % | ≤ 300 MB VRAM, ≤ 400 MB RAM | none over +10 points |
| Music (audio ring live) | target ≤ 4 %, max 6 % | target ≤ 6 %, max 8 % | same | none over +15 points |
| Opening a pop-up / Control Center | short burst OK | short burst OK | — | under 25 % for under 1 s |
| LITE | ≤ 60 % of the FULL numbers | ≤ 60 % of FULL | — | — |
| LOW / STEALTH | ≤ 1 % | ≤ 2 % | — | — |
| A fullscreen app or game covering the HUD | ≈ 0 (scheduler paused, rAF stopped) | ≈ 0 | — | — |
| On battery | `BatteryMinTier` (default 1 = LITE) applies; use the LITE row | | | |

- **Headless A/B budget** (what the plans use): no more than +10 % over the previous step on FULL, as interleaved medians of 3 rounds.
- **Which GPU:** WebView2 should run on the integrated Radeon in hybrid mode. Check which adapter it uses (`gpu_baseline.ps1` prints one row per GPU; Task Manager has a "GPU engine" column). Never let the HUD wake the RTX 5070 on its own: that costs battery and heat.
- **Frame-rate targets:**

  | What | Rate |
  |---|---|
  | Animations (orb, audio) | ≤ 20-30 fps is enough (the audio feed is 20 fps) |
  | Light tiles | ≤ 10 Hz (`TILE_MS`) |
  | Glass | ≤ 4 Hz |
  | Telemetry | at the host reading rate (about 1-2 Hz) |
  | Everything else | 0 Hz while idle |

## 12. Everything we should still do to improve the UI (after the current work)
Each item says what, why and how, cheapest first. Ask the user before building anything marked (ASK).

### A. Frame and hull (the biggest realism gains)
1. **Blender shell render (Tasks 8-9) (ASK, the GPU must be free).**
   - **What:** bevels, AO, PBR gunmetal with roughness variation, curved dash and bezels, contact shadows; grayscale light passes per light group, tinted live (so theme colours keep working). Orthographic camera, so the layout cannot move.
   - **Also bake:** recessed screen bezels under each MFD zone. That is what makes MAIN's MFDs look like hardware.
2. **Real curvature (Task 10), after the render.** The strip, console line and rails bend with the shell (shared `curve.json`).
3. **Micro-detail on the hull** (baked, free): panel seams, screw heads, warning stencils, tiny serial numbers and vent grilles near the struts. Keep it low-contrast and in the periphery only.
4. **Trim tubes as inlays:** a baked groove that the neon sits in (R7 added the spill; the groove needs the render).
5. **Interior reflections:** a faint baked reflection of the dash lights in the side glass (Task 8's `glass_reflect` pass).

### B. Light, glass, lens (runtime, on the light canvas)
6. **Tune the lens with the user, live:** `LENS_SPREAD`, `GHOST_ALPHA`, and the dirt density (seed and count in `lens_assets.py`).
7. **Depth haze (K8), cheaply:** add a `far` flag on `OpsView`, so the decor, back faces and faint grids get one extra blur pass in their own tile only. It is cached, so it costs almost nothing while idle.
8. **Radial chromatic aberration:** only with the WebGL2 compositor (plan Task 12). Skip unless the live GPU number has headroom. Never per text.
9. **Light that follows state:** the orb's spill brightens when JARVIS speaks, and the audio dial's spill pulses with the level. Change the opacity of a static layer (cheap); never animate a blur.
10. **Glare streaks on the two or three hottest points** (orb core, warning lamp): a tiny precomputed sprite drawn into the light tile, never a full-screen effect.

### C. Screens and instruments (MFD realism)
11. **Bezels around every screen:** a 1-2 px dark recess plus a highlight lip (baked, or `litPlate` variants), so the readouts sit *in* the hull.
12. **Pixel structure on large screens:** a subpixel or fine grid at about 3 % on the side panels and pop-ups only. Readability first; never on small text.
13. **Data density:** peripheral micro-readouts (coordinates, serials, labelled ticks) in the dim colour around the big readouts, as in `inline_image_preview.jpg`. Keep the primary numbers large and clean.
14. **Real data wherever possible,** no static fake numbers. Life comes from data updates, not idle animation.
15. **Entry/update flicker (K9 shimmer):** extend it to more readouts, but only on a change, never while idle.

### D. Holograms and the orb
16. **Hologram breathe (K11):** throttled through the tile cache (≤ 10 Hz), FULL only, opacity only. Measure first.
17. **Interference lines and a little instability** on the schematics: a static pattern plus a rare (every 8-15 s) one-frame glitch. Rare, so it costs nothing on average.
18. **The orb:** its vector rings become filled thin sectors with a gradient (K10), plus a slow travelling hot head.

### E. Motion
19. **Music ball motion (user complaint).**
    - Research per-band attack/decay (fast attack about 10-30 ms, slower release about 150-300 ms), peak-hold with gravity, and log-frequency bands.
    - The DSP is in `ShipCore.Core/SpectrumBands.cs`, mirrored in `tools/visual-check/spec.cjs`; the drawing is in `src/modules/audio.ts`.
    - Show the user frames from `burst.cjs`.
20. **One motion language:** ease-out for things arriving, linear for scanning, no bounce, durations of 120-250 ms. Respect reduced motion (`data-reduce-motion`).
21. **Boot sequence:** add the lens and grain fading in last, as if a camera settles.

### F. Pop-ups, Control Center, wizard
22. **Pop-ups (log, drawer, boot check):** use the same bezel and screen language as the MFDs (item 11). Control Center outer glow via a wrapper element (deferred in R9).
23. **Control Center and wizard stay readable** (they are settings): lit keys for the active items and a subtle texture. No fringe or flicker on their text.
24. **Hints:** the user wants most kept but condensed. Audit every hint string (≤ 1 line) with impeccable (critique/polish).

### G. Typography and colour
25. **One type system:**
    - Rajdhani for labels.
    - A mono font with tabular figures for numbers, so digits don't jitter.
    - Michroma for titles only.
    - Keep sizes ≥ 7 pt at 100 % scale.
26. **Colour discipline:** one dominant hue, white-hot cores, one warm accent. Review the five doubtful `st.warn` uses (§6) with the user.
27. **Contrast check:** dim text on the darkest panels at 100 % and 150 % scale (impeccable's audit can flag it).

### H. Engineering and performance
28. **Live GPU/VRAM measurement** (§5, §11). Do this before anything big.
29. **Cache `getScreenCTM`** per resize instead of on every render (deferred minor).
30. **Rounded-rect glow** (`rect.r`) in `paintOps` (deferred minor).
31. **WebGL2 compositor (Task 12)**, only if the live numbers fail: one pass for bloom + CA + grain + vignette, rendered only when something changed.
32. **LOW/STEALTH gradients:** decide whether they go back to flat fills (about two lines in `canvas.ts`).
33. **K7 fringe:** keep or drop it now that the light canvas exists (ASK).
34. **Flaky e2e tests** (§2): make them wait for state, not for time.
35. **Line endings:** every commit warns "LF will be replaced by CRLF". It is harmless; a `.gitattributes` would silence it. Coordinate first, because the JARVIS session is editing `.gitignore`.

## 13. What should be looked at (audits and risks)
- **Live run over the real wallpaper.** Check:
  - legibility at 100 % and 150 % display scale;
  - lens strength;
  - grain visibility;
  - no doubled text from the ghost;
  - the glow sitting exactly on the lines on every monitor and DPI.
- **WebView2 occlusion:** after a fullscreen game or sleep/resume, does the HUD wake up and redraw the light canvas? rAF can be paused while occluded; BloomLayer redraws on the next bus change or resize.
- **Multi-monitor / DPI change while running:** the anchors re-post on `resize`. Check that a DPI change fires `resize` in WebView2.
- **Battery:** LITE on battery (`BatteryMinTier`). Check that the light and glass layers are off (they are FULL only).
- **Theme colours:** change `ColorAccent` live; check the glow, spill, trim and grain.
- **Rainmeter parity:** the app shares `Settings.inc` and `Images/` with the Rainmeter skin. The hyperreal work changed no Rainmeter images, and the skin ignores the new keys (`BloomEngine`, `LensFx`). Verify the skin still loads if you add more.
- **Reduced motion:** shimmer, power-on and any new animation stop under `data-reduce-motion` / `prefers-reduced-motion`.
- **Push hygiene:** before pushing, run all gates on `main`, make sure no JARVIS files are staged, and keep `Refrences-Art/` untracked.

## 14. Recommendations (how to work)
1. **Measure live before building more.** One `gpu_baseline.ps1` run per condition decides whether the WebGL path (Task 12) or the depth haze (item 7) is affordable.
2. **Bake static, light dynamic.** Anything that does not change goes into PNGs (Blender, numpy); anything that changes goes through the cached light canvas. No new CSS `filter: blur()` on elements that update.
3. **Small slices:** one commit each, an interleaved headless A/B every 2-3 slices, and a crop pair against the matching reference image (`tools/visual-check/pair.cjs`).
4. **Every new effect gets a runtime switch** (like `BloomEngine`/`LensFx`), so the user can roll back without git.
5. **Test behaviour, not op counts.** The bloom tests check what is drawn, where and how often, through the dev hooks (§4).
6. **Look at crops, not full frames.** Full frames are expensive in tokens, and whole-frame pixel diffs are noise.
7. **Ask the user before:** Blender runs, live runs while the GPU is busy, colour changes, removing R-slice effects, and pushing.

## 15. Skills and plugins to use, per part
| Part of the work | Use | Why |
|---|---|---|
| Starting any new feature or effect | `superpowers:brainstorming` | settles the intent and design before code |
| Turning a design into tasks | `superpowers:writing-plans` (save under `tasks/`, as `hyperrealism-plan.md` is) | exact files, interfaces, tests per task |
| Executing a plan | `superpowers:executing-plans` (inline, cheaper), or `superpowers:subagent-driven-development` (a reviewer per task; only if the user asks for agents) | ledger in `.superpowers/sdd/<plan>/progress.md`; `task-start` / `task-done` scripts |
| Every code change | `superpowers:test-driven-development` | watch the test fail first; this caught the clip and dash bugs |
| A test fails or something looks wrong | `superpowers:systematic-debugging` | find the cause before patching (the stale light came from BloomLayer being unmounted) |
| Before saying "done" | `superpowers:verification-before-completion` | run the gates and read the output |
| Reviewing a branch | `superpowers:requesting-code-review`, `code-review` (low/medium; `ultra` is user-triggered and billed), `simplify` | a fresh review (this round's final review was a self-review) |
| Finishing or merging a branch | `superpowers:finishing-a-development-branch` | merge/push options, cleanup |
| Visual design: critique, polish, audit, hierarchy, contrast | `impeccable:impeccable`; its agents: `impeccable-finish-reviewer` (review against the references), `impeccable-asset-producer` (raster assets from approved mocks), `impeccable-documenter` (DESIGN.md) | the design skill for this UI; run its detector after visual edits |
| A bold new look for one part (pop-up style, MFD look) | `frontend-design:frontend-design` | distinctive, non-template choices |
| Gauges, graphs, telemetry cells, stat tiles | `dataviz` | colour formulas, mark specs, sparkline and meter rules |
| Looking at references on the web (ArtStation "FUI hud", "MFD cockpit UI", Territory Studio, Cantina Creative, GMUNK) | `claude-in-chrome` / `anthropic-skills:chrome-browser` | open one tab, read it, close it |
| Broad research with a written report | `anthropic-skills:deep-research` (uses subagents: only if the user asks) | multi-source synthesis |
| Library and API docs (Preact, @preact/signals, Vite, Playwright, Canvas2D, WebView2, Blender `bpy`) | Context7 MCP (`resolve-library-id` → `query-docs`) | current docs; required by `~/.claude/rules/context7.md` |
| Who calls what (modules ↔ draw ↔ host) | `graphify` (`graphify-out/`; the CLI may be blocked by Smart App Control, so read `graph.json` with a short Python query) | cross-file relationships |
| Launching or screenshotting the app | the `run` skill, or the `tools/visual-check` scripts against the dev server on port 5199 | crops, contact sheets, bursts |
| Blender scene (Task 8) | Context7 for the `bpy` docs; plain Python; TDD for `tools/test_render_frame.py` | renders checked by tests (size, window alpha IoU ≥ 0.995) |
| Any host or IPC change | `security-review` | model output must never authorise OS actions |

## 2c. Blender shell render (hyperrealism plan Tasks 8-9; Task 10 skipped) - branch `feature/hull-render`, 2026-11-03
Commits (revert each with `git revert <sha>`): `dfeedcf` Task 8 (scene + passes), `ba4dba6` Task 9 (`HullRender`), `009faba` tuning (darker hull, softer tints).
- **Task 8:** `tools/ref_layout_json.py` -> `tools/frame_src/layout_polys.json` (the folder is gitignored; the two JSONs were added with `git add -f`). `tools/blender/cockpit_scene.py` renders six PNGs into `Skins/Spaceship/@Resources/Images/Render/` (hull, corners, light_screens, light_trim, light_orb, glass_reflect), one Cycles render per pass, orthographic camera, vertical-wall extrusion so the silhouette stays exact. Command (run from the repo root, about 2 min on the RTX):
  `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup -P tools/blender/cockpit_scene.py -- --layout tools/frame_src/layout_polys.json --curve tools/frame_src/curve.json --out Skins/Spaceship/@Resources/Images/Render --samples 256` (`--only hull,corners` for some passes, `--percent 25 --samples 16` for drafts). Light passes are rendered on a neutral diffuse hull, so they can be tinted live. Tuning knobs: `K_SCREEN`, trim/orb emission strengths, world strength (0.22) and sun strengths in the script. Blender's relative `--out` resolves against the drive root when no .blend is loaded; the script now resolves it to an absolute path.
- **Test:** `py -3 -I tools/test_render_frame.py` (size, hull alpha vs window_mask IoU 0.998, grayscale light passes, curve.json).
- **Task 9:** setting `HullRender` (default **0**, both Settings.inc and registry). With 1: FULL swaps hull+corners for the render and adds `light_screens`/`light_trim` (accent), `light_orb` (live JARVIS state colour, brighter while listening or speaking) and `glass_reflect`, all `mix-blend-mode: screen`; spill, trim spill and the CSS orb light are not drawn. LITE: render art plus today's CSS spill. LOW/STEALTH: static hull swap only. Export adds `RENDER_IMAGES` and `src/generated/curve.json`.
- **Task 10 (branch `feature/hull-curve`, stacked on `feature/hull-render`):** `curve.json` `edgeSag` = top 12 / bottom 10. The Blender script bows the long near-horizontal edges inside the canvas (the windscreen's top edge up, its bottom edge down: a barrel, the glass grows, the HUD stays in it; hull alpha IoU vs the old mask 0.9936, the test allows 0.985 once a sag is set). `src/draw/curve.ts` (`bendFor`, `warpPoly`) plus an optional `Zone.id` and `Style.curve` in `Canvas`: with `HullRender=1`, zones listed in `curve.json` `zones` bend their lines, rects (become polys), text/ellipse anchors. **`zones` is empty on purpose:** over one zone's width the shell's curve moves an edge by under 1 px (a 12 px bow over the 1300 px windscreen edge is the largest), and no strip, console line or rail hugs the bowed edges, so a bend would be invisible. To bend one: add `"B_stripL": -4` (units; positive sags down) and look. Decision for you: which edges should bow, and should the Decor trim lines (and their emitters) follow?
- **Default not flipped.** To approve: set `HullRender=1` in Settings.inc and registry.ts, `npm run gen`, `UPDATE_CONTRACT=1 npx vitest run tests/contract.test.ts`.
- **Rollback:** `HullRender=0` (default) or `git revert 009faba ba4dba6 dfeedcf`.
- **Open:** the hull and seams are a first pass (brick-grid seams are arbitrary); check on the real wallpaper. A stray folder `C:\Skins\` from a first Blender draft (relative-path bug, fixed) may still exist: delete it by hand (the safety check blocked me).

## 16. UI clean-up session (2026-11-03) - branch `chore/ui-cleanup` (off `feature/hull-curve`)
Gates after every slice (all green at the tip): `npx tsc --noEmit -p .`, `npx vitest run` (60 files, 450 tests), `npx vite build`, `npx playwright test` (68/68), `py -3 -I tools/test_render_frame.py`, `tools/test_export_ui_assets.py`, `tools/contract_check.py` (all exit 0).
Commits (revert each with `git revert <sha>`):
- `fb9eeda` e2e: the idle-light test waits for state, not a fixed 3 s. Before: `playwright test` x3 = 68/68 each, no flake seen; the 3 s sleep was the one latent flake. The other `waitForTimeout` calls are rate-measurement windows and stay.
- `4d225d0` tests: `HullRender` 0/unset never gives a curve table and never bends; removed the unused `val` import. `tsc --noUnusedLocals --noUnusedParameters` found only that and `consoleIntent`'s unused `view` param (public signature, kept).
- `1fcff97` hints: the 12 longest setting hints (67-93 chars) condensed to about 50-68. The other 150 are <= 57 chars.
- `fc9ea15` contrast (user OK'd): `ColorDim` 0,110,150 -> 0,140,185. Computed: dim text was 2.9-3.7:1 on the darkest panels, now 4.3-5.2:1 (text/accent/warn/white were already >= 6.6:1). Not changed: `lib.lua` fallback and the `control.lua` CYAN preset still carry the old value. Rainmeter's skin reads the same `Settings.inc`, so its dim also brightens.
- `e99180a` render (user OK'd): hull seams dropped (`seams=False`), hull + corners re-rendered (31 s, GPU idle). Alpha identical, IoU 0.9936.
Checked, no commit: list 8 console/network: `?preview=1&module=all`, 60 s, with `HullRender` 0 and 1: 0 warnings/errors, 0 failed requests, all hull/light PNGs served.
Skipped: 5 (`st.warn` list: sites are `canvas.ts:88-89` gauge ramp, `boot.ts:155,164`, `category.ts:112`, `dial.ts:124`, `MissionClock.tsx:29`, `slot.ts:28,75`, `sphere.ts:42`, `strip.ts:37,39`, `sysinfo.ts:54,61`, `upkeep.ts:31`; no colour change without approval); 6 K7 fringe (user: keep); 7 pop-ups unification and the Control Center glow wrapper (ASK, not asked this session); 10 `.gitattributes` (user: skip, coordinate with the JARVIS session); 11 `C:\Skins\` still exists, delete by hand.
For the Live Test: dim-text contrast was computed from token maths, not pixel crops; verify at 100 % and 150 % on the real wallpaper. Note: another session has an uncommitted edit to `tools/contract_check.py` (not staged here).
