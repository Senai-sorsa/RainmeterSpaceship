"""Mode gate: which tools exist in which mode. The mode is set by the person when the session is built,
never by a tool or by model text. ULTRON is fixed to no tools."""
from dataclasses import dataclass

READ_TOOLS = frozenset({"fs_list", "fs_stat", "fs_read", "fs_grep", "sys_memory"})
TOOLS_BY_MODE = {
    "chat": frozenset(),
    "read": READ_TOOLS,
    "tweak": READ_TOOLS | {"apply_patch"},
    "ultron": frozenset(),
}
MODES = tuple(TOOLS_BY_MODE)


class Violation(Exception):
    """A forbidden attempt. The session must stop (tripwire)."""

    def __init__(self, kind, detail):
        super().__init__(f"{kind}: {detail}")
        self.kind, self.detail = kind, detail


@dataclass(frozen=True)
class ModeGate:
    mode: str
    slot: str

    def __post_init__(self):
        if self.mode not in TOOLS_BY_MODE:
            raise ValueError(f"unknown mode {self.mode!r}")
        if self.slot == "ultron" and self.mode != "ultron":
            raise ValueError("ULTRON only runs in ultron mode (chat only)")
        if self.mode == "ultron" and self.slot != "ultron":
            raise ValueError("ultron mode is only for the ULTRON slot")

    @property
    def tools(self):
        return TOOLS_BY_MODE[self.mode]

    def check(self, name, args):
        if not isinstance(name, str) or name not in self.tools:
            raise Violation("tool-not-allowed", f"{name!r} is not allowed in {self.mode} mode")
        if not isinstance(args, dict):
            raise Violation("bad-arguments", f"{name}: arguments must be an object")
        if len(repr(args)) > 20000:
            raise Violation("bad-arguments", f"{name}: arguments too large")
