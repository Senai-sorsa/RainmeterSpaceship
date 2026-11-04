"""Comfortable-RAM rule: measure, budget, place, watch.

Pure logic (budget, plan, Watchdog) is separate from the OS probe so tests use fake snapshots.
Plan section 3. Numbers marked [E] in the plan are defaults the user can tune.
"""
import ctypes
import shutil
import subprocess
import sys
from dataclasses import dataclass, field

GiB = 1 << 30


@dataclass(frozen=True)
class Snapshot:
    total_ram: int
    avail_ram: int
    commit_used: int
    commit_limit: int
    vram_total: int | None = None   # None = unknown (never treated as 0 free)
    vram_used: int | None = None


@dataclass(frozen=True)
class Policy:
    reserve_min: int = 6 * GiB          # always left for Windows + the user's apps
    reserve_frac: float = 0.20          # ...or this share of total RAM, whichever is larger
    vram_reserve: int = int(1.5 * GiB)  # JARVIS Whisper + Kokoro (1.27 GB measured) + margin
    gpu_overhead: int = 1 * GiB         # CUDA context + compute buffers [E]
    stream_floor: float = 0.40          # below this RAM coverage of CPU experts: not worth it [S]
    pause_below: int = 4 * GiB
    resume_above: int = int(5.5 * GiB)
    stop_below: int = int(2.5 * GiB)
    pause_samples: int = 3
    resume_samples: int = 5
    commit_pause_frac: float = 0.90
    private_commit_cap: int = 6 * GiB   # Job Object cap for private memory (not the mapped model)
    cpu_cap_pct: int = 70


def reserve(snap, pol):
    return max(pol.reserve_min, int(snap.total_ram * pol.reserve_frac))


def ram_budget(snap, pol):
    """Bytes a model may use comfortably right now (0 if none)."""
    return max(0, snap.avail_ram - reserve(snap, pol))


def vram_budget(snap, pol):
    if snap.vram_total is None or snap.vram_used is None:
        return None
    return max(0, snap.vram_total - snap.vram_used - pol.vram_reserve)


@dataclass(frozen=True)
class Placement:
    mode: str                  # gpu | split | stream | refuse
    reason: str
    ctx: int = 0
    n_cpu_moe: int = 0
    threads: int = 1
    ram_budget: int = 0
    vram_budget: int = 0
    cpu_expert_bytes: int = 0
    coverage: float = 1.0      # share of CPU experts that fits in the RAM budget
    working_set_cap: int = 0   # hard working-set max for the process (0 = none)


def _ctx_candidates(p):
    c = p.ctx_default
    while c >= p.ctx_min:
        yield c
        c //= 2


def plan(p, snap, pol=Policy(), physical_cores=8):
    """Placement for a llama-server MoE run. Never returns a plan that exceeds the budgets."""
    rb, vb = ram_budget(snap, pol), vram_budget(snap, pol)
    threads = max(1, physical_cores - 2)
    if vb is None:
        return Placement("refuse", "VRAM could not be measured, so GPU placement is not safe", threads=threads, ram_budget=rb)
    if p.n_layers <= 0 or p.file_bytes <= 0:
        return Placement("refuse", "model profile is empty (slot reserved or not inspected yet)", threads=threads,
                         ram_budget=rb, vram_budget=vb)
    for ctx in _ctx_candidates(p):
        gpu_fixed = p.other_bytes + p.kv_bytes_per_token * ctx + pol.gpu_overhead
        if gpu_fixed <= vb:
            break
    else:
        return Placement("refuse", f"attention weights + KV cache need more than the {vb / GiB:.1f} GiB of VRAM "
                         f"that is free (even at {p.ctx_min} context)", threads=threads, ram_budget=rb, vram_budget=vb)
    per = p.expert_bytes_per_layer
    if per == 0:
        return Placement("gpu", "dense model fits in VRAM", ctx=ctx, threads=threads, ram_budget=rb, vram_budget=vb)
    gpu_layers = min(p.n_layers, (vb - gpu_fixed) // per)
    n_cpu_moe = p.n_layers - gpu_layers
    cpu_exp = n_cpu_moe * per
    common = dict(ctx=ctx, n_cpu_moe=n_cpu_moe, threads=threads, ram_budget=rb, vram_budget=vb, cpu_expert_bytes=cpu_exp)
    if n_cpu_moe == 0:
        return Placement("gpu", "whole model fits in VRAM", **common)
    coverage = min(1.0, rb / cpu_exp)
    if cpu_exp <= rb:
        return Placement("split", f"{n_cpu_moe} expert layers in RAM, all inside the comfortable budget",
                         coverage=coverage, working_set_cap=min(rb, cpu_exp + GiB), **common)
    if coverage >= pol.stream_floor and rb > 0:
        return Placement("stream", f"experts stream from the SSD: {coverage:.0%} fit in comfortable RAM "
                         f"({rb / GiB:.1f} GiB); expect slow but steady output", coverage=coverage,
                         working_set_cap=rb, **common)
    return Placement("refuse", f"only {coverage:.0%} of the CPU experts fit in comfortable RAM "
                     f"({rb / GiB:.1f} GiB free after the reserve); below {pol.stream_floor:.0%} it would thrash. "
                     "Close some apps and try again", coverage=coverage, **common)


def ollama_check(p, snap, pol=Policy()):
    """Pre-load check for a model run by Ollama (layer split only, no expert offload; weights are mmap'd).
    Returns (mode, num_ctx, reason), mode = fits | stream | refuse.
    Approximation [E]: RAM need = file - what fits on the GPU. 'stream' = the CPU part is bigger than the
    comfortable budget but >= stream_floor of it fits; the OS pages the rest from the SSD (slower)."""
    rb, vb = ram_budget(snap, pol), vram_budget(snap, pol)
    if p.file_bytes <= 0:
        return "refuse", 0, "model profile is empty (slot reserved or not inspected yet)"
    vb = vb or 0
    best = None
    for ctx in _ctx_candidates(p):
        on_gpu = max(0, vb - p.kv_bytes_per_token * ctx - pol.gpu_overhead)
        need = max(0, p.file_bytes - on_gpu)
        if need <= rb:
            return "fits", ctx, f"needs ~{need / GiB:.1f} GiB RAM of {rb / GiB:.1f} GiB comfortable"
        best = (ctx, need)
    ctx, need = best
    coverage = rb / need if need else 1.0
    if coverage >= pol.stream_floor:
        return "stream", ctx, (f"needs ~{need / GiB:.1f} GiB RAM, {rb / GiB:.1f} GiB comfortable ({coverage:.0%}): "
                               "runs slower, paging weights from the SSD; the watchdog pauses it if RAM gets tight")
    return "refuse", 0, (f"needs ~{need / GiB:.1f} GiB RAM but only {rb / GiB:.1f} GiB is comfortable ({coverage:.0%}); "
                         "close some apps and try again")


@dataclass
class Watchdog:
    """Sampled every ~2 s. Hysteresis so it doesn't flap. Returns none | pause | resume | stop."""
    pol: Policy = field(default_factory=Policy)
    paused: bool = False
    stopped: bool = False
    _low: int = 0
    _ok: int = 0

    def step(self, snap):
        if self.stopped:
            return "none"
        if snap.avail_ram < self.pol.stop_below:
            self.stopped = True
            return "stop"
        tight = snap.avail_ram < self.pol.pause_below or (
            snap.commit_limit and snap.commit_used > self.pol.commit_pause_frac * snap.commit_limit)
        if tight:
            self._low, self._ok = self._low + 1, 0
        else:
            self._low = 0
            self._ok = self._ok + 1 if snap.avail_ram > self.pol.resume_above else 0
        if not self.paused and self._low >= self.pol.pause_samples:
            self.paused = True
            return "pause"
        if self.paused and self._ok >= self.pol.resume_samples:
            self.paused = False
            return "resume"
        return "none"


# ---------------- OS probe (Windows). Read-only calls only. ----------------

class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def _ram():
    m = _MEMORYSTATUSEX()
    m.dwLength = ctypes.sizeof(m)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
        raise OSError("GlobalMemoryStatusEx failed")
    # TotalPageFile = commit limit, AvailPageFile = commit left (Windows naming).
    return m.ullTotalPhys, m.ullAvailPhys, m.ullTotalPageFile - m.ullAvailPageFile, m.ullTotalPageFile


def parse_nvidia_smi(text):
    """'12231, 0' (MiB) -> (total_bytes, used_bytes) for the first GPU, or (None, None)."""
    for line in text.strip().splitlines():
        parts = [x.strip() for x in line.split(",")]
        if len(parts) == 2 and all(x.isdigit() for x in parts):
            return int(parts[0]) << 20, int(parts[1]) << 20
    return None, None


def _vram(run=subprocess.run):
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None, None
    try:
        r = run([exe, "--query-gpu=memory.total,memory.used", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None, None
    if r.returncode != 0:
        return None, None
    return parse_nvidia_smi(r.stdout)


def snapshot():
    if sys.platform != "win32":
        raise OSError("the memory probe is Windows-only")
    total, avail, cu, cl = _ram()
    vt, vu = _vram()
    return Snapshot(total, avail, cu, cl, vt, vu)


def physical_cores():
    """Counts RelationProcessorCore records (GetLogicalProcessorInformationEx). Falls back to logical/2."""
    import os
    fallback = max(1, (os.cpu_count() or 2) // 2)
    try:
        k32 = ctypes.windll.kernel32
        size = ctypes.c_ulong(0)
        k32.GetLogicalProcessorInformationEx(0, None, ctypes.byref(size))
        buf = ctypes.create_string_buffer(size.value)
        if not k32.GetLogicalProcessorInformationEx(0, buf, ctypes.byref(size)):
            return fallback
        n, off = 0, 0
        while off < size.value:
            rel, rsize = ctypes.c_ulong.from_buffer(buf, off).value, ctypes.c_ulong.from_buffer(buf, off + 4).value
            if rsize == 0:
                break
            n += rel == 0
            off += rsize
        return n or fallback
    except (OSError, AttributeError):
        return fallback
