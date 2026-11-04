"""G2 spike, part 3: OS-enforced secret blocking without admin (NO_READ_UP integrity label).
Works only on a scratch folder this script creates in %TEMP%. Checks:
 1. before labelling, a low-IL child CAN read the scratch file (control);
 2. after labelling the folder Medium+NO_READ_UP, the low-IL child CANNOT read the existing file;
 3. nor a file created after the label (inheritance);
 4. this normal (medium) process can still read both;
 5. after removing the label, the low-IL child can read again (undo works).
Run: py -3 -I GodMode/spikes/label_spike.py"""
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godmode import sandbox_win as sb  # noqa: E402

PY = sys.executable
READ = ("import sys\n"
        "for p in sys.argv[1:]:\n"
        "    try: open(p).read(); print('READ', p)\n"
        "    except OSError as e: print('DENIED', p, type(e).__name__)\n")


def low_read(*files):
    low = sb.low_il_dir() / "spike"
    low.mkdir(parents=True, exist_ok=True)
    code, out = sb.run([PY, "-I", "-B", "-c", READ, *map(str, files)], cwd=str(low), timeout=60)
    return out


def main():
    d = Path(tempfile.mkdtemp(prefix="godlabel-"))
    old = d / "old_secret.txt"
    old.write_text("not really a secret", encoding="utf-8")
    checks = []
    try:
        checks.append(("control: low IL reads an unlabelled file", f"READ {old}" in low_read(old)))
        sb.set_label(d, no_read_up=True)
        new = d / "new_secret.txt"
        new.write_text("made after the label", encoding="utf-8")
        out = low_read(old, new)
        print(out.strip())
        checks.append(("labelled: low IL denied the existing file", f"DENIED {old}" in out))
        checks.append(("labelled: low IL denied a new file (inherited)", f"DENIED {new}" in out))
        checks.append(("medium process still reads both", old.read_text() and new.read_text() and True))
        sb.set_label(d, no_read_up=False)
        for f in (old, new):
            sb.set_label(f, no_read_up=False)
        out = low_read(old)
        checks.append(("undo: low IL reads again", f"READ {old}" in out))
    finally:
        try:
            sb.set_label(d, no_read_up=False)
        except OSError:
            pass
        shutil.rmtree(d, ignore_errors=True)
    for name, ok in checks:
        print(("PASS " if ok else "FAIL ") + name)
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
