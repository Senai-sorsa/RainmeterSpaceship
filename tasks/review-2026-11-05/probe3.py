import os, sys
JD = sys.argv[1]; sys.path.insert(0, os.path.join(JD, "tools")); sys.argv[1:] = []
import golden_common as G
with G.Box() as b:
    J = b.jarvis
    for t in ["travis set the volume to ten", "set a timer for 5 minutes jarvis", "volume to 30 please jarvis", "jarvis volume 30", "hey travis, mute", "set a timer for five minutes please",
              "play the next song please", "stop", "stop the timer", "stop the alarm", "pause it", "resume the music", "cancel", "cancel that timer", "cancel it",
              "turn it off", "turn it up", "louder", "quieter", "mute it", "what is the time", "what time is it in tokyo", "set a timer for 0 minutes", "set a timer for 5 hours",
              "set a timer for 100 hours", "wake me at 25:00", "set an alarm for 7:75", "volume minus 5", "set the volume to negative ten", "set volume to 3.5",
              "set the volume to 0", "remind me in 0 minutes", "remind me yesterday at 5", "set an alarm for 7 am tomorrow and cancel it",
              "set a timer for 5 minutes then undo", "lock", "shutdown", "restart", "sleep", "mute and lock the computer", "set the volume to 20 and lock the pc"]:
        b.reset()
        d = J.understand(t, "none", True, "")
        print(f"{t!r:52} -> {d.kind}.{d.action} target={str(d.target)[:40]} prompt={str(d.prompt)[:50]!r} via={d.via} reread={'interpret' in b.model_calls}")
        del b.model_calls[:]
