"""Windows sandbox launcher (plan sections 3 and 5). No admin needed for any of it.

Sandboxes:
- "lowil": low-integrity copy of the user's token. The OS refuses writes outside LocalLow / AppDataLow;
  reads work, except objects labelled NO_READ_UP (see protect_no_read_up). Network still allowed (loopback
  is needed by model servers). [MSDN bb625960]
- "appcontainer": AppContainer with zero capabilities. No network at all (loopback included), no access to
  the user's files unless a folder is granted to its SID. For running model-modified code (tests).
- "none": plain child (only for the spikes' control runs).
Every child: started suspended, put in a Job Object (kill-on-close, process count, private-commit cap,
per-process working-set cap, BELOW_NORMAL, CPU hard cap), low memory priority, then resumed.
Only handles we list are inherited (PROC_THREAD_ATTRIBUTE_HANDLE_LIST). Only our own children are ever killed."""
import ctypes
import os
import subprocess
import sys
import tempfile
from ctypes import wintypes as W
from dataclasses import dataclass
from pathlib import Path

LOW_IL_SID = "S-1-16-4096"
MEDIUM_IL_SID = "S-1-16-8192"
AC_NAME = "CSpace.GodMode.Tests"


@dataclass(frozen=True)
class Limits:
    max_processes: int = 4
    private_commit: int = 6 << 30        # job-wide private commit (bytes); 0 = none
    cpu_pct: int = 70                    # hard cap, 1..99; 100 = none
    working_set_cap: int = 0             # per-process hard working-set max (bytes); 0 = none
    low_memory_priority: bool = True
    below_normal: bool = True


def low_il_dir():
    """%USERPROFILE%\\AppData\\LocalLow\\CSpace\\GodMode (the only place a low-IL child may write)."""
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "AppData" / "LocalLow" / "CSpace" / "GodMode"


def broker_dir():
    """%LOCALAPPDATA%\\CSpace\\GodMode (medium integrity: audit, config, work copies, proposals)."""
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "CSpace" / "GodMode"


def env_block(env):
    items = sorted(env.items(), key=lambda kv: kv[0].upper())
    s = "".join(f"{k}={v}\0" for k, v in items if "=" not in k and "\0" not in f"{k}{v}") + "\0"
    return ctypes.create_unicode_buffer(s, len(s))


def base_env(extra):
    keep = ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "PATH", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE",
            "USERPROFILE", "LOCALAPPDATA", "APPDATA", "USERNAME", "HOMEDRIVE", "HOMEPATH", "SYSTEMDRIVE",
            "PROGRAMDATA", "PROGRAMFILES", "CUDA_PATH",
            # the user's GPU routing: hides the Radeon 880M from Ollama/llama.cpp (JARVIS-Repair-Plan)
            "HIP_VISIBLE_DEVICES", "ROCR_VISIBLE_DEVICES", "CUDA_VISIBLE_DEVICES")
    env = {k: v for k, v in os.environ.items() if k.upper() in keep}
    env.update(extra or {})
    return env


if sys.platform == "win32":
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    uenv = ctypes.WinDLL("userenv", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    ntdll = ctypes.WinDLL("ntdll")

    class SID_AND_ATTRIBUTES(ctypes.Structure):
        _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", W.DWORD)]

    class TOKEN_MANDATORY_LABEL(ctypes.Structure):
        _fields_ = [("Label", SID_AND_ATTRIBUTES)]

    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [("cb", W.DWORD), ("lpReserved", W.LPWSTR), ("lpDesktop", W.LPWSTR), ("lpTitle", W.LPWSTR),
                    ("dwX", W.DWORD), ("dwY", W.DWORD), ("dwXSize", W.DWORD), ("dwYSize", W.DWORD),
                    ("dwXCountChars", W.DWORD), ("dwYCountChars", W.DWORD), ("dwFillAttribute", W.DWORD),
                    ("dwFlags", W.DWORD), ("wShowWindow", W.WORD), ("cbReserved2", W.WORD),
                    ("lpReserved2", ctypes.c_void_p), ("hStdInput", W.HANDLE), ("hStdOutput", W.HANDLE),
                    ("hStdError", W.HANDLE)]

    class STARTUPINFOEXW(ctypes.Structure):
        _fields_ = [("StartupInfo", STARTUPINFOW), ("lpAttributeList", ctypes.c_void_p)]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [("hProcess", W.HANDLE), ("hThread", W.HANDLE), ("dwProcessId", W.DWORD), ("dwThreadId", W.DWORD)]

    class SECURITY_CAPABILITIES(ctypes.Structure):
        _fields_ = [("AppContainerSid", ctypes.c_void_p), ("Capabilities", ctypes.c_void_p),
                    ("CapabilityCount", W.DWORD), ("Reserved", W.DWORD)]

    class BASIC_LIMIT(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", W.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", W.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", W.DWORD), ("SchedulingClass", W.DWORD)]

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in ("ReadOps", "WriteOps", "OtherOps", "ReadBytes", "WriteBytes",
                                                    "OtherBytes")]

    class EXTENDED_LIMIT(ctypes.Structure):
        _fields_ = [("Basic", BASIC_LIMIT), ("Io", IO_COUNTERS), ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t)]

    class CPU_RATE(ctypes.Structure):
        _fields_ = [("ControlFlags", W.DWORD), ("CpuRate", W.DWORD)]

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [("cb", W.DWORD), ("PageFaultCount", W.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t)]

    _sigs = {
        (k32, "CreateJobObjectW"): (W.HANDLE, [ctypes.c_void_p, W.LPCWSTR]),
        (k32, "SetInformationJobObject"): (W.BOOL, [W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD]),
        (k32, "QueryInformationJobObject"): (W.BOOL, [W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD,
                                                       ctypes.c_void_p]),
        (k32, "AssignProcessToJobObject"): (W.BOOL, [W.HANDLE, W.HANDLE]),
        (k32, "TerminateJobObject"): (W.BOOL, [W.HANDLE, W.UINT]),
        (k32, "GetCurrentProcess"): (W.HANDLE, []),
        (k32, "ResumeThread"): (W.DWORD, [W.HANDLE]),
        (k32, "WaitForSingleObject"): (W.DWORD, [W.HANDLE, W.DWORD]),
        (k32, "GetExitCodeProcess"): (W.BOOL, [W.HANDLE, ctypes.POINTER(W.DWORD)]),
        (k32, "CloseHandle"): (W.BOOL, [W.HANDLE]),
        (k32, "OpenProcess"): (W.HANDLE, [W.DWORD, W.BOOL, W.DWORD]),
        (k32, "SetProcessWorkingSetSizeEx"): (W.BOOL, [W.HANDLE, ctypes.c_size_t, ctypes.c_size_t, W.DWORD]),
        (k32, "SetProcessInformation"): (W.BOOL, [W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD]),
        (k32, "LocalFree"): (ctypes.c_void_p, [ctypes.c_void_p]),
        (k32, "InitializeProcThreadAttributeList"): (W.BOOL, [ctypes.c_void_p, W.DWORD, W.DWORD,
                                                               ctypes.POINTER(ctypes.c_size_t)]),
        (k32, "UpdateProcThreadAttribute"): (W.BOOL, [ctypes.c_void_p, W.DWORD, ctypes.c_size_t, ctypes.c_void_p,
                                                       ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p]),
        (k32, "DeleteProcThreadAttributeList"): (None, [ctypes.c_void_p]),
        (k32, "CreateProcessW"): (W.BOOL, [W.LPCWSTR, W.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, W.BOOL, W.DWORD,
                                           ctypes.c_void_p, W.LPCWSTR, ctypes.c_void_p,
                                           ctypes.POINTER(PROCESS_INFORMATION)]),
        (ntdll, "NtSuspendProcess"): (ctypes.c_long, [W.HANDLE]),
        (ntdll, "NtResumeProcess"): (ctypes.c_long, [W.HANDLE]),
        (psapi, "EmptyWorkingSet"): (W.BOOL, [W.HANDLE]),
        (k32, "CreateIoCompletionPort"): (W.HANDLE, [W.HANDLE, W.HANDLE, ctypes.c_size_t, W.DWORD]),
        (k32, "GetQueuedCompletionStatus"): (W.BOOL, [W.HANDLE, ctypes.POINTER(W.DWORD),
                                                       ctypes.POINTER(ctypes.c_size_t),
                                                       ctypes.POINTER(ctypes.c_void_p), W.DWORD]),
        (adv, "OpenProcessToken"): (W.BOOL, [W.HANDLE, W.DWORD, ctypes.POINTER(W.HANDLE)]),
        (adv, "DuplicateTokenEx"): (W.BOOL, [W.HANDLE, W.DWORD, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                             ctypes.POINTER(W.HANDLE)]),
        (adv, "ConvertStringSidToSidW"): (W.BOOL, [W.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)]),
        (adv, "ConvertSidToStringSidW"): (W.BOOL, [ctypes.c_void_p, ctypes.POINTER(W.LPWSTR)]),
        (adv, "GetLengthSid"): (W.DWORD, [ctypes.c_void_p]),
        (adv, "FreeSid"): (ctypes.c_void_p, [ctypes.c_void_p]),
        (adv, "SetTokenInformation"): (W.BOOL, [W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD]),
        (adv, "CreateProcessAsUserW"): (W.BOOL, [W.HANDLE, W.LPCWSTR, W.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
                                                 W.BOOL, W.DWORD, ctypes.c_void_p, W.LPCWSTR, ctypes.c_void_p,
                                                 ctypes.POINTER(PROCESS_INFORMATION)]),
        (adv, "LookupPrivilegeValueW"): (W.BOOL, [W.LPCWSTR, W.LPCWSTR, ctypes.c_void_p]),
        (adv, "AdjustTokenPrivileges"): (W.BOOL, [W.HANDLE, W.BOOL, ctypes.c_void_p, W.DWORD, ctypes.c_void_p,
                                                  ctypes.c_void_p]),
        (adv, "InitializeAcl"): (W.BOOL, [ctypes.c_void_p, W.DWORD, W.DWORD]),
        (adv, "AddMandatoryAce"): (W.BOOL, [ctypes.c_void_p, W.DWORD, W.DWORD, W.DWORD, ctypes.c_void_p]),
        (adv, "SetNamedSecurityInfoW"): (W.DWORD, [W.LPWSTR, ctypes.c_int, W.DWORD, ctypes.c_void_p, ctypes.c_void_p,
                                                   ctypes.c_void_p, ctypes.c_void_p]),
        (uenv, "CreateAppContainerProfile"): (ctypes.c_long, [W.LPCWSTR, W.LPCWSTR, W.LPCWSTR, ctypes.c_void_p,
                                                              W.DWORD, ctypes.POINTER(ctypes.c_void_p)]),
        (uenv, "DeriveAppContainerSidFromAppContainerName"): (ctypes.c_long, [W.LPCWSTR,
                                                                             ctypes.POINTER(ctypes.c_void_p)]),
        (psapi, "GetProcessMemoryInfo"): (W.BOOL, [W.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), W.DWORD]),
    }
    for (dll, name), (res, args) in _sigs.items():
        f = getattr(dll, name)
        f.restype, f.argtypes = res, args


def _ok(r, what):
    if not r:
        raise OSError(ctypes.get_last_error(), f"{what} failed")
    return r


# ---------------- tokens and SIDs ----------------

def low_il_token():
    tok, dup, sid = W.HANDLE(), W.HANDLE(), ctypes.c_void_p()
    _ok(adv.OpenProcessToken(k32.GetCurrentProcess(), 0x1 | 0x2 | 0x8 | 0x80, ctypes.byref(tok)), "OpenProcessToken")
    try:
        _ok(adv.DuplicateTokenEx(tok, 0x02000000, None, 2, 1, ctypes.byref(dup)), "DuplicateTokenEx")
        _ok(adv.ConvertStringSidToSidW(LOW_IL_SID, ctypes.byref(sid)), "ConvertStringSidToSid")
        tml = TOKEN_MANDATORY_LABEL(SID_AND_ATTRIBUTES(sid, 0x20))   # SE_GROUP_INTEGRITY
        _ok(adv.SetTokenInformation(dup, 25, ctypes.byref(tml), ctypes.sizeof(tml) + adv.GetLengthSid(sid)),
            "SetTokenInformation(TokenIntegrityLevel)")
        return dup
    except Exception:
        if dup:
            k32.CloseHandle(dup)
        raise
    finally:
        if sid:
            k32.LocalFree(sid)
        k32.CloseHandle(tok)


def appcontainer_sid(name=AC_NAME):
    """Creates the AppContainer profile if needed (no admin). Returns a PSID the caller frees with FreeSid."""
    sid = ctypes.c_void_p()
    hr = uenv.CreateAppContainerProfile(name, name, "CSpace GOD mode sandbox (no capabilities)", None, 0,
                                        ctypes.byref(sid))
    if hr == 0:
        return sid
    if (hr & 0xFFFFFFFF) == 0x800700B7:   # ERROR_ALREADY_EXISTS
        sid = ctypes.c_void_p()
        hr = uenv.DeriveAppContainerSidFromAppContainerName(name, ctypes.byref(sid))
        if hr == 0:
            return sid
    raise OSError(hr, f"AppContainer profile failed (HRESULT 0x{hr & 0xFFFFFFFF:08X})")


def sid_string(sid):
    s = W.LPWSTR()
    _ok(adv.ConvertSidToStringSidW(sid, ctypes.byref(s)), "ConvertSidToStringSid")
    try:
        return s.value
    finally:
        k32.LocalFree(s)


def appcontainer_sid_string(name=AC_NAME):
    sid = appcontainer_sid(name)
    try:
        return sid_string(sid)
    finally:
        adv.FreeSid(sid)


def grant_appcontainer(folder, access="RX", name=AC_NAME, run=subprocess.run):
    """Gives the AppContainer read (RX) or modify (M) on a folder the user owns. Additive and reversible
    with revoke_appcontainer. Uses icacls with fixed arguments; exit code checked."""
    if access not in ("RX", "M"):
        raise ValueError("access must be RX or M")
    sid = appcontainer_sid_string(name)
    exe = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "icacls.exe"
    r = run([str(exe), str(folder), "/grant", f"*{sid}:(OI)(CI)({access})", "/T", "/C", "/Q"],
            capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise OSError(r.returncode, f"icacls grant failed: {r.stdout.strip()} {r.stderr.strip()}")
    return sid


def revoke_appcontainer(folder, name=AC_NAME, run=subprocess.run):
    sid = appcontainer_sid_string(name)
    exe = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "icacls.exe"
    r = run([str(exe), str(folder), "/remove:g", f"*{sid}", "/T", "/C", "/Q"], capture_output=True, text=True,
            timeout=600)
    if r.returncode != 0:
        raise OSError(r.returncode, f"icacls remove failed: {r.stdout.strip()} {r.stderr.strip()}")


# ---------------- integrity labels (OS-enforced secret blocking for low-IL children) ----------------

def set_label(path, no_read_up=True):
    """Labels a file/folder the user owns Medium + NO_WRITE_UP (+ NO_READ_UP), inherited by children.
    Low-integrity processes then cannot read it; normal (medium) apps are unaffected.
    no_read_up=False writes an empty label ACL, which restores the default (unlabelled = medium, no-write-up)."""
    acl = ctypes.create_string_buffer(256)
    _ok(adv.InitializeAcl(acl, 256, 2), "InitializeAcl")
    if no_read_up:
        sid = ctypes.c_void_p()
        _ok(adv.ConvertStringSidToSidW(MEDIUM_IL_SID, ctypes.byref(sid)), "ConvertStringSidToSid")
        try:
            inherit = 0x1 | 0x2 if os.path.isdir(path) else 0   # OBJECT_INHERIT | CONTAINER_INHERIT
            _ok(adv.AddMandatoryAce(acl, 2, inherit, 0x1 | 0x2, sid), "AddMandatoryAce")
        finally:
            k32.LocalFree(sid)
    err = adv.SetNamedSecurityInfoW(ctypes.create_unicode_buffer(str(path)), 1, 0x10, None, None, None, acl)
    if err:
        raise OSError(err, f"SetNamedSecurityInfo(label) failed for {path}")


# ---------------- jobs and processes ----------------

def enable_privilege(name="SeIncreaseWorkingSetPrivilege"):
    """Turns on a privilege the user already holds (standard users hold this one, disabled by default).
    Affects only our own process token. Returns True if it is now enabled."""
    tok = W.HANDLE()
    if not adv.OpenProcessToken(k32.GetCurrentProcess(), 0x20 | 0x8, ctypes.byref(tok)):   # ADJUST | QUERY
        return False
    try:
        luid = (W.DWORD * 2)()
        if not adv.LookupPrivilegeValueW(None, name, luid):
            return False
        tp = (W.DWORD * 4)(1, luid[0], luid[1], 0x2)   # 1 privilege, LUID, SE_PRIVILEGE_ENABLED
        ctypes.set_last_error(0)
        adv.AdjustTokenPrivileges(tok, False, tp, 0, None, None)
        return ctypes.get_last_error() == 0              # 1300 = ERROR_NOT_ALL_ASSIGNED
    finally:
        k32.CloseHandle(tok)


def make_job(lim):
    job = _ok(k32.CreateJobObjectW(None, None), "CreateJobObject")
    info = EXTENDED_LIMIT()
    flags = 0x2000 | 0x400 | 0x8            # KILL_ON_JOB_CLOSE | DIE_ON_UNHANDLED_EXCEPTION | ACTIVE_PROCESS
    info.Basic.ActiveProcessLimit = max(1, lim.max_processes)
    if lim.private_commit:
        flags |= 0x200                      # JOB_MEMORY
        info.JobMemoryLimit = lim.private_commit
    # Note: the job-wide WORKINGSET limit needs SeIncreaseBasePriorityPrivilege (admin only, error 1314 measured),
    # so the per-process hard cap is applied by Proc.enforce_caps() to every process in the job instead.
    if lim.below_normal:
        flags |= 0x20                       # PRIORITY_CLASS
        info.Basic.PriorityClass = 0x4000   # BELOW_NORMAL_PRIORITY_CLASS
    info.Basic.LimitFlags = flags
    _ok(k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)), "SetInformationJobObject(limits)")
    if 0 < lim.cpu_pct < 100:
        rate = CPU_RATE(0x1 | 0x4, lim.cpu_pct * 100)   # ENABLE | HARD_CAP
        _ok(k32.SetInformationJobObject(job, 15, ctypes.byref(rate), ctypes.sizeof(rate)), "SetInformationJobObject(cpu)")
    return job


class Proc:
    """A sandboxed child in its own job. Closing it (or our process exiting) kills the whole job."""

    def __init__(self, job, pi, stdout=None, stdin=None, out_file=None):
        self.job, self.hp, self.ht, self.pid = job, pi.hProcess, pi.hThread, pi.dwProcessId
        self.stdout, self.stdin, self._out_file = stdout, stdin, out_file

    def wait(self, timeout=None):
        r = k32.WaitForSingleObject(self.hp, 0xFFFFFFFF if timeout is None else int(timeout * 1000))
        if r != 0:
            return None
        c = W.DWORD()
        k32.GetExitCodeProcess(self.hp, ctypes.byref(c))
        return c.value

    def alive(self):
        return self.wait(0) is None

    def kill(self):
        if self.job:
            k32.TerminateJobObject(self.job, 1)

    def pids(self):
        """All process ids in the job (the child and anything it started)."""
        buf = (ctypes.c_size_t * 66)()   # JOBOBJECT_BASIC_PROCESS_ID_LIST: 2 DWORDs packed in a ULONG_PTR + ids
        ctypes.memset(buf, 0, ctypes.sizeof(buf))
        ctypes.cast(buf, ctypes.POINTER(W.DWORD))[0] = 64
        if not k32.QueryInformationJobObject(self.job, 3, buf, ctypes.sizeof(buf), None):
            return []
        n = ctypes.cast(buf, ctypes.POINTER(W.DWORD))[1]
        return [int(buf[1 + i]) for i in range(n)]

    def working_sets(self):
        """{pid: (working_set, peak_working_set)} for every process in the job."""
        out = {}
        for pid in self.pids():
            h = k32.OpenProcess(0x1000 | 0x0010, False, pid)   # QUERY_LIMITED_INFORMATION | VM_READ
            if not h:
                continue
            try:
                c = PROCESS_MEMORY_COUNTERS()
                c.cb = ctypes.sizeof(c)
                if psapi.GetProcessMemoryInfo(h, ctypes.byref(c), c.cb):
                    out[pid] = (c.WorkingSetSize, c.PeakWorkingSetSize)
            finally:
                k32.CloseHandle(h)
        return out

    def enforce_caps(self, limits):
        """Applies the hard working-set cap and low memory priority to every process in the job that does not
        have them yet (children it started too, e.g. Ollama's runner). Call every ~0.5-2 s. Returns pids capped."""
        done = getattr(self, "_capped", set())
        self._capped = done
        new = []
        for pid in self.pids():
            if pid in done:
                continue
            h = k32.OpenProcess(0x0100 | 0x0200 | 0x1000, False, pid)   # SET_QUOTA | SET_INFORMATION | QUERY_LIMITED
            if not h:
                continue
            try:
                ok = True
                if limits.working_set_cap:
                    ok = bool(k32.SetProcessWorkingSetSizeEx(h, 1 << 20, limits.working_set_cap, 0x4 | 0x2))
                if limits.low_memory_priority:
                    prio = W.ULONG(2)
                    k32.SetProcessInformation(h, 0, ctypes.byref(prio), 4)
                if ok:
                    done.add(pid)
                    new.append(pid)
            finally:
                k32.CloseHandle(h)
        return new

    def watch_new_processes(self, limits, on_event=None):
        """Event-driven capping: the job posts JOB_OBJECT_MSG_NEW_PROCESS the moment a process joins, and we cap it
        right away (no polling gap). Runs a daemon thread until the job is closed. on_event(msg, pid) optional."""
        import threading
        port = k32.CreateIoCompletionPort(W.HANDLE(-1), None, 0, 1)
        if not port:
            raise OSError(ctypes.get_last_error(), "CreateIoCompletionPort failed")

        class ASSOC(ctypes.Structure):
            _fields_ = [("CompletionKey", ctypes.c_void_p), ("CompletionPort", W.HANDLE)]
        a = ASSOC(None, port)
        _ok(k32.SetInformationJobObject(self.job, 7, ctypes.byref(a), ctypes.sizeof(a)), "job completion port")
        self._port = port
        self.enforce_caps(limits)   # anything that joined before the port was attached

        def loop():
            msg, key, ov = W.DWORD(), ctypes.c_size_t(), ctypes.c_void_p()
            while self.job:
                if not k32.GetQueuedCompletionStatus(port, ctypes.byref(msg), ctypes.byref(key), ctypes.byref(ov), 500):
                    continue
                if msg.value == 6:          # JOB_OBJECT_MSG_NEW_PROCESS
                    self.enforce_caps(limits)
                if on_event:
                    on_event(msg.value, ov.value or 0)
                if msg.value == 4:          # JOB_OBJECT_MSG_ACTIVE_PROCESS_ZERO
                    break
            k32.CloseHandle(port)
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        return t

    def _each(self, access, fn):
        n = 0
        for pid in self.pids():
            h = k32.OpenProcess(access, False, pid)
            if h:
                try:
                    n += bool(fn(h))
                finally:
                    k32.CloseHandle(h)
        return n

    def freeze(self, trim=True):
        """Pause without losing work: suspend every process in the job (the generation stops mid-token and
        keeps its state), then give its RAM back to Windows (EmptyWorkingSet). Pages come back on resume."""
        n = self._each(0x0800, lambda h: ntdll.NtSuspendProcess(h) == 0)          # PROCESS_SUSPEND_RESUME
        if trim:
            self._each(0x0100 | 0x0400, lambda h: psapi.EmptyWorkingSet(h))      # SET_QUOTA | QUERY_INFORMATION
        return n

    def thaw(self):
        return self._each(0x0800, lambda h: ntdll.NtResumeProcess(h) == 0)

    def output(self):
        if self._out_file is None:
            return ""
        self._out_file.seek(0)
        return self._out_file.read().decode("utf-8", "replace")

    def close(self):
        for h in (self.ht, self.hp, self.job):
            if h:
                k32.CloseHandle(h)
        self.ht = self.hp = self.job = None
        for f in (self.stdin, self.stdout, self._out_file):
            try:
                f and f.close()
            except OSError:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def spawn(argv, cwd, env=None, limits=Limits(), sandbox="lowil", pipes=False, ac_name=AC_NAME):
    """Starts argv[0] (absolute path) sandboxed. pipes=True gives Proc.stdin/stdout (binary) for a JSON-lines
    protocol; otherwise stdout+stderr go to a temp file (Proc.output())."""
    if sys.platform != "win32":
        raise OSError("Windows only")
    if sandbox not in ("lowil", "appcontainer", "none"):
        raise ValueError("unknown sandbox")
    exe = Path(argv[0])
    if not exe.is_absolute() or not exe.is_file():
        raise ValueError("argv[0] must be an absolute path to an existing program")
    import msvcrt
    cmd = ctypes.create_unicode_buffer(subprocess.list2cmdline([str(a) for a in argv]))
    blk = env_block(base_env(env))
    parent_files, child_fds = [], []
    if pipes:
        r_in, w_in = os.pipe()     # child reads r_in
        r_out, w_out = os.pipe()   # child writes w_out
        stdin_f, stdout_f, out_file = os.fdopen(w_in, "wb", buffering=0), os.fdopen(r_out, "rb", buffering=0), None
        child_fds = [r_in, w_out]
        h_in, h_out = msvcrt.get_osfhandle(r_in), msvcrt.get_osfhandle(w_out)
    else:
        out_file = tempfile.TemporaryFile()
        nul = open(os.devnull, "rb")
        parent_files.append(nul)
        stdin_f = stdout_f = None
        h_in, h_out = msvcrt.get_osfhandle(nul.fileno()), msvcrt.get_osfhandle(out_file.fileno())
    handles = sorted({h_in, h_out})
    for h in handles:
        os.set_handle_inheritable(h, True)

    size = ctypes.c_size_t(0)
    k32.InitializeProcThreadAttributeList(None, 2, 0, ctypes.byref(size))
    attr = ctypes.create_string_buffer(size.value)
    _ok(k32.InitializeProcThreadAttributeList(attr, 2, 0, ctypes.byref(size)), "InitializeProcThreadAttributeList")
    harr = (W.HANDLE * len(handles))(*handles)
    _ok(k32.UpdateProcThreadAttribute(attr, 0, 0x00020002, harr, ctypes.sizeof(harr), None, None),
        "UpdateProcThreadAttribute(HANDLE_LIST)")
    sid = None
    if sandbox == "appcontainer":
        sid = appcontainer_sid(ac_name)
        sc = SECURITY_CAPABILITIES(sid, None, 0, 0)
        _ok(k32.UpdateProcThreadAttribute(attr, 0, 0x00020009, ctypes.byref(sc), ctypes.sizeof(sc), None, None),
            "UpdateProcThreadAttribute(SECURITY_CAPABILITIES)")
    six = STARTUPINFOEXW()
    six.StartupInfo.cb = ctypes.sizeof(six)
    six.StartupInfo.dwFlags = 0x100          # STARTF_USESTDHANDLES
    six.StartupInfo.hStdInput, six.StartupInfo.hStdOutput, six.StartupInfo.hStdError = h_in, h_out, h_out
    six.lpAttributeList = ctypes.cast(attr, ctypes.c_void_p)
    pi = PROCESS_INFORMATION()
    tok = low_il_token() if sandbox == "lowil" else None
    job = make_job(limits)
    flags = 0x4 | 0x400 | 0x08000000 | 0x00080000   # SUSPENDED | UNICODE_ENV | NO_WINDOW | EXTENDED_STARTUPINFO
    try:
        if tok is not None:
            _ok(adv.CreateProcessAsUserW(tok, None, cmd, None, None, True, flags, blk, str(cwd), ctypes.byref(six),
                                         ctypes.byref(pi)), "CreateProcessAsUser")
        else:
            _ok(k32.CreateProcessW(None, cmd, None, None, True, flags, blk, str(cwd), ctypes.byref(six),
                                   ctypes.byref(pi)), "CreateProcess")
        try:
            _ok(k32.AssignProcessToJobObject(job, pi.hProcess), "AssignProcessToJobObject")
            if limits.working_set_cap:
                _ok(k32.SetProcessWorkingSetSizeEx(pi.hProcess, 1 << 20, limits.working_set_cap, 0x4 | 0x2),
                    "SetProcessWorkingSetSizeEx")   # HARDWS_MAX_ENABLE | HARDWS_MIN_DISABLE
            if limits.low_memory_priority:
                prio = W.ULONG(2)                    # MEMORY_PRIORITY_LOW
                _ok(k32.SetProcessInformation(pi.hProcess, 0, ctypes.byref(prio), 4), "SetProcessInformation")
        except Exception:
            k32.TerminateJobObject(job, 1)
            raise
        k32.ResumeThread(pi.hThread)
    except Exception:
        k32.CloseHandle(job)
        raise
    finally:
        k32.DeleteProcThreadAttributeList(attr)
        if tok:
            k32.CloseHandle(tok)
        if sid:
            adv.FreeSid(sid)
        for fd in child_fds:
            os.close(fd)
        for f in parent_files:
            f.close()
    return Proc(job, pi, stdout=stdout_f, stdin=stdin_f, out_file=out_file)


def run(argv, cwd, env=None, timeout=600, limits=Limits(), low_il=True, sandbox=None):
    """Runs to completion; returns (exit_code or None on timeout, combined output)."""
    sb = sandbox or ("lowil" if low_il else "none")
    with spawn(argv, cwd, env, limits, sb) as p:
        code = p.wait(timeout)
        if code is None:
            p.kill()
            p.wait(10)
        return code, p.output()
