import sys,time
import numpy as np, sounddevice as sd
print(sd.query_devices(kind="output")['name'], sd.default.device, sd.query_devices(kind="output")['default_samplerate'])
sr=24000; blk=int(sr*0.04); z=np.zeros(blk,dtype=np.float32)
res=[]
for k in range(12):
    t0=time.time()
    with sd.OutputStream(samplerate=sr,channels=1,dtype="float32") as o:
        t1=time.time(); o.write(z); t2=time.time()
        for _ in range(5): o.write(z)
        t3=time.time()
    t4=time.time()
    res.append((t1-t0,t2-t1,t4-t3,t4-t0))
r=np.array(res)*1000
print("ms  open / first-write / close / total  (median, max)")
for n,c in zip(["open","first write","close","total"],r.T): print(f"{n:12s} median {np.median(c):6.1f}  max {c.max():6.1f}  min {c.min():6.1f}")
# latency reported
with sd.OutputStream(samplerate=sr,channels=1,dtype="float32") as o: print("stream latency (s):",o.latency)
