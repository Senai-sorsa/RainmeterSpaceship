import sys,time,json,os
sys.path.insert(0,r"C:\Users\Senai\RainmeterSpaceship\Skins\Spaceship\@Resources\Jarvis")
import numpy as np
from jarvislib import tts, say
T=[ "Good morning, sir. The time is 1:48 AM.",
 "You have three meetings today, and the first is at nine.",
 "Disk usage is at 91 percent, so I would clear something soon.",
 "Certainly.",
 "Opening Spotify.",
 "It is quite late, sir, and you have an early class tomorrow, so I would suggest getting some rest.",
 "The loop has no valid exit condition, or the condition is never met.",
 "Timer set for 10 minutes.",
 "Light from the Sun takes about eight minutes and twenty seconds to reach us.",
 "I can't reach your phone from here. I can set that on this PC, though."]
def sil(a,sr,thr=0.01):
    m=np.abs(a)>thr
    if not m.any(): return len(a)/sr,0
    i=np.argmax(m); j=len(a)-np.argmax(m[::-1])
    return i/sr,(len(a)-j)/sr
tts.synth_audio("warm up.")
rows=[]
for t in T:
    t0=time.time(); a,sr=tts.synth_audio(say.speakable(t)); st=time.time()-t0
    lead,trail=sil(a,sr); dur=len(a)/sr
    rms=float(np.sqrt(np.mean(a**2))); pk=float(np.abs(a).max())
    rows.append((t[:40],round(st,2),round(dur,2),round(st/dur,2),round(lead,3),round(trail,3),round(rms,3),round(pk,2),sr))
    print(rows[-1])
# fragment test
print("--- first-5-word fragment vs whole sentence")
for t in T[:2]+T[5:6]+T[8:9]:
    w=t.split(); frag=" ".join(w[:5]); rest=" ".join(w[5:])
    a,sr=tts.synth_audio(say.speakable(t)); f,_=tts.synth_audio(say.speakable(frag)); r,_=tts.synth_audio(say.speakable(rest))
    fl,ft=sil(f,sr); rl,rt=sil(r,sr); wl,wt=sil(a,sr)
    print(f"{t[:34]!r}: whole {len(a)/sr:.2f}s | frag {len(f)/sr:.2f}s (trail sil {ft:.2f}) + rest {len(r)/sr:.2f}s (lead {rl:.2f}) = {(len(f)+len(r))/sr:.2f}s ; seam silence {ft+rl:.2f}s (+ stream open)")
