# From line art to realism: plan for the CSpace HUD (written 2026-11-02, nothing here is built yet)

Hand-off for a new session. Read in order: §0 rules, §1 the problem, §2 the engine (how drawing works today), §3 the
research, §4 the shared techniques, §5 feature by feature, §6 the plan (slices), §7 validation, §8 risks/rollback,
§9 references. Start a fresh session for this work (the last one reached 600k tokens of context; see §10).

## 0. Rules that still apply
- `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` (fake first, dry run first, no real destructive calls) and both CLAUDE.md files.
- **Keep the base frame and the layout. Do not move features.** The user (2026-11-02): "I like the base frame we have
  right now. What I don't like are the designs of the smaller features, ALL of the popups, and a lot more of the frame
  and everything else". The goal now: every feature should look "like looking at a real part of a spaceship HUD", not
  line art. Memory: `visual-overhaul-direction`.
- Work on branch `feature/visual-overhaul` (or a branch off it). One commit per slice, explicit paths, never `git add .`.
  Not pushed yet; push and live run only on the user's word.
- Respect saved choices: `Off_CenterTarget=1`, `Off_CenterHUD=1` (State.inc) keep the windscreen clear.
- Do not touch the JARVIS Python files (another session owns them; they may be dirty in the tree).
- Every change must keep the tier system: FULL (0) gets the effects, LITE (1) a cheaper subset, LOW (2) and STEALTH (3)
  stay as they are. The user does not want the HUD to cause GPU spikes.

## 1. The problem (assessment of 2026-11-02)
The overhaul made the HUD consistent and clean, but most features still read as **glowing vector outlines drawn over a
picture**. The reference cockpits look like **light coming off real screens and projectors inside a ship**.

| Feature | Verdict | Why |
|---|---|---|
| Cockpit frame (hull, struts, glass) | mostly there | rendered picture + sheen/vignette/soft neon; the neon trim is still a flat tube |
| JARVIS orb | close | image-based, volumetric; its rings are thin vector circles |
| Hologram schematics | partial | glowing wireframe is a real convention; no projection beam, depth or instability |
| App / category rows | line art | outlines + stroked icon + text on a faint plate; no lit screen |
| Top telemetry cells | line art | good hierarchy; graphs are a stroke and a faint fill |
| Calendar / network blocks | line art | text on a faint plate between two rules |
| Tabs, page pips, console mode tabs | line art | text with ticks and plates |
| Volume / audio dials | partial | dense dashes and a peak meter; no glass, no depth |
| Bottom status strip | line art | small stroked icons and numbers on a line |
| Tilted side panels (pilot/host) | partial | the tinted screen in perspective feels physical; the text on it is tiny and flat |
| Power / battery rails | line art | a rail, a tick scale and a coloured stroke |
| Pop-ups (log, drawer, boot check) | partial | glass panels; read as an app window, not a screen in the ship |
| Control Center, wizard | partial | polished sci-fi web page (fine for settings, not "hardware") |
| Boot sequence | partial | good motion; vector rings and text |

## 2. The engine today (what a new session must know)
All HUD modules draw through one pipeline, so most realism work can be done **once** and inherited:

- `SpaceshipApp/SpaceshipUI/src/draw/canvas.ts` — `Canvas`, a port of the skin's `lib.lua`. Records ops in zone units on
  four layers in paint order: `base` (fills, hairlines), `glow` (halo strokes), `core` (the lines), `top` (text).
  Primitives: `neon` (halo + glow + core), `line`, `hair`, `poly`, `hairPoly`, `fillPoly`, `fillRect`, `rect`, `circle`,
  `dot`, `halo`, `arc`, `dashArc`, `sector`, `segBar`, `graph`, `brackets`, `chamfer`, `text`, `icon`, `appIcon`,
  `sprite`. `flush()` returns `Op[]`; on FULL it tags glow-layer ops with `bloom` (blur radius).
  `Op = { shape, fill?: RGBA, stroke?: {color,width,dash}, bloom? }` — **fills are solid RGBA only (no gradients yet).**
  `FONT_SCALE` (Rajdhani 1.14) and the weight rule live here too.
- `src/draw/ops.tsx` — `OpsView` turns ops into SVG; consecutive `bloom` ops become one `<g style="filter:blur()">`.
  Text glow is a blurred copy of the text. Images use an feColorMatrix filter per image.
- `src/draw/popup.ts` — the shared pop-up frame (`popupFrame` with offset/alpha, `popupRule`, `popupChip`, `popupClose`).
- `src/draw/gauge.ts` — `railTrack` (rail + tick scale).
- Modules: `src/modules/*.ts` build ops per zone (`graph.ts`, `slot.ts`, `category.ts`, `calendar`/`MissionClock.tsx`,
  `sysinfo.ts`, `console.ts`, `power.ts`, `battery.ts`, `audio.ts`, `dial.ts`, `strip.ts`, `panels.ts`, `jarvis.ts`,
  `drawer.ts`, `boot.ts`, `upkeep.ts`, `dev.ts`, `alert.ts`); wrappers `*Module.tsx` place them in each zone's matrix
  (`layout.zones[].matrix`, many are skewed to follow the cockpit's perspective).
- Frame: `src/ui/FrameLayers.tsx` stacks the rendered cockpit PNGs (`src/generated/frame/*`: glass_fx, scan, shade,
  hull, mist, corners, window_mask) and the Parts SVG (`Decor` neon tubes, `Lights`, `Spill`, `Accents`), then the
  finish layers (sheen, bounce, vignette). `window_mask.png`: white = window glass (luminance mask).
- DOM pop-ups: `src/ui/ui.css` + `src/ui/finish.css` (the lit-glass layer; loaded after ui.css; uses `--line`,
  `--line-hi`, `--glass-hi`, `--glass-lo`, `--chamfer-6/4`). Control Center `ControlCenter.tsx`, wizard `Wizard.tsx`,
  kit `ui/kit/*`, captions `Caption.tsx`, notices `Notices.tsx`.
- Settings: `Skins/Spaceship/@Resources/Settings.inc` → `npm run gen` → `src/generated/settings.json`; registry defaults in
  `src/settings/registry.ts` must equal Settings.inc (a test checks); `UPDATE_CONTRACT=1 npx vitest run tests/contract.test.ts`
  regenerates `contract/config-keys.json` after a registry change. Style object: `src/modules/style.ts`.
- Tiers: `src/host/perfTier.ts` (page computes it); `Style.tier` 0 FULL, 1 LITE, 2 LOW, 3 STEALTH.
- The app is WebView2 (Chromium) with a transparent page: the desktop wallpaper shows through the windows.
- Preview and checks: `tools/visual-check/README.md` (scripts + preview switches).

## 3. What the research found (why the references look real)
Sources in §9. Observed in the user's reference images (`Refrences-Art/`) and in professional FUI work (ArtStation
"FUI hud", Territory Studio / Cantina Creative style, Star Citizen MFDs):

1. **Emissive surfaces, not strokes.** Readouts sit on a *display*: a backlit glass rectangle with a luminance gradient
   (brighter near the source, falling off to the edges), a faint inner border, and a soft glow beyond its edge.
   MAIN-REFRENCE: every MFD at the bottom is a lit screen, not lines on the hull.
2. **Light behaves physically.** Hot cores burn near-white and fall off through the accent colour (a colour ramp, not
   one hue at varying alpha). Bloom is wide and soft around the brightest few things only. Lit screens **spill light** on
   nearby hull surfaces (a coloured pool under/around them).
3. **Fill and mass.** Solid filled segments, gradient bars, dense dot/block fields, filled wedges. Lines are the
   *minority*: structure, ticks, leaders. Our HUD is mostly 1-2 px outlines.
4. **Screen texture and imperfection.** Very faint pixel grid or horizontal scan texture on the display glass, slight
   chromatic fringing on bright edges, tiny luminance noise, a rare flicker on update ("each gauge and readout flickers
   slightly upon entry, mimicking the startup of a high-performance system" — envato listing). Perfect maths reads as
   digital art.
5. **Depth.** Several planes: far layers slightly softer and dimmer, near layers crisp. Holograms have an emitter, a beam
   or base, interference lines and a little instability. Projected HUD elements sit *in front* of the glass.
6. **Colour discipline.** One dominant hue with white-hot accents; a single warm colour (orange/amber) for points of
   interest or warnings. Star Citizen's team works from a mood board to a short style guide (colours, fonts, layout).
7. **Readability first.** Players complain about CRT-style MFDs that are hard to read (RSI forum). Texture and fringing
   must stay subtle; text stays crisp.

## 4. Shared techniques to build once (the "realism kit")
Each is a small engine addition; features then opt in. FULL only unless noted.

| ID | Technique | How (in this codebase) | Cost / tier |
|---|---|---|---|
| K1 | **Gradient fills** | Extend `Op.fill` to `RGBA | Grad` (`{kind:'linear'|'radial', stops:[[off,RGBA]...], x1..}` in zone units). `OpsView` emits one `<linearGradient>/<radialGradient>` in a local `<defs>` per op (id from `name-i`), `gradientUnits="userSpaceOnUse"`. Add `Canvas.gradRect/gradPoly`. | Static; cheap. All tiers. |
| K2 | **Display surface** `Canvas.screen(x,y,w,h,opts)` | A backlit panel: K1 gradient body (lit from the source edge), inner hairline at 30 %, a 1 px bright top edge, corner cut option, faint pixel texture (K4), and an outer glow (a blurred copy of the outline on the glow layer). Feature graphics are drawn *on* it. | Static ops; blur via bloom group. LITE: no texture, no outer glow. |
| K3 | **Hot-core colour ramp** | In `neon()`: core = mix(col, white, 0.55..0.75) by brightness, inner glow = col, outer halo = col darkened/shifted. Today `coreWhite` mixes evenly. Make the ramp a function `heat(col, k)` in canvas.ts. | Free. All tiers. |
| K4 | **Screen texture** | One SVG `<pattern>` (2 px scanline or 3 px pixel grid, 3-5 % alpha) defined once in `Hud.tsx` `<defs>`, used as a second fill on K2 bodies (`fill="url(#hud-scan)"`). No animation. | Static; cheap. FULL + LITE. |
| K5 | **Two-pass bloom** | Bloom today = one blur of the glow layer. Add a *wide* faint pass only for elements tagged `hot` (orb rings, lit values, active tab): blur ~3x, alpha low. Implement as a second bloom value on ops (`bloom2`) grouped like `bloom`. | One more blurred group per module; measure GPU. FULL only. |
| K6 | **Light spill on the hull** | In `FrameLayers.tsx` (after hull/corners, before Parts): radial accent pools at each lit feature's zone centre (from `layout.zones`, transformed by the zone matrix), `mix-blend-mode: screen`, masked to *not glass* (reuse the `notGlass` mask). Intensity follows the feature (e.g. audio level, JARVIS state) only if cheap; otherwise static. | Static compositing. FULL + LITE. |
| K7 | **Chromatic fringe** | On FULL only, for large bright text and hot strokes: two extra copies offset ±0.6 px in red and blue at 15-20 % alpha (or an SVG filter with feOffset on R/B channels applied to the `top` layer group). Keep text legible. | Extra ops/filter; FULL only; must be measured. |
| K8 | **Depth haze** | Far layers (frame decor, faint grids, back faces) get slightly lower contrast and a tiny blur (0.4 px); near layers (values, active items) crisp. Add `depth?: 'far'|'near'` on ops or per module group. | Static. FULL + LITE. |
| K9 | **Entry flicker / update shimmer** | Reuse `flicker()` from `boot.ts`: when a value changes, its readout gets a 3-frame on-off-on via a CSS class (opacity keyframes, 120 ms) — no JS loop. Rare: only on change, never idle. | CSS only; no idle cost; off under reduced motion. |
| K10 | **Filled instrument shapes** | Prefer `sector`, `segBar`, filled wedges and gradient bars over stroked arcs: e.g. gauge = filled arc sector with K1 gradient + a thin bright leading edge. | Static. All tiers. |
| K11 | **Hologram projection** | For schematics and the orb: a base emitter ellipse (filled radial gradient), a faint beam cone (K1 gradient trapezoid, screen blend), horizontal interference lines across the hologram (K4-style pattern clipped to the icon's box), a slow 1-2 % opacity breathe (CSS). | Static + one CSS animation per hologram (FULL only). |
| K12 | **Glass layer for DOM pop-ups** | `finish.css`: add K4 texture as a background layer, an inner radial light from the header, a 1 px top specular line, and a soft outer glow (box-shadow cannot escape clip-path: use a wrapper or `filter: drop-shadow` on the wrapper). | CSS; static. |

## 5. Feature by feature (current → target → how)
File paths are under `SpaceshipApp/SpaceshipUI/src/` unless shown.

1. **Cockpit frame** (`ui/FrameLayers.tsx`, Parts `Decor.inc` via `frameparts.json`)
   - Target: neon trim reads as a lit inlay in the hull, not a tube on top.
   - How: K3 for the Decor core strokes (white-hot core); K6 spill along the trims (a blurred wide stroke of the same path
     in `screen` blend at 8-12 %, masked to not-glass); keep the glints. Optional K8 on the Decor halo.
2. **JARVIS orb** (`modules/jarvis.ts`, `modules/JarvisModule.tsx`)
   - Target: a projected energy core over an emitter.
   - How: K11 emitter/beam under the orb (the pedestal ellipses are in Parts `Accents`); K5 wide bloom on the active rings;
     K10 for the ring arcs (filled thin sectors with gradient instead of strokes); state colour drives K6 spill.
3. **Hologram schematics** (`modules/category.ts` `schematicFrame`, `scanFrame`)
   - Target: a hologram projected from the panel, slightly unstable.
   - How: K11 (emitter under the box, beam, interference lines clipped to the box, breathe); K8 (back-face copy softer);
     the existing scan line becomes the interference sweep.
4. **App / category rows** (`modules/slot.ts`)
   - Target: each row is a small lit display with an emblem module.
   - How: K2 body behind title/status (gradient lit from the emblem side), K4 texture, emblem as a filled chamfer tile
     (K1) with the icon in white-hot (K3), status as a filled pill (K10) not a dot, the stepped underline as the lit
     bottom edge of the display.
5. **Top telemetry cells** (`modules/graph.ts`)
   - Target: four small MFD screens.
   - How: K2 per cell (lit from the bottom), graph as a K1 gradient area (bright near the line, fading down) + bright
     leading dot (K5), grid via K4-like pattern, the hero number in white-hot (K3) with K9 on change.
6. **Calendar / network blocks** (`modules/MissionClock.tsx`, `modules/sysinfo.ts`)
   - How: K2 body between the rules; first row on a filled highlight band (K10) in its state colour; Wi-Fi emblem bars as
     filled segments; K9 when a row changes.
7. **Tabs, pips, console mode tabs** (`modules/category.ts` `tabsFrame`/`dotsFrame`, `modules/console.ts`)
   - How: the selected item becomes a lit key (K1 gradient plate + K3 text + K5 small bloom); pips as filled cells with
     the current one lit; dividers stay hairlines.
8. **Volume / audio dials** (`modules/dial.ts`, `modules/audio.ts`)
   - How: dial face as a K2 round display (radial K1 gradient, K4 texture), the volume arc as a filled gradient sector
     with a bright leading edge (K10), spectrum spokes as filled wedges with height-based colour ramp (K3), peak meter
     segments filled; K6 spill pool under each dial.
9. **Bottom status strip** (`modules/strip.ts`)
   - How: each readout on a small K2 chip (or one long K2 strip display) so the numbers sit on a lit surface; icons
     filled/duotone rather than stroked.
10. **Tilted side panels** (`modules/panels.ts`, BottomModule)
    - How: they already are screens; add K4 texture, K1 gradient, larger/cleaner text, a K6 spill pool on the hull, K8.
11. **Power / battery rails** (`modules/power.ts`, `modules/battery.ts`, `draw/gauge.ts`)
    - How: the rail becomes a recessed track (dark inset K1) with a filled gradient bar (K10) and a bright leading edge;
      ticks stay; K9 on change.
12. **Pop-ups: JARVIS log, CARGO drawer, boot check** (`draw/popup.ts`, `modules/jarvis.ts`, `modules/drawer.ts`,
    `modules/boot.ts`)
    - Target: screens that "power on" in the cockpit, not app windows.
    - How: `popupFrame` gains K2/K4 (gradient body, texture, specular top line, outer glow), rows on faint alternating
      lit bands, the active row as a lit band; an opening animation (scan-in from the header, 150 ms, CSS) — not the old
      scan line across the screen; K6 spill while open.
13. **Control Center, wizard, captions, notices** (`ui/finish.css`, `ui/kit/*`)
    - Target: settings stay readable; add hardware feel without hurting legibility.
    - How: K12 (texture, inner light, specular line, outer glow on a wrapper); the rail and active items as lit keys; keep
      text crisp (no fringe/flicker here).
14. **Boot sequence** (`modules/boot.ts`)
    - How: K10 filled ring sectors with gradient, K5 bloom on the head, a K11-style emitter glow under the ring, K4 on
      the check panel; the count-up digits in white-hot.

## 6. The plan (slices; one at a time, each its own commit)
For every slice (CLAUDE.md §3): goal, scope, non-goals, acceptance, validation, risks, rollback in the commit message.
Gates: `npx tsc --noEmit -p .`, `npx vitest run`, `npx playwright test`, `npx vite build`; `dotnet build ShipCore.App`
if C# changed. Visual check with `tools/visual-check` (crops + contact sheets). Perf check (§7) after R1 and every 3 slices.

| Slice | Content | Acceptance |
|---|---|---|
| **R0 Baseline** (headless done 2026-11-02; live GPU run still open) | Measure: headless CPU (`hold.cjs`+`cpu.ps1`) and, with the user's OK, a **live WebView2 run** with GPU % / VRAM (Task Manager or `nvidia-smi`) for 60 s idle and with music. Save before-screenshots of every feature (crops, one contact sheet). | Numbers recorded in this file §7; before sheet saved outside the repo. |
| **R1 Engine kit A** (done 2026-11-02: `Op.grad`/`Op.pattern` are separate fields so `Op.fill` stays RGBA for existing code; `Canvas.gradRect/gradPoly/screen`, `heat()`, `HudDefs` with `#hud-scan`; tests `tests/realismKit.test.ts`) | K1 gradients, K2 `screen()`, K3 heat ramp, K4 texture pattern. Unit tests for the new op shapes and for `heat()`. No module uses them yet except one demo in `?panel=kit` or a test page. | Tests pass; demo renders; no visual change elsewhere. |
| **R2 Telemetry + rails** | Features 5 and 11 adopt K2/K3/K10. | Each cell reads as a lit screen in the crop; numbers still crisp; tests updated by behaviour, not op counts. |
| **R3 Rows + blocks** | Features 4 and 6. | Same. |
| **R4 Dials + strip + side panels** | Features 8, 9, 10. | Same; audio ring still moves smoothly (`burst.cjs`). |
| **R5 Light: K5 + K6 + K8** | Two-pass bloom on hot items, hull spill pools, depth haze. | Perf within budget (§7); spill never darkens/tints the windows (mask). |
| **R6 Holograms + orb** | Features 2 and 3 with K11. | Hologram reads as projected; idle CPU unchanged within noise. |
| **R7 Tabs/pips + frame trim** | Features 1 and 7. | Lit keys; trims read as inlays. |
| **R8 Pop-ups** | Feature 12 (+ K9 entry). | Log/drawer/boot check read as cockpit screens; hit boxes unchanged (e2e). |
| **R9 DOM surfaces** | Feature 13 (K12). | Playwright 41/41; contrast still readable. |
| **R10 Boot** | Feature 14. | `bootat.cjs` frames 10/22/45/80/110 look right. |
| **R11 Imperfection** | K7 fringe + K9 shimmer, FULL only, subtle. | Text legibility unchanged at 100 % and 150 % scale; reduced motion turns K9 off. |
| **R12 Tier + perf pass + live check** | Verify LITE/LOW/STEALTH; final measurements; with the user's OK a live WebView2 check over the real wallpaper. | §7 budget met; user signs off. |

### Status (2026-11-02, second session)
R1-R11 built and committed on `feature/visual-overhaul` (one commit per slice; not pushed). R12: tier pass done (below);
the live WebView2 GPU/VRAM run and the user's live sign-off are still open (user: "dont run it yet").
Left out on purpose: K8 depth haze (extra blur groups; measure live GPU first), the K11 hologram breathe (a new idle
animation), an outer glow on the Control Center (needs a wrapper element), log row bands (wrapped text gets noisy).
Tier pass (DOM counts on the full preview with `?audio=demo`, PerfOverride 0-3):

| Tier | gradient fills | texture fills | bloom groups | shimmer | spill / trimspill | text elements |
|---|---|---|---|---|---|---|
| FULL | 65 | 29 | 45 | 4 | yes / yes | 252 |
| LITE | 65 | 29 | 0 | 0 | yes / yes | 244 |
| LOW | 52 | 0 | 0 | 0 | no / no | 137 |
| STEALTH | 50 | 0 | 0 | 0 | no / no | 134 |

LOW and STEALTH keep the static gradient fills (K1/K10 are "all tiers" in section 4; same paint cost as the solid fills
they replaced). If those tiers must look exactly as before, gate `gradRect`/`gradPoly` to a solid fill on tier >= 2.

## 7. Validation and performance budget
- Visual: crops per feature before/after, plus one `sheet.cjs` contact sheet per slice (cheap on tokens).
- Comparison: put our crop next to the matching reference image (`pair.cjs`) — MAIN-REFRENCE for the cockpit,
  `images.jpg` for panel frames, `images (4).jpg` / `maxresdefault.jpg` for data screens and holograms.
- Perf (headless, software rendering; relative only): before this plan, full HUD 115-120 % of one core
  (`hold.cjs` + `cpu.ps1 15`, 2026-11-02). Budget: **no more than +10 %** on FULL in headless; LITE and below unchanged.
- Perf (live WebView2, needs the user's OK): GPU % and VRAM idle and with music, before R1 and after R5/R12. Budget:
  no sustained rise over +5 points of GPU % idle; no spikes on update (watch K5/K7/K11).
- Filters (blur, drop-shadow, mix-blend) rasterize per group: keep them per module group, never per op; animate only
  opacity/transform; nothing animates while idle except existing loops.
- Tests: assert behaviour (which op is the hot segment, which text is shown) not op counts or draw order — several
  tests were rewritten this way already (`tests/power.test.ts`, `tests/graph.test.ts`).
### Measurements (append one line per check)
| Date | When | Headless CPU (`hold.cjs` + `cpu.ps1 15`) | Live GPU % / VRAM | Notes |
|---|---|---|---|---|
| 2026-11-02 | R0 baseline | 118.4 %, 119.4 % of one core | not run (needs the user's OK) | before frames: `C:\Users\Senai\cspace-visual-baseline\R0` (full, audio, drawer, boot 10/45/110, `sweep/`, `sheet-main.png`) |
| 2026-11-02 | after R1 | 119.2 % | not run | no HUD element uses the kit yet (DOM: 0 gradient / 0 texture fills); kit demo `?panel=kit` → `cspace-visual-baseline\R1\kit.png` |
| 2026-11-02 | after R4 | 113.6 %, 119.9 % | not run (user: skip for now) | R2-R4 adopted the kit; audio ring still moves (`burst.cjs` frames differ ~10k px) |
| 2026-11-02 | after R5 | 116.0 %, 116.3 % | not run | K5 hot bloom + K6 spill layer; K8 depth haze deferred (needs per-group blur: measure live GPU first) |
| 2026-11-02 | after R6 | 128.9, 116.0, 114.4, 118.9, 118.8 % (median 118.8) | not run | orb segments: one extra hot-bloom group per frame on FULL; hologram breathe (K11) left out: it would be a new idle animation |
| 2026-11-02 | after R7 | 122.9, 117.3, 119.3 % (median 119.3) | not run | lit keys + trim spill layer (one static 14 px blur group) |
| 2026-11-02 | after R11 | 122.2, 121.8, 119.5 % (median 121.8; about +3 points over baseline, budget +10 %) | not run | fringe on text >= 13 (FULL); shimmer on battery readout and next calendar event |

Note for pixel diffs: two captures of the same code differ by ~130k pixels (animation and the preview feed), so compare
crops by eye or check the DOM, not whole-frame pixel counts.

- C#: `dotnet test` may be blocked by Smart App Control (0x800711C7); do not bypass it. Mirror pure maths in JS if needed.

## 8. Risks and rollback
| Risk | Impact | Mitigation |
|---|---|---|
| GPU cost from blurs/blends | High (user does not want spikes) | FULL only; per group; measure after R1/R5/R11; tier fallbacks |
| Legibility loss (texture, fringe) | Med | Keep K4 ≤ 5 %, K7 only on large text; check at 100 % and 150 % |
| Over-decoration (busy) | Med | Lines become the minority, not more lines; one hot focus per cluster |
| Tests coupled to op counts | Low | Rewrite to behaviour as done for power/graph |
| Skewed zone matrices distort gradients | Low | Gradients in zone units inside the zone group (userSpaceOnUse) so they skew with the zone |
Rollback: each slice is one commit; `git revert <sha>`. R1 is additive (no module uses it) so it can stay even if a
later slice is reverted.

## 9. References
User's images (`Refrences-Art/`, untracked; keep them out of git unless the user says so):
- `MAIN-REFRENCE-try_to_capture_curvness.jpg` — the target: curved cockpit, lit MFD screens at the bottom, thin
  structure lines with bright joints, a warm orange reticle as the focal accent, ship wireframe left, data list right.
- `images.jpg` — chamfered panel/frame set: gradient-filled frames, lit header strips, connector dots.
- `HUD Interface Scene 03.jpg`, `maxresdefault.jpg` — callouts with leader lines, wireframe ship "anatomy", rings with
  micro-ticks, orbit diagrams, warm accents.
- `images (1).jpg`, `images (2).jpg`, `images (3).jpg` — cockpits with free-floating lit screens and reticles.
- `images (4).jpg` — dense data dashboard: gauges, sliders, filled bars, circular keyboard.
- `images (5).jpg` — realistic cockpit interior (materials, lighting, rain).
- `inline_image_preview.jpg` — point-cloud terrain with dense side telemetry.
- `inline_image_preview (1).jpg` — racing HUD: big circular gauges with filled arcs and large numerals.
Online (looked at 2026-11-02):
- ArtStation search "FUI hud", sorted by likes (Love Death + Robots FUI, Mad Dogs, navigation HUDs):
  https://www.artstation.com/search?sort_by=likes&query=FUI%20hud — layered glow, micro-detail, warm accents, depth.
- gskinner, FUI FUN (process: reference gathering, procedural detail): https://blog.gskinner.com/archives/2019/04/fui-fun.html
- Hands & Guis, Star Citizen UI revisited (shared component system per ship): https://www.hudsandguis.com/home/star-citizen-revisited-part-1
- Star Citizen UI process (mood board → style guide): https://starcitizen.tools/User_Interface
- Readability complaints about CRT-style MFDs: https://robertsspaceindustries.com/spectrum/community/SC/forum/4/thread/new-crt-like-mfds-are-unhealthy-for-eyes-and-shoul
- Boot/entry flicker convention (stock listing): https://elements.envato.com/screen-ui-interface-HNUXS8T
- Diegetic vs non-diegetic HUD framework (Fagerholt & Lorentzon 2009), summary: https://www.wayline.io/blog/diegetic-interfaces-game-design
- Audio visualizer DSP (used for the ring): https://raw.org/demo/winamp-equalizer/ ,
  https://www.mathworks.com/help/audio/ref/octavespectrumestimator-system-object.html , https://github.com/stevo-k/AudioAnalyzer
- Inno Setup dark wizard (6.6+): https://jrsoftware.org/files/is6-whatsnew.htm
Useful ArtStation/Pinterest searches for more: "MFD cockpit UI", "sci-fi cockpit screen", "hologram UI", "FUI screen
glow", "Territory Studio", "Cantina Creative", "GMUNK".

## 10. Other useful context
- Done before this plan (see `tasks/visual-overhaul-plan.md` for commits): bloom, Rajdhani text, telemetry cells, glass
  plates on rows/blocks, callouts, pop-up frame, Control Center/wizard finish, frame sheen/bounce/vignette, soft neon
  tubes + glints, new boot sequence, real audio visualizer DSP + 20 fps feed, dark tray menu, dark installer.
- Tools: impeccable plugin (design critique/polish; run its detector after edits), frontend-design plugin, Graphify map
  in `graphify-out/` (the `graphify` CLI may be blocked by Smart App Control; read `graphify-out/graph.json` directly with
  a short Python query), Claude in Chrome for looking at references (open one tab, close it after).
- Token budget (the last session: 325 requests, 111.7M cached tokens re-read, peak context 612k, 89 images): start a fresh
  session per slice group, look at crops and contact sheets instead of full frames, keep command output short, avoid
  reading whole plan files, run `/compact` between slices.
- Known pre-existing items: `dotnet build` warns MSB3277 (WebView2 WPF reference), not ours. The compiled installer in
  `installer/Output` was deleted by an `ISCC /O-` check; rebuild with `installer/Build-Installer.ps1` when needed.
