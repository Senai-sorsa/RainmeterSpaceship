"""Mutation checks (review 2026-11-05). Works ONLY inside the scratch mirror (never the repo): for each mutant, restore the files
from the repo (read-only source), replace one exact snippet, run test_jarvis.py through tests/guarded_run.py with a timeout,
report caught / SURVIVED / timeout. usage: python -B mutate.py <mirror Jarvis dir> <repo Jarvis dir> [id ...]
Repo files use CRLF: multi-line snippets use \\r\\n."""
import os
import shutil
import subprocess
import sys
import time

MIR, REPO = sys.argv[1], sys.argv[2]
ONLY = set(sys.argv[3:])
PY = os.path.join(os.environ["LOCALAPPDATA"], "SpaceshipHUD", "venv", "Scripts", "python.exe")
J, R, F, M, C, H = "jarvis.py", "jarvislib/routing.py", "jarvislib/followup.py", "jarvislib/mood.py", "jarvislib/confirm.py", "jarvislib/hearing.py"
MEM, POL = "jarvislib/memory.py", "jarvislib/reply/policy.py"
MUT = [
    ("M01 lone yes", J, 'if turn.text != turn.room and is_yes(turn.text) and not asked_you(recent["me"]):', "if False:"),
    ("M02 late in ear, no name", J, "if follow and onset[0] > wait and strip_name(text) == text:", "if False:"),
    ("M03 undo window only undo", J, "if not followup.only_undo(decision[0], said, decision):", "if False:"),
    ("M04 whisper unsure: never act", J, "if changes and heard_score[0] < -1.0:", "if False:"),
    ("M05 typed ask not confirmed by mic", J, 'log("confirm: typed turn - not confirmed, ask out loud")\r\n        return False', "pass"),
    ("M06 own prompt echo ignored", J, 'if len(heard) >= 3 and heard <= set(re.findall(r"[a-z\']+", prompt.lower())):', "if False:"),
    ("M07 crisis line", J, 'if lane == "chat" and mood.crisis(turn.text):', "if False:"),
    ("M08 stopped while model read", J, "if cancel.is_set():                                    # stopped while the model read it: nothing runs", "if False:"),
    ("M09 offer channel check", J, 'offer.pop("typed", None) == typed_turn[0]', "True"),
    ("M10 directed no -> quiet", J, '    if heard_as == "no":  ', "    if False:  "),
    ("M11 level after volume only", J, "if did and did[-1][1] in VOLUME_DID and time.time() - did[-1][0] <= ACTIVE_TTL:", "if True:"),
    ("M12 50 facts cap", J, "if len(facts) >= 50:", "if False:"),
    ("M13 danger guard", R, "if DANGER.search(t):", "if False:"),
    ("M14 protected process", R, "if exe and (is_protected(exe) or is_own_model(exe)):", "if False:"),
    ("M15 volume > 100 guard", R, "if n is not None and n > 100:", "if False:"),
    ("M16 yes expires", C, 'return is_yes(answer) and now < pending["expires"]', "return is_yes(answer)"),
    ("M17 correction TTL", F, "time.time() - did[-1][0] <= CORRECTION_TTL and", "True and"),
    ("M18 mode_after undo", F, 'return "undo" if is_command(kind, action) else "ear"', 'return "ear"'),
    ("M19 UNDO_WAIT shorter", F, "UNDO_WAIT = 2.0", "UNDO_WAIT = 0.5"),
    ("M20 crisis setting gate", M, 'return on("JarvisSeriousTopics") and bool(CRISIS.search(text or ""))', "return False"),
    ("M21 phantom transcript", H, "if text and PHANTOM.fullmatch(text):", "if False:"),
    ("M22 weak thank-you after wake", J, "if polite and not (woke and heard_score[0] < -1.0):", "if polite:"),
    ("M23 unsure ask -> quiet", J, 'if heard_as == "ask" and setting("JarvisRoomAsk", "0") != "1":', "if False:"),
    ("M24 replace-fact prompt", MEM, "if fact in facts or not same:", "if True:"),
    ("M25 busy lock", J, "if not busy.acquire(blocking=False):", "if False:"),
    ("M26 spoken yes needs confident hearing", J, "and (typed_turn[0] or heard_score[0] >= -1.0))", "and True)"),
    ("M05b typed ask not confirmed by mic", J, 'log("confirm: typed turn - not confirmed, ask out loud")\r\n        return False', "pass"),
    ("M27 watchdog 3 min", J, "if time.time() - started > 180:", "if False:"),
    ("M28 never mind ends", J, 'if kind == "end":', "if False:"),
    ("M29 what did you hear", J, 'if kind == "heard":', "if False:"),
    ("M30 say that again", J, 'if kind == "again":', "if False:"),
    ("M31 no data fixed reply", J, "if empty:  ", "if False:  "),
    ("M32 diagnostics", J, 'if kind == "diag":', "if False:"),
    ("M33 act needs yes", J, "if ask_yes(prompt, turn.quiet):\r\n            ok = run_action(", "if True:\r\n            ok = run_action("),
    ("M34 claims filter", POL, "no_claims(sentences_from(stream, collected), collected)", "sentences_from(stream, collected)"),
    ("M35 grounded filter", POL, "mood.grounded(mood.no_hope(", "(mood.no_hope("),
    ("M36 diag close protected", J, "exe = None if exe and is_protected(exe) else exe", "exe = exe"),
    ("M37 new topic", J, "if m:                                                  # files the window", "if False:                                              # files the window"),
]


def run(tag, rel, old, new):
    p = os.path.join(MIR, rel)
    shutil.copy(os.path.join(REPO, rel), p)
    src = open(p, encoding="utf-8", newline="").read()
    n = src.count(old)
    if n != 1:
        return f"{tag}: SKIPPED snippet found {n}x"
    open(p, "w", encoding="utf-8", newline="").write(src.replace(old, new))
    t0 = time.time()
    try:
        r = subprocess.run([PY, "-B", "tests/guarded_run.py", "test_jarvis.py"], cwd=MIR, capture_output=True, text=True, timeout=420,
                           env=dict(os.environ, TZ="ABC+12"))
        last = (r.stdout + r.stderr).strip().splitlines()[-3:]
        ok = any(l.startswith("test_jarvis: OK") for l in last) and "tripwires hit: 0" in "\n".join(last)
        verdict = "SURVIVED (no test caught it)" if ok else "caught"
        tail = " | ".join(l.strip()[:70] for l in last[-2:])
    except subprocess.TimeoutExpired:
        verdict, tail = "timeout (loop/hang = caught in practice)", ""
    finally:
        shutil.copy(os.path.join(REPO, rel), p)
    return f"{tag}: {verdict}  [{time.time() - t0:.0f}s] {tail}"


for m in MUT:
    if ONLY and m[0].split()[0] not in ONLY:
        continue
    print(run(*m), flush=True)
print("MUT_DONE", flush=True)
