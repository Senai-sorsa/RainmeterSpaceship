# Hyperrealism Implementation Plan (written 2026-11-02, nothing here is built yet)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take the CSpace HUD from "polished FUI" to the hyperreal look of `Refrences-Art/`, while keeping the base frame and the layout, keeping the tier system, and using **less** GPU than today (or no more than +5 GPU points on FULL).

**Architecture:** Three cheap mechanisms replace today's per-element tricks:
1. **One quarter-resolution light canvas** (bloom, lens dirt, glass ghost), fed by the ops the modules already tag as glow. It replaces the CSS `filter: blur()` groups that the GPU re-blurs on every update.
2. **An offline Blender render of the cockpit shell**: same 2D layout, real bevels and curvature, and grayscale light passes tinted live. Zero runtime cost.
3. **A shared curvature table** so the long HUD elements bend with the rendered shell.

**Tech Stack:** Preact + SVG (existing), Canvas2D (new, built in), Blender 5.2 Cycles (offline only, already installed at `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`), Python 3.12 + numpy (existing), Vitest, Playwright.

**Spec:** this file, §A (research) and §B (design). Companion plan: `tasks/line-art-realism-plan.md` (K1-K12, R0-R12).

---

## §0 Start condition: after the current runner finishes
Another session is executing `tasks/line-art-realism-plan.md`; at the time of writing it has committed R1-R9 (`aebe8b4`), and `boot.ts` is dirty (R10 in progress).
Do not start until all of these hold:
- [ ] `git log --oneline -20` shows the R12 commit (or the user says the runner is done or stopped).
- [ ] `git status --short SpaceshipApp/ tools/ Skins/Spaceship/@Resources/Images` shows no modified files from that session.
- [ ] Read §7 of `tasks/line-art-realism-plan.md`. Copy its last measurement row into §D below as the "before" point.
- [ ] If R11 added K7 (chromatic-fringe copies on text), leave it in. Task 4 looks at whether the light canvas makes it redundant, and removes it only with the user's OK.
- [ ] Work on a new branch off the runner's final commit: `git switch -c feature/hyperreal`.

## Global Constraints
- Read `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` first (fake first, dry run first, no real destructive calls). Both CLAUDE.md files apply.
- Keep the base frame and the layout; **do not move features** (memory `visual-overhaul-direction`). Zone positions in `layout.json` are not edited.
- Tiers: FULL (0) gets the new effects. LITE (1) keeps exactly what it has today, unless a task says otherwise. LOW (2) and STEALTH (3) are unchanged.
- No new npm or pip dependencies. Blender is an **offline** tool, not shipped; ask the user before the first Blender run (Task 8).
- Do not touch JARVIS Python files (`Skins/Spaceship/@Resources/Jarvis/**`).
- The Rainmeter skin's images (`Skins/Spaceship/@Resources/Images/*.png`) are shared with Rainmeter. New render art goes in a **new folder** (`Images/Render/`), and the existing files are not overwritten.
- Settings rule: every new key goes into `Skins/Spaceship/@Resources/Settings.inc` **and** `src/settings/registry.ts` with the same default. Then run `npm run gen` and `UPDATE_CONTRACT=1 npx vitest run tests/contract.test.ts`.
- One commit per task, explicit paths (never `git add .`). Commit messages carry goal, scope, non-goals, acceptance, validation, risks and rollback (CLAUDE.md §3), and end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Gates after every task (from `SpaceshipApp/SpaceshipUI`): `npx tsc --noEmit -p .`, `npx vitest run`, `npx playwright test`, `npx vite build`. Report exact results; never claim a pass that was not run.
- Perf budget: headless CPU (`tools/visual-check/hold.cjs` + `cpu.ps1 15`) no more than +10 % over the §0 point. Live GPU (`tools/gpu_baseline.ps1`, only with the user's OK) no sustained rise over +5 points, and no spikes on update.
- Do not push and do not deploy without the user's word.

## Review Focus
1. **Display scale / window resize / zoom**: the light canvas must stay registered on the SVG after a resize or DPI change. It re-reads every anchor's CTM on `resize` (test in Task 3).
2. **A module hides or unmounts** (Off_ settings, console OFF tab, pop-up closes): its light must disappear on the next frame, not linger (test in Task 2 + Task 3).
3. **Tier changes while running** (FULL→LITE→FULL from GPU load): the canvas clears on LITE and rebuilds on FULL, with no stale frame (test in Task 3).
4. **Fonts not yet loaded on first paint**: text glow drawn in a fallback font must be redrawn once `document.fonts.ready` resolves (test in Task 3).
5. **Theme colour change** (ColorAccent / JARVIS state colours): the tinted light passes and the glass layer follow the new colour without a reload (test in Task 9).

---

## §A Research: why the references look real, and what it costs

### A1. Verdict on the current plan
Done well, `line-art-realism-plan.md` reaches **polished FUI**: lit display bodies, gradients, a hot-core ramp, spill, holograms. It does not reach **hyperreal**, for six reasons:

| # | Gap | Evidence |
|---|---|---|
| G1 | No curvature anywhere. The main reference is literally named "try to capture curvness". | `MAIN-REFRENCE-…jpg`; zone matrices are 2D affine |
| G2 | The hull is a procedural 2D texture (numpy streaks and grime on flat polygons), not lit geometry. The references' realism is mostly *material and light*: bevels catching light, AO in seams, curved glossy panels, contact shadows. | `tools/frame_render.py` docstring; `images (5).jpg` |
| G3 | No camera/lens layer. Every reference is seen through a lens: multi-radius bloom, slight softness, grain, lens dirt lit by bright sources, faint reflections in the glass. | all references; PremiumBeat tips 3, 4, 8, 9, bonus |
| G4 | Bloom is the wrong kind, and in the wrong place for the GPU. It is a CSS `filter: blur()` on SVG groups (`draw/ops.tsx:51`), and per text element (`ops.tsx:89`, glow copies on the `top` layer, `canvas.ts:279`), inside modules that re-render (audio ring 20 fps, orb, clock). A blurred element that changes is re-blurred by the GPU on every update. A single radius looks "glowy" rather than optical. | Chrome "Animating a blur"; FrostKiwi |
| G5 | Low-alpha gradients over near-black (K1 bodies, K6 spill) band in 8-bit. Nothing dithers. | Zed GPUI added ±2/255 dither for exactly this |
| G6 | Live GPU has never been measured: every number is headless CPU. | `line-art-realism-plan.md` §7 |

### A2. Findings (with sources in §E)
- **Blur cost is texture taps and memory traffic.** Gaussian cost grows with radius². Downsampling first makes a wide blur cheap. Dual Kawase (ARM, SIGGRAPH 2015) and mip-chain bloom are the motion-stable cheap variants, still used by KDE's blur today. One mobile study measured mipmap bloom at 10.29 ms vs Kawase 11.49 ms vs Gaussian 14.12 ms (a single study, so treat it as indicative).
- **Optical bloom = several radii stacked** (Kawase GDC 2004, Jimenez SIGGRAPH 2014), not one blur. That falloff is what reads as "light through a lens".
- **Chrome:** a blurred element that is promoted gets its blur run on the GPU every frame. A blurred element that is *not* changing gets rasterised once into its parent and reused. So: blur things that change at low resolution, and let static things be cached.
- **Lens dirt** is a scatter coefficient: dirt × bloom. It is invisible in dark areas and lights up only around bright sources, which is exactly why it reads as real glass.
- **Compositing tricks from film FUI** (PremiumBeat): a 2-4 px overall softening to take the "crispy edge" off, CA at ~100.3 % scale, a ghost reflection at 15-30 % (we use far less), optics compensation (lens curvature) for a first-person look, and grain on top.
- **Dither:** add about ±2/255 noise before 8-bit quantisation. Blue noise is the best pattern (Wronski). Blender's 8-bit output has its own `dither_intensity`.
- **Blender baking/rendering:** Cycles can render separate light contributions (light groups / emission passes), so a lit screen's spill can be rendered as its own grayscale pass and tinted at runtime.
- **Screen-graphics practice** (Territory Studio interviews): design for the display hardware it supposedly runs on. A screen in a ship needs a believable surface, bezel and light.

### A3. What "hyperreal" means for each part (the target)
| Part | Today | Target | Mechanism |
|---|---|---|---|
| Hull, struts, dash | numpy-textured flat art | bevelled, curved, PBR metal, AO, contact shadows | Task 8 Blender render |
| Light on the hull | radial CSS pools (`ui/spill.ts`) | rendered spill that wraps bevels and is occluded by struts | Task 8-9 light passes |
| Glow on lines/text | full-res CSS blur per group/text | quarter-res stacked bloom, one layer | Tasks 2-4 |
| Window glass | smudge PNG + vignette | dirt that lights up near bright HUD parts + faint HUD ghost | Tasks 5-6 |
| Banding | none handled | blue-noise grain on the hull | Task 7 |
| Long elements | straight lines | bent with the shell's curvature | Task 10 |
| Composition | many lit things | 1-3 hot things per cluster, one warm accent | Task 11 |

## §B Design decisions
- **D1. Light bus, not DOM scraping.** `OpsView` already splits ops into bloom runs. In canvas mode it renders a hook-carrying `<BloomAnchor>` element in place of each run. The anchor reads its own `getScreenCTM()` (so every zone matrix and the viewBox fit come for free) and posts `{ops, ctm}` to a signal map keyed by a unique name. `OpsView` itself stays a pure function, so the existing tests that call it directly keep working.
- **D2. Text glow joins the light canvas.** On FULL, `top`-layer text copies with `blur > 0` are routed to the bus as well. Bloom drawn *over* the crisp text with `screen` blend is how optical bloom behaves, and it removes one CSS filter per glowing text element.
- **D3. Canvas2D first, WebGL only if measured necessary.** Quarter resolution (1/16 of the pixels) plus `ctx.filter = 'blur()'` at three radii is expected to be cheaper than today. A raw WebGL2 dual-Kawase compositor with radial CA is Task 12, gated on measurements.
- **D4. Redraw on change only.** A bus change schedules one `requestAnimationFrame`. No timers; zero work while idle; nothing runs while the page is hidden.
- **D5. Orthographic shell render.** Rendering the Blender scene with an orthographic camera keeps the 2D silhouette identical to `ref_layout.py`, so the layout cannot move. Curvature is real depth (it changes shading, reflections and highlights), plus an optional small edge sagitta (`curve.json`) that the HUD shares.
- **D6. Settings for rollback at runtime:** `BloomEngine` (`canvas|svg`, default `canvas`), `LensFx` (0/1, default 1), `HullRender` (0/1, default 0 until the user approves the look, then 1). Every effect can be turned off without a code revert.

## File Structure
| File | Responsibility |
|---|---|
| Create `SpaceshipApp/SpaceshipUI/src/draw/bloomBus.ts` | signal map of light entries; `postBloom`, `dropBloom`, `bloomEntries` |
| Create `SpaceshipApp/SpaceshipUI/src/draw/bloomPaint.ts` | pure painters: ops → a 2D context (`paintOps`), the stacked blur (`stackBlur`), the glass layer (`paintGlass`) |
| Create `SpaceshipApp/SpaceshipUI/src/ui/BloomLayer.tsx` | the canvases, rAF coalescing, resize/fonts/tier handling |
| Create `SpaceshipApp/SpaceshipUI/src/draw/bloomMode.ts` | `bloomMode(tier, values)` → `'canvas' \| 'svg' \| 'off'` |
| Modify `SpaceshipApp/SpaceshipUI/src/draw/ops.tsx` | `OpsView` emits `BloomAnchor` in canvas mode |
| Modify `SpaceshipApp/SpaceshipUI/src/Hud.tsx` | mount `<BloomLayer>` after `#hud`, before `<Caption>` |
| Create `tools/lens_assets.py` + `tools/test_lens_assets.py` | deterministic blue-noise tile and lens-dirt map (numpy + zlib PNG writer) |
| Create `SpaceshipApp/SpaceshipUI/src/assets/lens/{bluenoise.png,dirt.png}` | generated, committed |
| Modify `SpaceshipApp/SpaceshipUI/src/ui/FrameLayers.tsx` | grain layer; render-pass layers when `HullRender=1` |
| Create `tools/blender/cockpit_scene.py`, `tools/ref_layout_json.py`, `tools/frame_src/curve.json` | Blender scene from the layout; one curvature table |
| Create `tools/test_render_frame.py` | render output checks (size, window alpha vs `window_mask.png`) |
| Create `Skins/Spaceship/@Resources/Images/Render/*.png` | render art (new folder; Rainmeter's art untouched) |
| Modify `tools/export_ui_assets.py` | `RENDER_IMAGES` copied like `FRAME_IMAGES`; `curve.json` → `src/generated/curve.json` |
| Create `SpaceshipApp/SpaceshipUI/src/draw/curve.ts` | `bendFor(zoneId)` warp from `curve.json` |
| Modify `SpaceshipApp/SpaceshipUI/src/draw/canvas.ts` | optional point warp in `push()`; `hotCount()` |
| Settings: `Skins/Spaceship/@Resources/Settings.inc`, `src/settings/registry.ts`, `contract/config-keys.json` | `BloomEngine`, `LensFx`, `HullRender` |

---

### Task 1: Live GPU baseline (H0)

**Files:** Modify: `tasks/hyperrealism-plan.md` §D only.

- [ ] **Step 1: Ask the user** for OK to run the live HUD and `tools/gpu_baseline.ps1`. It is read-only, but it runs the real app. If the answer is no, record "not run" and continue; Tasks 4 and 13 then compare headless numbers only.
- [ ] **Step 2: Measure** with the user's OK: `powershell -File tools\gpu_baseline.ps1 -Seconds 30 -Label "<label>"` for "FULL idle", "FULL + music", "LITE idle" (LITE via Control Center > Performance, PerfOverride 1). Then headless: run `node tools/visual-check/hold.cjs` in the background, wait 7 s, then `powershell -File tools/visual-check/cpu.ps1 15`, twice.
- [ ] **Step 3: Record** the median and peak per condition in §D, then commit: `git add tasks/hyperrealism-plan.md && git commit -m "docs: hyperreal H0 baseline"`.

### Task 2: Light bus and painters (pure, no UI yet)

**Files:**
- Create: `SpaceshipApp/SpaceshipUI/src/draw/bloomBus.ts`, `src/draw/bloomPaint.ts`, `src/draw/bloomMode.ts`
- Test: `SpaceshipApp/SpaceshipUI/tests/bloom.test.ts`

**Interfaces:**
- Produces:
  - `type Ctm = { a: number; b: number; c: number; d: number; e: number; f: number }` (SVG user units → CSS px)
  - `type BloomEntry = { ops: Op[]; ctm: Ctm }`
  - `bloomEntries: Signal<ReadonlyMap<string, BloomEntry>>`, `postBloom(key: string, e: BloomEntry): void`, `dropBloom(key: string): void`. Each call replaces the map, so subscribers see a new value; posting identical ops+ctm is a no-op (no new map).
  - `type Ctx2D = Pick<CanvasRenderingContext2D, 'setTransform' | 'beginPath' | 'moveTo' | 'lineTo' | 'closePath' | 'ellipse' | 'rect' | 'fill' | 'stroke' | 'fillText' | 'save' | 'restore' | 'drawImage' | 'clearRect'> & { fillStyle: unknown; strokeStyle: unknown; lineWidth: number; font: string; textAlign: CanvasTextAlign; textBaseline: CanvasTextBaseline; globalAlpha: number; globalCompositeOperation: GlobalCompositeOperation; filter: string; lineCap: CanvasLineCap; lineJoin: CanvasLineJoin }`
  - `paintOps(ctx: Ctx2D, entries: Iterable<BloomEntry>, scale: number): void`. `scale` = canvas px per CSS px (0.25). For each entry: `setTransform(ctm.a*scale, ctm.b*scale, ctm.c*scale, ctm.d*scale, ctm.e*scale, ctm.f*scale)`. Then per op: poly → path + stroke/fill; ellipse/rect likewise; text → `font = "<weight> <px>px <font>"` (px as in `ops.tsx`: `size*PT_PX*(FONT_SCALE[font]??1)`), alignment from `textAlign()` mapped to canvas values, `fillText`; image ops are skipped; gradient/pattern fills fall back to the last stop's colour.
  - `BLOOM_STACK: readonly [radiusMul: number, alpha: number][] = [[1, 0.6], [3, 0.3], [9, 0.15]]`
  - `stackBlur(dst: Ctx2D, src: CanvasImageSource, baseRadius: number): void`. For each `[m, a]`: `filter = blur(${baseRadius*m}px)`, `globalAlpha = a`, `drawImage(src, 0, 0)`. Then resets `filter = 'none'` and `globalAlpha = 1`.
  - `bloomMode(tier: number, values: Record<string,string>): 'canvas' | 'svg' | 'off'`: tier ≥ 1 → `'off'` (today only FULL blooms); `values.BloomEngine === 'svg'` → `'svg'`; else `'canvas'`.

- [ ] **Step 1: Write the failing tests** in `tests/bloom.test.ts`, using a recording fake `Ctx2D` (an object whose methods push `[name, ...args]` into `calls`, and whose properties are plain fields):
  - `postBloom then dropBloom removes the entry` → `bloomEntries.value.has('k')` true, then false.
  - `posting identical ops keeps the same map` → the map reference is unchanged after a second identical `postBloom`.
  - `paintOps scales the CTM to the canvas` → with ctm `{a:2,b:0,c:0,d:2,e:10,f:20}` and scale 0.25, the first `setTransform` call is `[0.5,0,0,0.5,2.5,5]`.
  - `paintOps strokes a poly with the op colour and width` → `strokeStyle === 'rgba(0,210,255,0.502)'` (use the project's `css()` from `lib/theme`), `lineWidth === 3`, and a `stroke` call exists.
  - `paintOps draws glow text with the HUD font size` → `font` contains `px Rajdhani` and the size equals `10*4/3*1.14` to 2 decimals; there is one `fillText` call.
  - `paintOps skips image ops` → no `drawImage` call.
  - `stackBlur draws three passes with growing radii` → the `filter` values seen are `['blur(2px)','blur(6px)','blur(18px)']` for base 2, and the alphas are `[0.6,0.3,0.15]`.
  - `bloomMode` → `(0,{})='canvas'`, `(0,{BloomEngine:'svg'})='svg'`, `(1,{})='off'`, `(3,{})='off'`.
- [ ] **Step 2: Run** `npx vitest run tests/bloom.test.ts`. Expected: FAIL (modules not found).
- [ ] **Step 3: Implement** the three files to the interfaces above. `bloomBus` uses `@preact/signals` `signal`. Equality for the no-op check: same `ops` array reference and the same six ctm numbers.
- [ ] **Step 4: Run** `npx vitest run tests/bloom.test.ts`. Expected: PASS. Then run all gates.
- [ ] **Step 5: Commit** `git add src/draw/bloomBus.ts src/draw/bloomPaint.ts src/draw/bloomMode.ts tests/bloom.test.ts` with message `feat(draw): light bus and canvas painters for the quarter-res bloom (H1a)`.

### Task 3: Light canvas in the HUD (canvas mode on FULL)

**Files:**
- Create: `SpaceshipApp/SpaceshipUI/src/ui/BloomLayer.tsx`
- Modify: `src/draw/ops.tsx` (`OpsView`, new `BloomAnchor`), `src/Hud.tsx`, `src/ui/ui.css` (one rule), settings files (`BloomEngine`)
- Test: `tests/ops.test.ts` (add), `tests/bloom.test.ts` (add), `e2e/bloom.spec.ts` (create)

**Interfaces:**
- Consumes: Task 2's `postBloom`, `dropBloom`, `bloomEntries`, `paintOps`, `stackBlur`, `bloomMode`.
- Produces:
  - `OpsView({ ops, name, mode? }: { ops: Op[]; name: string; mode?: 'canvas' | 'svg' | 'off' })`. When `mode === 'canvas'`: each bloom run, and each text op with `shape.blur > 0`, is collected (in order) into one `<BloomAnchor key=… id={name} ops={collected} />` placed where the first run was, and they are **not** emitted as SVG. Default `mode` comes from a module-level `currentBloomMode` signal set by `Hud`, so the 27 call sites need no edits.
  - `BloomAnchor({ id, ops })`: renders `<g data-bloom-anchor={id} />`. It calls `postBloom(id, {ops, ctm})` in `useLayoutEffect` after every render and on `resize`, where `ctm` is `ref.getScreenCTM()`. On unmount it calls `dropBloom(id)`.
  - `BloomLayer({ mode, lens })`: renders `<canvas class="bloom-layer" data-mode={mode} />`. The canvas size is `ceil(innerWidth/4) × ceil(innerHeight/4)`; it is CSS-stretched to `100vw × 100vh`, `position: fixed; inset: 0; pointer-events: none; mix-blend-mode: screen`. On a `bloomEntries` change it schedules one rAF. The draw does: clear an offscreen `src` canvas (same size), `paintOps(src, entries, 0.25)`, clear the visible canvas, `stackBlur(visible, src, baseRadius)` with `baseRadius = max(1, 1.6*glowW*0.45*s/4)` (today's FULL bloom in quarter px), then draws `src` once more at alpha 0.5 (the near-field light). In `mode !== 'canvas'` it clears and draws nothing. It redraws on `resize` and once on `document.fonts.ready`.

- [ ] **Step 1: Write the failing tests:**
  - `tests/ops.test.ts`, `canvas mode replaces bloom runs with one anchor`: OpsView with one plain op, two bloom ops and one text op with `blur: 4`, `mode: 'canvas'` → the children's types are `[OpEl, BloomAnchor]`, no child has `class === 'bloom'`, and the anchor's `ops.length === 3`.
  - `tests/ops.test.ts`, `svg mode is unchanged`: the same ops with `mode: 'svg'` produce the existing `g.bloom` group (assert `props.class === 'bloom'`).
  - `e2e/bloom.spec.ts` (`/?host=mock&preview=1&module=all`, booted as in `frame.spec.ts`):
    - `FULL draws light on one canvas and no blurred svg groups`: `canvas.bloom-layer[data-mode=canvas]` exists; `#hud g.bloom` has count 0; the canvas pixel sum (`getImageData` over the whole canvas, alpha channel) > 0.
    - `light follows a resize` (Review Focus 1): set the viewport to 1280×800, wait one frame, then read the `data-bloom-anchor` CTMs via `page.evaluate` and compare them with the canvas's last-posted CTMs, exposed for tests as `window.__bloomLast` (a map of key → ctm, written only when `import.meta.env.DEV`). They must be equal.
    - `a hidden module's light goes away` (Review Focus 2): open the console OFF tab (as `hud.spec.ts` does), then `window.__bloomLast` has no key starting `B_`/`L_`/`R_`/`C_`.
    - `LITE clears the canvas` (Review Focus 3): set `PerfOverride=1` through the mock host config, then the pixel sum is 0 and `data-mode="off"`; set it back to -1 and the sum is > 0 again.
    - `fonts ready triggers a redraw` (Review Focus 4): in dev, `window.__bloomDraws` counts draws; after `await document.fonts.ready` plus one frame, the count is ≥ 2.
- [ ] **Step 2: Run** `npx vitest run tests/ops.test.ts` and `npx playwright test e2e/bloom.spec.ts`. Expected: FAIL.
- [ ] **Step 3: Add the setting** `BloomEngine`: Settings.inc line `BloomEngine=canvas` next to `GlowAlpha`. In registry.ts: `['BloomEngine', 'Glow engine', 'Canvas: one soft light layer (lighter on the GPU). SVG: the old per-element blur.', sel('canvas|Canvas', 'svg|SVG'), 'canvas', { opt: 1 }]` in the same category as `GlowAlpha`. Then `npm run gen` and `UPDATE_CONTRACT=1 npx vitest run tests/contract.test.ts`.
- [ ] **Step 4: Implement** `BloomAnchor` and the `mode` handling in `ops.tsx`, `BloomLayer.tsx`, and the mount in `Hud.tsx` (set `currentBloomMode.value = bloomMode(perfTier.value, values)` each render; place `<BloomLayer>` right after `</svg>`). The `ui.css` rule for `.bloom-layer` uses `z-index` equal to the svg's, so the Control Center and other DOM pop-ups stay above it.
- [ ] **Step 5: Run** the tests from Step 2, then all gates. Expected: PASS; the existing e2e suite passes unchanged.
- [ ] **Step 6: Commit** the explicit paths with message `feat(ui): quarter-res light canvas replaces per-group CSS blur on FULL (H1b)`.

### Task 4: Measure and tune H1 (no new code paths)

**Files:** Modify: `src/draw/bloomPaint.ts` (`BLOOM_STACK` values only, if tuning is needed), `tasks/hyperrealism-plan.md` §D.

- [ ] **Step 1: Capture** crops before (`BloomEngine=svg`) and after (`canvas`) with `tools/visual-check/proto.cjs` for C_sphere, B_audio, the G1-G4 cells and the L/R rows. Then build one `sheet.cjs` contact sheet and one `pair.cjs` with `MAIN-REFRENCE…jpg`. Save outside the repo (`C:\Users\Senai\cspace-visual-baseline\H1\`).
- [ ] **Step 2: Tune** `BLOOM_STACK` only if the glow is visibly weaker or stronger than svg mode at the line itself. Acceptance: same brightness at the core, wider and softer falloff.
- [ ] **Step 3: Measure** headless CPU (twice) and, if the user OKs it, live GPU for FULL idle and FULL + music, and add rows to §D. Acceptance: within the Global Constraints budget. If the CPU is over budget, check the draw count per second with `window.__bloomDraws`, and if it exceeds the audio feed rate, coalesce harder before anything else.
- [ ] **Step 4: Check K7.** If R11's fringe copies exist, look at a crop with them on and off under canvas bloom. If they add nothing, ask the user before removing them.
- [ ] **Step 5: Commit** `tasks/hyperrealism-plan.md` (and `bloomPaint.ts` if tuned) with message `perf(ui): H1 measured and tuned`.

### Task 5: Lens assets (blue-noise tile, dirt map)

**Files:**
- Create: `tools/lens_assets.py`, `tools/test_lens_assets.py`, `SpaceshipApp/SpaceshipUI/src/assets/lens/bluenoise.png`, `SpaceshipApp/SpaceshipUI/src/assets/lens/dirt.png`

**Interfaces:**
- Produces:
  - `blue_noise(n: int = 128, sigma: float = 1.5, seed: int = 7) -> np.ndarray` (uint8 n×n, void-and-cluster with FFT Gaussian energy, values = rank scaled to 0..255).
  - `dirt(w: int = 640, h: int = 400, seed: int = 11) -> np.ndarray` (uint8 h×w alpha: ~60 soft round smudges of radius 6-40 px at alpha 20-90, plus 6 long faint wipe streaks at 8-14°, blurred σ 1.5).
  - `write_png(path, gray_or_rgba: np.ndarray) -> None` (zlib + struct; no PIL).
  - CLI: `py -3 -I tools/lens_assets.py [--check]` writes or verifies the two PNGs.

- [ ] **Step 1: Write the failing test** `tools/test_lens_assets.py` (plain asserts, like `test_image_frame.py`):
  - `blue_noise(32)` is a permutation: the sorted values cover 0..255 evenly (`np.histogram` with 8 bins, each bin 128 ± 1).
  - Low-frequency energy: the mean of the 3×3 box-filtered tile has std < 0.25 × the raw std (blue noise has little low-frequency content).
  - Determinism: two calls with the same seed are equal.
  - `dirt()` has shape (400, 640), mean alpha between 4 and 20, and max ≥ 60.
  - `write_png` round trip: the PNG signature is present, and the IHDR width/height match.
- [ ] **Step 2: Run** `py -3 -I tools/test_lens_assets.py`. Expected: FAIL (ImportError).
- [ ] **Step 3: Implement** `tools/lens_assets.py`. Dry-run first (CLAUDE-READ rule 2): the script only writes the two PNG paths, nothing else.
- [ ] **Step 4: Run** the test (PASS), then `py -3 -I tools/lens_assets.py` and `py -3 -I tools/lens_assets.py --check` (exit 0).
- [ ] **Step 5: Commit** the four paths with message `feat(tools): deterministic blue-noise and lens-dirt maps (H2a)`.

### Task 6: Glass layer: lens dirt + ghost reflection (FULL)

**Files:**
- Modify: `src/draw/bloomPaint.ts`, `src/ui/BloomLayer.tsx`, settings files (`LensFx`)
- Test: `tests/bloom.test.ts` (add), `e2e/bloom.spec.ts` (add)

**Interfaces:**
- Consumes: the Task 3 bloom canvas; Task 5's `dirt.png`; `window_mask` from `src/generated/frame/manifest.json` (as in `FrameLayers.tsx`).
- Produces: `paintGlass(ctx: Ctx2D, bloom: CanvasImageSource, dirt: CanvasImageSource, w: number, h: number): void`, which:
  1. draws `bloom` at alpha 1 (`source-over`);
  2. sets `destination-in` and draws `dirt` (now bloom × dirt);
  3. sets `source-over`, alpha `GHOST_ALPHA = 0.07`, and draws `bloom` scaled by `GHOST_SCALE = 1.035` about the centre;
  4. resets alpha and the composite mode.

  `BloomLayer` draws this into a second canvas `.glass-layer` (same size and blend as the bloom canvas, opacity 0.8), masked with CSS `mask-image: url(window_mask)`, `mask-mode: luminance` (white = glass), so it shows only on the windows.

- [ ] **Step 1: Write the failing tests:**
  - `paintGlass composites dirt into the light, then adds the ghost`: the recorded `globalCompositeOperation` values in order are `['source-over','destination-in','source-over']`, and the third `drawImage` uses width `w*1.035`.
  - e2e `glass layer only on FULL with LensFx`: `canvas.glass-layer` is visible on FULL; with `LensFx=0` it is absent; on LITE it is absent.
- [ ] **Step 2: Run** them. Expected: FAIL.
- [ ] **Step 3: Add the setting** `LensFx=1` (Settings.inc) and the registry row `['LensFx', 'Glass and lens', 'Smudges on the windows catch the HUD light; a faint reflection of the HUD in the glass.', tog, '1', { opt: 1 }]`. Then gen and contract.
- [ ] **Step 4: Implement**, then run the tests and gates. Expected: PASS.
- [ ] **Step 5: Visual check**: a crop of the upper window with JARVIS speaking (`?jarvis=speak`). Acceptance: smudges visible only near bright HUD parts; the wallpaper is otherwise untouched; no visible doubled text (lower the ghost alpha if there is).
- [ ] **Step 6: Commit** with message `feat(ui): lens dirt and HUD ghost on the window glass (H2b)`.

### Task 7: Grain on the hull (FULL + LITE)

**Files:** Modify: `src/ui/FrameLayers.tsx`; Test: `e2e/frame.spec.ts`.

**Interfaces:** Produces the frame layer `data-layer="grain"`: `background: url(bluenoise.png)` repeat at 128 px, `mix-blend-mode: soft-light`, `opacity: GRAIN = 0.07`, masked to not-glass with the existing `notGlass` mask, placed after `trimspill` and before `Parts`. Present when `PerfTier < 2` and the style is rendered.

- [ ] **Step 1: Update the failing test**: the first assertion in `frame.spec.ts` gets the expected list `[... 'vignette', 'trimspill', 'grain']` for rendered; picture and none are unchanged.
- [ ] **Step 2: Run** `npx playwright test e2e/frame.spec.ts`. Expected: FAIL.
- [ ] **Step 3: Implement** the layer. Import the PNG with `?url` as the other images are.
- [ ] **Step 4: Run** the test and gates (PASS). Visual crop of a K6 spill pool, before and after. Acceptance: no visible banding steps, grain invisible at normal viewing distance at 100 % and 150 %.
- [ ] **Step 5: Commit** with message `feat(ui): blue-noise grain on the hull ends gradient banding (H2c)`.

### Task 8: Blender render of the cockpit shell (needs the user's OK)

**Files:**
- Create: `tools/ref_layout_json.py`, `tools/frame_src/curve.json`, `tools/blender/cockpit_scene.py`, `tools/test_render_frame.py`, `Skins/Spaceship/@Resources/Images/Render/{hull.png,corners.png,light_screens.png,light_trim.png,light_orb.png,glass_reflect.png}`

**Interfaces:**
- Produces:
  - `tools/ref_layout_json.py` → writes `tools/frame_src/layout_polys.json` with `{canvas:{w,h}, windows:[[x,y]...], bezels:[[x,y]...], struts:[...], zones:{id:[x,y,w,h]}}` from `ref_layout.py` (canvas units, already scaled by SX/SY).
  - `tools/frame_src/curve.json`: `{ "radius": 5200, "edgeSag": { "top": 0, "bottom": 0 }, "zones": {} }`. `radius` = cylinder radius in canvas units for depth only; `edgeSag` in canvas units (0 = silhouette identical to today). Task 10 fills `zones`.
  - `cockpit_scene.py` is run as `blender.exe -b --factory-startup -P tools/blender/cockpit_scene.py -- --layout tools/frame_src/layout_polys.json --curve tools/frame_src/curve.json --out Skins/Spaceship/@Resources/Images/Render --samples 256`. It builds:
    - the hull plate from the layout polygons: a 40-unit extrusion, a 6-unit bevel (3 segments), and Z displaced by `z = -(x - w/2)² / (2·radius)` (a cylinder);
    - struts as bevelled bars;
    - materials: Principled BSDF — gunmetal (base 0.05, metallic 1, roughness 0.38 plus a noise-driven roughness variation 0.3-0.5), panel seams with AO.
    - an **orthographic** camera sized to the canvas (2560×1600 px);
    - a key light (area, top-left, cool white) plus a dim warm rim;
    - emissive planes at each lit zone in `SPILL` (`ui/spill.ts`), at strengths proportional to the SPILL percent; trim emitters along the Decor paths; an orb emitter at C_sphere.

    Render passes (Cycles light groups): `hull` (key + rim only, window areas transparent via a holdout), `corners` (as the current corners layer), and `light_screens`, `light_trim`, `light_orb` (each light group alone, **grayscale**, on black). `glass_reflect` is the screens' reflection on a glossy glass plane at the windows only. 8-bit PNG output with `scene.render.dither_intensity = 1.0`.
- [ ] **Step 1: Ask the user** for OK to run Blender, and show the command. Dry run first: read the script for anything outside writing PNGs into `Images/Render/` (it must not touch the network, other folders or system settings).
- [ ] **Step 2: Write the failing test** `tools/test_render_frame.py` (plain asserts; reads PNG headers and alpha with the zlib reader from Task 5):
  - every file exists and is 2560×1600;
  - `hull.png`'s alpha matches `Images/window_mask.png` (inverted) with IoU ≥ 0.995: the layout did not move;
  - each `light_*.png` is grayscale (R=G=B within 1) and has a mean > 0;
  - `curve.json` parses and `edgeSag.top` is within [0, 24].
- [ ] **Step 3: Run** `py -3 -I tools/test_render_frame.py`. Expected: FAIL (files missing).
- [ ] **Step 4: Implement** `ref_layout_json.py` and `cockpit_scene.py`, then render (expect minutes on the RTX; use `--samples 64` for drafts). Iterate on materials only by looking at crops next to `MAIN-REFRENCE…jpg` and `images (5).jpg` (`pair.cjs`).
- [ ] **Step 5: Run** the test. Expected: PASS.
- [ ] **Step 6: Commit** the scripts, `curve.json`, `layout_polys.json` and the PNGs with message `feat(frame): Blender-rendered cockpit shell and grayscale light passes (H3a)`.

### Task 9: Render passes in the app (`HullRender`)

**Files:**
- Modify: `tools/export_ui_assets.py` (`RENDER_IMAGES`, curve.json), `src/ui/FrameLayers.tsx`, settings files (`HullRender`)
- Test: `tools/test_export_ui_assets.py` (add), `e2e/frame.spec.ts` (add)

**Interfaces:**
- Consumes: Task 8's PNGs and `curve.json`.
- Produces:
  - Export: `RENDER_IMAGES = ["render_hull", "render_corners", "light_screens", "light_trim", "light_orb", "glass_reflect"]`, sourced from `Images/Render/<name without render_>.png` and hashed into `src/generated/frame/` like the others. `curve.json` is copied to `src/generated/curve.json`.
  - FrameLayers with `HullRender=1` and the rendered style:
    - `render_hull` and `render_corners` replace `hull` and `corners`;
    - `spill` (radial pools) and `trimspill` are **not** drawn;
    - instead there are three tint layers (the existing `tint()` helper, luminance mask) with `mix-blend-mode: screen`: `light_screens` in the accent at opacity `LIGHT_SCREENS = 0.9` × the hull alpha, `light_trim` in the accent, and `light_orb` in the **current JARVIS state colour** (from `jarvisFeed`);
    - `glass_reflect` is drawn masked to glass at opacity 0.25.
  - `HullRender=1` on LOW/STEALTH still swaps the hull art (static) but drops the light layers.
- [ ] **Step 1: Write the failing tests:**
  - export test: `RENDER_IMAGES` all appear in the generated manifest after `gen`.
  - e2e `render hull swaps art and light`: with `HullRender=1`, the rendered layer list contains `render_hull`, `light_screens`, `light_trim`, `light_orb`, `glass_reflect` and not `spill`/`trimspill`.
  - e2e (Review Focus 5): change `ColorAccent` via the mock host. The computed `background-color` of the `light_screens` layer equals the new colour without a reload. With `?jarvis=listen`, the `light_orb` colour equals `JarvisColorListen`.
- [ ] **Step 2: Run** them. Expected: FAIL.
- [ ] **Step 3: Add the setting** `HullRender=0` and the registry row `['HullRender', 'Rendered hull', 'Use the 3D-rendered cockpit shell with real light from the screens.', tog, '0', { opt: 1 }]`. Gen and contract.
- [ ] **Step 4: Implement**; run the tests and gates (PASS). `npm test` runs `export_ui_assets.py --check`: it must pass.
- [ ] **Step 5: Show the user** a full-frame comparison (old vs `HullRender=1`). If they approve, flip the default to `1` in both Settings.inc and registry.ts, and regenerate the contract.
- [ ] **Step 6: Commit** with message `feat(ui): rendered hull with live-tinted light passes (H3b)`.

### Task 10: Long elements follow the shell's curve

**Files:**
- Create: `src/draw/curve.ts`
- Modify: `src/draw/canvas.ts` (optional warp in `push()`), `tools/frame_src/curve.json` (`zones`), and the modules that draw the strip, the top console line and the rails (`modules/strip.ts`, `modules/console.ts`, `draw/gauge.ts`, via a `Canvas` option only)
- Test: `tests/curve.test.ts`

**Interfaces:**
- Consumes: `src/generated/curve.json` (Task 9).
- Produces:
  - `type Warp = (p: Pt) => Pt`
  - `bendFor(zoneId: string, zone: Zone, s: number): Warp | undefined`: `sag = curve.zones[zoneId]` (canvas units; positive = sags down) maps `y' = y + sag·s·(1 − (2(x−x0)/w − 1)²)`; `undefined` when sag is 0 or missing.
  - `new Canvas(st, zone, { warp })`: when `warp` is set, `push()` maps every poly point. A rect becomes a 4-point poly (24-segment edges for width > 200 units, so it bends). Text, ellipses and gradients map their anchor point only.
- [ ] **Step 1: Write the failing tests** `tests/curve.test.ts`:
  - `bendFor` returns undefined for a zone not in the table;
  - with sag 10 on a zone x0=0, w=200: points x=0 and x=200 keep y; x=100 gets y+10;
  - a Canvas with that warp turns a 200-wide rect into a poly whose middle top point is 10 lower than its ends;
  - text keeps its x and moves its y by the warp at its x.
- [ ] **Step 2: Run** `npx vitest run tests/curve.test.ts`. Expected: FAIL.
- [ ] **Step 3: Implement** `curve.ts` and the Canvas option. Pass `warp: bendFor(zone.id, …)` only in the strip, console and rail call sites.
- [ ] **Step 4: Set the values.** Fill `curve.json.zones` by matching the rendered shell: for B_strip* and T_* zones, measure the shell's bezel line sagitta in the Task 8 render (a crop and a pixel row scan). Start at 0, then step by 2 units until the HUD line runs parallel to the bezel. If `edgeSag` stayed 0, the bezel is straight and these stay 0: report that and skip this task's visual part.
- [ ] **Step 5: Run** the tests and gates (PASS). Visual pair against MAIN-REFRENCE. Hit boxes unchanged: `e2e/hud.spec.ts` passes.
- [ ] **Step 6: Commit** with message `feat(ui): strip, console line and rails follow the shell curvature (H4)`.

### Task 11: Composition rule: few hot things per cluster

**Files:** Modify: `src/draw/canvas.ts` (`hotCount()`); Test: `tests/hotBudget.test.ts`.

**Interfaces:** Produces `Canvas.hotCount(): number` (the number of `hot()`/`hotDot()` calls recorded since construction).

- [ ] **Step 1: Write the failing test** `tests/hotBudget.test.ts`: for every frame builder the module tests already exercise (`graphFrame`, the slot/category frames, `dialFrame`, `stripFrame`, the jarvis frame; reuse fixtures from the existing tests), the Canvas's `hotCount()` ≤ 2 per zone, with idle fixtures. Use `expect.soft` so one run lists every offender.
- [ ] **Step 2: Run** it. Expected: PASS or a list of offenders. If there are offenders, show them to the user with crops; reduce only those the user agrees to.
- [ ] **Step 3: Warm accent check**: grep the modules for `st.warn` use on non-warning items; list the hits for the user (do not change colours without approval).
- [ ] **Step 4: Commit** the test (and agreed changes) with message `test(ui): hot budget per cluster (H5)`.

### Task 12 (only if Task 4 or 13 measurements fail the budget): WebGL2 compositor
**Files:** Create `src/ui/glBloom.ts`; Modify `src/ui/BloomLayer.tsx`.
**Interfaces:** `createGlBloom(canvas: HTMLCanvasElement): { draw(src: TexImageSource, baseRadius: number): void; dispose(): void } | null` (null when WebGL2 is unavailable → Canvas2D path). Dual Kawase: 3 down + 3 up passes, 4 taps each (FrostKiwi's shaders as reference). It adds the stacked composite and a radial chromatic aberration (R/B sampled at ±0.003 × distance from centre). The context is created with `premultipliedAlpha: true`, and shaders output premultiplied colour.
- [ ] Test: unit-test the pass plan (`passPlan(w,h,levels)` → sizes 1/2, 1/4, 1/8), then e2e pixel sum > 0 with `BloomEngine=webgl` (a third option added to the Task 3 select; `bloomMode` returns `'canvas'` for it, and `BloomLayer` picks the GL path). Measure before and after. Commit with message `perf(ui): WebGL2 dual-Kawase light canvas (H1c)`.

### Task 13: Tier pass, final measurements, live check
- [ ] **Step 1:** For each of FULL/LITE/LOW/STEALTH (PerfOverride 0-3), check headlessly which layers exist (e2e assertions in `e2e/bloom.spec.ts`): FULL = bloom + glass + grain (+ light passes if `HullRender`); LITE = grain only (+ static render art); LOW/STEALTH = none of the new layers.
- [ ] **Step 2:** Headless CPU twice, plus live GPU (with the user's OK) for FULL idle, FULL + music, LITE idle. Add the rows to §D. Acceptance: the Global Constraints budget is met.
- [ ] **Step 3:** With the user's OK, a live WebView2 check over the real wallpaper. Collect the user's sign-off.
- [ ] **Step 4:** Commit with message `docs: hyperreal final measurements`.

---

## §C Risks and rollback
| Risk | Impact | Mitigation |
|---|---|---|
| Light canvas misregistered (scale, skew, DPI) | Med | CTM from `getScreenCTM()`; resize test; `BloomEngine=svg` fallback |
| Canvas2D `filter` slower than expected on WebView2 | Med | quarter res; Task 4 measurement; Task 12 WebGL path |
| Ghost/dirt look dirty or reduce legibility | Med | masked to glass only; `LensFx=0`; alphas are constants for tuning |
| Render hull looks different from the user's taste | High | `HullRender` default 0 until the user approves; the old art stays |
| Blender render time / repeatability | Low | `--samples 64` drafts; fixed seeds; outputs committed |
| Bending changes hit boxes | Low | hit regions unchanged (only drawing warps); `hud.spec.ts` |
| Rainmeter skin affected | Low | new art in `Images/Render/` only; Rainmeter ignores the new keys |
Rollback: each task is one commit (`git revert <sha>`). Runtime switches: `BloomEngine=svg`, `LensFx=0`, `HullRender=0`.

## §D Measurements (append one line per check)
| Date | When | Headless CPU | Live GPU % (median / peak) | Notes |
|---|---|---|---|---|
| 2026-11-02 | §0 before (runner's R11 row) | 122.2, 121.8, 119.5 % (median 121.8) | not run | runner's last row; tier pass: FULL 45 bloom groups, LITE/LOW/STEALTH 0 |
| 2026-11-02 | H0 | — (the §0 row stands; Task 4 does the svg/canvas A/B in one sitting) | not run (the user told the runner "dont run it yet") | Task 1 Step 1: no live run without the user's word |
| 2026-11-02 | H1 first cut (no cache) | svg 158.9/161.9; canvas 187.5/193.8; music: svg 155.2/163.6, canvas 209.9/198.8 | not run | canvas redrew all 33 light sources ~11x/s; over budget |
| 2026-11-02 | H1 tuned (tile cache + equal-ops skip + normal blend), interleaved x3 | svg 152.0/158.0/146.0 (median 152); canvas+screen 137.0/140.9/178.1 (median 140.9); canvas normal 119.4/130.7/127.3 (median 127.3) | not run | idle rebuilds only for real changes (orb ~10/s, graphs ~2/s); about 16 % under svg; machine noise is +-20 points between rounds |
| 2026-11-02 | H2 (light + glass + grain), interleaved x3 | idle: svg 128.1/118.1/118.8, new 142.7/154.1/150.7; music: svg 120.9/115.9/131.4, new 178.1/180.9/154.2 | not run | over budget: the glass layer ran two wide blurs on every light redraw |
| 2026-11-03 | H2 tuned (glass at half size, <= 4/s; tiles re-blurred <= 10/s), interleaved x3 | idle: svg 137.4/134.7/132.8 (median 134.7), new 139.3/138.5/139.3 (median 139.3, +3.4 %); music: svg 133.0/129.6/142.9 (median 133.0), new 145.8/142.4/164.8 (median 145.8, +9.6 %) | not run | within the +10 % headless budget; music is at the edge |
| 2026-11-03 | UI session 2 (d98b87c..80443ec: haze, bezels, music motion, CTM cache, orb light, boot settle) vs 3d13728, interleaved x3 | idle: old 124.7/129.0/122.8 (median 124.7), new 128.0/121.6/129.8 (median 128.0, +2.6 %); music: old 167.0/171.3/136.3 (median 167.0), new 168.4/167.1/134.3 (median 167.1, +0.1 %) | not run | within budget; a mid-session run (after haze + bezels + music) gave idle +5.1 %, music -12.1 %; getScreenCTM reads idle 65/s -> <10 per 3 s |

## §E Sources
- FrostKiwi, "Video Game Blurs (and how the best one works)": box/Gaussian/separable, downsampling, Kawase, dual Kawase, stacked blurs (Kawase 2004, Jimenez 2014), ARM 2015, KDE: https://blog.frost.kiwi/dual-kawase/
- Chrome for Developers, "Animating a blur" (promoted + blurred = re-blurred every frame; cache non-changing blurs): https://developer.chrome.com/blog/animated-blur/
- Intel, fast real-time GPU blur algorithms: https://www.intel.com/content/www/us/en/developer/articles/technical/an-investigation-of-fast-real-time-gpu-based-image-blur-algorithms.html
- ETASR mobile bloom study (mipmap 10.29 / Kawase 11.49 / Gaussian 14.12 ms): https://etasr.com/index.php/ETASR/article/download/19101/6940
- pmndrs postprocessing bloom options (mip levels vs resolution, threshold): https://pmndrs.github.io/postprocessing/docs/interfaces/BloomEffectOptions.html
- Unity HDRP thread on lens dirt as a scatter coefficient: https://discussions.unity.com/t/hdrp-5-3-0-ppv3-bloom-blurs-the-whole-frame/730229?page=3
- PremiumBeat, 10 tips for sci-fi HUDs (softening, CA 100.3 %, ghosting, optics compensation, grain): https://www.premiumbeat.com/blog/10-tips-for-creating-sci-fi-huds-in-after-effects/
- Bart Wronski, dithering part three: https://bartwronski.com/2016/10/30/dithering-part-three-real-world-2d-quantization-dithering/
- Zed GPUI gradient dither (±2/255): https://git.secluded.site/zed/commit/a46858ac21ec43b1af94d8b2b9a5a8fde4ac4f01
- Blender manual, render baking / passes: https://docs.blender.org/manual/en/latest/render/cycles/baking.html
- WebGL transparent canvas and premultiplied alpha: https://webgl2fundamentals.org/webgl/lessons/webgl-qna-how-to-make-webgl-canvas-transparent.html
- WebView2 DefaultBackgroundColor (transparent only at alpha 0): https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2controlleroptions
- Territory Studio interview (screen graphics craft): https://www.pushing-pixels.org/?p=9769
- User references: `Refrences-Art/` (MAIN-REFRENCE for curvature and lit MFDs; `images (5).jpg` for materials and light; `images.jpg` for panel frames; `maxresdefault.jpg` and `HUD Interface Scene 03.jpg` for holograms and callouts).
