import sys,time,wave
sys.path.insert(0,r"C:\Users\Senai\RainmeterSpaceship\Skins\Spaceship\@Resources\Jarvis")
import numpy as np, sounddevice as sd
from jarvislib import tts, say
for i,h in enumerate(sd.query_hostapis()): print(i,h['name'],'default out',h['default_output_device'])
out=sd.query_devices(kind="output"); print("default:",out['name'],sd.query_hostapis(out['hostapi'])['name'],"low/high latency",out['default_low_output_latency'],out['default_high_output_latency'])
# open cost per host api / latency setting
sr=24000; z=np.zeros(int(sr*0.04),dtype=np.float32)
def trial(name,**kw):
    try:
        ts=[]
        for _ in range(5):
            t0=time.time(); o=sd.OutputStream(samplerate=sr,channels=1,dtype="float32",**kw); o.start(); o.write(z); t1=time.time(); lat=o.latency; o.stop(); o.close(); ts.append((t1-t0)*1000)
        print(f"{name:34s} open+first write median {np.median(ts):6.1f} ms  latency {lat:.3f}s")
    except Exception as e: print(name,"fail",str(e)[:80])
trial("default")
trial("latency=low",latency="low")
trial("latency=0.05",latency=0.05)
for i,d in enumerate(sd.query_devices()):
    if d['max_output_channels']>0 and 'WASAPI' in sd.query_hostapis(d['hostapi'])['name'] and 'Speakers' in d['name']:
        trial(f"WASAPI dev{i} auto-convert",device=i,extra_settings=sd.WasapiSettings(auto_convert=True),latency="low"); break
# envelope / pitch
def env(a,ms=10):
    n=int(24000*ms/1000); k=len(a)//n
    return 20*np.log10(np.sqrt((a[:k*n].reshape(k,n)**2).mean(1))+1e-9)
def f0(seg,sr=24000):
    seg=seg-seg.mean(); ac=np.correlate(seg,seg,"full")[len(seg)-1:]
    lo,hi=int(sr/300),int(sr/70); p=lo+np.argmax(ac[lo:hi]); return sr/p if ac[p]>0.3*ac[0] else float('nan')
def pitch_track(a,sr=24000,win=0.04):
    n=int(sr*win); return [f0(a[i:i+n]) for i in range(0,len(a)-n,n)]
t="You have three meetings today, and the first is at nine."
w=t.split(); frag=" ".join(w[:5])
A,_=tts.synth_audio(say.speakable(t)); F,_=tts.synth_audio(say.speakable(frag)); R,_=tts.synth_audio(say.speakable(" ".join(w[5:])))
e=env(F); print("fragment tail envelope dB (last 40x10ms):",np.round(e[-40::4]).astype(int).tolist())
pf=[p for p in pitch_track(F) if p==p]; pa=[p for p in pitch_track(A[:len(F)]) if p==p]
print("frag pitch last 6 voiced (Hz):",np.round(pf[-6:]).tolist())
# pitch of the same words inside the whole sentence (same time span approx)
print("whole pitch around same span (Hz):",np.round(pa[-6:]).tolist())
pr=[p for p in pitch_track(R) if p==p]; print("rest pitch first 4 (Hz):",np.round(pr[:4]).tolist())
# tail silence profile of full clips
for name,x in (("whole",A),("rest",R)):
    e=env(x); idx=np.where(e>-45)[0]; print(name,"last frame above -45 dB at",len(x)/24000-(len(e)-1-idx[-1])*0.01,"of",len(x)/24000)
def wr(n,x):
    with wave.open(n,"wb") as f: f.setnchannels(1); f.setsampwidth(2); f.setframerate(24000); f.writeframes((np.clip(x,-1,1)*32767).astype("<i2").tobytes())
gap=lambda s:np.zeros(int(24000*s),dtype=np.float32)
dev_open=0.15   # measured seam extra ~ open+start latency
wr("A_whole.wav",A)
wr("B_current_seam.wav",np.concatenate([F,gap(dev_open),R]))
def trim(x,thr=0.01,keep=0.02):
    m=np.abs(x)>thr; i=np.argmax(m); j=len(x)-np.argmax(m[::-1]); return x[max(0,i-int(keep*24000)):j+int(keep*24000)]
def fade(x,ms=12):
    n=int(24000*ms/1000); x=x.copy(); x[:n]*=np.linspace(0,1,n); x[-n:]*=np.linspace(1,0,n); return x
wr("C_trimmed_crossfade.wav",np.concatenate([fade(trim(F)),fade(trim(R))]))
# crossfade overlap
Ft,Rt=trim(F),trim(R); n=int(0.015*24000)
x=np.concatenate([Ft[:-n],Ft[-n:]*np.linspace(1,0,n)+Rt[:n]*np.linspace(0,1,n),Rt[n:]])
wr("D_overlap_15ms.wav",x)
print("lengths whole/current/trimmed/overlap:",len(A)/24000,(len(F)+len(R))/24000+dev_open,(len(fade(trim(F)))+len(fade(trim(R))))/24000,len(x)/24000)
