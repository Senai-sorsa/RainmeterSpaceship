import os, sys, time
JD = sys.argv[1]; sys.path.insert(0, os.path.join(JD, "tools")); sys.argv[1:] = []
import golden_common as G
with G.Box() as b:
    J = b.jarvis; j = b.j
    now = time.time()                       # frozen by the Box
    # case A: an old turn, nothing touched turn_id -> watchdog must cancel
    J.busy.acquire(); J.cancel.clear(); old = now - 181; J.turn_id[0] = old; J.turn_started[0] = old
    J.watchdog(old); print("A: stuck 181 s, turn_id unchanged -> cancel set:", J.cancel.is_set())
    # case B: same stuck turn, but an alarm ring set turn_id = now (jarvis.py:529) -> watchdog silently quits
    J.cancel.clear(); J.turn_id[0] = now; J.turn_started[0] = old
    J.watchdog(old); print("B: stuck 181 s, alarm refreshed turn_id -> cancel set:", J.cancel.is_set(), "(watchdog gave up without cancelling)")
    # case C: after the watchdog fired, is the lock freed? (it only sets the Event)
    print("C: busy still locked after a watchdog cancel:", J.busy.locked())
    # case D: a second turn while busy: what does the user get?
    said = []; j.reply_line = lambda t, q: said.append(t); b.logs.clear()
    J.exchange(0, 0, False, None, {}, typed="what time is it")
    print("D: second turn while busy -> said:", said, "| log lines:", b.logs)
    J.busy.release()
