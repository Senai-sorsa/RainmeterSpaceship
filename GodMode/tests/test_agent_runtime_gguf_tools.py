import json
import struct
import tempfile
import unittest
from pathlib import Path

from godmode import agent, audit, gguf, memory, paths, runtime
from godmode.gate import ModeGate, Violation
from godmode.tools import ToolBox, schemas

G = memory.GiB


class ScriptedClient:
    def __init__(self, replies):
        self.replies, self.seen = list(replies), []

    def chat(self, messages, tools):
        self.seen.append((len(messages), [t["function"]["name"] for t in tools or []]))
        return self.replies.pop(0) if self.replies else {"content": "done", "tool_calls": []}


class FakeTools:
    def __init__(self):
        self.calls = []

    def call(self, name, args):
        self.calls.append((name, args))
        if name == "fs_read" and "bad" in args.get("path", ""):
            raise paths.PathRejected("ADS")
        return "<<untrusted data: x>>\nhello\n<<end of data>>"


def call(name, **args):
    return {"content": "", "tool_calls": [{"id": "1", "name": name, "arguments": args}]}


def session(replies, mode="read", slot="advanced", **kw):
    d = Path(tempfile.mkdtemp())
    s = agent.Session(client=ScriptedClient(replies), gate=ModeGate(mode, slot), toolbox=FakeTools(),
                      audit=audit.AuditLog(d / "audit.jsonl"), jobs_dir=d / "jobs", lock_file=d / "lock", **kw)
    return s, d


class Agent(unittest.TestCase):
    def test_tool_then_answer_and_checkpoint(self):
        s, d = session([call("fs_read", path="C:\\a.txt"), {"content": "It says hello (C:\\a.txt:1).", "tool_calls": []}])
        r = s.ask("what does a.txt say?")
        self.assertEqual(r["status"], "done")
        self.assertEqual(s.toolbox.calls, [("fs_read", {"path": "C:\\a.txt"})])
        ck = json.loads((d / "jobs" / f"{s.job_id}.json").read_text(encoding="utf-8"))
        self.assertEqual(ck["status"], "done")
        self.assertTrue(audit.AuditLog(d / "audit.jsonl").verify()[0])

    def test_tool_not_allowed_trips_and_locks(self):
        s, d = session([call("apply_patch", reason="x", edits=[])])
        with self.assertRaises(agent.Tripped):
            s.ask("change your code")
        self.assertTrue((d / "lock").exists())
        with self.assertRaises(RuntimeError):   # locked until a person acknowledges
            agent.Session(client=None, gate=ModeGate("read", "advanced"), toolbox=None, audit=None, jobs_dir=d,
                          lock_file=d / "lock")

    def test_bad_path_trips(self):
        s, _ = session([call("fs_read", path="C:\\bad")])
        with self.assertRaises(agent.Tripped):
            s.ask("x")

    def test_ultron_sends_no_tools_and_trips_on_any_call(self):
        s, _ = session([call("fs_read", path="C:\\a.txt")], mode="ultron", slot="ultron")
        with self.assertRaises(agent.Tripped):
            s.ask("read a file")
        self.assertEqual(s.client.seen[0][1], [])
        self.assertEqual(s.toolbox.calls, [])

    def test_repeat_loop_stops(self):
        s, _ = session([call("fs_read", path="C:\\a.txt")] * 5)
        self.assertEqual(s.ask("x")["status"], "repeat-loop")

    def test_step_cap(self):
        s, _ = session([call("fs_read", path=f"C:\\{i}.txt") for i in range(10)], caps=agent.Caps(max_steps=3))
        self.assertEqual(s.ask("x")["status"], "step-cap")

    def test_memory_pause_then_resume(self):
        snaps = iter([3.5, 3.5, 3.5, 6, 6, 6, 6, 6] + [8] * 20)
        sleeps = []
        s, d = session([{"content": "ok", "tool_calls": []}], watchdog=memory.Watchdog(),
                       snapshot=lambda: memory.Snapshot(32 * G, int(next(snaps) * G), 0, 0, 12 * G, 0),
                       sleep=sleeps.append)
        # first sample is low but not yet sustained -> runs; make it sustained by pre-stepping twice
        s.watchdog.step(memory.Snapshot(32 * G, int(3.5 * G), 0, 0, 12 * G, 0))
        s.watchdog.step(memory.Snapshot(32 * G, int(3.5 * G), 0, 0, 12 * G, 0))
        self.assertEqual(s.ask("x")["status"], "done")
        self.assertTrue(sleeps)

    def test_memory_critical_stops(self):
        s, _ = session([{"content": "ok", "tool_calls": []}], watchdog=memory.Watchdog(),
                       snapshot=lambda: memory.Snapshot(32 * G, 1 * G, 0, 0, 12 * G, 0))
        self.assertEqual(s.ask("x")["status"], "stopped-memory")

    def test_resume_from_checkpoint(self):
        s, d = session([call("fs_read", path="C:\\a.txt")] * 1, caps=agent.Caps(max_steps=1))
        s.ask("x")
        path = d / "jobs" / f"{s.job_id}.json"
        s2 = agent.Session.resume(path, client=ScriptedClient([]), gate=ModeGate("read", "advanced"),
                                  toolbox=FakeTools(), audit=audit.AuditLog(d / "audit.jsonl"), jobs_dir=d / "jobs")
        self.assertEqual(s2.job_id, s.job_id)
        with self.assertRaises(ValueError):
            agent.Session.resume(path, client=None, gate=ModeGate("tweak", "advanced"), toolbox=None,
                                 audit=None, jobs_dir=d / "jobs")


class Runtime(unittest.TestCase):
    def test_loopback_only(self):
        for bad in ["http://10.0.0.5:11434", "https://127.0.0.1:1", "http://example.com", "file:///c:/x"]:
            with self.assertRaises(ValueError):
                runtime.OllamaClient("m", base=bad)
        runtime.OllamaClient("m", base="http://127.0.0.1:11434")

    def test_args_parsing_never_throws(self):
        self.assertEqual(runtime._args('{"a": 1}'), {"a": 1})
        self.assertIn("_malformed", runtime._args("{nope"))
        self.assertIn("_malformed", runtime._args("[1]"))
        self.assertIn("_malformed", runtime._args(None))

    def test_llama_server_argv(self):
        pl = memory.Placement("stream", "r", ctx=16384, n_cpu_moe=30, threads=8)
        argv, env, key = runtime.llama_server_argv("C:\\ls\\llama-server.exe", "C:\\m\\gpt.gguf", pl, 5555)
        self.assertNotIn("--no-mmap", argv)
        self.assertNotIn("--mlock", argv)
        self.assertEqual(argv[argv.index("--host") + 1], "127.0.0.1")
        self.assertEqual(argv[argv.index("--n-cpu-moe") + 1], "30")
        self.assertNotIn(key, argv)
        self.assertEqual(env["LLAMA_ARG_API_KEY"], key)
        self.assertEqual(env["GGML_CUDA_NO_PINNED"], "1")
        for bad in (["--no-mmap"], ["--mlock"], ["--host", "0.0.0.0"]):
            with self.assertRaises(ValueError):
                runtime.llama_server_argv("C:\\ls\\l.exe", "C:\\m\\g.gguf", pl, 1, extra=bad)
        with self.assertRaises(ValueError):
            runtime.llama_server_argv("C:\\l.exe", "C:\\g.gguf", memory.Placement("refuse", "no"), 1)


def write_gguf(path, template="{{ messages }}", n_layers=2):
    def s(x):
        b = x.encode()
        return struct.pack("<Q", len(b)) + b
    kv = [("general.architecture", 8, s("gptoss")), ("gptoss.block_count", 4, struct.pack("<I", n_layers)),
          ("gptoss.attention.head_count_kv", 4, struct.pack("<I", 8)),
          ("gptoss.attention.key_length", 4, struct.pack("<I", 64)),
          ("tokenizer.ggml.tokens", 9, struct.pack("<IQ", 8, 2) + s("a") + s("b")),
          ("tokenizer.chat_template", 8, s(template))]
    tensors = [("blk.0.attn_q.weight", 100), ("blk.0.ffn_up_exps.weight", 300), ("blk.1.ffn_down_exps.weight", 200)]
    head = b"GGUF" + struct.pack("<IQQ", 3, len(tensors), len(kv))
    for k, t, v in kv:
        head += s(k) + struct.pack("<I", t) + v
    off = 0
    for name, size in tensors:
        head += s(name) + struct.pack("<I", 1) + struct.pack("<Q", size) + struct.pack("<IQ", 0, off)
        off += size
    pad = (-len(head)) % 32
    Path(path).write_bytes(head + b"\0" * pad + b"\1" * off)


class GGUF(unittest.TestCase):
    def test_summary(self):
        p = Path(tempfile.mkdtemp()) / "m.gguf"
        write_gguf(p)
        s = gguf.summarize(gguf.read(p))
        self.assertEqual((s["architecture"], s["n_layers"], s["expert_bytes"]), ("gptoss", 2, 500))
        self.assertEqual(s["kv_bytes_per_token_f16"], 2 * 2 * 8 * 64 * 2)
        self.assertEqual(s["template_red_flags"], [])

    def test_template_red_flags(self):
        p = Path(tempfile.mkdtemp()) / "m.gguf"
        write_gguf(p, template="{{ cycler.__init__.__globals__.os.popen('calc') }}")
        self.assertTrue(gguf.summarize(gguf.read(p))["template_red_flags"])

    def test_not_gguf(self):
        p = Path(tempfile.mkdtemp()) / "x.gguf"
        p.write_bytes(b"NOPE" + b"\0" * 40)
        with self.assertRaises(gguf.GGUFError):
            gguf.read(p)

    def test_ollama_blob(self):
        root = Path(tempfile.mkdtemp())
        man = root / "manifests" / "registry.ollama.ai" / "library" / "gpt-oss"
        man.mkdir(parents=True)
        dig = "sha256:" + "a" * 64
        (man / "120b").write_text(json.dumps({"layers": [{"mediaType": "application/vnd.ollama.image.model",
                                                         "digest": dig}]}))
        self.assertEqual(gguf.ollama_blob("gpt-oss:120b", root), root / "blobs" / ("sha256-" + "a" * 64))
        for bad in ("../x", "a/b", "A:1"):
            with self.assertRaises(ValueError):
                gguf.ollama_blob(bad, root)


class TempOnlyFacts(paths.OSFacts):
    """Real facts inside the test's temp folder; parent folders count as plain folders. Keeps these tests
    independent of the machine's folder permissions (they also run inside the AppContainer)."""

    def __init__(self, root):
        self.root = str(root).lower()

    def attributes(self, p):
        return super().attributes(p) if p.lower().startswith(self.root) else 0x10


class Tools(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        (self.d / "notes.md").write_text("line one\nJarvis rocks\n", encoding="utf-8")
        (self.d / ".env").write_text("KEY=1", encoding="utf-8")
        (self.d / "blob.bin").write_bytes(b"\0\1\2")
        self.tb = ToolBox(policy=paths.PathPolicy(TempOnlyFacts(self.d)))

    def test_read_with_line_numbers_and_label(self):
        out = self.tb.call("fs_read", {"path": str(self.d / "notes.md")})
        self.assertIn("2: Jarvis rocks", out)
        self.assertIn("untrusted data", out)

    def test_secret_not_read_or_listed(self):
        self.assertIn("privacy", self.tb.call("fs_read", {"path": str(self.d / ".env")}))
        self.assertNotIn(".env", self.tb.call("fs_list", {"path": str(self.d)}))

    def test_binary_gives_hash(self):
        self.assertIn("sha256", self.tb.call("fs_read", {"path": str(self.d / "blob.bin")}))

    def test_grep(self):
        out = self.tb.call("fs_grep", {"path": str(self.d), "text": "jarvis"})
        self.assertIn("notes.md:2", out)

    def test_bad_path_raises_rejected(self):
        with self.assertRaises(paths.PathRejected):
            self.tb.call("fs_read", {"path": str(self.d / "notes.md") + ":ads"})

    def test_missing_args_and_malformed(self):
        self.assertTrue(self.tb.call("fs_read", {}).startswith("error"))
        self.assertTrue(self.tb.call("fs_read", {"path": "C:\\x", "_malformed": "x"}).startswith("error"))

    def test_apply_patch_unavailable_without_broker(self):
        self.assertIn("not available", self.tb.call("apply_patch", {"reason": "r", "edits": []}))

    def test_unknown_tool(self):
        with self.assertRaises(Violation):
            self.tb.call("shell", {})

    def test_schemas_valid(self):
        names = {x["function"]["name"] for x in schemas({"fs_read", "apply_patch"})}
        self.assertEqual(names, {"fs_read", "apply_patch"})


if __name__ == "__main__":
    unittest.main()
