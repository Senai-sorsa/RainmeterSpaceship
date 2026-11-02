# CSpace visual overhaul (started 2026-11-02, branch `feature/visual-overhaul`)

## The user's direction (note, 2026-11-02)

> Please don't move features around too much: I like the base frame we have right now. What I don't like are the
> designs of the smaller features, ALL of the pop-ups, and a lot more of the frame and everything else. They could
> look so much smoother and more realistic, while they look rough right now.

So: **same layout, same zones, same clicks.** Refine in place. Saved choices stay (the windscreen is clear because
`Off_CenterTarget=1` and `Off_CenterHUD=1` in State.inc).

References: `Refrences-Art/` (MAIN-REFRENCE = the curvature and the glass-panel cockpit; the chamfered panel set;
the callout/leader-line style of the "HUD Interface" packs).

## Design rules used (from the references and FUI practice)
1. One hero value per cluster: big and bright. Labels are small, single-line and dim.
2. Hairlines carry the structure; glow is for what is lit or active, and it falls off softly (bloom), never as a hard band.
3. Panels are lit glass: a faint plate, a brighter band at the lit edge, doubled rules, corner marks, step ticks.
4. Callouts: name, rule and a leader line ending in a dot.
5. Colour: cyan structure, white for live values, warn/alert colours only for state.
6. Type: Rajdhani for words (weights carry the hierarchy), B612 Mono for numbers.

## Done
| Commit | What |
|---|---|
| 763b5bb | Bloom on the glow layer (FULL tier), Rajdhani body text with weight hierarchy, dev-server fonts |
| 968eac5 | Top telemetry cells: label, large readout and unit, history on a grid |
| 18f8748 | App and category rows on lit glass plates |
| f50307e | Assistant name and state as a callout tied to the orb |
| f05db11 | Control Center: lit glass, one type scale, chamfered quiet controls (new `src/ui/finish.css`) |
| 437a48e, b20b88f | JARVIS log and CARGO drawer share one lit-glass pop-up frame (`src/draw/popup.ts`) |
| ec3326c | Wizard, notices and kit panels |
| 04e1ae4 | Mission clock and network block plates; times and addresses in the text face |
| ae7ba81 | Frame lighting finish: glass sheen, console bounce, hull vignette |
| a010419 | Category tabs on a lit plate; page dots as segment pips |
| c24fbfb, 9bf88fa | Hover captions as glass tags; System tab column |
| 86f0a46 | New boot sequence (ignition ring, lock-on, flicker build-on; scan line removed) |
| ab6a873 | Frame neon tubes: soft falloff and white-hot glints |
| 7a262e2 | Audio ring: real visualizer DSP (Hann, dB, 24 bands, 20 fps feed, attack/release) |

Preview switches for screenshot checks (plain browser only): `?preview=1&module=all`, `?jarvislog=demo`,
`?drawer=1|<folder>`, `?bootat=<frame>`, `?audio=demo`, `?jarvis=<state>`, `?panel=control`.

## Next
1. Second comparison round against `Refrences-Art/` and online FUI work (glints and micro-detail on focal elements,
   one sparing warm accent).
2. Hover hints: condense, remove only the obvious ones (user's answer 2026-11-02).
3. Live check in WebView2 (not done: everything is verified in headless Chromium only).

## Measuring
Headless Chromium CPU, 15 s of the full HUD: 111-113% with bloom vs 114-118% without (no measurable cost; headless
renders in software, so WebView2 on the GPU is lower). Re-measure after each larger slice.
After the round (2026-11-02): 115-117% all on vs 119-125% with bloom off (no added cost).

## Rollback
Each slice is one commit on `feature/visual-overhaul`; `git revert <sha>` undoes one. The branch was cut from
`feature/standalone-host` at 84d4c44.
