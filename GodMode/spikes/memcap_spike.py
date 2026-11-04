"""G2 spike, part 2: does the hard working-set cap really hold memory down? (comfortable-RAM rule)
Measures a low-IL child's working set (resident RAM) for:
  A. 600 MB of touched private memory, no cap (control)
  B. same, with a 200 MB hard cap
  C. a 600 MB memory-mapped file read end to end, no cap (control)  <- how a model file is read
  D. same, with a 200 MB hard cap
  E. a grandchild (started by the child) under the job-wide cap
Safe: writes one 600 MB scratch file in LocalLow\\CSpace\\GodMode\\spike and deletes it; may page ~1 GB
to the pagefile briefly. Run: py -3 -I GodMode/spikes/memcap_spike.py"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godmode import sandbox_win as sb  # noqa: E402

PY, MB = sys.executable, 1 << 20
SIZE = 600 * MB
CAP = 200 * MB

TOUCH = ("import sys,time\n"
         "b=bytearray(%d)\n"
         "for i in range(0,len(b),4096): b[i]=1\n"
         "print('READY',flush=True); time.sleep(4)\n" % SIZE)
MAPREAD = ("import sys,mmap,time\n"
           "f=open(sys.argv[1],'rb'); m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)\n"
           "s=0\n"
           "for i in range(0,len(m),4096): s+=m[i]\n"
           "print('READY',s,flush=True); time.sleep(4)\n")
GRAND = ("import subprocess,sys\n"
         "p=subprocess.Popen([sys.executable,'-I','-B','-c',sys.argv[1]]); p.wait()\n")


def measure(argv, cap, low):
    lim = sb.Limits(private_commit=2 << 30, working_set_cap=cap, cpu_pct=100, low_memory_priority=True)
    with sb.spawn(argv, cwd=str(low), env={"TEMP": str(low), "TMP": str(low)}, limits=lim, pipes=True) as p:
        line = b""
        t0 = time.time()
        import threading
        stop = threading.Event()

        p.watch_new_processes(lim)   # event-driven: caps each new process as it joins the job
        while b"READY" not in line and time.time() - t0 < 120:
            ch = p.stdout.readline()
            if not ch:
                break
            line = ch
        time.sleep(0.5)
        ws = p.working_sets()
        stop.set()
        p.kill()
        p.wait(10)
    peak = max((v[1] for v in ws.values()), default=0)
    cur = max((v[0] for v in ws.values()), default=0)
    return b"READY" in line, cur, peak, len(ws)


def main():
    low = sb.low_il_dir() / "spike"
    low.mkdir(parents=True, exist_ok=True)
    big = low / "mapped.bin"
    with open(big, "wb") as f:
        chunk = b"\x01" * (8 * MB)
        for _ in range(SIZE // len(chunk)):
            f.write(chunk)
    rows = []
    try:
        rows.append(("A private, no cap", *measure([PY, "-I", "-B", "-c", TOUCH], 0, low)))
        rows.append(("B private, 200 MB cap", *measure([PY, "-I", "-B", "-c", TOUCH], CAP, low)))
        rows.append(("C mmap file, no cap", *measure([PY, "-I", "-B", "-c", MAPREAD, str(big)], 0, low)))
        rows.append(("D mmap file, 200 MB cap", *measure([PY, "-I", "-B", "-c", MAPREAD, str(big)], CAP, low)))
        rows.append(("E grandchild mmap, event cap", *measure([PY, "-I", "-B", "-c", GRAND,
                                                              MAPREAD.replace("sys.argv[1]", repr(str(big)))], CAP, low)))
    finally:
        big.unlink(missing_ok=True)
    for name, ready, cur, peak, n in rows:
        print(f"{name:28s} ready={ready} procs={n} working_set={cur / MB:6.0f} MB  peak={peak / MB:6.0f} MB")
    ok = {r[0][0]: r for r in rows}
    checks = [
        ("controls really used the memory (A,C > 500 MB peak)", ok["A"][3] > 500 * MB and ok["C"][3] > 500 * MB),
        ("hard cap holds private memory (B peak <= cap + 16 MB)", ok["B"][3] <= CAP + 16 * MB),
        ("hard cap holds mapped-file pages (D peak <= cap + 16 MB)", ok["D"][3] <= CAP + 16 * MB),
        ("event cap holds a grandchild (E peak <= cap + 16 MB)", ok["E"][3] <= CAP + 16 * MB),
    ]
    for name, good in checks:
        print(("PASS " if good else "FAIL ") + name)
    return 0 if all(g for _, g in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
