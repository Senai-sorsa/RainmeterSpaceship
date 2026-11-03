# Live Test (for a separate session; written 2026-11-03)

Goal: before the user signs off the hyperreal HUD (light canvas, lens, rendered hull, curve), a session checks, measures and
fixes everything it can **by itself**, then reports what only the user can judge. The user should not have to do anything
until the final "look at this" list.

## 0. Read first
1. `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` (fake first, dry run first, no real destructive calls). Both CLAUDE.md files apply.
2. `tasks/UI-handoff.md`: §1 rules, §2c (Blender render, `HullRender`), §4 (light canvas), §5 and §11 (measurements, budgets).
3. `tasks/hyperrealism-plan.md`: Global Constraints and §D (measurement rows).

Hard rules: do not touch JARVIS (`Skins/Spaceship/@Resources/Jarvis/**`, `Docs/Jarvis-*`, `tasks/jarvis-*`, `tasks/phase10-slice2-todo.md`, `.gitignore`);
`GodMode/` and `Refrences-Art/` stay untracked; never `git add .`; no push, no deploy; Rainmeter's own images do not change;
the `HullRender` default stays 0 until the user says so. Ask before: a live GPU run while the GPU is busy (check `nvidia-smi` first),
anything that kills or restarts the user's real HUD or Rainmeter, colour changes, removing effects.

## 1. State to test
- `main`: light canvas (bloom), lens (glass + grain), depth haze, screen bezels, music motion, orb light, boot settle.
- `feature/hull-render` (3 commits + docs): the `HullRender` setting, Blender-rendered hull and light passes.
- `feature/hull-curve` (stacked on it): barrel-bowed windscreen edges and `Canvas` zone-bend support (`curve.json` `zones` is empty).
- `chore/ui-cleanup` (stacked on it, 6 commits, handoff §16): the UI clean-up. Changes to verify: a latent-flake fix in `e2e/bloom.spec.ts`; tests for the `HullRender=0` no-bend gate; 12 shorter setting hints; `ColorDim` 0,110,150 -> 0,140,185 (also in `Settings.inc`, so the Rainmeter skin's dim changes); the hull re-rendered without the brick-grid seams (`hull.png`, `corners.png`).

Test the **tip of `chore/ui-cleanup`** (it contains everything) and compare against `main` for CPU. Make fixes on a new branch (`fix/live-test`) off that tip. Nothing is merged or pushed; merging into `main` waits for the user's OK after this test.
Known: `tools/contract_check.py` may show an uncommitted edit from another session; leave it, never stage it. `C:\Skins\` is a stray folder the user deletes by hand.

## 2. Automatic checks (the session runs these itself)
Run from `SpaceshipApp/SpaceshipUI` unless noted. Record exact commands and results (§6).

| # | Check | How | Pass |
|---|---|---|---|
| A1 | Types, unit, e2e, build | `npx tsc --noEmit -p .`, `npx vitest run`, `npx playwright test`, `npx vite build` | all green (last: 450 unit, 68 e2e) |
| A2 | Python | from the repo root: `py -3 -I tools/test_render_frame.py`, `tools/test_export_ui_assets.py`, `tools/test_lens_assets.py`, `tools/contract_check.py`, `tools/export_ui_assets.py --check` | all ok |
| A3 | Flaky tests | run `npx playwright test` 3 times; list any test that fails once | none flaky, or fixed to wait for state, not time (handoff §12 item 34) |
| A4 | Every tier x HullRender | PerfOverride 0-3 with `HullRender` 0 and 1 via the mock host; list `.frame [data-layer]` and count `g.bloom` | FULL = bloom + glass + grain (+ light passes if HullRender); LITE = grain + static art; LOW and STEALTH = none of the new layers |
| A5 | Rainmeter parity | `git diff main --stat -- "Skins/Spaceship/@Resources/Images/*.png"` shows nothing outside `Images/Render/`; `Settings.inc` and `registry.ts` agree on every key | no diff; contract test ok |
| A6 | Theme live | with `?preview=1`, change `ColorAccent` and the JARVIS colours; computed colours of `light_screens`, `light_orb`, glow and grain follow | they follow, no reload |
| A7 | Hide / unmount | `Off_` settings, the console OFF tab, pop-up close: that module's light disappears on the next frame | no lingering light |
| A8 | Resize / DPI / zoom | viewports 1280x800, 1707x1067 @1.5, 2560x1600 @1, 3840x2160 @1.5; crops of three glow spots (orb, a graph, the top console) | glow sits on its lines; no offset over 1 px |
| A9 | Text legibility | crops at 100 % and 150 % of the dimmest text on the darkest panel; no doubled text from the ghost; compute dim-text contrast from pixels | readable, contrast >= 4.5:1; list failures |
| A10 | Reduced motion | `prefers-reduced-motion` and `data-reduce-motion=1`: no shimmer, power-on, orb-light or lens fade animation | all stop |
| A11 | Boot sequence | `tools/visual-check/bootat.cjs` at 6 frames; lens and grain fade in last | no flash, no stale frame |
| A12 | Console and network | `?preview=1&module=all` for 60 s: read console messages and requests | no errors or warnings; every `Render/` image loads |
| A13 | Hit boxes | `e2e/hud.spec.ts` and the hit-region tests pass with `HullRender=1` (add the config if a spec has none) | unchanged |
| A14 | Render pass sanity | numpy on `Images/Render/*.png`: sizes, hull alpha vs `window_mask.png` IoU >= 0.985, light passes not clipped (share of 255 under 5 %) | ok |
| A15 | Visual pair | `tools/visual-check/proto.cjs` old vs `HullRender=1`, then `crop.cjs` on: orb + sphere, top console, a side panel, bottom strip, the windscreen edges; compare to `Refrences-Art/MAIN-REFRENCE-try_to_capture_curvness.jpg` and `images (5).jpg` with `pair.cjs` | list what differs; if a material or light is clearly off, fix it in `tools/blender/cockpit_scene.py` and re-render with `--only` |

### 2b. Checks for the UI clean-up (`chore/ui-cleanup`)
| # | Check | How | Pass |
|---|---|---|---|
| C1 | Dim colour agrees everywhere | grep `ColorDim` default in `Settings.inc`, `src/lib/theme.ts`, `src/settings/registry.ts`, `src/tokens.css`, `contract/config-keys.json`; `UPDATE_CONTRACT` must not be needed | all `0,140,185`; contract test ok |
| C2 | Dim-text contrast from pixels | crops (`tools/visual-check/crop.cjs`) of the dimmest labels on the darkest panels at 100 % and 150 %; contrast of text pixels vs the panel behind; token maths gave 5.2:1 on panel-over-black, 4.6:1 on the hull, 4.3:1 on a lighter backdrop | >= 4.5:1 on the darkest panels; list any lighter-backdrop miss (needs user) |
| C3 | Dim lines not too bright | `?preview=1&module=all` crops of inactive lines, grids and graph baselines, before (`main`) vs after | still clearly dimmer than the accent; no line competes with live data; else needs user |
| C4 | Theme paths still consistent | change `ColorDim` live through the mock host (A6 method); apply the CYAN preset in the Control Center | the dim follows; note that the CYAN preset (`control.lua`) still carries `0,110,150` (decide with the user) |
| C5 | Hints | extract the 3rd field of every row in `registry.ts`; longest hint; open the tooltip for the 12 changed ones (`WallpaperOn`, `ReduceMotion`, `BloomEngine`, `LensFx`, `WallpaperQuality`, `ScreenBezel`, `DepthHaze`, `PowerSaver`, `WallpaperFit`, `WallpaperPauseMax`, `StateLight`, `HullRender`) | none over 68 characters; each fits in at most 2 tooltip lines at 280 px, and no meaning was lost |
| C6 | Hull without seams | numpy on `Images/Render/hull.png` and `corners.png`: size 2560x1600, alpha IoU vs `window_mask.png` (A14), mean RGB about 24.8 (was 24.3), no clipping; crop of a hull strut | no visible grid line; silhouette unchanged |
| C7 | `HullRender=0` never bends | `npx vitest run tests/curve.test.ts` (8 tests); with `HullRender=0` the frame shows no `render_*` or `light_*` layer | pass |
| C8 | Flake check | `npx playwright test` three times, then `npx playwright test e2e/bloom.spec.ts` three times | all 68/68 and 18/18; any failure of "idle light is not re-blurred" is a regression of `fb9eeda` |
| C9 | Rainmeter skin still loads | reload the skin (user's Rainmeter; ask first, do not restart it yourself) or parse `Settings.inc` with `tools/contract_check.py`; `Images/*.png` diff vs `main` (A5) | loads; only `Images/Render/` changed |
| C10 | Console and network with the new render | A12 with `HullRender=1`, 60 s | 0 warnings; the new hashed `render_hull` and `render_corners` load |

## 3. Measurements (the session does them; the user need not)
- **Headless CPU, interleaved A/B, 3 rounds, medians:** `main` vs the tip, idle and `?audio=demo` music, `HullRender` 0 and 1.
  Method: two dev servers on their own ports (`npx vite --port 5197 --strictPort`). For `main`, use a temporary `git worktree` in the scratchpad with a
  junction to `node_modules`, run `py -3 -I tools/export_ui_assets.py` there, and remove the junction with `cmd /c rmdir` before removing the worktree.
  Hold the page like `tools/visual-check/hold.cjs`, then `cpu.ps1 15`. Budget: within +10 % of `main`.
  Last result (2026-11-03): idle -3 %, music +2 % to +7 %, machine noise about +-10 points.
- **Live GPU and VRAM** (`powershell -File tools\gpu_baseline.ps1 -Seconds 30 -Label "..."`, read-only): FULL idle, FULL + music, LITE idle, with `HullRender` 0 and 1.
  Budget: no sustained rise over +5 points, no spikes on update. Check `nvidia-smi` first; if the GPU is busy, say so and ask. Add rows to `tasks/hyperrealism-plan.md` §D.
- **Memory:** browser RSS idle vs after 10 minutes (look for growth in the light-canvas tile cache or after tier changes).
- **Redraw cost:** `performance.now()` around the light-canvas redraw, and `getScreenCTM` reads per second (handoff §2b: under 10 per 3 s idle).
- **Size and load:** size of `src/generated/frame/` (the render PNGs add about 7 MB) and the preview's cold-load time.

## 4. What the session may fix on its own (small, reversible, one commit each)
Flaky tests; text-contrast failures; a misregistered glow; a stale layer after a tier change; a render material or light that is clearly wrong
(too bright, clipped); hint strings over one line; console warnings.
Not on its own: moving features, new dependencies, changing the `HullRender` default, colour rebrands, bending HUD zones (`curve.json` `zones`), anything JARVIS.

## 5. What only the user can judge (collect into one short list, with crops)
1. The real wallpaper under the live WebView2 HUD (not the headless preview): lens strength, grain visibility, glow registration on every monitor and DPI.
2. `HullRender=1` vs `0` side by side. If they approve, flip the default: Settings.inc + registry.ts, `npm run gen`, `UPDATE_CONTRACT=1 npx vitest run tests/contract.test.ts`.
3. Which edges should curve and which HUD lines should follow (open decision, handoff §2c).
4. Music ball motion (frames from `tools/visual-check/burst.cjs`).
5. WebView2 occlusion after a fullscreen game or sleep/resume: does the light canvas redraw? Say exactly what to do, then read the result from the console or a screenshot.
6. LITE on battery (`BatteryMinTier`).
7. The new dim blue (`0,140,185`) on the real wallpaper in the HUD and in the Rainmeter skin: readable but not too bright? If not, a middle value is `0,125,170`; change it in the same five places as C1, then `npm run gen` and `UPDATE_CONTRACT=1 npx vitest run tests/contract.test.ts`.
8. The hull without seams (`HullRender=1`): does the plain gunmetal look right, or should panel lines follow the layout?
9. The open clean-up questions (handoff §16): the doubtful `st.warn` uses, and pop-ups / Control Center glow.

## 6. Report format
Append a dated section to `tasks/UI-handoff.md` and give a short chat summary. For each check: ID, command or method, observed result, verdict
(pass / fixed / needs user / failed). Separate confirmed findings from unverified guesses (CLAUDE.md §7). List failed, skipped and unverified checks,
modified files, the commits (with `git revert <sha>`), and the open questions for the user.
