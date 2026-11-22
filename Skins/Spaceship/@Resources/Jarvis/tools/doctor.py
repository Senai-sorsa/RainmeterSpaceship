"""doctor: one read-only health report for JARVIS (OpenJarvis idea: `jarvis doctor`, probes run concurrently, JSON option, a hint per failure).

    "%LOCALAPPDATA%\\SpaceshipHUD\\venv\\Scripts\\python.exe" -B tools/doctor.py [--json] [path to @Resources]

Reads files, asks Ollama's /api/tags on localhost (2 s), checks that packages can be found (find_spec: nothing is imported or loaded),
and lists audio devices only if sounddevice is already installed. It starts no process, writes nothing, loads no model, uses no GPU.
Exit code 0 = no failures (warnings are fine), 1 = at least one FAIL."""
import importlib.util
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
JARVIS_DIR = os.path.dirname(HERE)
sys.path.insert(0, JARVIS_DIR)
sys.path.insert(0, HERE)
from settings_check import check as settings_problems, read_settings  # noqa: E402

REQUIRED = {"faster_whisper": "speech recognition", "numpy": "audio maths", "sounddevice": "microphone and speakers",
            "soundfile": "audio files", "kokoro_onnx": "the voice", "openwakeword": "wake word", "onnxruntime": "voice and wake word"}
OPTIONAL = {"vosk": "stop words while he speaks", "pywebrtc_audio": "echo cancelling for the stop words", "chromadb": "smart note search",
            "piper": "backup voice"}
FILES = (("kokoro/kokoro-v1.0.onnx", "voice model"), ("kokoro/voices-v1.0.bin", "voice styles"),
         ("vosk/vosk-model-small-en-us-0.15", "stop-word model"), ("persona.txt", "persona"))
SETUP = "Control Center > CLOVER > SETUP"


def res_dir(argv):
    given = [a for a in argv[1:] if not a.startswith("--")]
    return os.path.abspath(given[0]) if given else os.path.dirname(JARVIS_DIR)


def r(name, status, message, hint=""):
    return {"name": name, "status": status, "message": message, "hint": hint}


def check_python():
    v = sys.version_info
    ok = (v.major, v.minor) >= (3, 11)
    return r("Python", "ok" if ok else "warn", f"{v.major}.{v.minor}.{v.micro} ({sys.executable})",
             "" if ok else "JARVIS is pinned for Python 3.12 (requirements.txt); run it with the venv python")


def check_packages():
    out = []
    for mod, why in REQUIRED.items():
        found = importlib.util.find_spec(mod) is not None
        out.append(r(f"package {mod}", "ok" if found else "fail", why if found else f"missing ({why})", "" if found else f"run {SETUP}"))
    for mod, why in OPTIONAL.items():
        found = importlib.util.find_spec(mod) is not None
        out.append(r(f"package {mod}", "ok" if found else "warn", why if found else f"missing: {why} is off", "" if found else f"run {SETUP}"))
    return out


def check_files(res):
    out = []
    for rel, why in FILES:
        p = os.path.join(JARVIS_DIR, *rel.split("/"))
        out.append(r(f"file {rel}", "ok" if os.path.exists(p) else "fail", why if os.path.exists(p) else f"missing ({why})",
                     "" if os.path.exists(p) else f"run {SETUP}"))
    data = os.path.join(res, "Data")
    ok = os.path.isdir(data) and os.access(data, os.W_OK)
    out.append(r("Data folder", "ok" if ok else "fail", data if ok else f"{data} is missing or not writable", "" if ok else "start the HUD once so it creates Data"))
    return out


def check_settings(res):
    path = os.path.join(res, "Settings.inc")
    if not os.path.exists(path):
        return [r("Settings.inc", "fail", f"not found at {path}", "start the HUD / Control Center once")]
    problems, set_count = settings_problems(path)
    if problems:
        return [r("Settings.inc", "warn", f"{len(problems)} problem(s); first: {problems[0]}", "py -3 -B tools/settings_check.py shows all of them")]
    return [r("Settings.inc", "ok", f"{set_count} Jarvis keys set, all known and well-formed")]


def check_ollama(res):
    want = "llama3.1:8b"
    try:
        want = read_settings(os.path.join(res, "Settings.inc")).get("JarvisModel", (want, 0))[0] or want
    except OSError:
        pass
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as resp:
            names = [m["name"] for m in json.loads(resp.read().decode()).get("models", [])]
    except Exception as e:
        return [r("Ollama", "fail", f"not answering on localhost:11434 ({type(e).__name__})", "start Ollama, or run " + SETUP)]
    out = [r("Ollama", "ok", f"{len(names)} model(s) installed")]
    have = want in names or any(n.split(":")[0] == want.split(":")[0] and ":" not in want for n in names)
    out.append(r(f"model {want}", "ok" if have else "fail", "installed" if have else "not installed", "" if have else f"ollama pull {want}"))
    return out


def check_log(res):
    p = os.path.join(res, "Data", "jarvis.log")
    if not os.path.exists(p):
        return [r("jarvis.log", "warn", "no log yet", "")]
    size = os.path.getsize(p)
    return [r("jarvis.log", "ok" if size < 500_000 else "warn", f"{size // 1024} KB (rotates at 500 KB)")]


def check_audio():
    if importlib.util.find_spec("sounddevice") is None:
        return [r("audio devices", "warn", "sounddevice not installed, not checked")]
    try:
        import sounddevice as sd
        devs = sd.query_devices()
        n_in = sum(1 for d in devs if d["max_input_channels"] > 0)
        n_out = sum(1 for d in devs if d["max_output_channels"] > 0)
        bad = n_in == 0 or n_out == 0
        return [r("audio devices", "fail" if bad else "ok", f"{n_in} input, {n_out} output", "check the microphone and speakers in Windows sound settings" if bad else "")]
    except Exception as e:
        return [r("audio devices", "warn", f"could not list ({type(e).__name__})")]


def run(res):
    jobs = [check_python, check_packages, lambda: check_files(res), lambda: check_settings(res), lambda: check_ollama(res),
            lambda: check_log(res), check_audio]
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:                    # concurrent, like OpenJarvis doctor
        results = list(pool.map(lambda f: f(), jobs))
    flat = []
    for item in results:
        flat += item if isinstance(item, list) else [item]
    return flat


def main(argv):
    res = res_dir(argv)
    rows = run(res)
    if "--json" in argv:
        print(json.dumps(rows, indent=1))
    else:
        mark = {"ok": "ok  ", "warn": "WARN", "fail": "FAIL"}
        for row in rows:
            print(f"{mark[row['status']]} {row['name']:28} {row['message']}" + (f"\n       -> {row['hint']}" if row["hint"] else ""))
        print(f"{sum(x['status'] == 'fail' for x in rows)} fail, {sum(x['status'] == 'warn' for x in rows)} warn, {len(rows)} checks")
    return 1 if any(x["status"] == "fail" for x in rows) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
