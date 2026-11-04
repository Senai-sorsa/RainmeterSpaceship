"""Runs every tests/test_*.py in its own process (no fake can leak from one file to the next); prints "tests: OK" when all pass.
The old test_jarvis.py and test_host_pipe.py are still run separately (refactor plan section 4) until phase 8 moves them here.
Run the old test_jarvis.py ONLY through the tripwire runner:  py -3 -B tests/guarded_run.py test_jarvis.py  (from this folder's parent).
It makes any destructive call the test forgot to fake (real process, delete outside temp, recycle bin, registry write, lock, sleep) fail loudly instead of acting."""
import glob
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    failed = []
    for path in sorted(glob.glob(os.path.join(HERE, "test_*.py"))):
        t0 = time.time()
        r = subprocess.run([sys.executable, "-B", path], cwd=HERE, capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        last = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
        print(f"{'ok  ' if r.returncode == 0 else 'FAIL'} {os.path.basename(path)} ({time.time() - t0:.1f}s): {last}")
        if r.returncode:
            failed.append(path)
            print(r.stdout[-3000:], r.stderr[-3000:], sep="\n")
    print("tests: OK" if not failed else f"tests: {len(failed)} FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
