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
- **No Blender yet** (user, 2026-11-03: the GPU and memory are busy). Tasks 8-10 of the hyperrealism plan wait for the user's go.
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
