"""G2 spike, part 1: prove the low-integrity sandbox on this laptop. Safe: it only creates and writes
two small files in folders it makes itself, and only ever terminates its own child (via the job).

Checks:
 1. child at low IL cannot write a medium-integrity folder (a temp folder this script creates);
 2. child CAN write LocalLow\\CSpace\\GodMode\\spike;
 3. a timed-out child is killed by the job;
 4. the private-commit cap stops a child that tries to allocate past it.
Run:  py -3 -I GodMode/spikes/lowil_spike.py"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godmode import sandbox_win as sb  # noqa: E402

PY = sys.executable


def main():
    results = []
    medium = Path(tempfile.mkdtemp(prefix="godspike-medium-"))
    low = sb.low_il_dir() / "spike"
    low.mkdir(parents=True, exist_ok=True)
    child = ("import sys\n"
             "def w(p):\n"
             "    try:\n"
             "        open(p,'w').write('x'); print('WROTE', p)\n"
             "    except OSError as e: print('DENIED', p, type(e).__name__)\n"
             "w(sys.argv[1]); w(sys.argv[2])\n")
    code, out = sb.run([PY, "-I", "-B", "-c", child, str(medium / "should_fail.txt"), str(low / "should_work.txt")],
                       cwd=str(low), env={"TEMP": str(low), "TMP": str(low)}, timeout=60,
                       limits=sb.Limits(cpu_pct=50))
    print("child exit", code)
    print(out.strip())
    results.append(("low IL cannot write medium folder", f"DENIED {medium / 'should_fail.txt'}" in out))
    results.append(("low IL can write LocalLow", f"WROTE {low / 'should_work.txt'}" in out))

    code, out = sb.run([PY, "-I", "-B", "-c", "import time; time.sleep(30)"], cwd=str(low), timeout=2,
                       limits=sb.Limits())
    results.append(("timeout kills the child via the job", code is None))

    code, out = sb.run([PY, "-I", "-B", "-c", "b = bytearray(1500 * 1024 * 1024); print('ALLOCATED')"],
                       cwd=str(low), timeout=60, limits=sb.Limits(private_commit=512 << 20))
    results.append(("private-commit cap stops a 1.5 GB allocation", "ALLOCATED" not in out and code not in (0, None)))

    for name, ok in results:
        print(("PASS " if ok else "FAIL ") + name)
    (medium / "should_fail.txt").unlink(missing_ok=True)
    medium.rmdir()
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    sys.exit(main())
