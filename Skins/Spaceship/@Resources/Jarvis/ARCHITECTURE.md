# JARVIS architecture (as of the 2026-11-03 refactor, phases 0-7)

This describes what the code IS now, not a target. Plan and history: `tasks/jarvis-refactor-plan-2026-11-03.md`,
`tasks/HANDOFF-jarvis-semi-live.md` (section 6 log).

## One turn (`jarvis.py`)
```
exchange(tier, follow, woke, mode, left, typed)         owns busy lock, cancel, watchdog, the one `route:` log line (finally)
  _hear(...)          input: preflight, click/typed text, listen, transcribe, quiet-end checks      -> text, model, ... | None
  _gate(...)          was it for him? late-in-the-ear, undo-only, directed()/room talk              -> True | None
  (middle, still inline)  courtesies, confirmations, understand() -> route kind, commands, fixed replies, HUD blocks, prompt
  reply_chain(...)    jarvislib/reply/policy.py: sentences_from > no_claims > no_hope > grounded > polish   (lazy: first piece out early)
  speak_all(...)      jarvislib/voice/speaker.py: synth ahead of playback, pacing, pop-up text, text guard
  _record_chat(...)   history, memory (facts, promises), offers, model unload bookkeeping
```
The middle is NOT split: it shares `quiet`, `text`, `way` and the `fixed()` closure with the code around it (see log k).

## Where things live (`jarvislib/`)
| Concern | Module |
|---|---|
| Settings keys + code defaults | `config.py` (checked by `tests/test_settings_schema.py`); read with `setting(key, default)` from `base.py` |
| Fixed lines he says from code | `reply/fixed.py` (one registry; `FIXED_LINES` is derived; `jarvis.py` uses `FX.<NAME>`) |
| Reply filters + their order | `reply/policy.py` `reply_chain`; the filters are in `routing.py` (claims), `mood.py` (hope, grounded, polish) |
| What a phrase means | `routing.py`: `route()` -> `_route_rest()` -> `RULES` (15 ordered areas, `tests/test_rule_order.py`); `understand()` in `jarvis.py` adds follow-ups and the AI reread |
| Actions he can run | `routing.py` `ACTION_TABLE` (risk: change / ask), handlers in `actions.py`; checked by `tests/test_action_table.py` |
| Voice | `voice/` chunker, pacing, player, synth, output, fillers, speaker; old names still import from `speech.py`, `tts.py`, `player.py` |
| Conversation memory (module-level) | `turnstate.py` (undo, recent, offer, last, did); one reset: `session.reset_turn_state()` |

## Where do I add...
| A new... | Do this | Then run |
|---|---|---|
| voice command | add the rule inside the right area function in `routing.py` (an earlier area wins!), an `ACTION_TABLE` row + `DID` text if it acts | golden routes `--check`, then regenerate on purpose |
| fixed line | `reply/fixed.py` `register(...)` (`passthrough=True` if `polish` must leave it alone), use `FX.NAME` | `tests/test_fixed_lines.py` |
| reply filter | a stage in `mood.py`/`routing.py` + one name in `reply/policy.py` (order matters, keep the first piece lazy) | `tests/test_reply_policy.py`, golden replies |
| setting | one entry in `config.py`, then the read with the same default | `tests/test_settings_schema.py` |
| TTS behaviour | `voice/synth.py` (engine), `voice/pacing.py` (pauses), `voice/chunker.py` (cuts) | `tools/voice_gaps.py --no-synth`, silent device smoke |

## Gates (all on a scratch copy, `TZ=ABC+12`, never the live folder)
1. `python -B test_jarvis.py` with the venv python AND `py -3`; `python -B test_host_pipe.py`; `python -B tests/run_all.py`.
2. `python -B tools/golden_routes.py --check` and `tools/golden_replies.py --check` (0 diffs).
3. Semi-live `tools/semi_live.py --model ... --cases ... --seed 7`, scored by `tools/score_semi_live.py`; run noise is about +-5 per bank,
   so compare against a run of the previous code in the same hour. Decisions (route + actions) should be identical: compare them, not just cost.
4. Before running anything new: `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` (fakes first, dry-run grep, no real destructive calls).

## Known traps
`jarvislib.base.RES` is read from `sys.argv[1]` at import: clear/replace `sys.argv` before importing or you write the real `Data\jarvis.log`.
Tests fake by name across ALL modules (`Everywhere`): a moved function must keep its name bound in every module that used it.
Do not retype regexes: they hold `\b`; edit with a tool that does not eat backslashes and grep the file for 0x08.
