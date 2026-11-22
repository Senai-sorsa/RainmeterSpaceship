import os, sys
JD = sys.argv[1]; sys.path.insert(0, os.path.join(JD, "tools")); sys.argv[1:] = []
import golden_common as G
with G.Box() as b:
    J = b.jarvis
    from jarvislib import mic, llm, hearing
    getters = {"follow_wait": ("JarvisFollowUpWait", mic.follow_wait), "follow_name_wait": ("JarvisFollowNameWindow", mic.follow_name_wait),
               "ctx_tokens": ("JarvisContext", llm.ctx_tokens), "keep_alive": ("JarvisKeepAlive", llm.keep_alive), "hud_tier": ("PerfTier", J.hud_tier)}
    bad = []
    for name, (key, fn) in getters.items():
        for v in ["", "abc", "-5", "0", "1e9", "nan", "inf", "-inf", "99999", "3,5", " 7 "]:
            b.set_setting(key, v)
            try:
                r = fn()
            except Exception as e:
                bad.append((name, key, v, type(e).__name__))
    print("getters that raise on odd setting values:", bad)
    # reminders / memory file problems
    from jarvislib import memory as MEM
    import builtins
    open(MEM.MEMORY_FILE, "wb").write(b"\xff\xfe\x00bad bytes \x80\x81\n")
    try:
        print("load_memory on invalid UTF-8 ->", MEM.load_memory())
    except Exception as e:
        print("load_memory on invalid UTF-8 raises", type(e).__name__, "(callers catch OSError/ValueError):", isinstance(e, (OSError, ValueError)))
    os.remove(MEM.MEMORY_FILE)
    print("tripwires:", len(G.SL.TRIPS))
