"""G2 spike, part 4: AppContainer with zero capabilities (no admin).
Creates the AppContainer profile 'CSpace.GodMode.Tests', a scratch folder granted to it, and a private Python
runtime copy (see godmode/pyruntime.py). Changes ACLs only on those two GOD mode folders. Checks:
 1. control: a normal child reaches Ollama on 127.0.0.1:11434;
 2. the AppContainer child cannot reach 127.0.0.1 (loopback) or the internet;
 3. it cannot read a file in the user's TEMP folder;
 4. it can write its granted scratch folder;
 5. Python runs inside it from the private runtime and is equally blocked.
Run: py -3 -I GodMode/spikes/appcontainer_spike.py"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godmode import pyruntime  # noqa: E402
from godmode import sandbox_win as sb  # noqa: E402

SYS32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
CMD, CURL = SYS32 / "cmd.exe", SYS32 / "curl.exe"
NET = ("import socket,sys\n"
       "for host,port in (('127.0.0.1',11434),('1.1.1.1',443)):\n"
       "    try: socket.create_connection((host,port),timeout=4).close(); print('CONNECTED',host)\n"
       "    except OSError as e: print('BLOCKED',host,type(e).__name__)\n"
       "try: open(sys.argv[1]).read(); print('READ user file')\n"
       "except OSError: print('DENIED user file')\n"
       "open(sys.argv[2],'w').write('x'); print('WROTE scratch')\n")


def main():
    scratch = sb.broker_dir() / "acspike"
    scratch.mkdir(parents=True, exist_ok=True)
    rt = pyruntime.build(sb.broker_dir() / "runtime" / "python")
    sid = sb.grant_appcontainer(scratch, "M")
    sb.grant_appcontainer(rt, "RX")
    print("AppContainer SID", sid)
    fd, name = tempfile.mkstemp(prefix="godac-", suffix=".txt")
    os.close(fd)
    user_file = Path(name)
    user_file.write_text("user data", encoding="utf-8")
    lim = sb.Limits(cpu_pct=100)
    checks = []
    try:
        code, out = sb.run([str(CURL), "-s", "-m", "5", "http://127.0.0.1:11434/api/version"], cwd=str(scratch),
                           sandbox="none", limits=lim, timeout=30)
        checks.append(("control: normal child reaches Ollama on loopback", "version" in out))
        code, out = sb.run([str(CURL), "-s", "-m", "5", "http://127.0.0.1:11434/api/version"], cwd=str(scratch),
                           sandbox="appcontainer", limits=lim, timeout=30)
        checks.append(("AppContainer curl: loopback blocked", "version" not in out and code != 0))
        code, out = sb.run([str(CURL), "-s", "-m", "5", "-I", "https://www.microsoft.com"], cwd=str(scratch),
                           sandbox="appcontainer", limits=lim, timeout=30)
        checks.append(("AppContainer curl: internet blocked", code != 0 and "HTTP/" not in out))
        code, out = sb.run([str(CMD), "/c", "type", str(user_file), "&", "echo", "ok>", str(scratch / "cmd.txt")],
                           cwd=str(scratch), sandbox="appcontainer", limits=lim, timeout=30)
        print("cmd:", out.strip())
        checks.append(("AppContainer cmd: user file not readable", "user data" not in out))
        checks.append(("AppContainer cmd: granted folder writable", (scratch / "cmd.txt").is_file()))
        code, out = sb.run([str(rt / "python.exe"), "-I", "-S", "-B", "-c", NET, str(user_file),
                            str(scratch / "py.txt")], cwd=str(scratch), sandbox="appcontainer", limits=lim, timeout=60)
        print("python:", out.strip())
        checks.append(("AppContainer python runs and is offline",
                       "BLOCKED 127.0.0.1" in out and "BLOCKED 1.1.1.1" in out and "WROTE scratch" in out))
        checks.append(("AppContainer python: user file denied", "DENIED user file" in out))
    finally:
        user_file.unlink(missing_ok=True)
        for f in ("cmd.txt", "py.txt"):
            (scratch / f).unlink(missing_ok=True)
    for name, ok in checks:
        print(("PASS " if ok else "FAIL ") + name)
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
