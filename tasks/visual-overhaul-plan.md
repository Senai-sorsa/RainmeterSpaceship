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

## Next (in order)
1. Pop-ups, all of them: Control Center, JARVIS log, CARGO drawer, wizard, help, about, notices, Settings button.
2. Small features: calendar block, network block, dials (volume, audio), bottom status strip, tabs, page dots, side panels.
3. Frame finish: smoother edges and lighting on the rendered cockpit (glass sheen, rim light, vignette), with no layout change.

## Measuring
Headless Chromium CPU, 15 s of the full HUD: 111-113% with bloom vs 114-118% without (no measurable cost; headless
renders in software, so WebView2 on the GPU is lower). Re-measure after each larger slice.

## Rollback
Each slice is one commit on `feature/visual-overhaul`; `git revert <sha>` undoes one. The branch was cut from
`feature/standalone-host` at 84d4c44.
