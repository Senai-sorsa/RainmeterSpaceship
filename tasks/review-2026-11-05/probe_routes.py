"""Route probe (review 2026-11-05). Run with TZ=ABC+12 from the mirror's Jarvis folder:  python -B <this> <mirror-jarvis-dir>
Uses tools/golden_common.Box (temp RES, tripwires, no model, frozen clock). Prints misses (route != expectation).
Expectation = "kind" or "kind.action" prefix of route(); "chat" means must stay chat (false-positive check)."""
import json
import os
import sys

JD = sys.argv[1]
sys.path.insert(0, os.path.join(JD, "tools"))
sys.argv[1:] = []
import golden_common as G                                     # noqa: E402

CASES = [
    # --- volume
    ("set the volume to 30", "act.volume"), ("volume 30", "act.volume"), ("volume to thirty percent", "act.volume"),
    ("make it louder", "act.volume"), ("turn it down a bit", "act.volume"), ("a little quieter please", "act.volume"),
    ("jarvis could you possibly set the volume to forty", "act.volume"), ("um set the volume to uh twenty", "act.volume"),
    ("set the value to 40", "act.volume"), ("set the volume to for ty", "act.volume"), ("set the volume to 150", "say"),
    ("max volume", "act.volume"), ("half volume", "act.volume"), ("volume up", "act.volume"), ("raise the volume by 20", "act.volume"),
    ("it's too loud", "act.volume"), ("it is too quiet", "act.volume"), ("too loud", "act.volume"), ("I can't hear you", "act.volume"),
    ("turn the volume all the way down", "act.volume"), ("set volume at fifty", "act.volume"), ("volume fifty five percent", "act.volume"),
    ("set the volume to 30 no 40", "act.volume"), ("set the volume to 30, I mean 40", "act.volume"),
    ("what is the volume", "level"), ("how loud is it", "level"), ("is it muted", "level"),
    ("what is a volume knob", "chat"), ("how do I increase the volume on my iPhone", "chat"), ("the volume of a sphere", "chat"),
    ("don't change the volume", "chat"), ("do not turn the volume down", "chat"), ("why is the volume so low", "chat"),
    ("can you turn the volume up", "act.volume"), ("could you lower the volume", "act.volume"), ("would you mute", "act.mute"),
    # --- mute
    ("mute", "act.mute"), ("unmute", "act.unmute"), ("mute the sound", "act.mute"), ("mute yourself", "act.mute"),
    ("shut up", "act"), ("be quiet", "act"), ("silence", "act"), ("stop talking", "act"),
    ("mute the mic", "act.mic_mute"), ("unmute my microphone", "act.mic_unmute"),
    # --- brightness
    ("set brightness to 50", "act.brightness"), ("dim the screen", "act.brightness"), ("brightness down a bit", "act.brightness"),
    ("make the screen brighter", "act.brightness"), ("turn up the brightness", "act.brightness"), ("brightness 200", "say"),
    ("it's too bright", "act.brightness"), ("it's too dark in here", "chat"), ("what is brightness", "chat"),
    # --- mic level / device
    ("set the mic to 70", "act.mic_level"), ("turn up the microphone", "act.mic_level"), ("which microphone are you using", "say"),
    ("use the headset microphone", "act.micdev"),
    # --- timers / alarms / reminders
    ("set a timer for 5 minutes", "remind.set"), ("timer 10 minutes", "remind.set"), ("a five minute timer", "remind.set"),
    ("I need a ten minute timer", "remind.set"), ("set a timer for half an hour", "remind.set"), ("set a timer for an hour and a half", "remind.set"),
    ("set a timer for ninety seconds", "remind.set"), ("start a timer", "remind"), ("set an alarm for 7", "remind.set"),
    ("wake me up at 6:30", "remind.set"), ("set an alarm for 7 am", "remind.set"), ("alarm for quarter past seven", "remind.set"),
    ("set an alarm for noon", "remind.set"), ("set an alarm for midnight", "remind.set"), ("remind me to call mom at 5", "remind.set"),
    ("remind me in ten minutes to stretch", "remind.set"), ("remind me tomorrow at nine to pay rent", "remind.set"),
    ("cancel the timer", "remind.cancel"), ("cancel all timers", "remind.cancel"), ("stop the alarm", "remind"), ("snooze", "remind.snooze"),
    ("snooze for ten minutes", "remind.snooze"), ("what timers do I have", "remind.list"), ("how much time is left", "remind"),
    ("how long is left on the timer", "remind"), ("list my reminders", "remind.list"), ("delete my alarm", "remind"),
    ("make it 20 minutes", "remind"), ("make that 20 minutes", "remind"), ("change the timer to 15 minutes", "remind"),
    ("set a timer for five minutes and remind me to stretch", "multi"), ("set an alarm for 7 and a timer for 5 minutes", "multi"),
    ("timer for five", "remind"), ("set a time her for five minutes", "remind.set"), ("set a tie mer for 5 min", "remind"),
    ("what is a timer", "chat"), ("how long should I boil an egg", "chat"), ("do I need a timer for this", "chat"),
    ("I set a timer yesterday", "chat"), ("the alarm didn't go off", "chat"), ("don't set a timer", "chat"),
    ("should I set an alarm for tomorrow", "chat"),
    # --- memory
    ("remember that my sister is Ana", "memory"), ("remember my locker code is 1234", "memory"), ("what do you remember", "memory.list"),
    ("what do you know about me", "memory.about"), ("forget that", "chat"), ("forget my sister", "memory"), ("forget everything", "act.forget_all"),
    ("do you remember that film", "chat"), ("remember to buy milk", "remind"), ("I remember when we met", "chat"),
    ("don't forget that I like tea", "memory"), ("my dog is called Rex, remember that", "memory"),
    # --- apps / media / power
    ("open chrome", "act.open"), ("launch spotify", "act.open"), ("pull up discord", "act.open"), ("can you open the calculator", "act.open"),
    ("open google chrome please", "act.open"), ("start code", "act.open"), ("close chrome", "say"), ("quit notepad", "say"),
    ("open the pod bay doors", "chat"), ("open my mind", "chat"), ("run a speed test", "chat"),
    ("pause", "act.media"), ("pause the music", "act.media"), ("play", "act.media"), ("resume", "act.media"), ("stop the music", "act.media"),
    ("next song", "act.media"), ("skip", "act.media"), ("previous track", "act.media"), ("skip this song", "act.media"),
    ("play some jazz", "chat"), ("play Despacito", "chat"), ("what song is this", "chat"),
    ("lock the computer", "act.lock"), ("lock my pc", "act.lock"), ("lock it", "act.lock"), ("go to sleep", "act.sleep"), ("sleep mode", "act.sleep"),
    ("restart the pc", "act.restart"), ("reboot", "act.restart"), ("shut down", "act.shutdown"), ("shut down the computer", "act.shutdown"),
    ("turn off the pc", "act.shutdown"), ("power off", "act.shutdown"), ("hibernate", "say"), ("sign me out", "say"),
    ("should I restart my computer", "chat"), ("how do I shut down windows 11", "chat"), ("my computer went to sleep", "chat"),
    ("don't shut down", "chat"), ("do not lock the computer", "chat"), ("what happens if I shut down", "chat"),
    ("empty the recycle bin", "act.recycle"), ("take a screenshot", "act.screenshot"), ("show the desktop", "act.desktop"),
    ("switch to dark mode", "act.theme"), ("turn on dark mode", "act.theme"), ("light mode", "act.theme"),
    # --- bluetooth / wifi / settings
    ("turn on bluetooth", "act.bluetooth"), ("turn bluetooth off", "act.bluetooth_off"), ("connect my headphones", "act"),
    ("connect to the JBL", "act"), ("disconnect wh-1000xm4", "act"), ("which bluetooth devices are connected", "say"), ("pair a new device", "act.page"),
    ("turn off wi-fi", "say"), ("turn on the wifi", "say"), ("open wifi settings", "act.page"), ("open sound settings", "act.page"),
    ("open display settings", "act.page"), ("are there windows updates", "act.page"), ("turn on night light", "act.page"),
    ("what's the wifi password", "chat"), ("is my wifi slow", "diag"),
    # --- notes / calendar / todo / diag
    ("search my notes for taxes", "notes"), ("what's in my notes about the trip", "notes"), ("add buy milk to my to-do list", "act.todo"),
    ("what's on my calendar", "chat"), ("add a meeting to my calendar", "say"), ("schedule a meeting tomorrow at 3", "chat"),
    ("good morning", "brief"), ("brief me", "brief"), ("what's my day look like", "brief"),
    ("why is my pc slow", "diag"), ("why is my computer so hot", "diag"), ("what's using my cpu", "diag"), ("how's my battery", "diag"),
    ("is my gpu hot", "diag"), ("how much ram am I using", "diag"), ("what time is it", "fact"), ("what's the date", "fact"),
    ("what's 15 percent of 80", "fact"), ("what is twelve times nine", "fact"),
    # --- control
    ("undo", "undo"), ("undo that", "undo"), ("put it back", "undo"), ("never mind", "end"), ("cancel that", "undo"),
    ("what did you hear", "heard"), ("what did I just say", "heard"), ("say that again", "again"), ("repeat that", "again"),
    ("what did you just do", "chat"), ("what did you do", "chat"),
    ("be serious", "act.mood"), ("stop joking", "act.mood"), ("be brief for ten minutes", "say"),
    # --- other device / can't do
    ("set my alarm on my phone", "say"), ("turn off the tv", "say"), ("send an email to John", "chat"), ("order a pizza", "chat"),
    # --- chat that must stay chat
    ("hello", "chat"), ("how are you", "chat"), ("tell me a joke", "chat"), ("what's the capital of France", "chat"),
    ("thanks", "chat"), ("who made you", "chat"), ("explain how a timer circuit works", "chat"), ("is it loud in space", "chat"),
    ("I like the new volume of the book", "chat"), ("what's the best way to open a jar", "chat"),
    ("close the door", "chat"), ("close the deal with the client", "chat"), ("open a new chapter in life", "chat"), ("start the day", "chat"),
    ("turn the lights off", "say"), ("turn on the lights", "say"), ("dim the lights", "say"),
    ("tell me about the Shackleton expedition", "chat"), ("what is a hackathon", "chat"), ("how do I delete all my emails in gmail", "chat"),
    ("what is a destroyer ship", "chat"), ("tell me about the brickell neighborhood", "chat"), ("how do I format my resume", "chat"),
    ("I want to blow up this balloon", "chat"), ("who is the hacker in mr robot", "chat"), ("explain what a nuke is", "chat"),
    ("mute the argument", "chat"), ("lock in", "chat"), ("sleep well", "chat"), ("I need some sleep", "chat"), ("I need to sleep", "chat"),
]


def main():
    miss, fp, n = [], [], 0
    reread_list = []
    with G.Box() as b:
        from jarvislib import routing as R
        for say, want in CASES:
            b.reset()
            n += 1
            try:
                before = len(b.model_calls)
                d = b.jarvis.understand(say, "none", True, "")
                r = (d.kind, d.action, d.target, d.prompt)
                reread = len(b.model_calls) > before
            except Exception as e:
                miss.append((say, want, "RAISES " + repr(e)[:100]))
                continue
            got = r[0] + ("." + r[1] if r[1] else "")
            if r[0] == "chat" and reread and want != "chat":
                reread_list.append((say, want))
                continue
            ok = got == want or got.startswith(want + ".") or (want == got.split(".")[0])
            if want == "say" and r[0] == "say":
                ok = True
            if not ok:
                (fp if want == "chat" else miss).append((say, want, got, (r[3] or "")[:70] if isinstance(r[3], str) else ""))
        print(f"cases: {n}  misses: {len(miss)}  false positives (should be chat): {len(fp)}  tripwires: {len(G.SL.TRIPS)}  model calls: {len(b.model_calls)}")
    print("--- WOULD ASK THE MODEL (AI reread; outcome unknown without a model):", len(reread_list))
    for m in reread_list:
        print(json.dumps(m, ensure_ascii=False))
    print("--- MISSES (expected route, got another)")
    for m in miss:
        print(json.dumps(m, ensure_ascii=False))
    print("--- FALSE POSITIVES (should have stayed chat)")
    for m in fp:
        print(json.dumps(m, ensure_ascii=False))


if __name__ == "__main__":
    main()
