"""llm: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import json
import os
import queue
import subprocess
import threading
import time
import urllib.request
from .base import MODELS_FILE, NO_WINDOW, OLLAMA, cancel, log, setting
from .gpu import cpu_in_use, cpu_threads, gpu


def ctx_tokens():
    """The model's context window (JarvisContext, default 2048 - less memory and a faster first word)."""
    try:
        return max(1024, min(32768, int(float(setting("JarvisContext", "2048")))))
    except ValueError:
        return 2048


# ------------------------------------------------------------------ Ollama
def http_json(path, payload=None, timeout=5):
    req = urllib.request.Request(OLLAMA + path, data=json.dumps(payload).encode() if payload is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def ensure_ollama():
    """Ensure Ollama is running, starting it if needed."""
    try:
        http_json("/api/tags", timeout=2)
        return True
    except Exception:
        pass
    try:
        # with both cards visible Ollama picks the Radeon (more shared memory): hide it, so it is the NVIDIA card or nothing
        env = dict(os.environ, ROCR_VISIBLE_DEVICES="-1", HIP_VISIBLE_DEVICES="-1")
        subprocess.Popen(["ollama", "serve"], creationflags=NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    except OSError:
        return False
    # Wait for Ollama to start (up to 10 seconds)
    for _ in range(20):
        time.sleep(0.5)
        try:
            http_json("/api/tags", timeout=2)
            return True
        except Exception:
            pass
    return False


def installed_models():
    try:
        names = sorted(m["name"] for m in http_json("/api/tags", timeout=3).get("models", []))
    except Exception:
        return None
    try:
        with open(MODELS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(names) + "\n")
    except OSError:
        pass
    return names


def pick_model(tier):
    """JarvisModel normally; JarvisModelFast (if set) while the HUD is on LITE / LOW because the GPU is busy."""
    want = setting("JarvisModel", "llama3.1:8b")
    fast = setting("JarvisModelFast", "")
    if tier >= 1 and fast:
        want = fast
    names = installed_models()
    if names is None:
        return want
    other = fast if want != fast else setting("JarvisModel", "llama3.1:8b")
    for n in (want, want + ":latest", other, other + ":latest"):
        if n in names:                                         # only a model you configured: never an embedding model
            if n not in (want, want + ":latest"):
                log(f"model {want} not downloaded - using {n}, the other configured model")
            return n
    log(f"model {want} not downloaded and no other configured model is installed")
    return None


def keep_alive():
    try:
        return f"{max(1, int(float(setting('JarvisKeepAlive', '10'))))}m"
    except ValueError:
        return "10m"


def load_options():
    """The options that decide how Ollama LOADS the model: the same for the warm-up and for every chat call. A call
    with another num_ctx makes Ollama unload the model and load it again (seconds), so these must never differ."""
    opts = {"num_ctx": ctx_tokens()}
    if not gpu():
        opts["num_thread"] = cpu_threads()
    return opts


def warm(model):
    def go():
        try:
            http_json("/api/generate", {"model": model, "prompt": "", "keep_alive": keep_alive(), "options": load_options()},
                      timeout=120)
        except Exception:
            pass
    threading.Thread(target=go, daemon=True).start()


def ollama_on_cpu(model):
    """Warn when Ollama keeps any part of the chat model in ordinary memory instead of on the graphics card."""
    try:
        for m in http_json("/api/ps", timeout=2).get("models", []):
            if m.get("name") == model and m.get("size_vram", 0) < m.get("size", 0):
                cpu_in_use("the chat model", f"{100 - 100 * m.get('size_vram', 0) // m['size']}% of it is off the GPU")
                return True
    except Exception:
        pass
    return False


_moved = set()                 # chat models reloaded once since they were last seen fully on the card


def chat_to_gpu(model):
    """Ollama keeps part of the chat model off the card: if the card is there, unload and warm it again - once, so a
    card full of a game's data costs one reload, not one per turn."""
    if model in _moved or not gpu():
        return False
    _moved.add(model)

    def go():
        try:
            http_json("/api/generate", {"model": model, "keep_alive": 0}, timeout=30)
        except Exception as e:
            log(f"chat model reload failed ({type(e).__name__})")
            return
        log(f"chat model {model} reloaded to move it onto the GPU")
        warm(model)
    threading.Thread(target=go, daemon=True).start()
    return True


def chat_json(model, schema, system, user, predict, timeout):
    """One answer in a JSON schema, parsed (AI router, compaction); raises when the model is down or answers nonsense."""
    opts = dict(load_options(), temperature=0, num_predict=predict)   # the same load options as warm(): no model reload
    out = http_json("/api/chat", {"model": model, "stream": False, "format": schema, "keep_alive": keep_alive(),
                                  "options": opts, "messages": [{"role": "system", "content": system},
                                                                {"role": "user", "content": user}]}, timeout=timeout)
    return json.loads(out["message"]["content"])


def chat_stream(model, messages, temperature=0.5):
    opts = dict(load_options(), temperature=temperature, num_predict=160)
    body = json.dumps({"model": model, "messages": messages, "stream": True, "keep_alive": keep_alive(),
                       "options": opts}).encode()
    req = urllib.request.Request(OLLAMA + "/api/chat", data=body, headers={"Content-Type": "application/json"})
    # the blocking network read runs in its own thread, so a cancel is seen within 0.2 s even while the model is
    # still thinking; the abandoned read closes its connection as soon as it wakes, which makes Ollama stop too
    lines, gone = queue.Queue(), threading.Event()

    def pump():
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                for raw in r:
                    if gone.is_set():
                        return
                    lines.put(raw)
            lines.put(None)
        except Exception as e:
            lines.put(e)

    threading.Thread(target=pump, daemon=True).start()
    try:
        while True:
            try:
                raw = lines.get(timeout=0.2)
            except queue.Empty:
                if cancel.is_set():
                    return
                continue
            if raw is None or cancel.is_set():
                return
            if isinstance(raw, Exception):
                raise raw
            raw = raw.strip()
            if not raw:
                continue
            obj = json.loads(raw)
            piece = obj.get("message", {}).get("content", "")
            if piece:
                yield piece
            if obj.get("done"):
                return
    finally:
        gone.set()
