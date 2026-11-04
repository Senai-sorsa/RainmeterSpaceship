"""GOD mode's own model servers, sandboxed and capped (handoff gap: "Ollama is shared with JARVIS").

PrivateOllama: its own `ollama serve` on a random loopback port, at low integrity, in our Job Object, every
process (server + runner) hard-capped as it starts. Reads the normal model store; low IL means it cannot
change or prune it (OLLAMA_NOPRUNE=1 as well). JARVIS's Ollama on 11434 is never touched.
Proven by spikes/private_ollama_spike.py (CUDA works at low IL)."""
import json
import os
import time
import urllib.request
from pathlib import Path

from . import gguf, runtime
from . import sandbox_win as sb

OLLAMA_EXE = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"


def server_limits(working_set_cap, cpu_pct=70):
    # private_commit 0: CUDA reserves large private commit; RAM is held by the working-set cap instead.
    return sb.Limits(max_processes=8, private_commit=0, cpu_pct=cpu_pct, working_set_cap=int(working_set_cap))


class PrivateOllama:
    def __init__(self, working_set_cap, exe=OLLAMA_EXE, spawn=sb.spawn, port=None, cpu_pct=70):
        self.exe, self.spawn = Path(exe), spawn
        self.limits = server_limits(working_set_cap, cpu_pct)
        self.port = port or runtime.free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        self.proc = None

    def env(self):
        tmp = sb.low_il_dir() / "ollama-tmp"
        return {"OLLAMA_HOST": f"127.0.0.1:{self.port}", "OLLAMA_NOPRUNE": "1",
                "OLLAMA_MODELS": str(gguf.ollama_models_dir()), "OLLAMA_MAX_LOADED_MODELS": "1",
                "OLLAMA_NUM_PARALLEL": "1", "OLLAMA_KEEP_ALIVE": "5m", "TEMP": str(tmp), "TMP": str(tmp)}

    def start(self, timeout=30):
        if not self.exe.is_file():
            raise FileNotFoundError(f"Ollama not found at {self.exe}")
        env = self.env()
        Path(env["TEMP"]).mkdir(parents=True, exist_ok=True)
        self.proc = self.spawn([str(self.exe), "serve"], cwd=env["TEMP"], env=env, limits=self.limits,
                               sandbox="lowil")
        self.proc.watch_new_processes(self.limits)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            try:
                with opener.open(self.base + "/api/version", timeout=2) as r:
                    return json.loads(r.read())["version"]
            except OSError:
                time.sleep(0.5)
        self.stop()
        raise TimeoutError("private Ollama did not start")

    def client(self, model, **kw):
        kw.setdefault("timeout", 12 * 3600)   # must outlast memory pauses (the server is frozen, not cancelled)
        return runtime.OllamaClient(model, base=self.base, **kw)

    def stop(self):
        if self.proc:
            self.proc.kill()
            self.proc.wait(15)
            self.proc.close()
            self.proc = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *a):
        self.stop()
