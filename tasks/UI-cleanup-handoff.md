# UI clean-up handoff (written 2026-11-03): get the UI ready for the Live Test

Goal: one session tidies the UI so that the Live Test (`tasks/LIVE-TEST.md`, run by a different session) finds as little as possible.
Small, reversible commits. No new features, no big visual changes.

## 0. Read first, in this order
1. `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md`, then both CLAUDE.md files.
2. `tasks/UI-handoff.md`: §1 rules, §2c (Blender render and curve), §12 (the improvement list), §13 (audits).
3. `tasks/LIVE-TEST.md` (what will be checked, so you can pre-empt it).

## 1. Branches (current state)
- `main`: all light-canvas / lens work.
- `feature/hull-render` (3 commits + docs `ec3593b`): `HullRender` setting and the Blender passes.
- `feature/hull-curve` (`8ddeab6`, stacked): bowed windscreen edges, `Canvas` bend support.
Neither feature branch is merged or pushed. Step 1 is to decide the order with the user's OK: merge `feature/hull-curve` into `main` (it contains the
others) only after the gates are green and the user agrees. Until then, do the clean-up on a new branch off `feature/hull-curve` (`chore/ui-cleanup`).

## 2. Hard rules
- Do not touch JARVIS: `Skins/Spaceship/@Resources/Jarvis/**`, `Docs/Jarvis-*`, `tasks/jarvis-*`, `tasks/phase10-slice2-todo.md`, `.gitignore`. Another session has uncommitted work
  there (`tasks/HANDOFF-jarvis-semi-live.md` and Jarvis files show as modified): never stage, stash or check out over it. `GodMode/` and `Refrences-Art/` stay untracked.
- Keep the base frame and the layout; do not move features. Rainmeter's own images (`Images/*.png`) do not change; render art lives in `Images/Render/`.
- `HullRender` stays default 0. No new npm or pip dependencies. No push, no deploy. One commit per slice, explicit paths (never `git add .`);
  `tools/frame_src/` is gitignored, so a new file there needs `git add -f <file>` (do not edit `.gitignore`).
- Commit trailer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Commit messages carry goal, scope, non-goals, acceptance, validation, risks, rollback.
- TDD where it makes sense; use few tokens (crops and contact sheets, not full frames; `tools/visual-check/README.md`).
- Gates after every slice (from `SpaceshipApp/SpaceshipUI`): `npx tsc --noEmit -p .`, `npx vitest run`, `npx playwright test`, `npx vite build`;
  from the root: `py -3 -I tools/test_render_frame.py`, `tools/test_export_ui_assets.py`, `tools/contract_check.py`. After a settings change: `npm run gen`, then `UPDATE_CONTRACT=1 npx vitest run tests/contract.test.ts`.
- CPU budget: headless within +10 % of `main` (last: idle about 128 to 150, music about 147 to 167 depending on machine noise); measure only if a slice touches drawing.

## 3. The clean-up list (cheapest first; ask the user before items marked ASK)
1. **Flaky e2e tests** (handoff §2 and §12 item 34): run `npx playwright test` three times, list the flakes, make them wait for state, not time.
2. **Dead or untested paths:** the `Canvas` bend (`src/draw/curve.ts`) has an empty `zones` table; keep it, but make sure `tests/curve.test.ts` covers rect, line, text and the no-op case (it does) and that `HullRender=0` never bends. Look for unused exports and leftovers from R1-R12 and H1-H4 (`tsc --noUnusedLocals` as a read-only probe; fix only the real ones).
3. **Hint strings:** audit every hint (<= 1 line, keep most, condense). `impeccable` critique/polish may help (user ruling: keep and condense).
4. **Contrast and legibility:** dim text on the darkest panels at 100 % and 150 % scale (compute from pixels; fix with token changes, not per-element hacks).
5. **The five doubtful `st.warn` uses** (handoff §6): list them with crops; do not change colours without approval (ASK).
6. **K7 fringe copies on text:** keep or drop now that the light canvas exists (ASK).
7. **Pop-ups** (log, drawer, boot check, Control Center): same bezel and screen language as the MFDs, no fringe or flicker on settings text; Control Center outer glow needs a wrapper (deferred in R9; ASK).
8. **Console and network hygiene:** `?preview=1&module=all` for 60 s with zero warnings; every `Render/` image loads.
9. **Render art polish (optional, ASK):** the hull's brick-grid seams are arbitrary; either drop them (`seams=False` in `tools/blender/cockpit_scene.py`) or align them to the layout, then re-render (`blender.exe -b --factory-startup -P tools/blender/cockpit_scene.py -- ... --only hull,corners`; the full command is in handoff §2c). The user OKed Blender; still dry-run the script first and check `nvidia-smi`.
10. **Line endings:** every commit warns that LF becomes CRLF. Harmless. A `.gitattributes` would silence it, but the JARVIS session edits `.gitignore`; coordinate, do not do it alone (ASK).
11. **Stray folder:** `C:\Skins\` (a first Blender draft wrote there; the script is fixed). The user must delete it; do not try (the safety check blocks it).
12. **Docs:** keep `tasks/UI-handoff.md` accurate (a new dated section, with rollback per commit); update the plan's §D only with measured rows.

## 4. Do not do (belongs to the Live Test or needs the user)
Live GPU runs, the real-wallpaper check, WebView2 occlusion, the `HullRender` default flip, which edges curve, music-ball motion approval.

## 5. Done means
Gates green with exact commands and results reported; a short list of what changed, what was skipped and why, what remains for the Live Test; commits listed with `git revert <sha>`.
