"""Read-only GGUF header reader: tensor sizes (experts vs the rest), layer count, KV cost per token,
and a safety scan of the embedded chat template (Jinja templates are a known attack route:
CVE-2024-34359, arXiv 2602.04653). Never loads weights. Never renders the template."""
import json
import os
import re
import struct
from pathlib import Path

_SCALARS = {0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i", 6: "<f", 7: "<?", 10: "<Q", 11: "<q", 12: "<d"}
STRING, ARRAY = 8, 9
MAX_STR = 64 << 20

# Patterns that have no business in a chat template. Any hit = do not use the embedded template.
TEMPLATE_RED_FLAGS = [r"__\w+__", r"\bmro\b", r"subclasses", r"globals", r"builtins", r"\bimport\b", r"popen",
                      r"\bos\.", r"subprocess", r"\beval\b", r"\bexec\b", r"\bcycler\b", r"\bjoiner\b",
                      r"\blipsum\b", r"\bself\._", r"\bconfig\.", r"\brequest\.", r"attr\("]


class GGUFError(ValueError):
    pass


class _R:
    def __init__(self, f):
        self.f = f

    def take(self, fmt):
        n = struct.calcsize(fmt)
        b = self.f.read(n)
        if len(b) != n:
            raise GGUFError("file ends inside the header")
        return struct.unpack(fmt, b)[0]

    def string(self, keep=True):
        n = self.take("<Q")
        if n > MAX_STR:
            raise GGUFError("string too long")
        if not keep:
            self.f.seek(n, os.SEEK_CUR)
            return None
        b = self.f.read(n)
        if len(b) != n:
            raise GGUFError("file ends inside a string")
        return b.decode("utf-8", "replace")

    def value(self, t, keep=True):
        if t in _SCALARS:
            return self.take(_SCALARS[t])
        if t == STRING:
            return self.string(keep)
        if t == ARRAY:
            it, n = self.take("<I"), self.take("<Q")
            if it in _SCALARS and it != 7:
                size = struct.calcsize(_SCALARS[it]) * n
                self.f.seek(size, os.SEEK_CUR)
                return f"<array {n}>"
            for _ in range(n):
                self.value(it, keep=False)
            return f"<array {n}>"
        raise GGUFError(f"unknown value type {t}")


def read(path):
    path = Path(path)
    size = path.stat().st_size
    with open(path, "rb") as f:
        r = _R(f)
        if f.read(4) != b"GGUF":
            raise GGUFError("not a GGUF file")
        version = r.take("<I")
        if version not in (2, 3):
            raise GGUFError(f"unsupported GGUF version {version}")
        n_tensors, n_kv = r.take("<Q"), r.take("<Q")
        meta = {}
        for _ in range(n_kv):
            key = r.string()
            t = r.take("<I")
            keep = t != ARRAY
            meta[key] = r.value(t, keep)
        tensors = []
        for _ in range(n_tensors):
            name = r.string()
            nd = r.take("<I")
            if nd > 8:
                raise GGUFError("too many dims")
            dims = [r.take("<Q") for _ in range(nd)]
            ttype, off = r.take("<I"), r.take("<Q")
            tensors.append((name, dims, ttype, off))
        align = int(meta.get("general.alignment", 32) or 32)
        pos = f.tell()
        data_start = (pos + align - 1) // align * align
    order = sorted(tensors, key=lambda t: t[3])
    sizes = {}
    for i, (name, _, _, off) in enumerate(order):
        end = order[i + 1][3] if i + 1 < len(order) else size - data_start
        sizes[name] = max(0, end - off)
    return {"version": version, "meta": meta, "sizes": sizes, "file_bytes": size}


def template_flags(template):
    if not isinstance(template, str):
        return []
    return sorted({p for p in TEMPLATE_RED_FLAGS if re.search(p, template)})


def summarize(info):
    meta, sizes = info["meta"], info["sizes"]
    arch = meta.get("general.architecture", "?")
    expert = sum(v for k, v in sizes.items() if "_exps" in k)
    layers = int(meta.get(f"{arch}.block_count", 0) or 0)
    kv_heads = meta.get(f"{arch}.attention.head_count_kv")
    heads = meta.get(f"{arch}.attention.head_count")
    key_len = meta.get(f"{arch}.attention.key_length")
    emb = meta.get(f"{arch}.embedding_length")
    head_dim = key_len or (emb // heads if emb and heads else None)
    kv_per_tok = 2 * layers * kv_heads * head_dim * 2 if (layers and kv_heads and head_dim) else None
    tmpl = meta.get("tokenizer.chat_template")
    return {
        "architecture": arch,
        "file_bytes": info["file_bytes"],
        "expert_bytes": expert,
        "n_layers": layers,
        "kv_bytes_per_token_f16": kv_per_tok,
        "n_tensors": len(sizes),
        "has_chat_template": isinstance(tmpl, str),
        "template_red_flags": template_flags(tmpl),
    }


def ollama_models_dir():
    return Path(os.environ.get("OLLAMA_MODELS") or Path.home() / ".ollama" / "models")


_TAG = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}(:[a-z0-9][a-z0-9._-]{0,63})?$")


def ollama_blob(tag, models_dir=None):
    """Path of the GGUF weights blob for an installed Ollama tag (library models only)."""
    if not _TAG.match(tag):
        raise ValueError("bad tag")
    name, _, ver = tag.partition(":")
    root = Path(models_dir or ollama_models_dir())
    manifest = root / "manifests" / "registry.ollama.ai" / "library" / name / (ver or "latest")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    for layer in data.get("layers", []):
        if layer.get("mediaType") == "application/vnd.ollama.image.model":
            digest = layer["digest"]
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                raise ValueError("bad digest in manifest")
            return root / "blobs" / digest.replace(":", "-")
    raise FileNotFoundError("no model layer in manifest")
