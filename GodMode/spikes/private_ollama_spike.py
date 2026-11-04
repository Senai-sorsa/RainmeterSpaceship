"""G2 spike, part 5: a PRIVATE Ollama server for GOD mode, inside our job, at low integrity, capped.
Fixes "Ollama is shared with JARVIS, so it can't be capped": GOD mode gets its own `ollama serve` on a random
loopback port, reading the same model store (low IL: it physically cannot change or prune that store;
OLLAMA_NOPRUNE=1 as well). JARVIS's Ollama on 11434 is never touched.
Uses the already-installed llama3.2:3b, 8 tokens. Kills only its own job at the end. Checks:
 1. the private server starts at low IL and answers on its port;
 2. it generates with llama3.2:3b;
 3. every process in the job (server + runner) stays under the working-set cap;
 4. the model store is unchanged (same files, same sizes) and JARVIS's Ollama still answers on 11434.
Run: py -3 -I GodMode/spikes/private_ollama_spike.py"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from godmode import gguf, runtime  # noqa: E402
from godmode import sandbox_win as sb  # noqa: E402

MB = 1 << 20
CAP = 3 << 30
OLLAMA = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Ollama" / "ollama.exe"


def store_listing():
    root = gguf.ollama_models_dir()
    return sorted((str(p.relative_to(root)), p.stat().st_size) for p in root.rglob("*") if p.is_file())


def get(url, timeout=5):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(url, timeout=timeout) as r:
        return json.loads(r.read())


def main():
    before = store_listing()
    port = runtime.free_port()
    low = sb.low_il_dir() / "ollama-tmp"
    low.mkdir(parents=True, exist_ok=True)
    env = {"OLLAMA_HOST": f"127.0.0.1:{port}", "OLLAMA_NOPRUNE": "1", "OLLAMA_MODELS": str(gguf.ollama_models_dir()),
           "OLLAMA_KEEP_ALIVE": "10s", "OLLAMA_MAX_LOADED_MODELS": "1", "OLLAMA_NUM_PARALLEL": "1",
           "TEMP": str(low), "TMP": str(low)}
    lim = sb.Limits(max_processes=8, private_commit=0, cpu_pct=70, working_set_cap=CAP)
    checks, peak = [], {}
    p = sb.spawn([str(OLLAMA), "serve"], cwd=str(low), env=env, limits=lim)
    try:
        p.watch_new_processes(lim)
        base = f"http://127.0.0.1:{port}"
        ver = None
        for _ in range(60):
            try:
                ver = get(base + "/api/version")["version"]
                break
            except OSError:
                time.sleep(0.5)
        checks.append(("private server answers at low IL", ver is not None))
        out = ""
        if ver:
            c = runtime.OllamaClient("llama3.2:3b", base=base, options={"num_predict": 8, "num_ctx": 2048},
                                     timeout=180)
            r = c.chat([{"role": "user", "content": "Reply with the single word: ready"}], None)
            out = r["content"]
            for pid, (ws, pk) in p.working_sets().items():
                peak[pid] = pk
        log = p.output()
        gpu_lines = [ln for ln in log.splitlines() if any(k in ln for k in ("offloaded", "CUDA0", "inference compute",
                                                                         "library=cuda", "layers.offload"))]
        print("GPU lines:", *gpu_lines[-6:], sep="\n  ")
        checks.append(("GPU (CUDA) used from low integrity", any("offloaded" in ln and not "offloaded 0/" in ln
                                                                  for ln in gpu_lines) or "CUDA0" in log))
        print("model said:", repr(out), "| processes:", {k: f"{v / MB:.0f} MB peak" for k, v in peak.items()})
        checks.append(("generates with llama3.2:3b", bool(out.strip())))
        checks.append(("server + runner under the working-set cap", bool(peak) and max(peak.values()) <= CAP + 16 * MB))
    finally:
        p.kill()
        p.wait(15)
        p.close()
    checks.append(("model store unchanged", store_listing() == before))
    try:
        checks.append(("JARVIS Ollama on 11434 still answers", "version" in get("http://127.0.0.1:11434/api/version")))
    except OSError:
        checks.append(("JARVIS Ollama on 11434 still answers", False))
    for name, ok in checks:
        print(("PASS " if ok else "FAIL ") + name)
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
