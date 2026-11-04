"""Model slots and their profiles. ULTRON can never have tools, whatever the JSON says."""
import json
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNTIMES = ("ollama", "llama-server")
NO_TOOL_SLOTS = frozenset({"ultron"})


@dataclass(frozen=True)
class Profile:
    slot: str
    display: str
    runtime: str
    model: str
    file_bytes: int
    expert_bytes: int
    n_layers: int
    kv_bytes_per_token: int
    ctx_default: int
    ctx_min: int
    tools: bool
    estimate: bool = True
    reserved: bool = False

    @property
    def other_bytes(self):
        """Weights that are not routed experts (attention, shared, embeddings)."""
        return max(0, self.file_bytes - self.expert_bytes)

    @property
    def expert_bytes_per_layer(self):
        return self.expert_bytes // self.n_layers if self.n_layers else 0


def problem(slot, d):
    """Returns a reason string if the profile is not usable, else None."""
    if d.get("runtime") not in RUNTIMES:
        return f"{slot}: unknown runtime {d.get('runtime')!r}"
    for k in ("file_bytes", "expert_bytes", "n_layers", "kv_bytes_per_token", "ctx_default", "ctx_min"):
        v = d.get(k)
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            return f"{slot}: {k} must be a non-negative integer"
    if d["expert_bytes"] > d["file_bytes"]:
        return f"{slot}: expert_bytes larger than file_bytes"
    if d["ctx_min"] > d["ctx_default"]:
        return f"{slot}: ctx_min larger than ctx_default"
    return None


def load(path=None):
    data = json.loads(Path(path or HERE / "models.json").read_text(encoding="utf-8"))
    out = {}
    for slot, d in data["slots"].items():
        p = problem(slot, d)
        if p:
            raise ValueError(p)
        tools = bool(d.get("tools")) and slot not in NO_TOOL_SLOTS
        out[slot] = Profile(slot=slot, display=d["display"], runtime=d["runtime"], model=d["model"],
                            file_bytes=d["file_bytes"], expert_bytes=d["expert_bytes"], n_layers=d["n_layers"],
                            kv_bytes_per_token=d["kv_bytes_per_token"], ctx_default=d["ctx_default"],
                            ctx_min=d["ctx_min"], tools=tools, estimate=bool(d.get("estimate", True)),
                            reserved=bool(d.get("reserved", False)))
    return out
