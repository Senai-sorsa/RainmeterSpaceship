"""Model runtimes, loopback only.
- OllamaClient: /api/chat with tools (Jarvis Advanced; ULTRON later, without tools).
- OpenAIClient: llama-server /v1/chat/completions with a per-run API key (Jarvis Ascendent, split mode).
- llama_server_argv: the split/stream command line from a memory Placement. Never --no-mmap / --mlock."""
import json
import secrets
import socket
import urllib.parse
import urllib.request
from pathlib import Path

LOOPBACK = {"127.0.0.1", "localhost", "::1"}
FORBIDDEN_FLAGS = {"--no-mmap", "--mlock", "--listen", "--host"}


class RuntimeError_(Exception):
    pass


def check_loopback(url):
    u = urllib.parse.urlparse(url)
    if u.scheme != "http" or u.hostname not in LOOPBACK:
        raise ValueError(f"only http://127.0.0.1 URLs are allowed, got {url!r}")
    return url.rstrip("/")


_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # never route through a proxy


def _post(url, body, timeout, headers=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json", **(headers or {})})
    with _opener.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _get(url, timeout=5, headers=None):
    with _opener.open(urllib.request.Request(url, headers=headers or {}), timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _args(raw):
    """Tool-call arguments may arrive as a dict or a JSON string; malformed -> {'_malformed': text}."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            v = json.loads(raw)
            return v if isinstance(v, dict) else {"_malformed": raw[:500]}
        except ValueError:
            return {"_malformed": raw[:500]}
    return {"_malformed": repr(raw)[:500]}


class OllamaClient:
    def __init__(self, model, base="http://127.0.0.1:11434", options=None, timeout=3600, think=None):
        self.base, self.model = check_loopback(base), model
        self.options, self.timeout, self.think = options or {}, timeout, think

    def version(self):
        return _get(self.base + "/api/version").get("version")

    def tags(self):
        return [m.get("name") for m in _get(self.base + "/api/tags").get("models", [])]

    def unload(self):
        _post(self.base + "/api/generate", {"model": self.model, "keep_alive": 0}, timeout=30)

    def chat(self, messages, tools):
        body = {"model": self.model, "messages": [_to_ollama(m) for m in messages], "stream": False,
                "options": self.options}
        if tools:
            body["tools"] = tools
        if self.think is not None:
            body["think"] = self.think
        r = _post(self.base + "/api/chat", body, self.timeout)
        msg = r.get("message") or {}
        calls = [{"id": f"c{i}", "name": (c.get("function") or {}).get("name"),
                  "arguments": _args((c.get("function") or {}).get("arguments"))}
                 for i, c in enumerate(msg.get("tool_calls") or [])]
        return {"content": msg.get("content") or "", "thinking": msg.get("thinking") or "", "tool_calls": calls,
                "stats": {k: r.get(k) for k in ("eval_count", "eval_duration", "prompt_eval_count",
                                                 "prompt_eval_duration")}}


def _to_ollama(m):
    if m["role"] == "tool":
        return {"role": "tool", "tool_name": m.get("name", ""), "content": m["content"]}
    if m["role"] == "assistant" and m.get("tool_calls"):
        return {"role": "assistant", "content": m.get("content", ""),
                "tool_calls": [{"function": {"name": c["name"], "arguments": c["arguments"]}} for c in m["tool_calls"]]}
    return {"role": m["role"], "content": m["content"]}


class OpenAIClient:
    def __init__(self, base, api_key, model="local", timeout=7200):
        self.base, self.key, self.model, self.timeout = check_loopback(base), api_key, model, timeout

    def health(self):
        return _get(self.base + "/health", headers={"Authorization": f"Bearer {self.key}"})

    def chat(self, messages, tools):
        body = {"model": self.model, "messages": [_to_openai(m) for m in messages], "stream": False}
        if tools:
            body["tools"] = tools
        r = _post(self.base + "/v1/chat/completions", body, self.timeout, {"Authorization": f"Bearer {self.key}"})
        msg = ((r.get("choices") or [{}])[0]).get("message") or {}
        calls = [{"id": c.get("id") or f"c{i}", "name": (c.get("function") or {}).get("name"),
                  "arguments": _args((c.get("function") or {}).get("arguments"))}
                 for i, c in enumerate(msg.get("tool_calls") or [])]
        return {"content": msg.get("content") or "", "thinking": msg.get("reasoning_content") or "",
                "tool_calls": calls, "stats": r.get("timings") or {}}


def _to_openai(m):
    if m["role"] == "tool":
        return {"role": "tool", "tool_call_id": m.get("id", ""), "content": m["content"]}
    if m["role"] == "assistant" and m.get("tool_calls"):
        return {"role": "assistant", "content": m.get("content", ""),
                "tool_calls": [{"id": c["id"], "type": "function",
                                "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])}}
                               for c in m["tool_calls"]]}
    return {"role": m["role"], "content": m["content"]}


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def llama_server_argv(exe, model_path, placement, port, chat_template_file=None, kv_q8=True, extra=()):
    """Returns (argv, env). The API key goes in the environment (LLAMA_ARG_API_KEY), not the command line."""
    if placement.mode not in ("gpu", "split", "stream"):
        raise ValueError(f"placement refused: {placement.reason}")
    for flag in extra:
        if str(flag).split("=")[0] in FORBIDDEN_FLAGS:
            raise ValueError(f"{flag} is not allowed (it breaks the comfortable-RAM rule or loopback-only)")
    exe, model_path = Path(exe), Path(model_path)
    if not exe.is_absolute() or not model_path.is_absolute():
        raise ValueError("absolute paths only")
    argv = [str(exe), "-m", str(model_path), "--host", "127.0.0.1", "--port", str(int(port)),
            "-ngl", "99", "--n-cpu-moe", str(placement.n_cpu_moe), "-c", str(placement.ctx),
            "-t", str(placement.threads), "--parallel", "1", "--jinja"]
    if kv_q8:
        argv += ["-ctk", "q8_0", "-ctv", "q8_0"]
    if chat_template_file:
        argv += ["--chat-template-file", str(Path(chat_template_file))]
    argv += [str(x) for x in extra]
    key = secrets.token_urlsafe(32)
    env = {"LLAMA_ARG_API_KEY": key}
    if placement.n_cpu_moe > 0:
        env["GGML_CUDA_NO_PINNED"] = "1"   # experts on CPU: avoid pinned-host OOM [S, ollama#11772]
    return argv, env, key
